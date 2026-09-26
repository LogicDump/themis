"""Offline V2.1 instance-aware table-region assembler with transient PDFium glyph geometry.

This layer refines V2 spatial fragments into strictly separated physical table instances:
- Resolves cross-instance false merges (e.g. multi-holerite pages, separate IRPF sections);
- Recovers internal form splits (e.g. pay stub body to bases across internal whitespace);
- Isolates and rejects marginal chancela footers and signature blocks without tabular data matrix;
- Preserves 100% of aux_is_table, transient glyph runs, and spatial seed promotions.

The canonical database is opened immutable/read-only. Neither ``pages.content`` nor
``structure_json`` is modified.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

try:
    from core.runtime_paths import index_db_path
except ModuleNotFoundError:
    from runtime_paths import index_db_path
from typing import Any

import onnxruntime as ort
import pypdfium2 as pdfium

THEMIS_ROOT = Path(__file__).resolve().parents[1]
if str(THEMIS_ROOT) not in sys.path:
    sys.path.insert(0, str(THEMIS_ROOT))

from core.pdfium_structuralizer import extract_page_glyph_runs
from core import table_region_assembler_v0 as v0
from core import table_region_assembler_v1 as v1
from core import table_region_assembler_v2 as v2


def _source_path(db: sqlite3.Connection, data_root: Path, document_id: str) -> Path:
    canonical = data_root / "documentos" / document_id / "source.pdf"
    if canonical.is_file():
        return canonical
    row = db.execute("SELECT path FROM files WHERE sha256=?", (document_id,)).fetchone()
    return Path(row["path"]) if row and row["path"] else canonical


def _glyph_runs_for_page(
    documents: dict[str, Any], db: sqlite3.Connection, data_root: Path, document_id: str, pdf_page: int,
) -> tuple[dict[int, list[Any]], str | None]:
    path = _source_path(db, data_root, document_id)
    if not path.is_file():
        return {}, f"source_not_found:{path}"
    try:
        document = documents.setdefault(document_id, pdfium.PdfDocument(str(path)))
        page = document.get_page(pdf_page - 1)
        try:
            textpage = page.get_textpage()
            return extract_page_glyph_runs(page.raw, textpage.raw, pdf_page), None
        finally:
            page.close()
    except Exception as exc:
        return {}, f"pdfium:{type(exc).__name__}:{exc}"


def _bbox_gap(a: list[float], b: list[float]) -> tuple[float, float, float]:
    h_gap = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
    v_gap = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    h_overlap = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    return h_gap, v_gap, h_overlap


def _union_bbox(regions: list[dict[str, Any]]) -> list[float]:
    boxes = [region["bbox"] for region in regions]
    return [
        round(min(box[0] for box in boxes), 2), round(min(box[1] for box in boxes), 2),
        round(max(box[2] for box in boxes), 2), round(max(box[3] for box in boxes), 2),
    ]


class _UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        left, right = self.find(left), self.find(right)
        if left != right:
            self.parent[right] = left


def _is_regular_body_line(l: dict[str, Any], page_w: float, page_h: float) -> bool:
    """Ignore full-page vertical margin stamps and extreme right edge chancelas."""
    bbox = l["bbox"]
    h = bbox[3] - bbox[1]
    if h >= page_h * 0.40:
        return False
    if bbox[0] >= page_w * 0.88:
        return False
    return True


def _shared_column_anchors(a: dict[str, Any], b: dict[str, Any], tolerance: float = 8.0) -> int:
    """Count how many column X-starts are shared between fragments a and b."""
    a_anchors = [float(run["bbox"][0]) for line in a.get("line_evidence", []) for run in line.get("glyph_runs", [])]
    b_anchors = [float(run["bbox"][0]) for line in b.get("line_evidence", []) for run in line.get("glyph_runs", [])]
    if not a_anchors or not b_anchors:
        return 0
    shared = 0
    for ax in set(round(x, 1) for x in a_anchors):
        if any(abs(ax - bx) <= tolerance for bx in b_anchors):
            shared += 1
    return shared


def _has_intervening_barrier(
    box_a: list[float],
    box_b: list[float],
    frag_a: dict[str, Any],
    frag_b: dict[str, Any],
    lines: list[dict[str, Any]],
    page_w: float,
    page_h: float,
) -> tuple[bool, str | None]:
    """Check if between box_a and box_b there is a geometric instance barrier."""
    y_top_bot = max(box_a[1], box_b[1])  # lower edge of upper box
    y_bot_top = min(box_a[3], box_b[3])  # upper edge of lower box

    if y_top_bot <= y_bot_top:
        return False, None

    v_gap = y_top_bot - y_bot_top

    intervening = [
        l for l in lines
        if _is_regular_body_line(l, page_w, page_h)
        and l["bbox"][1] >= y_bot_top - 2.0
        and l["bbox"][3] <= y_top_bot + 2.0
    ]
    if not intervening:
        return False, None

    # 1. Non-tabular prose / section separator:
    # If gap is large (> 60 pt), any line with P(table) < 0.40 is an instance barrier
    # If gap is compact (<= 60 pt), require strict prose P(table) < 0.20
    if v_gap > 60.0:
        low_p_lines = [l for l in intervening if l["p_table"] < 0.40]
        if low_p_lines:
            return True, f"intervening_low_p_table_line (count={len(low_p_lines)}, min_p={min(l['p_table'] for l in low_p_lines):.3f})"
    else:
        strict_low_p = [l for l in intervening if l["p_table"] < 0.20]
        if strict_low_p:
            return True, f"intervening_strict_low_p_line (count={len(strict_low_p)})"

    # 2. Multi-form separator across mid-page boundary (e.g. upper stub to lower stub)
    crossing_midpage = (box_a[1] >= page_h * 0.48 and box_b[3] <= page_h * 0.48) or (box_b[1] >= page_h * 0.48 and box_a[3] <= page_h * 0.48)
    if crossing_midpage and v_gap >= 40.0:
        shared_cols = _shared_column_anchors(frag_a, frag_b)
        if shared_cols < 3:
            return True, "intervening_multiform_page_divider"

    # 3. Bottom marginal chancela isolation:
    # A single-run / text-only fragment at bottom margin (y_max <= 0.15 * H) must not merge across gap >= 30 pt
    bot_frag = frag_a if box_a[3] < box_b[3] else frag_b
    if min(box_a[3], box_b[3]) <= page_h * 0.15:
        bot_runs = sum(l.get("glyph_run_count", 0) for l in bot_frag.get("line_evidence", []))
        bot_anchors = _shared_column_anchors(bot_frag, bot_frag)
        if bot_runs <= 2 or bot_anchors <= 2:
            if v_gap >= 30.0:
                return True, "bottom_marginal_chancela_isolation"

    return False, None


def _is_signature_or_chancela_fp(region: dict[str, Any], page_w: float, page_h: float) -> bool:
    """Detect isolated marginal signature / chancela blocks without tabular data matrix."""
    bbox = region["bbox"]
    y_min, y_max = bbox[1], bbox[3]
    h = y_max - y_min
    lines = region.get("line_evidence", [])

    # Bottom margin check: y_max <= 0.15 * page_h (~126 pt)
    if y_max <= page_h * 0.15:
        if len(lines) <= 3 or h <= 65.0:
            total_runs = sum(l.get("glyph_run_count", 0) for l in lines)
            if total_runs <= 6:
                return True

    # Top margin check: y_min >= 0.92 * page_h and height <= 45 pt
    if y_min >= page_h * 0.92 and len(lines) <= 2:
        return True

    return False


def _connection_v2_1(
    a: dict[str, Any],
    b: dict[str, Any],
    lines: list[dict[str, Any]],
    page_w: float,
    page_h: float,
) -> tuple[bool, dict[str, Any]]:
    h_gap, v_gap, h_overlap = _bbox_gap(a["bbox"], b["bbox"])
    a_width = max(1.0, a["bbox"][2] - a["bbox"][0])
    b_width = max(1.0, b["bbox"][2] - b["bbox"][0])
    overlap_ratio = h_overlap / min(a_width, b_width)

    same_row_band = v_gap <= max(8.0, page_h * 0.015)

    # 1. Check intervening barrier
    has_barrier, barrier_reason = _has_intervening_barrier(a["bbox"], b["bbox"], a, b, lines, page_w, page_h)
    if has_barrier:
        return False, {
            "horizontal_gap": round(h_gap, 2),
            "vertical_gap": round(v_gap, 2),
            "horizontal_overlap_ratio": round(overlap_ratio, 3),
            "same_row_band": same_row_band,
            "reason": f"barrier_blocked:{barrier_reason}",
        }

    # 2. Side-by-side compatible (in the same row band)
    side_by_side_compatible = same_row_band and h_gap <= page_w * 0.20

    # 3. Stacked compatible
    y_top_bot = max(a["bbox"][1], b["bbox"][1])
    y_bot_top = min(a["bbox"][3], b["bbox"][3])

    intervening_non_tabular = [
        l for l in lines
        if _is_regular_body_line(l, page_w, page_h)
        and l["bbox"][1] >= y_bot_top - 2.0
        and l["bbox"][3] <= y_top_bot + 2.0
        and l["p_table"] < 0.40
    ]

    # If all intervening lines are tabular (or no intervening lines), allow up to 0.22 * page_h (~185 pt)
    max_v_gap = page_h * 0.22 if not intervening_non_tabular else page_h * 0.18

    stacked_compatible = v_gap <= max_v_gap and overlap_ratio >= 0.20

    connected = (stacked_compatible or side_by_side_compatible)
    return connected, {
        "horizontal_gap": round(h_gap, 2),
        "vertical_gap": round(v_gap, 2),
        "horizontal_overlap_ratio": round(overlap_ratio, 3),
        "same_row_band": same_row_band,
        "reason": "stacked_shared_x" if stacked_compatible else ("same_row_horizontal_proximity" if side_by_side_compatible else "not_compatible"),
    }


def merge_page(diagnostic: dict[str, Any]) -> dict[str, Any]:
    fragments = diagnostic["candidate_regions"]
    page_w = float(diagnostic["page_geometry"]["width"])
    page_h = float(diagnostic["page_geometry"]["height"])
    lines = diagnostic.get("line_diagnostics", [])

    union_find = _UnionFind(len(fragments))
    merge_events: list[dict[str, Any]] = []
    prevented_merges: list[dict[str, Any]] = []

    for left in range(len(fragments)):
        for right in range(left + 1, len(fragments)):
            connected, evidence = _connection_v2_1(
                fragments[left], fragments[right], lines, page_w, page_h
            )
            if connected:
                union_find.union(left, right)
                merge_events.append({"fragments": [left, right], **evidence})
            else:
                prevented_merges.append({"fragments": [left, right], **evidence})

    components: dict[int, list[dict[str, Any]]] = {}
    for index, fragment in enumerate(fragments):
        components.setdefault(union_find.find(index), []).append(fragment)

    regions: list[dict[str, Any]] = []
    rejected = list(diagnostic["rejected_activations"])

    for component in components.values():
        line_ids = sorted({line_id for fragment in component for line_id in fragment["line_ids"]})
        strong_parts = sum(fragment["confidence"] == "strong" for fragment in component)
        mean_probability = sum(fragment["geometry_evidence"]["mean_p_table"] for fragment in component) / len(component)

        comp_evidence = {
            "mean_p_table": round(mean_probability, 5),
            "line_evidence": [line for fragment in component for line in fragment.get("line_evidence", [])]
        }
        cand_region = {
            "bbox": _union_bbox(component),
            "line_ids": line_ids,
            "confidence": "strong" if strong_parts or (len(component) >= 3 and mean_probability >= v0.STRONG_THRESHOLD) else "ambiguous",
            "fragment_count": len(component),
            "mean_p_table": round(mean_probability, 5),
            "line_evidence": comp_evidence["line_evidence"],
            "geometry_evidence": {
                "merge_basis": "2d_instance_aware_assembler_v2_1",
                "source_fragment_bboxes": [fragment["bbox"] for fragment in component],
            },
        }

        # 1. Single non-strong fragment rejection
        if len(component) == 1 and component[0]["confidence"] != "strong":
            rejected.append({
                "line_ids": line_ids,
                "reason": "isolated_spatial_component",
                "evidence": {"mean_p_table": round(mean_probability, 5), "fragment_count": 1},
            })
            continue

        # 2. Check if it is a marginal signature/chancela FP
        if _is_signature_or_chancela_fp(cand_region, page_w, page_h):
            rejected.append({
                "line_ids": line_ids,
                "reason": "marginal_signature_or_chancela_block",
                "evidence": {"bbox": cand_region["bbox"], "line_count": len(line_ids)},
            })
            continue

        regions.append(cand_region)

    result = dict(diagnostic)
    result["candidate_regions"] = sorted(regions, key=lambda item: (item["bbox"][1], item["bbox"][0]))
    result["rejected_activations"] = rejected
    result["spatial_merge_events"] = merge_events
    result["prevented_merges"] = prevented_merges
    return result


def analyze_process(
    db: sqlite3.Connection, process_id: str, session: ort.InferenceSession, data_root: Path,
) -> dict[str, Any]:
    documents: dict[str, Any] = {}
    pages: list[dict[str, Any]] = []
    unavailable: list[dict[str, Any]] = []
    try:
        for row in v0._iter_pages(db, process_id):
            glyph_runs, error = _glyph_runs_for_page(documents, db, data_root, row["document_id"], int(row["page_number"]))
            if error:
                unavailable.append({"document_id": row["document_id"], "pdf_page": row["page_number"], "reason": error})
            diagnostic = v0.assemble_page(
                json.loads(row["structure_json"]),
                session,
                glyph_runs,
                require_glyph_alignment=True,
            )
            diagnostic["document_id"] = row["document_id"]
            diagnostic["pdf_page"] = row["page_number"]
            diagnostic["glyph_seed_fragment_count"] = v2._promote_spatial_glyph_seeds(diagnostic)
            diagnostic["glyph_geometry"] = v2._glyph_summary(diagnostic)
            pages.append(merge_page(diagnostic))
    finally:
        for document in documents.values():
            document.close()

    regions = [region for page in pages for region in page["candidate_regions"]]
    rejected = [item for page in pages for item in page["rejected_activations"]]
    return {
        "process_id": process_id,
        "page_count": len(pages),
        "candidate_region_count": len(regions),
        "pages_affected": sum(bool(page["candidate_regions"]) for page in pages),
        "region_confidence_counts": dict(Counter(region["confidence"] for region in regions)),
        "rejected_activation_count": len(rejected),
        "source_pages_unavailable": unavailable,
        "pages": pages,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=index_db_path())
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--process", action="append", dest="processes")
    parser.add_argument("--output", type=Path, default=Path("scratch/table_region_assembler_v2_1.json"))
    args = parser.parse_args()

    data_root = args.data_root or args.db.resolve().parent.parent
    processes = args.processes or ["1029994-43.2023.8.26.0554", "1000045-87.2026.8.26.0450"]
    db = sqlite3.connect(args.db.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    db.row_factory = sqlite3.Row
    session = ort.InferenceSession(str(v0.MODEL_PATH_DEFAULT), providers=["CPUExecutionProvider"])
    try:
        results = [analyze_process(db, process_id, session, data_root) for process_id in processes]
    finally:
        db.close()

    output = {
        "prototype": "THEMIS-TABLE-REGION-ASSEMBLER-V2.1",
        "mode": "offline-read-only",
        "glyph_contract": "transient PDFium GlyphRun only; never persisted",
        "model": v0.MODEL_PATH_DEFAULT.name,
        "comparison_base": "THEMIS-TABLE-REGION-ASSEMBLER-V2",
        "processes": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    for process in results:
        print(f"{process['process_id']}: V2.1 {process['candidate_region_count']} regiões em {process['pages_affected']} páginas ({process['rejected_activation_count']} rejeições)")
    print(f"JSON: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
