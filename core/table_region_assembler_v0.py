"""Offline diagnostic prototype for candidate table regions.

This script reads only ``page_structures.structure_json`` from a SQLite URI opened
read-only.  It does not modify the canonical pipeline, ``pages.content``, model,
or database.  Its output is diagnostic JSON only: candidate regions, boundary
probabilities, and the physical evidence that made (or rejected) each candidate.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

try:
    from core.runtime_paths import index_db_path
except ModuleNotFoundError:
    from runtime_paths import index_db_path
from statistics import median
from typing import Any

import numpy as np
import onnxruntime as ort

# Permit direct execution from ``scripts/`` without changing the environment.
THEMIS_ROOT = Path(__file__).resolve().parents[1]
if str(THEMIS_ROOT) not in sys.path:
    sys.path.insert(0, str(THEMIS_ROOT))

from core.paragraph_boundary_engine import (
    MODEL_PATH_DEFAULT,
    LineGeom,
    build_adjacent_pairs_from_lines,
    extract_32_features,
)


TABLE_SEED_THRESHOLD = 0.55
STRONG_THRESHOLD = 0.70
HORIZONTAL_BAND_TOLERANCE_FACTOR = 0.45
FIRST_LINE_INDENT_MIN = 12.0
FIRST_LINE_INDENT_MAX = 48.0


def _softmax_probability(logits: np.ndarray, positive_index: int = 1) -> float:
    shifted = logits - np.max(logits)
    probs = np.exp(shifted) / np.sum(np.exp(shifted))
    return float(probs[positive_index])


def _bbox(value: Any) -> tuple[float, float, float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    try:
        x0, y0, x1, y1 = (float(part) for part in value)
    except (TypeError, ValueError):
        return None
    return (x0, y0, x1, y1) if x1 >= x0 and y1 >= y0 else None


@dataclass(frozen=True)
class PageLine:
    index: int
    line_id: int
    text: str
    bbox: tuple[float, float, float, float]
    font_size: float
    is_bold: bool
    is_italic: bool

    @property
    def x0(self) -> float:
        return self.bbox[0]

    @property
    def y0(self) -> float:
        return self.bbox[1]

    @property
    def x1(self) -> float:
        return self.bbox[2]

    @property
    def y1(self) -> float:
        return self.bbox[3]

    @property
    def y_center(self) -> float:
        return (self.y0 + self.y1) / 2.0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def is_regular_text_geometry(self) -> bool:
        # PDF decoration or a marginal glyph can have a page-height bbox;
        # it is not evidence of a textual table row.
        return self.height <= self.font_size * 2.5


def _page_lines(structure: dict[str, Any]) -> list[PageLine]:
    result: list[PageLine] = []
    for index, item in enumerate(structure.get("lines") or []):
        if not isinstance(item, dict):
            continue
        bbox = _bbox(item.get("bbox"))
        text = item.get("text")
        if bbox is None or not isinstance(text, str) or not text.strip():
            continue
        result.append(PageLine(
            index=index,
            line_id=int(item.get("raw_line_id", item.get("line_id", index + 1))),
            text=text.strip(),
            bbox=bbox,
            font_size=max(1.0, float(item.get("font_size") or 12.0)),
            is_bold=bool(item.get("is_bold")),
            is_italic=bool(item.get("is_italic")),
        ))
    return result


def _page_geometry(structure: dict[str, Any]) -> tuple[float, float]:
    geometry = structure.get("page_geometry") or {}
    return (max(100.0, float(geometry.get("width") or 595.0)), max(100.0, float(geometry.get("height") or 842.0)))


def _horizontal_evidence(
    lines: list[PageLine],
    glyph_runs_by_raw_line: dict[int, list[Any]] | None = None,
    *,
    allow_text_whitespace_evidence: bool = True,
) -> list[dict[str, Any]]:
    """Find same-baseline components and preserve physical gaps between them."""
    if not lines:
        return []
    typical_font = median(line.font_size for line in lines)
    tolerance = max(2.0, typical_font * HORIZONTAL_BAND_TOLERANCE_FACTOR)
    result: list[dict[str, Any]] = []
    for line in lines:
        peers = sorted(
            (peer for peer in lines if peer.is_regular_text_geometry and abs(peer.y_center - line.y_center) <= tolerance),
            key=lambda peer: peer.x0,
        )
        gaps = [
            round(right.x0 - left.x1, 2)
            for left, right in zip(peers, peers[1:])
            if right.x0 > left.x1
        ]
        whitespace_runs = [len(match.group(0)) for match in re.finditer(r"[ \t]{2,}", line.text)] if allow_text_whitespace_evidence else []
        glyph_runs = (glyph_runs_by_raw_line or {}).get(line.line_id, [])
        glyph_run_records = [
            {
                "text": run.text,
                "bbox": [round(value, 2) for value in run.bbox],
                "gap_before": round(float(run.gap_before), 2) if run.gap_before is not None else None,
                "gap_before_normalized": round(float(run.gap_before_normalized), 3) if run.gap_before_normalized is not None else None,
            }
            for run in glyph_runs
        ]
        intraline_gaps = [float(run.gap_before) for run in glyph_runs if run.gap_before is not None]
        has_glyph_columnar_gap = len(glyph_runs) >= 2 and bool(intraline_gaps)
        result.append({
            "same_baseline_components": len(peers),
            "horizontal_gaps": gaps,
            "max_horizontal_gap": round(max(gaps, default=0.0), 2),
            "intra_line_whitespace_runs": whitespace_runs,
            "has_columnar_gap": len(peers) >= 2 and max(gaps, default=0.0) >= max(12.0, typical_font * 1.25),
            "has_intra_line_gap": bool(whitespace_runs) or has_glyph_columnar_gap,
            "glyph_run_count": len(glyph_runs),
            "glyph_runs": glyph_run_records,
            "intraline_gaps": [round(gap, 2) for gap in intraline_gaps],
            "has_glyph_columnar_gap": has_glyph_columnar_gap,
        })
    return result


def _boundary_scores(lines: list[PageLine], page_width: float, page_height: float, session: ort.InferenceSession) -> list[dict[str, Any]]:
    geoms = [LineGeom(line.text, line.bbox, line.font_size, line.is_bold, line.is_italic, raw_line_id=line.line_id) for line in lines]
    pairs = build_adjacent_pairs_from_lines(geoms)
    if not pairs:
        return []
    features = np.array([
        extract_32_features(pair, prev_line=geoms[index - 1].text if index else "", next_line=geoms[index + 2].text if index + 2 < len(geoms) else "", page_w=page_width, page_h=page_height)
        for index, pair in enumerate(pairs)
    ], dtype=np.float32)
    boundary_prob, aux_is_table = session.run(["boundary_prob", "aux_is_table"], {"geom_features": features})
    return [{
        "between_line_indexes": [index, index + 1],
        "between_line_ids": [lines[index].line_id, lines[index + 1].line_id],
        "p_continue": round(float(boundary_prob[index][0]), 5),
        "p_break": round(float(boundary_prob[index][1]), 5),
        # aux_is_table is logits, unlike boundary_prob; convert it to P(table).
        "p_table": round(_softmax_probability(aux_is_table[index]), 5),
    } for index in range(len(pairs))]


def _annotate_recurring_glyph_alignments(horizontal: list[dict[str, Any]], tolerance: float = 12.0) -> None:
    """Attach cross-row X recurrence using geometry only.

    A candidate run aligns when another physical raw line starts in the same X
    band.  Text is deliberately absent from this decision.
    """
    starts = [
        (line_index, float(run["bbox"][0]))
        for line_index, evidence in enumerate(horizontal)
        for run in evidence["glyph_runs"]
    ]
    for line_index, evidence in enumerate(horizontal):
        aligned = 0
        for run in evidence["glyph_runs"]:
            x0 = float(run["bbox"][0])
            if any(other_index != line_index and abs(other_x0 - x0) <= tolerance for other_index, other_x0 in starts):
                aligned += 1
        evidence["recurring_x_alignment_count"] = aligned
        evidence["has_recurring_x_alignment"] = aligned > 0


def _union_bbox(lines: list[PageLine]) -> list[float]:
    return [
        round(min(line.x0 for line in lines), 2), round(min(line.y0 for line in lines), 2),
        round(max(line.x1 for line in lines), 2), round(max(line.y1 for line in lines), 2),
    ]


def assemble_page(
    structure: dict[str, Any],
    session: ort.InferenceSession,
    glyph_runs_by_raw_line: dict[int, list[Any]] | None = None,
    *,
    require_glyph_alignment: bool = False,
) -> dict[str, Any]:
    """Assemble only diagnostics for one physical page; no text is rewritten."""
    lines = _page_lines(structure)
    page_width, page_height = _page_geometry(structure)
    horizontal = _horizontal_evidence(
        lines,
        glyph_runs_by_raw_line,
        allow_text_whitespace_evidence=glyph_runs_by_raw_line is None,
    )
    if glyph_runs_by_raw_line is not None:
        _annotate_recurring_glyph_alignments(horizontal)
    boundaries = _boundary_scores(lines, page_width, page_height, session)
    line_scores = [0.0 for _ in lines]
    for boundary in boundaries:
        for index in boundary["between_line_indexes"]:
            line_scores[index] = max(line_scores[index], boundary["p_table"])

    left_baseline = median(line.x0 for line in lines) if lines else 0.0
    candidate_flags: list[bool] = []
    rejected: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        geom = horizontal[index]
        has_columnar_geometry = geom["has_columnar_gap"] or geom["has_intra_line_gap"]
        if require_glyph_alignment and geom["has_glyph_columnar_gap"]:
            has_columnar_geometry = has_columnar_geometry and geom["has_recurring_x_alignment"]
        candidate_flags.append(line.is_regular_text_geometry and line_scores[index] >= TABLE_SEED_THRESHOLD and has_columnar_geometry)
        if line_scores[index] >= TABLE_SEED_THRESHOLD and not has_columnar_geometry:
            indent = line.x0 - left_baseline
            rejected.append({
                "line_ids": [line.line_id],
                "reason": "non_text_geometry" if not line.is_regular_text_geometry else ("isolated_first_line_indent" if FIRST_LINE_INDENT_MIN <= indent <= FIRST_LINE_INDENT_MAX else "model_activation_without_columnar_geometry"),
                "evidence": {
                    "p_table": round(line_scores[index], 5),
                    "first_line_indent": round(float(indent), 2),
                    "same_baseline_components": geom["same_baseline_components"],
                },
            })

    typical_leading = median(
        [lines[index].y0 - lines[index + 1].y1 for index in range(len(lines) - 1) if 0.0 <= lines[index].y0 - lines[index + 1].y1 <= 40.0] or [14.0]
    )
    regions: list[dict[str, Any]] = []
    baseline_tolerance = max(2.0, median(line.font_size for line in lines) * HORIZONTAL_BAND_TOLERANCE_FACTOR) if lines else 2.0
    index = 0
    while index < len(lines):
        if not candidate_flags[index]:
            index += 1
            continue
        end = index
        while end + 1 < len(lines) and candidate_flags[end + 1]:
            baseline_delta = lines[end].y_center - lines[end + 1].y_center
            same_baseline = abs(baseline_delta) <= baseline_tolerance
            next_row = 0.0 < baseline_delta <= max(typical_leading * 3.0, lines[end].font_size * 2.5)
            if not (same_baseline or next_row):
                break
            end += 1
        members = lines[index:end + 1]
        member_geom = horizontal[index:end + 1]
        member_scores = line_scores[index:end + 1]
        columnar_lines = sum(1 for evidence in member_geom if evidence["has_columnar_gap"] or evidence["has_intra_line_gap"])
        baseline_centers: list[float] = []
        for line in members:
            if not any(abs(line.y_center - center) <= baseline_tolerance for center in baseline_centers):
                baseline_centers.append(line.y_center)
        row_band_count = len(baseline_centers)
        marginal = any(
            (line.x1 - line.x0) <= page_width * 0.20
            and (line.y1 >= page_height * 0.95 or line.y0 <= page_height * 0.05 or line.x0 <= page_width * 0.04 or line.x1 >= page_width * 0.96)
            for line in members
        )
        first_indent = members[0].x0 - left_baseline
        isolated_indent = len(members) == 1 and FIRST_LINE_INDENT_MIN <= first_indent <= FIRST_LINE_INDENT_MAX and columnar_lines == 0
        evidence = {
            "mean_p_table": round(float(sum(member_scores) / len(member_scores)), 5),
            "max_p_table": round(max(member_scores), 5),
            "columnar_line_count": columnar_lines,
            "row_band_count": row_band_count,
            "typical_leading": round(float(typical_leading), 2),
            "first_line_indent": round(float(first_indent), 2),
            "marginal_geometry": marginal,
        }
        if len(members) < 2:
            reason = "isolated_first_line_indent" if isolated_indent else "isolated_activation"
            rejected.append({"line_ids": [line.line_id for line in members], "reason": reason, "evidence": evidence})
        elif marginal:
            rejected.append({"line_ids": [line.line_id for line in members], "reason": "marginal_element", "evidence": evidence})
        elif columnar_lines < 2:
            rejected.append({"line_ids": [line.line_id for line in members], "reason": "insufficient_repeated_columnar_geometry", "evidence": evidence})
        elif row_band_count < 2:
            rejected.append({"line_ids": [line.line_id for line in members], "reason": "single_row_column_layout", "evidence": evidence})
        else:
            confidence = "strong" if evidence["mean_p_table"] >= STRONG_THRESHOLD and len(members) >= 3 else "ambiguous"
            regions.append({
                "bbox": _union_bbox(members),
                "line_ids": [line.line_id for line in members],
                "line_indexes": [line.index for line in members],
                "confidence": confidence,
                "boundary_probabilities": [boundary for boundary in boundaries if index <= boundary["between_line_indexes"][0] <= end],
                "geometry_evidence": evidence,
                "line_evidence": [{"line_id": line.line_id, "p_table": round(line_scores[pos], 5), **horizontal[pos]} for pos, line in enumerate(lines) if index <= pos <= end],
            })
        index = end + 1

    return {
        "page": structure.get("page"),
        "page_geometry": {"width": page_width, "height": page_height},
        # Complete per-line evidence is diagnostic-only.  V2 uses it to let
        # the existing spatial merger reconnect non-adjacent PDFium rows.
        "line_diagnostics": [
            {
                "line_id": line.line_id,
                "line_index": line.index,
                "bbox": _union_bbox([line]),
                "p_table": round(line_scores[index], 5),
                **horizontal[index],
            }
            for index, line in enumerate(lines)
        ],
        "boundary_count": len(boundaries),
        "boundaries": boundaries,
        "candidate_regions": regions,
        "rejected_activations": rejected,
    }


def _iter_pages(db: sqlite3.Connection, process_id: str):
    rows = db.execute("""
        SELECT p.document_id, p.page_number, ps.structure_json
        FROM docket_snapshots ds
        JOIN docket_documents dd ON dd.snapshot_id=ds.snapshot_id
        JOIN pages p ON p.document_id=dd.document_id
        JOIN page_structures ps ON ps.page_id=p.page_id
        WHERE ds.process_id=?
          AND ds.created_at=(SELECT MAX(created_at) FROM docket_snapshots WHERE process_id=?)
        ORDER BY dd.ordinal, p.page_number
    """, (process_id, process_id))
    yield from rows


def analyze_process(db: sqlite3.Connection, process_id: str, session: ort.InferenceSession) -> dict[str, Any]:
    pages: list[dict[str, Any]] = []
    for row in _iter_pages(db, process_id):
        diagnostic = assemble_page(json.loads(row["structure_json"]), session)
        diagnostic["document_id"] = row["document_id"]
        diagnostic["pdf_page"] = row["page_number"]
        pages.append(diagnostic)
    regions = [region for page in pages for region in page["candidate_regions"]]
    rejected = [item for page in pages for item in page["rejected_activations"]]
    return {
        "process_id": process_id,
        "page_count": len(pages),
        "pages_affected": sum(bool(page["candidate_regions"]) for page in pages),
        "candidate_region_count": len(regions),
        "region_confidence_counts": dict(Counter(region["confidence"] for region in regions)),
        "rejected_activation_count": len(rejected),
        "samples": {
            "strong": [region for region in regions if region["confidence"] == "strong"][:3],
            "ambiguous": [region for region in regions if region["confidence"] == "ambiguous"][:3],
            "rejected": rejected[:3],
        },
        "pages": pages,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=index_db_path())
    parser.add_argument("--process", action="append", dest="processes", default=["1029994-43.2023.8.26.0554", "1000045-87.2026.8.26.0450"])
    parser.add_argument("--output", type=Path, default=Path("scratch/table_region_assembler_v0.json"))
    args = parser.parse_args()

    db_uri = args.db.resolve().as_uri() + "?mode=ro&immutable=1"
    db = sqlite3.connect(db_uri, uri=True)
    db.row_factory = sqlite3.Row
    session = ort.InferenceSession(str(MODEL_PATH_DEFAULT), providers=["CPUExecutionProvider"])
    try:
        process_results = [analyze_process(db, process_id, session) for process_id in args.processes]
    finally:
        db.close()
    output = {
        "prototype": "THEMIS-TABLE-REGION-ASSEMBLER-V0",
        "mode": "offline-read-only",
        "model": MODEL_PATH_DEFAULT.name,
        "thresholds": {"table_seed": TABLE_SEED_THRESHOLD, "strong": STRONG_THRESHOLD},
        "processes": process_results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    for process in process_results:
        print(f"{process['process_id']}: {process['candidate_region_count']} regiões em {process['pages_affected']} páginas; {process['rejected_activation_count']} ativações rejeitadas")
    print(f"JSON: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
