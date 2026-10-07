"""Precedent / Ratio Analyzer V1.

Semantically classifies retrieved precedent candidates against neutral legal
issues and extractively anchors the identified ratio/holding to provider text.
IDs, issue/candidate links, provenance, sufficiency and unresolved states are
derived deterministically by Themis.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from core.legal_skills.source_contract_v1 import normalize_text

SCHEMA_VERSION = "precedent-ratio-analyzer-v1"

APPLICABILITY = ("DIRECT", "ANALOGOUS", "DISTINGUISHABLE", "UNCLEAR")

PRECEDENT_RATIO_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "analyses": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "issue_id": {"type": "string", "minLength": 1},
                    "candidate_id": {"type": "string", "minLength": 1},
                    "applicability": {"type": "string", "enum": list(APPLICABILITY)},
                    "ratio_quote": {
                        "anyOf": [
                            {"type": "string", "minLength": 1},
                            {"type": "null"},
                        ]
                    },
                    "fact_ids": {
                        "type": "array",
                        "uniqueItems": True,
                        "items": {"type": "string", "minLength": 1},
                    },
                },
                "required": [
                    "issue_id",
                    "candidate_id",
                    "applicability",
                    "ratio_quote",
                    "fact_ids",
                ],
            },
        },
    },
    "required": ["analyses"],
}


def build_precedent_ratio_instructions() -> str:
    return """TASK: PRECEDENT_RATIO_ANALYZE

INPUT:
- items[] = exact issue/candidate pairs to analyze.
- issue.question is neutral.
- issue.facts[] are only the current-case facts linked to that issue.
- candidate.excerpts[] are the only precedent text you may use.

YOU DO ONLY TWO SEMANTIC THINGS:
1. classify applicability: DIRECT / ANALOGOUS / DISTINGUISHABLE / UNCLEAR;
2. copy one exact ratio/holding quote from candidate.excerpts[] when identifiable.

CLASSIFICATION:
- DIRECT = excerpt directly states a rule/holding addressing the same legal question in materially matching context.
- ANALOGOUS = excerpt states a relevant rule/holding, but application is by analogy rather than direct identity.
- DISTINGUISHABLE = excerpt is facially relevant, but a material factual/procedural/legal difference limits direct application.
- UNCLEAR = excerpt is insufficient to identify the ratio/holding or applicability safely.

HARD RULES:
1. Output exactly one analysis for every input item and no others.
2. Use only issue_id, candidate_id and fact_ids supplied in that item.
3. ratio_quote must be copied verbatim from one supplied excerpt. Never paraphrase it.
4. DIRECT / ANALOGOUS / DISTINGUISHABLE require ratio_quote. UNCLEAR requires ratio_quote=null.
5. Before choosing UNCLEAR, inspect any explicit condition in the ratio (for example: when/if/desde que/only if). Compare that condition with every supplied current-case fact. If a fact expressly states the condition is absent or opposite, classify DISTINGUISHABLE and include that fact_id.
6. fact_ids contains only current-case facts materially used for fit/distinction; it may be empty.
7. Do not invent facts, holdings, statutes, cases or authorities.
8. Do not label a precedent favorable/adverse and do not decide merits, strategy or persuasive weight.
9. If the excerpt does not safely support the classification after that check, use UNCLEAR.

OUTPUT: schema only."""


def _flatten_facts(fact_outputs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    facts: dict[str, dict[str, Any]] = {}
    for output in fact_outputs or []:
        if not isinstance(output, dict) or not isinstance(output.get("facts"), list):
            raise ValueError("fact_output inválido")
        for item in output["facts"]:
            fact_id = str(item.get("fact_id") or "").strip()
            statement = str(item.get("statement") or "").strip()
            if not fact_id or not statement or fact_id in facts:
                raise ValueError("fact inválido/duplicado")
            facts[fact_id] = {
                "fact_id": fact_id,
                "statement": statement,
            }
    return facts


def _flatten_issues(
    issue_outputs: list[dict[str, Any]],
    facts: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    issues: dict[str, dict[str, Any]] = {}
    for output in issue_outputs or []:
        if not isinstance(output, dict) or not isinstance(output.get("issues"), list):
            raise ValueError("issue_output inválido")
        for item in output["issues"]:
            issue_id = str(item.get("issue_id") or "").strip()
            question = str(item.get("question") or "").strip()
            fact_ids = sorted({str(x) for x in item.get("fact_ids") or []})
            if not issue_id or not question or issue_id in issues:
                raise ValueError("issue inválida/duplicada")
            if any(fact_id not in facts for fact_id in fact_ids):
                raise ValueError("issue referencia fact inexistente")
            issues[issue_id] = {
                "issue_id": issue_id,
                "question": question,
                "kind": str(item.get("kind") or "").strip().upper(),
                "fact_ids": fact_ids,
            }
    return issues


def _query_issue_map(research_outputs: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for output in research_outputs or []:
        if not isinstance(output, dict) or not isinstance(output.get("queries"), list):
            raise ValueError("research_output inválido")
        for item in output["queries"]:
            query_id = str(item.get("query_id") or "").strip()
            issue_id = str(item.get("issue_id") or "").strip()
            if not query_id or not issue_id:
                raise ValueError("research query inválida")
            if query_id in mapping and mapping[query_id] != issue_id:
                raise ValueError("query_id mapeia múltiplas issues")
            mapping[query_id] = issue_id
    return mapping


def build_precedent_ratio_input(
    issue_outputs: list[dict[str, Any]],
    fact_outputs: list[dict[str, Any]],
    research_outputs: list[dict[str, Any]],
    jurisprudence_outputs: list[dict[str, Any]],
) -> dict[str, Any]:
    facts = _flatten_facts(fact_outputs)
    issues = _flatten_issues(issue_outputs, facts)
    query_to_issue = _query_issue_map(research_outputs)

    candidates: dict[str, dict[str, Any]] = {}
    upstream_unresolved: list[dict[str, Any]] = []

    for output in jurisprudence_outputs or []:
        if not isinstance(output, dict) or not isinstance(output.get("candidates"), list):
            raise ValueError("jurisprudence_output inválido")
        for unresolved in output.get("unresolved_points") or []:
            if isinstance(unresolved, dict):
                upstream_unresolved.append(dict(unresolved))

        for candidate in output["candidates"]:
            if not isinstance(candidate, dict):
                raise ValueError("precedent candidate inválido")
            candidate_id = str(candidate.get("candidate_id") or "").strip()
            court = str(candidate.get("court") or "").strip()
            identifier = str(candidate.get("identifier") or "").strip()
            query_ids = sorted({str(x) for x in candidate.get("query_ids") or [] if str(x).strip()})
            hits = candidate.get("retrieval_hits")
            if (
                not candidate_id
                or candidate_id in candidates
                or not court
                or not identifier
                or not query_ids
                or not isinstance(hits, list)
                or not hits
            ):
                raise ValueError("precedent candidate incompleto/duplicado")
            if any(query_id not in query_to_issue for query_id in query_ids):
                raise ValueError("candidate referencia query inexistente")

            norm_hits: list[dict[str, Any]] = []
            for hit in hits:
                if not isinstance(hit, dict):
                    raise ValueError("retrieval_hit inválido")
                query_id = str(hit.get("query_id") or "").strip()
                excerpt = str(hit.get("excerpt") or "").strip()
                provenance = hit.get("provenance")
                if (
                    query_id not in query_ids
                    or not excerpt
                    or not isinstance(provenance, dict)
                    or not all(str(provenance.get(k) or "").strip() for k in (
                        "provider", "provider_result_id", "retrieved_at", "content_sha256"
                    ))
                ):
                    raise ValueError("retrieval_hit sem provenance conferível")
                norm_hits.append({
                    "query_id": query_id,
                    "excerpt": excerpt,
                    "source_url": str(hit.get("source_url") or "").strip() or None,
                    "document_ref": str(hit.get("document_ref") or "").strip() or None,
                    "provenance": {
                        "provider": str(provenance["provider"]).strip(),
                        "provider_result_id": str(provenance["provider_result_id"]).strip(),
                        "retrieved_at": str(provenance["retrieved_at"]).strip(),
                        "content_sha256": str(provenance["content_sha256"]).strip(),
                    },
                })

            candidates[candidate_id] = {
                "candidate_id": candidate_id,
                "court": court,
                "identifier": identifier,
                "query_ids": query_ids,
                "retrieval_hits": norm_hits,
            }

    items: list[dict[str, Any]] = []
    required_pairs: list[dict[str, str]] = []
    pair_excerpts: dict[str, list[dict[str, Any]]] = {}

    for candidate_id in sorted(candidates):
        candidate = candidates[candidate_id]
        issue_ids = sorted({query_to_issue[qid] for qid in candidate["query_ids"]})
        for issue_id in issue_ids:
            issue = issues.get(issue_id)
            if issue is None:
                raise ValueError("candidate referencia issue inexistente")
            issue_query_ids = {
                qid for qid in candidate["query_ids"]
                if query_to_issue[qid] == issue_id
            }
            excerpts = [
                hit for hit in candidate["retrieval_hits"]
                if hit["query_id"] in issue_query_ids
            ]
            if not excerpts:
                raise ValueError("candidate sem excerpt para issue vinculada")
            pair_key = issue_id + "\0" + candidate_id
            pair_excerpts[pair_key] = excerpts
            required_pairs.append({
                "issue_id": issue_id,
                "candidate_id": candidate_id,
            })
            items.append({
                "issue": {
                    "issue_id": issue_id,
                    "question": issue["question"],
                    "kind": issue["kind"],
                    "facts": [facts[fid] for fid in issue["fact_ids"]],
                },
                "candidate": {
                    "candidate_id": candidate_id,
                    "court": candidate["court"],
                    "identifier": candidate["identifier"],
                    "excerpts": [
                        {
                            "query_id": hit["query_id"],
                            "excerpt": hit["excerpt"],
                        }
                        for hit in excerpts
                    ],
                },
            })

    return {
        "items": items,
        "required_pairs": required_pairs,
        "issues": issues,
        "candidates": candidates,
        "pair_excerpts": pair_excerpts,
        "upstream_unresolved": upstream_unresolved,
    }


def build_precedent_ratio_llm_input(skill_input: dict[str, Any]) -> dict[str, Any]:
    return {"items": list(skill_input.get("items") or [])}


def _stable_analysis_id(issue_id: str, candidate_id: str) -> str:
    raw = "\0".join((issue_id, candidate_id))
    return "precedent_analysis_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _matching_hit(
    ratio_quote: str,
    hits: list[dict[str, Any]],
) -> dict[str, Any] | None:
    needle = normalize_text(ratio_quote)
    if not needle:
        return None
    for hit in hits:
        if needle in normalize_text(hit["excerpt"]):
            return hit
    return None


def validate_precedent_ratio(
    value: Any,
    skill_input: dict[str, Any],
) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Precedent Ratio output não é JSON válido") from exc
    if not isinstance(value, dict) or set(value) != {"analyses"} or not isinstance(value["analyses"], list):
        raise ValueError("Precedent Ratio output divergente do schema")

    required = {
        (str(item["issue_id"]), str(item["candidate_id"]))
        for item in skill_input.get("required_pairs") or []
    }
    issues = skill_input.get("issues") or {}
    candidates = skill_input.get("candidates") or {}
    pair_excerpts = skill_input.get("pair_excerpts") or {}

    analyses: list[dict[str, Any]] = []
    unresolved_points: list[dict[str, Any]] = [
        {
            "code": "UPSTREAM_JURISPRUDENCE_INSUFFICIENT",
            "query_id": str(item.get("query_id") or ""),
        }
        for item in skill_input.get("upstream_unresolved") or []
    ]
    seen: set[tuple[str, str]] = set()

    for item in value["analyses"]:
        if not isinstance(item, dict) or set(item) != {
            "issue_id", "candidate_id", "applicability", "ratio_quote", "fact_ids"
        }:
            raise ValueError("precedent analysis divergente do schema")
        issue_id = str(item.get("issue_id") or "").strip()
        candidate_id = str(item.get("candidate_id") or "").strip()
        applicability = str(item.get("applicability") or "").strip().upper()
        ratio_quote = item.get("ratio_quote")
        fact_ids = sorted({str(x) for x in item.get("fact_ids") or []})
        pair = (issue_id, candidate_id)

        if pair not in required:
            raise ValueError("precedent analysis não solicitada")
        if pair in seen:
            raise ValueError("precedent analysis duplicada")
        if applicability not in APPLICABILITY:
            raise ValueError("applicability inválida")
        issue = issues[issue_id]
        if any(fact_id not in issue["fact_ids"] for fact_id in fact_ids):
            raise ValueError("precedent analysis referencia fact fora da issue")

        pair_key = issue_id + "\0" + candidate_id
        hits = pair_excerpts[pair_key]
        source_ref = None

        if applicability == "UNCLEAR":
            if ratio_quote not in (None, ""):
                raise ValueError("UNCLEAR exige ratio_quote nulo")
            ratio_quote = None
            fact_ids = []
        else:
            if not isinstance(ratio_quote, str) or not ratio_quote.strip():
                raise ValueError("applicability exige ratio_quote")
            ratio_quote = ratio_quote.strip()
            hit = _matching_hit(ratio_quote, hits)
            if hit is None:
                raise ValueError("ratio_quote sem provenance conferível")
            source_ref = {
                "provider": hit["provenance"]["provider"],
                "provider_result_id": hit["provenance"]["provider_result_id"],
                "retrieved_at": hit["provenance"]["retrieved_at"],
                "content_sha256": hit["provenance"]["content_sha256"],
                "source_url": hit["source_url"],
                "document_ref": hit["document_ref"],
                "quote": ratio_quote,
            }

        seen.add(pair)
        candidate = candidates[candidate_id]
        analyses.append({
            "analysis_id": _stable_analysis_id(issue_id, candidate_id),
            "issue_id": issue_id,
            "candidate_id": candidate_id,
            "court": candidate["court"],
            "identifier": candidate["identifier"],
            "applicability": applicability,
            "ratio_quote": ratio_quote,
            "fact_ids": fact_ids,
            "source_ref": source_ref,
        })
        if applicability == "UNCLEAR":
            unresolved_points.append({
                "issue_id": issue_id,
                "candidate_id": candidate_id,
                "code": "PRECEDENT_APPLICABILITY_UNCLEAR",
            })

    missing = sorted(required - seen)
    for issue_id, candidate_id in missing:
        unresolved_points.append({
            "issue_id": issue_id,
            "candidate_id": candidate_id,
            "code": "PRECEDENT_ANALYSIS_MISSING",
        })

    analyses.sort(key=lambda x: (x["issue_id"], x["candidate_id"]))
    unresolved_points.sort(key=lambda x: (
        str(x.get("issue_id") or ""),
        str(x.get("candidate_id") or ""),
        str(x.get("query_id") or ""),
        str(x.get("code") or ""),
    ))
    return {
        "schema_version": SCHEMA_VERSION,
        "context_sufficiency": "INSUFFICIENT" if unresolved_points else "SUFFICIENT",
        "analyses": analyses,
        "unresolved_points": unresolved_points,
    }


def score_precedent_ratio(
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:
    exp = {
        (str(x.get("issue_id")), str(x.get("candidate_id"))): x
        for x in expected.get("analyses") or []
    }
    act = {
        (str(x.get("issue_id")), str(x.get("candidate_id"))): x
        for x in actual.get("analyses") or []
    }
    matched_pairs = set(exp) & set(act)
    precision = 1.0 if not act else len(matched_pairs) / len(act)
    recall = 1.0 if not exp else len(matched_pairs) / len(exp)

    applicability_mismatches = 0
    ratio_mismatches = 0
    fact_link_mismatches = 0
    for pair in matched_pairs:
        e = exp[pair]
        a = act[pair]
        if str(e.get("applicability")) != str(a.get("applicability")):
            applicability_mismatches += 1
        expected_quote = normalize_text(str(e.get("ratio_quote") or ""))
        actual_quote = normalize_text(str(a.get("ratio_quote") or ""))
        if expected_quote != actual_quote:
            ratio_mismatches += 1
        if set(e.get("fact_ids") or []) != set(a.get("fact_ids") or []):
            fact_link_mismatches += 1

    dangerous_unprovenanced_ratio = any(
        item.get("applicability") != "UNCLEAR"
        and (
            not isinstance(item.get("source_ref"), dict)
            or normalize_text(str(item.get("ratio_quote") or ""))
            not in normalize_text(str(item.get("source_ref", {}).get("quote") or ""))
        )
        for item in actual.get("analyses") or []
    )
    return {
        "analysis_precision": precision,
        "analysis_recall": recall,
        "applicability_mismatch_count": applicability_mismatches,
        "ratio_mismatch_count": ratio_mismatches,
        "fact_link_mismatch_count": fact_link_mismatches,
        "sufficiency_match": expected.get("context_sufficiency") == actual.get("context_sufficiency"),
        "dangerous_unprovenanced_ratio": dangerous_unprovenanced_ratio,
    }
