"""Generic Page Triage for Themis: OCR/Native/Visual/Blank/Missing routing.

Strictly signal-based and agnostic: zero hardcoded folios, doc IDs, or process-specific heuristics.
Detects corrupted text layers (C0 control bytes, PUA, scrambled Type 3 CMaps), visually rendered
document text, and deficient native text (scanned images with only marginal furniture).
"""
from __future__ import annotations

import ctypes
import math
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# Add project root if needed
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_raw
import numpy as np
from PIL import Image


class PageCategory(str, Enum):
    NATIVE_VALID = "NATIVE_VALID"
    CORRUPTED_TEXT_LAYER = "CORRUPTED_TEXT_LAYER"
    TEXTUAL_VISUAL = "TEXTUAL_VISUAL"
    VISUAL_ASSET = "VISUAL_ASSET"
    BLANK_PAGE = "BLANK_PAGE"
    BLANK_BODY = "BLANK_BODY"
    MISSING_FOLIO = "MISSING_FOLIO"


class TriageAction(str, Enum):
    USE_NATIVE_PDFIUM = "USE_NATIVE_PDFIUM"
    TRIGGER_OCR = "TRIGGER_OCR"
    SKIP_BLANK = "SKIP_BLANK"
    RECORD_GAP = "RECORD_GAP"


@dataclass
class TriageDecision:
    page_number: int
    category: PageCategory
    action: TriageAction
    confidence: float
    reason: str
    metrics: dict[str, Any] = field(default_factory=dict)


def analyze_visual_ink_and_text_coverage(
    raw_page: Any,
    raw_tp: Any | None,
    width: float,
    height: float,
    scale: float = 0.20
) -> tuple[float, float, float, int, int, bool]:
    """Compute visual ink density, text bbox mask, native coverage, and unexplained ink ratio.
    
    Returns:
        (ink_ratio, native_coverage, unexplained_ink_ratio, body_rects, margin_rects, has_visual_ink)
    """
    try:
        w_px = max(1, int(round(width * scale)))
        h_px = max(1, int(round(height * scale)))
        
        bitmap = pdfium_raw.FPDFBitmap_Create(w_px, h_px, 1)
        pdfium_raw.FPDFBitmap_FillRect(bitmap, 0, 0, w_px, h_px, 0xFFFFFFFF)
        pdfium_raw.FPDF_RenderPageBitmap(bitmap, raw_page, 0, 0, w_px, h_px, 0, 0x01)
        
        buf_ptr = pdfium_raw.FPDFBitmap_GetBuffer(bitmap)
        stride = pdfium_raw.FPDFBitmap_GetStride(bitmap)
        raw_bytes = ctypes.string_at(buf_ptr, stride * h_px)
        img_arr = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((h_px, stride))[:, :w_px * 4].reshape((h_px, w_px, 4))
        # Standard luminance (REC 601)
        gray = (0.299 * img_arr[:, :, 2] + 0.587 * img_arr[:, :, 1] + 0.114 * img_arr[:, :, 0]).astype(np.uint8)
        pdfium_raw.FPDFBitmap_Destroy(bitmap)
        
        # Binary ink mask (ink = dark luminance < 235)
        ink_mask = gray < 235
        
        # Body margin: exclude outer 5% to avoid scanner edge shadows
        mx0 = int(round(w_px * 0.05))
        mx1 = int(round(w_px * 0.95))
        my0 = int(round(h_px * 0.05))
        my1 = int(round(h_px * 0.95))
        
        # Build text bounding box mask
        n_rects = pdfium_raw.FPDFText_CountRects(raw_tp, 0, -1) if raw_tp else 0
        text_mask = np.zeros((h_px, w_px), dtype=bool)
        body_rects_count = 0
        margin_rects_count = 0
        
        l, t, r, b = ctypes.c_double(), ctypes.c_double(), ctypes.c_double(), ctypes.c_double()
        for i in range(n_rects):
            pdfium_raw.FPDFText_GetRect(raw_tp, i, ctypes.byref(l), ctypes.byref(t), ctypes.byref(r), ctypes.byref(b))
            
            rx_mid = ((l.value + r.value) / 2.0) / width
            ry_mid = ((t.value + b.value) / 2.0) / height
            
            # Marginal stamp check: lateral edges (rx_mid > 0.90 or rx_mid < 0.08) or top/bottom edges
            if rx_mid > 0.90 or rx_mid < 0.08 or ry_mid > 0.94 or ry_mid < 0.05:
                margin_rects_count += 1
            else:
                body_rects_count += 1
                
            x0 = max(0, int(math.floor(min(l.value, r.value) * scale)) - 2)
            x1 = min(w_px, int(math.ceil(max(l.value, r.value) * scale)) + 2)
            y0 = max(0, int(math.floor((height - max(t.value, b.value)) * scale)) - 2)
            y1 = min(h_px, int(math.ceil((height - min(t.value, b.value)) * scale)) + 2)
            if x1 > x0 and y1 > y0:
                text_mask[y0:y1, x0:x1] = True
                
        body_ink_mask = ink_mask[my0:my1, mx0:mx1]
        body_text_mask = text_mask[my0:my1, mx0:mx1]
        
        body_total_pixels = body_ink_mask.size
        body_ink_pixels = int(np.sum(body_ink_mask))
        explained_ink_pixels = int(np.sum(body_ink_mask & body_text_mask))
        unexplained_ink_pixels = int(np.sum(body_ink_mask & (~body_text_mask)))
        
        ink_ratio = body_ink_pixels / max(body_total_pixels, 1)
        native_coverage = (explained_ink_pixels / body_ink_pixels) if body_ink_pixels > 0 else 1.0
        unexplained_ink_ratio = unexplained_ink_pixels / max(body_total_pixels, 1)
        
        has_visual_ink = ink_ratio >= 0.003
        return (
            round(ink_ratio, 4),
            round(native_coverage, 4),
            round(unexplained_ink_ratio, 4),
            body_rects_count,
            margin_rects_count,
            has_visual_ink
        )
    except Exception:
        return 0.0, 1.0, 0.0, 0, 0, True


def analyze_page_objects(raw_page: Any, width: float, height: float) -> tuple[int, float, int]:
    """Inspect embedded page objects: image count, total image area ratio, vector path count."""
    try:
        n_objs = pdfium_raw.FPDFPage_CountObjects(raw_page)
        if n_objs <= 0:
            return 0, 0.0, 0
            
        img_count = 0
        img_total_area = 0.0
        path_count = 0
        page_area = max(width * height, 1.0)
        
        l, b, r, t = ctypes.c_float(), ctypes.c_float(), ctypes.c_float(), ctypes.c_float()
        
        for i in range(n_objs):
            obj = pdfium_raw.FPDFPage_GetObject(raw_page, i)
            t_obj = pdfium_raw.FPDFPageObj_GetType(obj)
            
            if t_obj == pdfium_raw.FPDF_PAGEOBJ_IMAGE:
                img_count += 1
                pdfium_raw.FPDFPageObj_GetBounds(obj, ctypes.byref(l), ctypes.byref(b), ctypes.byref(r), ctypes.byref(t))
                area = max(0.0, (r.value - l.value) * (t.value - b.value))
                img_total_area += area
            elif t_obj == pdfium_raw.FPDF_PAGEOBJ_PATH:
                path_count += 1
                
        img_area_ratio = min(1.0, img_total_area / page_area)
        return img_count, round(img_area_ratio, 4), path_count
    except Exception:
        return 0, 0.0, 0


def _textual_visual_pattern(unexplained: np.ndarray) -> tuple[dict[str, Any], list[tuple[int, int]]]:
    """Classify a body ink mask and return paragraph-band regions in mask pixels."""
    row_counts = unexplained.sum(axis=1)
    threshold = max(2, int(round(unexplained.shape[1] * 0.005)))
    active = row_counts >= threshold
    bands: list[dict[str, Any]] = []
    start: int | None = None
    for row, is_active in enumerate(active.tolist() + [False]):
        if is_active and start is None:
            start = row
        elif not is_active and start is not None:
            end = row
            band_height = end - start
            band_ink = unexplained[start:end].any(axis=0)
            positions = np.flatnonzero(band_ink)
            span = int(positions[-1] - positions[0] + 1) if len(positions) else 0
            edges = np.diff(np.r_[False, band_ink, False].astype(np.int8))
            component_runs = int(np.count_nonzero(edges == 1))
            if 1 <= band_height <= max(8, int(unexplained.shape[0] * 0.025)) and span:
                bands.append({
                    "y0": start,
                    "y1": end,
                    "span_ratio": span / max(unexplained.shape[1], 1),
                    "component_runs": component_runs,
                })
            start = None
    text_bands = [b for b in bands if b["span_ratio"] >= 0.16 and b["component_runs"] >= 4]
    band_count = len(text_bands)
    component_median = float(np.median([b["component_runs"] for b in text_bands])) if text_bands else 0.0
    span_cv = 0.0
    if len(text_bands) >= 2:
        spans = np.asarray([b["span_ratio"] for b in text_bands], dtype=float)
        span_cv = float(spans.std() / max(spans.mean(), 1e-9))
    qualifies = band_count >= 8 and component_median >= 5 and span_cv >= 0.10

    regions: list[tuple[int, int]] = []
    if qualifies:
        gaps = [b["y0"] - a["y1"] for a, b in zip(text_bands, text_bands[1:]) if b["y0"] > a["y1"]]
        pitch = float(np.median(gaps)) if gaps else 2.0
        max_gap = max(3.0, pitch * 2.1)
        current = [text_bands[0]["y0"], text_bands[0]["y1"]]
        for band in text_bands[1:]:
            if band["y0"] - current[1] <= max_gap:
                current[1] = band["y1"]
            else:
                regions.append((current[0], current[1]))
                current = [band["y0"], band["y1"]]
        regions.append((current[0], current[1]))
    return {
        "textual_visual_band_count": band_count,
        "textual_visual_component_median": round(component_median, 2),
        "textual_visual_span_cv": round(span_cv, 3),
        "textual_visual_candidate": qualifies,
    }, regions


def _textual_visual_regions(
    raw_page: Any,
    width: float,
    height: float,
    raw_tp: Any | None,
    *,
    scale: float = 0.20,
) -> tuple[dict[str, Any], list[dict[str, float]]]:
    """Find repeated, glyph-sized horizontal bands in the body and return PDF-space regions.

    This is a cheap routing signal, not OCR or a semantic classifier. Repeated narrow
    ink bands with glyph-like horizontal components distinguish page text from the
    continuous texture of photos and the sparse long strokes common in plans/sketches.
    """
    try:
        w_px = max(1, int(round(width * scale)))
        h_px = max(1, int(round(height * scale)))
        bitmap = pdfium_raw.FPDFBitmap_Create(w_px, h_px, 1)
        pdfium_raw.FPDFBitmap_FillRect(bitmap, 0, 0, w_px, h_px, 0xFFFFFFFF)
        pdfium_raw.FPDF_RenderPageBitmap(bitmap, raw_page, 0, 0, w_px, h_px, 0, 0x01)
        buf_ptr = pdfium_raw.FPDFBitmap_GetBuffer(bitmap)
        stride = pdfium_raw.FPDFBitmap_GetStride(bitmap)
        rgba = np.frombuffer(
            ctypes.string_at(buf_ptr, stride * h_px), dtype=np.uint8
        ).reshape((h_px, stride))[:, : w_px * 4].reshape((h_px, w_px, 4))
        gray = (0.299 * rgba[:, :, 2] + 0.587 * rgba[:, :, 1] + 0.114 * rgba[:, :, 0]).astype(np.uint8)
        pdfium_raw.FPDFBitmap_Destroy(bitmap)

        x0, x1 = int(w_px * 0.05), int(w_px * 0.95)
        y0, y1 = int(h_px * 0.05), int(h_px * 0.95)
        ink = gray[y0:y1, x0:x1] < 200
        text_mask = np.zeros_like(ink)
        rect_count = pdfium_raw.FPDFText_CountRects(raw_tp, 0, -1) if raw_tp else 0
        left, top, right, bottom = (ctypes.c_double() for _ in range(4))
        for rect_idx in range(rect_count):
            pdfium_raw.FPDFText_GetRect(
                raw_tp, rect_idx, ctypes.byref(left), ctypes.byref(top),
                ctypes.byref(right), ctypes.byref(bottom),
            )
            rx0 = max(0, int(min(left.value, right.value) * scale) - x0 - 2)
            rx1 = min(ink.shape[1], int(max(left.value, right.value) * scale) - x0 + 3)
            ry0 = max(0, int((height - max(top.value, bottom.value)) * scale) - y0 - 2)
            ry1 = min(ink.shape[0], int((height - min(top.value, bottom.value)) * scale) - y0 + 3)
            if rx1 > rx0 and ry1 > ry0:
                text_mask[ry0:ry1, rx0:rx1] = True
        unexplained = ink & ~text_mask
        pattern, relative_regions = _textual_visual_pattern(unexplained)
        regions_px = [(top_y + y0, bottom_y + y0) for top_y, bottom_y in relative_regions]

        pad = max(3, int(round(4.0 * scale)))
        regions = [
            {
                "x0": round(x0 / scale, 2),
                "y0": round(height - min(h_px, bottom_y + pad) / scale, 2),
                "x1": round(x1 / scale, 2),
                "y1": round(height - max(0, top_y - pad) / scale, 2),
            }
            for top_y, bottom_y in regions_px
        ]
        metrics = {**pattern, "textual_visual_region_count": len(regions)}
        return metrics, regions
    except Exception:
        return {
            "textual_visual_band_count": 0,
            "textual_visual_component_median": 0.0,
            "textual_visual_span_cv": 0.0,
            "textual_visual_region_count": 0,
            "textual_visual_candidate": False,
        }, []


def triage_page(
    page: Any,
    page_num: int,
    raw_tp: Any | None = None
) -> TriageDecision:
    """Evaluate objective signals of page content and return autonomous routing decision.
    
    Strictly signal-based and agnostic: zero hardcoded folios or document IDs.
    - CORRUPTED_TEXT_LAYER (C0 control bytes, PUA, scrambled Type 3 CMaps) -> existing OCR route
    - TEXTUAL_VISUAL (repeated glyph-sized body ink bands not covered by native text) -> regional OCR
    - BLANK_BODY / BLANK_PAGE -> SKIP_BLANK
    - VISUAL_ASSET / NATIVE_VALID -> USE_NATIVE_PDFIUM (marginal furniture never triggers OCR)
    """
    raw_page = page.raw if hasattr(page, "raw") else page
    width, height = page.get_size() if hasattr(page, "get_size") else (
        pdfium_raw.FPDF_GetPageWidthF(raw_page),
        pdfium_raw.FPDF_GetPageHeightF(raw_page)
    )
    
    if raw_tp is None:
        textpage = page.get_textpage() if hasattr(page, "get_textpage") else None
        raw_tp = textpage.raw if textpage else None
        
    n_chars = pdfium_raw.FPDFText_CountChars(raw_tp) if raw_tp else 0
    
    # Extract native text stream
    raw_text = ""
    if n_chars > 0:
        buf_len = (n_chars + 1) * 2
        raw_buf = ctypes.create_string_buffer(buf_len)
        chars_written = pdfium_raw.FPDFText_GetText(raw_tp, 0, n_chars, ctypes.cast(raw_buf, ctypes.POINTER(ctypes.c_ushort)))
        if chars_written > 0:
            raw_text = raw_buf.raw[: (chars_written - 1) * 2].decode("utf-16le", errors="replace")
            
    # Compute textual quality signals
    ctrl_count = sum(1 for c in raw_text if ord(c) < 32 and c not in "\t\n\r")
    pua_count = sum(1 for c in raw_text if 0xE000 <= ord(c) <= 0xF8FF or c == "\ufffd")
    alpha_count = sum(1 for c in raw_text if c.isalnum())
    symbol_count = sum(1 for c in raw_text if not c.isalnum() and not c.isspace())
    alpha_ratio = round(alpha_count / max(n_chars, 1), 4)
    
    # Compute visual signals & spatial coverage
    (
        ink_ratio,
        native_coverage,
        unexplained_ink_ratio,
        body_rects,
        margin_rects,
        has_visual_ink
    ) = analyze_visual_ink_and_text_coverage(raw_page, raw_tp, width, height, scale=0.20)
    
    img_count, img_area_ratio, path_count = analyze_page_objects(raw_page, width, height)
    has_visual_content = has_visual_ink or (img_area_ratio >= 0.05 and ink_ratio >= 0.003)
    
    metrics = {
        "n_chars": n_chars,
        "alpha_ratio": alpha_ratio,
        "symbol_count": symbol_count,
        "ctrl_count": ctrl_count,
        "pua_count": pua_count,
        "ink_ratio": ink_ratio,
        "img_ratio": img_area_ratio,
        "native_coverage": native_coverage,
        "unexplained_ink_ratio": unexplained_ink_ratio,
        "body_rects": body_rects,
        "margin_rects": margin_rects,
        "img_count": img_count,
        "path_count": path_count,
        "has_visual_ink": has_visual_content
    }

    # =========================================================================
    # DECISION TREE (Generic, multi-signal, deterministic)
    # =========================================================================
    
    # 1. Blank Body / Marginal Furniture Only Check:
    # Body has no native text (only margin stamps) AND body ink is negligible (blank canvas)
    if body_rects == 0 and (ink_ratio < 0.003 or unexplained_ink_ratio < 0.003):
        return TriageDecision(
            page_number=page_num,
            category=PageCategory.BLANK_BODY,
            action=TriageAction.SKIP_BLANK,
            confidence=0.99,
            reason=f"Page body is visually empty (body ink={ink_ratio:.4f}, unexplained={unexplained_ink_ratio:.4f}; only {margin_rects} marginal furniture stamps)",
            metrics=metrics
        )
        
    # 2. Blank Page Check: no ink, no embedded images, minimal text
    if not has_visual_content and n_chars < 15 and img_area_ratio < 0.10:
        return TriageDecision(
            page_number=page_num,
            category=PageCategory.BLANK_PAGE,
            action=TriageAction.SKIP_BLANK,
            confidence=0.99,
            reason="Zero/negligible visual ink and empty text layer (blank canvas)",
            metrics=metrics
        )
        
    # 3. Corrupted Text Layer (Unequivocally corrupted CMap / C0 / PUA / scrambled Type 3) -> TRIGGER_OCR
    # Case A: C0 unprintable control characters pollution (e.g. \x01\x04\x05...)
    if ctrl_count >= 5 or (n_chars > 0 and (ctrl_count / n_chars) > 0.01):
        return TriageDecision(
            page_number=page_num,
            category=PageCategory.CORRUPTED_TEXT_LAYER,
            action=TriageAction.TRIGGER_OCR,
            confidence=0.98,
            reason=f"Text layer polluted by {ctrl_count} unprintable C0 control bytes",
            metrics=metrics
        )
        
    # Case B: PUA / replacement character dominance
    if pua_count >= 5 or (n_chars > 0 and (pua_count / n_chars) > 0.03):
        return TriageDecision(
            page_number=page_num,
            category=PageCategory.CORRUPTED_TEXT_LAYER,
            action=TriageAction.TRIGGER_OCR,
            confidence=0.96,
            reason=f"Text layer dominated by {pua_count} unmapped replacement/PUA glyphs",
            metrics=metrics
        )
        
    # Case C: Scrambled Type 3 / Non-standard CMap (symbols like !#$%& dominate instead of letters)
    if n_chars >= 40 and alpha_ratio < 0.35 and symbol_count > 30 and (has_visual_content or ink_ratio >= 0.005):
        return TriageDecision(
            page_number=page_num,
            category=PageCategory.CORRUPTED_TEXT_LAYER,
            action=TriageAction.TRIGGER_OCR,
            confidence=0.99,
            reason=f"CMap scrambled: alpha ratio {alpha_ratio:.2f} < 0.35 with {symbol_count} non-alphanumeric symbols",
            metrics=metrics
        )

    candidate_regions: list[dict[str, float]] = []
    if native_coverage < 0.45 and unexplained_ink_ratio >= 0.003 and has_visual_content:
        textvisual_metrics, candidate_regions = _textual_visual_regions(
            raw_page, width, height, raw_tp
        )
        metrics.update(textvisual_metrics)

    # Route visually rendered document text to regional OCR before generic visual
    # assets. Native text may exist in marginal stamps, so use body coverage too.
    if (
        metrics.get("textual_visual_candidate", False)
        and native_coverage < 0.45
        and unexplained_ink_ratio >= 0.003
        and candidate_regions
    ):
        metrics["candidate_regions_pdf"] = candidate_regions
        return TriageDecision(
            page_number=page_num,
            category=PageCategory.TEXTUAL_VISUAL,
            action=TriageAction.TRIGGER_OCR,
            confidence=0.90,
            reason=(
                "Repeated glyph-sized body ink bands are poorly covered by native text "
                f"(coverage={native_coverage:.3f}, bands={metrics['textual_visual_band_count']})"
            ),
            metrics=metrics,
        )
        
    # 4. Scanned / Visual Content without semantic text -> VisualNode / Asset (USE_NATIVE_PDFIUM, no OCR)
    if body_rects == 0 and has_visual_content:
        return TriageDecision(
            page_number=page_num,
            category=PageCategory.VISUAL_ASSET,
            action=TriageAction.USE_NATIVE_PDFIUM,
            confidence=0.98,
            reason=f"Visual asset page preserved as VisualNode without OCR (ink={ink_ratio:.3f}, img_r={img_area_ratio:.2f}; only {margin_rects} margin stamps)",
            metrics=metrics
        )
        
    # 5. Native Valid: text layer is readable, letters dominate, and native text covers the page
    return TriageDecision(
        page_number=page_num,
        category=PageCategory.NATIVE_VALID,
        action=TriageAction.USE_NATIVE_PDFIUM,
        confidence=0.99,
        reason=f"Valid native text layer (chars={n_chars}, alpha={alpha_ratio:.2f}, cov={native_coverage:.2f})",
        metrics=metrics
    )
