"""Canonical Table Structure Assembler V1: consolidates geometric matrix into canonical contract.

Transforms the validated offline multiline output (V0.4) into the CanonicalTableInstance schema:
TableInstance -> SubGrid -> Row -> Cell.

Validates exact structural round-trip and conservation of:
- 137 TableInstances
- 255 SubGrids
- 1,403 Rows
- 3,753 Non-empty Cells
- 1,580 Empty Cells
- 46 Multiline Cells
- 467 ColSpan Cells (>1)
- 4,400 / 4,400 GlyphRuns
- row_span == 1 for 100% of cells
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

try:
    from core.runtime_paths import index_db_path
except ModuleNotFoundError:
    from runtime_paths import index_db_path
from typing import Any

THEMIS_ROOT = Path(__file__).resolve().parents[1]
if str(THEMIS_ROOT) not in sys.path:
    sys.path.insert(0, str(THEMIS_ROOT))
from core.table_canonical_schema import (
    CanonicalCell,
    CanonicalRow,
    CanonicalColumnSlot,
    CanonicalSubGrid,
    CanonicalProvenance,
    CanonicalTableInstance,
)


def convert_v04_table_to_canonical(table_dict: dict[str, Any], page_id_map: dict[tuple[str, int], str] | None = None) -> CanonicalTableInstance:
    """Convert a single table from table_cell_multiline_v0_4.json to CanonicalTableInstance."""
    doc_id = table_dict["document_id"]
    pdf_page = table_dict.get("page_number", table_dict.get("pdf_page", 1))
    page_id = page_id_map.get((doc_id, pdf_page)) if page_id_map else None

    # Provenance
    raw_prov = table_dict.get("provenance", {})
    prov = CanonicalProvenance(
        source_engine="THEMIS-TABLE-REGION-V2.1",
        assembler_version="2.1",
        cell_engine_version="0.4",
        source_line_count=raw_prov.get("source_line_count", 0),
        source_run_count=raw_prov.get("source_run_count", 0),
        confidence=table_dict.get("confidence", "strong"),
    )

    # SubGrids
    canonical_subgrids = []
    for sg_data in table_dict.get("subgrids", []):
        # Column Slots
        slots = []
        for s in sg_data.get("column_slots", []):
            slots.append(CanonicalColumnSlot(
                col_index=s["col_index"],
                x0=round(s["x0"], 2),
                x1=round(s["x1"], 2),
                alignment=s.get("alignment", "left"),
                confidence=round(s.get("confidence", 1.0), 2),
            ))

        # Rows and Cells
        rows = []
        for r_data in sg_data.get("rows", []):
            cells = []
            for c_data in r_data.get("cells", []):
                cells.append(CanonicalCell(
                    row_index=r_data["row_index"],
                    col_index=c_data["col_index"],
                    row_span=c_data.get("row_span", 1),
                    col_span=c_data.get("col_span", 1),
                    is_empty=c_data.get("is_empty", False),
                    text=c_data.get("text", ""),
                    bbox=[round(x, 2) for x in c_data.get("bbox", [])],
                    source_line_ids=sorted(set(c_data.get("source_line_ids", []))),
                    glyph_run_count=c_data.get("glyph_run_count", 0),
                    semantic_role=None,
                    data_type=None,
                ))

            rows.append(CanonicalRow(
                row_index=r_data["row_index"],
                bbox=[round(x, 2) for x in r_data.get("bbox", [])],
                cells=cells,
                semantic_role=None,
            ))

        canonical_subgrids.append(CanonicalSubGrid(
            subgrid_index=sg_data["subgrid_index"],
            bbox=[round(x, 2) for x in sg_data.get("subgrid_bbox", sg_data.get("bbox", []))],
            row_count=len(rows),
            col_count=len(slots),
            column_slots=slots,
            rows=rows,
            section_type=None,
        ))

    return CanonicalTableInstance(
        instance_id=table_dict["instance_id"],
        document_id=doc_id,
        page_number=pdf_page,
        page_id=page_id,
        region_bbox=[round(x, 2) for x in table_dict.get("region_bbox", [])],
        is_compound=len(canonical_subgrids) > 1,
        subgrid_count=len(canonical_subgrids),
        subgrids=canonical_subgrids,
        provenance=prov,
        table_type=None,
    )


def build_page_id_map(db_path: Path) -> dict[tuple[str, int], str]:
    """Retrieve mapping from (document_id, page_number) -> page_id from themis.db."""
    if not db_path.exists():
        return {}
    db = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    db.row_factory = sqlite3.Row
    try:
        rows = db.execute("SELECT page_id, document_id, page_number FROM pages").fetchall()
        return {(r["document_id"], r["page_number"]): r["page_id"] for r in rows}
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("scratch/table_cell_multiline_v0_4.json"))
    parser.add_argument("--db", type=Path, default=index_db_path())
    parser.add_argument("--output", type=Path, default=Path("scratch/table_canonical_structure_v1.json"))
    args = parser.parse_args()

    page_id_map = build_page_id_map(args.db)

    with open(args.input, "r", encoding="utf-8") as f:
        v04_data = json.load(f)

    canonical_processes = []
    total_tables = 0
    total_subgrids = 0
    total_rows = 0
    total_non_empty = 0
    total_empty = 0
    total_multiline = 0
    total_colspan = 0
    total_runs = 0
    row_span_is_one_count = 0
    total_cell_count = 0

    for proc in v04_data["processes"]:
        proc_id = proc["process_id"]
        canonical_tables = []
        for t_dict in proc["tables"]:
            c_table = convert_v04_table_to_canonical(t_dict, page_id_map)
            
            # Round-trip verification: to_dict -> from_dict -> to_dict
            t_dict_1 = c_table.to_dict()
            c_table_rt = CanonicalTableInstance.from_dict(t_dict_1)
            t_dict_2 = c_table_rt.to_dict()
            assert t_dict_1 == t_dict_2, f"Round-trip failed for table {c_table.instance_id}!"

            total_tables += 1
            for sg in c_table.subgrids:
                total_subgrids += 1
                total_rows += sg.row_count
                for r in sg.rows:
                    for c in r.cells:
                        total_cell_count += 1
                        if c.row_span == 1:
                            row_span_is_one_count += 1
                        if c.is_empty:
                            total_empty += 1
                        else:
                            total_non_empty += 1
                            total_runs += c.glyph_run_count
                            if "\n" in c.text:
                                total_multiline += 1
                            if c.col_span > 1:
                                total_colspan += 1

            canonical_tables.append(c_table.to_dict())

        canonical_processes.append({
            "process_id": proc_id,
            "table_count": len(canonical_tables),
            "tables": canonical_tables,
        })

    output_payload = {
        "contract": "THEMIS-TABLE-CANONICAL-STRUCTURE-V1",
        "schema_version": "1.0",
        "processes": canonical_processes,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 80)
    print("CANONICAL STRUCTURE V1 CONVERSION AND VALIDATION SUMMARY:")
    print("=" * 80)
    print(f"  - TableInstances: {total_tables} (Expected: 137)")
    print(f"  - SubGrids: {total_subgrids} (Expected: 255)")
    print(f"  - Rows: {total_rows} (Expected: 1403)")
    print(f"  - Non-empty Cells: {total_non_empty} (Expected: 3753)")
    print(f"  - Empty Cells: {total_empty} (Expected: 1580)")
    print(f"  - Multiline Cells (\\n): {total_multiline} (Expected: 46)")
    print(f"  - ColSpan Cells (>1): {total_colspan} (Expected: 467)")
    print(f"  - Total Cells: {total_cell_count} (row_span=1 in {row_span_is_one_count}/{total_cell_count})")
    print(f"  - GlyphRuns: {total_runs} (Expected: 4400)")
    print(f"  - Output JSON: {args.output.resolve()}")

    assert total_tables == 137
    assert total_subgrids == 255
    assert total_rows == 1403
    assert total_non_empty == 3753
    assert total_empty == 1580
    assert total_multiline == 46
    assert total_colspan == 467
    assert total_runs == 4400
    assert row_span_is_one_count == total_cell_count

    print("\nALL CANONICAL V1 INVARIANTS SATISFIED WITH 100% ACCURACY!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
