"""Evidence Mapper V1.

Maps available evidentiary material to already extracted facts without deciding
truth, legal sufficiency of proof, or ultimate evidentiary weight.
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

SCHEMA_VERSION = "evidence-mapper-v1"

EVIDENCE_KINDS = (
    "DOCUMENT",
    "OFFICIAL_RECORD",
    "TESTIMONY",
    "ADMISSION",
    "EXPERT_OPINION",
    "VISUAL_ASSET",
    "OTHER",
)
EVIDENCE_SOURCE_KINDS = (
    "PARTY_SUBMISSION",
    "DOCUMENT",
    "OFFICIAL_RECORD",
    "TESTIMONY",
    "EXPERT_REPORT",
    "VISUAL_ASSET",
    "OTHER",
)
_IDENTITY_UNCLEAR_RE = re.compile(
    r"\b(sem\s+identifica[cç][aã]o\s+d[oa]\s+(?:benefici[aá]ri[oa]|destinat[aá]ri[oa])|"
    r"(?:benefici[aá]ri[oa]|destinat[aá]ri[oa])\s+n[aã]o\s+identificad[oa]|"
    r"identidade\s+(?:n[aã]o\s+)?(?:informada|identificada))\b",
    re.IGNORECASE,
)
EVIDENCE_RELATIONS = ("SUPPORTS", "CONTRADICTS", "INCONCLUSIVE")
DIRECTNESS_STATES = ("DIRECT", "INDIRECT", "UNKNOWN")
SCOPE_STATES = ("FULL", "PARTIAL")
LIMITATION_CODES = (
    "AUTHENTICITY_DISPUTED",
    "SOURCE_INCOMPLETE",
    "IDENTITY_UNCLEAR",
    "TEMPORAL_MISMATCH",
    "HEARSAY",
    "LEGIBILITY_LIMITED",
    "OTHER",
)
UNRESOLVED_CODES = (
    "REFERENCED_EVIDENCE_NOT_AVAILABLE",
    "VISUAL_CONTENT_NOT_AVAILABLE",
    "SOURCE_IDENTITY_UNCLEAR",
    "EVIDENCE_REFERENCE_AMBIGUOUS",
    "OTHER",
)

EVIDENCE_MAPPER_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "evidence_items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "key": {"type": "string", "minLength": 1},
                    "source_id": {"type": "string", "minLength": 1},
                    "kind": {"type": "string", "enum": list(EVIDENCE_KINDS)},
                    "description": {"type": "string", "minLength": 1},
                    "source_refs": {
                        "type": "array", "minItems": 1, "items": SOURCE_REF_SCHEMA,
                    },
                },
                "required": ["key", "source_id", "kind", "description", "source_refs"],
            },
        },
        "links": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "fact_id": {"type": "string", "minLength": 1},
                    "evidence_key": {"type": "string", "minLength": 1},
                    "relation": {"type": "string", "enum": list(EVIDENCE_RELATIONS)},
                    "directness": {"type": "string", "enum": list(DIRECTNESS_STATES)},
                    "scope": {"type": "string", "enum": list(SCOPE_STATES)},
                    "limitations": {
                        "type": "array",
                        "uniqueItems": True,
                        "items": {"type": "string", "enum": list(LIMITATION_CODES)},
                    },
                    "source_refs": {
                        "type": "array", "minItems": 1, "items": SOURCE_REF_SCHEMA,
                    },
                },
                "required": [
                    "fact_id", "evidence_key", "relation", "directness",
                    "scope", "limitations", "source_refs",
                ],
            },
        },
        "unresolved_points": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "fact_id": {"type": ["string", "null"]},
                    "code": {"type": "string", "enum": list(UNRESOLVED_CODES)},
                    "reason": {"type": "string", "minLength": 1},
                    "source_refs": {
                        "type": "array", "minItems": 1, "items": SOURCE_REF_SCHEMA,
                    },
                },
                "required": ["fact_id", "code", "reason", "source_refs"],
            },
        },
    },
    "required": ["evidence_items", "links", "unresolved_points"],
}
def build_evidence_mapper_instructions() -> str:
    return """TASK: EVIDENCE_MAP

INPUT:
- facts[] = already validated factual propositions.
- evidence_sources[] = material actually available in this context.

SOURCE GATE — apply before any Fact×Evidence comparison:
1. source_kind=PARTY_SUBMISSION:
   - party narrative/repetition -> NOT EVIDENCE of underlying fact; emit no evidence_item;
   - explicit admission against the declarant's interest -> ADMISSION may be emitted.
2. source_kind=VISUAL_ASSET and content is only an unanalysed placeholder -> no evidence_item; unresolved VISUAL_CONTENT_NOT_AVAILABLE.
3. document/evidence only REFERENCED but content absent -> no evidence_item; unresolved REFERENCED_EVIDENCE_NOT_AVAILABLE.
4. otherwise, create evidence_item only for material actually present in evidence_sources.

FOR EACH Fact × admissible Evidence:
A. Compare material dimensions when present:
   actor/identity, action/event, object, amount, date/time, location.
B. If a REQUIRED dimension for the fact is UNKNOWN in evidence -> relation=INCONCLUSIVE.
C. Else if a material dimension is incompatible -> relation=CONTRADICTS.
D. Else if evidence is compatible with the proposition -> relation=SUPPORTS.
E. directness:
   DIRECT = source itself records/observes the relevant proposition;
   INDIRECT = requires an inferential step;
   UNKNOWN = cannot classify safely.
F. scope:
   FULL = all material fact dimensions covered;
   PARTIAL = only part covered.
G. limitations: emit only limitations explicitly supported by source/context.

PRECEDENCE:
SOURCE_GATE_REJECT > REQUIRED_DIMENSION_UNKNOWN > MATERIAL_CONTRADICTION > SUPPORT > INCONCLUSIVE

NEVER:
- decide PROVEN/NOT_PROVEN;
- infer legal sufficiency or ultimate evidentiary weight;
- invent authenticity disputes or generic weaknesses;
- treat the absence of evidence in this input as absence of evidence in the process.

SOURCE_REF: literal and verifiable, belonging to the same source_id.
OUTPUT: schema only."""


def _normalize_evidence_sources(process_id: str, evidence_sources: Any) -> list[dict[str, Any]]:
    if not isinstance(evidence_sources, list) or not evidence_sources:
        raise ValueError("evidence_sources deve ser lista não vazia")
    normalized: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    seen_pages: set[tuple[str, int]] = set()
    for source in evidence_sources:
        if not isinstance(source, dict):
            raise ValueError("evidence_source inválido")
        source_id = str(source.get("source_id") or "").strip()
        movement_id = str(source.get("movement_id") or "").strip()
        document_id = str(source.get("document_id") or "").strip()
        title = str(source.get("title") or "").strip()
        source_kind = str(source.get("source_kind") or "OTHER").strip().upper()
        actor_id = source.get("actor_id")
        pages = source.get("pages")
        if not source_id or source_id in seen_sources or not movement_id or not document_id:
            raise ValueError("evidence_source exige IDs únicos")
        if source_kind not in EVIDENCE_SOURCE_KINDS:
            raise ValueError("evidence_source contém source_kind inválido")
        if not isinstance(pages, list) or not pages:
            raise ValueError("evidence_source exige pages")
        normalized_pages = []
        for page in pages:
            if not isinstance(page, dict):
                raise ValueError("evidence page inválida")
            pdf_page = page.get("pdf_page")
            content = page.get("content")
            if isinstance(pdf_page, bool) or not isinstance(pdf_page, int) or pdf_page < 1 or not isinstance(content, str):
                raise ValueError("evidence page exige pdf_page positivo e content textual")
            key = (document_id, pdf_page)
            if key in seen_pages:
                raise ValueError("document/page duplicado em evidence_sources")
            seen_pages.add(key)
            normalized_pages.append({
                "document_id": document_id,
                "pdf_page": pdf_page,
                "content": content,
            })
        normalized.append({
            "source_id": source_id,
            "movement_id": movement_id,
            "document_id": document_id,
            "title": title,
            "source_kind": source_kind,
            "actor_id": actor_id,
            "pages": normalized_pages,
        })
        seen_sources.add(source_id)
    return normalized


def build_evidence_mapper_input(
    fact_skill_input: dict[str, Any],
    fact_output: dict[str, Any],
    evidence_sources: list[dict[str, Any]],
) -> dict[str, Any]:
    source = validate_source_input(fact_skill_input)
    if not isinstance(fact_output, dict) or not isinstance(fact_output.get("facts"), list):
        raise ValueError("fact_output sem facts")
    facts = []
    seen: set[str] = set()
    for item in fact_output["facts"]:
        if not isinstance(item, dict):
            raise ValueError("fact inválido")
        fact_id = str(item.get("fact_id") or "").strip()
        statement = str(item.get("statement") or "").strip()
        status = str(item.get("epistemic_status") or "").strip().upper()
        if not fact_id or fact_id in seen or not statement or not status:
            raise ValueError("fact incompleto/duplicado")
        seen.add(fact_id)
        facts.append({
            "fact_id": fact_id,
            "statement": statement,
            "epistemic_status": status,
            "actor_id": item.get("actor_id"),
            "source_refs": item.get("source_refs") or [],
        })
    normalized_sources = _normalize_evidence_sources(source["process_id"], evidence_sources)
    return {
        "process_id": source["process_id"],
        "facts": facts,
        "evidence_sources": normalized_sources,
    }


def _flat_source(skill_input: dict[str, Any]) -> dict[str, Any]:
    pages = []
    for source in skill_input.get("evidence_sources") or []:
        pages.extend(source.get("pages") or [])
    return {
        "process_id": skill_input["process_id"],
        "movement_id": "EVIDENCE_CONTEXT",
        "pages": pages,
    }


def _source_indexes(skill_input: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, int], str]]:
    by_id: dict[str, dict[str, Any]] = {}
    page_to_source: dict[tuple[str, int], str] = {}
    for source in skill_input.get("evidence_sources") or []:
        source_id = str(source["source_id"])
        by_id[source_id] = source
        for page in source.get("pages") or []:
            page_to_source[(str(page["document_id"]), int(page["pdf_page"]))] = source_id
    return by_id, page_to_source


def _stable_evidence_id(process_id: str, source_id: str, kind: str, description: str) -> str:
    raw = "\0".join((process_id, source_id, kind, normalize_text(description)))
    return "ev_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _fact_state(fact_id: str, links: list[dict[str, Any]]) -> str:
    relations = {item["relation"] for item in links if item["fact_id"] == fact_id}
    if "SUPPORTS" in relations and "CONTRADICTS" in relations:
        return "MIXED"
    if "SUPPORTS" in relations:
        return "SUPPORT_PRESENT"
    if "CONTRADICTS" in relations:
        return "CONTRADICTION_PRESENT"
    if "INCONCLUSIVE" in relations:
        return "INCONCLUSIVE"
    return "NO_EVIDENCE_IN_CONTEXT"


def _visual_placeholder_only(source: dict[str, Any]) -> bool:
    texts = [normalize_text(page.get("content") or "") for page in source.get("pages") or []]
    return bool(texts) and all(text.startswith("[visual_asset:") for text in texts)


def validate_evidence_mapping(value: Any, skill_input: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Evidence Mapper output não é JSON válido") from exc
    if not isinstance(value, dict) or set(value) != {"evidence_items", "links", "unresolved_points"}:
        raise ValueError("Evidence Mapper output divergente do schema")
    if not all(isinstance(value[name], list) for name in ("evidence_items", "links", "unresolved_points")):
        raise ValueError("coleções do Evidence Mapper devem ser listas")

    flat_source = _flat_source(skill_input)
    validate_source_input(flat_source)
    source_by_id, page_to_source = _source_indexes(skill_input)
    facts = {str(item["fact_id"]): item for item in skill_input.get("facts") or []}

    evidence_items: list[dict[str, Any]] = []
    keys: dict[str, str] = {}
    key_sources: dict[str, str] = {}
    key_kinds: dict[str, str] = {}
    for item in value["evidence_items"]:
        required = {"key", "source_id", "kind", "description", "source_refs"}
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError("evidence_item divergente do schema")
        key = str(item["key"] or "").strip()
        source_id = str(item["source_id"] or "").strip()
        kind = str(item["kind"] or "").strip().upper()
        description = str(item["description"] or "").strip()
        if not key or key in keys or source_id not in source_by_id or kind not in EVIDENCE_KINDS or not description:
            raise ValueError("evidence_item inválido")
        source_meta = source_by_id[source_id]
        if source_meta["source_kind"] == "PARTY_SUBMISSION" and kind != "ADMISSION":
            raise ValueError("PARTY_SUBMISSION não pode ser evidência do fato subjacente")
        if source_meta["source_kind"] == "PARTY_SUBMISSION" and kind == "ADMISSION" and not source_meta.get("actor_id"):
            raise ValueError("ADMISSION exige declarant actor_id em PARTY_SUBMISSION")
        if source_meta["source_kind"] == "VISUAL_ASSET" and _visual_placeholder_only(source_meta):
            raise ValueError("VISUAL_ASSET sem conteúdo analisável não pode virar evidence_item")
        refs = validate_source_refs(item["source_refs"], flat_source, field_name=f"{key}.source_refs")
        if any(page_to_source[(ref["document_id"], ref["pdf_page"])] != source_id for ref in refs):
            raise ValueError(f"{key}.source_refs não pertencem ao source_id")
        evidence_id = _stable_evidence_id(skill_input["process_id"], source_id, kind, description)
        keys[key] = evidence_id
        key_sources[key] = source_id
        key_kinds[key] = kind
        evidence_items.append({
            "evidence_id": evidence_id,
            "source_id": source_id,
            "kind": kind,
            "description": description,
            "source_refs": refs,
        })

    links: list[dict[str, Any]] = []
    seen_links: set[tuple[str, str, str]] = set()
    for item in value["links"]:
        required = {
            "fact_id", "evidence_key", "relation", "directness",
            "scope", "limitations", "source_refs",
        }
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError("evidence link divergente do schema")
        fact_id = str(item["fact_id"] or "").strip()
        evidence_key = str(item["evidence_key"] or "").strip()
        relation = str(item["relation"] or "").upper()
        directness = str(item["directness"] or "").upper()
        scope = str(item["scope"] or "").upper()
        limitations = item["limitations"]
        if fact_id not in facts:
            raise ValueError("evidence link referencia fact_id inexistente")
        if evidence_key not in keys:
            raise ValueError("evidence link referencia evidence_key inexistente")
        if relation not in EVIDENCE_RELATIONS or directness not in DIRECTNESS_STATES or scope not in SCOPE_STATES:
            raise ValueError("evidence link contém classificação inválida")
        if not isinstance(limitations, list) or len(set(limitations)) != len(limitations):
            raise ValueError("limitations inválido")
        limitations = [str(code).upper() for code in limitations]
        if any(code not in LIMITATION_CODES for code in limitations):
            raise ValueError("limitation code inválido")

        expected_source_id = key_sources[evidence_key]
        source_meta = source_by_id[expected_source_id]
        if source_meta["source_kind"] == "PARTY_SUBMISSION" and key_kinds[evidence_key] == "ADMISSION":
            declarant_id = source_meta.get("actor_id")
            fact_actor_id = facts[fact_id].get("actor_id")
            if not declarant_id or str(declarant_id) == str(fact_actor_id):
                raise ValueError("self-serving PARTY_SUBMISSION não pode ser promovida a ADMISSION")

        source_text = " ".join(str(page.get("content") or "") for page in source_meta.get("pages") or [])
        if relation == "SUPPORTS" and _IDENTITY_UNCLEAR_RE.search(source_text):
            relation = "INCONCLUSIVE"
            directness = "UNKNOWN"
            scope = "PARTIAL"
            limitations = [code for code in limitations if code != "AUTHENTICITY_DISPUTED"]
            if "IDENTITY_UNCLEAR" not in limitations:
                limitations.append("IDENTITY_UNCLEAR")

        refs = validate_source_refs(item["source_refs"], flat_source, field_name="link.source_refs")
        if any(page_to_source[(ref["document_id"], ref["pdf_page"])] != expected_source_id for ref in refs):
            raise ValueError("link.source_refs não pertencem à evidence source")
        key = (fact_id, keys[evidence_key], relation)
        if key in seen_links:
            raise ValueError("evidence link duplicado")
        seen_links.add(key)
        links.append({
            "fact_id": fact_id,
            "evidence_id": keys[evidence_key],
            "relation": relation,
            "directness": directness,
            "scope": scope,
            "limitations": limitations,
            "source_refs": refs,
        })

    unresolved_points: list[dict[str, Any]] = []
    has_ambiguous = False
    for item in value["unresolved_points"]:
        required = {"fact_id", "code", "reason", "source_refs"}
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError("unresolved_point divergente do schema")
        fact_id = item["fact_id"]
        if fact_id is not None:
            fact_id = str(fact_id).strip()
            if fact_id not in facts:
                raise ValueError("unresolved_point referencia fact_id inexistente")
        code = str(item["code"] or "").upper()
        reason = str(item["reason"] or "").strip()
        if code not in UNRESOLVED_CODES or not reason:
            raise ValueError("unresolved_point inválido")
        refs = validate_source_refs(item["source_refs"], flat_source, field_name="unresolved_point.source_refs")
        if code == "EVIDENCE_REFERENCE_AMBIGUOUS":
            has_ambiguous = True
        unresolved_points.append({
            "fact_id": fact_id,
            "code": code,
            "reason": reason,
            "source_refs": refs,
        })

    fact_states = [
        {"fact_id": fact_id, "evidence_state": _fact_state(fact_id, links)}
        for fact_id in facts
    ]
    sufficiency = "AMBIGUOUS" if has_ambiguous else ("INSUFFICIENT" if unresolved_points else "SUFFICIENT")
    return {
        "schema_version": SCHEMA_VERSION,
        "context_sufficiency": sufficiency,
        "evidence_items": evidence_items,
        "links": links,
        "fact_states": fact_states,
        "unresolved_points": unresolved_points,
    }


def score_evidence_mapping(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    exp_items = list(expected.get("evidence_items") or [])
    act_items = list(actual.get("evidence_items") or [])
    matched_items = 0
    unmatched = set(range(len(act_items)))
    item_map: dict[str, str] = {}
    for exp in exp_items:
        hit = next((
            i for i in unmatched
            if str(exp.get("kind") or "") == str(act_items[i].get("kind") or "")
            and str(exp.get("source_id") or "") == str(act_items[i].get("source_id") or "")
        ), None)
        if hit is not None:
            matched_items += 1
            unmatched.remove(hit)
            if exp.get("key"):
                item_map[str(exp["key"])] = str(act_items[hit].get("evidence_id") or "")

    item_precision = 1.0 if not act_items else matched_items / len(act_items)
    item_recall = 1.0 if not exp_items else matched_items / len(exp_items)

    exp_links = list(expected.get("links") or [])
    act_links = list(actual.get("links") or [])
    matched_links = 0
    unmatched_links = set(range(len(act_links)))
    for exp in exp_links:
        expected_evidence_id = item_map.get(str(exp.get("evidence_key") or ""))
        hit = next((
            i for i in unmatched_links
            if str(exp.get("fact_id") or "") == str(act_links[i].get("fact_id") or "")
            and str(exp.get("relation") or "") == str(act_links[i].get("relation") or "")
            and str(exp.get("directness") or "") == str(act_links[i].get("directness") or "")
            and str(exp.get("scope") or "") == str(act_links[i].get("scope") or "")
            and (not expected_evidence_id or expected_evidence_id == act_links[i].get("evidence_id"))
        ), None)
        if hit is not None:
            matched_links += 1
            unmatched_links.remove(hit)

    link_precision = 1.0 if not act_links else matched_links / len(act_links)
    link_recall = 1.0 if not exp_links else matched_links / len(exp_links)

    expected_support = {
        str(item.get("fact_id"))
        for item in exp_links
        if item.get("relation") == "SUPPORTS"
    }
    dangerous_support_invention = any(
        item.get("relation") == "SUPPORTS"
        and str(item.get("fact_id")) not in expected_support
        for item in act_links
    )
    expected_states = {
        str(item.get("fact_id")): str(item.get("evidence_state"))
        for item in expected.get("fact_states") or []
    }
    actual_states = {
        str(item.get("fact_id")): str(item.get("evidence_state"))
        for item in actual.get("fact_states") or []
    }
    state_accuracy = (
        1.0 if not expected_states
        else sum(actual_states.get(fid) == state for fid, state in expected_states.items()) / len(expected_states)
    )
    return {
        "evidence_item_precision": item_precision,
        "evidence_item_recall": item_recall,
        "evidence_link_precision": link_precision,
        "evidence_link_recall": link_recall,
        "fact_state_accuracy": state_accuracy,
        "sufficiency_match": expected.get("context_sufficiency") == actual.get("context_sufficiency"),
        "dangerous_support_invention": dangerous_support_invention,
    }
