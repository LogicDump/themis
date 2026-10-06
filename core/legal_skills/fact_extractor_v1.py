"""Fact Extractor V1.

Extracts source-grounded factual propositions without upgrading allegations into
proof. Evidence assessment is deliberately left to the downstream Evidence Mapper.
"""
from __future__ import annotations

import json
from typing import Any

from core.legal_skills.source_contract_v1 import (
    SOURCE_REF_SCHEMA,
    UNRESOLVED_POINT_SCHEMA,
    validate_source_input,
    validate_source_refs,
    validate_sufficiency,
    validate_unresolved_points,
)

SCHEMA_VERSION = "fact-extractor-v1"
EPISTEMIC_STATUSES = (
    "ALLEGED",
    "ADMITTED",
    "JUDICIAL_FINDING",
    "DOCUMENTED_EVENT",
)

FACT_EXTRACTOR_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "context_sufficiency": {
            "type": "string",
            "enum": ["SUFFICIENT", "INSUFFICIENT", "AMBIGUOUS"],
        },
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "fact_id": {"type": "string", "minLength": 1},
                    "statement": {"type": "string", "minLength": 1},
                    "epistemic_status": {
                        "type": "string",
                        "enum": list(EPISTEMIC_STATUSES),
                    },
                    "actor_id": {"type": ["string", "null"]},
                    "temporal_text": {"type": ["string", "null"]},
                    "source_refs": {
                        "type": "array",
                        "minItems": 1,
                        "items": SOURCE_REF_SCHEMA,
                    },
                },
                "required": [
                    "fact_id",
                    "statement",
                    "epistemic_status",
                    "actor_id",
                    "temporal_text",
                    "source_refs",
                ],
            },
        },
        "unresolved_points": {
            "type": "array",
            "items": UNRESOLVED_POINT_SCHEMA,
        },
    },
    "required": ["context_sufficiency", "facts", "unresolved_points"],
}


def build_fact_extractor_instructions() -> str:
    return (
        "Você é o Fact Extractor do Themis. Extraia somente proposições factuais sustentadas pelo texto fornecido. "
        "Não extraia posição jurídica, pedido, argumento, conclusão doutrinária ou obrigação como se fossem fatos. "
        "Preserve o estatuto epistêmico da fonte: ALLEGED quando uma parte apenas afirma algo; ADMITTED somente quando "
        "houver admissão/confissão expressa; JUDICIAL_FINDING somente quando o juízo expressamente estabelece um fato; "
        "DOCUMENTED_EVENT somente para ocorrência diretamente registrada pelo próprio documento, sem inferência adicional. "
        "Nunca use 'PROVEN', 'TRUE' ou equivalente: prova e força probatória pertencem ao Evidence Mapper posterior. "
        "actor_id só pode referenciar actor RESOLVED recebido no input. Se o ator necessário estiver ambíguo ou não resolvido, "
        "preserve a lacuna em unresolved_points; não escolha por plausibilidade. temporal_text deve copiar apenas expressão temporal "
        "explícita relevante, ou null. Toda proposição exige source_refs com quote literal conferível na página indicada. "
        "Se o texto não contiver proposição factual material, facts=[] pode ser SUFFICIENT. "
        "Responda somente no schema."
    )


def build_fact_extractor_input(
    actor_skill_input: dict[str, Any],
    actor_output: dict[str, Any],
) -> dict[str, Any]:
    source = validate_source_input(actor_skill_input)
    if not isinstance(actor_output, dict):
        raise ValueError("actor_output deve ser objeto")
    actors = actor_output.get("actors")
    if not isinstance(actors, list):
        raise ValueError("actor_output sem actors")
    compact_actors: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in actors:
        if not isinstance(item, dict):
            raise ValueError("actor inválido")
        actor_id = str(item.get("actor_id") or "").strip()
        status = str(item.get("resolution_status") or "").upper()
        if not actor_id or actor_id in seen or status not in {"RESOLVED", "AMBIGUOUS", "UNRESOLVED"}:
            raise ValueError("actor_id/status inválido")
        seen.add(actor_id)
        compact_actors.append({
            "actor_id": actor_id,
            "mention": item.get("mention"),
            "actor_kind": item.get("actor_kind"),
            "participant_id": item.get("participant_id"),
            "process_role": item.get("process_role"),
            "resolution_status": status,
        })
    return {
        **source,
        "actors": compact_actors,
    }


def validate_fact_extraction(value: Any, skill_input: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Fact Extractor output não é JSON válido") from exc
    if not isinstance(value, dict) or set(value) != {
        "context_sufficiency", "facts", "unresolved_points"
    }:
        raise ValueError("Fact Extractor output divergente do schema")
    if not isinstance(value["facts"], list):
        raise ValueError("facts deve ser lista")

    source = validate_source_input(skill_input)
    actors = {
        str(item.get("actor_id") or ""): item
        for item in skill_input.get("actors") or []
        if str(item.get("actor_id") or "").strip()
    }
    unresolved_points = validate_unresolved_points(value["unresolved_points"], source)
    facts: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in value["facts"]:
        required = {
            "fact_id", "statement", "epistemic_status",
            "actor_id", "temporal_text", "source_refs",
        }
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError("fact divergente do schema")
        fact_id = str(item["fact_id"] or "").strip()
        statement = str(item["statement"] or "").strip()
        status = str(item["epistemic_status"] or "").upper()
        actor_id = item["actor_id"]
        temporal_text = item["temporal_text"]
        if not fact_id or fact_id in seen or not statement:
            raise ValueError("fact_id/statement ausente ou duplicado")
        if status not in EPISTEMIC_STATUSES:
            raise ValueError(f"epistemic_status inválido em {fact_id}")
        if temporal_text is not None and not str(temporal_text).strip():
            raise ValueError(f"temporal_text vazio em {fact_id}")

        if actor_id is not None:
            actor_id = str(actor_id).strip()
            actor = actors.get(actor_id)
            if not actor:
                raise ValueError(f"actor_id inexistente em {fact_id}")
            if str(actor.get("resolution_status") or "").upper() != "RESOLVED":
                raise ValueError(f"fact não pode usar actor não resolvido em {fact_id}")
        if status in {"ALLEGED", "ADMITTED"} and actor_id is None:
            raise ValueError(f"{status} exige actor_id resolvido em {fact_id}")
        if status == "JUDICIAL_FINDING" and actor_id is not None:
            actor = actors[actor_id]
            if str(actor.get("actor_kind") or "").upper() != "COURT":
                raise ValueError(f"JUDICIAL_FINDING só pode ser atribuído ao COURT em {fact_id}")

        facts.append({
            "fact_id": fact_id,
            "statement": statement,
            "epistemic_status": status,
            "actor_id": actor_id,
            "temporal_text": None if temporal_text is None else str(temporal_text),
            "source_refs": validate_source_refs(item["source_refs"], source, field_name=f"{fact_id}.source_refs"),
        })
        seen.add(fact_id)

    sufficiency = validate_sufficiency(value["context_sufficiency"], unresolved_points)
    return {
        "schema_version": SCHEMA_VERSION,
        "context_sufficiency": sufficiency,
        "facts": facts,
        "unresolved_points": unresolved_points,
    }


def score_fact_extraction(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    def key(item: dict[str, Any]) -> tuple[str, str, Any]:
        return (
            " ".join(str(item.get("statement") or "").casefold().split()),
            str(item.get("epistemic_status") or ""),
            item.get("actor_id"),
        )
    expected_set = {key(item) for item in expected.get("facts") or []}
    actual_set = {key(item) for item in actual.get("facts") or []}
    matched = len(expected_set & actual_set)
    precision = 1.0 if not actual_set else matched / len(actual_set)
    recall = 1.0 if not expected_set else matched / len(expected_set)

    expected_alleged = {
        " ".join(str(item.get("statement") or "").casefold().split())
        for item in expected.get("facts") or []
        if item.get("epistemic_status") == "ALLEGED"
    }
    dangerous_status_upgrade = any(
        " ".join(str(item.get("statement") or "").casefold().split()) in expected_alleged
        and item.get("epistemic_status") in {"JUDICIAL_FINDING", "DOCUMENTED_EVENT"}
        for item in actual.get("facts") or []
    )
    return {
        "fact_precision": precision,
        "fact_recall": recall,
        "sufficiency_match": expected.get("context_sufficiency") == actual.get("context_sufficiency"),
        "dangerous_status_upgrade": dangerous_status_upgrade,
    }
