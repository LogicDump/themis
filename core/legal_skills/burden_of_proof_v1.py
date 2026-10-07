"""Burden of Proof Analyzer V1.

Maps supplied burden-of-proof rules to validated legal issues and facts.
The model may select and apply only rules explicitly present in burden_rules.
It never invents legal bases or shifts burden without an explicit supplied rule.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA_VERSION = "burden-of-proof-analyzer-v1"

BURDEN_SIDES = ("CLAIMANT", "RESPONDENT", "BOTH", "THIRD_PARTY", "UNRESOLVED")
ALLOCATION_TYPES = ("DEFAULT", "SHIFTED", "DYNAMIC", "SHARED", "UNRESOLVED")

BURDEN_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "allocations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "issue_id": {"type": "string", "minLength": 1},
                    "fact_ids": {
                        "type": "array",
                        "minItems": 1,
                        "uniqueItems": True,
                        "items": {"type": "string", "minLength": 1},
                    },
                    "rule_id": {"type": "string", "minLength": 1},
                },
                "required": ["issue_id", "fact_ids", "rule_id"],
            },
        },
    },
    "required": ["allocations"],
}


def build_burden_instructions() -> str:
    return """TASK: BURDEN_OF_PROOF_MAP

INPUT:
- issues[] = validated legal issues.
- facts[] = validated factual propositions.
- burden_rules[] = ONLY legal rules you may select. Each rule already contains its deterministic allocation consequence.

RULE GATE:
1. NEVER use a legal rule not present in burden_rules[].
2. NEVER cite statutes, cases, doctrines or exceptions from memory.
3. If no supplied rule governs the issue/fact safely -> OMIT allocation. Themis will create the unresolved point deterministically.
4. A CONDITIONAL rule may be selected only when precondition_status=SATISFIED. UNKNOWN/UNSATISFIED -> OMIT allocation.
5. DO NOT choose burden_side, allocation_type or reason_code; Themis derives them from the selected rule.

MAPPING:
6. Link each allocation to one issue_id and only the fact_ids whose proof burden is actually being allocated.
7. Select the supplied rule whose own statement/conditions govern the factual proposition. The rule itself defines the resulting side/type.
8. Do not assign burden to a pure question of law with no factual proposition requiring proof. Always omit issues without fact_ids.
9. Evidence gap != burden. Evidence availability/strength does not change burden unless a supplied rule says it does.
10. Contradiction != burden shift.

OUTPUT:
- one allocation only for each burden determination actually supported by a supplied applicable rule;
- if unresolved, OMIT the allocation entirely;
- use only IDs from input;
- schema only."""


def build_burden_input(
    process_id: str,
    issue_outputs: list[dict[str, Any]],
    fact_outputs: list[dict[str, Any]],
    burden_rules: list[dict[str, Any]],
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
                "source_refs": list(item.get("source_refs") or []),
            })

    issues: list[dict[str, Any]] = []
    issue_ids: set[str] = set()
    for output in issue_outputs or []:
        if not isinstance(output, dict) or not isinstance(output.get("issues"), list):
            raise ValueError("issue_output inválido")
        for item in output["issues"]:
            issue_id = str(item.get("issue_id") or "").strip()
            question = str(item.get("question") or "").strip()
            linked_facts = sorted({str(x) for x in item.get("fact_ids") or []})
            if not issue_id or issue_id in issue_ids or not question:
                raise ValueError("issue inválida/duplicada")
            if any(fid not in fact_ids for fid in linked_facts):
                raise ValueError("issue referencia fact inexistente")
            issue_ids.add(issue_id)
            issues.append({
                "issue_id": issue_id,
                "question": question,
                "kind": str(item.get("kind") or ""),
                "fact_ids": linked_facts,
                "legal_position_ids": list(item.get("legal_position_ids") or []),
                "request_ids": list(item.get("request_ids") or []),
            })

    rules: list[dict[str, Any]] = []
    rule_ids: set[str] = set()
    for rule in burden_rules or []:
        if not isinstance(rule, dict):
            raise ValueError("burden_rule inválida")
        rule_id = str(rule.get("rule_id") or "").strip()
        statement = str(rule.get("statement") or "").strip()
        authority = str(rule.get("authority") or "").strip()
        regime = str(rule.get("regime") or "").strip()
        applicability = str(rule.get("applicability") or "GENERAL").strip().upper()
        side = rule.get("burden_side")
        allocation_type = rule.get("allocation_type")
        reason_code = rule.get("reason_code")
        status = rule.get("precondition_status", "UNKNOWN")
        conditions = [str(x).strip() for x in rule.get("conditions") or [] if str(x).strip()]
        if not rule_id or rule_id in rule_ids or not statement or not authority or not regime:
            raise ValueError("burden_rule incompleta/duplicada")
        if applicability not in {"GENERAL", "CONDITIONAL"}:
            raise ValueError("burden_rule applicability inválida")
        if side not in BURDEN_SIDES[:-1] or allocation_type not in ALLOCATION_TYPES[:-1]:
            raise ValueError("burden_rule consequence inválida")
        if not isinstance(reason_code, str) or not reason_code.strip():
            raise ValueError("burden_rule reason_code obrigatório")
        if status not in {"SATISFIED", "UNKNOWN", "UNSATISFIED"}:
            raise ValueError("burden_rule precondition_status inválido")
        rule_ids.add(rule_id)
        rules.append({
            "rule_id": rule_id,
            "statement": statement,
            "authority": authority,
            "regime": regime,
            "applicability": applicability,
            "burden_side": side,
            "allocation_type": allocation_type,
            "reason_code": reason_code.strip(),
            "precondition_status": status,
            "conditions": conditions,
        })

    return {
        "process_id": process_id,
        "issues": issues,
        "facts": facts,
        "burden_rules": rules,
    }


def build_burden_llm_input(skill_input: dict[str, Any]) -> dict[str, Any]:
    return {
        "issues": list(skill_input.get("issues") or []),
        "facts": [
            {
                "fact_id": x["fact_id"],
                "statement": x["statement"],
                "epistemic_status": x["epistemic_status"],
                "actor_id": x.get("actor_id"),
            }
            for x in skill_input.get("facts") or []
        ],
        "burden_rules": list(skill_input.get("burden_rules") or []),
    }
def _stable_id(
    process_id: str,
    issue_id: str,
    fact_ids: list[str],
    rule_id: str | None,
    side: str,
    allocation_type: str,
) -> str:
    raw = "\0".join((
        process_id,
        issue_id,
        ",".join(sorted(fact_ids)),
        rule_id or "",
        side,
        allocation_type,
    ))
    return "burden_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def validate_burden_allocations(value: Any, skill_input: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Burden Analyzer output não é JSON válido") from exc
    if not isinstance(value, dict) or set(value) != {"allocations"} or not isinstance(value["allocations"], list):
        raise ValueError("Burden Analyzer output divergente do schema")

    issues = {str(x["issue_id"]): x for x in skill_input.get("issues") or []}
    facts = {str(x["fact_id"]): x for x in skill_input.get("facts") or []}
    rules = {str(x["rule_id"]): x for x in skill_input.get("burden_rules") or []}

    allocations: list[dict[str, Any]] = []
    unresolved_points: list[dict[str, Any]] = []
    covered: dict[str, set[str]] = {iid: set() for iid in issues}
    for item in value["allocations"]:
        if not isinstance(item, dict) or set(item) != {"issue_id", "fact_ids", "rule_id"}:
            raise ValueError("burden allocation divergente do schema")
        issue_id, rule_id, fact_ids = item["issue_id"], item["rule_id"], item["fact_ids"]
        if not isinstance(issue_id, str) or issue_id not in issues:
            raise ValueError("allocation referencia issue inexistente")
        if (not isinstance(fact_ids, list) or not fact_ids
                or any(not isinstance(fid, str) or fid not in facts for fid in fact_ids)
                or len(set(fact_ids)) != len(fact_ids)):
            raise ValueError("allocation exige fact_ids válidos e únicos")
        fact_ids = sorted(fact_ids)
        if any(fid not in issues[issue_id]["fact_ids"] for fid in fact_ids):
            raise ValueError("allocation fact_id não pertence à issue")
        if not isinstance(rule_id, str) or rule_id not in rules:
            raise ValueError("allocation referencia rule_id inexistente")
        rule = rules[rule_id]
        if rule["applicability"] == "CONDITIONAL" and rule["precondition_status"] != "SATISFIED":
            continue  # Ineligible selections never allocate; uncovered facts remain unresolved.
        if covered[issue_id].intersection(fact_ids):
            raise ValueError("allocation duplicada/sobreposta para issue/facts")
        covered[issue_id].update(fact_ids)
        side, allocation_type = rule["burden_side"], rule["allocation_type"]
        allocations.append({
            "allocation_id": _stable_id(skill_input["process_id"], issue_id, fact_ids, rule_id, side, allocation_type),
            "issue_id": issue_id,
            "fact_ids": fact_ids,
            "rule_id": rule_id,
            **{field: rule[field] for field in ("burden_side", "allocation_type", "reason_code", "authority", "regime")},
        })
    allocations.sort(key=lambda item: (item["issue_id"], item["fact_ids"], item["rule_id"]))
    for issue_id, issue in sorted(issues.items()):
        missing = sorted(set(issue["fact_ids"]) - covered[issue_id])
        if missing:
            unresolved_points.append({"issue_id": issue_id, "fact_ids": missing, "code": "RULE_NOT_SUPPLIED"})

    sufficiency = "INSUFFICIENT" if unresolved_points else "SUFFICIENT"
    return {
        "schema_version": SCHEMA_VERSION,
        "context_sufficiency": sufficiency,
        "allocations": allocations,
        "unresolved_points": unresolved_points,
    }


def score_burden_allocations(
    expected: dict[str, Any], actual: dict[str, Any], skill_input: dict[str, Any],
) -> dict[str, Any]:
    def key(item: dict[str, Any]) -> tuple:
        return (
            str(item.get("issue_id") or ""),
            tuple(sorted(item.get("fact_ids") or [])),
            item.get("rule_id"),
            str(item.get("burden_side") or ""),
            str(item.get("allocation_type") or ""),
        )

    exp = {key(x) for x in expected.get("allocations") or []}
    act = {key(x) for x in actual.get("allocations") or []}
    matched = len(exp & act)
    precision = 1.0 if not act else matched / len(act)
    recall = 1.0 if not exp else matched / len(exp)

    rules = {rule["rule_id"]: rule for rule in skill_input["burden_rules"]}
    invented_rule = any(item.get("rule_id") not in rules for item in actual.get("allocations") or [])
    dangerous_shift = False
    for item in actual.get("allocations") or []:
        if item.get("allocation_type") not in {"SHIFTED", "DYNAMIC"}:
            continue
        rule = rules.get(item.get("rule_id"))
        if (rule is None or item.get("allocation_type") != rule["allocation_type"]
                or item.get("burden_side") != rule["burden_side"]
                or (rule["applicability"] == "CONDITIONAL" and rule["precondition_status"] != "SATISFIED")):
            dangerous_shift = True
    return {
        "allocation_precision": precision,
        "allocation_recall": recall,
        "sufficiency_match": expected.get("context_sufficiency") == actual.get("context_sufficiency"),
        "dangerous_invented_rule": invented_rule,
        "dangerous_shift_invention": dangerous_shift,
    }
