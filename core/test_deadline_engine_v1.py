from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta

import pytest

from core.documentos.deadline_engine_v1 import (
    CommunicationFact,
    DeadlineCalculationInput,
    calculate_deadline,
)
from core.documentos.deadline_policies_v1 import CourtCalendar


def ctx(domain: str, regime: str) -> dict:
    return {"legal_domain": domain, "base_regime": regime, "procedure_class": "SYNTHETIC",
            "applicable_regimes": [regime], "jurisdiction": "SYNTHETIC"}


def calendar_day(day: date, status: str) -> CourtCalendar:
    return CourtCalendar("SYNTHETIC", "SYNTHETIC_COURT", "SYNTHETIC_UNIT", day.isoformat(), status,
                         "SYNTHETIC_TEST_ONLY", "fixture://calendar", "2026-01-01", "fixture-v1")


def calendar_between(start: str, end: str, non_business: set[str] = frozenset()) -> tuple[CourtCalendar, ...]:
    current, finish = date.fromisoformat(start), date.fromisoformat(end)
    entries = []
    while current <= finish:
        entries.append(calendar_day(current, "HOLIDAY" if current.isoformat() in non_business else "BUSINESS_DAY"))
        current += timedelta(days=1)
    return tuple(entries)


def calc(regime: str, domain: str, *, trigger: str, term: int, rule="JUDICIAL_EXPLICIT_TERM",
         policy: str | None = None, calendar=(), qualifier=None, exceptions=None, personal=False,
         method="DJEN_PUBLICATION", published_on: str | None = None, event_type="PUBLICATION",
         term_unit="DAYS"):
    fact = CommunicationFact("pe_synthetic_1", event_type, method, source_refs=({"ref": "synthetic"},),
                             provenance={"fixture": True}, published_on=published_on or trigger)
    return calculate_deadline(DeadlineCalculationInput(
        legal_context=ctx(domain, regime), resolved_rule_id=rule, term_value=term, term_unit=term_unit,
        counting_policy_id=policy, communication_policy_id="DJEN_PUBLICATION",
        communication_fact=fact, calendar_entries=tuple(calendar), relevant_date=trigger,
        explicit_counting_qualifier=qualifier, requires_personal_notice=personal,
        applicable_suspension_exceptions=exceptions or {},
        resolved_rule_provenance={"source_event_id": "pe_order_synthetic", "source_refs": [{"fixture": True}]},
    ))


def test_cpc_business_counts_only_calendar_business_days_and_holiday():
    result = calc("CPC", "CIVIL", trigger="2026-03-02", term=3,
                  calendar=calendar_between("2026-03-03", "2026-03-06", {"2026-03-04"}))
    assert result.status == "CALCULATED"
    assert [x["date"] for x in result.counted_days] == ["2026-03-03", "2026-03-05", "2026-03-06"]
    assert result.due_date == "2026-03-06"
    assert any(x["reason"] == "HOLIDAY" for x in result.excluded_days)


def test_cpp_counts_intermediate_weekend_as_continuous_days():
    days = (
        calendar_day(date(2026, 3, 6), "BUSINESS_DAY"),
        calendar_day(date(2026, 3, 7), "HOLIDAY"),
        calendar_day(date(2026, 3, 8), "HOLIDAY"),
        calendar_day(date(2026, 3, 9), "BUSINESS_DAY"),
    )
    result = calc("CPP", "CRIMINAL", trigger="2026-03-05", term=3, calendar=days)
    assert result.status == "CALCULATED"
    assert [x["date"] for x in result.counted_days] == ["2026-03-06", "2026-03-07", "2026-03-08"]
    assert result.due_date == "2026-03-09"


def test_cpp_expiry_adjustment_uses_supplied_calendar_only():
    days = (calendar_day(date(2026, 3, 3), "BUSINESS_DAY"),
            calendar_day(date(2026, 3, 7), "HOLIDAY"), calendar_day(date(2026, 3, 8), "RECESS"),
            calendar_day(date(2026, 3, 9), "BUSINESS_DAY"))
    result = calc("CPP", "CRIMINAL", trigger="2026-03-02", term=5, calendar=days)
    assert result.status == "CALCULATED" and result.due_date == "2026-03-09"
    assert any(x.get("purpose") == "EXPIRY_ADJUSTMENT" for x in result.excluded_days)


def test_clt_business_policy_is_independent_of_cpc_policy():
    result = calc("CLT", "LABOR", trigger="2026-03-02", term=2,
                  calendar=calendar_between("2026-03-03", "2026-03-04"))
    assert result.status == "CALCULATED" and result.counting_policy_id == "CLT_BUSINESS_DAYS"
    assert result.due_date == "2026-03-04"


def test_law_9099_unspecified_boundaries_do_not_fall_back_to_cpc():
    result = calc("LAW_9099", "SPECIAL_COURTS", trigger="2026-01-05", term=5,
                  rule="LAW_9099_ART_49_DECLARATORY_EMBARGOS")
    assert result.status == "REVIEW_REQUIRED"
    assert result.reason["code"] == "COUNTING_BOUNDARY_UNSPECIFIED"
    assert result.counting_policy_id == "LAW_9099_BUSINESS_DAYS"


def test_cpc_suspension_policy_skips_recess_days():
    dates = calendar_between("2026-12-19", "2027-01-23")
    result = calc("CPC", "CIVIL", trigger="2026-12-18", term=3, calendar=dates)
    assert result.status == "CALCULATED" and result.due_date == "2027-01-22"
    assert any(x["policy_id"] == "CPC_ART_220_GENERAL" for x in result.applied_suspensions)


def test_cpp_recess_without_exception_resolution_requires_review():
    days = (
        calendar_day(date(2026, 12, 19), "HOLIDAY"),
        calendar_day(date(2026, 12, 20), "HOLIDAY"),
        calendar_day(date(2026, 12, 21), "BUSINESS_DAY"),
    )
    result = calc("CPP", "CRIMINAL", trigger="2026-12-18", term=3, calendar=days)
    assert result.status == "REVIEW_REQUIRED"
    assert result.reason["code"] == "SUSPENSION_EXCEPTION_UNRESOLVED"


def test_cpp_recess_with_structured_exception_counts_dates():
    days = (
        calendar_day(date(2026, 12, 19), "HOLIDAY"),
        calendar_day(date(2026, 12, 20), "HOLIDAY"),
        calendar_day(date(2026, 12, 21), "BUSINESS_DAY"),
        calendar_day(date(2026, 12, 23), "BUSINESS_DAY"),
    )
    result = calc("CPP", "CRIMINAL", trigger="2026-12-18", term=3, calendar=days,
                  exceptions={"CPP_ART_798A_RECESS": "INCISO_I"})
    assert result.status == "CALCULATED"
    assert [x["date"] for x in result.counted_days] == ["2026-12-21", "2026-12-22", "2026-12-23"]
    assert any(x["exception"] == "INCISO_I" and not x["suspended"] for x in result.applied_suspensions)


@pytest.mark.parametrize(("regime", "domain", "expected"), [
    ("CPC", "CIVIL", "CPC_BUSINESS_DAYS"),
    ("CPP", "CRIMINAL", "CPP_CONTINUOUS_DAYS"),
    ("CLT", "LABOR", "CLT_BUSINESS_DAYS"),
])
def test_explicit_judicial_term_uses_regime_registry(regime, domain, expected):
    days = calendar_between("2026-03-03", "2026-03-07")
    result = calc(regime, domain, trigger="2026-03-02", term=2, calendar=days)
    assert result.status == "CALCULATED" and result.counting_policy_id == expected


def test_structured_business_day_qualifier_is_not_erased():
    result = calc("CPC", "CIVIL", trigger="2026-03-02", term=2, qualifier="BUSINESS_DAYS",
                  calendar=calendar_between("2026-03-03", "2026-03-04"))
    assert result.status == "CALCULATED" and result.counting_policy_id == "CPC_BUSINESS_DAYS"


def test_business_days_structured_term_unit_selects_business_policy():
    result = calc("CPC", "CIVIL", trigger="2026-03-02", term=2, term_unit="BUSINESS_DAYS",
                  calendar=calendar_between("2026-03-03", "2026-03-04"))
    assert result.status == "CALCULATED" and result.counting_policy_id == "CPC_BUSINESS_DAYS"


def test_djen_derives_publication_and_start_from_available_on_for_cpp():
    fact = CommunicationFact(
        "pe_available", "PUBLICATION", "DJEN_PUBLICATION",
        available_on="2026-03-05",
        provenance={"fixture": True},
    )
    days = (
        calendar_day(date(2026, 3, 6), "BUSINESS_DAY"),
        calendar_day(date(2026, 3, 7), "HOLIDAY"),
        calendar_day(date(2026, 3, 8), "HOLIDAY"),
        calendar_day(date(2026, 3, 9), "BUSINESS_DAY"),
        calendar_day(date(2026, 3, 11), "BUSINESS_DAY"),
    )
    result = calculate_deadline(DeadlineCalculationInput(
        legal_context=ctx("CRIMINAL", "CPP"),
        resolved_rule_id="JUDICIAL_EXPLICIT_TERM",
        term_value=3,
        term_unit="DAYS",
        counting_policy_id=None,
        communication_policy_id="DJEN_PUBLICATION",
        communication_fact=fact,
        calendar_entries=days,
        relevant_date="2026-03-05",
        resolved_rule_provenance={"source_event_id": "pe_order_synthetic"},
    ))
    assert result.status == "CALCULATED"
    assert result.trigger_date == "2026-03-06"
    assert result.trigger_resolution_method == "DERIVED_FROM_AVAILABLE_ON_NEXT_BUSINESS_DAY"
    assert result.counting_start_date == "2026-03-09"
    assert [x["date"] for x in result.counted_days] == ["2026-03-09", "2026-03-10", "2026-03-11"]


def test_calendar_coverage_missing_and_communication_trigger_missing():
    incomplete = calc("CPC", "CIVIL", trigger="2026-03-02", term=2, calendar=())
    assert incomplete.status == "UNRESOLVED" and incomplete.reason["code"] == "CALENDAR_COVERAGE_MISSING"
    # Exercise a missing date field directly; the engine must not fill it.
    fact = CommunicationFact("pe_missing", "PUBLICATION", "DJEN_PUBLICATION")
    original = DeadlineCalculationInput(ctx("CIVIL", "CPC"), "JUDICIAL_EXPLICIT_TERM", 2, "DAYS", None,
        "DJEN_PUBLICATION", fact, calendar_between("2026-03-03", "2026-03-04"), "2026-03-02",
        resolved_rule_provenance={"source_event_id": "pe_order_synthetic"})
    missing = calculate_deadline(original)
    assert missing.status == "UNRESOLVED" and missing.reason["code"] == "COMMUNICATION_TRIGGER_MISSING"


def test_personal_notice_requirement_rejects_djen_policy():
    result = calc("CPC", "CIVIL", trigger="2026-01-05", term=2, personal=True)
    assert result.status == "REVIEW_REQUIRED" and result.reason["code"] == "COMMUNICATION_POLICY_NOT_APPLICABLE"


def test_repeated_identical_input_is_semantically_identical_and_has_no_time_of_day():
    args = dict(regime="CPC", domain="CIVIL", trigger="2026-03-02", term=2,
                calendar=calendar_between("2026-03-03", "2026-03-04"))
    first, second = calc(**args), calc(**args)
    assert asdict(first) == asdict(second)
    assert "due_at" not in asdict(first)
    assert first.due_date == "2026-03-04"


def test_material_rule_supplies_its_own_counting_policy():
    result = calc("CPC", "CIVIL", trigger="2026-03-02", term=15,
                  rule="CPC_ART_437_P1_DOCUMENT_RESPONSE", calendar=calendar_between("2026-03-03", "2026-03-31"))
    assert result.status == "CALCULATED" and result.counting_policy_id == "CPC_BUSINESS_DAYS"
