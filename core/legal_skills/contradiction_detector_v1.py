"""Contradiction Detector V1.

Detects material incompatibilities among already validated facts and projects
Evidence Mapper CONTRADICTS links without deciding truth or credibility.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from core.legal_skills.source_contract_v1 import normalize_text

SCHEMA_VERSION = "contradiction-detector-v1"

CONTRADICTION_STRENGTHS = ("DIRECT", "POTENTIAL")
_INDEFINITE_EVENT_RE = re.compile(
    r"\b(um|uma)\s+(pagamento|transfer[eê]ncia|dep[oó]sito|entrega|compra|venda|"
    r"liga[cç][aã]o|mensagem|reuni[aã]o|dep[oó]sito|saque)\b",
    re.IGNORECASE,
)
_NEGATION_RE = re.compile(r"\bn[aã]o\b", re.IGNORECASE)

CONTRADICTION_DIMENSIONS = (
    "IDENTITY",
    "ACTION_EVENT",
    "OBJECT",
    "AMOUNT",
    "DATE_TIME",
    "LOCATION",
    "EXISTENCE",
    "STATUS",
    "OTHER",
)

CONTRADICTION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "fact_pairs": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "left_fact_id": {"type": "string", "minLength": 1},
                    "right_fact_id": {"type": "string", "minLength": 1},
                    "strength": {"type": "string", "enum": list(CONTRADICTION_STRENGTHS)},
                    "dimensions": {
                        "type": "array",
                        "minItems": 1,
                        "uniqueItems": True,
                        "items": {"type": "string", "enum": list(CONTRADICTION_DIMENSIONS)},
                    },
                },
                "required": ["left_fact_id", "right_fact_id", "strength", "dimensions"],
            },
        },
    },
    "required": ["fact_pairs"],
}


def build_contradiction_instructions() -> str:
    return """TASK: CONTRADICTION_DETECT

INPUT:
- facts[] = already validated factual propositions.
- Evidence is intentionally absent from the LLM input; Themis projects Evidence Mapper contradictions deterministically.

FOR EACH possible Fact×Fact pair:

REFERENT GATE — before comparing values:
1. Establish whether both propositions concern the SAME material referent/event/state.
2. Same actor, same date, same amount or similar wording alone DOES NOT establish same event.
3. Indefinite events ("um pagamento", "uma transferência") may be different instances unless a transaction/object/event identifier makes them the same.
4. A state that can change over time (residence, possession, balance, employment, location) at different non-overlapping times -> NO PAIR.
5. A uniquely identified event/object (the same hearing, contract, vehicle at the same instant, identified transaction) may be compared across statements.
6. If same referent cannot be established but the propositions might target the same instance -> POTENTIAL, never DIRECT.

VALUE GATE — only after referent is established:
7. If both propositions can still be true simultaneously -> NO PAIR.
8. More specific/general but compatible -> NO PAIR.
9. Silence, incompleteness, unsupported status or absence of evidence -> NO PAIR.
10. Explicit mutually exclusive values for the same referent and temporal scope -> DIRECT.
11. dimensions = only dimensions that create the incompatibility.

MATERIAL DIMENSIONS:
IDENTITY, ACTION_EVENT, OBJECT, AMOUNT, DATE_TIME, LOCATION, EXISTENCE, STATUS, OTHER.

PRECEDENCE:
DIFFERENT_REFERENT_OR_NONOVERLAPPING_TIME -> NO PAIR
CAN_BOTH_BE_TRUE -> NO PAIR
REFERENT_NOT_ESTABLISHED_BUT_POSSIBLY_SAME -> POTENTIAL
SAME_REFERENT_AND_MUTUALLY_EXCLUSIVE -> DIRECT

NEVER:
- decide which fact is true;
- rank credibility or evidentiary weight;
- turn lack of support into contradiction;
- treat different epistemic_status values alone as contradiction;
- output evidence contradictions: Themis derives those deterministically from evidence_links.

OUTPUT: schema only."""


def _refs(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError("source_refs deve ser lista")
    out: list[dict[str, Any]] = []
    for ref in value:
        if not isinstance(ref, dict):
            raise ValueError("source_ref inválido")
        document_id = str(ref.get("document_id") or "").strip()
        pdf_page = ref.get("pdf_page")
        quote = str(ref.get("quote") or "").strip()
        if not document_id or isinstance(pdf_page, bool) or not isinstance(pdf_page, int) or pdf_page < 1 or not quote:
            raise ValueError("source_ref incompleto")
        out.append({"document_id": document_id, "pdf_page": pdf_page, "quote": quote})
    return out


def build_contradiction_input(
    process_id: str,
    fact_outputs: list[dict[str, Any]],
    evidence_outputs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    process_id = str(process_id or "").strip()
    if not process_id:
        raise ValueError("process_id obrigatório")
    if not isinstance(fact_outputs, list) or not fact_outputs:
        raise ValueError("fact_outputs deve ser lista não vazia")

    facts: list[dict[str, Any]] = []
    seen_facts: set[str] = set()
    for output in fact_outputs:
        if not isinstance(output, dict) or not isinstance(output.get("facts"), list):
            raise ValueError("fact_output inválido")
        for item in output["facts"]:
            if not isinstance(item, dict):
                raise ValueError("fact inválido")
            fact_id = str(item.get("fact_id") or "").strip()
            statement = str(item.get("statement") or "").strip()
            status = str(item.get("epistemic_status") or "").strip().upper()
            if not fact_id or fact_id in seen_facts or not statement or not status:
                raise ValueError("fact incompleto/duplicado")
            facts.append({
                "fact_id": fact_id,
                "statement": statement,
                "epistemic_status": status,
                "actor_id": item.get("actor_id"),
                "temporal_text": item.get("temporal_text"),
                "source_refs": _refs(item.get("source_refs") or []),
            })
            seen_facts.add(fact_id)

    evidence_items: list[dict[str, Any]] = []
    evidence_links: list[dict[str, Any]] = []
    seen_evidence: set[str] = set()
    for output in evidence_outputs or []:
        if not isinstance(output, dict):
            raise ValueError("evidence_output inválido")
        for item in output.get("evidence_items") or []:
            evidence_id = str(item.get("evidence_id") or "").strip()
            if not evidence_id or evidence_id in seen_evidence:
                raise ValueError("evidence_id ausente/duplicado")
            evidence_items.append({
                "evidence_id": evidence_id,
                "source_id": item.get("source_id"),
                "kind": item.get("kind"),
                "description": item.get("description"),
                "source_refs": _refs(item.get("source_refs") or []),
            })
            seen_evidence.add(evidence_id)
        for link in output.get("links") or []:
            fact_id = str(link.get("fact_id") or "").strip()
            evidence_id = str(link.get("evidence_id") or "").strip()
            relation = str(link.get("relation") or "").strip().upper()
            if fact_id not in seen_facts or not evidence_id or relation not in {"SUPPORTS", "CONTRADICTS", "INCONCLUSIVE"}:
                raise ValueError("evidence link inválido")
            evidence_links.append({
                "fact_id": fact_id,
                "evidence_id": evidence_id,
                "relation": relation,
                "directness": str(link.get("directness") or "").upper(),
                "scope": str(link.get("scope") or "").upper(),
                "limitations": list(link.get("limitations") or []),
                "source_refs": _refs(link.get("source_refs") or []),
            })

    return {
        "process_id": process_id,
        "facts": facts,
        "evidence_items": evidence_items,
        "evidence_links": evidence_links,
    }


def build_contradiction_llm_input(skill_input: dict[str, Any]) -> dict[str, Any]:
    """Return only semantic input needed by the LLM.

    Evidence contradictions are deterministic projections and are intentionally
    hidden from the model to prevent Fact×Evidence leakage into fact_pairs.
    """
    return {
        "process_id": str(skill_input.get("process_id") or ""),
        "facts": list(skill_input.get("facts") or []),
    }


def _stable_id(process_id: str, kind: str, left_id: str, right_id: str) -> str:
    a, b = sorted((str(left_id), str(right_id)))
    raw = "\0".join((process_id, kind, a, b))
    return "cd_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _dedupe_refs(refs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for ref in refs:
        key = (ref["document_id"], ref["pdf_page"], normalize_text(ref["quote"]))
        if key not in seen:
            seen.add(key)
            out.append(ref)
    return out


def _safety_gate_pair(
    left: dict[str, Any],
    right: dict[str, Any],
    strength: str,
    dimensions: list[str],
) -> tuple[str | None, list[str]]:
    left_statement = str(left.get("statement") or "")
    right_statement = str(right.get("statement") or "")

    if normalize_text(left_statement) == normalize_text(right_statement):
        return None, dimensions

    if strength != "DIRECT":
        return strength, dimensions

    left_indefinite = bool(_INDEFINITE_EVENT_RE.search(left_statement))
    right_indefinite = bool(_INDEFINITE_EVENT_RE.search(right_statement))
    if left_indefinite or right_indefinite:
        left_neg = bool(_NEGATION_RE.search(left_statement))
        right_neg = bool(_NEGATION_RE.search(right_statement))
        if left_neg != right_neg and any(d in {"ACTION_EVENT", "EXISTENCE"} for d in dimensions):
            return "POTENTIAL", dimensions
        return None, dimensions

    left_time = normalize_text(left.get("temporal_text") or "")
    right_time = normalize_text(right.get("temporal_text") or "")
    if left_time and right_time and left_time != right_time:
        if dimensions == ["DATE_TIME"]:
            return "DIRECT", dimensions
        if any(d in {"ACTION_EVENT", "EXISTENCE"} for d in dimensions):
            return "POTENTIAL", dimensions
        return None, dimensions

    return strength, dimensions


def validate_contradictions(value: Any, skill_input: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Contradiction Detector output não é JSON válido") from exc
    if not isinstance(value, dict) or set(value) != {"fact_pairs"} or not isinstance(value["fact_pairs"], list):
        raise ValueError("Contradiction Detector output divergente do schema")

    process_id = str(skill_input.get("process_id") or "").strip()
    facts = {str(item["fact_id"]): item for item in skill_input.get("facts") or []}
    evidence_items = {str(item["evidence_id"]): item for item in skill_input.get("evidence_items") or []}

    fact_contradictions: list[dict[str, Any]] = []
    unresolved_points: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()

    for item in value["fact_pairs"]:
        required = {"left_fact_id", "right_fact_id", "strength", "dimensions"}
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError("fact_pair divergente do schema")
        left_id = str(item["left_fact_id"] or "").strip()
        right_id = str(item["right_fact_id"] or "").strip()
        strength = str(item["strength"] or "").strip().upper()
        dimensions = [str(x).strip().upper() for x in item["dimensions"]] if isinstance(item["dimensions"], list) else []
        if left_id not in facts or right_id not in facts or left_id == right_id:
            raise ValueError("fact_pair referencia fact inválido")
        if strength not in CONTRADICTION_STRENGTHS:
            raise ValueError("strength inválido")
        if not dimensions or len(set(dimensions)) != len(dimensions) or any(x not in CONTRADICTION_DIMENSIONS for x in dimensions):
            raise ValueError("dimensions inválido")

        pair = tuple(sorted((left_id, right_id)))
        if pair in seen_pairs:
            raise ValueError("fact_pair duplicado")
        seen_pairs.add(pair)

        left = facts[pair[0]]
        right = facts[pair[1]]
        strength, dimensions = _safety_gate_pair(left, right, strength, dimensions)
        if strength is None:
            continue

        contradiction_id = _stable_id(process_id, "FACT_FACT", pair[0], pair[1])
        record = {
            "contradiction_id": contradiction_id,
            "kind": "FACT_FACT",
            "left_fact_id": pair[0],
            "right_fact_id": pair[1],
            "strength": strength,
            "dimensions": dimensions,
            "left_source_refs": left["source_refs"],
            "right_source_refs": right["source_refs"],
        }
        fact_contradictions.append(record)

        if strength == "POTENTIAL":
            unresolved_points.append({
                "code": "CONTRADICTION_REFERENT_AMBIGUOUS",
                "reason": "A incompatibilidade depende de identidade, tempo, transação ou referente ainda não resolvido.",
                "source_refs": _dedupe_refs(left["source_refs"] + right["source_refs"]),
            })

    evidence_contradictions: list[dict[str, Any]] = []
    by_fact_relations: dict[str, set[str]] = {}
    for link in skill_input.get("evidence_links") or []:
        fact_id = str(link["fact_id"])
        relation = str(link["relation"]).upper()
        by_fact_relations.setdefault(fact_id, set()).add(relation)
        if relation != "CONTRADICTS":
            continue
        evidence_id = str(link["evidence_id"])
        evidence = evidence_items.get(evidence_id)
        if evidence is None:
            raise ValueError("CONTRADICTS referencia evidence_id inexistente")
        fact = facts[fact_id]
        evidence_contradictions.append({
            "contradiction_id": _stable_id(process_id, "FACT_EVIDENCE", fact_id, evidence_id),
            "kind": "FACT_EVIDENCE",
            "fact_id": fact_id,
            "evidence_id": evidence_id,
            "strength": "DIRECT",
            "directness": link.get("directness"),
            "scope": link.get("scope"),
            "limitations": list(link.get("limitations") or []),
            "fact_source_refs": fact["source_refs"],
            "evidence_source_refs": _dedupe_refs(evidence["source_refs"] + list(link.get("source_refs") or [])),
        })

    mixed_evidence_fact_ids = sorted(
        fact_id
        for fact_id, relations in by_fact_relations.items()
        if "SUPPORTS" in relations and "CONTRADICTS" in relations
    )

    sufficiency = "AMBIGUOUS" if unresolved_points else "SUFFICIENT"
    return {
        "schema_version": SCHEMA_VERSION,
        "context_sufficiency": sufficiency,
        "fact_contradictions": fact_contradictions,
        "evidence_contradictions": evidence_contradictions,
        "mixed_evidence_fact_ids": mixed_evidence_fact_ids,
        "unresolved_points": unresolved_points,
    }


def score_contradictions(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    def pair_key(item: dict[str, Any]) -> tuple[str, str, str]:
        a, b = sorted((str(item.get("left_fact_id") or ""), str(item.get("right_fact_id") or "")))
        return (a, b, str(item.get("strength") or ""))

    expected_pairs = {pair_key(x) for x in expected.get("fact_contradictions") or []}
    actual_pairs = {pair_key(x) for x in actual.get("fact_contradictions") or []}
    matched = len(expected_pairs & actual_pairs)
    precision = 1.0 if not actual_pairs else matched / len(actual_pairs)
    recall = 1.0 if not expected_pairs else matched / len(expected_pairs)

    expected_direct = {
        (a, b)
        for a, b, strength in expected_pairs
        if strength == "DIRECT"
    }
    dangerous_direct = any(
        strength == "DIRECT" and (a, b) not in expected_direct
        for a, b, strength in actual_pairs
    )

    expected_evidence = {
        (str(x.get("fact_id")), str(x.get("evidence_id")))
        for x in expected.get("evidence_contradictions") or []
    }
    actual_evidence = {
        (str(x.get("fact_id")), str(x.get("evidence_id")))
        for x in actual.get("evidence_contradictions") or []
    }
    evidence_match = expected_evidence == actual_evidence

    return {
        "fact_pair_precision": precision,
        "fact_pair_recall": recall,
        "sufficiency_match": expected.get("context_sufficiency") == actual.get("context_sufficiency"),
        "dangerous_direct_invention": dangerous_direct,
        "evidence_projection_match": evidence_match,
        "mixed_evidence_match": sorted(expected.get("mixed_evidence_fact_ids") or []) == sorted(actual.get("mixed_evidence_fact_ids") or []),
    }
