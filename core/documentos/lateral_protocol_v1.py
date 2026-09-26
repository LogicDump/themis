"""Factual projection of lateral e-SAJ protocol and release markings."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any, Iterable

from core.documentos.provider_document_marker_v1 import build_provider_document_marker_projection


LATERAL_PROTOCOL_VERSION = "v1"
_CNJ = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")
_ESAJ_ATTESTATION = re.compile(r"(Este\s+documento.{0,1800}?fls\.\s*\d+)", re.IGNORECASE | re.DOTALL)


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower().split())


def _source_map(document_id: str, page: int, region: dict[str, Any]) -> dict[str, Any]:
    return {
        "document_id": document_id,
        "pdf_page": page,
        "region_id": region["region_id"],
        "source_line_ids": list(region.get("source_line_ids", [])),
    }


def _fields(text: str) -> dict[str, Any]:
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]", " ", text)
    normalized = _normalized(text)
    # e-SAJ can omit the calendar date in the lateral attestation while still
    # supplying the provider event and clock time.  Keep the missing date
    # factual instead of discarding those two explicit fields.
    event_match = re.search(r"\b(protocolado|liberado nos autos)\s+em\s+(?:(\d{2}/\d{2}/\d{4})[^\d]{0,12})?(?:as\s+)?(\d{1,2}:\d{2})", normalized)
    signer_match = re.search(r"assinado digitalmente por\s+(.+?)(?=,?\s*(?:protocolado|liberado nos autos)\b|\.|$)", text, re.IGNORECASE | re.DOTALL)
    protocol_match = re.search(r"\b(WPRC[A-Za-z0-9]+)\b", text, re.IGNORECASE)
    code_match = re.search(r"c.{0,3}digo\s+([A-Za-z0-9]+)(?:\.|\s|$)", text, re.IGNORECASE)
    url_match = re.search(r"https?://[^\s,]+", text, re.IGNORECASE)
    signer = " ".join(signer_match.group(1).split()) if signer_match else None
    # This is a fixed provider attestation tail, not part of the person's
    # signature.  Preserve it in raw_text, but never project it as the actor.
    if signer:
        signer = re.sub(r"\s+e\s+Tribunal\s+de\s+Justi.a\s+do\s+Estado\s+de\s+S.o\s+Paulo\s*$", "", signer, flags=re.IGNORECASE).strip() or None
    event_date = event_match.group(2) if event_match else None
    event_time = event_match.group(3) if event_match else None
    return {
        "event": event_match.group(1).upper() if event_match else None,
        "event_date": event_date,
        "event_time": event_time,
        "event_at": f"{event_date} {event_time}" if event_date and event_time else None,
        # Compatibility aliases for consumers of the first marker projection.
        "occurred_on": event_date,
        "occurred_at": event_time,
        "signatory_literal": signer,
        "protocol_number": protocol_match.group(1) if protocol_match else None,
        "verification_code": code_match.group(1) if code_match else None,
        "verification_url": url_match.group(0) if url_match else None,
        "process_references": sorted(set(_CNJ.findall(text))),
    }


def _esaj_attestations(pdfium_page_text: str) -> list[str]:
    """Return only complete e-SAJ attestations from a PDFium page dump."""
    return [
        " ".join(match.group(1).split())
        for match in _ESAJ_ATTESTATION.finditer(pdfium_page_text)
        if "para conferir o original" in _normalized(match.group(1))
    ]


def _recovered_attestation(region_text: str, pdfium_page_text: str | None) -> str:
    """Restore a legacy compacted lateral line by its provider verification code.

    Historical structures retained the lateral bbox but not their raw PDFium
    line.  The verification code is a provider-issued identity contained in
    both strings, so this never searches the legal body for a date.
    """
    if not pdfium_page_text:
        return region_text
    code = _fields(region_text).get("verification_code")
    if not code:
        return region_text
    matches = [text for text in _esaj_attestations(pdfium_page_text) if _fields(text).get("verification_code") == code]
    return matches[0] if len(matches) == 1 else region_text


def _is_esaj_lateral(region: dict[str, Any]) -> bool:
    text = str(region.get("raw_text") or region.get("text") or "")
    normalized = _normalized(text)
    if (
        "assinado digitalmente por" in normalized
        or "para conferir o original" in normalized
        or "pastadigital" in normalized
        or "liberado nos autos" in normalized
    ):
        return True
    return region.get("kind") in {"signature", "stamp", "unknown"}


def _outer_score(record: dict[str, Any], target_process_id: str | None) -> tuple[int, float, str]:
    fields = record["fields"]
    refs = fields["process_references"]
    target_match = target_process_id in refs if target_process_id else None
    x0, _y0, x1, y1 = record["bbox"]
    width, height = max(0.0, x1 - x0), max(0.0, y1 - _y0)
    # A full-height, wider e-SAJ strip is normally the filing envelope.  The
    # score only selects the outer candidate; it never changes embedded data.
    return (
        4 if target_match else 3 if fields["protocol_number"] else 2 if fields["event"] else 1,
        width * height,
        record["lateral_protocol_id"],
    )


def _fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _movement_fingerprint(fields: dict[str, Any], target_process_id: str | None) -> tuple[str | None, str | None]:
    """Identify an outer filing/release without using its per-document code."""
    protocol = fields.get("protocol_number")
    if isinstance(protocol, str) and protocol.upper().startswith("WPRC"):
        # WPRC is the provider's movement/protocol identity.  Do not add
        # display metadata that can vary across pages of the same envelope.
        return _fingerprint({"identity_kind": "WPRC", "identity_value": protocol.upper()}), "WPRC"
    if not all(fields.get(key) for key in ("event", "occurred_on", "occurred_at", "signatory_literal")):
        return None, None
    payload = {
        "identity_kind": "EVENT_LITERAL",
        "process_id": target_process_id,
        "event": fields["event"],
        "occurred_on": fields["occurred_on"],
        "occurred_at": fields["occurred_at"],
        "signatory_literal": fields["signatory_literal"],
    }
    return _fingerprint(payload), "EVENT_LITERAL"


def _artifact_fingerprint(fields: dict[str, Any]) -> tuple[str | None, str | None]:
    """The conference code identifies an e-SAJ artifact/upload, never a logical document."""
    code = fields.get("verification_code")
    if not code:
        return None, None
    return _fingerprint({
        "identity_kind": "VERIFICATION_CODE_ARTIFACT",
        "identity_value": code,
        "process_references": fields.get("process_references", []),
    }), "VERIFICATION_CODE"


def _esaj_observations(text: str) -> list[str]:
    """Split explicit e-SAJ attestations preserved inside a BAD whole-page region."""
    starts = list(re.finditer(r"este\s+documento", text, re.IGNORECASE))
    if len(starts) < 2:
        return [text]
    return [text[start.start(): starts[index + 1].start() if index + 1 < len(starts) else len(text)] for index, start in enumerate(starts)]


def _overlaps(first: list[Any], second: list[Any]) -> bool:
    try:
        fx0, fy0, fx1, fy1 = map(float, first)
        sx0, sy0, sx1, sy1 = map(float, second)
    except (TypeError, ValueError):
        return False
    return min(fx1, sx1) > max(fx0, sx0) and min(fy1, sy1) > max(fy0, sy0)


def _same_lateral_strip(first: list[Any], second: list[Any]) -> bool:
    if _overlaps(first, second):
        return True
    try:
        fx0, fy0, fx1, fy1 = map(float, first)
        sx0, sy0, sx1, sy1 = map(float, second)
    except (TypeError, ValueError):
        return False
    vertical_overlap = min(fy1, sy1) > max(fy0, sy0)
    horizontal_gap = max(sx0 - fx1, fx0 - sx1, 0.0)
    return vertical_overlap and horizontal_gap <= 4.0


def _djen_certificate(page: int, regions: list[dict[str, Any]], document_id: str) -> dict[str, Any] | None:
    text = "\n".join(str(region.get("text") or "") for region in regions)
    normalized = _normalized(text)
    if not ("teor da comunicacao" in normalized and "data da publicacao" in normalized and "lei 11.419" in normalized):
        return None
    refs = [_source_map(document_id, page, region) for region in regions if "teor da comunicacao" in _normalized(str(region.get("text") or "")) or "lei 11.419" in _normalized(str(region.get("text") or ""))]
    return {"kind": "DJEN_CERTIFICATE", "source_map": refs}


def extract_lateral_protocols(
    document_id: str,
    page_structures: Iterable[dict[str, Any]],
    *,
    target_process_id: str | None = None,
    recovered_pdfium_page_text: dict[int, str] | None = None,
) -> dict[str, Any]:
    """Extract non-mutating lateral protocol observations and contiguous envelopes."""
    pages: list[dict[str, Any]] = []
    for page_structure in sorted((item for item in page_structures if isinstance(item, dict) and isinstance(item.get("page"), int)), key=lambda item: item["page"]):
        page = page_structure["page"]
        regions = [region for region in page_structure.get("regions", []) if isinstance(region, dict) and isinstance(region.get("region_id"), str)]
        records = []
        for region in (region for region in regions if _is_esaj_lateral(region)):
            original_text = str(region.get("raw_text") or region.get("text") or "")
            text = _recovered_attestation(original_text, (recovered_pdfium_page_text or {}).get(page))
            bbox = list(region.get("bbox") or [])
            if len(bbox) != 4:
                continue
            for observation in _esaj_observations(text):
                fields = _fields(observation)
                index = len(records) + 1
                record = {
                    "lateral_protocol_id": f"p{page}-lp{index:04d}",
                    "kind": "ESAJ_LATERAL",
                    "text": observation,
                    "bbox": bbox,
                    "fields": fields,
                    "source_map": _source_map(document_id, page, region),
                    "relationship": "unresolved",
                }
                record["movement_fingerprint"], record["movement_fingerprint_basis"] = _movement_fingerprint(fields, target_process_id)
                record["artifact_fingerprint"], record["artifact_fingerprint_basis"] = _artifact_fingerprint(fields)
                # Embedded-document consumers use this as an opaque marker key;
                # it is deliberately not a logical-document identity.
                record["fingerprint"] = record["artifact_fingerprint"]
                record["fingerprint_basis"] = record["artifact_fingerprint_basis"]
                records.append(record)

        outer: dict[str, Any] | None = None
        if records:
            candidates = [record for record in records if not target_process_id or target_process_id in record["fields"]["process_references"]]
            outer = max(candidates, key=lambda record: _outer_score(record, target_process_id)) if candidates else None
            if outer:
                target_match = target_process_id in outer["fields"]["process_references"] if target_process_id else None
                outer["relationship"] = "outer_submission" if outer["fields"]["event"] == "PROTOCOLADO" else "outer_release" if outer["fields"]["event"] == "LIBERADO NOS AUTOS" else "unresolved"
                outer["target_process_match"] = target_match
        foreign_records = [record for record in records if record is not outer and record["fields"]["process_references"]]
        for record in records:
            if record is not outer:
                related = [candidate["lateral_protocol_id"] for candidate in foreign_records if candidate is not record and _same_lateral_strip(record["bbox"], candidate["bbox"])]
                if record["fields"]["process_references"] or related:
                    record["relationship"] = "embedded_source"
                    if related:
                        record["embedded_source_lateral_protocol_ids"] = related

        pages.append({
            "page": page,
            "lateral_protocols": records,
            "outer_lateral_protocol_id": outer["lateral_protocol_id"] if outer else None,
            "absence_of_lateral_evidence": not bool(records),
            "djen_certificate": _djen_certificate(page, regions, document_id),
        })

    groups = []
    current: dict[str, Any] | None = None
    previous_page: int | None = None
    for page in pages:
        outer = next((record for record in page["lateral_protocols"] if record["lateral_protocol_id"] == page["outer_lateral_protocol_id"]), None)
        fingerprint = outer.get("movement_fingerprint") if outer else None
        if fingerprint and current and previous_page == page["page"] - 1 and current["fingerprint"] == fingerprint:
            current["pages"].append(page["page"])
            current["source_map"].append(outer["source_map"])
        else:
            if current:
                groups.append(current)
            current = {"group_id": f"lp-group-{page['page']:04d}", "fingerprint": fingerprint, "fingerprint_basis": outer.get("movement_fingerprint_basis") if outer else None, "pages": [page["page"]], "source_map": [outer["source_map"]] if outer else []} if fingerprint else None
        previous_page = page["page"]
    if current:
        groups.append(current)
    result = {
        "lateral_protocol_version": LATERAL_PROTOCOL_VERSION,
        "document_id": document_id,
        "target_process_id": target_process_id,
        "pages": pages,
        "groups": groups,
    }
    markers = []
    marker_by_lateral_id = {}
    for page in pages:
        for record in page["lateral_protocols"]:
            fields = record["fields"]
            identity_kind = "PROTOCOL" if fields.get("protocol_number") else "VERIFICATION_CODE" if fields.get("verification_code") else None
            marker = {
                "marker_id": record["lateral_protocol_id"],
                "provider": "ESAJ",
                "marker_kind": "PROVIDER_DOCUMENT_MARKER",
                "document_id": document_id,
                "provider_identity": {
                    "process_id": target_process_id,
                    "process_references": list(fields["process_references"]),
                    "document_or_movement_or_protocol": {"kind": identity_kind, "value": fields.get("protocol_number") or fields.get("verification_code")},
                },
                "event": fields["event"],
                "event_date": fields["event_date"],
                "event_time": fields["event_time"],
                "event_at": fields["event_at"],
                "occurred_on": fields["occurred_on"],
                "occurred_at": fields["occurred_at"],
                "signatory_literal": fields["signatory_literal"],
                "verification": {"code": fields["verification_code"], "url": fields["verification_url"]},
                "raw_text": record["text"],
                "bbox": list(record["bbox"]),
                "source_map": dict(record["source_map"]),
                "field_source_maps": {
                    key: dict(record["source_map"])
                    for key in ("event", "event_date", "event_time", "event_at", "signatory_literal", "protocol_number", "verification_code")
                    if fields.get(key)
                },
                "provenance_relationship": record["relationship"],
                "target_process_match": record.get("target_process_match"),
                "fingerprint": record.get("fingerprint"),
                "fingerprint_basis": record.get("fingerprint_basis"),
                "movement_fingerprint": record.get("movement_fingerprint"),
                "movement_fingerprint_basis": record.get("movement_fingerprint_basis"),
                "artifact_fingerprint": record.get("artifact_fingerprint"),
                "artifact_fingerprint_basis": record.get("artifact_fingerprint_basis"),
            }
            markers.append(marker)
            marker_by_lateral_id[record["lateral_protocol_id"]] = marker
    provider_groups = []
    for group in groups:
        marker_ids = [
            page["outer_lateral_protocol_id"]
            for page in pages
            if page["page"] in group["pages"] and page["outer_lateral_protocol_id"] in marker_by_lateral_id
        ]
        provider_groups.append({
            "provider_marker_group_id": f"ESAJ:{group['group_id']}",
            "provider": "ESAJ",
            "marker_ids": marker_ids,
            "pages": list(group["pages"]),
            "fingerprint": group["fingerprint"],
            "fingerprint_basis": group["fingerprint_basis"],
            "source_map": list(group["source_map"]),
            "provenance_relationship": "outer_envelope_continuity",
        })
    result["provider_document_markers"] = build_provider_document_marker_projection(
        provider="ESAJ", document_id=document_id, target_process_id=target_process_id,
        markers=markers, groups=provider_groups,
    )
    return result
