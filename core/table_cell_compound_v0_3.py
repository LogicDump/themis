"""Offline Compound Table Cell Engine V0.3: schema-aware subgrid decomposition.

This layer refines the SubGrid partitioner to prevent over-segmentation in simple tables
with visual spacing (BO, IRPF, Bank statements) by requiring BOTH significant vertical gap
AND persistent horizontal column schema incompatibility before introducing a split.
Neither paragraph pipeline, canonical database, nor ONNX model is modified.
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
SCRIPTS_DIR = THEMIS_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core.pdfium_structuralizer import extract_page_glyph_runs
from core import table_region_assembler_v0 as v0
from core import table_region_assembler_v2_1 as v2_1
from core.table_cell_engine_v0 import _cluster_row_bands
from core.table_cell_grid_v0_1 import ColumnSlot, CellRecord, RowRecord, normalize_table_grid


@dataclass
class SubGridRecord:
    subgrid_index: int
    subgrid_bbox: list[float]
    num_rows: int
    num_cols: int
    column_slots: list[dict[str, Any]]
    rows: list[RowRecord]


@dataclass
class CompoundTableInstanceRecord:
    instance_id: str
    document_id: str
    pdf_page: int
    region_bbox: list[float]
    confidence: str
    is_compound: bool
    num_subgrids: int
    subgrids: list[SubGridRecord]
    provenance: dict[str, Any]


def _get_block_column_boundaries(block: list[dict[str, Any]]) -> list[float]:
    """Derive internal column separator boundaries for a block of rows."""
    if not block:
        return []
    sec_runs = [r for b in block for r in b["runs"]]
    if not sec_runs:
        return []
    sec_bbox = [
        min(r["bbox"][0] for r in sec_runs),
        min(b["y0"] for b in block),
        max(r["bbox"][2] for r in sec_runs),
        max(b["y1"] for b in block),
    ]
    dummy = {
        "instance_id": "dummy",
        "document_id": "doc",
        "pdf_page": 1,
        "region_bbox": sec_bbox,
        "confidence": "strong",
        "rows": [{
            "row_index": b_i,
            "bbox": b["bbox"],
            "cells": [{
                "row_index": b_i,
                "col_index": 0,
                "bbox": r["bbox"],
                "text": r["text"],
                "is_empty": False,
                "source_line_ids": [r["line_id"]],
                "glyph_run_count": 1,
            } for r in b["runs"]],
        } for b_i, b in enumerate(block)],
        "provenance": {},
    }
    norm = normalize_table_grid(dummy)
    slots = norm.column_slots
    return [s["x0"] for s in slots[1:]]


def are_block_schemas_incompatible(block_top: list[dict[str, Any]], block_bot: list[dict[str, Any]]) -> bool:
    """Check if two blocks have fundamentally incompatible column structures."""
    if not block_top or not block_bot:
        return False

    seps_top = _get_block_column_boundaries(block_top)
    seps_bot = _get_block_column_boundaries(block_bot)

    # If one of the blocks is 1-row or has <= 1 row (e.g. title or single run)
    if len(block_top) <= 1 or len(block_bot) <= 1:
        left_top = min(r["bbox"][0] for b in block_top for r in b["runs"])
        left_bot = min(r["bbox"][0] for b in block_bot for r in b["runs"])
        if abs(left_top - left_bot) < 20.0:
            return False

    # If both blocks have multi-column grids:
    if len(seps_top) != len(seps_bot):
        # Different column count across populated blocks (e.g. 2-col header vs 5-col rubricas in Holerite)
        if len(block_top) >= 2 and len(block_bot) >= 2:
            return True
        return False

    if not seps_top and not seps_bot:
        return False

    # Same number of columns: check average shift of internal column boundaries
    shifts = [abs(st - sb) for st, sb in zip(seps_top, seps_bot)]
    avg_shift = sum(shifts) / len(shifts)

    # Significant shift in column intervals (e.g. Holerite Lançamentos vs Bases where shift > 100 pt)
    if avg_shift > 40.0:
        return True

    return False


def partition_raw_row_bands_v3(row_bands: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Detect section boundaries requiring BOTH spatial gap/boundary AND schema incompatibility."""
    if not row_bands:
        return []

    cuts = [0]
    i = 0
    while i < len(row_bands) - 1:
        b_curr = row_bands[i]
        b_next = row_bands[i + 1]
        v_gap = b_curr["y0"] - b_next["y1"]

        prefix_bands = row_bands[cuts[-1]:i + 1]
        suffix_bands = row_bands[i + 1:]

        # Condition 1: Substantial vertical gap (> 25 pt) with incompatible schemas
        if v_gap > 25.0:
            if are_block_schemas_incompatible(prefix_bands, suffix_bands):
                cuts.append(i + 1)
                i += 1
                continue

        # Condition 2: Clear schema transition before a full tabular header line (>= 4 columns starting at margin < 35 pt)
        next_runs = b_next["runs"]
        curr_runs = b_curr["runs"]
        if next_runs and curr_runs:
            next_x0 = min(r["bbox"][0] for r in next_runs)
            curr_x0 = min(r["bbox"][0] for r in curr_runs)
            if len(next_runs) >= 4 and next_x0 < 35.0 and curr_x0 > 60.0 and len(curr_runs) <= 2:
                if are_block_schemas_incompatible(prefix_bands, suffix_bands):
                    cuts.append(i + 1)
                    i += 1
                    continue

        i += 1

    cuts.append(len(row_bands))
    cuts = sorted(set(cuts))

    sections = []
    for s_idx in range(len(cuts) - 1):
        start_idx = cuts[s_idx]
        end_idx = cuts[s_idx + 1]
        sections.append(row_bands[start_idx:end_idx])

    return sections


def reconstruct_compound_table_v3(
    instance_id: str,
    doc_id: str,
    pdf_page: int,
    region: dict[str, Any],
    all_runs: list[dict[str, Any]],
) -> CompoundTableInstanceRecord:
    region_bbox = region["bbox"]
    line_ids_set = set(region["line_ids"])
    confidence = region.get("confidence", "strong")

    runs = [r for r in all_runs if r["line_id"] in line_ids_set]
    raw_bands = _cluster_row_bands(runs)
    sections = partition_raw_row_bands_v3(raw_bands)

    subgrid_records: list[SubGridRecord] = []

    for s_idx, sec_bands in enumerate(sections):
        sec_runs = [r for b in sec_bands for r in b["runs"]]
        sec_bbox = [
            round(min(r["bbox"][0] for r in sec_runs), 2),
            round(min(b["y0"] for b in sec_bands), 2),
            round(max(r["bbox"][2] for r in sec_runs), 2),
            round(max(b["y1"] for b in sec_bands), 2),
        ]

        dummy_table = {
            "instance_id": f"{instance_id}_s{s_idx}",
            "document_id": doc_id,
            "pdf_page": pdf_page,
            "region_bbox": sec_bbox,
            "confidence": confidence,
            "rows": [{
                "row_index": b_i,
                "bbox": b["bbox"],
                "cells": [{
                    "row_index": b_i,
                    "col_index": 0,
                    "bbox": r["bbox"],
                    "text": r["text"],
                    "is_empty": False,
                    "source_line_ids": [r["line_id"]],
                    "glyph_run_count": 1,
                } for r in b["runs"]],
            } for b_i, b in enumerate(sec_bands)],
            "provenance": {},
        }

        norm_instance = normalize_table_grid(dummy_table)

        subgrid_records.append(SubGridRecord(
            subgrid_index=s_idx,
            subgrid_bbox=sec_bbox,
            num_rows=norm_instance.num_rows,
            num_cols=norm_instance.num_cols,
            column_slots=norm_instance.column_slots,
            rows=norm_instance.rows,
        ))

    return CompoundTableInstanceRecord(
        instance_id=instance_id,
        document_id=doc_id,
        pdf_page=pdf_page,
        region_bbox=region_bbox,
        confidence=confidence,
        is_compound=len(subgrid_records) > 1,
        num_subgrids=len(subgrid_records),
        subgrids=subgrid_records,
        provenance={
            "source_line_count": len(line_ids_set),
            "source_run_count": len(runs),
        },
    )


def process_processes_v3(
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
                    table_rec = reconstruct_compound_table_v3(inst_id, doc_id, pdf_page, region, all_runs)
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
        "engine": "THEMIS-TABLE-CELL-COMPOUND-V0.3",
        "mode": "offline-schema-aware-compound-decomposition",
        "processes": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=index_db_path())
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--process", action="append", dest="processes")
    parser.add_argument("--output", type=Path, default=Path("scratch/table_cell_compound_v0_3.json"))
    args = parser.parse_args()

    data_root = args.data_root or args.db.resolve().parent.parent
    processes = args.processes or ["1029994-43.2023.8.26.0554", "1000045-87.2026.8.26.0450"]

    db = sqlite3.connect(args.db.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    db.row_factory = sqlite3.Row
    session = ort.InferenceSession(str(v0.MODEL_PATH_DEFAULT), providers=["CPUExecutionProvider"])

    try:
        output_data = process_processes_v3(db, processes, session, data_root)
    finally:
        db.close()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")

    for p in output_data["processes"]:
        print(f"{p['process_id']}: Reconstruídas {p['table_count']} tabelas em V0.3")
    print(f"JSON: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
