"""Strict Issue Map V1 for drafting-context retrieval.

The mapper reads the target act in full and emits only source-grounded issues used
as retrieval queries against the rest of the process.
"""
from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

SCHEMA_VERSION = "drafting-issue-map-v1"
ISSUE_KINDS = (
    "FACTUAL_ASSERTION",
    "LEGAL_POSITION",
    "REQUEST",
    "JUDICIAL_DECISION",
    "EVIDENCE_REFERENCE",
    "OTHER_MATERIAL_POINT",
)

SOURCE_REF_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "document_id": {"type": "string", "minLength": 1},
        "pdf_page": {"type": "integer", "minimum": 1},
        "quote": {"type": "string", "minLength": 1},
    },
    "required": ["document_id", "pdf_page", "quote"],
}

ISSUE_MAP_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "issue_id": {"type": "string", "minLength": 1},
                    "kind": {"type": "string", "enum": list(ISSUE_KINDS)},
                    "text": {"type": "string", "minLength": 1},
                    "retrieval_query": {"type": "string", "minLength": 1},
                    "target_source_refs": {
                        "type": "array",
                        "minItems": 1,
                        "items": SOURCE_REF_SCHEMA,
                    },
                },
                "required": [
                    "issue_id",
                    "kind",
                    "text",
                    "retrieval_query",
                    "target_source_refs",
                ],
            },
        },
    },
    "required": ["issues"],
}


def build_issue_mapper_instructions(task_kind: str, goal: str) -> str:
    return (
        "Leia integralmente o ato-alvo fornecido. Não o resuma e não tente responder à peça. "
        "Sua única função é construir um mapa de questões materiais para buscar contexto no restante dos autos. "
        "Crie uma issue apenas quando o próprio ato-alvo sustentar sua existência. Preserve a natureza jurídica: "
        "alegação factual não é fato provado; posição jurídica não é fato; pedido não é decisão. "
        "Cada issue deve conter target_source_refs com quote copiado literalmente do content da MESMA página indicada. "
        "retrieval_query deve ser uma consulta curta e discriminativa para localizar no restante do processo fatos, "
        "decisões, documentos, alegações ou antecedentes relacionados àquela issue; não inclua conclusão jurídica nova. "
        f"task_kind={task_kind}; objetivo={goal}. Responda somente no schema."
    )


def build_issue_mapper_input(target_document: dict[str, Any]) -> dict[str, Any]:
    if target_document.get("source_mode") != "FULL_CANONICAL":
        raise ValueError("Issue Mapper exige ato-alvo integral canônico")
    pages = target_document.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("ato-alvo sem páginas canônicas")
    return {
        "movement_id": target_document.get("movement_id"),
        "title": target_document.get("title"),
        "actor": target_document.get("actor"),
        "occurred_at": target_document.get("occurred_at"),
        "movement_type": target_document.get("movement_type"),
        "pages": pages,
    }


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip().casefold()


def validate_issue_map(value: Any, target_document: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Issue Map não é JSON válido") from exc
    if not isinstance(value, dict) or set(value) != {"issues"} or not isinstance(value["issues"], list):
        raise ValueError("Issue Map deve conter somente issues[]")

    pages = {
        (str(page.get("document_id") or ""), int(page.get("pdf_page") or 0)): str(page.get("content") or "")
        for page in target_document.get("pages") or []
    }
    seen: set[str] = set()
    validated: list[dict[str, Any]] = []
    for issue in value["issues"]:
        required = {"issue_id", "kind", "text", "retrieval_query", "target_source_refs"}
        if not isinstance(issue, dict) or set(issue) != required:
            raise ValueError("issue divergente do schema")
        issue_id = str(issue["issue_id"]).strip()
        if not issue_id or issue_id in seen:
            raise ValueError("issue_id ausente/duplicado")
        if issue["kind"] not in ISSUE_KINDS:
            raise ValueError(f"kind inválido em {issue_id}")
        if not str(issue["text"]).strip() or not str(issue["retrieval_query"]).strip():
            raise ValueError(f"issue sem texto/query em {issue_id}")
        refs = issue["target_source_refs"]
        if not isinstance(refs, list) or not refs:
            raise ValueError(f"issue sem target_source_refs em {issue_id}")
        for ref in refs:
            if not isinstance(ref, dict) or set(ref) != {"document_id", "pdf_page", "quote"}:
                raise ValueError(f"target_source_ref inválida em {issue_id}")
            key = (str(ref["document_id"]), int(ref["pdf_page"]))
            source = pages.get(key)
            quote = str(ref["quote"])
            if source is None or not quote.strip() or _norm(quote) not in _norm(source):
                raise ValueError(f"target_source_ref não conferível em {issue_id}")
        seen.add(issue_id)
        validated.append(issue)
    return validated
