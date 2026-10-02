"""Strict, source-verifiable contract for Movement Analysis V3."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any

SCHEMA_VERSION = "movement-analysis-v3"
SEMANTIC_ROLES = (
    "FACTUAL_ASSERTION", "LEGAL_POSITION", "REQUEST", "JUDICIAL_FINDING",
    "JUDICIAL_DECISION", "EVIDENCE_REFERENCE", "EVENT", "OBLIGATION",
)
EPISTEMIC_STATUSES = (
    "UNILATERAL", "CONTESTED_EXPLICIT", "ADMITTED_EXPLICIT",
    "JUDICIALLY_FOUND", "NOT_APPLICABLE", "UNCERTAIN",
)
SUPPORT_STATUSES = ("NONE_IN_CONTEXT", "EVIDENCE_REFERENCED", "NOT_APPLICABLE")
NONFACTUAL_ROLES = {
    "LEGAL_POSITION", "REQUEST", "JUDICIAL_DECISION",
    "EVIDENCE_REFERENCE", "EVENT", "OBLIGATION",
}
ACTOR_MODES = ("MAIN_REF", "SOURCE_TEXT", "UNSPECIFIED")
MOVEMENT_INPUT_FIELDS = (
    "movement_id", "origin", "occurred_at", "movement_type", "pages",
)
SOURCE_REF_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "document_id": {"type": "string"},
        "page_number": {"type": "integer", "minimum": 1},
        "quote": {"type": "string", "minLength": 1},
    },
    "required": ["document_id", "page_number", "quote"],
}
ACTOR_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "mode": {"type": "string", "enum": list(ACTOR_MODES)},
        "value": {"type": "string"},
    },
    "required": ["mode", "value"],
}
EVIDENCE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "key": {"type": "string", "minLength": 1},
        "semantic_role": {"type": "string", "enum": list(SEMANTIC_ROLES)},
        "text": {"type": "string", "minLength": 1},
        "actor": ACTOR_SCHEMA,
        "epistemic_status": {
            "type": "string",
            "enum": list(EPISTEMIC_STATUSES),
            "description": (
                "FACTUAL_ASSERTION: UNILATERAL/CONTESTED_EXPLICIT/ADMITTED_EXPLICIT/UNCERTAIN; "
                "JUDICIAL_FINDING: JUDICIALLY_FOUND; other semantic roles: NOT_APPLICABLE."
            ),
        },
        "support_status": {
            "type": "string",
            "enum": list(SUPPORT_STATUSES),
            "description": (
                "Only FACTUAL_ASSERTION uses NONE_IN_CONTEXT/EVIDENCE_REFERENCED; "
                "other semantic roles require NOT_APPLICABLE."
            ),
        },
        "temporal_reference": {"type": "string"},
        "material_qualifiers": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "source_refs": {"type": "array", "minItems": 1, "items": SOURCE_REF_SCHEMA},
    },
    "required": [
        "key", "semantic_role", "text", "actor", "epistemic_status",
        "support_status", "temporal_reference", "material_qualifiers", "source_refs",
    ],
}
DRAFTING_EXTRACT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "key": {"type": "string", "minLength": 1},
        "evidence_key": {"type": "string", "minLength": 1},
        "text": {"type": "string", "minLength": 1},
        "semantic_role": {"type": "string", "enum": list(SEMANTIC_ROLES)},
        "actor": ACTOR_SCHEMA,
        "epistemic_status": {
            "type": "string",
            "enum": list(EPISTEMIC_STATUSES),
            "description": (
                "FACTUAL_ASSERTION: UNILATERAL/CONTESTED_EXPLICIT/ADMITTED_EXPLICIT/UNCERTAIN; "
                "JUDICIAL_FINDING: JUDICIALLY_FOUND; other semantic roles: NOT_APPLICABLE."
            ),
        },
        "support_status": {
            "type": "string",
            "enum": list(SUPPORT_STATUSES),
            "description": (
                "Only FACTUAL_ASSERTION uses NONE_IN_CONTEXT/EVIDENCE_REFERENCED; "
                "other semantic roles require NOT_APPLICABLE."
            ),
        },
        "material_qualifiers": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "source_refs": {"type": "array", "minItems": 1, "items": SOURCE_REF_SCHEMA},
    },
    "required": [
        "key", "evidence_key", "text", "semantic_role", "actor",
        "epistemic_status", "support_status", "material_qualifiers", "source_refs",
    ],
}
REF_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "scope": {"type": "string", "enum": ["movement", "known", "main"]},
        "value": {"type": "string", "minLength": 1},
    },
    "required": ["scope", "value"],
}
RELATION_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "key": {"type": "string", "minLength": 1},
        "subject": REF_SCHEMA,
        "predicate": {"type": "string", "minLength": 1},
        "object": REF_SCHEMA,
        "source_refs": {"type": "array", "minItems": 1, "items": SOURCE_REF_SCHEMA},
    },
    "required": ["key", "subject", "predicate", "object", "source_refs"],
}
ANALYSIS_JSON_SCHEMA: dict[str, Any] = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "movements": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "movement_id": {"type": "string"},
                    "summary": {"type": "string", "minLength": 1},
                    "summary_source_refs": {
                        "type": "array", "minItems": 1, "items": SOURCE_REF_SCHEMA,
                    },
                    "evidence": {"type": "array", "items": EVIDENCE_SCHEMA},
                    "drafting_extracts": {"type": "array", "items": DRAFTING_EXTRACT_SCHEMA},
                    "relations": {"type": "array", "items": RELATION_SCHEMA},
                },
                "required": [
                    "movement_id", "summary", "summary_source_refs",
                    "evidence", "drafting_extracts", "relations",
                ],
            },
        },
    },
    "required": ["movements"],
}
def build_analysis_input(
    main: dict[str, Any], known: list[dict[str, Any]], records: list[dict[str, Any]]
) -> dict[str, Any]:
    movements = []
    for record in records:
        if any(field not in record for field in MOVEMENT_INPUT_FIELDS):
            raise ValueError("Movement V3 sem campo de entrada obrigatório")
        movements.append({field: record[field] for field in MOVEMENT_INPUT_FIELDS})
    return {"main": main, "known": known, "movements": movements}


def build_analysis_instructions(movement_ids: list[str]) -> str:
    if (
        not isinstance(movement_ids, list)
        or not movement_ids
        or any(not isinstance(value, str) or not value.strip() for value in movement_ids)
        or len(set(movement_ids)) != len(movement_ids)
    ):
        raise ValueError("movement_ids deve ser lista explícita, não vazia e sem duplicados")
    ids_json = json.dumps(movement_ids, ensure_ascii=False)
    return (
        "Analise cada Movement de forma independente e juridicamente conservadora. "
        "main contém somente identidade/contexto processual compartilhado; known contém apenas objetos "
        "anteriores já validados. origin é metadata do provider e não autoriza inferir identidade, autoria ou parte. "
        "Use exclusivamente pages[].content da peça principal; cada página vem separada com document_id e page_number. "
        "Anexos não estão implicitamente provados. Cada summary, unidade de evidence, drafting_extract e relation deve "
        "ser sustentado por source_refs cujo quote seja copiado como substring literal do content da mesma página indicada "
        "por document_id/page_number. Não parafraseie o quote nem atribua trecho de uma página a outra. Preserve contradições "
        "e ambiguidades em vez de harmonizá-las. "
        "Nunca promova alegação a fato provado, referência documental a prova validada, posição jurídica a fato, "
        "pedido a decisão ou decisão a cumprimento. "
        "Em evidence use exatamente os papéis FACTUAL_ASSERTION, LEGAL_POSITION, REQUEST, JUDICIAL_FINDING, "
        "JUDICIAL_DECISION, EVIDENCE_REFERENCE, EVENT ou OBLIGATION. FACTUAL_ASSERTION descreve afirmação factual "
        "atribuída; JUDICIAL_FINDING somente constatação factual efetivamente adotada pelo juízo; JUDICIAL_DECISION "
        "somente comando ou resultado decisório. Use epistemic_status SOMENTE para FACTUAL_ASSERTION e JUDICIAL_FINDING: "
        "FACTUAL_ASSERTION admite UNILATERAL, CONTESTED_EXPLICIT, ADMITTED_EXPLICIT ou UNCERTAIN; JUDICIAL_FINDING exige "
        "JUDICIALLY_FOUND. Para LEGAL_POSITION, REQUEST, JUDICIAL_DECISION, EVIDENCE_REFERENCE, EVENT e OBLIGATION use "
        "epistemic_status=NOT_APPLICABLE, pois o papel semântico já expressa sua natureza. "
        "support_status=EVIDENCE_REFERENCED apenas quando a própria FACTUAL_ASSERTION fizer referência expressa a suporte probatório; "
        "sem afirmar que esse suporte foi validado. actor MAIN_REF só pode usar id recebido em main; SOURCE_TEXT exige "
        "expressão literal do texto; se não for seguro, use UNSPECIFIED com value vazio. temporal_reference deve ser "
        "vazio quando não houver referência temporal material segura. material_qualifiers deve conter trechos curtos "
        "literais da fonte que preservem negações, condicionantes, exceções, parcialidade, incerteza, alcance, datas, "
        "valores, prazos ou outros qualificadores "
        "cuja perda alteraria o sentido jurídico. drafting_extracts são fragmentos reutilizáveis para futura redação: "
        "produza apenas para evidência materialmente útil, um extract por evidence_key. O texto deve ser a menor "
        "formulação autossuficiente que preserve o sentido do ato, sem limite fixo de tamanho; se não for possível "
        "comprimir com segurança, mantenha formulação mais longa. No drafting_extract copie exatamente semantic_role, "
        "actor, epistemic_status, support_status, material_qualifiers e source_refs da evidence referenciada; não "
        "acrescente conclusão jurídica nova. summary deve ser uma síntese factual curta do ato, não substitui evidence "
        "nem a fonte original. Responda somente no schema, com exatamente um registro por Movement, na ordem recebida; "
        "IDs esperados: " + ids_json
    )


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip().casefold()


def deterministic_id(
    process_id: str, movement_id: str, source_hash: str, collection: str, key: str
) -> str:
    raw = "\0".join((process_id, movement_id, source_hash, collection, key))
    return "ma3_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _same_refs(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> bool:
    return json.dumps(left, ensure_ascii=False, sort_keys=True) == json.dumps(
        right, ensure_ascii=False, sort_keys=True
    )


def _numeric_tokens(text: str) -> set[str]:
    return set(re.findall(r"(?<!\w)\d[\d./,:-]*", text))


def validate_analysis(
    value: Any,
    movement_ids: list[str],
    *,
    sources: dict[str, dict[tuple[str, int], str]],
    known_ids: set[str],
    main_ids: set[str],
    actor_ids: set[str],
) -> list[dict[str, Any]]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("resposta V3 não é JSON válido") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"movements"}
        or not isinstance(value["movements"], list)
    ):
        raise ValueError("resposta V3 deve conter somente movements[]")
    expected = [str(item) for item in movement_ids]
    entries = value["movements"]
    if (
        len(entries) != len(expected)
        or [entry.get("movement_id") for entry in entries if isinstance(entry, dict)] != expected
    ):
        raise ValueError("resposta V3 deve conter exatamente os Movement ids, na ordem enviada")

    def check_refs(refs: Any, movement_id: str) -> None:
        if not isinstance(refs, list) or not refs:
            raise ValueError("todo conteúdo semântico exige source_refs")
        allowed_pages = sources.get(movement_id, {})
        for ref in refs:
            if not isinstance(ref, dict) or set(ref) != {"document_id", "page_number", "quote"}:
                raise ValueError("source_ref inválida")
            if (
                not isinstance(ref["document_id"], str)
                or not ref["document_id"].strip()
                or isinstance(ref["page_number"], bool)
                or not isinstance(ref["page_number"], int)
                or ref["page_number"] < 1
                or not isinstance(ref["quote"], str)
                or not ref["quote"].strip()
            ):
                raise ValueError("source_ref contém tipos/valores inválidos")
            source = allowed_pages.get((ref["document_id"], ref["page_number"]))
            if source is None or _norm(ref["quote"]) not in _norm(source):
                raise ValueError(
                    f"provenance não conferível em {movement_id}: "
                    f"{ref.get('document_id')}:{ref.get('page_number')}"
                )

    def check_actor(actor: Any, movement_id: str) -> None:
        if not isinstance(actor, dict) or set(actor) != {"mode", "value"}:
            raise ValueError(f"actor inválido em {movement_id}")
        mode, actor_value = actor.get("mode"), actor.get("value")
        if mode not in ACTOR_MODES or not isinstance(actor_value, str):
            raise ValueError(f"actor inválido em {movement_id}")
        if mode == "MAIN_REF" and actor_value not in actor_ids:
            raise ValueError(f"actor MAIN_REF órfão em {movement_id}: {actor_value}")
        if mode == "UNSPECIFIED" and actor_value:
            raise ValueError(f"actor UNSPECIFIED deve ter value vazio em {movement_id}")
        if mode == "SOURCE_TEXT":
            if not actor_value.strip():
                raise ValueError(f"actor SOURCE_TEXT vazio em {movement_id}")
            joined = " ".join(sources.get(movement_id, {}).values())
            if _norm(actor_value) not in _norm(joined):
                raise ValueError(f"actor SOURCE_TEXT não conferível em {movement_id}")

    validated: list[dict[str, Any]] = []
    for entry in entries:
        required = {
            "movement_id", "summary", "summary_source_refs",
            "evidence", "drafting_extracts", "relations",
        }
        if not isinstance(entry, dict) or set(entry) != required:
            raise ValueError("campos do Movement V3 divergentes do schema")
        movement_id = entry["movement_id"]
        if not isinstance(entry["summary"], str) or not entry["summary"].strip():
            raise ValueError(f"summary vazio em {movement_id}")
        check_refs(entry["summary_source_refs"], movement_id)
        if not isinstance(entry["evidence"], list):
            raise ValueError(f"evidence deve ser lista em {movement_id}")

        evidence_by_key: dict[str, dict[str, Any]] = {}
        for item in entry["evidence"]:
            expected_fields = {
                "key", "semantic_role", "text", "actor", "epistemic_status",
                "support_status", "temporal_reference", "material_qualifiers", "source_refs",
            }
            if not isinstance(item, dict) or set(item) != expected_fields:
                raise ValueError(f"evidence inválida em {movement_id}")
            key = item["key"]
            if not isinstance(key, str) or not key.strip() or key in evidence_by_key:
                raise ValueError(f"key de evidence ausente/duplicada em {movement_id}")
            if (
                item["semantic_role"] not in SEMANTIC_ROLES
                or item["epistemic_status"] not in EPISTEMIC_STATUSES
                or item["support_status"] not in SUPPORT_STATUSES
                or not isinstance(item["text"], str)
                or not item["text"].strip()
                or not isinstance(item["temporal_reference"], str)
            ):
                raise ValueError(f"conteúdo/status inválido em {movement_id}.{key}")
            qualifiers = item["material_qualifiers"]
            if (
                not isinstance(qualifiers, list)
                or any(not isinstance(q, str) or not q.strip() for q in qualifiers)
                or len(qualifiers) != len(set(qualifiers))
            ):
                raise ValueError(f"material_qualifiers inválidos em {movement_id}.{key}")
            check_actor(item["actor"], movement_id)
            check_refs(item["source_refs"], movement_id)
            source_text = " ".join(sources.get(movement_id, {}).values())
            if item["temporal_reference"] and _norm(item["temporal_reference"]) not in _norm(source_text):
                raise ValueError(f"temporal_reference não conferível em {movement_id}.{key}")
            for qualifier in qualifiers:
                if _norm(qualifier) not in _norm(source_text):
                    raise ValueError(
                        f"material_qualifier não conferível em {movement_id}.{key}: {qualifier}"
                    )
            role, status = item["semantic_role"], item["epistemic_status"]
            support = item["support_status"]
            if role == "FACTUAL_ASSERTION":
                if status not in {
                    "UNILATERAL", "CONTESTED_EXPLICIT", "ADMITTED_EXPLICIT", "UNCERTAIN",
                }:
                    raise ValueError(
                        f"FACTUAL_ASSERTION com estado epistêmico inválido em {movement_id}.{key}"
                    )
                if support not in {"NONE_IN_CONTEXT", "EVIDENCE_REFERENCED"}:
                    raise ValueError(
                        f"FACTUAL_ASSERTION com support_status inválido em {movement_id}.{key}"
                    )
            elif role == "JUDICIAL_FINDING":
                if status != "JUDICIALLY_FOUND" or support != "NOT_APPLICABLE":
                    raise ValueError(
                        f"JUDICIAL_FINDING exige JUDICIALLY_FOUND em {movement_id}.{key}"
                    )
            elif status != "NOT_APPLICABLE" or support != "NOT_APPLICABLE":
                raise ValueError(
                    f"papel não factual exige estado NOT_APPLICABLE em {movement_id}.{key}"
                )
            evidence_by_key[key] = item

        if not isinstance(entry["drafting_extracts"], list):
            raise ValueError(f"drafting_extracts deve ser lista em {movement_id}")
        drafting_keys: set[str] = set()
        drafting_evidence: set[str] = set()
        for item in entry["drafting_extracts"]:
            expected_fields = {
                "key", "evidence_key", "text", "semantic_role", "actor",
                "epistemic_status", "support_status", "material_qualifiers", "source_refs",
            }
            if not isinstance(item, dict) or set(item) != expected_fields:
                raise ValueError(f"drafting_extract inválido em {movement_id}")
            key, evidence_key = item["key"], item["evidence_key"]
            if (
                not isinstance(key, str) or not key.strip() or key in drafting_keys
                or not isinstance(evidence_key, str) or evidence_key not in evidence_by_key
                or evidence_key in drafting_evidence
                or not isinstance(item["text"], str) or not item["text"].strip()
            ):
                raise ValueError(f"drafting_extract inválido/duplicado em {movement_id}")
            source = evidence_by_key[evidence_key]
            source_text = " ".join(sources.get(movement_id, {}).values())
            for token in _numeric_tokens(item["text"]):
                if token not in source_text:
                    raise ValueError(
                        f"drafting_extract contém dado numérico não conferível em {movement_id}.{key}: {token}"
                    )
            for field in (
                "semantic_role", "actor", "epistemic_status",
                "support_status", "material_qualifiers",
            ):
                if item[field] != source[field]:
                    raise ValueError(
                        f"drafting_extract diverge da evidence em {movement_id}.{key}: {field}"
                    )
            if not _same_refs(item["source_refs"], source["source_refs"]):
                raise ValueError(
                    f"drafting_extract diverge da evidence em {movement_id}.{key}: source_refs"
                )
            drafting_keys.add(key)
            drafting_evidence.add(evidence_key)

        if not isinstance(entry["relations"], list):
            raise ValueError(f"relations deve ser lista em {movement_id}")
        relation_keys: set[str] = set()
        for relation in entry["relations"]:
            if (
                not isinstance(relation, dict)
                or set(relation) != {"key", "subject", "predicate", "object", "source_refs"}
            ):
                raise ValueError(f"relation inválida em {movement_id}")
            key = relation["key"]
            if (
                not isinstance(key, str) or not key.strip() or key in relation_keys
                or not isinstance(relation["predicate"], str) or not relation["predicate"].strip()
            ):
                raise ValueError(f"key/predicate inválido em {movement_id}")
            check_refs(relation["source_refs"], movement_id)
            for ref in (relation["subject"], relation["object"]):
                if not isinstance(ref, dict) or set(ref) != {"scope", "value"}:
                    raise ValueError(f"endpoint de relation inválido em {movement_id}.{key}")
                scope, ref_value = ref["scope"], ref["value"]
                if not isinstance(ref_value, str) or not ref_value:
                    raise ValueError(f"endpoint de relation vazio em {movement_id}.{key}")
                if scope == "movement" and ref_value not in evidence_by_key:
                    raise ValueError(f"referência local órfã em {movement_id}.{key}: {ref_value}")
                if scope == "known" and ref_value not in known_ids:
                    raise ValueError(f"referência known órfã em {movement_id}.{key}: {ref_value}")
                if scope == "main" and ref_value not in main_ids:
                    raise ValueError(f"referência main órfã em {movement_id}.{key}: {ref_value}")
                if scope not in {"movement", "known", "main"}:
                    raise ValueError(f"scope inválido em {movement_id}.{key}: {scope}")
            relation_keys.add(key)
        validated.append(entry)
    return validated


def build_known(
    rows: list[dict[str, Any]], *, exclude_movement_ids: set[str] | None = None
) -> list[dict[str, str]]:
    exclude = exclude_movement_ids or set()
    result: list[dict[str, str]] = []
    for row in rows:
        if row.get("movement_id") in exclude:
            continue
        analysis = row.get("analysis") or {}
        for item in analysis.get("evidence", []):
            result.append({
                "id": deterministic_id(
                    row["process_id"], row["movement_id"], row["source_hash"],
                    "evidence", item["key"],
                ),
                "semantic_role": item["semantic_role"],
                "text": item["text"],
                "movement_id": row["movement_id"],
            })
        for relation in analysis.get("relations", []):
            result.append({
                "id": deterministic_id(
                    row["process_id"], row["movement_id"], row["source_hash"],
                    "relations", relation["key"],
                ),
                "semantic_role": "RELATION",
                "text": json.dumps(
                    {
                        "subject": relation["subject"],
                        "predicate": relation["predicate"],
                        "object": relation["object"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "movement_id": row["movement_id"],
            })
    return sorted(
        result, key=lambda item: (item["movement_id"], item["semantic_role"], item["id"])
    )

def validate_analysis_independently(
    value: Any,
    movement_ids: list[str],
    *,
    sources: dict[str, dict[tuple[str, int], str]],
    known_ids: set[str],
    main_ids: set[str],
    actor_ids: set[str],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Validate requested Movements separately and preserve valid results."""
    expected = [str(item) for item in movement_ids]
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            reason = f"resposta V3 não é JSON válido: {exc.msg}"
            return [], {movement_id: reason for movement_id in expected}
    if not isinstance(value, dict) or set(value) != {"movements"} or not isinstance(value.get("movements"), list):
        reason = "resposta V3 deve conter somente movements[]"
        return [], {movement_id: reason for movement_id in expected}

    entries_by_id: dict[str, list[dict[str, Any]]] = {movement_id: [] for movement_id in expected}
    for entry in value["movements"]:
        if isinstance(entry, dict) and isinstance(entry.get("movement_id"), str):
            bucket = entries_by_id.get(entry["movement_id"])
            if bucket is not None:
                bucket.append(entry)

    validated: list[dict[str, Any]] = []
    rejected: dict[str, str] = {}
    for movement_id in expected:
        entries = entries_by_id[movement_id]
        if not entries:
            rejected[movement_id] = "Movement ausente na resposta estruturada"
            continue
        if len(entries) != 1:
            rejected[movement_id] = f"Movement repetido na resposta estruturada ({len(entries)} ocorrências)"
            continue
        try:
            result = validate_analysis(
                {"movements": entries},
                [movement_id],
                sources={movement_id: sources.get(movement_id, {})},
                known_ids=known_ids,
                main_ids=main_ids,
                actor_ids=actor_ids,
            )
            validated.append(result[0])
        except Exception as exc:
            rejected[movement_id] = str(exc) or type(exc).__name__
    return validated, rejected
