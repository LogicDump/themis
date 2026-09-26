"""Offline Cell Engine V0: deterministic row, column, and cell reconstruction.

This layer takes table regions from ``table_region_assembler_v2_1.py`` and derives
their internal 2D grid matrix (Table -> Row -> Cell) using transient PDFium GlyphRuns.
Neither ``pages.content`` nor ``structure_json`` is modified.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import asdict, dataclass, field
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
from core import table_region_assembler_v2_1 as v2_1


@dataclass
class CellRecord:
    row_index: int
    col_index: int
    bbox: list[float]  # [x0, y0, x1, y1]
    text: str = ""
    is_empty: bool = False
    source_line_ids: list[int] = field(default_factory=list)
    glyph_run_count: int = 0


@dataclass
class RowRecord:
    row_index: int
    bbox: list[float]
    cells: list[CellRecord] = field(default_factory=list)


@dataclass
class ColumnSlot:
    col_index: int
    x0: float
    x1: float
    anchor_x0: float


@dataclass
class TableInstanceRecord:
    instance_id: str
    document_id: str
    pdf_page: int
    region_bbox: list[float]
    confidence: str
    num_rows: int
    num_cols: int
    column_slots: list[dict[str, Any]]
    rows: list[RowRecord]
    provenance: dict[str, Any]


def _cluster_row_bands(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group glyph runs into baseline row bands sorted from top to bottom (Y descending)."""
    sorted_runs = sorted(runs, key=lambda r: (-(r["bbox"][1] + r["bbox"][3]) / 2.0, r["bbox"][0]))
    bands: list[dict[str, Any]] = []

    for r in sorted_runs:
        yc = (r["bbox"][1] + r["bbox"][3]) / 2.0
        h = max(2.0, r["bbox"][3] - r["bbox"][1])
        placed = False
        for b in bands:
            if abs(yc - b["y_center"]) <= max(3.0, h * 0.45):
                b["runs"].append(r)
                b["y_center"] = sum((x["bbox"][1] + x["bbox"][3]) / 2.0 for x in b["runs"]) / len(b["runs"])
                b["y0"] = min(b["y0"], r["bbox"][1])
                b["y1"] = max(b["y1"], r["bbox"][3])
                placed = True
                break
        if not placed:
            bands.append({
                "y_center": yc,
                "y0": r["bbox"][1],
                "y1": r["bbox"][3],
                "runs": [r],
            })

    for b_idx, b in enumerate(bands):
        b["row_index"] = b_idx
        b["runs"] = sorted(b["runs"], key=lambda r: r["bbox"][0])
        b["bbox"] = [
            round(min(r["bbox"][0] for r in b["runs"]), 2),
            round(b["y0"], 2),
            round(max(r["bbox"][2] for r in b["runs"]), 2),
            round(b["y1"], 2),
        ]
    return bands


def _derive_column_slots(
    runs: list[dict[str, Any]], row_bands: list[dict[str, Any]], region_bbox: list[float],
) -> list[ColumnSlot]:
    """Derive columns by finding recurring horizontal column anchors across row bands."""
    if not runs:
        return [ColumnSlot(0, region_bbox[0], region_bbox[2], region_bbox[0])]

    x0_list = [r["bbox"][0] for r in runs]

    # Cluster X0 starts with 16pt tolerance
    clusters: list[list[float]] = []
    for x in sorted(x0_list):
        if not clusters:
            clusters.append([x])
        elif abs(x - sum(clusters[-1]) / len(clusters[-1])) <= 16.0:
            clusters[-1].append(x)
        else:
            clusters.append([x])

    anchor_candidates = []
    for c in clusters:
        avg_x = sum(c) / len(c)
        band_count = sum(1 for b in row_bands if any(abs(r["bbox"][0] - avg_x) <= 16.0 for r in b["runs"]))
        anchor_candidates.append({
            "anchor": round(avg_x, 2),
            "count": len(c),
            "band_count": band_count,
            "min_x": min(c),
            "max_x": max(c),
        })

    # Merge sub-anchors that are too close (< 35 pt) unless both have multiple row bands
    merged_anchors: list[dict[str, Any]] = []
    for cand in anchor_candidates:
        if not merged_anchors:
            merged_anchors.append(cand)
        elif cand["anchor"] - merged_anchors[-1]["anchor"] < 35.0:
            if cand["band_count"] < 2 or merged_anchors[-1]["band_count"] < 2:
                if cand["band_count"] > merged_anchors[-1]["band_count"]:
                    merged_anchors[-1] = cand
            else:
                merged_anchors.append(cand)
        else:
            merged_anchors.append(cand)

    final_anchors = [a["anchor"] for a in merged_anchors]

    slots: list[ColumnSlot] = []
    for j, a in enumerate(final_anchors):
        if j == 0:
            x0 = region_bbox[0]
        else:
            prev_a = final_anchors[j - 1]
            prev_runs = [r for r in runs if prev_a - 16.0 <= r["bbox"][0] < (a - 10.0)]
            prev_max_x1 = max((r["bbox"][2] for r in prev_runs), default=prev_a + 20.0)
            x0 = (prev_max_x1 + a) / 2.0 if a > prev_max_x1 else (prev_a + a) / 2.0

        if j + 1 < len(final_anchors):
            next_a = final_anchors[j + 1]
            j_runs = [r for r in runs if a - 16.0 <= r["bbox"][0] < (next_a - 10.0)]
            j_max_x1 = max((r["bbox"][2] for r in j_runs), default=a + 20.0)
            x1 = (j_max_x1 + next_a) / 2.0 if next_a > j_max_x1 else (a + next_a) / 2.0
        else:
            x1 = region_bbox[2]

        slots.append(ColumnSlot(
            col_index=j,
            x0=round(x0, 2),
            x1=round(x1, 2),
            anchor_x0=a,
        ))

    slots[0].x0 = min(slots[0].x0, region_bbox[0])
    slots[-1].x1 = max(slots[-1].x1, region_bbox[2])
    for j in range(len(slots) - 1):
        mid = (slots[j].x1 + slots[j + 1].x0) / 2.0
        slots[j].x1 = round(mid, 2)
        slots[j + 1].x0 = round(mid, 2)

    return slots


def reconstruct_table_cells(
    instance_id: str,
    doc_id: str,
    pdf_page: int,
    region: dict[str, Any],
    all_runs: list[dict[str, Any]],
) -> TableInstanceRecord:
    region_bbox = region["bbox"]
    line_ids_set = set(region["line_ids"])
    confidence = region.get("confidence", "strong")

    runs = [r for r in all_runs if r["line_id"] in line_ids_set]
    row_bands = _cluster_row_bands(runs)
    col_slots = _derive_column_slots(runs, row_bands, region_bbox)

    num_cols = len(col_slots)
    num_rows = len(row_bands)

    rows_records: list[RowRecord] = []

    for row_idx, band in enumerate(row_bands):
        row_cells: list[CellRecord] = []
        band_runs = list(band["runs"])

        for col_idx, slot in enumerate(col_slots):
            # Assign each run uniquely to the column slot containing its starting x0 (or centered in slot)
            matching_runs = [
                r for r in band_runs
                if (slot.x0 <= r["bbox"][0] < slot.x1) or (col_idx == len(col_slots) - 1 and r["bbox"][0] >= slot.x0)
            ]

            if matching_runs:
                matching_runs.sort(key=lambda r: r["bbox"][0])
                cell_text = " ".join(r["text"] for r in matching_runs)
                cell_bbox = [
                    round(min(r["bbox"][0] for r in matching_runs), 2),
                    round(min(r["bbox"][1] for r in matching_runs), 2),
                    round(max(r["bbox"][2] for r in matching_runs), 2),
                    round(max(r["bbox"][3] for r in matching_runs), 2),
                ]
                cell_lids = sorted(set(r["line_id"] for r in matching_runs))
                row_cells.append(CellRecord(
                    row_index=row_idx,
                    col_index=col_idx,
                    bbox=cell_bbox,
                    text=cell_text,
                    is_empty=False,
                    source_line_ids=cell_lids,
                    glyph_run_count=len(matching_runs),
                ))
            else:
                cell_bbox = [
                    slot.x0,
                    band["y0"],
                    slot.x1,
                    band["y1"],
                ]
                row_cells.append(CellRecord(
                    row_index=row_idx,
                    col_index=col_idx,
                    bbox=cell_bbox,
                    text="",
                    is_empty=True,
                    source_line_ids=[],
                    glyph_run_count=0,
                ))

        rows_records.append(RowRecord(
            row_index=row_idx,
            bbox=band["bbox"],
            cells=row_cells,
        ))

    return TableInstanceRecord(
        instance_id=instance_id,
        document_id=doc_id,
        pdf_page=pdf_page,
        region_bbox=region_bbox,
        confidence=confidence,
        num_rows=num_rows,
        num_cols=num_cols,
        column_slots=[asdict(s) for s in col_slots],
        rows=rows_records,
        provenance={
            "source_line_count": len(line_ids_set),
            "source_run_count": len(runs),
        },
    )


def process_tables(
    db: sqlite3.Connection,
    processes: list[str],
    session: ort.InferenceSession,
    data_root: Path,
) -> dict[str, Any]:
    documents: dict[str, Any] = {}
    results = []

    try:
        for process_id in processes:
            v2_1_proc = v2_1.analyze_process(db, process_id, session, data_root)
            tables_in_proc = []

            for page in v2_1_proc["pages"]:
                doc_id = page["document_id"]
                pdf_page = page["pdf_page"]
                candidate_regions = page["candidate_regions"]
                if not candidate_regions:
                    continue

                glyph_runs, _ = v2_1._glyph_runs_for_page(documents, db, data_root, doc_id, pdf_page)

                # Collect all runs for the page
                structure_row = db.execute("""
                    SELECT ps.structure_json FROM pages p
                    JOIN page_structures ps ON ps.page_id=p.page_id
                    WHERE p.document_id=? AND p.page_number=?
                """, (doc_id, pdf_page)).fetchone()

                structure = json.loads(structure_row["structure_json"]) if structure_row else {}
                all_runs = []
                for l in structure.get("lines", []):
                    lid = l.get("raw_line_id", l.get("line_id"))
                    runs = glyph_runs.get(lid, [])
                    for r in runs:
                        all_runs.append({
                            "line_id": lid,
                            "text": r.text,
                            "bbox": [round(x, 2) for x in r.bbox],
                        })

                for reg_idx, region in enumerate(candidate_regions):
                    inst_id = f"table_{doc_id[:8]}_p{pdf_page}_r{reg_idx}"
                    table_rec = reconstruct_table_cells(inst_id, doc_id, pdf_page, region, all_runs)
                    tables_in_proc.append(asdict(table_rec))

            results.append({
                "process_id": process_id,
                "table_count": len(tables_in_proc),
                "tables": tables_in_proc,
            })
    finally:
        for doc in documents.values():
            doc.close()

    return {
        "engine": "THEMIS-TABLE-CELL-ENGINE-V0",
        "mode": "offline-deterministic-grid",
        "processes": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=index_db_path())
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--process", action="append", dest="processes")
    parser.add_argument("--output", type=Path, default=Path("scratch/table_cell_engine_v0.json"))
    args = parser.parse_args()

    data_root = args.data_root or args.db.resolve().parent.parent
    processes = args.processes or ["1029994-43.2023.8.26.0554", "1000045-87.2026.8.26.0450"]

    db = sqlite3.connect(args.db.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    db.row_factory = sqlite3.Row
    session = ort.InferenceSession(str(v0.MODEL_PATH_DEFAULT), providers=["CPUExecutionProvider"])

    try:
        output_data = process_tables(db, processes, session, data_root)
    finally:
        db.close()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")

    for p in output_data["processes"]:
        print(f"{p['process_id']}: Reconstruídas {p['table_count']} tabelas em células")
    print(f"JSON: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
