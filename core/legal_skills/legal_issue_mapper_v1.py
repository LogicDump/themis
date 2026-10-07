"""Legal Issue Mapper V1.

Maps validated facts, legal positions, requests, contradictions and evidence
gaps into neutral legal/factual issues. This is distinct from
core.drafting.issue_map_v1, which exists only to generate retrieval queries.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from core.legal_skills.source_contract_v1 import normalize_text

SCHEMA_VERSION = "legal-issue-mapper-v1"

ISSUE_KINDS = ("FACTUAL", "LEGAL", "MIXED", "PROCEDURAL")

LEGAL_ISSUE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "question": {"type": "string", "minLength": 1},
                    "kind": {"type": "string", "enum": list(ISSUE_KINDS)},
                    "fact_ids": {
                        "type": "array", "uniqueItems": True,
                        "items": {"type": "string", "minLength": 1},
                    },
                    "legal_position_ids": {
                        "type": "array", "uniqueItems": True,
                        "items": {"type": "string", "minLength": 1},
                    },
                    "request_ids": {
                        "type": "array", "uniqueItems": True,
                        "items": {"type": "string", "minLength": 1},
                    },
                },
                "required": [
                    "question", "kind", "fact_ids",
                    "legal_position_ids", "request_ids",
                ],
            },
        },
    },
    "required": ["issues"],
}


def build_legal_issue_instructions() -> str:
    return """TASK: LEGAL_ISSUE_MAP

INPUT:
- facts[] = validated factual propositions.
- legal_positions[] = legal theses/grounds/objections defended by actors.
- requests[] = requested judicial/procedural outcomes.
- fact_contradictions[] = already detected factual incompatibilities.
- evidence_gaps[] = coverage state only; a gap is NOT itself an issue.

DEFINITION:
An issue is a neutral question whose answer can materially affect a request,
a legal position, or an already detected factual contradiction.

FOR EACH candidate:
1. Pure background fact with no contradiction and no connection to a legal_position/request -> SKIP.
2. Evidence gap alone -> SKIP. Link the underlying fact only if it forms a material issue.
3. Two compatible facts -> SKIP.
4. Repetition of the same legal position -> SKIP.
5. Opposing/incompatible factual propositions about the same material point -> FACTUAL.
6. Competing legal propositions/objections about the same legal consequence -> LEGAL.
7. Resolution requires both a disputed fact and a legal proposition -> MIXED.
8. Competence, admissibility, timeliness, standing or procedural validity -> PROCEDURAL.
9. A request may define a live legal issue even when no opposing legal_position is yet present, but do not invent opposition.
10. COVERAGE: every material request must be linked to at least one issue. Every material legal_position should be linked unless it is merely duplicative of another linked proposition.

QUESTION:
- neutral and outcome-free;
- preferably interrogative ("se...", "qual...", "houve...");
- no answer, recommendation, burden of proof, strategy or new legal basis.

LINKS:
- include only IDs from input that are necessary to define the issue;
- at least one linked ID is required;
- DO NOT output IDs invented by you.

NEVER:
- decide which side is correct;
- convert lack of evidence into factual falsity;
- infer burden of proof;
- add statutes, precedents or legal grounds absent from legal_positions;
- merge unrelated controversies merely because they involve the same party.

OUTPUT: schema only."""


def _validate_refs(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for ref in value:
        if not isinstance(ref, dict):
            continue
        document_id = str(ref.get("document_id") or "").strip()
        pdf_page = ref.get("pdf_page")
        quote = str(ref.get("quote") or "").strip()
        if document_id and isinstance(pdf_page, int) and not isinstance(pdf_page, bool) and pdf_page > 0 and quote:
            out.append({"document_id": document_id, "pdf_page": pdf_page, "quote": quote})
    return out


def build_legal_issue_input(
    process_id: str,
    fact_outputs: list[dict[str, Any]],
    claim_outputs: list[dict[str, Any]] | None = None,
    contradiction_outputs: list[dict[str, Any]] | None = None,
    gap_outputs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    process_id = str(process_id or "").strip()
    if not process_id:
        raise ValueError("process_id obrigatório")

    facts: list[dict[str, Any]] = []
    fact_ids: set[str] = set()
    for output in fact_outputs or []:
        if not isinstance(output, dict) or not isinstance(output.get("facts"), list):
            raise ValueError("fact_output inválido")
        for item in output["facts"]:
            fact_id = str(item.get("fact_id") or "").strip()
            statement = str(item.get("statement") or "").strip()
            if not fact_id or fact_id in fact_ids or not statement:
                raise ValueError("fact inválido/duplicado")
            fact_ids.add(fact_id)
            facts.append({
                "fact_id": fact_id,
                "statement": statement,
                "epistemic_status": str(item.get("epistemic_status") or ""),
                "actor_id": item.get("actor_id"),
                "temporal_text": item.get("temporal_text"),
                "source_refs": _validate_refs(item.get("source_refs") or []),
            })

    legal_positions: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []
    position_ids: set[str] = set()
    request_ids: set[str] = set()
    for output in claim_outputs or []:
        if not isinstance(output, dict):
            raise ValueError("claim_output inválido")
        for item in output.get("legal_positions") or []:
            item_id = str(item.get("item_id") or "").strip()
            text = str(item.get("text") or "").strip()
            if not item_id or item_id in position_ids or not text:
                raise ValueError("legal_position inválida/duplicada")
            position_ids.add(item_id)
            legal_positions.append({
                "legal_position_id": item_id,
                "text": text,
                "actor_id": item.get("actor_id"),
                "source_refs": _validate_refs(item.get("source_refs") or []),
            })
        for item in output.get("requests") or []:
            item_id = str(item.get("item_id") or "").strip()
            text = str(item.get("text") or "").strip()
            if not item_id or item_id in request_ids or not text:
                raise ValueError("request inválido/duplicado")
            request_ids.add(item_id)
            requests.append({
                "request_id": item_id,
                "text": text,
                "actor_id": item.get("actor_id"),
                "source_refs": _validate_refs(item.get("source_refs") or []),
            })

    fact_contradictions: list[dict[str, Any]] = []
    for output in contradiction_outputs or []:
        if not isinstance(output, dict):
            raise ValueError("contradiction_output inválido")
        for item in output.get("fact_contradictions") or []:
            left = str(item.get("left_fact_id") or "").strip()
            right = str(item.get("right_fact_id") or "").strip()
            if left not in fact_ids or right not in fact_ids:
                raise ValueError("fact_contradiction referencia fact inexistente")
            fact_contradictions.append({
                "contradiction_id": str(item.get("contradiction_id") or ""),
                "left_fact_id": left,
                "right_fact_id": right,
                "strength": str(item.get("strength") or ""),
                "dimensions": list(item.get("dimensions") or []),
            })

    evidence_gaps: list[dict[str, Any]] = []
    for output in gap_outputs or []:
        if not isinstance(output, dict):
            raise ValueError("gap_output inválido")
        for item in output.get("gap_items") or []:
            fact_id = str(item.get("fact_id") or "").strip()
            if fact_id not in fact_ids:
                raise ValueError("gap_item referencia fact inexistente")
            evidence_gaps.append({
                "fact_id": fact_id,
                "support_coverage": str(item.get("support_coverage") or ""),
                "gap_open": bool(item.get("gap_open")),
                "gap_codes": list(item.get("gap_codes") or []),
            })

    return {
        "process_id": process_id,
        "facts": facts,
        "legal_positions": legal_positions,
        "requests": requests,
        "fact_contradictions": fact_contradictions,
        "evidence_gaps": evidence_gaps,
    }
def build_legal_issue_llm_input(skill_input: dict[str, Any]) -> dict[str, Any]:
    return {
        "facts": [
            {
                "fact_id": x["fact_id"],
                "statement": x["statement"],
                "epistemic_status": x["epistemic_status"],
                "actor_id": x.get("actor_id"),
                "temporal_text": x.get("temporal_text"),
            }
            for x in skill_input.get("facts") or []
        ],
        "legal_positions": [
            {
                "legal_position_id": x["legal_position_id"],
                "text": x["text"],
                "actor_id": x.get("actor_id"),
            }
            for x in skill_input.get("legal_positions") or []
        ],
        "requests": [
            {
                "request_id": x["request_id"],
                "text": x["text"],
                "actor_id": x.get("actor_id"),
            }
            for x in skill_input.get("requests") or []
        ],
        "fact_contradictions": list(skill_input.get("fact_contradictions") or []),
        "evidence_gaps": list(skill_input.get("evidence_gaps") or []),
    }


def _stable_issue_id(
    process_id: str,
    kind: str,
    question: str,
    fact_ids: list[str],
    position_ids: list[str],
    request_ids: list[str],
) -> str:
    raw = "\0".join((
        process_id,
        kind,
        normalize_text(question),
        ",".join(sorted(fact_ids)),
        ",".join(sorted(position_ids)),
        ",".join(sorted(request_ids)),
    ))
    return "issue_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _dedupe_refs(refs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()
    for ref in refs:
        key = (
            str(ref.get("document_id") or ""),
            int(ref.get("pdf_page") or 0),
            normalize_text(ref.get("quote") or ""),
        )
        if key[0] and key[1] > 0 and key[2] and key not in seen:
            seen.add(key)
            out.append({
                "document_id": key[0],
                "pdf_page": key[1],
                "quote": str(ref.get("quote") or ""),
            })
    return out


def validate_legal_issues(value: Any, skill_input: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Legal Issue Mapper output não é JSON válido") from exc
    if not isinstance(value, dict) or set(value) != {"issues"} or not isinstance(value["issues"], list):
        raise ValueError("Legal Issue Mapper output divergente do schema")

    facts = {str(x["fact_id"]): x for x in skill_input.get("facts") or []}
    positions = {str(x["legal_position_id"]): x for x in skill_input.get("legal_positions") or []}
    requests = {str(x["request_id"]): x for x in skill_input.get("requests") or []}
    contradiction_pairs = {
        frozenset((str(x["left_fact_id"]), str(x["right_fact_id"])))
        for x in skill_input.get("fact_contradictions") or []
    }
    gaps = {
        str(x["fact_id"]): x
        for x in skill_input.get("evidence_gaps") or []
    }

    seen: set[tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = set()
    issues: list[dict[str, Any]] = []
    unresolved_points: list[dict[str, Any]] = []

    for item in value["issues"]:
        required = {"question", "kind", "fact_ids", "legal_position_ids", "request_ids"}
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError("issue divergente do schema")
        question = str(item["question"] or "").strip()
        kind = str(item["kind"] or "").upper()
        fact_ids = sorted({str(x) for x in item["fact_ids"]})
        position_ids = sorted({str(x) for x in item["legal_position_ids"]})
        request_ids = sorted({str(x) for x in item["request_ids"]})
        if not question or kind not in ISSUE_KINDS:
            raise ValueError("issue question/kind inválido")
        if not fact_ids and not position_ids and not request_ids:
            raise ValueError("issue sem vínculos")
        if any(x not in facts for x in fact_ids):
            raise ValueError("issue referencia fact inexistente")
        if any(x not in positions for x in position_ids):
            raise ValueError("issue referencia legal_position inexistente")
        if any(x not in requests for x in request_ids):
            raise ValueError("issue referencia request inexistente")

        has_contradiction = any(
            pair.issubset(set(fact_ids))
            for pair in contradiction_pairs
        )

        # Hard classification from link structure. Only PROCEDURAL remains a
        # semantic subtype the model may select.
        if kind != "PROCEDURAL":
            if fact_ids and (position_ids or request_ids):
                kind = "MIXED"
            elif position_ids or request_ids:
                kind = "LEGAL"
            else:
                kind = "FACTUAL"

        # A fact-only candidate is a live issue only when an upstream factual
        # contradiction already established controversy. Evidence gap alone is
        # not enough; discard the candidate safely.
        if kind == "FACTUAL" and not position_ids and not request_ids and not has_contradiction:
            continue

        if kind == "PROCEDURAL" and not position_ids and not request_ids:
            raise ValueError("PROCEDURAL issue sem conteúdo jurídico")

        key = (kind, tuple(fact_ids), tuple(position_ids), tuple(request_ids))
        if key in seen:
            raise ValueError("issue duplicada")
        seen.add(key)

        refs: list[dict[str, Any]] = []
        actor_ids: set[str] = set()
        for fact_id in fact_ids:
            refs.extend(facts[fact_id].get("source_refs") or [])
            if facts[fact_id].get("actor_id"):
                actor_ids.add(str(facts[fact_id]["actor_id"]))
        for position_id in position_ids:
            refs.extend(positions[position_id].get("source_refs") or [])
            if positions[position_id].get("actor_id"):
                actor_ids.add(str(positions[position_id]["actor_id"]))
        for request_id in request_ids:
            refs.extend(requests[request_id].get("source_refs") or [])
            if requests[request_id].get("actor_id"):
                actor_ids.add(str(requests[request_id]["actor_id"]))

        gap_codes = sorted({
            str(code)
            for fact_id in fact_ids
            for code in (gaps.get(fact_id, {}).get("gap_codes") or [])
        })
        contradiction_ids = sorted({
            str(x.get("contradiction_id"))
            for x in skill_input.get("fact_contradictions") or []
            if str(x.get("left_fact_id")) in fact_ids and str(x.get("right_fact_id")) in fact_ids
        })

        issue_id = _stable_issue_id(
            skill_input["process_id"], kind, question,
            fact_ids, position_ids, request_ids,
        )
        issues.append({
            "issue_id": issue_id,
            "question": question,
            "kind": kind,
            "fact_ids": fact_ids,
            "legal_position_ids": position_ids,
            "request_ids": request_ids,
            "actor_ids": sorted(actor_ids),
            "contradiction_ids": contradiction_ids,
            "evidence_gap_codes": gap_codes,
            "source_refs": _dedupe_refs(refs),
        })

        if any(gaps.get(fid, {}).get("gap_open") for fid in fact_ids):
            unresolved_points.append({
                "issue_id": issue_id,
                "code": "UNDERLYING_EVIDENCE_GAP",
                "fact_ids": [fid for fid in fact_ids if gaps.get(fid, {}).get("gap_open")],
            })

    sufficiency = "INSUFFICIENT" if unresolved_points else "SUFFICIENT"
    return {
        "schema_version": SCHEMA_VERSION,
        "context_sufficiency": sufficiency,
        "issues": issues,
        "unresolved_points": unresolved_points,
    }
def score_legal_issues(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    exp = list(expected.get("issues") or [])
    act = list(actual.get("issues") or [])
    unmatched = set(range(len(act)))
    matched = 0
    kind_mismatches = 0
    link_mismatches = 0

    for e in exp:
        e_facts = set(e.get("fact_ids") or [])
        e_pos = set(e.get("legal_position_ids") or [])
        e_req = set(e.get("request_ids") or [])
        hit = next((
            i for i in unmatched
            if (
                set(act[i].get("fact_ids") or []) == e_facts
                and set(act[i].get("legal_position_ids") or []) == e_pos
                and set(act[i].get("request_ids") or []) == e_req
            )
        ), None)
        if hit is None:
            continue
        matched += 1
        unmatched.remove(hit)
        if str(act[hit].get("kind")) != str(e.get("kind")):
            kind_mismatches += 1

    precision = 1.0 if not act else matched / len(act)
    recall = 1.0 if not exp else matched / len(exp)

    expected_link_sets = {
        (
            tuple(sorted(x.get("fact_ids") or [])),
            tuple(sorted(x.get("legal_position_ids") or [])),
            tuple(sorted(x.get("request_ids") or [])),
        )
        for x in exp
    }
    for a in act:
        links = (
            tuple(sorted(a.get("fact_ids") or [])),
            tuple(sorted(a.get("legal_position_ids") or [])),
            tuple(sorted(a.get("request_ids") or [])),
        )
        if links not in expected_link_sets:
            link_mismatches += 1

    dangerous_unlinked_issue = any(
        not (x.get("fact_ids") or x.get("legal_position_ids") or x.get("request_ids"))
        for x in act
    )
    return {
        "issue_precision": precision,
        "issue_recall": recall,
        "kind_mismatch_count": kind_mismatches,
        "link_mismatch_count": link_mismatches,
        "sufficiency_match": expected.get("context_sufficiency") == actual.get("context_sufficiency"),
        "dangerous_unlinked_issue": dangerous_unlinked_issue,
    }
