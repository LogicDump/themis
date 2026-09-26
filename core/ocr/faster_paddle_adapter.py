"""Selective OCR Fallback Adapter using faster-paddle (ONNX Runtime).

Provides high-performance fallback for pages with missing or scrambled CMap/ToUnicode text layers.
"""
from __future__ import annotations

import io
import logging
import threading
import time
from typing import Any

import faster_paddle

logger = logging.getLogger("themis.ocr.faster_paddle")

_ocr_engine: faster_paddle.OcrEngine | None = None
_ocr_lock = threading.Lock()


def get_ocr_engine(model_size: str = "small", rec_batch: int = 32) -> faster_paddle.OcrEngine:
    """Retrieve or initialize the thread-safe singleton OCR engine."""
    global _ocr_engine
    if _ocr_engine is None:
        with _ocr_lock:
            if _ocr_engine is None:
                logger.info(f"Initializing faster-paddle OcrEngine (model_size={model_size}, rec_batch={rec_batch})")
                _ocr_engine = faster_paddle.OcrEngine(model_size=model_size, rec_batch=rec_batch)
    return _ocr_engine


def is_text_layer_invalid(raw_text: str, n_chars: int) -> bool:
    """Detect if page text layer is unequivocally invalid or corrupted.
    
    Checks for:
    1. Zero text characters on non-blank pages.
    2. Dominance of C0 unprintable control characters.
    3. Dominance of replacement characters (\ufffd) or Private Use Area codes.
    4. Scrambled CMap / Type3 font without ToUnicode (high non-alphanumeric ratio).
    """
    if n_chars == 0:
        return True

    # 1. C0 control chars (other than tab, newline, cr)
    ctrl_count = sum(1 for c in raw_text if ord(c) < 32 and c not in "\t\n\r")
    if ctrl_count >= 5 or (ctrl_count / max(n_chars, 1)) > 0.01:
        return True

    # 2. Replacement chars (\ufffd) or Private Use Area (0xE000-0xF8FF)
    pua_count = sum(1 for c in raw_text if 0xE000 <= ord(c) <= 0xF8FF or c == "\ufffd")
    if pua_count >= 5 or (pua_count / max(n_chars, 1)) > 0.03:
        return True

    # 3. Scrambled CMap / Type 3 font without ToUnicode: high non-alphanumeric ratio
    alpha_chars = sum(1 for c in raw_text if c.isalnum())
    symbol_chars = sum(1 for c in raw_text if not c.isalnum() and not c.isspace())
    if n_chars >= 40 and (alpha_chars / max(n_chars, 1)) < 0.35 and symbol_chars > 30:
        return True

    return False


def ocr_page_to_structured(
    page: Any,
    width: float,
    height: float,
    page_num: int,
    scale: float = 2.0,
    model_size: str = "small",
    rec_batch: int = 32,
) -> dict[str, Any]:
    """Rasterize PDF page at scale 2.0x and execute faster-paddle OCR.
    
    Preserves text, bounding boxes mapped back to PDF user space (points, bottom-left origin),
    confidence score, and provenance='ocr'.
    """
    t0 = time.perf_counter()

    # 1. Rasterize with PDFium
    bitmap = page.render(scale=scale)
    img = bitmap.to_pil()

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    # 2. Run faster-paddle OCR
    engine = get_ocr_engine(model_size=model_size, rec_batch=rec_batch)
    res = engine.ocr(png_bytes)
    t_ocr = (time.perf_counter() - t0) * 1000

    bounds = res.get("bounds", {})

    lines_out: list[dict[str, Any]] = []
    blocks_out: list[dict[str, Any]] = []
    source_refs: list[dict[str, Any]] = []

    # Sort items geometrically: top-to-bottom (Y bucketed), then left-to-right (X)
    sorted_items = sorted(
        bounds.values(),
        key=lambda item: (item.get("topLeftCoord", [0, 0])[1] // 15, item.get("topLeftCoord", [0, 0])[0]),
    )
    md_paragraphs: list[str] = []

    for idx, item in enumerate(sorted_items, start=1):
        top_left = item.get("topLeftCoord", [0, 0])
        bottom_right = item.get("bottomRightCoord", [0, 0])
        line_text = item.get("text", "").strip()
        conf = float(item.get("confidence", 0.0))

        if not line_text:
            continue

        md_paragraphs.append(line_text)

        # PDF user space coords (bottom-left origin, points):
        x0 = round(top_left[0] / scale, 2)
        y0 = round(height - (bottom_right[1] / scale), 2)
        x1 = round(bottom_right[0] / scale, 2)
        y1 = round(height - (top_left[1] / scale), 2)

        lines_out.append({
            "line_id": idx,
            "text": line_text,
            "bbox": [x0, y0, x1, y1],
            "confidence": round(conf, 4),
            "font_size": 11.0,
            "is_bold": False,
            "is_italic": False,
            "raw_line_id": idx,
            "provenance": "ocr",
            "source": "ocr_faster_paddle",
        })

        blocks_out.append({
            "block_id": idx,
            "type_candidate": "paragraph",
            "text": line_text,
            "bbox": [x0, y0, x1, y1],
            "confidence": round(conf, 4),
            "font_size": 11.0,
            "is_bold": False,
            "is_italic": False,
            "provenance": "ocr",
            "source": "ocr_faster_paddle",
            "flow_kind": "PROSE",
            "source_line_ids": [idx],
        })

        source_refs.append({
            "page": page_num,
            "source": "ocr_faster_paddle",
            "provenance": "ocr",
            "bbox": [x0, y0, x1, y1],
            "confidence": round(conf, 4),
        })

    formatted_md = "\n\n".join(md_paragraphs).strip()

    return {
        "page": page_num,
        "text": formatted_md,
        "logical_text": formatted_md,
        "lines": lines_out,
        "blocks": blocks_out,
        "furniture": [],
        "source_refs": source_refs,
        "tables": [],
        "has_images": True,
        "quality": "OCR_RECOVERED",
        "fallback_status": "OCR_APPLIED",
        "provenance": "ocr",
        "engine_used": f"faster_paddle_{model_size}",
        "timing_ocr_ms": round(t_ocr, 2),
        "page_geometry": {"width": width, "height": height},
    }
