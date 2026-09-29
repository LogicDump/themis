"""Pure deterministic rule selection. This module never computes due dates."""
from __future__ import annotations

from datetime import date
from typing import Any, Iterable

PRECEDENCE = {
    "JUDICIAL_ORDER": 4,
    "STATUTORY_SPECIFIC": 3,
    "SPECIAL_PROCEDURE": 2,
    "RESIDUAL_DEFAULT": 1,
}


def _date(value: Any) -> date | None:
    if not value:
        return None
    return date.fromisoformat(str(value)[:10])


def resolve_deadline_rule(
    *, process_context: dict[str, Any], procedural_act_type: str,
    explicit_term_value: int | None = None, explicit_term_unit: str | None = None,
    candidate_rule_ids: Iterable[str] = (), model_preferred_rule_id: str | None = None,
    recipient_role: str | None = None, relevant_date: str | None = None,
    catalog: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Choose a compatible rule by documented precedence, independent of ML."""
    catalog_by_id = {r["rule_id"]: r for r in catalog}
    candidates = set(candidate_rule_ids)
    if model_preferred_rule_id:
        candidates.add(model_preferred_rule_id)
    valid: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    on_date = _date(relevant_date)
    for rule_id in sorted(candidates):
        rule = catalog_by_id.get(rule_id)
        reason = None
        if rule is None:
            reason = "UNKNOWN_RULE"
        elif rule.get("applicable_act_types") and "*" not in rule["applicable_act_types"] and procedural_act_type not in rule["applicable_act_types"]:
            reason = "PROCEDURAL_ACT_TYPE"
        elif rule.get("jurisdiction_scope") not in (None, "*", process_context.get("jurisdiction")):
            reason = "JURISDICTION"
        elif rule.get("process_classes") and process_context.get("process_class") not in rule["process_classes"]:
            reason = "PROCESS_CLASS"
        elif rule.get("procedures") and process_context.get("procedure") not in rule["procedures"]:
            reason = "PROCEDURE"
        elif rule.get("recipient_roles") and recipient_role not in rule["recipient_roles"]:
            reason = "RECIPIENT_ROLE"
        elif on_date and (_date(rule.get("effective_from")) and on_date < _date(rule["effective_from"]) or _date(rule.get("effective_to")) and on_date > _date(rule["effective_to"])):
            reason = "OUTSIDE_EFFECTIVE_PERIOD"
        if reason:
            rejected.append({"rule_id": rule_id, "reason": reason})
        else:
            valid.append(rule)

    explicit_rule = next((r for r in valid if r.get("category") == "JUDICIAL_ORDER" and r.get("allow_explicit_override")), None)
    if explicit_term_value is not None and explicit_rule:
        selected, method = explicit_rule, "JUDICIAL_EXPLICIT_TERM"
        term_value, term_unit = explicit_term_value, explicit_term_unit
    else:
        selected = max(valid, key=lambda r: (PRECEDENCE.get(r.get("category"), 0), r.get("precedence", 0), r["rule_id"]), default=None)
        method = "CATALOG_PRECEDENCE" if selected else "UNRESOLVED"
        term_value = selected.get("default_term_value") if selected else None
        term_unit = selected.get("term_unit") if selected else None
    return {
        "resolved_rule_id": selected["rule_id"] if selected else None,
        "resolution_method": method,
        "term_value": term_value,
        "term_unit": term_unit,
        "legal_basis": selected.get("legal_basis") if selected else None,
        "precedence_applied": selected.get("category") if selected else None,
        "review_required": selected is None or bool(rejected),
        "explanation": {"catalog_version": "1.0.0", "candidate_rule_ids": sorted(candidates), "rejected": rejected,
                        "model_preferred_rule_id": model_preferred_rule_id, "model_preference_authoritative": False},
    }
