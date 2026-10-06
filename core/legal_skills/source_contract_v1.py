"""Shared strict source/provenance contract for Themis legal skills."""
from __future__ import annotations

import re
import unicodedata
from typing import Any

SUFFICIENCY_STATES = ("SUFFICIENT", "INSUFFICIENT", "AMBIGUOUS")

SOURCE_REF_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "document_id": {"type": "string", "minLength": 1},
        "pdf_page": {"type": "integer", "minimum": 1},
        "quote": {"type": "string", "minLength": 1},
    },
    "required": ["document_id", "pdf_page", "quote"],
}

UNRESOLVED_POINT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "code": {"type": "string", "minLength": 1},
        "reason": {"type": "string", "minLength": 1},
        "source_refs": {
            "type": "array",
            "minItems": 1,
            "items": SOURCE_REF_SCHEMA,
        },
    },
    "required": ["code", "reason", "source_refs"],
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or ""))).strip().casefold()


def validate_source_input(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("source input deve ser objeto")
    required = {"process_id", "movement_id", "pages"}
    if not required.issubset(value):
        raise ValueError("source input exige process_id, movement_id e pages")
    if not str(value.get("process_id") or "").strip():
        raise ValueError("process_id obrigatório")
    if not str(value.get("movement_id") or "").strip():
        raise ValueError("movement_id obrigatório")
    pages = value.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("source input exige pages não vazio")
    seen: set[tuple[str, int]] = set()
    normalized_pages: list[dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, dict):
            raise ValueError("page inválida")
        document_id = str(page.get("document_id") or "").strip()
        pdf_page = page.get("pdf_page")
        content = page.get("content")
        if (
            not document_id
            or isinstance(pdf_page, bool)
            or not isinstance(pdf_page, int)
            or pdf_page < 1
            or not isinstance(content, str)
        ):
            raise ValueError("page exige document_id, pdf_page positivo e content textual")
        key = (document_id, pdf_page)
        if key in seen:
            raise ValueError("page duplicada no source input")
        seen.add(key)
        normalized_pages.append({
            "document_id": document_id,
            "pdf_page": pdf_page,
            "content": content,
        })
    return {
        **value,
        "process_id": str(value["process_id"]).strip(),
        "movement_id": str(value["movement_id"]).strip(),
        "pages": normalized_pages,
    }


def source_page_index(source: dict[str, Any]) -> dict[tuple[str, int], str]:
    source = validate_source_input(source)
    return {
        (page["document_id"], page["pdf_page"]): page["content"]
        for page in source["pages"]
    }


def validate_source_refs(refs: Any, source: dict[str, Any], *, field_name: str = "source_refs") -> list[dict[str, Any]]:
    if not isinstance(refs, list) or not refs:
        raise ValueError(f"{field_name} deve ser lista não vazia")
    pages = source_page_index(source)
    validated: list[dict[str, Any]] = []
    for ref in refs:
        if not isinstance(ref, dict) or set(ref) != {"document_id", "pdf_page", "quote"}:
            raise ValueError(f"{field_name} contém referência divergente do schema")
        document_id = str(ref["document_id"] or "").strip()
        pdf_page = ref["pdf_page"]
        quote = str(ref["quote"] or "")
        if isinstance(pdf_page, bool) or not isinstance(pdf_page, int) or pdf_page < 1:
            raise ValueError(f"{field_name} contém pdf_page inválido")
        content = pages.get((document_id, pdf_page))
        if content is None or not quote.strip() or normalize_text(quote) not in normalize_text(content):
            raise ValueError(f"{field_name} contém provenance não conferível")
        validated.append({
            "document_id": document_id,
            "pdf_page": pdf_page,
            "quote": quote,
        })
    return validated


def validate_unresolved_points(value: Any, source: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError("unresolved_points deve ser lista")
    validated: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"code", "reason", "source_refs"}:
            raise ValueError("unresolved_point divergente do schema")
        code = str(item["code"] or "").strip()
        reason = str(item["reason"] or "").strip()
        if not code or not reason:
            raise ValueError("unresolved_point exige code e reason")
        validated.append({
            "code": code,
            "reason": reason,
            "source_refs": validate_source_refs(item["source_refs"], source, field_name="unresolved_point.source_refs"),
        })
    return validated


def validate_sufficiency(status: Any, unresolved_points: list[dict[str, Any]]) -> str:
    status = str(status or "").strip().upper()
    if status not in SUFFICIENCY_STATES:
        raise ValueError("context_sufficiency inválido")
    if status == "SUFFICIENT" and unresolved_points:
        raise ValueError("SUFFICIENT não pode conter unresolved_points")
    if status != "SUFFICIENT" and not unresolved_points:
        raise ValueError(f"{status} exige unresolved_points")
    return status
