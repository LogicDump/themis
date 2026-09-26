"""Runtime orchestration of the frozen Canonical Table V1 chain.

The individual algorithms are mechanical ports of their homologated offline
counterparts.  This module supplies their per-page inputs while PDFium is open;
GlyphRuns remain ephemeral and are never returned in the table contract.
"""
from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
from typing import Any

import onnxruntime as ort

from core import table_region_assembler_v0 as region_v0
from core import table_region_assembler_v2 as region_v2
from core import table_region_assembler_v2_1 as region_v2_1
from core import table_cell_engine_v0 as cell_v0
from core import table_cell_grid_v0_1 as grid_v0_1
from core import table_cell_multiline_v0_4 as multiline_v0_4
from core.table_canonical_assembler_v1 import convert_v04_table_to_canonical
from core.table_canonical_projection import canonical_table_to_structural_model


@lru_cache(maxsize=1)
def _table_session() -> ort.InferenceSession:
    """Load the existing Boundary model once, exactly as offline V2.1 does."""
    return ort.InferenceSession(
        str(region_v0.MODEL_PATH_DEFAULT), providers=["CPUExecutionProvider"]
    )


def _runtime_structure(raw_data: dict[str, Any], page_number: int) -> dict[str, Any]:
    return {
        "page": page_number,
        "page_geometry": {"width": raw_data["width"], "height": raw_data["height"]},
        "lines": [
            {
                "line_id": index,
                "raw_line_id": line.raw_line_id,
                "text": line.text,
                "bbox": list(line.bbox),
                "font_size": line.font_size,
                "is_bold": line.is_bold,
                "is_italic": line.is_italic,
            }
            for index, line in enumerate(raw_data.get("line_structs", []), start=1)
        ],
    }


def reconstruct_canonical_tables(
    raw_data: dict[str, Any],
    *,
    document_id: str,
    page_number: int,
    page_id: str | None = None,
) -> list[dict[str, Any]]:
    """Run V2.1 -> V0 -> V0.1 -> V0.3 -> V0.4 -> Canonical V1 for one page.

    The V0/V0.1 pass is retained as an explicit stage of the homologated chain.
    V0.3 performs its own frozen subgrid normalization before V0.4 creates the
    authoritative compound representation, exactly as the offline run did.
    """
    return _reconstruct(
        _runtime_structure(raw_data, page_number),
        raw_data.get("glyph_runs_by_raw_line", {}),
        document_id=document_id,
        page_number=page_number,
        page_id=page_id,
    )


def reconstruct_canonical_tables_from_structure(
    structure: dict[str, Any],
    glyph_runs_by_raw_line: dict[int, list[Any]],
    *,
    document_id: str,
    page_number: int,
    page_id: str | None = None,
) -> list[dict[str, Any]]:
    """Regression entry point for an already-persisted structural page.

    It is deliberately separate from the PDF runtime input and lets the frozen
    903-page corpus verify the port without reading GlyphRuns from storage.
    """
    return _reconstruct(
        structure, glyph_runs_by_raw_line,
        document_id=document_id, page_number=page_number, page_id=page_id,
    )


def _reconstruct(
    structure: dict[str, Any],
    glyphs: dict[int, list[Any]],
    *,
    document_id: str,
    page_number: int,
    page_id: str | None,
) -> list[dict[str, Any]]:
    diagnostic = region_v0.assemble_page(
        structure, _table_session(), glyphs, require_glyph_alignment=True
    )
    diagnostic["document_id"] = document_id
    diagnostic["pdf_page"] = page_number
    region_v2._promote_spatial_glyph_seeds(diagnostic)
    merged = region_v2_1.merge_page(diagnostic)
    runs = [
        {"line_id": line_id, "text": run.text, "bbox": [round(value, 2) for value in run.bbox]}
        for line_id, line_runs in glyphs.items() for run in line_runs
    ]
    result: list[dict[str, Any]] = []

    for region_index, region in enumerate(merged["candidate_regions"]):
        instance_id = f"table_{document_id[:8]}_p{page_number}_r{region_index}"
        # Preserve the two intermediate frozen stages.  Their output is
        # intentionally not persisted; V0.3 is the canonical subgrid source.
        v0_table = asdict(cell_v0.reconstruct_table_cells(
            instance_id, document_id, page_number, region, runs,
        ))
        grid_v0_1.normalize_table_grid(v0_table)
        v04 = asdict(multiline_v0_4.reconstruct_multiline_table_v4(
            instance_id, document_id, page_number, region, runs,
        ))
        canonical = convert_v04_table_to_canonical(v04, {(document_id, page_number): page_id} if page_id else None)
        result.append(canonical_table_to_structural_model(canonical.to_dict()))
    return result
