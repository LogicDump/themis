"""Deterministic, non-mutating projections over canonical page regions."""
from __future__ import annotations

from typing import Any, Iterable


PROJECTION_VERSION = "source-mapped-projection-v1"


def _selection(values: Iterable[str] | None) -> set[str] | None:
    if values is None:
        return None
    return {str(value) for value in values}


def _ordered_regions(page_structure: dict[str, Any]) -> list[dict[str, Any]]:
    regions = page_structure.get("regions", [])
    if not isinstance(regions, list):
        return []
    # Page structures already retain their factual extraction order.  Never
    # promote a deterministic region identifier into a reading order.
    return [region for region in regions if isinstance(region, dict) and isinstance(region.get("region_id"), str)]


def _selected_regions(
    page_structure: dict[str, Any],
    *,
    include_region_ids: Iterable[str] | None = None,
    exclude_region_ids: Iterable[str] | None = None,
    include_region_kinds: Iterable[str] | None = None,
    exclude_region_kinds: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    include_ids, exclude_ids = _selection(include_region_ids), _selection(exclude_region_ids) or set()
    include_kinds, exclude_kinds = _selection(include_region_kinds), _selection(exclude_region_kinds) or set()
    result = []
    for region in _ordered_regions(page_structure):
        region_id, kind = region["region_id"], str(region.get("kind", "unknown"))
        if include_ids is not None and region_id not in include_ids:
            continue
        if include_kinds is not None and kind not in include_kinds:
            continue
        if region_id in exclude_ids or kind in exclude_kinds:
            continue
        result.append(region)
    return result


def _structure_page(document_structure: dict[str, Any] | None, page: Any) -> dict[str, Any] | None:
    if not isinstance(document_structure, dict) or document_structure.get("document_structure_version") != "v1":
        return None
    for candidate in document_structure.get("pages", []):
        if isinstance(candidate, dict) and candidate.get("page") == page:
            return candidate
    return None


def _ordered_selected_regions(
    selected: list[dict[str, Any]], structure_page: dict[str, Any] | None,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Apply explicit L1 reading slots, retaining uncertainty in each segment."""
    if structure_page is None:
        return [(region, {
            "ordering_status": "UNRESOLVED",
            "ordering_reason": "DOCUMENT_STRUCTURE_NOT_PROVIDED",
            "serialization_order": "SOURCE_ORDER_UNRESOLVED",
            "unresolved_region_ids": [region["region_id"]],
        }) for region in selected]

    selected_by_id = {region["region_id"]: region for region in selected}
    source_positions = {
        ref.get("region_id"): ref.get("source_order_position")
        for ref in structure_page.get("source_order", [])
        if isinstance(ref, dict) and isinstance(ref.get("region_id"), str)
    }
    result: list[tuple[dict[str, Any], dict[str, Any]]] = []
    used: set[str] = set()
    for slot in structure_page.get("reading_order", []):
        if not isinstance(slot, dict):
            continue
        references = [ref for ref in slot.get("region_refs", []) if isinstance(ref, dict) and isinstance(ref.get("region_id"), str)]
        present = [ref for ref in references if ref["region_id"] in selected_by_id]
        if not present:
            continue
        status = str(slot.get("status", "UNRESOLVED"))
        if status == "RESOLVED":
            ordered_refs = present
        else:
            # The order is needed to serialize text, but it is deliberately
            # factual source order rather than a claim of a resolved reading.
            ordered_refs = sorted(present, key=lambda ref: (source_positions.get(ref["region_id"], 10**9), ref["region_id"]))
        group_region_ids = [ref["region_id"] for ref in references]
        for ref in ordered_refs:
            region_id = ref["region_id"]
            if region_id in used:
                continue
            used.add(region_id)
            result.append((selected_by_id[region_id], {
                "ordering_status": status,
                "reading_order_position": slot.get("reading_order_position"),
                "ordering_reason": slot.get("reason"),
                "serialization_order": "READING_ORDER" if status == "RESOLVED" else "SOURCE_ORDER_UNRESOLVED",
                "unresolved_region_ids": group_region_ids if status != "RESOLVED" else None,
            }))
    # A partial or malformed L1 input must not cause canonical text to vanish.
    for region in sorted((item for item in selected if item["region_id"] not in used), key=lambda item: (source_positions.get(item["region_id"], 10**9), item["region_id"])):
        result.append((region, {
            "ordering_status": "UNRESOLVED",
            "ordering_reason": "MISSING_READING_ORDER_ENTRY",
            "serialization_order": "SOURCE_ORDER_UNRESOLVED",
            "unresolved_region_ids": [region["region_id"]],
        }))
    return result


def _asset_refs(
    page_structure: dict[str, Any], selected_region_ids: set[str], *, include_visual_assets: bool,
    include_visual_asset_ids: Iterable[str] | None,
) -> list[dict[str, Any]]:
    requested = _selection(include_visual_asset_ids)
    if not include_visual_assets and requested is None:
        return []
    refs = []
    for asset in page_structure.get("visual_assets", []):
        if not isinstance(asset, dict) or not isinstance(asset.get("visual_asset_id"), str):
            continue
        asset_id = asset["visual_asset_id"]
        overlaps = [str(value) for value in asset.get("overlapping_region_ids", [])]
        if requested is not None:
            if asset_id not in requested:
                continue
        elif not set(overlaps).intersection(selected_region_ids):
            continue
        source = asset.get("visual_asset_source") if isinstance(asset.get("visual_asset_source"), dict) else {}
        refs.append({
            "visual_asset_id": asset_id,
            "page": asset.get("page", page_structure.get("page")),
            "kind": asset.get("kind", "unknown"),
            "bbox": asset.get("bbox"),
            "overlapping_region_ids": overlaps,
            "blob_sha256": source.get("blob_sha256"),
            "source_identity_sha256": source.get("source_identity_sha256"),
        })
    return sorted(refs, key=lambda asset: asset["visual_asset_id"])


def project_page(
    page_structure: dict[str, Any],
    *,
    document_structure: dict[str, Any] | None = None,
    include_region_ids: Iterable[str] | None = None,
    exclude_region_ids: Iterable[str] | None = None,
    include_region_kinds: Iterable[str] | None = None,
    exclude_region_kinds: Iterable[str] | None = None,
    include_visual_assets: bool = False,
    include_visual_asset_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Project exact canonical region text with deterministic provenance spans."""
    selected = _selected_regions(
        page_structure,
        include_region_ids=include_region_ids,
        exclude_region_ids=exclude_region_ids,
        include_region_kinds=include_region_kinds,
        exclude_region_kinds=exclude_region_kinds,
    )
    structure_page = _structure_page(document_structure, page_structure.get("page"))
    ordered = _ordered_selected_regions(selected, structure_page)
    content_parts: list[str] = []
    source_map: list[dict[str, Any]] = []
    offset = 0
    page = page_structure.get("page")
    for index, (region, ordering) in enumerate(ordered):
        if index:
            content_parts.append("\n\n")
            offset += 2
        text = str(region.get("text", ""))
        content_parts.append(text)
        segment = {
            "segment_id": f"p{page}-s{index + 1:04d}",
            "start_offset": offset,
            "end_offset": offset + len(text),
            "page": page,
            "region_id": region["region_id"],
            "region_kind": region.get("kind", "unknown"),
            "source_line_ids": list(region.get("source_line_ids", [])),
            "bbox": region.get("bbox"),
            **ordering,
        }
        if isinstance(document_structure, dict) and isinstance(document_structure.get("document_id"), str):
            segment["document_id"] = document_structure["document_id"]
        source_map.append(segment)
        offset += len(text)
    selected_ids = {region["region_id"] for region in selected}
    return {
        "projection_version": PROJECTION_VERSION,
        "page": page,
        "document_structure_version": document_structure.get("document_structure_version") if isinstance(document_structure, dict) else None,
        "content": "".join(content_parts),
        "source_map": source_map,
        "visual_asset_refs": _asset_refs(
            page_structure, selected_ids,
            include_visual_assets=include_visual_assets,
            include_visual_asset_ids=include_visual_asset_ids,
        ),
    }


def project_document(
    page_structures: Iterable[dict[str, Any]], *, document_structure: dict[str, Any] | None = None, **selection: Any,
) -> dict[str, Any]:
    """Compose page projections while translating every provenance offset."""
    raw_pages = [page for page in page_structures if isinstance(page, dict)]
    if isinstance(document_structure, dict) and document_structure.get("document_structure_version") == "v1":
        by_number = {page.get("page"): page for page in raw_pages}
        factual_numbers = [item.get("page") for item in document_structure.get("pages", []) if isinstance(item, dict)]
        ordered_raw = [by_number.pop(number) for number in factual_numbers if number in by_number]
        ordered_raw.extend(sorted(by_number.values(), key=lambda value: value.get("page", 0)))
    else:
        ordered_raw = sorted(raw_pages, key=lambda value: value.get("page", 0))
    pages = [project_page(page, document_structure=document_structure, **selection) for page in ordered_raw]
    content_parts: list[str] = []
    source_map: list[dict[str, Any]] = []
    visual_asset_refs: list[dict[str, Any]] = []
    offset = 0
    for index, page in enumerate(pages):
        if index:
            content_parts.append("\n\n")
            offset += 2
        content_parts.append(page["content"])
        for segment in page["source_map"]:
            source_map.append({
                **segment,
                "start_offset": segment["start_offset"] + offset,
                "end_offset": segment["end_offset"] + offset,
            })
        visual_asset_refs.extend(page["visual_asset_refs"])
        offset += len(page["content"])
    return {
        "projection_version": PROJECTION_VERSION,
        "document_structure_version": document_structure.get("document_structure_version") if isinstance(document_structure, dict) else None,
        "content": "".join(content_parts),
        "source_map": source_map,
        "visual_asset_refs": visual_asset_refs,
        "pages": pages,
    }
