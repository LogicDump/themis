"""Pure, deterministic LegalRule selection; never computes dates or reads calendars."""
from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from core.documentos.legal_context_v1 import LegalContext

EXPLICIT_FACT_RULE_ID = "JUDICIAL_EXPLICIT_TERM"
_LEGACY_CATEGORY_ORDER = {"JUDICIAL_ORDER": 4, "STATUTORY_SPECIFIC": 3, "SPECIAL_PROCEDURE": 2, "RESIDUAL_DEFAULT": 1}


def _date(value: Any) -> date | None:
    return date.fromisoformat(str(value)[:10]) if value else None


def _rule_regimes(rule: dict[str, Any]) -> tuple[str, ...]:
    constraints = rule.get("regime_constraints")
    if isinstance(constraints, dict):
        constraints = constraints.get("allowed_regimes", ())
    if isinstance(constraints, str):
        constraints = (constraints,)
    regimes = constraints or rule.get("applicable_regimes") or ()
    if isinstance(regimes, str):
        regimes = (regimes,)
    if not regimes and rule.get("base_regime"):
        regimes = (rule["base_regime"],)
    return tuple(str(x).upper() for x in regimes)


def _check(rule: dict[str, Any], context: LegalContext, act_type: str,
           recipient_role: str | None, on_date: date | None) -> str | None:
    domain = rule.get("legal_domain")
    if domain and str(domain).upper() not in {context.legal_domain, "*", "ANY"}:
        return "LEGAL_DOMAIN"
    regimes = _rule_regimes(rule)
    if regimes and not any(x in context.applicable_regimes for x in regimes):
        return "BASE_REGIME" if rule.get("base_regime") and not rule.get("applicable_regimes") else "APPLICABLE_REGIMES"
    act_types = rule.get("procedural_act_types", rule.get("applicable_act_types", ()))
    if act_types and "*" not in act_types and act_type not in act_types:
        return "PROCEDURAL_ACT_TYPE"
    classes = rule.get("procedure_classes", rule.get("process_classes", ()))
    if classes and context.procedure_class not in classes:
        return "PROCEDURE_CLASS"
    jurisdiction = rule.get("jurisdiction_scope")
    if jurisdiction not in (None, "", "*", "ANY", "BR", context.jurisdiction):
        scopes = jurisdiction if isinstance(jurisdiction, (list, tuple, set)) else (jurisdiction,)
        if not any(scope in {"*", "ANY", "BR", context.jurisdiction} for scope in scopes):
            return "JURISDICTION"
    roles = rule.get("recipient_roles", ())
    if roles and recipient_role not in roles:
        return "RECIPIENT_ROLE"
    start, end = _date(rule.get("effective_from")), _date(rule.get("effective_to"))
    if on_date and ((start and on_date < start) or (end and on_date > end)):
        return "OUTSIDE_EFFECTIVE_PERIOD"
    return None


def resolve_deadline_rule(
    *, process_context: dict[str, Any] | LegalContext | None = None,
    legal_context: dict[str, Any] | LegalContext | None = None,
    procedural_act_type: str,
    explicit_term_value: int | None = None,
    explicit_term_unit: str | None = None,
    explicit_term_permitted: bool = True,
    candidate_rule_ids: Iterable[str] = (),
    model_preferred_rule_id: str | None = None,
    recipient_role: str | None = None,
    relevant_date: str | None = None,
    catalog: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Resolve only from compatible rules, regime order, and declared precedence."""
    raw_context = legal_context if legal_context is not None else process_context
    if raw_context is None:
        raise ValueError("legal_context obrigatório")
    context = raw_context if isinstance(raw_context, LegalContext) else LegalContext.from_mapping(raw_context)
    rules = tuple(catalog)
    by_id = {r["rule_id"]: r for r in rules}
    requested = set(candidate_rule_ids)
    # ML remains a hypothesis and enters only the same compatibility checks.
    if model_preferred_rule_id:
        requested.add(model_preferred_rule_id)
    on_date = _date(relevant_date)

    # Explicit term is an observed judicial fact. It does not require any model
    # candidate. If a catalog-specific override rule exists, its constraints
    # still apply; otherwise the fact is returned without inventing a LegalRule.
    explicit_valid = (isinstance(explicit_term_value, int) and not isinstance(explicit_term_value, bool)
                      and explicit_term_value > 0
                      and explicit_term_unit in {"DAYS", "BUSINESS_DAYS", "HOURS", "MONTHS"})
    if explicit_term_value is not None and explicit_valid and explicit_term_permitted:
        judicial = [r for r in rules if r.get("category") in {"JUDICIAL_ORDER", "JUDICIAL_EXPLICIT_TERM"} and r.get("allow_explicit_override")]
        compatible = [r for r in judicial if _check(r, context, procedural_act_type, recipient_role, on_date) is None]
        selected = compatible[0] if compatible else None
        return {
            "resolved_rule_id": selected["rule_id"] if selected else EXPLICIT_FACT_RULE_ID,
            "resolution_method": "JUDICIAL_EXPLICIT_TERM",
            "term_value": explicit_term_value,
            "term_unit": explicit_term_unit,
            "counting_policy_id": selected.get("counting_policy_id") if selected else None,
            "communication_policy_id": selected.get("communication_policy_id") if selected else None,
            "legal_basis": selected.get("legal_basis") if selected else None,
            "precedence_applied": "JUDICIAL_EXPLICIT_TERM",
            "review_required": False,
            "explanation": {"candidate_rule_ids": sorted(requested), "explicit_term_is_observed_fact": True,
                            "model_preference_authoritative": False, "calendar_consulted": False},
        }

    rejected: list[dict[str, str]] = []
    if explicit_term_value is not None and (not explicit_valid or not explicit_term_permitted):
        rejected.append({"rule_id": EXPLICIT_FACT_RULE_ID,
                         "reason": "INVALID_EXPLICIT_TERM" if not explicit_valid else "EXPLICIT_OVERRIDE_NOT_PERMITTED"})
    valid: list[tuple[dict[str, Any], int]] = []
    regime_order = {regime: i for i, regime in enumerate(context.applicable_regimes)}
    for rule_id in sorted(requested):
        rule = by_id.get(rule_id)
        reason = "UNKNOWN_RULE" if rule is None else _check(rule, context, procedural_act_type, recipient_role, on_date)
        if reason:
            rejected.append({"rule_id": rule_id, "reason": reason})
            continue
        rule_regimes = _rule_regimes(rule)
        # Earlier applicable_regimes are more specific. This makes a special
        # regime outrank the base regime without hardcoding any legal system.
        regime_rank = min((regime_order[r] for r in rule_regimes if r in regime_order), default=len(regime_order))
        valid.append((rule, regime_rank))

    def order(item: tuple[dict[str, Any], int]) -> tuple[int, int, int, str]:
        rule, regime_rank = item
        declared = int(rule.get("precedence", 0))
        legacy_category = _LEGACY_CATEGORY_ORDER.get(rule.get("category"), 0)
        return (-regime_rank, declared, legacy_category, str(rule["rule_id"]))

    selected_pair = max(valid, key=order, default=None)
    selected = selected_pair[0] if selected_pair else None
    return {
        "resolved_rule_id": selected["rule_id"] if selected else None,
        "resolution_method": "REGIME_AND_DECLARED_PRECEDENCE" if selected else "UNRESOLVED",
        "term_value": selected.get("term_value", selected.get("default_term_value")) if selected else None,
        "term_unit": selected.get("term_unit") if selected else None,
        "counting_policy_id": selected.get("counting_policy_id") if selected else None,
        "communication_policy_id": selected.get("communication_policy_id") if selected else None,
        "legal_basis": selected.get("legal_basis") if selected else None,
        "precedence_applied": {"regime_rank": selected_pair[1], "declared_precedence": selected.get("precedence")} if selected_pair else None,
        "review_required": selected is None or bool(rejected),
        "explanation": {"legal_context": context.as_dict(), "candidate_rule_ids": sorted(requested),
                        "rejected": rejected, "model_preferred_rule_id": model_preferred_rule_id,
                        "model_preference_authoritative": False, "calendar_consulted": False},
    }
