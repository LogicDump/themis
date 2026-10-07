"""Evidence Gap Analyzer V1.

Deterministic coverage analysis over validated Facts, Evidence Mapper outputs,
and Contradiction Detector outputs. It does not decide legal materiality,
burden of proof, evidentiary sufficiency, or truth.
"""
from __future__ import annotations

import hashlib
from typing import Any

from core.legal_skills.contradiction_detector_v1 import build_contradiction_input
from core.legal_skills.source_contract_v1 import normalize_text

SCHEMA_VERSION = "evidence-gap-analyzer-v1"

SUPPORT_COVERAGE = ("NONE", "PARTIAL", "FULL", "SELF_DOCUMENTED")
GAP_CODES = (
    "NO_EVIDENCE_IN_CONTEXT",
    "NO_SUPPORT_IN_CONTEXT",
    "PARTIAL_SUPPORT",
    "INCONCLUSIVE_EVIDENCE",
    "CONFLICTING_EVIDENCE",
    "REFERENCED_EVIDENCE_NOT_AVAILABLE",
    "VISUAL_CONTENT_NOT_AVAILABLE",
    "AMBIGUOUS_EVIDENCE_REFERENCE",
    "UNRESOLVED_EVIDENCE",
    "FACTUAL_CONTRADICTION_UNRESOLVED",
)

_SELF_DOCUMENTED_STATUSES = {"JUDICIAL_FINDING", "DOCUMENTED_EVENT"}


def _stable_gap_id(process_id: str, fact_id: str) -> str:
    raw = "\0".join((process_id, fact_id))
    return "gap_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _dedupe_refs(refs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        document_id = str(ref.get("document_id") or "").strip()
        pdf_page = ref.get("pdf_page")
        quote = str(ref.get("quote") or "").strip()
        if not document_id or isinstance(pdf_page, bool) or not isinstance(pdf_page, int) or pdf_page < 1 or not quote:
            continue
        key = (document_id, pdf_page, normalize_text(quote))
        if key not in seen:
            seen.add(key)
            out.append({"document_id": document_id, "pdf_page": pdf_page, "quote": quote})
    return out


def _normalize_contradictions(
    fact_ids: set[str],
    contradiction_outputs: list[dict[str, Any]] | None,
) -> tuple[set[str], set[str], list[dict[str, Any]]]:
    fact_contradiction_ids: set[str] = set()
    mixed_fact_ids: set[str] = set()
    refs_by_fact: list[dict[str, Any]] = []

    for output in contradiction_outputs or []:
        if not isinstance(output, dict):
            raise ValueError("contradiction_output inválido")
        for item in output.get("fact_contradictions") or []:
            if not isinstance(item, dict):
                raise ValueError("fact_contradiction inválida")
            left = str(item.get("left_fact_id") or "").strip()
            right = str(item.get("right_fact_id") or "").strip()
            if left not in fact_ids or right not in fact_ids:
                raise ValueError("fact_contradiction referencia fact inexistente")
            contradiction_id = str(item.get("contradiction_id") or "").strip()
            if not contradiction_id:
                raise ValueError("fact_contradiction sem contradiction_id")
            fact_contradiction_ids.update((left, right))
            refs_by_fact.append({
                "fact_id": left,
                "source_refs": list(item.get("left_source_refs") or []),
            })
            refs_by_fact.append({
                "fact_id": right,
                "source_refs": list(item.get("right_source_refs") or []),
            })
        for fact_id in output.get("mixed_evidence_fact_ids") or []:
            fact_id = str(fact_id)
            if fact_id not in fact_ids:
                raise ValueError("mixed_evidence_fact_id inexistente")
            mixed_fact_ids.add(fact_id)

    return fact_contradiction_ids, mixed_fact_ids, refs_by_fact


def analyze_evidence_gaps(
    process_id: str,
    fact_outputs: list[dict[str, Any]],
    evidence_outputs: list[dict[str, Any]] | None = None,
    contradiction_outputs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Analyze evidence coverage deterministically.

    The input facts are assumed to have been selected upstream for the current
    task. This skill does not decide whether a fact is legally material.
    """
    normalized = build_contradiction_input(process_id, fact_outputs, evidence_outputs)
    process_id = normalized["process_id"]
    facts = {str(item["fact_id"]): item for item in normalized["facts"]}
    evidence_items = {str(item["evidence_id"]): item for item in normalized["evidence_items"]}
    links_by_fact: dict[str, list[dict[str, Any]]] = {fact_id: [] for fact_id in facts}
    for link in normalized["evidence_links"]:
        links_by_fact[str(link["fact_id"])].append(link)

    unresolved_by_fact: dict[str, list[dict[str, Any]]] = {fact_id: [] for fact_id in facts}
    for output in evidence_outputs or []:
        if not isinstance(output, dict):
            raise ValueError("evidence_output inválido")
        for point in output.get("unresolved_points") or []:
            if not isinstance(point, dict):
                raise ValueError("evidence unresolved_point inválido")
            fact_id = point.get("fact_id")
            if fact_id is None:
                continue
            fact_id = str(fact_id)
            if fact_id not in facts:
                raise ValueError("evidence unresolved_point referencia fact inexistente")
            unresolved_by_fact[fact_id].append(point)

    fact_contradictions, mixed_from_cd, cd_refs = _normalize_contradictions(
        set(facts),
        contradiction_outputs,
    )
    for row in cd_refs:
        if row["fact_id"] in facts:
            unresolved_by_fact[row["fact_id"]].append({
                "code": "FACTUAL_CONTRADICTION",
                "reason": "Contradição factual detectada.",
                "source_refs": row["source_refs"],
            })

    gap_items: list[dict[str, Any]] = []
    open_gap_fact_ids: list[str] = []

    for fact_id, fact in facts.items():
        links = links_by_fact.get(fact_id) or []
        supports = [link for link in links if link["relation"] == "SUPPORTS"]
        contradicts = [link for link in links if link["relation"] == "CONTRADICTS"]
        inconclusive = [link for link in links if link["relation"] == "INCONCLUSIVE"]

        if any(link.get("scope") == "FULL" for link in supports):
            coverage = "FULL"
        elif supports:
            coverage = "PARTIAL"
        elif not links and fact.get("epistemic_status") in _SELF_DOCUMENTED_STATUSES:
            coverage = "SELF_DOCUMENTED"
        else:
            coverage = "NONE"

        codes: list[str] = []
        if coverage == "NONE" and not links:
            codes.append("NO_EVIDENCE_IN_CONTEXT")
        elif coverage == "NONE" and links:
            codes.append("NO_SUPPORT_IN_CONTEXT")
        elif coverage == "PARTIAL":
            codes.append("PARTIAL_SUPPORT")

        if inconclusive:
            codes.append("INCONCLUSIVE_EVIDENCE")

        has_mixed = bool(supports and contradicts) or fact_id in mixed_from_cd
        if has_mixed:
            codes.append("CONFLICTING_EVIDENCE")

        unresolved_points = unresolved_by_fact.get(fact_id) or []
        for point in unresolved_points:
            code = str(point.get("code") or "").upper()
            mapped = {
                "REFERENCED_EVIDENCE_NOT_AVAILABLE": "REFERENCED_EVIDENCE_NOT_AVAILABLE",
                "VISUAL_CONTENT_NOT_AVAILABLE": "VISUAL_CONTENT_NOT_AVAILABLE",
                "EVIDENCE_REFERENCE_AMBIGUOUS": "AMBIGUOUS_EVIDENCE_REFERENCE",
                "FACTUAL_CONTRADICTION": "FACTUAL_CONTRADICTION_UNRESOLVED",
            }.get(code)
            if mapped:
                codes.append(mapped)
            elif code:
                codes.append("UNRESOLVED_EVIDENCE")

        if fact_id in fact_contradictions and "FACTUAL_CONTRADICTION_UNRESOLVED" not in codes:
            codes.append("FACTUAL_CONTRADICTION_UNRESOLVED")

        codes = list(dict.fromkeys(codes))

        # A full/self-documented fact remains covered despite extra unavailable
        # material unless there is an actual conflict/contradiction.
        if coverage in {"FULL", "SELF_DOCUMENTED"} and not has_mixed and fact_id not in fact_contradictions:
            codes = [
                code for code in codes
                if code not in {
                    "REFERENCED_EVIDENCE_NOT_AVAILABLE",
                    "VISUAL_CONTENT_NOT_AVAILABLE",
                    "AMBIGUOUS_EVIDENCE_REFERENCE",
                    "UNRESOLVED_EVIDENCE",
                }
            ]

        support_ids = sorted({str(link["evidence_id"]) for link in supports})
        contradiction_ids = sorted({str(link["evidence_id"]) for link in contradicts})
        inconclusive_ids = sorted({str(link["evidence_id"]) for link in inconclusive})
        limitations = sorted({
            str(code)
            for link in links
            for code in (link.get("limitations") or [])
            if str(code)
        })
        refs = _dedupe_refs(
            list(fact.get("source_refs") or [])
            + [
                ref
                for link in links
                for ref in (link.get("source_refs") or [])
            ]
            + [
                ref
                for point in unresolved_points
                for ref in (point.get("source_refs") or [])
            ]
        )

        is_open = bool(codes)
        if is_open:
            open_gap_fact_ids.append(fact_id)

        gap_items.append({
            "gap_id": _stable_gap_id(process_id, fact_id),
            "fact_id": fact_id,
            "epistemic_status": fact.get("epistemic_status"),
            "support_coverage": coverage,
            "gap_open": is_open,
            "gap_codes": codes,
            "supporting_evidence_ids": support_ids,
            "contradictory_evidence_ids": contradiction_ids,
            "inconclusive_evidence_ids": inconclusive_ids,
            "limitations": limitations,
            "source_refs": refs,
        })

    ambiguous_codes = {"CONFLICTING_EVIDENCE", "AMBIGUOUS_EVIDENCE_REFERENCE", "FACTUAL_CONTRADICTION_UNRESOLVED"}
    if any(ambiguous_codes.intersection(item["gap_codes"]) for item in gap_items):
        sufficiency = "AMBIGUOUS"
    elif open_gap_fact_ids:
        sufficiency = "INSUFFICIENT"
    else:
        sufficiency = "SUFFICIENT"

    return {
        "schema_version": SCHEMA_VERSION,
        "context_sufficiency": sufficiency,
        "gap_items": gap_items,
        "open_gap_fact_ids": sorted(open_gap_fact_ids),
    }
def score_evidence_gaps(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    expected_by_fact = {
        str(item.get("fact_id")): item
        for item in expected.get("gap_items") or []
    }
    actual_by_fact = {
        str(item.get("fact_id")): item
        for item in actual.get("gap_items") or []
    }

    fact_ids = set(expected_by_fact)
    coverage_matches = 0
    code_matches = 0
    dangerous_closed_gap = False
    for fact_id in fact_ids:
        exp = expected_by_fact[fact_id]
        act = actual_by_fact.get(fact_id) or {}
        if exp.get("support_coverage") == act.get("support_coverage"):
            coverage_matches += 1
        if sorted(exp.get("gap_codes") or []) == sorted(act.get("gap_codes") or []):
            code_matches += 1
        if bool(exp.get("gap_open")) and not bool(act.get("gap_open")):
            dangerous_closed_gap = True

    denominator = len(fact_ids) or 1
    return {
        "coverage_accuracy": coverage_matches / denominator,
        "gap_code_accuracy": code_matches / denominator,
        "open_gap_match": sorted(expected.get("open_gap_fact_ids") or []) == sorted(actual.get("open_gap_fact_ids") or []),
        "sufficiency_match": expected.get("context_sufficiency") == actual.get("context_sufficiency"),
        "dangerous_closed_gap": dangerous_closed_gap,
    }
