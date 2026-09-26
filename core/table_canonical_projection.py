"""Read-only bridge from Canonical Table Structure V1 to the Markdown projection.

The table reconstruction chain is deliberately offline and frozen.  This module
does not run any of its algorithms: it loads their validated Canonical V1 output
and adapts it to the pre-existing structural table/GFM contract.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from core.table_canonical_schema import CanonicalTableInstance


CANONICAL_TABLE_CONTRACT = "THEMIS-TABLE-CANONICAL-STRUCTURE-V1"
CANONICAL_TABLE_SCHEMA_VERSION = "1.0"
DEFAULT_CANONICAL_TABLE_PATH = Path(__file__).with_name("table_canonical_structure_v1.json")


def _positive_int(value: Any, default: int = 1) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return default


def _canonical_source_line_ids(table: dict[str, Any]) -> set[int]:
    result: set[int] = set()
    for subgrid in table.get("subgrids", []):
        for row in subgrid.get("rows", []):
            for cell in row.get("cells", []):
                for line_id in cell.get("source_line_ids", []):
                    try:
                        result.add(int(line_id))
                    except (TypeError, ValueError):
                        continue
    return result


def _subgrid_projection(subgrid: dict[str, Any], page: int) -> dict[str, Any]:
    """Adapt one canonical SubGrid to serialize_table_gfm's existing input."""
    rows = []
    flat_cells = []
    for row in sorted(subgrid.get("rows", []), key=lambda item: int(item.get("row_index", 0))):
        adapted_cells = []
        for cell in sorted(row.get("cells", []), key=lambda item: int(item.get("col_index", 0))):
            adapted = {
                "text": str(cell.get("text", "")),
                "row_index": int(row.get("row_index", 0)),
                "column_index": int(cell.get("col_index", 0)),
                "colspan": _positive_int(cell.get("col_span", 1)),
                # Canonical V1 was audited with TRUE_ROWSPAN=0.  The adapter
                # accepts the contract field but never invents a span.
                "rowspan": _positive_int(cell.get("row_span", 1)),
                "bbox": list(cell.get("bbox", [])),
                "source_line_ids": list(cell.get("source_line_ids", [])),
                "glyph_run_count": int(cell.get("glyph_run_count", 0)),
                "is_empty": bool(cell.get("is_empty", False)),
                "is_header": str(row.get("semantic_role") or "") == "header_row" or str(cell.get("semantic_role") or "") == "header",
            }
            adapted_cells.append(adapted)
            flat_cells.append(adapted)
        rows.append({
            "row_index": int(row.get("row_index", 0)),
            "bbox": list(row.get("bbox", [])),
            "cells": adapted_cells,
        })
    return {
        "type": "table",
        "page": page,
        "bbox": list(subgrid.get("bbox", [])),
        "rows": rows,
        "cells": flat_cells,
        "column_count": int(subgrid.get("col_count", 0)),
    }


def canonical_table_to_structural_model(table: dict[str, Any]) -> dict[str, Any]:
    """Keep Canonical V1 whole while exposing its GFM projection fields.

    ``subgrids`` remains the authoritative lossless hierarchy in
    ``structure_json['tables']``.  ``projection_subgrids`` is only an adapter
    for the established Markdown serializer.
    """
    canonical = CanonicalTableInstance.from_dict(table).to_dict()
    if any(cell.get("row_span", 1) != 1 for subgrid in canonical["subgrids"] for row in subgrid["rows"] for cell in row["cells"]):
        raise ValueError(f"Canonical V1 table {canonical['instance_id']} has unsupported row_span")
    projection_subgrids = [_subgrid_projection(subgrid, canonical["page_number"]) for subgrid in canonical["subgrids"]]
    return {
        **canonical,
        "type": "table",
        "page": canonical["page_number"],
        "bbox": list(canonical["region_bbox"]),
        "source": "canonical_table_v1",
        "source_line_ids": sorted(_canonical_source_line_ids(canonical)),
        "projection_subgrids": projection_subgrids,
    }


@dataclass(frozen=True)
class CanonicalTableRegistry:
    tables_by_page: dict[tuple[str, int], tuple[dict[str, Any], ...]]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CanonicalTableRegistry":
        if payload.get("contract") != CANONICAL_TABLE_CONTRACT or str(payload.get("schema_version")) != CANONICAL_TABLE_SCHEMA_VERSION:
            raise ValueError("artefato Canonical Table V1 incompatível")
        grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
        for process in payload.get("processes", []):
            for raw_table in process.get("tables", []):
                model = canonical_table_to_structural_model(raw_table)
                grouped[(model["document_id"], model["page"])] .append(model)
        return cls({key: tuple(sorted(value, key=lambda item: (item["bbox"][1] if len(item["bbox"]) == 4 else 0, item["bbox"][0] if len(item["bbox"]) == 4 else 0))) for key, value in grouped.items()})

    def tables_for_page(self, document_id: str, page_number: int) -> list[dict[str, Any]]:
        return [dict(table) for table in self.tables_by_page.get((document_id, page_number), ())]


@lru_cache(maxsize=4)
def load_canonical_table_registry(path: str | None = None) -> CanonicalTableRegistry:
    configured = path or os.environ.get("THEMIS_CANONICAL_TABLE_STRUCTURE_PATH")
    artifact = Path(configured) if configured else DEFAULT_CANONICAL_TABLE_PATH
    if not artifact.is_file():
        return CanonicalTableRegistry({})
    with artifact.open("r", encoding="utf-8") as stream:
        return CanonicalTableRegistry.from_payload(json.load(stream))


def canonical_tables_by_page(document_id: str, pages: set[int] | list[int]) -> dict[int, list[dict[str, Any]]]:
    registry = load_canonical_table_registry()
    return {page: registry.tables_for_page(document_id, page) for page in pages}


def canonical_table_markdown(table: dict[str, Any], serialize_table_gfm: Any) -> str:
    """Render Canonical V1 only through the pre-existing safe GFM serializer."""
    return "\n\n".join(
        markdown for subgrid in table.get("projection_subgrids", [])
        if (markdown := serialize_table_gfm(subgrid))
    )
