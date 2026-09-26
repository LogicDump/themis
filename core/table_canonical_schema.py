"""Canonical Table Structure Schema V1.

Defines the unified, lossless schema for structured table extraction in Themis:
TableInstance -> SubGrid -> Row -> Cell.

Explicitly distinguishes:
1. Physical / Original Extraction Data (bboxes, glyph runs, source line ids, doc/page provenance)
2. Derived Geometric Grid Structure (row/col indices, spans, empty indicators, multiline text)
3. Optional Future Semantic Classification Fields (semantic_role, data_type, table_type)
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CanonicalCell:
    """Represents a single cell within a canonical table row."""
    # Derived Geometric Grid Coordinates
    row_index: int
    col_index: int
    row_span: int = 1
    col_span: int = 1
    is_empty: bool = False

    # Physical / Extracted Text & Geometry
    text: str = ""
    bbox: list[float] = field(default_factory=list)  # [x0, y0, x1, y1] in pt
    source_line_ids: list[str] = field(default_factory=list)
    glyph_run_count: int = 0

    # Optional Future Semantic Classification
    semantic_role: str | None = None  # e.g., 'header', 'data', 'summary', 'label', 'value'
    data_type: str | None = None      # e.g., 'text', 'numeric', 'currency', 'date'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CanonicalCell:
        return cls(
            row_index=data["row_index"],
            col_index=data["col_index"],
            row_span=data.get("row_span", 1),
            col_span=data.get("col_span", 1),
            is_empty=data.get("is_empty", False),
            text=data.get("text", ""),
            bbox=[round(x, 2) for x in data.get("bbox", [])],
            source_line_ids=data.get("source_line_ids", []),
            glyph_run_count=data.get("glyph_run_count", 0),
            semantic_role=data.get("semantic_role"),
            data_type=data.get("data_type"),
        )


@dataclass
class CanonicalRow:
    """Represents a single row of cells in a SubGrid."""
    row_index: int
    bbox: list[float] = field(default_factory=list)  # [x0, y0, x1, y1] in pt
    cells: list[CanonicalCell] = field(default_factory=list)

    # Optional Future Semantic Classification
    semantic_role: str | None = None  # e.g., 'header_row', 'data_row', 'summary_row'

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_index": self.row_index,
            "bbox": [round(x, 2) for x in self.bbox],
            "cells": [c.to_dict() for c in self.cells],
            "semantic_role": self.semantic_role,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CanonicalRow:
        return cls(
            row_index=data["row_index"],
            bbox=[round(x, 2) for x in data.get("bbox", [])],
            cells=[CanonicalCell.from_dict(c) for c in data.get("cells", [])],
            semantic_role=data.get("semantic_role"),
        )


@dataclass
class CanonicalColumnSlot:
    """Represents a physical/logical column slot interval."""
    col_index: int
    x0: float
    x1: float
    alignment: str = "left"  # 'left', 'right', 'center'
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "col_index": self.col_index,
            "x0": round(self.x0, 2),
            "x1": round(self.x1, 2),
            "alignment": self.alignment,
            "confidence": round(self.confidence, 2),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CanonicalColumnSlot:
        return cls(
            col_index=data["col_index"],
            x0=round(data["x0"], 2),
            x1=round(data["x1"], 2),
            alignment=data.get("alignment", "left"),
            confidence=round(data.get("confidence", 1.0), 2),
        )


@dataclass
class CanonicalSubGrid:
    """Represents a structurally homogeneous 2D matrix of rows and columns."""
    subgrid_index: int
    bbox: list[float] = field(default_factory=list)  # [x0, y0, x1, y1] in pt
    row_count: int = 0
    col_count: int = 0
    column_slots: list[CanonicalColumnSlot] = field(default_factory=list)
    rows: list[CanonicalRow] = field(default_factory=list)

    # Optional Future Semantic Classification
    section_type: str | None = None  # e.g., 'header_section', 'body_section', 'footer_section'

    def to_dict(self) -> dict[str, Any]:
        return {
            "subgrid_index": self.subgrid_index,
            "bbox": [round(x, 2) for x in self.bbox],
            "row_count": self.row_count,
            "col_count": self.col_count,
            "column_slots": [s.to_dict() for s in self.column_slots],
            "rows": [r.to_dict() for r in self.rows],
            "section_type": self.section_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CanonicalSubGrid:
        rows = [CanonicalRow.from_dict(r) for r in data.get("rows", [])]
        slots = [CanonicalColumnSlot.from_dict(s) for s in data.get("column_slots", [])]
        return cls(
            subgrid_index=data["subgrid_index"],
            bbox=[round(x, 2) for x in data.get("bbox", data.get("subgrid_bbox", []))],
            row_count=data.get("row_count", data.get("num_rows", len(rows))),
            col_count=data.get("col_count", data.get("num_cols", len(slots))),
            column_slots=slots,
            rows=rows,
            section_type=data.get("section_type"),
        )


@dataclass
class CanonicalProvenance:
    """Tracks extraction provenance and confidence from Table Region Assembler V2.1."""
    source_engine: str = "THEMIS-TABLE-REGION-V2.1"
    assembler_version: str = "2.1"
    cell_engine_version: str = "0.4"
    source_line_count: int = 0
    source_run_count: int = 0
    confidence: str = "strong"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CanonicalProvenance:
        return cls(
            source_engine=data.get("source_engine", "THEMIS-TABLE-REGION-V2.1"),
            assembler_version=data.get("assembler_version", "2.1"),
            cell_engine_version=data.get("cell_engine_version", "0.4"),
            source_line_count=data.get("source_line_count", 0),
            source_run_count=data.get("source_run_count", 0),
            confidence=data.get("confidence", "strong"),
        )


@dataclass
class CanonicalTableInstance:
    """Canonical representation of an independent physical table instance."""
    instance_id: str
    document_id: str
    page_number: int
    page_id: str | None = None
    region_bbox: list[float] = field(default_factory=list)  # [x0, y0, x1, y1] in pt
    is_compound: bool = False
    subgrid_count: int = 1
    subgrids: list[CanonicalSubGrid] = field(default_factory=list)
    provenance: CanonicalProvenance = field(default_factory=CanonicalProvenance)

    # Optional Future Semantic Classification
    table_type: str | None = None  # e.g., 'financial_statement', 'paystub', 'tax_return', 'police_report'

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "page_id": self.page_id,
            "region_bbox": [round(x, 2) for x in self.region_bbox],
            "is_compound": self.is_compound,
            "subgrid_count": self.subgrid_count,
            "subgrids": [s.to_dict() for s in self.subgrids],
            "provenance": self.provenance.to_dict(),
            "table_type": self.table_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CanonicalTableInstance:
        subgrids = [CanonicalSubGrid.from_dict(s) for s in data.get("subgrids", [])]
        prov_data = data.get("provenance", {})
        if not isinstance(prov_data, dict):
            prov = CanonicalProvenance()
        else:
            prov = CanonicalProvenance.from_dict(prov_data)

        return cls(
            instance_id=data["instance_id"],
            document_id=data["document_id"],
            page_number=data.get("page_number", data.get("pdf_page", 1)),
            page_id=data.get("page_id"),
            region_bbox=[round(x, 2) for x in data.get("region_bbox", [])],
            is_compound=data.get("is_compound", len(subgrids) > 1),
            subgrid_count=data.get("subgrid_count", data.get("num_subgrids", len(subgrids))),
            subgrids=subgrids,
            provenance=prov,
            table_type=data.get("table_type"),
        )
