"""Offline Table Cell Multiline Engine V0.4: intra-cell multiline merging.

This layer runs after SubGrid reconstruction (Compound V0.3) to merge consecutive
baseline rows that represent visual line-wraps within the same logical cells.
- Preserves physical reading order using internal newlines ('\\n').
- Merges bounding boxes, source_line_ids, and glyph_run_counts.
- Does NOT alter paragraph boundary engine, canonical database, or ONNX model.
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

THEMIS_ROOT = Path(__file__).resolve().parents[1]
if str(THEMIS_ROOT) not in sys.path:
    sys.path.insert(0, str(THEMIS_ROOT))
SCRIPTS_DIR = THEMIS_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core import table_region_assembler_v0 as v0
from core import table_cell_compound_v0_3 as v0_3
from core.table_cell_grid_v0_1 import CellRecord, RowRecord
from core.table_cell_compound_v0_3 import SubGridRecord, CompoundTableInstanceRecord, reconstruct_compound_table_v3


def merge_multiline_rows_in_subgrid(subgrid: SubGridRecord | dict[str, Any]) -> SubGridRecord:
    """Merge consecutive multiline continuation rows within a SubGrid."""
    if isinstance(subgrid, dict):
        rows_data = subgrid["rows"]
        sg_idx = subgrid["subgrid_index"]
        sg_bbox = subgrid["subgrid_bbox"]
        num_cols = subgrid["num_cols"]
        col_slots = subgrid["column_slots"]
    else:
        rows_data = [asdict(r) if hasattr(r, "__dataclass_fields__") else r for r in subgrid.rows]
        sg_idx = subgrid.subgrid_index
        sg_bbox = subgrid.subgrid_bbox
        num_cols = subgrid.num_cols
        col_slots = subgrid.column_slots

    if len(rows_data) <= 1:
        recs = [RowRecord(
            row_index=r["row_index"],
            bbox=r["bbox"],
            cells=[CellRecord(**c) for c in r["cells"]],
        ) for r in rows_data]
        return SubGridRecord(
            subgrid_index=sg_idx,
            subgrid_bbox=sg_bbox,
            num_rows=len(recs),
            num_cols=num_cols,
            column_slots=col_slots,
            rows=recs,
        )

    merged_rows = []
    i = 0
    while i < len(rows_data):
        curr_row = dict(rows_data[i])
        curr_cells = [dict(c) for c in curr_row["cells"]]
        curr_bbox = list(curr_row["bbox"])

        while i + 1 < len(rows_data):
            next_row = rows_data[i + 1]
            next_cells = next_row["cells"]

            # Vertical gap check (<= 12 pt, typical interline spacing within cell)
            v_gap = curr_bbox[1] - next_row["bbox"][3]
            if v_gap > 12.0:
                break

            curr_non_empty = [c["col_index"] for c in curr_cells if not c["is_empty"]]
            next_non_empty = [c["col_index"] for c in next_cells if not c["is_empty"]]

            if not next_non_empty:
                # next row is entirely empty
                break

            # Rule 1: A continuation row MUST have its leading key column (col 0) empty in multi-column tables.
            # Presence of col 0 signifies a distinct logical item/entry.
            if 0 in next_non_empty and len(curr_cells) > 1:
                break

            # Rule 2: All non-empty columns in next_row must correspond to active columns in curr_row
            if not all(col in curr_non_empty for col in next_non_empty):
                break

            # Merge next_cells into curr_cells
            for nc in next_cells:
                if not nc["is_empty"]:
                    col_idx = nc["col_index"]
                    tc = curr_cells[col_idx]
                    tc["text"] = tc["text"] + "\n" + nc["text"] if tc["text"] else nc["text"]
                    tc["bbox"] = [
                        min(tc["bbox"][0], nc["bbox"][0]),
                        min(tc["bbox"][1], nc["bbox"][1]),
                        max(tc["bbox"][2], nc["bbox"][2]),
                        max(tc["bbox"][3], nc["bbox"][3]),
                    ]
                    tc["source_line_ids"] = sorted(set(tc["source_line_ids"] + nc["source_line_ids"]))
                    tc["glyph_run_count"] += nc["glyph_run_count"]
                    tc["is_empty"] = False

            curr_bbox = [
                min(curr_bbox[0], next_row["bbox"][0]),
                min(curr_bbox[1], next_row["bbox"][1]),
                max(curr_bbox[2], next_row["bbox"][2]),
                max(curr_bbox[3], next_row["bbox"][3]),
            ]
            i += 1

        curr_row_idx = len(merged_rows)
        for c in curr_cells:
            c["row_index"] = curr_row_idx

        merged_rows.append(RowRecord(
            row_index=curr_row_idx,
            bbox=curr_bbox,
            cells=[CellRecord(**c) for c in curr_cells],
        ))
        i += 1

    return SubGridRecord(
        subgrid_index=sg_idx,
        subgrid_bbox=sg_bbox,
        num_rows=len(merged_rows),
        num_cols=num_cols,
        column_slots=col_slots,
        rows=merged_rows,
    )


def reconstruct_multiline_table_v4(
    instance_id: str,
    doc_id: str,
    pdf_page: int,
    region: dict[str, Any],
    all_runs: list[dict[str, Any]],
) -> CompoundTableInstanceRecord:
    """Reconstruct Compound table and merge multiline cell wraps within each subgrid."""
    compound_table = reconstruct_compound_table_v3(instance_id, doc_id, pdf_page, region, all_runs)

    merged_subgrids = []
    for s in compound_table.subgrids:
        s_merged = merge_multiline_rows_in_subgrid(s)
        merged_subgrids.append(s_merged)

    return CompoundTableInstanceRecord(
        instance_id=instance_id,
        document_id=doc_id,
        pdf_page=pdf_page,
        region_bbox=compound_table.region_bbox,
        confidence=compound_table.confidence,
        is_compound=compound_table.is_compound,
        num_subgrids=len(merged_subgrids),
        subgrids=merged_subgrids,
        provenance=compound_table.provenance,
    )


def process_processes_v4(
    db: sqlite3.Connection,
    processes: list[str],
    session: ort.InferenceSession,
    data_root: Path,
) -> dict[str, Any]:
    documents: dict[str, Any] = {}
    results = []

    try:
        for process_id in processes:
            import table_region_assembler_v2_1 as v2_1
            v2_1_proc = v2_1.analyze_process(db, process_id, session, data_root)
            tables_in_proc = []

            for page in v2_1_proc["pages"]:
                doc_id = page["document_id"]
                pdf_page = page["pdf_page"]
                candidate_regions = page["candidate_regions"]
                if not candidate_regions:
                    continue

                glyph_runs, _ = v2_1._glyph_runs_for_page(documents, db, data_root, doc_id, pdf_page)

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
                    table_rec = reconstruct_multiline_table_v4(inst_id, doc_id, pdf_page, region, all_runs)
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
        "engine": "THEMIS-TABLE-CELL-MULTILINE-V0.4",
        "mode": "offline-intra-cell-multiline-merging",
        "processes": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=index_db_path())
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--process", action="append", dest="processes")
    parser.add_argument("--output", type=Path, default=Path("scratch/table_cell_multiline_v0_4.json"))
    args = parser.parse_args()

    data_root = args.data_root or args.db.resolve().parent.parent
    processes = args.processes or ["1029994-43.2023.8.26.0554", "1000045-87.2026.8.26.0450"]

    db = sqlite3.connect(args.db.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    db.row_factory = sqlite3.Row
    session = ort.InferenceSession(str(v0.MODEL_PATH_DEFAULT), providers=["CPUExecutionProvider"])

    try:
        output_data = process_processes_v4(db, processes, session, data_root)
    finally:
        db.close()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")

    for p in output_data["processes"]:
        print(f"{p['process_id']}: Reconstruídas {p['table_count']} tabelas em V0.4")
    print(f"JSON: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
