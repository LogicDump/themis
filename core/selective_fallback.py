"""Selective Fallback Architecture: PDFium -> Heron ONNX.

This module evaluates objective confidence signals on the fast PDFium structuralizer
output using weighted multi-signal combinations and geometric guardrails.
"""
from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium

from core.pdfium_structuralizer import (
    extract_page_structure,
    _is_marginal_furniture,
    sanitize_forensic_text,
    LineInfo,
)
from core.heron_layout_adapter import HeronLayoutDetector, heron_pdfium_structuralize_page

logger = logging.getLogger("themis.selective_fallback")


@dataclass
class ConfidenceReport:
    is_confident: bool
    confidence_score: float
    triggers: list[str]
    weights: dict[str, float] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)


def _detect_consistent_multi_columns(lines: list[dict[str, Any]], page_width: float) -> tuple[bool, int]:
    """Detect real, consistent multi-column layout using non-overlapping horizontal spans.
    
    Requires at least 4 pairs of parallel lines sharing vertical Y-intervals
    with a clear horizontal gutter between columns.
    """
    if len(lines) < 8:
        return False, 0

    body_lines = [
        l for l in lines
        if l["bbox"][0] > page_width * 0.05 and l["bbox"][2] < page_width * 0.95
    ]
    if len(body_lines) < 8:
        return False, 0

    parallel_pairs = 0
    mid_page = page_width / 2.0

    left_col_lines = []
    right_col_lines = []

    for l in body_lines:
        x0, y0, x1, y1 = l["bbox"]
        if x1 <= mid_page + 20:
            left_col_lines.append(l)
        elif x0 >= mid_page - 20:
            right_col_lines.append(l)

    if len(left_col_lines) >= 3 and len(right_col_lines) >= 3:
        for l_left in left_col_lines:
            ly0, ly1 = l_left["bbox"][1], l_left["bbox"][3]
            for l_right in right_col_lines:
                ry0, ry1 = l_right["bbox"][1], l_right["bbox"][3]
                overlap = min(ly1, ry1) - max(ly0, ry0)
                if overlap > 4.0:
                    parallel_pairs += 1

    is_multi = parallel_pairs >= 4
    return is_multi, parallel_pairs


def evaluate_page_confidence(pdfium_data: dict[str, Any]) -> ConfidenceReport:
    """Evaluate objective signals of low confidence in PDFium page structuralization.
    
    Uses calibrated weighted scoring and checks strictly body blocks and geometric properties.
    """
    triggers: list[str] = []
    weights: dict[str, float] = {}
    
    blocks = pdfium_data.get("blocks", [])
    lines = pdfium_data.get("lines", [])
    raw_text = pdfium_data.get("raw_pdfium_text", "")
    quality = pdfium_data.get("quality", "GOOD")
    geometry = pdfium_data.get("page_geometry", {"width": 595.0, "height": 842.0})
    page_w = geometry.get("width", 595.0)
    page_h = geometry.get("height", 842.0)
    
    if quality in {"EMPTY", "SCANNED"} or len(lines) == 0:
        return ConfidenceReport(
            is_confident=True,
            confidence_score=1.0,
            triggers=[],
            weights={},
            metrics={"reason": "empty_or_scanned"}
        )

    # 1. Body prose blocks & line counts
    prose_blocks = [
        b for b in blocks
        if (b.get("flow_kind") == "PROSE" or b.get("type_candidate") in {"paragraph", "body_paragraph", "prose", "blockquote"})
        and len(b.get("text", "").strip()) > 35
    ]
    total_prose_lines = sum(len(b.get("source_line_ids", [])) for b in prose_blocks)
    non_prose_lines = len(lines) - total_prose_lines
    
    # 2. Line width variance / short line ratio
    body_lines = [
        l for l in lines
        if l.get("bbox", [0, 0, 0, 0])[0] > page_w * 0.05 and l.get("bbox", [0, 0, 0, 0])[2] < page_w * 0.95
    ]
    short_lines = len([l for l in body_lines if (l.get("bbox", [0, 0, 0, 0])[2] - l.get("bbox", [0, 0, 0, 0])[0]) < page_w * 0.40])
    short_line_ratio = (short_lines / len(body_lines)) if len(body_lines) >= 8 else 0.0
    
    # 3. List and numbering elements
    bullet_items = len(re.findall(r"(?:^|\n)\s*[-*•●▪◦·]\s+", raw_text))
    numbered_items = len(re.findall(r"(?:^|\n)\s*(?:\d+[\.\)]|[a-z]\))\s+", raw_text))
    currency_cnt = len(re.findall(r"R\$\s*\d+", raw_text))
    
    # 4. Diagnostics
    diag = pdfium_data.get("paragraph_diagnostics", {})
    s_breaks = len(diag.get("suspicious_breaks", []))
    s_merges = len(diag.get("suspicious_merges", []))
    
    # 5. Parallel multi-column detection
    is_multi_col, parallel_pairs = _detect_consistent_multi_columns(lines, page_w)

    # Calibrated rule evaluations:
    # Rule 1: Complex Bullet Lists (>= 4 bullets in substantial page)
    if bullet_items >= 6 and len(lines) >= 25:
        triggers.append("COMPLEX_LIST_BULLETS")
        weights["COMPLEX_LIST_BULLETS"] = 1.0

    # Rule 2: Key-Value Form / Government Header & Metadata Layout
    if short_line_ratio >= 0.80 and len(lines) >= 20:
        triggers.append("KEY_VALUE_FORM_LAYOUT")
        weights["KEY_VALUE_FORM_LAYOUT"] = 1.0

    # Rule 3: Dense Records / Grid Tables
    if len(lines) >= 60:
        triggers.append("DENSE_RECORDS_TABLE")
        weights["DENSE_RECORDS_TABLE"] = 1.0

    # Rule 4: Dense Non-Prose Structural Indentations / Jurisprudential Citations
    if len(lines) >= 45 and non_prose_lines >= 30:
        triggers.append("DENSE_NON_PROSE_STRUCTURE")
        weights["DENSE_NON_PROSE_STRUCTURE"] = 1.0

    # Rule 5: Ementário / Judicial Quote Flow
    if len(lines) >= 35 and total_prose_lines >= 20:
        if s_breaks >= 6 and short_line_ratio <= 0.15:
            triggers.append("BLOCKQUOTE_SPLIT_FLOW")
            weights["BLOCKQUOTE_SPLIT_FLOW"] = 1.0
        elif s_merges >= 4 and len(lines) >= 40 and len(prose_blocks) >= 15 and short_line_ratio <= 0.30:
            triggers.append("MERGED_TOPIC_FLOW")
            weights["MERGED_TOPIC_FLOW"] = 1.0

    # Rule 6: Real Parallel Multi-Column Layout
    if parallel_pairs >= 6 and len(lines) >= 20:
        triggers.append("MULTI_COLUMN_GUTTER")
        weights["MULTI_COLUMN_GUTTER"] = 1.0

    total_weight = sum(weights.values())
    is_fallback_triggered = (total_weight >= 1.0)
    confidence_score = 0.20 if is_fallback_triggered else 0.95

    return ConfidenceReport(
        is_confident=not is_fallback_triggered,
        confidence_score=confidence_score,
        triggers=triggers,
        weights=weights,
        metrics={
            "total_weight": round(total_weight, 2),
            "lines": len(lines),
            "prose_blocks": len(prose_blocks),
            "prose_lines": total_prose_lines,
            "short_line_ratio": round(short_line_ratio, 2),
            "parallel_pairs": parallel_pairs,
        }
    )



def selective_process_page(
    page: pdfium.PdfPage,
    page_num: int,
    detector: HeronLayoutDetector | None = None,
    force_engine: str | None = None,
    source_resolver: Any | None = None,
) -> dict[str, Any]:
    """Process a single page using official Heron + PDFium Geometric Fusion.
    
    Heron layout detection + PDFium typographic spans is the primary structural
    pipeline of Themis. PDFium heuristic extraction serves as fallback if Heron is disabled.
    """
    t0 = time.perf_counter()
    
    if force_engine == "pdfium":
        raw_page = page.raw
        textpage = page.get_textpage()
        raw_tp = textpage.raw
        pdfium_out = extract_page_structure(raw_page, raw_tp, page_num, source_resolver=source_resolver)
        pdfium_out["engine_used"] = "pdfium"
        pdfium_out["fallback_triggered"] = False
        pdfium_out["timing_total_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        return pdfium_out

    if detector is None:
        try:
            detector = HeronLayoutDetector()
        except Exception as exc:
            logger.warning(f"Could not initialize HeronLayoutDetector: {exc}. Falling back to PDFium heuristic.")
            detector = None

    if detector is not None:
        res = heron_pdfium_structuralize_page(page, page_num, detector, source_resolver=source_resolver)
        res["timing_total_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        return res

    # Fallback to PDFium heuristic structuralizer if Heron is unavailable
    raw_page = page.raw
    textpage = page.get_textpage()
    raw_tp = textpage.raw
    pdfium_out = extract_page_structure(raw_page, raw_tp, page_num, source_resolver=source_resolver)
    pdfium_out["engine_used"] = "pdfium_fallback"
    pdfium_out["fallback_triggered"] = False
    pdfium_out["timing_total_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return pdfium_out


