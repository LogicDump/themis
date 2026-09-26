"""Conservative, non-mutating candidates for boundaries between PDF pages."""
from __future__ import annotations

import re
from typing import Any, Iterable

from core.documentos.embedded_document_signals_v1 import extract_embedded_document_signals


PIECE_BOUNDARY_CANDIDATES_VERSION = "v1"


def _page_regions(document_id: str, page: dict[str, Any]) -> list[dict[str, Any]]:
    number = page["page"]
    return [
        {"document_id": document_id, "pdf_page": number, "region_id": region["region_id"], "source_line_ids": list(region.get("source_line_ids", []))}
        for region in page.get("regions", [])
        if isinstance(region, dict) and isinstance(region.get("region_id"), str)
    ]


def _title_evidence(document_id: str, page: dict[str, Any]) -> dict[str, Any] | None:
    for block in page.get("blocks", []):
        if not isinstance(block, dict) or block.get("type_candidate") != "document_title":
            continue
        return {
            "kind": "VISUAL_DOCUMENT_TITLE_AT_PAGE_START",
            "polarity": "FOR_BOUNDARY",
            "strength": "WEAK",
            "source_map": [{
                "document_id": document_id,
                "pdf_page": page["page"],
                "region_id": None,
                "source_line_ids": list(block.get("source_line_ids", [])),
            }],
        }
    return None


def _explicit_text_continuity(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Require observable body continuation, not merely a page heuristic flag."""
    if left.get("continues_to_page") != right["page"] or right.get("continues_from_page") != left["page"]:
        return False
    left_body = [str(region.get("text") or "").strip() for region in left.get("regions", []) if isinstance(region, dict) and region.get("kind") == "body"]
    right_body = [str(region.get("text") or "").strip() for region in right.get("regions", []) if isinstance(region, dict) and region.get("kind") == "body"]
    if not left_body or not right_body:
        return False
    head = right_body[0].lstrip()
    # Lowercase prose or a continuing numbered item is observable continuity.
    # A fresh uppercase title/header must not be suppressed by a weak heuristic.
    return bool(head and (head[0].islower() or re.match(r"^\d+\s*[-.)]", head))) and _title_evidence("", right) is None


def _group_by_page(markers: dict[str, Any] | None) -> dict[int, dict[str, Any]]:
    if not isinstance(markers, dict) or markers.get("provider_document_marker_version") != "v1":
        return {}
    result: dict[int, dict[str, Any]] = {}
    for group in markers.get("groups", []):
        if not isinstance(group, dict):
            continue
        for page in group.get("pages", []):
            if isinstance(page, int):
                result[page] = group
    return result


def _embedded_by_page(markers: dict[str, Any] | None) -> dict[int, list[dict[str, Any]]]:
    result: dict[int, list[dict[str, Any]]] = {}
    if not isinstance(markers, dict) or markers.get("provider_document_marker_version") != "v1":
        return result
    for marker in markers.get("markers", []):
        if not isinstance(marker, dict) or marker.get("provenance_relationship") != "embedded_source" or not marker.get("fingerprint"):
            continue
        source = marker.get("source_map") if isinstance(marker.get("source_map"), dict) else {}
        page = source.get("pdf_page")
        if isinstance(page, int):
            result.setdefault(page, []).append(marker)
    return result


def _deduplicated_source_map(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result, seen = [], set()
    for item in evidence:
        for ref in item.get("source_map", []):
            if not isinstance(ref, dict):
                continue
            key = (ref.get("document_id"), ref.get("pdf_page"), ref.get("region_id"), tuple(ref.get("source_line_ids", [])))
            if key not in seen:
                seen.add(key)
                result.append(ref)
    return result


def detect_piece_boundary_candidates(
    document_id: str,
    page_structures: Iterable[dict[str, Any]],
    *,
    provider_document_markers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Emit explainable candidates only for consecutive factual PDF pages."""
    pages = sorted(
        (page for page in page_structures if isinstance(page, dict) and isinstance(page.get("page"), int)),
        key=lambda page: page["page"],
    )
    group_by_page = _group_by_page(provider_document_markers)
    embedded_by_page = _embedded_by_page(provider_document_markers)
    embedded_signals = extract_embedded_document_signals(
        document_id, pages, provider_document_markers=provider_document_markers,
        target_process_id=provider_document_markers.get("target_process_id") if isinstance(provider_document_markers, dict) else None,
    )
    signal_by_page = {item["page"]: item for item in embedded_signals["pages"]}
    candidates = []
    for left, right in zip(pages, pages[1:]):
        if right["page"] != left["page"] + 1:
            continue
        evidence: list[dict[str, Any]] = []
        submission_evidence: list[dict[str, Any]] = []
        left_group, right_group = group_by_page.get(left["page"]), group_by_page.get(right["page"])
        if left_group and right_group and left_group.get("provider_marker_group_id") == right_group.get("provider_marker_group_id"):
            source_map = list(left_group.get("source_map", []))
            submission_evidence.append({
                "kind": "SAME_OUTER_PROVIDER_MARKER_GROUP",
                "polarity": "AGAINST_BOUNDARY",
                "strength": "STRONG",
                "provider_marker_group_id": left_group.get("provider_marker_group_id"),
                "source_map": source_map,
            })
            evidence.append({
                "kind": "SAME_OUTER_PROVIDER_MARKER_GROUP",
                "polarity": "NEUTRAL",
                "strength": "FACTUAL_CONTEXT",
                "provider_marker_group_id": left_group.get("provider_marker_group_id"),
                "source_map": source_map,
            })
        elif left_group or right_group:
            source_map = []
            if left_group:
                source_map.extend(left_group.get("source_map", []))
            if right_group:
                source_map.extend(right_group.get("source_map", []))
            submission_evidence.append({
                "kind": "OUTER_PROVIDER_MARKER_GROUP_TRANSITION",
                "polarity": "FOR_BOUNDARY",
                "strength": "WEAK",
                "source_map": source_map,
            })
            evidence.append({
                "kind": "OUTER_PROVIDER_MARKER_GROUP_TRANSITION",
                "polarity": "NEUTRAL",
                "strength": "FACTUAL_CONTEXT",
                "source_map": source_map,
            })

        left_embedded, right_embedded = embedded_by_page.get(left["page"], []), embedded_by_page.get(right["page"], [])
        shared_fingerprints = {item["fingerprint"] for item in left_embedded}.intersection(item["fingerprint"] for item in right_embedded)
        if shared_fingerprints:
            refs = [item["source_map"] for item in left_embedded + right_embedded if item["fingerprint"] in shared_fingerprints]
            evidence.append({
                "kind": "SAME_EMBEDDED_PROVIDER_MARKER",
                "polarity": "AGAINST_BOUNDARY",
                "strength": "STRONG",
                "fingerprints": sorted(shared_fingerprints),
                "source_map": refs,
            })
        elif left_embedded or right_embedded:
            evidence.append({
                "kind": "EMBEDDED_PROVIDER_MARKER_TRANSITION",
                "polarity": "FOR_BOUNDARY",
                "strength": "WEAK",
                "source_map": [item["source_map"] for item in left_embedded + right_embedded],
            })

        left_signals, right_signals = signal_by_page[left["page"]], signal_by_page[right["page"]]
        left_refs = {item["process_id"]: item for item in left_signals["embedded_process_references"]}
        right_refs = {item["process_id"]: item for item in right_signals["embedded_process_references"]}
        common_refs = set(left_refs).intersection(right_refs)
        if common_refs:
            evidence.append({
                "kind": "SAME_EMBEDDED_PROCESS_REFERENCE",
                "polarity": "AGAINST_BOUNDARY",
                "strength": "MEDIUM",
                "process_references": sorted(common_refs),
                "source_map": [ref for process_id in sorted(common_refs) for ref in left_refs[process_id]["source_map"] + right_refs[process_id]["source_map"] if isinstance(ref, dict)],
            })
        elif left_refs or right_refs:
            evidence.append({
                "kind": "EMBEDDED_PROCESS_REFERENCE_TRANSITION",
                "polarity": "FOR_BOUNDARY",
                "strength": "WEAK",
                "source_map": [ref for signal in list(left_refs.values()) + list(right_refs.values()) for ref in signal["source_map"] if isinstance(ref, dict)],
            })
        left_folios = {item["value"] for item in left_signals["internal_folios"]}
        right_folios = {item["value"] for item in right_signals["internal_folios"]}
        continued_folios = sorted(value for value in left_folios if value + 1 in right_folios)
        if continued_folios:
            evidence.append({
                "kind": "INTERNAL_FOLIO_CONTINUITY",
                "polarity": "AGAINST_BOUNDARY",
                "strength": "STRONG",
                "folios": [{"before": value, "after": value + 1} for value in continued_folios],
                "source_map": [item["source_map"] for item in left_signals["internal_folios"] + right_signals["internal_folios"] if item["value"] in set(continued_folios) | {value + 1 for value in continued_folios}],
            })
        elif left_folios and right_folios and min(right_folios) <= min(left_folios):
            evidence.append({
                "kind": "INTERNAL_FOLIO_RESTART",
                "polarity": "FOR_BOUNDARY",
                "strength": "WEAK",
                "source_map": [item["source_map"] for item in left_signals["internal_folios"] + right_signals["internal_folios"]],
            })
        left_headers = {item["text_key"]: item for item in left_signals["repeated_headers"]}
        right_headers = {item["text_key"]: item for item in right_signals["repeated_headers"]}
        common_headers = set(left_headers).intersection(right_headers)
        if common_headers:
            evidence.append({
                "kind": "REPEATED_INTERNAL_HEADER",
                "polarity": "AGAINST_BOUNDARY",
                "strength": "MEDIUM",
                "headers": sorted(common_headers),
                "source_map": [left_headers[key]["source_map"] for key in sorted(common_headers)] + [right_headers[key]["source_map"] for key in sorted(common_headers)],
            })

        if _explicit_text_continuity(left, right):
            evidence.append({
                "kind": "EXPLICIT_TEXT_CONTINUITY",
                "polarity": "AGAINST_BOUNDARY",
                "strength": "STRONG",
                "source_map": _page_regions(document_id, left) + _page_regions(document_id, right),
            })
        title = _title_evidence(document_id, right)
        if title:
            evidence.append(title)
        for page in (left, right):
            if page.get("quality") in {"BAD", "SCANNED", "EMPTY"}:
                evidence.append({
                    "kind": "LOW_TEXTUAL_EVIDENCE",
                    "polarity": "NEUTRAL",
                    "strength": "NONE",
                    "quality": page.get("quality"),
                    "source_map": _page_regions(document_id, page),
                })

        strong_against = any(item["polarity"] == "AGAINST_BOUNDARY" and item["strength"] == "STRONG" for item in evidence)
        positive_kinds = {item["kind"] for item in evidence if item["polarity"] == "FOR_BOUNDARY"}
        inferred = not strong_against and {"EMBEDDED_PROVIDER_MARKER_TRANSITION", "VISUAL_DOCUMENT_TITLE_AT_PAGE_START"}.issubset(positive_kinds)
        status, confidence = ("INFERRED", "MEDIUM") if inferred else ("UNRESOLVED", "NONE")
        candidates.append({
            "boundary_candidate_id": f"pb-{left['page']:04d}-{right['page']:04d}",
            "boundary_level": "PIECE",
            "before_anchor": {"document_id": document_id, "pdf_page": left["page"], "region_id": None},
            "after_anchor": {"document_id": document_id, "pdf_page": right["page"], "region_id": None},
            "status": status,
            "confidence": confidence,
            "evidence": evidence,
            "source_map": _deduplicated_source_map(evidence),
            "submission_boundary": {
                "boundary_level": "SUBMISSION",
                "status": "UNRESOLVED",
                "confidence": "NONE",
                "evidence": submission_evidence,
                "source_map": _deduplicated_source_map(submission_evidence),
            },
        })
    return {
        "piece_boundary_candidates_version": PIECE_BOUNDARY_CANDIDATES_VERSION,
        "document_id": document_id,
        "candidates": candidates,
    }
