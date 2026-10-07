"""Legal Research Planner V1.

Turns validated legal issues into constrained research queries. Research
objectives and source scopes are deterministic; the LLM only formulates the
query text for each required objective.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from core.legal_skills.source_contract_v1 import normalize_text

SCHEMA_VERSION = "legal-research-planner-v1"

OBJECTIVES = (
    "CONTROLLING_RULE",
    "PROCEDURAL_RULE",
    "PRECEDENT_LANDSCAPE",
)

OBJECTIVE_SOURCE_TYPES = {
    "CONTROLLING_RULE": ["LEGISLATION", "BINDING_AUTHORITY"],
    "PROCEDURAL_RULE": ["LEGISLATION", "BINDING_AUTHORITY"],
    "PRECEDENT_LANDSCAPE": ["BINDING_AUTHORITY", "JURISPRUDENCE"],
}

_CITATION_PATTERNS = (
    re.compile(r"\bart\.?\s*\d+", re.IGNORECASE),
    re.compile(r"\bs[uú]mula\s*\d+", re.IGNORECASE),
    re.compile(r"\b(?:resp|re|are|hc|rhc|ms|agrg|agint)\s*\d+", re.IGNORECASE),
    re.compile(r"\btema\s*\d+", re.IGNORECASE),
)

RESEARCH_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "queries": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "issue_id": {"type": "string", "minLength": 1},
                    "objective": {"type": "string", "enum": list(OBJECTIVES)},
                    "query_text": {"type": "string", "minLength": 1},
                },
                "required": ["issue_id", "objective", "query_text"],
            },
        },
    },
    "required": ["queries"],
}


def required_objectives_for_issue(issue: dict[str, Any]) -> list[str]:
    kind = str(issue.get("kind") or "").upper()
    if kind in {"LEGAL", "MIXED"}:
        return ["CONTROLLING_RULE", "PRECEDENT_LANDSCAPE"]
    if kind == "PROCEDURAL":
        return ["PROCEDURAL_RULE", "PRECEDENT_LANDSCAPE"]
    return []


def build_research_instructions() -> str:
    return """TASK: LEGAL_RESEARCH_PLAN

INPUT:
- issues[] = validated issues.
- required_queries[] = exact issue_id/objective pairs that require query text.
- known_authorities[] = authorities already supplied upstream; only these may be named explicitly.

YOU DO ONLY ONE THING:
For every required_queries[] item, write one neutral search query in query_text.

RULES:
1. Output exactly one query for each required issue_id/objective pair.
2. Do not add or remove objectives.
3. Do not answer the issue.
4. Do not state what the law is.
5. Do not invent statute/article numbers, súmulas, temas, case numbers, precedent names or holdings.
6. A specific authority may appear only if already present verbatim in known_authorities[].
7. Query must be neutral: search the legal question/controversy, not a desired outcome.
8. PRECEDENT_LANDSCAPE must seek the jurisprudential treatment/criteria/limits of the issue, not a favorable case.
9. Keep query concise and suitable for a legal search engine.

OUTPUT:
- issue_id
- objective
- query_text
- schema only."""


def _validate_issue_output(output: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(output, dict) or not isinstance(output.get("issues"), list):
        raise ValueError("issue_output inválido")
    return output["issues"]


def build_research_input(
    process_id: str,
    issue_outputs: list[dict[str, Any]],
    burden_outputs: list[dict[str, Any]] | None = None,
    *,
    jurisdiction: str = "BR",
    court_context: str | None = None,
) -> dict[str, Any]:
    process_id = str(process_id or "").strip()
    if not process_id:
        raise ValueError("process_id obrigatório")

    issues: list[dict[str, Any]] = []
    issue_ids: set[str] = set()
    for output in issue_outputs or []:
        for item in _validate_issue_output(output):
            issue_id = str(item.get("issue_id") or "").strip()
            question = str(item.get("question") or "").strip()
            kind = str(item.get("kind") or "").strip().upper()
            if not issue_id or issue_id in issue_ids or not question:
                raise ValueError("issue inválida/duplicada")
            issue_ids.add(issue_id)
            issues.append({
                "issue_id": issue_id,
                "question": question,
                "kind": kind,
                "fact_ids": list(item.get("fact_ids") or []),
                "legal_position_ids": list(item.get("legal_position_ids") or []),
                "request_ids": list(item.get("request_ids") or []),
            })

    known_authorities: list[str] = []
    for output in burden_outputs or []:
        if not isinstance(output, dict):
            raise ValueError("burden_output inválido")
        for item in output.get("allocations") or []:
            issue_id = str(item.get("issue_id") or "")
            if issue_id not in issue_ids:
                raise ValueError("burden allocation referencia issue inexistente")
            authority = str(item.get("authority") or "").strip()
            if authority and authority not in known_authorities:
                known_authorities.append(authority)

    required_queries: list[dict[str, str]] = []
    for issue in issues:
        for objective in required_objectives_for_issue(issue):
            required_queries.append({
                "issue_id": issue["issue_id"],
                "objective": objective,
            })

    return {
        "process_id": process_id,
        "jurisdiction": str(jurisdiction or "").strip() or "BR",
        "court_context": str(court_context or "").strip() or None,
        "issues": issues,
        "required_queries": required_queries,
        "known_authorities": known_authorities,
    }


def build_research_llm_input(skill_input: dict[str, Any]) -> dict[str, Any]:
    return {
        "jurisdiction": skill_input["jurisdiction"],
        "court_context": skill_input.get("court_context"),
        "issues": [
            {
                "issue_id": x["issue_id"],
                "question": x["question"],
                "kind": x["kind"],
            }
            for x in skill_input.get("issues") or []
        ],
        "required_queries": list(skill_input.get("required_queries") or []),
        "known_authorities": list(skill_input.get("known_authorities") or []),
    }


def _stable_id(process_id: str, issue_id: str, objective: str) -> str:
    raw = "\0".join((process_id, issue_id, objective))
    return "research_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _contains_unsupplied_specific_authority(query: str, known_authorities: list[str]) -> bool:
    norm = normalize_text(query)
    known = [normalize_text(x) for x in known_authorities]
    for pattern in _CITATION_PATTERNS:
        for match in pattern.finditer(norm):
            token = match.group(0)
            if not any(token in authority for authority in known):
                return True
    return False


def validate_research_plan(value: Any, skill_input: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Research Planner output não é JSON válido") from exc
    if not isinstance(value, dict) or set(value) != {"queries"} or not isinstance(value["queries"], list):
        raise ValueError("Research Planner output divergente do schema")

    issues = {str(x["issue_id"]): x for x in skill_input.get("issues") or []}
    required = {
        (str(x["issue_id"]), str(x["objective"]))
        for x in skill_input.get("required_queries") or []
    }
    known_authorities = list(skill_input.get("known_authorities") or [])

    queries: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in value["queries"]:
        if not isinstance(item, dict) or set(item) != {"issue_id", "objective", "query_text"}:
            raise ValueError("research query divergente do schema")
        issue_id = str(item["issue_id"] or "").strip()
        objective = str(item["objective"] or "").strip().upper()
        query_text = str(item["query_text"] or "").strip()
        key = (issue_id, objective)
        if issue_id not in issues:
            raise ValueError("research query referencia issue inexistente")
        if key not in required:
            raise ValueError("research query não solicitada")
        if key in seen:
            raise ValueError("research query duplicada")
        if not query_text:
            raise ValueError("research query vazia")
        if _contains_unsupplied_specific_authority(query_text, known_authorities):
            raise ValueError("research query inventa autoridade específica")
        seen.add(key)
        queries.append({
            "query_id": _stable_id(skill_input["process_id"], issue_id, objective),
            "issue_id": issue_id,
            "objective": objective,
            "query_text": query_text,
            "source_types": list(OBJECTIVE_SOURCE_TYPES[objective]),
            "jurisdiction": skill_input["jurisdiction"],
            "court_context": skill_input.get("court_context"),
        })

    missing = sorted(required - seen)
    unresolved_points = [
        {
            "issue_id": issue_id,
            "objective": objective,
            "code": "RESEARCH_QUERY_MISSING",
        }
        for issue_id, objective in missing
    ]

    queries.sort(key=lambda x: (x["issue_id"], x["objective"]))
    sufficiency = "INSUFFICIENT" if unresolved_points else "SUFFICIENT"
    return {
        "schema_version": SCHEMA_VERSION,
        "context_sufficiency": sufficiency,
        "queries": queries,
        "unresolved_points": unresolved_points,
    }


def score_research_plan(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    def keys(value: dict[str, Any]) -> set[tuple[str, str]]:
        return {
            (str(x.get("issue_id") or ""), str(x.get("objective") or ""))
            for x in value.get("queries") or []
        }

    exp = keys(expected)
    act = keys(actual)
    matched = len(exp & act)
    precision = 1.0 if not act else matched / len(act)
    recall = 1.0 if not exp else matched / len(exp)

    dangerous_authority_invention = any(
        bool(_contains_unsupplied_specific_authority(
            str(x.get("query_text") or ""),
            list(expected.get("known_authorities") or []),
        ))
        for x in actual.get("queries") or []
    )
    return {
        "query_precision": precision,
        "query_recall": recall,
        "sufficiency_match": expected.get("context_sufficiency") == actual.get("context_sufficiency"),
        "dangerous_authority_invention": dangerous_authority_invention,
    }
