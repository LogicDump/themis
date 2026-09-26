"""Offline Cell Grid Normalizer V0.1: subcolumn normalization and colspan resolution.

This layer normalizes spurious geometric subcolumns and resolves horizontal colspans
for simple table grids based on the output of Table Cell Engine V0.
Neither canonical pipeline, database, nor ONNX model is modified.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

THEMIS_ROOT = Path(__file__).resolve().parents[1]
if str(THEMIS_ROOT) not in sys.path:
    sys.path.insert(0, str(THEMIS_ROOT))


@dataclass
class ColumnSlot:
    col_index: int
    x0: float
    x1: float
    anchor_x0: float


@dataclass
class CellRecord:
    row_index: int
    col_index: int
    col_span: int
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


def normalize_table_grid(table: dict[str, Any]) -> TableInstanceRecord:
    """Normalize subcolumns and resolve colspans for a single TableInstance."""
    iid = table["instance_id"]
    doc_id = table["document_id"]
    pdf_page = table["pdf_page"]
    region_bbox = table["region_bbox"]
    confidence = table.get("confidence", "strong")
    rows = table["rows"]

    # Extract non-empty runs per row
    row_bands: list[dict[str, Any]] = []
    for r in rows:
        runs = []
        for c in r["cells"]:
            if not c["is_empty"]:
                runs.append({
                    "x0": c["bbox"][0],
                    "y0": c["bbox"][1],
                    "x1": c["bbox"][2],
                    "y1": c["bbox"][3],
                    "text": c["text"],
                    "lids": c["source_line_ids"],
                    "run_count": c["glyph_run_count"],
                })
        runs.sort(key=lambda x: x["x0"])
        row_bands.append({
            "row_index": r["row_index"],
            "bbox": r["bbox"],
            "runs": runs,
        })

    non_empty_rows = [b for b in row_bands if b["runs"]]
    if not non_empty_rows:
        # Table with no non-empty rows: 1 empty column
        slot = ColumnSlot(0, region_bbox[0], region_bbox[2], region_bbox[0])
        empty_rows = []
        for b in row_bands:
            empty_rows.append(RowRecord(
                row_index=b["row_index"],
                bbox=b["bbox"],
                cells=[CellRecord(
                    row_index=b["row_index"],
                    col_index=0,
                    col_span=1,
                    bbox=[slot.x0, b["bbox"][1], slot.x1, b["bbox"][3]],
                    text="",
                    is_empty=True,
                )],
            ))
        return TableInstanceRecord(
            instance_id=iid,
            document_id=doc_id,
            pdf_page=pdf_page,
            region_bbox=region_bbox,
            confidence=confidence,
            num_rows=len(row_bands),
            num_cols=1,
            column_slots=[asdict(slot)],
            rows=empty_rows,
            provenance=table.get("provenance", {}),
        )

    # Determine maximum number of co-occurring runs in any single row band
    max_k = max(len(b["runs"]) for b in non_empty_rows)
    if max_k <= 1:
        slots = [ColumnSlot(0, region_bbox[0], region_bbox[2], region_bbox[0])]
    else:
        # Identify anchor rows (rows with max_k non-empty runs)
        anchor_rows = [b for b in non_empty_rows if len(b["runs"]) == max_k]
        col_x0_samples: list[list[float]] = [[] for _ in range(max_k)]
        col_x1_samples: list[list[float]] = [[] for _ in range(max_k)]

        for b in anchor_rows:
            for j, r in enumerate(b["runs"]):
                col_x0_samples[j].append(r["x0"])
                col_x1_samples[j].append(r["x1"])

        avg_x0 = [min(col_x0_samples[j]) for j in range(max_k)]
        avg_x1 = [max(col_x1_samples[j]) for j in range(max_k)]

        # Derive partition separators
        seps = [region_bbox[0]]
        for j in range(max_k - 1):
            left_bound = avg_x1[j]
            right_bound = avg_x0[j + 1]
            if right_bound > left_bound:
                sep = (left_bound + right_bound) / 2.0
            else:
                sep = (avg_x0[j] + avg_x0[j + 1]) / 2.0
            seps.append(round(sep, 2))
        seps.append(region_bbox[2])

        slots = []
        for j in range(max_k):
            slots.append(ColumnSlot(
                col_index=j,
                x0=seps[j],
                x1=seps[j + 1],
                anchor_x0=round(sum(col_x0_samples[j]) / len(col_x0_samples[j]), 2),
            ))

    # Construct normalized 2D matrix of cells with horizontal colspans
    result_rows: list[RowRecord] = []

    for b in row_bands:
        r_idx = b["row_index"]
        runs = list(b["runs"])

        # Map each run to its starting slot
        runs_by_slot: dict[int, list[dict[str, Any]]] = {j: [] for j in range(len(slots))}
        for r in runs:
            slot_idx = 0
            for j, s in enumerate(slots):
                if r["x0"] >= s.x0 or j == 0:
                    slot_idx = j
            runs_by_slot[slot_idx].append(r)

        row_cells: list[CellRecord] = []
        curr_c = 0
        while curr_c < len(slots):
            slot_runs = runs_by_slot[curr_c]
            if slot_runs:
                slot_runs.sort(key=lambda x: x["x0"])
                combined_text = " ".join(x["text"] for x in slot_runs)
                combined_bbox = [
                    min(x["x0"] for x in slot_runs),
                    min(x["y0"] for x in slot_runs),
                    max(x["x1"] for x in slot_runs),
                    max(x["y1"] for x in slot_runs),
                ]
                all_lids = sorted(set(lid for x in slot_runs for lid in x["lids"]))
                total_runs = sum(x["run_count"] for x in slot_runs)

                # Check if cell spans into subsequent empty column slots
                c_end = curr_c
                for next_c in range(curr_c + 1, len(slots)):
                    if runs_by_slot[next_c]:
                        break
                    if combined_bbox[2] > slots[next_c].x0 + 5.0:
                        c_end = next_c
                    else:
                        break

                span = c_end - curr_c + 1
                row_cells.append(CellRecord(
                    row_index=r_idx,
                    col_index=curr_c,
                    col_span=span,
                    bbox=[round(v, 2) for v in combined_bbox],
                    text=combined_text,
                    is_empty=False,
                    source_line_ids=all_lids,
                    glyph_run_count=total_runs,
                ))
                curr_c = c_end + 1
            else:
                s = slots[curr_c]
                row_cells.append(CellRecord(
                    row_index=r_idx,
                    col_index=curr_c,
                    col_span=1,
                    bbox=[s.x0, b["bbox"][1], s.x1, b["bbox"][3]],
                    text="",
                    is_empty=True,
                    source_line_ids=[],
                    glyph_run_count=0,
                ))
                curr_c += 1

        result_rows.append(RowRecord(
            row_index=r_idx,
            bbox=b["bbox"],
            cells=row_cells,
        ))

    return TableInstanceRecord(
        instance_id=iid,
        document_id=doc_id,
        pdf_page=pdf_page,
        region_bbox=region_bbox,
        confidence=confidence,
        num_rows=len(result_rows),
        num_cols=len(slots),
        column_slots=[asdict(s) for s in slots],
        rows=result_rows,
        provenance=table.get("provenance", {}),
    )


def process_v0_json(input_path: Path) -> dict[str, Any]:
    with input_path.open("r", encoding="utf-8") as f:
        v0_data = json.load(f)

    results = []
    for proc in v0_data.get("processes", []):
        normalized_tables = []
        for t in proc.get("tables", []):
            norm_rec = normalize_table_grid(t)
            normalized_tables.append(asdict(norm_rec))
        results.append({
            "process_id": proc["process_id"],
            "table_count": len(normalized_tables),
            "tables": normalized_tables,
        })

    return {
        "engine": "THEMIS-TABLE-CELL-GRID-V0.1",
        "mode": "offline-grid-normalized-colspan",
        "source_v0_file": str(input_path.resolve()),
        "processes": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("scratch/table_cell_engine_v0.json"))
    parser.add_argument("--output", type=Path, default=Path("scratch/table_cell_grid_v0_1.json"))
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Error: input file {args.input} not found.", file=sys.stderr)
        return 1

    output_data = process_v0_json(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")

    for p in output_data["processes"]:
        print(f"{p['process_id']}: Normalizadas {p['table_count']} tabelas em grid lógico V0.1")
    print(f"JSON: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
