"""Factual page signals for documents embedded inside an outer submission."""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable


EMBEDDED_DOCUMENT_SIGNALS_VERSION = "v1"
_CNJ = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")
_FOLIO = re.compile(r"\b(?:fls?\.?|folhas?|p[aá]g(?:ina)?\.?|p\.)\s*(\d+)\b", re.IGNORECASE)


def _header_key(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower().split())


def _source_map(document_id: str, page: int, region: dict[str, Any]) -> dict[str, Any]:
    return {"document_id": document_id, "pdf_page": page, "region_id": region["region_id"], "source_line_ids": list(region.get("source_line_ids", []))}


def extract_embedded_document_signals(
    document_id: str,
    page_structures: Iterable[dict[str, Any]],
    *,
    provider_document_markers: dict[str, Any] | None = None,
    target_process_id: str | None = None,
) -> dict[str, Any]:
    """Keep embedded identities as references; never promote them to parent process."""
    embedded_markers: dict[int, list[dict[str, Any]]] = {}
    if isinstance(provider_document_markers, dict):
        for marker in provider_document_markers.get("markers", []):
            if not isinstance(marker, dict) or marker.get("provenance_relationship") != "embedded_source":
                continue
            source = marker.get("source_map") if isinstance(marker.get("source_map"), dict) else {}
            if isinstance(source.get("pdf_page"), int):
                embedded_markers.setdefault(source["pdf_page"], []).append(marker)

    pages = []
    for page_structure in sorted((item for item in page_structures if isinstance(item, dict) and isinstance(item.get("page"), int)), key=lambda item: item["page"]):
        page = page_structure["page"]
        references: dict[str, list[dict[str, Any]]] = {}
        folios = []
        headers = []
        for region in page_structure.get("regions", []):
            if not isinstance(region, dict) or not isinstance(region.get("region_id"), str):
                continue
            text = str(region.get("raw_text") or region.get("text") or "")
            ref = _source_map(document_id, page, region)
            for process_id in set(_CNJ.findall(text)) | {item.get("process_id") for item in region.get("process_references", []) if isinstance(item, dict) and isinstance(item.get("process_id"), str)}:
                if process_id and process_id != target_process_id:
                    references.setdefault(process_id, []).append(ref)
            if region.get("kind") == "stamp":
                for match in _FOLIO.finditer(text):
                    folios.append({"value": int(match.group(1)), "source_map": ref})
            if region.get("kind") == "header":
                key = _header_key(text)
                if len(key) >= 12:
                    headers.append({"text_key": key, "source_map": ref})
        marker_rows = []
        for marker in embedded_markers.get(page, []):
            identity = marker.get("provider_identity") if isinstance(marker.get("provider_identity"), dict) else {}
            marker_rows.append({
                "marker_id": marker.get("marker_id"),
                "fingerprint": marker.get("fingerprint"),
                "process_references": list(identity.get("process_references", [])),
                "source_map": marker.get("source_map"),
            })
            for process_id in identity.get("process_references", []):
                if isinstance(process_id, str) and process_id != target_process_id:
                    references.setdefault(process_id, []).append(marker.get("source_map"))
        pages.append({
            "page": page,
            "embedded_process_references": [{"process_id": process_id, "source_map": refs} for process_id, refs in sorted(references.items())],
            "internal_folios": sorted(folios, key=lambda item: (item["value"], item["source_map"]["region_id"])),
            "repeated_headers": sorted(headers, key=lambda item: (item["text_key"], item["source_map"]["region_id"])),
            "embedded_markers": marker_rows,
        })
    return {"embedded_document_signals_version": EMBEDDED_DOCUMENT_SIGNALS_VERSION, "document_id": document_id, "target_process_id": target_process_id, "pages": pages}
