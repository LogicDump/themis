"""Factual DJEN/Comunica provider-document markers, independent of e-SAJ."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any, Iterable

from core.documentos.provider_document_marker_v1 import build_provider_document_marker_projection


DJEN_PROVIDER = "DJEN_COMUNICA"
DJEN_PROVIDER_MARKER_VERSION = "v1"
_CNJ = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")
_URL = re.compile(r"https?://comunicaapi\.pje\.jus\.br/api/v1/comunicacao/([A-Za-z0-9]+)/certidao", re.I)
_CODE = re.compile(r"c\w*digo\s+da\s+certid\w*\s*:\s*([A-Za-z0-9]+)", re.I)
_CERTIFICATE = re.compile(r"certid\w*\s+de\s+publica\w*\s+(\d+)", re.I)
_DATE = re.compile(r"disponibilizado\s+em\s*:\s*(\d{2}/\d{2}/\d{4})", re.I)


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower().split())


def _source_map(document_id: str, page: int, region: dict[str, Any]) -> dict[str, Any]:
    return {
        "document_id": document_id,
        "pdf_page": page,
        "region_id": region["region_id"],
        "source_line_ids": list(region.get("source_line_ids", [])),
    }


def _page_signal(document_id: str, page_structure: dict[str, Any]) -> dict[str, Any]:
    page = page_structure["page"]
    regions = [region for region in page_structure.get("regions", []) if isinstance(region, dict) and isinstance(region.get("region_id"), str)]
    text = "\n".join(str(region.get("raw_text") or region.get("text") or "") for region in regions)
    normalized = _normalized(text)
    url_match = _URL.search(text)
    code_match = _CODE.search(normalized)
    certificate_match = _CERTIFICATE.search(normalized)
    date_match = _DATE.search(normalized)
    is_certificate = bool(
        certificate_match
        and "teor da comunica" in normalized
        and "numero do processo" in normalized
    )
    source_maps = [_source_map(document_id, page, region) for region in regions if str(region.get("raw_text") or region.get("text") or "").strip()]
    return {
        "page": page,
        "raw_text": text,
        "is_certificate": is_certificate,
        "certificate_number": certificate_match.group(1) if certificate_match else None,
        "certificate_code": (url_match.group(1) if url_match else None) or (code_match.group(1) if code_match else None),
        "comunica_url": url_match.group(0) if url_match else None,
        "publication_date": date_match.group(1) if date_match else None,
        "process_references": sorted(set(_CNJ.findall(text))),
        "source_maps": source_maps,
    }


def _fingerprint(code: str) -> str:
    payload = json.dumps({"provider": DJEN_PROVIDER, "certificate_code": code}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def extract_djen_provider_document_markers(
    document_id: str,
    page_structures: Iterable[dict[str, Any]],
    *,
    target_process_id: str | None = None,
) -> dict[str, Any]:
    """Project only positively identified DJEN certificates and their QR/URL continuation."""
    signals = [_page_signal(document_id, item) for item in sorted(
        (item for item in page_structures if isinstance(item, dict) and isinstance(item.get("page"), int)),
        key=lambda item: item["page"],
    )]
    markers: list[dict[str, Any]] = []
    groups: list[dict[str, Any]] = []
    consumed: set[int] = set()
    for index, signal in enumerate(signals):
        if not signal["is_certificate"] or signal["page"] in consumed:
            continue
        members = [signal]
        code = signal["certificate_code"]
        url = signal["comunica_url"]
        # A code-only immediate next page is factual continuation of this
        # certificate; absence alone is never treated as continuation.
        if not code and index + 1 < len(signals):
            next_signal = signals[index + 1]
            if next_signal["page"] == signal["page"] + 1 and not next_signal["is_certificate"] and next_signal["certificate_code"]:
                members.append(next_signal)
                consumed.add(next_signal["page"])
                code, url = next_signal["certificate_code"], next_signal["comunica_url"]
        if not code:
            continue
        fingerprint = _fingerprint(code)
        marker_ids = []
        group_source_map = []
        for member in members:
            source_maps = list(member["source_maps"])
            source = source_maps[0] if source_maps else {"document_id": document_id, "pdf_page": member["page"], "region_id": None, "source_line_ids": []}
            marker_id = f"djen-p{member['page']:04d}-{code}"
            marker_ids.append(marker_id)
            group_source_map.extend(source_maps or [source])
            markers.append({
                "marker_id": marker_id,
                "provider": DJEN_PROVIDER,
                "marker_kind": "PROVIDER_DOCUMENT_MARKER",
                "document_id": document_id,
                "provider_identity": {
                    "process_id": target_process_id,
                    "process_references": list(signal["process_references"]),
                    "document_or_movement_or_protocol": {"kind": "DJEN_CERTIFICATE_CODE", "value": code},
                },
                "certificate_number": signal["certificate_number"],
                "publication_date": signal["publication_date"],
                "comunica_url": url,
                "raw_text": member["raw_text"],
                "source_map": source,
                "source_maps": source_maps,
                "provenance_relationship": "provider_document",
                "artifact_fingerprint": fingerprint,
                "artifact_fingerprint_basis": "DJEN_CERTIFICATE_CODE",
                "fingerprint": fingerprint,
                "fingerprint_basis": "DJEN_CERTIFICATE_CODE",
            })
        groups.append({
            "provider_marker_group_id": f"{DJEN_PROVIDER}:certificate:{code}",
            "provider": DJEN_PROVIDER,
            "marker_ids": marker_ids,
            "pages": [member["page"] for member in members],
            "fingerprint": None,
            "fingerprint_basis": None,
            "source_map": group_source_map,
            "provenance_relationship": "provider_document_continuity",
        })
    result = build_provider_document_marker_projection(
        provider=DJEN_PROVIDER,
        document_id=document_id,
        target_process_id=target_process_id,
        markers=markers,
        groups=groups,
    )
    result["djen_provider_marker_version"] = DJEN_PROVIDER_MARKER_VERSION
    return result
