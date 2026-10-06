"""Actor & Role Resolver V1.

The LLM only resolves literal mentions to known participant IDs (or leaves them
open). Actor kind, process role, sufficiency and unresolved diagnostics are
derived deterministically by Themis.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from core.legal_skills.source_contract_v1 import (
    SOURCE_REF_SCHEMA,
    normalize_text,
    validate_source_input,
    validate_source_refs,
)

SCHEMA_VERSION = "actor-role-resolver-v1"
RESOLUTION_STATUSES = ("RESOLVED", "AMBIGUOUS", "UNRESOLVED")

ACTOR_ROLE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "actors": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "mention": {"type": "string", "minLength": 1},
                    "participant_id": {"type": ["string", "null"]},
                    "resolution_status": {
                        "type": "string",
                        "enum": list(RESOLUTION_STATUSES),
                    },
                    "source_refs": {
                        "type": "array",
                        "minItems": 1,
                        "items": SOURCE_REF_SCHEMA,
                    },
                },
                "required": [
                    "mention",
                    "participant_id",
                    "resolution_status",
                    "source_refs",
                ],
            },
        },
    },
    "required": ["actors"],
}

_COURT_RE = re.compile(
    r"\b(ju[ií]zo|juiz|ju[ií]za|magistrad[oa]|relator(?:a)?|desembargador(?:a)?)\b",
    re.IGNORECASE,
)


def build_actor_role_instructions() -> str:
    return (
        "Você é o Actor & Role Resolver do Themis. Extraia SOMENTE atores efetivamente mencionados no texto. "
        "mention deve copiar literalmente a expressão usada no texto, nunca substituir pela identidade canônica da lista. "
        "Quando a menção corresponder inequivocamente a um participante estruturado, use participant_id e RESOLVED. "
        "Quando for ator explícito não cadastrado (inclusive juízo/magistrado), use participant_id=null e RESOLVED. "
        "Referências relacionais ou pronominais como 'parte contrária', 'parte adversa', 'seu patrono', 'ele/ela' "
        "não autorizam escolher participante por plausibilidade: use participant_id=null e AMBIGUOUS ou UNRESOLVED. "
        "Não emita participantes que não aparecem no texto. Toda menção exige source_refs com quote literal conferível. "
        "Responda somente no schema."
    )


def build_actor_role_input(source_document: dict[str, Any], process_frame: dict[str, Any]) -> dict[str, Any]:
    source = validate_source_input({
        "process_id": source_document.get("process_id"),
        "movement_id": source_document.get("movement_id"),
        "pages": source_document.get("pages"),
        "title": source_document.get("title"),
        "actor": source_document.get("actor"),
        "occurred_at": source_document.get("occurred_at"),
        "movement_type": source_document.get("movement_type"),
    })
    if str(process_frame.get("process_id") or "") != source["process_id"]:
        raise ValueError("process_frame divergente do source_document")

    participants = process_frame.get("participants") or []
    if not isinstance(participants, list):
        raise ValueError("process_frame.participants deve ser lista")
    compact_participants: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in participants:
        if not isinstance(item, dict):
            raise ValueError("participant inválido")
        participant_id = str(item.get("participant_id") or "").strip()
        display_name = str(item.get("display_name") or "").strip()
        base_role = str(item.get("base_role") or "").strip().upper()
        if not participant_id or participant_id in seen or not display_name or not base_role:
            raise ValueError("participant incompleto/duplicado")
        seen.add(participant_id)
        compact_participants.append({
            "participant_id": participant_id,
            "display_name": display_name,
            "base_role": base_role,
        })

    representations = process_frame.get("representations") or []
    if not isinstance(representations, list):
        raise ValueError("process_frame.representations deve ser lista")
    compact_representations: list[dict[str, Any]] = []
    for item in representations:
        if not isinstance(item, dict):
            raise ValueError("representation inválida")
        representative_id = str(item.get("representative_participant_id") or "").strip()
        represented_id = str(item.get("represented_participant_id") or "").strip()
        if not representative_id or not represented_id:
            raise ValueError("representation sem participantes")
        if representative_id not in seen or represented_id not in seen:
            raise ValueError("representation referencia participante inexistente")
        compact_representations.append({
            "representative_participant_id": representative_id,
            "represented_participant_id": represented_id,
            "representation_kind": item.get("representation_kind"),
        })

    return {**source, "participants": compact_participants, "representations": compact_representations}


def _derived_actor_id(source: dict[str, Any], mention: str, participant_id: str | None, actor_kind: str) -> str:
    if participant_id:
        return participant_id
    if actor_kind == "COURT":
        return "COURT"
    raw = "\0".join((source["movement_id"], normalize_text(mention), actor_kind))
    return "actor_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def validate_actor_role(value: Any, skill_input: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Actor Role output não é JSON válido") from exc
    if not isinstance(value, dict) or set(value) != {"actors"} or not isinstance(value["actors"], list):
        raise ValueError("Actor Role output deve conter somente actors[]")

    source = validate_source_input(skill_input)
    source_text = "\n".join(page["content"] for page in source["pages"])
    participants = {str(item["participant_id"]): item for item in skill_input.get("participants") or []}
    actors: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None]] = set()
    unresolved_points: list[dict[str, Any]] = []
    has_ambiguous = False
    has_unresolved = False

    for item in value["actors"]:
        required = {"mention", "participant_id", "resolution_status", "source_refs"}
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError("actor divergente do schema")
        mention = str(item["mention"] or "").strip()
        participant_id = item["participant_id"]
        status = str(item["resolution_status"] or "").upper()
        if not mention or normalize_text(mention) not in normalize_text(source_text):
            raise ValueError("mention deve existir literalmente no source")
        if status not in RESOLUTION_STATUSES:
            raise ValueError("resolution_status inválido")

        refs = validate_source_refs(item["source_refs"], source, field_name="actor.source_refs")
        if status == "RESOLVED":
            if participant_id is not None:
                participant_id = str(participant_id).strip()
                participant = participants.get(participant_id)
                if not participant:
                    raise ValueError("participant_id inexistente")
                actor_kind = "PROCESS_PARTICIPANT"
                process_role = str(participant["base_role"]).upper()
            else:
                actor_kind = "COURT" if _COURT_RE.search(mention) else "OTHER"
                process_role = "COURT" if actor_kind == "COURT" else "OTHER"
        else:
            if participant_id is not None:
                raise ValueError("ator aberto não pode fixar participant_id")
            actor_kind = "UNRESOLVED"
            process_role = "UNRESOLVED"
            if status == "AMBIGUOUS":
                has_ambiguous = True
                code = "ACTOR_REFERENCE_AMBIGUOUS"
                reason = "A menção admite mais de uma resolução com o contexto fornecido."
            else:
                has_unresolved = True
                code = "ACTOR_REFERENCE_UNRESOLVED"
                reason = "Falta contexto para resolver a identidade mencionada."
            unresolved_points.append({"code": code, "reason": reason, "source_refs": refs})

        key = (normalize_text(mention), participant_id)
        if key in seen:
            raise ValueError("actor duplicado")
        seen.add(key)
        actors.append({
            "actor_id": _derived_actor_id(source, mention, participant_id, actor_kind),
            "mention": mention,
            "actor_kind": actor_kind,
            "participant_id": participant_id,
            "process_role": process_role,
            "resolution_status": status,
            "source_refs": refs,
        })

    sufficiency = "AMBIGUOUS" if has_ambiguous else ("INSUFFICIENT" if has_unresolved else "SUFFICIENT")
    return {
        "schema_version": SCHEMA_VERSION,
        "context_sufficiency": sufficiency,
        "actors": actors,
        "unresolved_points": unresolved_points,
    }


def score_actor_role(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    expected_items = list(expected.get("actors") or [])
    actual_items = list(actual.get("actors") or [])

    def mentions_overlap(a: str, b: str) -> bool:
        a_n, b_n = normalize_text(a), normalize_text(b)
        return bool(a_n and b_n and (a_n in b_n or b_n in a_n))

    def matches(exp: dict[str, Any], act: dict[str, Any]) -> bool:
        exp_status = str(exp.get("resolution_status") or "")
        act_status = str(act.get("resolution_status") or "")
        if exp_status != act_status:
            return False
        exp_pid = exp.get("participant_id")
        if exp_pid is not None:
            return exp_pid == act.get("participant_id")
        if act.get("participant_id") is not None:
            return False
        if exp_status == "RESOLVED":
            expected_kind = exp.get("external_kind")
            if expected_kind:
                return str(actual.get("actor_kind") or "") == str(expected_kind)
        return mentions_overlap(str(exp.get("mention") or ""), str(act.get("mention") or ""))

    unmatched = set(range(len(actual_items)))
    matched = 0
    for exp in expected_items:
        hit = next((i for i in unmatched if matches(exp, actual_items[i])), None)
        if hit is not None:
            matched += 1
            unmatched.remove(hit)

    precision = 1.0 if not actual_items else matched / len(actual_items)
    recall = 1.0 if not expected_items else matched / len(expected_items)

    dangerous = False
    for exp in expected_items:
        if exp.get("resolution_status") == "RESOLVED":
            continue
        for act in actual_items:
            if act.get("resolution_status") != "RESOLVED":
                continue
            if mentions_overlap(str(exp.get("mention") or ""), str(act.get("mention") or "")):
                dangerous = True
                break
        if dangerous:
            break

    return {
        "actor_precision": precision,
        "actor_recall": recall,
        "sufficiency_match": expected.get("context_sufficiency") == actual.get("context_sufficiency"),
        "dangerous_false_resolution": dangerous,
    }
