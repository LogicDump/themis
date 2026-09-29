"""Pure deterministic deadline calculation over declared policies and calendars.

This module performs no acquisition, persistence, language inference, or legal
classification. Calendar coverage and all policy decisions are supplied by the
caller; unresolved legal or factual inputs are returned as structured states.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, timedelta
from typing import Any, Iterable, Mapping

from .deadline_policies_v1 import (
    COMMUNICATION_POLICIES,
    COUNTING_POLICIES,
    COUNTING_QUALIFIER_MODES,
    REGIME_COUNTING_POLICY_IDS,
    SUSPENSION_POLICIES,
    CommunicationPolicy,
    CountingPolicy,
    CourtCalendar,
    SuspensionPolicy,
)
from .legal_context_v1 import LegalContext
from .legal_deadline_rules_v1 import LegalDeadlineRule, get_catalog


@dataclass(frozen=True)
class CommunicationFact:
    source_event_id: str
    event_type: str
    communication_method: str
    source_refs: tuple[dict[str, Any], ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
    available_on: str | None = None
    published_on: str | None = None
    notified_on: str | None = None
    served_on: str | None = None
    acknowledged_on: str | None = None


@dataclass(frozen=True)
class DeadlineCalculationInput:
    legal_context: LegalContext | Mapping[str, Any]
    resolved_rule_id: str
    term_value: int
    term_unit: str
    counting_policy_id: str | None
    communication_policy_id: str | None
    communication_fact: CommunicationFact | Mapping[str, Any] | None
    calendar_entries: tuple[CourtCalendar | Mapping[str, Any], ...]
    relevant_date: str
    rule_version: str | None = None
    explicit_counting_qualifier: str | None = None
    requires_personal_notice: bool = False
    applicable_suspension_exceptions: Mapping[str, str] = field(default_factory=dict)
    resolved_rule_provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeadlineCalculationResult:
    status: str
    resolved_rule_id: str
    rule_version: str | None
    legal_domain: str
    base_regime: str
    term_value: int
    term_unit: str
    counting_policy_id: str | None
    counting_policy_version: str | None
    communication_policy_id: str | None
    communication_event_id: str | None
    trigger_date: str | None
    trigger_resolution_method: str | None
    counting_start_date: str | None
    due_date: str | None
    counted_days: tuple[dict[str, Any], ...]
    excluded_days: tuple[dict[str, Any], ...]
    applied_suspensions: tuple[dict[str, Any], ...]
    calendar_version: str | None
    calendar_provenance: tuple[dict[str, Any], ...]
    calculation_trace: tuple[dict[str, Any], ...]
    legal_basis: dict[str, Any]
    provenance: dict[str, Any]
    reason: dict[str, Any] | None = None


class _Stop(Exception):
    def __init__(self, status: str, code: str, detail: Mapping[str, Any] | None = None):
        self.status, self.code, self.detail = status, code, dict(detail or {})


def _mapping(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    return dict(value or {})


def _date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _policy_map(values: Iterable[Any], key: str) -> dict[str, Any]:
    return {str(getattr(value, key)): value for value in values}


def _record(value: Any) -> dict[str, Any]:
    return _mapping(value)


def _find_rule(rule_id: str, version: str | None, rules: Iterable[Mapping[str, Any]]) -> Mapping[str, Any]:
    found = [r for r in rules if r.get("rule_id") == rule_id and (version is None or r.get("rule_version") == version)]
    if not found:
        raise _Stop("UNRESOLVED", "RESOLVED_RULE_NOT_FOUND", {"rule_id": rule_id, "rule_version": version})
    if len(found) != 1:
        raise _Stop("REVIEW_REQUIRED", "RULE_VERSION_AMBIGUOUS", {"rule_id": rule_id})
    return found[0]


def _in_effect(policy: Any, when: date, *, from_field: str = "effective_from", to_field: str = "effective_to") -> bool:
    start = getattr(policy, from_field, None)
    end = getattr(policy, to_field, None)
    return (not start or _date(start) <= when) and (not end or when <= _date(end))


def _calendar_index(entries: Iterable[Any], context: LegalContext) -> tuple[dict[date, Any], str | None, list[dict[str, Any]]]:
    scoped: dict[date, Any] = {}
    for raw in entries:
        entry = _record(raw)
        if context.jurisdiction and entry.get("jurisdiction") not in (None, "*", context.jurisdiction):
            continue
        key = _date(entry["date"])
        if key in scoped and _record(scoped[key]) != entry:
            raise _Stop("REVIEW_REQUIRED", "CALENDAR_ENTRY_CONFLICT", {"date": key.isoformat()})
        scoped[key] = raw
    versions = sorted({str(_record(e).get("version") or "") for e in scoped.values()})
    if len(versions) > 1:
        raise _Stop("REVIEW_REQUIRED", "CALENDAR_VERSION_MISMATCH", {"versions": versions})
    provenance = tuple(sorted(({
        "date": _record(e)["date"], "jurisdiction": _record(e).get("jurisdiction"),
        "court": _record(e).get("court"), "locality_unit": _record(e).get("locality_unit"),
        "status": _record(e).get("status"), "scope": _record(e).get("scope"),
        "official_source": _record(e).get("official_source"),
        "verified_at": _record(e).get("verified_at"), "version": _record(e).get("version"),
    } for e in scoped.values()), key=lambda x: x["date"]))
    return scoped, versions[0] if versions else None, list(provenance)


def _period_contains(day: date, policy: SuspensionPolicy) -> bool:
    start_m, start_d = (int(v) for v in policy.period_start.split("-"))
    end_m, end_d = (int(v) for v in policy.period_end.split("-"))
    start = (start_m, start_d)
    end = (end_m, end_d)
    current = (day.month, day.day)
    inside = current >= start or current <= end if start > end else start <= current <= end
    if not policy.inclusive and inside:
        inside = current not in (start, end)
    return inside and _in_effect(policy, day)


def _resolve_counting_policy(rule: Mapping[str, Any], inp: DeadlineCalculationInput,
                             context: LegalContext, policies: Mapping[str, CountingPolicy]) -> CountingPolicy:
    mode_map = dict(COUNTING_QUALIFIER_MODES)
    if inp.explicit_counting_qualifier and inp.term_unit in mode_map and inp.explicit_counting_qualifier != inp.term_unit:
        raise _Stop("REVIEW_REQUIRED", "COUNTING_QUALIFIERS_CONFLICT", {
            "explicit_counting_qualifier": inp.explicit_counting_qualifier, "term_unit": inp.term_unit})
    explicit = inp.explicit_counting_qualifier or (inp.term_unit if inp.term_unit in mode_map else None)
    if explicit is not None and explicit not in mode_map:
        raise _Stop("REVIEW_REQUIRED", "UNSUPPORTED_COUNTING_QUALIFIER", {"qualifier": explicit})
    policy_id = inp.counting_policy_id or rule.get("counting_policy_id")
    is_explicit_rule = rule.get("category") == "JUDICIAL_ORDER" or rule.get("rule_id") == "JUDICIAL_EXPLICIT_TERM"
    if is_explicit_rule and rule.get("allow_explicit_override"):
        if explicit:
            mode = mode_map[explicit]
            matching = [p for p in policies.values() if p.base_regime == context.base_regime and p.day_mode == mode]
            if len(matching) != 1:
                raise _Stop("UNRESOLVED", "COUNTING_POLICY_FOR_QUALIFIER_NOT_FOUND", {"regime": context.base_regime, "qualifier": explicit})
            policy_id = matching[0].policy_id
        elif not policy_id:
            policy_id = dict(REGIME_COUNTING_POLICY_IDS).get(context.base_regime)
    elif explicit and policy_id:
        declared = policies.get(str(policy_id))
        if declared is None:
            raise _Stop("UNRESOLVED", "COUNTING_POLICY_NOT_FOUND", {"policy_id": policy_id})
        if declared.day_mode != mode_map[explicit]:
            raise _Stop("REVIEW_REQUIRED", "COUNTING_QUALIFIER_CONFLICTS_WITH_RULE", {"qualifier": explicit, "policy_id": policy_id})
    if not is_explicit_rule and rule.get("counting_policy_id") and inp.counting_policy_id not in (None, rule.get("counting_policy_id")):
        raise _Stop("REVIEW_REQUIRED", "COUNTING_POLICY_CONFLICTS_WITH_RULE", {"rule_policy_id": rule.get("counting_policy_id"), "input_policy_id": inp.counting_policy_id})
    if not policy_id:
        raise _Stop("UNRESOLVED", "COUNTING_POLICY_UNRESOLVED", {"base_regime": context.base_regime})
    policy = policies.get(str(policy_id))
    if policy is None:
        raise _Stop("UNRESOLVED", "COUNTING_POLICY_NOT_FOUND", {"policy_id": policy_id})
    relevant = _date(inp.relevant_date)
    if not _in_effect(policy, relevant):
        raise _Stop("UNRESOLVED", "COUNTING_POLICY_OUTSIDE_EFFECTIVE_PERIOD", {"policy_id": policy.policy_id})
    if policy.base_regime != context.base_regime or policy.legal_domain != context.legal_domain:
        raise _Stop("REVIEW_REQUIRED", "COUNTING_POLICY_CONTEXT_MISMATCH", {"policy_id": policy.policy_id})
    return policy


def _next_business_day(calendar: Mapping[date, Any], day: date, *, purpose: str) -> date:
    current = day + timedelta(days=1)
    while True:
        entry = calendar.get(current)
        if entry is None:
            raise _Stop("UNRESOLVED", "CALENDAR_COVERAGE_MISSING", {"date": current.isoformat(), "purpose": purpose})
        if _record(entry).get("status") == "BUSINESS_DAY":
            return current
        current += timedelta(days=1)


def _communication_trigger(inp: DeadlineCalculationInput, context: LegalContext,
                           policies: Mapping[str, CommunicationPolicy], calendar: Mapping[date, Any]) -> tuple[date, date | None, CommunicationPolicy, dict[str, Any], str]:
    if not inp.communication_policy_id or not inp.communication_fact:
        raise _Stop("UNRESOLVED", "COMMUNICATION_TRIGGER_MISSING")
    policy = policies.get(inp.communication_policy_id)
    if policy is None:
        raise _Stop("UNRESOLVED", "COMMUNICATION_POLICY_NOT_FOUND", {"policy_id": inp.communication_policy_id})
    fact = _mapping(inp.communication_fact)
    if not fact.get("source_event_id"):
        raise _Stop("UNRESOLVED", "COMMUNICATION_SOURCE_EVENT_MISSING", {"policy_id": policy.policy_id})
    regime = context.base_regime
    if not policy.applies(regime=regime, requires_personal_notice=inp.requires_personal_notice):
        raise _Stop("REVIEW_REQUIRED", "COMMUNICATION_POLICY_NOT_APPLICABLE", {"policy_id": policy.policy_id})
    if fact.get("event_type") != policy.trigger_event_type or fact.get("communication_method") != policy.communication_method:
        raise _Stop("REVIEW_REQUIRED", "COMMUNICATION_FACT_METHOD_MISMATCH", {"policy_id": policy.policy_id})
    field_name = policy.trigger_date_field
    value = fact.get(field_name) if field_name else None
    resolution_method = "DECLARED_COMMUNICATION_DATE"
    if value:
        trigger = _date(value)
    elif policy.fallback_trigger_date_field and policy.trigger_derivation == "NEXT_BUSINESS_DAY_AFTER_FALLBACK":
        fallback = fact.get(policy.fallback_trigger_date_field)
        if not fallback:
            raise _Stop("UNRESOLVED", "COMMUNICATION_TRIGGER_MISSING", {
                "policy_id": policy.policy_id,
                "required_field": field_name,
                "fallback_field": policy.fallback_trigger_date_field,
            })
        trigger = _next_business_day(calendar, _date(fallback), purpose="COMMUNICATION_PUBLICATION_DATE")
        resolution_method = "DERIVED_FROM_AVAILABLE_ON_NEXT_BUSINESS_DAY"
    else:
        raise _Stop("UNRESOLVED", "COMMUNICATION_TRIGGER_MISSING", {"policy_id": policy.policy_id, "required_field": field_name})
    if not _in_effect(policy, trigger, from_field="effective_from", to_field="effective_to"):
        raise _Stop("REVIEW_REQUIRED", "COMMUNICATION_POLICY_OUTSIDE_EFFECTIVE_PERIOD", {"policy_id": policy.policy_id})
    counting_start = None
    if policy.counting_start_adjustment == "NEXT_BUSINESS_DAY_AFTER_TRIGGER":
        counting_start = _next_business_day(calendar, trigger, purpose="COMMUNICATION_COUNTING_START")
    elif policy.counting_start_adjustment not in (None, "NONE"):
        raise _Stop("REVIEW_REQUIRED", "UNSUPPORTED_COMMUNICATION_START_ADJUSTMENT", {"value": policy.counting_start_adjustment})
    return trigger, counting_start, policy, fact, resolution_method


def calculate_deadline(
    calculation: DeadlineCalculationInput,
    *,
    rules: Iterable[Mapping[str, Any]] | None = None,
    counting_policies: Iterable[CountingPolicy] = COUNTING_POLICIES,
    communication_policies: Iterable[CommunicationPolicy] = COMMUNICATION_POLICIES,
    suspension_policies: Iterable[SuspensionPolicy] = SUSPENSION_POLICIES,
) -> DeadlineCalculationResult:
    """Calculate calendar dates solely from the supplied structured contracts."""
    ctx = calculation.legal_context if isinstance(calculation.legal_context, LegalContext) else LegalContext.from_mapping(dict(calculation.legal_context))
    trace: list[dict[str, Any]] = []
    counted: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    applied: list[dict[str, Any]] = []
    calendar_version: str | None = None
    calendar_provenance: list[dict[str, Any]] = []
    rule: Mapping[str, Any] = {}
    counting: CountingPolicy | None = None
    communication: CommunicationPolicy | None = None
    communication_fact: dict[str, Any] = {}
    trigger: date | None = None
    trigger_resolution_method: str | None = None
    communication_counting_start: date | None = None
    counting_start: date | None = None
    due: date | None = None
    legal_basis: dict[str, Any] = {}
    provenance: dict[str, Any] = {}
    status = "CALCULATED"
    reason = None
    try:
        if calculation.resolved_rule_id == "JUDICIAL_EXPLICIT_TERM":
            # This identifier denotes an observed judicial fact, not a
            # regime-specific material rule in the catalog.
            if not calculation.resolved_rule_provenance.get("source_event_id"):
                raise _Stop("REVIEW_REQUIRED", "JUDICIAL_TERM_PROVENANCE_MISSING")
            rule = {"rule_id": "JUDICIAL_EXPLICIT_TERM", "rule_version": calculation.rule_version,
                    "category": "JUDICIAL_ORDER", "allow_explicit_override": True,
                    "legal_basis": {"kind": "OBSERVED_JUDICIAL_TERM"}, "authority": "observed judicial act"}
        else:
            rule = _find_rule(calculation.resolved_rule_id, calculation.rule_version,
                              rules if rules is not None else get_catalog())
        rule_version = str(rule.get("rule_version")) if rule.get("rule_version") else None
        rule_domain = rule.get("legal_domain")
        rule_regimes = rule.get("applicable_regimes", [rule.get("base_regime")])
        if calculation.resolved_rule_id != "JUDICIAL_EXPLICIT_TERM" and rule_domain and rule_domain != ctx.legal_domain:
            raise _Stop("REVIEW_REQUIRED", "RULE_CONTEXT_MISMATCH", {"field": "legal_domain"})
        if calculation.resolved_rule_id != "JUDICIAL_EXPLICIT_TERM" and rule.get("base_regime") and rule.get("base_regime") != ctx.base_regime and not set(rule_regimes or ()) & set(ctx.applicable_regimes):
            raise _Stop("REVIEW_REQUIRED", "RULE_CONTEXT_MISMATCH", {"field": "base_regime"})
        if calculation.term_value <= 0:
            raise _Stop("REVIEW_REQUIRED", "INVALID_TERM_VALUE", {"term_value": calculation.term_value})
        if calculation.term_unit not in {"DAYS", "BUSINESS_DAYS", "CONTINUOUS_DAYS"}:
            raise _Stop("UNRESOLVED", "UNSUPPORTED_TERM_UNIT", {"term_unit": calculation.term_unit})
        if calculation.resolved_rule_id != "JUDICIAL_EXPLICIT_TERM" and not _in_effect(type("Effective", (), {"effective_from": rule.get("effective_from"), "effective_to": rule.get("effective_to")})(), _date(calculation.relevant_date)):
            raise _Stop("UNRESOLVED", "RULE_OUTSIDE_EFFECTIVE_PERIOD", {"rule_id": calculation.resolved_rule_id})
        if calculation.resolved_rule_id != "JUDICIAL_EXPLICIT_TERM":
            rule_term = rule.get("term_value", rule.get("default_term_value"))
            if rule_term is not None and calculation.term_value != rule_term:
                raise _Stop("REVIEW_REQUIRED", "TERM_CONFLICTS_WITH_RULE", {"rule_term_value": rule_term, "input_term_value": calculation.term_value})
        policies = _policy_map(counting_policies, "policy_id")
        counting = _resolve_counting_policy(rule, calculation, ctx, policies)
        if counting.include_start is None or counting.include_end is None:
            raise _Stop("REVIEW_REQUIRED", "COUNTING_BOUNDARY_UNSPECIFIED", {"policy_id": counting.policy_id})
        if counting.include_end is not True:
            raise _Stop("REVIEW_REQUIRED", "COUNTING_END_BOUNDARY_UNSUPPORTED", {"policy_id": counting.policy_id, "include_end": counting.include_end})
        calendar, calendar_version, calendar_provenance = _calendar_index(calculation.calendar_entries, ctx)
        communication_map = _policy_map(communication_policies, "policy_id")
        trigger, communication_counting_start, communication, communication_fact, trigger_resolution_method = _communication_trigger(
            calculation, ctx, communication_map, calendar
        )
        suspensions = _policy_map(suspension_policies, "policy_id")
        active_suspensions: list[SuspensionPolicy] = []
        exception_resolutions = dict(calculation.applicable_suspension_exceptions)
        for suspension_id in counting.suspension_policy_ids:
            suspension = suspensions.get(suspension_id)
            if suspension is None:
                raise _Stop("UNRESOLVED", "SUSPENSION_POLICY_NOT_FOUND", {"policy_id": suspension_id})
            if suspension.base_regime != ctx.base_regime:
                continue
            active_suspensions.append(suspension)
        current = communication_counting_start if communication_counting_start is not None else (trigger if counting.include_start else trigger + timedelta(days=1))
        counting_start = current
        trace.append({"step": "TRIGGER", "date": trigger.isoformat(), "source_event_id": communication_fact.get("source_event_id"),
                      "source_field": communication.trigger_date_field, "method": trigger_resolution_method})
        trace.append({"step": "COUNTING_POLICY", "policy_id": counting.policy_id, "version": counting.policy_version,
                      "day_mode": counting.day_mode, "include_start": counting.include_start, "include_end": counting.include_end})
        if communication_counting_start is not None:
            excluded.append({"date": trigger.isoformat(), "reason": "COMMUNICATION_START_RULE",
                             "source": communication.policy_id, "policy_id": communication.policy_id})
            trace.append({"date": trigger.isoformat(), "action": "EXCLUDED", "reason": "COMMUNICATION_START_RULE",
                          "source": communication.policy_id, "counting_start": communication_counting_start.isoformat()})
        elif not counting.include_start:
            excluded.append({"date": trigger.isoformat(), "reason": "START_DATE",
                             "source": counting.policy_id, "policy_id": counting.policy_id})
            trace.append({"date": trigger.isoformat(), "action": "EXCLUDED", "reason": "START_DATE",
                          "source": counting.policy_id})
        guard = 0
        while len(counted) < calculation.term_value:
            guard += 1
            if guard > 20000:
                raise _Stop("REVIEW_REQUIRED", "CALCULATION_LIMIT_REACHED")
            day = current
            exclusion_reason: str | None = None
            source: Any = None
            for suspension in active_suspensions:
                if _period_contains(day, suspension):
                    selected = exception_resolutions.get(suspension.policy_id)
                    if suspension.exceptions:
                        if selected is None:
                            raise _Stop("REVIEW_REQUIRED", "SUSPENSION_EXCEPTION_UNRESOLVED", {"policy_id": suspension.policy_id, "date": day.isoformat()})
                        if selected != "NONE":
                            known = {item.get("exception_id") for item in suspension.exceptions}
                            if selected not in known:
                                raise _Stop("REVIEW_REQUIRED", "UNKNOWN_SUSPENSION_EXCEPTION", {"policy_id": suspension.policy_id, "exception": selected})
                            applied.append({"policy_id": suspension.policy_id, "policy_version": suspension.policy_version,
                                            "period": {"start": suspension.period_start, "end": suspension.period_end},
                                            "date": day.isoformat(), "exception": selected, "suspended": False,
                                            "legal_basis": suspension.legal_basis})
                            trace.append({"date": day.isoformat(), "action": "COUNTING_CONTINUES", "reason": "SUSPENSION_EXCEPTION", "policy_id": suspension.policy_id, "exception": selected})
                            continue
                    exclusion_reason, source = "SUSPENSION_POLICY", suspension
                    applied.append({"policy_id": suspension.policy_id, "policy_version": suspension.policy_version,
                                    "period": {"start": suspension.period_start, "end": suspension.period_end},
                                    "date": day.isoformat(), "exception": selected, "suspended": True,
                                    "legal_basis": suspension.legal_basis})
                    break
            if exclusion_reason is None and counting.day_mode == "BUSINESS":
                entry = calendar.get(day)
                if entry is None:
                    raise _Stop("UNRESOLVED", "CALENDAR_COVERAGE_MISSING", {"date": day.isoformat()})
                entry_data = _record(entry)
                if entry_data.get("status") != "BUSINESS_DAY":
                    exclusion_reason, source = str(entry_data.get("status") or "CALENDAR_STATUS_MISSING"), entry
            if exclusion_reason:
                record = {"date": day.isoformat(), "reason": exclusion_reason,
                          "source": getattr(source, "policy_id", None) or _record(source).get("official_source"),
                          "policy_id": getattr(source, "policy_id", None)}
                excluded.append(record)
                trace.append({"date": day.isoformat(), "action": "EXCLUDED", "reason": exclusion_reason,
                              "source": record["source"]})
            else:
                ordinal = len(counted) + 1
                counted.append({"date": day.isoformat(), "ordinal": ordinal})
                trace.append({"date": day.isoformat(), "action": "COUNTED", "ordinal": ordinal})
            current += timedelta(days=1)
        due = _date(counted[-1]["date"])
        if counting.expiry_adjustment in {"NEXT_BUSINESS_DAY_IF_SUNDAY_OR_HOLIDAY", "NEXT_BUSINESS_DAY_PER_CPC_224"}:
            while True:
                entry = calendar.get(due)
                if entry is None:
                    raise _Stop("UNRESOLVED", "CALENDAR_COVERAGE_MISSING", {"date": due.isoformat(), "purpose": "EXPIRY_ADJUSTMENT"})
                entry_data = _record(entry)
                if entry_data.get("status") == "BUSINESS_DAY":
                    break
                excluded.append({"date": due.isoformat(), "reason": entry_data.get("status"),
                                 "source": entry_data.get("official_source"), "purpose": "EXPIRY_ADJUSTMENT"})
                trace.append({"date": due.isoformat(), "action": "EXPIRY_ADJUSTED", "reason": entry_data.get("status")})
                due += timedelta(days=1)
            if due.isoformat() != counted[-1]["date"]:
                trace.append({"step": "EXPIRY_ADJUSTMENT", "due_date": due.isoformat(), "policy": counting.expiry_adjustment})
        elif counting.expiry_adjustment not in {"NONE", "UNSPECIFIED_BY_ART_12A", "COURT_EXTENSION_ONLY_UNDER_CLT_775_1"}:
            raise _Stop("REVIEW_REQUIRED", "UNSUPPORTED_EXPIRY_ADJUSTMENT", {"value": counting.expiry_adjustment})
        legal_basis = {"rule": rule.get("legal_basis"), "counting_policy": counting.legal_basis,
                       "communication_policy": communication.legal_basis,
                       "suspensions": [x.legal_basis for x in active_suspensions]}
        provenance = {"rule": {"authority": rule.get("authority"), "official_source": rule.get("official_source"), "verified_at": rule.get("verified_at")},
                      "resolved_rule_provenance": dict(calculation.resolved_rule_provenance),
                      "communication_fact": communication_fact.get("provenance", {}),
                      "communication_source_refs": communication_fact.get("source_refs", []),
                      "communication": {"policy_id": communication.policy_id, "version": communication.policy_version,
                                         "authority": communication.authority, "official_source": list(communication.official_source)},
                      "policies": {"counting": {"policy_id": counting.policy_id, "version": counting.policy_version,
                                                  "authority": counting.authority, "official_source": counting.official_source},
                                   "suspensions": [{"policy_id": s.policy_id, "version": s.policy_version,
                                                    "authority": s.authority, "official_source": s.official_source}
                                                   for s in active_suspensions]}}
    except _Stop as stop:
        status = stop.status
        reason = {"code": stop.code, **stop.detail}
    except (KeyError, TypeError, ValueError) as exc:
        status = "REVIEW_REQUIRED"
        reason = {"code": "INVALID_STRUCTURED_INPUT", "detail": str(exc)}
    rule_version = (str(rule.get("rule_version")) if rule and rule.get("rule_version") else calculation.rule_version)
    if rule and not legal_basis:
        legal_basis = {"rule": rule.get("legal_basis")}
        if counting:
            legal_basis["counting_policy"] = counting.legal_basis
        if communication:
            legal_basis["communication_policy"] = communication.legal_basis
    if rule and not provenance:
        provenance = {"rule": {"authority": rule.get("authority"), "official_source": rule.get("official_source"),
                                "verified_at": rule.get("verified_at")},
                      "resolved_rule_provenance": dict(calculation.resolved_rule_provenance),
                      "communication_fact": communication_fact.get("provenance", {}),
                      "communication_source_refs": communication_fact.get("source_refs", [])}
    return DeadlineCalculationResult(
        status=status, resolved_rule_id=calculation.resolved_rule_id, rule_version=rule_version,
        legal_domain=ctx.legal_domain, base_regime=ctx.base_regime, term_value=calculation.term_value,
        term_unit=calculation.term_unit, counting_policy_id=counting.policy_id if counting else None,
        counting_policy_version=counting.policy_version if counting else None,
        communication_policy_id=communication.policy_id if communication else calculation.communication_policy_id,
        communication_event_id=communication_fact.get("source_event_id") or None,
        trigger_date=trigger.isoformat() if trigger else None,
        trigger_resolution_method=trigger_resolution_method if trigger else None,
        counting_start_date=counting_start.isoformat() if counting_start else None,
        due_date=due.isoformat() if due else None, counted_days=tuple(counted), excluded_days=tuple(excluded),
        applied_suspensions=tuple(applied), calendar_version=calendar_version,
        calendar_provenance=tuple(calendar_provenance), calculation_trace=tuple(trace),
        legal_basis=legal_basis, provenance=provenance, reason=reason,
    )
