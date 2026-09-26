"""Strict, source-verifiable contract for incremental Movement analysis V2."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any

SCHEMA_VERSION = "movement-analysis-v2"
COLLECTIONS = ("assertions", "requests", "decisions", "events", "obligations")
MOVEMENT_INPUT_FIELDS = ("movement_id", "origin", "occurred_at", "movement_type", "pages", "source_text")
ANALYSIS_JSON_SCHEMA: dict[str, Any] = {
    "type": "object", "additionalProperties": False,
    "properties": {"movements": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "movement_id": {"type": "string"}, "summary": {"type": "string"},
            "summary_source_refs": {"type": "array", "items": {"$ref": "#/$defs/source_ref"}},
            **{name: {"type": "array", "items": {"$ref": "#/$defs/fact"}} for name in COLLECTIONS},
            "relations": {"type": "array", "items": {"$ref": "#/$defs/relation"}},
        },
        "required": ["movement_id", "summary", "summary_source_refs", *COLLECTIONS, "relations"],
    }}},
    "required": ["movements"],
    "$defs": {
        "source_ref": {"type": "object", "additionalProperties": False,
            "properties": {"document_id": {"type": "string"}, "page_number": {"type": "integer", "minimum": 1}, "quote": {"type": "string", "minLength": 1}},
            "required": ["document_id", "page_number", "quote"]},
        "fact": {"type": "object", "additionalProperties": False,
            "properties": {"key": {"type": "string", "minLength": 1}, "text": {"type": "string", "minLength": 1}, "source_refs": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/source_ref"}}},
            "required": ["key", "text", "source_refs"]},
        "ref": {"type": "object", "additionalProperties": False,
            "properties": {"scope": {"type": "string", "enum": ["movement", "known", "main"]}, "collection": {"type": "string", "enum": list(COLLECTIONS)}, "key": {"type": "string"}, "id": {"type": "string"}},
            "required": ["scope"]},
        "relation": {"type": "object", "additionalProperties": False,
            "properties": {"key": {"type": "string", "minLength": 1}, "subject": {"$ref": "#/$defs/ref"}, "predicate": {"type": "string", "minLength": 1}, "object": {"$ref": "#/$defs/ref"}, "source_refs": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/source_ref"}}},
            "required": ["key", "subject", "predicate", "object", "source_refs"]},
    },
}


def build_analysis_input(main: dict[str, Any], known: list[dict[str, Any]], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep process identity once per batch and expose only Movement-owned source fields."""
    movements = []
    for record in records:
        if any(field not in record for field in MOVEMENT_INPUT_FIELDS):
            raise ValueError("Movement V2 sem campo de entrada obrigatório")
        movements.append({field: record[field] for field in MOVEMENT_INPUT_FIELDS})
    return {"main": main, "known": known, "movements": movements}


def build_analysis_instructions(movement_ids: list[str]) -> str:
    """Single V2 instruction contract passed to Hermes for structured analysis."""
    if not isinstance(movement_ids, list) or not movement_ids or any(not isinstance(value, str) or not value.strip() for value in movement_ids):
        raise ValueError("movement_ids deve ser lista explícita, não vazia e sem ids vazios")
    if len(set(movement_ids)) != len(movement_ids):
        raise ValueError("movement_ids não pode conter duplicados")
    ids_json = json.dumps(movement_ids, ensure_ascii=False)
    return (
        "Analise cada Movement recebido independentemente. `main` é identidade processual compartilhada; não repita nele dados estáveis em cada Movement. "
        "`known` contém somente objetos de análises V2 anteriores já validadas e persistidas; use seus IDs em relações quando pertinente. "
        "`origin` é exclusivamente metadata/provenance do provider e nunca cria parte, representante ou identidade. "
        "Não crie conteúdo sem suporte no texto da peça principal. Cada item de `summary_source_refs[]` e `source_refs[]` deve trazer citação literal verificável na página indicada. "
        "Use `summary` como síntese compatível com summary_text; `assertions` para alegações/fatos afirmados, `requests` para providências pedidas, `decisions` para comandos/decisões, `events` para ocorrências, `obligations` para deveres expressamente estabelecidos e `relations` para relações documentadas. "
        "Essas categorias não inferem status. Relations referencia objetos locais por scope=movement (collection/key), anteriores persistidos por scope=known (id), ou identidade processual compartilhada por scope=main (id), com predicate textual sustentado pela fonte. "
        "Responda somente no schema, com exatamente um registro para cada Movement e na ordem recebida; não omita, duplique nem crie IDs: " + ids_json
    )


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip().casefold()


def deterministic_id(process_id: str, movement_id: str, source_hash: str, collection: str, key: str) -> str:
    raw = "\0".join((process_id, movement_id, source_hash, collection, key))
    return "ma2_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def validate_analysis(value: Any, movement_ids: list[str], *, sources: dict[str, dict[tuple[str, int], str]], known_ids: set[str], main_ids: set[str]) -> list[dict[str, Any]]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("resposta V2 não é JSON válido") from exc
    if not isinstance(value, dict) or set(value) != {"movements"} or not isinstance(value["movements"], list):
        raise ValueError("resposta V2 deve conter somente movements[]")
    expected = [str(item) for item in movement_ids]
    entries = value["movements"]
    if len(entries) != len(expected) or [entry.get("movement_id") for entry in entries if isinstance(entry, dict)] != expected:
        raise ValueError("resposta V2 deve conter exatamente os Movement ids, na ordem enviada")
    validated = []

    def check_refs(refs: Any, movement_id: str) -> None:
        if not isinstance(refs, list) or not refs:
            raise ValueError("todo conteúdo semântico exige source_refs")
        allowed_pages = sources.get(movement_id, {})
        for ref in refs:
            if not isinstance(ref, dict) or set(ref) != {"document_id", "page_number", "quote"}:
                raise ValueError("source_ref inválida")
            if not isinstance(ref["document_id"], str) or not ref["document_id"].strip() or isinstance(ref["page_number"], bool) or not isinstance(ref["page_number"], int) or ref["page_number"] < 1 or not isinstance(ref["quote"], str):
                raise ValueError("source_ref contém tipos/valores inválidos")
            quote = str(ref["quote"] or "")
            source = allowed_pages.get((str(ref["document_id"]), ref["page_number"]))
            if not quote.strip() or source is None or _norm(quote) not in _norm(source):
                raise ValueError(f"provenance não conferível em {movement_id}: {ref.get('document_id')}:{ref.get('page_number')}")

    for entry in entries:
        required_fields = {"movement_id", "summary", "summary_source_refs", *COLLECTIONS, "relations"}
        if not isinstance(entry, dict) or set(entry) != required_fields:
            raise ValueError("campos do Movement V2 divergentes do schema")
        movement_id = entry["movement_id"]
        if not isinstance(entry.get("summary"), str) or not entry["summary"].strip():
            raise ValueError(f"summary vazio em {movement_id}")
        check_refs(entry["summary_source_refs"], movement_id)
        local: dict[str, set[str]] = {name: set() for name in COLLECTIONS}
        for collection in COLLECTIONS:
            values = entry.get(collection)
            if not isinstance(values, list):
                raise ValueError(f"{collection} deve ser lista")
            for item in values:
                if not isinstance(item, dict) or not isinstance(item.get("key"), str) or not item["key"].strip() or item["key"] in local[collection]:
                    raise ValueError(f"key ausente/duplicada em {movement_id}.{collection}")
                if not isinstance(item.get("text"), str) or not item["text"].strip():
                    raise ValueError(f"texto vazio em {movement_id}.{collection}")
                if set(item) != {"key", "text", "source_refs"}:
                    raise ValueError(f"campos inesperados em {movement_id}.{collection}")
                check_refs(item["source_refs"], movement_id)
                local[collection].add(item["key"])
        relation_keys: set[str] = set()
        if not isinstance(entry["relations"], list):
            raise ValueError("relations deve ser lista")
        for relation in entry["relations"]:
            if not isinstance(relation, dict) or set(relation) != {"key", "subject", "predicate", "object", "source_refs"}:
                raise ValueError(f"relation inválida em {movement_id}")
            key = relation["key"]
            if not isinstance(key, str) or not key.strip() or key in relation_keys or not isinstance(relation["predicate"], str) or not relation["predicate"].strip():
                raise ValueError(f"key de relation ausente/duplicada em {movement_id}")
            relation_keys.add(key)
            check_refs(relation["source_refs"], movement_id)
            for ref in (relation["subject"], relation["object"]):
                if not isinstance(ref, dict):
                    raise ValueError("endpoint de relation inválido")
                scope = ref.get("scope")
                if not isinstance(scope, str):
                    raise ValueError(f"scope inválido: {scope}")
                if scope == "known" and (set(ref) != {"scope", "id"} or not isinstance(ref.get("id"), str) or ref["id"] not in known_ids):
                    raise ValueError(f"referência known órfã: {ref.get('id')}")
                if scope == "main" and (set(ref) != {"scope", "id"} or not isinstance(ref.get("id"), str) or ref["id"] not in main_ids):
                    raise ValueError(f"referência main órfã: {ref.get('id')}")
                if scope == "movement":
                    collection, local_key = ref.get("collection"), ref.get("key")
                    if set(ref) != {"scope", "collection", "key"} or not isinstance(collection, str) or collection not in local or not isinstance(local_key, str) or local_key not in local[collection]:
                        raise ValueError("referência local órfã")
                if scope not in {"known", "main", "movement"}:
                    raise ValueError(f"scope inválido: {scope}")
        validated.append(entry)
    return validated


def validate_analysis_independently(
    value: Any,
    movement_ids: list[str],
    *,
    sources: dict[str, dict[tuple[str, int], str]],
    known_ids: set[str],
    main_ids: set[str],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Validate each requested Movement separately and return per-ID rejection reasons."""
    expected = [str(item) for item in movement_ids]
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            reason = f"resposta V2 não é JSON válido: {exc.msg}"
            return [], {movement_id: reason for movement_id in expected}
    if not isinstance(value, dict) or set(value) != {"movements"} or not isinstance(value.get("movements"), list):
        reason = "resposta V2 deve conter somente movements[]"
        return [], {movement_id: reason for movement_id in expected}

    entries_by_id: dict[str, list[dict[str, Any]]] = {movement_id: [] for movement_id in expected}
    for entry in value["movements"]:
        if isinstance(entry, dict) and isinstance(entry.get("movement_id"), str):
            entries = entries_by_id.get(entry["movement_id"])
            if entries is not None:
                entries.append(entry)

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
                {"movements": entries}, [movement_id],
                sources={movement_id: sources.get(movement_id, {})},
                known_ids=known_ids, main_ids=main_ids,
            )
            validated.append(result[0])
        except Exception as exc:
            rejected[movement_id] = str(exc) or type(exc).__name__
    return validated, rejected


def build_known(rows: list[dict[str, Any]], *, exclude_movement_ids: set[str] | None = None) -> list[dict[str, str]]:
    exclude = exclude_movement_ids or set()
    result = []
    for row in rows:
        if row.get("movement_id") in exclude:
            continue
        analysis = row.get("analysis") or {}
        for collection in COLLECTIONS:
            for item in analysis.get(collection, []):
                result.append({"id": deterministic_id(row["process_id"], row["movement_id"], row["source_hash"], collection, item["key"]), "collection": collection, "text": item["text"], "movement_id": row["movement_id"]})
        for relation in analysis.get("relations", []):
            result.append({"id": deterministic_id(row["process_id"], row["movement_id"], row["source_hash"], "relations", relation["key"]),
                           "collection": "relations", "text": json.dumps({"subject": relation["subject"], "predicate": relation["predicate"], "object": relation["object"]}, ensure_ascii=False, sort_keys=True),
                           "movement_id": row["movement_id"]})
    return sorted(result, key=lambda item: (item["movement_id"], item["collection"], item["id"]))
