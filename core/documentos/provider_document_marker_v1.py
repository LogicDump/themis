"""Generic, in-memory contract for provider-originated document markers."""
from __future__ import annotations

from typing import Any, Iterable


PROVIDER_DOCUMENT_MARKER_VERSION = "v1"


def _provider_artifact_groups(
    *,
    provider: str,
    document_id: str,
    target_process_id: str | None,
    markers: list[dict[str, Any]],
    groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Partition consecutive outer markers by provider artifact/upload identity."""
    marker_by_id = {marker["marker_id"]: marker for marker in markers}
    embedded_by_page: dict[int, list[dict[str, Any]]] = {}
    for marker in markers:
        if marker.get("provenance_relationship") != "embedded_source":
            continue
        source = marker.get("source_map") if isinstance(marker.get("source_map"), dict) else {}
        if isinstance(source.get("pdf_page"), int):
            embedded_by_page.setdefault(source["pdf_page"], []).append(marker)

    result: list[dict[str, Any]] = []
    for movement_group in groups:
        parent_id = movement_group["provider_marker_group_id"]
        current: dict[str, Any] | None = None
        previous_page: int | None = None
        for marker_id in movement_group.get("marker_ids", []):
            marker = marker_by_id.get(marker_id)
            if marker is None:
                continue
            source = marker.get("source_map") if isinstance(marker.get("source_map"), dict) else {}
            page = source.get("pdf_page")
            fingerprint = marker.get("artifact_fingerprint") or marker.get("fingerprint")
            if not isinstance(page, int) or not isinstance(fingerprint, str):
                if current:
                    result.append(current)
                current = None
                previous_page = page if isinstance(page, int) else None
                continue
            same_artifact = (
                current is not None
                and previous_page == page - 1
                and current["artifact_fingerprint"] == fingerprint
            )
            if not same_artifact:
                if current:
                    result.append(current)
                current = {
                    "provider_artifact_group_id": f"{provider}:{parent_id}:artifact:{page:04d}:{fingerprint[:16]}",
                    "provider": provider,
                    "document_id": document_id,
                    "target_process_id": target_process_id,
                    "provider_marker_group_id": parent_id,
                    "movement_fingerprint": movement_group.get("fingerprint"),
                    "artifact_fingerprint": fingerprint,
                    "artifact_fingerprint_basis": marker.get("artifact_fingerprint_basis") or marker.get("fingerprint_basis"),
                    "pages": [],
                    "marker_ids": [],
                    "markers": [],
                    "source_map": [],
                    "source_maps": [],
                    "embedded_sources": [],
                }
            current["pages"].append(page)
            current["marker_ids"].append(marker_id)
            current["markers"].append(marker)
            current["source_map"].append(source)
            current["source_maps"].extend(
                marker.get("source_maps") if isinstance(marker.get("source_maps"), list) else [source]
            )
            # Embedded material is retained as a subordinate observation.  Its
            # key never participates in the external provider-document split.
            for embedded in embedded_by_page.get(page, []):
                current["embedded_sources"].append({
                    "marker_id": embedded["marker_id"],
                    "artifact_fingerprint": embedded.get("artifact_fingerprint") or embedded.get("fingerprint"),
                    "movement_fingerprint": embedded.get("movement_fingerprint"),
                    "source_map": embedded.get("source_map"),
                })
            previous_page = page
        if current:
            result.append(current)
    return result


def build_provider_document_marker_projection(
    *,
    provider: str,
    document_id: str,
    target_process_id: str | None,
    markers: Iterable[dict[str, Any]],
    groups: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Wrap provider-neutral marker observations without changing their facts."""
    ordered_markers = sorted(
        (dict(marker) for marker in markers if isinstance(marker, dict) and isinstance(marker.get("marker_id"), str)),
        key=lambda marker: (marker.get("source_map", {}).get("pdf_page", 0), marker["marker_id"]),
    )
    ordered_groups = sorted(
        (dict(group) for group in groups if isinstance(group, dict) and isinstance(group.get("provider_marker_group_id"), str)),
        key=lambda group: (group.get("pages", [0])[0] if group.get("pages") else 0, group["provider_marker_group_id"]),
    )
    return {
        "provider_document_marker_version": PROVIDER_DOCUMENT_MARKER_VERSION,
        "provider": provider,
        "document_id": document_id,
        "target_process_id": target_process_id,
        "markers": ordered_markers,
        "groups": ordered_groups,
        "provider_artifact_groups": _provider_artifact_groups(
            provider=provider,
            document_id=document_id,
            target_process_id=target_process_id,
            markers=ordered_markers,
            groups=ordered_groups,
        ),
    }
