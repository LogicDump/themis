"""Jurisprudence Retriever V1.

Provider-neutral deterministic projection from Legal Research Planner queries and
normalized provider responses into provenance-valid precedent candidates.

This layer retrieves and normalizes candidates only. It does not decide ratio,
adherence, distinguishing, persuasive force, or merits.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime
from typing import Any

from core.legal_skills.source_contract_v1 import normalize_text

SCHEMA_VERSION = "jurisprudence-retriever-v1"

JUDICIAL_SOURCE_TYPES = ("BINDING_AUTHORITY", "JURISPRUDENCE")
PROVIDER_STATUSES = ("OK", "FAILED")
QUERY_STATUSES = ("FOUND", "NO_RESULTS", "FAILED", "INVALID_RESULTS", "NOT_ATTEMPTED")
DATE_KINDS = ("JUDGMENT", "PUBLICATION", "UNKNOWN")

_RESULT_FIELDS = {
    "provider_result_id",
    "source_type",
    "court",
    "judging_body",
    "identifier",
    "date",
    "date_kind",
    "excerpt",
    "source_url",
    "document_ref",
    "rank",
    "score",
}

_RESPONSE_FIELDS = {
    "query_id",
    "provider",
    "status",
    "retrieved_at",
    "results",
    "error_code",
}


def _stable_candidate_id(court: str, identifier: str) -> str:
    raw = "\0".join((normalize_text(court), normalize_text(identifier)))
    return "precedent_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _valid_date(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        date.fromisoformat(text)
    except ValueError:
        return None
    return text


def _valid_datetime(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return text


def build_jurisprudence_input(research_outputs: list[dict[str, Any]]) -> dict[str, Any]:
    """Select only judicial-source queries from validated research plans."""
    queries: list[dict[str, Any]] = []
    seen: set[str] = set()

    for output in research_outputs or []:
        if not isinstance(output, dict) or not isinstance(output.get("queries"), list):
            raise ValueError("research_output inválido")
        for item in output["queries"]:
            if not isinstance(item, dict):
                raise ValueError("research query inválida")
            query_id = str(item.get("query_id") or "").strip()
            issue_id = str(item.get("issue_id") or "").strip()
            objective = str(item.get("objective") or "").strip()
            query_text = str(item.get("query_text") or "").strip()
            jurisdiction = str(item.get("jurisdiction") or "").strip()
            source_types = item.get("source_types")
            if (
                not query_id
                or not issue_id
                or not objective
                or not query_text
                or not jurisdiction
                or not isinstance(source_types, list)
            ):
                raise ValueError("research query incompleta")
            if query_id in seen:
                raise ValueError("query_id duplicado")
            seen.add(query_id)

            allowed = sorted({
                str(source_type).strip().upper()
                for source_type in source_types
                if str(source_type).strip().upper() in JUDICIAL_SOURCE_TYPES
            })
            if not allowed:
                continue

            queries.append({
                "query_id": query_id,
                "issue_id": issue_id,
                "objective": objective,
                "query_text": query_text,
                "allowed_source_types": allowed,
                "jurisdiction": jurisdiction,
                "court_context": str(item.get("court_context") or "").strip() or None,
            })

    queries.sort(key=lambda x: x["query_id"])
    return {"queries": queries}


def _result_rejection_code(
    item: Any,
    allowed_source_types: set[str],
) -> str | None:
    if not isinstance(item, dict):
        return "RESULT_NOT_OBJECT"
    if set(item) != _RESULT_FIELDS:
        return "RESULT_SCHEMA_INVALID"

    provider_result_id = str(item.get("provider_result_id") or "").strip()
    source_type = str(item.get("source_type") or "").strip().upper()
    court = str(item.get("court") or "").strip()
    judging_body = item.get("judging_body")
    identifier = str(item.get("identifier") or "").strip()
    result_date = _valid_date(item.get("date"))
    date_kind = str(item.get("date_kind") or "").strip().upper()
    excerpt = str(item.get("excerpt") or "").strip()
    source_url = item.get("source_url")
    document_ref = item.get("document_ref")
    rank = item.get("rank")
    score = item.get("score")

    if not provider_result_id:
        return "PROVIDER_RESULT_ID_MISSING"
    if source_type not in allowed_source_types:
        return "SOURCE_TYPE_NOT_ALLOWED"
    if not court:
        return "COURT_MISSING"
    if judging_body is not None and not str(judging_body).strip():
        return "JUDGING_BODY_INVALID"
    if not identifier:
        return "IDENTIFIER_MISSING"
    if result_date is None:
        return "DATE_INVALID"
    if date_kind not in DATE_KINDS:
        return "DATE_KIND_INVALID"
    if not excerpt:
        return "EXCERPT_MISSING"

    if source_url is not None and not str(source_url).strip():
        return "SOURCE_URL_INVALID"
    if document_ref is not None and not str(document_ref).strip():
        return "DOCUMENT_REF_INVALID"
    if not (str(source_url or "").strip() or str(document_ref or "").strip()):
        return "LOCATOR_MISSING"

    if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
        return "RANK_INVALID"
    if score is not None and (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not math.isfinite(float(score))
    ):
        return "SCORE_INVALID"
    return None


def _normalize_hit(
    item: dict[str, Any],
    *,
    query_id: str,
    provider: str,
    retrieved_at: str,
) -> dict[str, Any]:
    payload = {
        "source_type": str(item["source_type"]).strip().upper(),
        "court": str(item["court"]).strip(),
        "judging_body": str(item["judging_body"]).strip() if item["judging_body"] is not None else None,
        "identifier": str(item["identifier"]).strip(),
        "date": str(item["date"]).strip(),
        "date_kind": str(item["date_kind"]).strip().upper(),
        "excerpt": str(item["excerpt"]).strip(),
        "source_url": str(item["source_url"]).strip() if item["source_url"] is not None else None,
        "document_ref": str(item["document_ref"]).strip() if item["document_ref"] is not None else None,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "query_id": query_id,
        **payload,
        "provider_rank": int(item["rank"]),
        "provider_score": float(item["score"]) if item["score"] is not None else None,
        "provenance": {
            "provider": provider,
            "provider_result_id": str(item["provider_result_id"]).strip(),
            "retrieved_at": retrieved_at,
            "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        },
    }


def _hit_sort_key(hit: dict[str, Any]) -> tuple[Any, ...]:
    provenance = hit["provenance"]
    return (
        normalize_text(hit["court"]),
        normalize_text(hit["identifier"]),
        int(hit["provider_rank"]),
        normalize_text(provenance["provider"]),
        normalize_text(provenance["provider_result_id"]),
        hit["query_id"],
    )


def retrieve_jurisprudence(
    skill_input: dict[str, Any],
    provider_responses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate provider responses, fail closed, and deduplicate precedents."""
    if not isinstance(skill_input, dict) or not isinstance(skill_input.get("queries"), list):
        raise ValueError("jurisprudence input inválido")

    queries = {str(q["query_id"]): q for q in skill_input["queries"]}
    if len(queries) != len(skill_input["queries"]):
        raise ValueError("query_id duplicado no jurisprudence input")

    seen_responses: set[tuple[str, str]] = set()
    attempted: dict[str, set[str]] = {qid: set() for qid in queries}
    failed: dict[str, set[str]] = {qid: set() for qid in queries}
    valid_hits: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    provider_failures: list[dict[str, Any]] = []

    for response in provider_responses or []:
        if not isinstance(response, dict) or set(response) != _RESPONSE_FIELDS:
            raise ValueError("provider response divergente do schema")

        query_id = str(response.get("query_id") or "").strip()
        provider = str(response.get("provider") or "").strip()
        status = str(response.get("status") or "").strip().upper()
        retrieved_at = _valid_datetime(response.get("retrieved_at"))
        results = response.get("results")
        error_code = response.get("error_code")

        if query_id not in queries:
            raise ValueError("provider response referencia query inexistente")
        if not provider:
            raise ValueError("provider obrigatório")
        if status not in PROVIDER_STATUSES:
            raise ValueError("provider status inválido")
        if retrieved_at is None:
            raise ValueError("retrieved_at inválido")
        if not isinstance(results, list):
            raise ValueError("provider results deve ser lista")

        response_key = (query_id, normalize_text(provider))
        if response_key in seen_responses:
            raise ValueError("provider response duplicada para query")
        seen_responses.add(response_key)
        attempted[query_id].add(provider)

        if status == "FAILED":
            code = str(error_code or "").strip()
            if results or not code:
                raise ValueError("provider FAILED exige error_code e results vazio")
            failed[query_id].add(provider)
            provider_failures.append({
                "query_id": query_id,
                "provider": provider,
                "error_code": code,
            })
            continue

        if error_code not in (None, ""):
            raise ValueError("provider OK não aceita error_code")

        allowed = set(queries[query_id]["allowed_source_types"])
        for item in results:
            code = _result_rejection_code(item, allowed)
            provider_result_id = (
                str(item.get("provider_result_id") or "").strip()
                if isinstance(item, dict)
                else None
            )
            if code:
                rejections.append({
                    "query_id": query_id,
                    "provider": provider,
                    "provider_result_id": provider_result_id or None,
                    "code": code,
                })
                continue
            valid_hits.append(_normalize_hit(
                item,
                query_id=query_id,
                provider=provider,
                retrieved_at=retrieved_at,
            ))

    valid_hits.sort(key=_hit_sort_key)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for hit in valid_hits:
        key = (normalize_text(hit["court"]), normalize_text(hit["identifier"]))
        grouped.setdefault(key, []).append(hit)

    candidates: list[dict[str, Any]] = []
    candidate_ids_by_query: dict[str, set[str]] = {qid: set() for qid in queries}
    for key in sorted(grouped):
        hits = grouped[key]
        first = hits[0]
        candidate_id = _stable_candidate_id(first["court"], first["identifier"])
        query_ids = sorted({hit["query_id"] for hit in hits})
        source_types = sorted({hit["source_type"] for hit in hits})
        for query_id in query_ids:
            candidate_ids_by_query[query_id].add(candidate_id)
        candidates.append({
            "candidate_id": candidate_id,
            "court": first["court"],
            "identifier": first["identifier"],
            "query_ids": query_ids,
            "source_types": source_types,
            "retrieval_hits": hits,
        })

    rejections.sort(key=lambda x: (
        x["query_id"],
        normalize_text(x["provider"]),
        normalize_text(x.get("provider_result_id") or ""),
        x["code"],
    ))
    provider_failures.sort(key=lambda x: (
        x["query_id"],
        normalize_text(x["provider"]),
        x["error_code"],
    ))

    rejection_count_by_query = {qid: 0 for qid in queries}
    for item in rejections:
        rejection_count_by_query[item["query_id"]] += 1

    query_results: list[dict[str, Any]] = []
    unresolved_points: list[dict[str, Any]] = []
    for query_id in sorted(queries):
        candidate_ids = sorted(candidate_ids_by_query[query_id])
        attempted_providers = sorted(attempted[query_id], key=normalize_text)
        failed_providers = sorted(failed[query_id], key=normalize_text)
        rejected_count = rejection_count_by_query[query_id]

        if candidate_ids:
            status = "FOUND"
        elif not attempted_providers:
            status = "NOT_ATTEMPTED"
        elif len(failed_providers) == len(attempted_providers):
            status = "FAILED"
        elif rejected_count:
            status = "INVALID_RESULTS"
        else:
            status = "NO_RESULTS"

        query_results.append({
            "query_id": query_id,
            "status": status,
            "candidate_ids": candidate_ids,
            "providers_attempted": attempted_providers,
            "providers_failed": failed_providers,
            "rejected_count": rejected_count,
        })
        if status != "FOUND":
            unresolved_points.append({
                "query_id": query_id,
                "code": f"JURISPRUDENCE_{status}",
            })

    context_sufficiency = (
        "SUFFICIENT"
        if all(item["status"] == "FOUND" for item in query_results)
        else "INSUFFICIENT"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "context_sufficiency": context_sufficiency,
        "query_results": query_results,
        "candidates": candidates,
        "provider_failures": provider_failures,
        "rejected_results": rejections,
        "unresolved_points": unresolved_points,
    }


def _candidate_key_set(value: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (normalize_text(item.get("court")), normalize_text(item.get("identifier")))
        for item in value.get("candidates") or []
        if item.get("court") and item.get("identifier")
    }


def _expected_candidate_key_set(value: dict[str, Any]) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for item in value.get("candidates") or []:
        if isinstance(item, dict):
            court = item.get("court")
            identifier = item.get("identifier")
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            court, identifier = item
        else:
            continue
        if court and identifier:
            result.add((normalize_text(court), normalize_text(identifier)))
    return result


def _dangerous_unprovenanced_acceptance(actual: dict[str, Any]) -> bool:
    for candidate in actual.get("candidates") or []:
        for hit in candidate.get("retrieval_hits") or []:
            provenance = hit.get("provenance")
            if not isinstance(provenance, dict):
                return True
            if not all(str(provenance.get(key) or "").strip() for key in (
                "provider",
                "provider_result_id",
                "retrieved_at",
                "content_sha256",
            )):
                return True
            if not str(hit.get("excerpt") or "").strip():
                return True
            if not (
                str(hit.get("source_url") or "").strip()
                or str(hit.get("document_ref") or "").strip()
            ):
                return True
    return False


def score_jurisprudence_retrieval(
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:
    expected_candidates = _expected_candidate_key_set(expected)
    actual_candidates = _candidate_key_set(actual)
    matched = len(expected_candidates & actual_candidates)
    precision = 1.0 if not actual_candidates else matched / len(actual_candidates)
    recall = 1.0 if not expected_candidates else matched / len(expected_candidates)

    expected_statuses = {
        str(item.get("query_id")): str(item.get("status"))
        for item in expected.get("query_results") or []
    }
    actual_statuses = {
        str(item.get("query_id")): str(item.get("status"))
        for item in actual.get("query_results") or []
    }

    return {
        "candidate_precision": precision,
        "candidate_recall": recall,
        "query_status_match": expected_statuses == actual_statuses,
        "sufficiency_match": expected.get("context_sufficiency") == actual.get("context_sufficiency"),
        "rejection_count_match": (
            int(expected.get("rejection_count", 0))
            == len(actual.get("rejected_results") or [])
        ),
        "provider_failure_count_match": (
            int(expected.get("provider_failure_count", 0))
            == len(actual.get("provider_failures") or [])
        ),
        "dangerous_unprovenanced_acceptance": _dangerous_unprovenanced_acceptance(actual),
    }
