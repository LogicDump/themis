"""Non-mutating L1 page/region structure for a canonical PDF document.

This module deliberately does not identify legal documents, sections, or
document boundaries.  It merely makes the two already available orders
explicit: PDF/source order and a conservative geometry-derived reading order.
"""
from __future__ import annotations

import math
from typing import Any, Iterable


DOCUMENT_STRUCTURE_VERSION = "v1"
_ROW_TOLERANCE = 3.0


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _bbox(region: dict[str, Any]) -> tuple[float, float, float, float] | None:
    value = region.get("bbox")
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    numbers = tuple(_number(item) for item in value)
    if any(item is None for item in numbers):
        return None
    x0, y0, x1, y1 = numbers  # type: ignore[misc]
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def _source_ref(document_id: str, page: int, region: dict[str, Any]) -> dict[str, Any]:
    return {
        "document_id": document_id,
        "pdf_page": page,
        "region_id": region["region_id"],
        "source_line_ids": list(region.get("source_line_ids", [])),
    }


def _regions(page_structure: dict[str, Any]) -> list[dict[str, Any]]:
    regions = page_structure.get("regions", [])
    if not isinstance(regions, list):
        return []
    # Keep the canonical list order.  It is the available factual source order;
    # specifically, do not derive it from the region identifier or geometry.
    return [region for region in regions if isinstance(region, dict) and isinstance(region.get("region_id"), str)]


def _overlap(first: tuple[float, float, float, float], second: tuple[float, float, float, float]) -> bool:
    return min(first[2], second[2]) > max(first[0], second[0]) and min(first[3], second[3]) > max(first[1], second[1])


def _same_row(first: tuple[float, float, float, float], second: tuple[float, float, float, float]) -> bool:
    return abs(first[3] - second[3]) <= _ROW_TOLERANCE and abs(first[1] - second[1]) <= _ROW_TOLERANCE


def _narrow_overlay(candidate: tuple[float, float, float, float], other: tuple[float, float, float, float]) -> bool:
    """Identify a geometrically independent overlay without interpreting it."""
    candidate_width = candidate[2] - candidate[0]
    other_width = other[2] - other[0]
    # A small height alone is common for ordinary text lines, so it cannot
    # establish an overlay.  Narrow vertical marks/signatures can.
    return candidate_width <= other_width * 0.25


def _geometry_slots(regions: list[dict[str, Any]], document_id: str, page: int) -> list[dict[str, Any]]:
    """Produce conservative, ordered reading slots without breaking ties silently."""
    usable: list[tuple[dict[str, Any], tuple[float, float, float, float]]] = []
    invalid: list[dict[str, Any]] = []
    for region in regions:
        bbox = _bbox(region)
        (usable if bbox is not None else invalid).append((region, bbox) if bbox is not None else region)  # type: ignore[arg-type]

    # A narrow item painted over a wide item is an independent overlay.  Its
    # relative reading position is unknown, but it must not make every region
    # beneath it an unordered set.
    overlays: list[tuple[dict[str, Any], tuple[float, float, float, float], list[str]]] = []
    flow: list[tuple[dict[str, Any], tuple[float, float, float, float]]] = []
    for region, bbox in usable:
        overlapped = [other[0]["region_id"] for other in usable if other[0] is not region and _overlap(bbox, other[1]) and _narrow_overlay(bbox, other[1])]
        if overlapped:
            overlays.append((region, bbox, sorted(overlapped)))
        else:
            flow.append((region, bbox))

    # The sort is only a candidate traversal.  Ambiguous peers are emitted as a
    # single unordered slot below, rather than becoming a hidden tie-break.
    remaining = sorted(flow, key=lambda item: (-item[1][3], item[1][0], item[0]["region_id"]))
    slots: list[dict[str, Any]] = []
    position = 1
    while remaining:
        first, first_bbox = remaining.pop(0)
        peers = [(first, first_bbox)]
        unresolved_reason: str | None = None
        for candidate, candidate_bbox in list(remaining):
            if _overlap(first_bbox, candidate_bbox):
                peers.append((candidate, candidate_bbox))
                remaining.remove((candidate, candidate_bbox))
                unresolved_reason = "OVERLAPPING_BBOX"
            elif not _same_row(first_bbox, candidate_bbox) and min(first_bbox[3], candidate_bbox[3]) > max(first_bbox[1], candidate_bbox[1]):
                peers.append((candidate, candidate_bbox))
                remaining.remove((candidate, candidate_bbox))
                unresolved_reason = "VERTICALLY_OVERLAPPING_COLUMNS"

        if unresolved_reason:
            # Region IDs only stabilize the representation of an unresolved set;
            # they never establish its reading order.
            peers.sort(key=lambda item: item[0]["region_id"])
            slots.append({
                "reading_order_position": position,
                "status": "UNRESOLVED",
                "reason": unresolved_reason,
                "region_refs": [_source_ref(document_id, page, region) for region, _ in peers],
            })
        else:
            slots.append({
                "reading_order_position": position,
                "status": "RESOLVED",
                "method": "GEOMETRY_TOP_TO_BOTTOM_LEFT_TO_RIGHT",
                "region_refs": [_source_ref(document_id, page, first)],
            })
        position += 1

    for region, _bbox_value, overlapped in sorted(overlays, key=lambda item: (-item[1][3], item[1][0], item[0]["region_id"])):
        slots.append({
            "reading_order_position": position,
            "status": "UNRESOLVED",
            "reason": "INDEPENDENT_OVERLAY",
            "related_region_ids": overlapped,
            "region_refs": [_source_ref(document_id, page, region)],
        })
        position += 1

    for region in invalid:
        slots.append({
            "reading_order_position": position,
            "status": "UNRESOLVED",
            "reason": "MISSING_OR_INVALID_BBOX",
            "region_refs": [_source_ref(document_id, page, region)],
        })
        position += 1
    return slots


def build_document_structure(document_id: str, page_structures: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Build deterministic L1 structure from already-canonical page structures."""
    pages: list[dict[str, Any]] = []
    source_map: list[dict[str, Any]] = []
    valid_pages = [item for item in page_structures if isinstance(item, dict) and isinstance(item.get("page"), int)]
    for page_structure in sorted(valid_pages, key=lambda item: item["page"]):
        page = page_structure["page"]
        regions = _regions(page_structure)
        source_order = []
        for index, region in enumerate(regions, start=1):
            ref = _source_ref(document_id, page, region)
            source_order.append({"source_order_position": index, **ref})
            source_map.append(ref)
        pages.append({
            "page": page,
            "page_order": len(pages) + 1,
            "regions_version": page_structure.get("regions_version"),
            "source_order": source_order,
            "reading_order": _geometry_slots(regions, document_id, page),
        })
    return {
        "document_structure_version": DOCUMENT_STRUCTURE_VERSION,
        "document_id": document_id,
        "pages": pages,
        "source_map": source_map,
    }
