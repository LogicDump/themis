"""Claim / Request Mapper V1."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any

from core.legal_skills.source_contract_v1 import (
    SOURCE_REF_SCHEMA,
    normalize_text,
    validate_source_input,
    validate_source_refs,
)

SCHEMA_VERSION = "claim-request-mapper-v1"

CLAIM_REQUEST_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "legal_positions": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "text": {"type": "string", "minLength": 1},
                "actor_id": {"type": ["string", "null"]},
                "source_refs": {"type": "array", "minItems": 1, "items": SOURCE_REF_SCHEMA},
            },
            "required": ["text", "actor_id", "source_refs"],
        }},
        "requests": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "text": {"type": "string", "minLength": 1},
                "actor_id": {"type": ["string", "null"]},
                "source_refs": {"type": "array", "minItems": 1, "items": SOURCE_REF_SCHEMA},
            },
            "required": ["text", "actor_id", "source_refs"],
        }},
    },
    "required": ["legal_positions", "requests"],
}

_ROLE_ALIASES = {
    "CLAIMANT": ("AUTOR", "AUTORA", "REQUERENTE", "REQTE", "EXEQUENTE", "EXEQTE"),
    "RESPONDENT": (
        "REU", "RÉU", "RE", "RÉ", "REQUERIDO", "REQUERIDA", "REQDO", "REQDA",
        "EXECUTADO", "EXECUTADA", "EXECTDO",
    ),
    "THIRD_PARTY": ("TERCEIRO INTERESSADO", "TERCEIRA INTERESSADA"),
    "EXPERT": ("PERITO", "PERITA"),
    "PUBLIC_PROSECUTOR": ("MINISTERIO PUBLICO", "MINISTÉRIO PÚBLICO", "PROMOTOR", "PROMOTORA"),
}


def _norm_ascii(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = value.encode("ascii", "ignore").decode("ascii").upper()
    return " ".join(re.sub(r"[^A-Z0-9\s]", " ", value).split())


def derive_source_actor(source_document: dict[str, Any], participants: list[dict[str, Any]]) -> dict[str, Any]:
    raw = str(source_document.get("actor") or "").strip()
    if not raw:
        return {"status": "UNRESOLVED", "actor_id": None, "candidate_actor_ids": [], "basis": "MOVEMENT_ACTOR_MISSING", "raw": None}

    raw_norm = _norm_ascii(raw)
    direct = [p for p in participants if _norm_ascii(p.get("display_name") or "") == raw_norm]
    if len(direct) == 1:
        pid = str(direct[0]["participant_id"])
        return {"status": "RESOLVED", "actor_id": pid, "candidate_actor_ids": [pid], "basis": "MOVEMENT_ACTOR_NAME", "raw": raw}
    if len(direct) > 1:
        ids = sorted(str(p["participant_id"]) for p in direct)
        return {"status": "AMBIGUOUS", "actor_id": None, "candidate_actor_ids": ids, "basis": "MOVEMENT_ACTOR_NAME", "raw": raw}

    role = None
    for base_role, aliases in _ROLE_ALIASES.items():
        if raw_norm in {_norm_ascii(alias) for alias in aliases}:
            role = base_role
            break
    if role is None:
        return {"status": "UNRESOLVED", "actor_id": None, "candidate_actor_ids": [], "basis": "MOVEMENT_ACTOR_UNMAPPED", "raw": raw}

    matches = [p for p in participants if str(p.get("base_role") or "").upper() == role]
    ids = sorted(str(p["participant_id"]) for p in matches)
    if len(ids) == 1:
        return {"status": "RESOLVED", "actor_id": ids[0], "candidate_actor_ids": ids, "basis": "MOVEMENT_ACTOR_ROLE", "raw": raw}
    return {
        "status": "AMBIGUOUS" if ids else "UNRESOLVED",
        "actor_id": None,
        "candidate_actor_ids": ids,
        "basis": "MOVEMENT_ACTOR_ROLE",
        "raw": raw,
    }


def build_claim_request_instructions() -> str:
    return (
        "Você é o Claim / Request Mapper do Themis. Extraia somente: "
        "(1) legal_positions: teses, fundamentos, objeções ou consequências JURÍDICAS defendidas pela parte; "
        "(2) requests: providências, tutela, condenação, reconhecimento, rejeição, acolhimento ou outro resultado pedido. "
        "Não extraia alegações puramente factuais, eventos, decisões do juízo, obrigações impostas, referências a prova ou mera narrativa. "
        "'A autora afirma que pagou' é fato, não legal_position. "
        "'Sustenta a incidência do art. 300 do CPC' é legal_position. "
        "'Requer a condenação ao pagamento' é request. "
        "Se uma tese aparecer apenas como objeto de um pedido, registre o request e não duplique posição idêntica sem argumento independente. "
        "actor_id só pode ser um actor RESOLVED recebido ou source_actor.actor_id quando source_actor.status=RESOLVED. "
        "Para sujeito implícito como 'Requer' ou 'Sustenta', use source_actor apenas se resolvido; caso contrário use null. "
        "Toda saída exige source_refs com quote literal conferível. Responda somente no schema."
    )


def build_claim_request_input(actor_skill_input: dict[str, Any], actor_output: dict[str, Any]) -> dict[str, Any]:
    source = validate_source_input(actor_skill_input)
    actors = actor_output.get("actors") if isinstance(actor_output, dict) else None
    if not isinstance(actors, list):
        raise ValueError("actor_output sem actors")
    compact_actors = []
    for item in actors:
        if not isinstance(item, dict):
            raise ValueError("actor inválido")
        actor_id = str(item.get("actor_id") or "").strip()
        status = str(item.get("resolution_status") or "").upper()
        if not actor_id or status not in {"RESOLVED", "AMBIGUOUS", "UNRESOLVED"}:
            raise ValueError("actor_id/status inválido")
        compact_actors.append({
            "actor_id": actor_id,
            "mention": item.get("mention"),
            "participant_id": item.get("participant_id"),
            "process_role": item.get("process_role"),
            "resolution_status": status,
        })

    participants = actor_skill_input.get("participants") or []
    if not isinstance(participants, list):
        raise ValueError("participants deve ser lista")
    return {
        **source,
        "actors": compact_actors,
        "source_actor": derive_source_actor(actor_skill_input, participants),
    }


def _stable_id(collection: str, source: dict[str, Any], text: str, actor_id: str | None) -> str:
    raw = "\0".join((source["process_id"], source["movement_id"], collection, normalize_text(text), str(actor_id or "")))
    return "cr_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def validate_claim_request(value: Any, skill_input: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Claim / Request output não é JSON válido") from exc
    if not isinstance(value, dict) or set(value) != {"legal_positions", "requests"}:
        raise ValueError("Claim / Request output divergente do schema")
    if not isinstance(value["legal_positions"], list) or not isinstance(value["requests"], list):
        raise ValueError("legal_positions/requests devem ser listas")

    source = validate_source_input(skill_input)
    resolved_actor_ids = {
        str(item["actor_id"])
        for item in skill_input.get("actors") or []
        if item.get("resolution_status") == "RESOLVED"
    }
    source_actor = skill_input.get("source_actor") or {}
    if source_actor.get("status") == "RESOLVED" and source_actor.get("actor_id"):
        resolved_actor_ids.add(str(source_actor["actor_id"]))

    unresolved_points: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str | None]] = set()

    def validate_items(collection: str, values: list[Any]) -> list[dict[str, Any]]:
        out = []
        for item in values:
            if not isinstance(item, dict) or set(item) != {"text", "actor_id", "source_refs"}:
                raise ValueError(f"{collection} item divergente do schema")
            text = str(item["text"] or "").strip()
            actor_id = item["actor_id"]
            if not text:
                raise ValueError(f"{collection} com texto vazio")
            if actor_id is not None:
                actor_id = str(actor_id).strip()
                if actor_id not in resolved_actor_ids:
                    raise ValueError(f"{collection} actor_id inexistente/não resolvido")
            refs = validate_source_refs(item["source_refs"], source, field_name=f"{collection}.source_refs")
            key = (collection, normalize_text(text), actor_id)
            if key in seen:
                raise ValueError(f"{collection} duplicado")
            seen.add(key)
            out.append({
                "item_id": _stable_id(collection, source, text, actor_id),
                "text": text,
                "actor_id": actor_id,
                "source_refs": refs,
            })
            if actor_id is None:
                status = str(source_actor.get("status") or "UNRESOLVED")
                unresolved_points.append({
                    "code": "IMPLICIT_ACTOR_AMBIGUOUS" if status == "AMBIGUOUS" else "IMPLICIT_ACTOR_UNRESOLVED",
                    "reason": "Conteúdo extraído sem autor atribuível com segurança.",
                    "source_refs": refs,
                })
        return out
    positions = validate_items("legal_positions", value["legal_positions"])
    requests = validate_items("requests", value["requests"])
    if any(p["code"] == "IMPLICIT_ACTOR_AMBIGUOUS" for p in unresolved_points):
        sufficiency = "AMBIGUOUS"
    elif unresolved_points:
        sufficiency = "INSUFFICIENT"
    else:
        sufficiency = "SUFFICIENT"

    return {
        "schema_version": SCHEMA_VERSION,
        "context_sufficiency": sufficiency,
        "source_actor": source_actor,
        "legal_positions": positions,
        "requests": requests,
        "unresolved_points": unresolved_points,
    }


def score_claim_request(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    def overlap(a: str, b: str) -> bool:
        a_n, b_n = normalize_text(a), normalize_text(b)
        return bool(a_n and b_n and (a_n in b_n or b_n in a_n))

    def score_collection(name: str) -> tuple[float, float, int]:
        exp = list(expected.get(name) or [])
        act = list(actual.get(name) or [])
        unmatched = set(range(len(act)))
        matched = 0
        actor_mismatches = 0
        for e in exp:
            hit = next((i for i in unmatched if overlap(str(e.get("text") or ""), str(act[i].get("text") or ""))), None)
            if hit is None:
                continue
            matched += 1
            unmatched.remove(hit)
            if e.get("actor_id") != act[hit].get("actor_id"):
                actor_mismatches += 1
        return (
            1.0 if not act else matched / len(act),
            1.0 if not exp else matched / len(exp),
            actor_mismatches,
        )

    lp_p, lp_r, lp_a = score_collection("legal_positions")
    rq_p, rq_r, rq_a = score_collection("requests")
    return {
        "legal_position_precision": lp_p,
        "legal_position_recall": lp_r,
        "request_precision": rq_p,
        "request_recall": rq_r,
        "actor_mismatch_count": lp_a + rq_a,
        "sufficiency_match": expected.get("context_sufficiency") == actual.get("context_sufficiency"),
    }
