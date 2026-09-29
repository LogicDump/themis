from __future__ import annotations

from core.documentos.deadline_rule_resolver_v1 import resolve_deadline_rule


def rule(rule_id, category, **kwargs):
    return {"rule_id": rule_id, "rule_version": "1", "category": category, "name": rule_id,
            "applicable_act_types": ["REPLY"], "jurisdiction_scope": "*", "default_term_value": 7,
            "term_unit": "DAYS", "counting_type": "UNSPECIFIED", "precedence": 1,
            "allow_explicit_override": False, "legal_basis": {"reference": "fixture"},
            "effective_from": "2020-01-01", "effective_to": None, **kwargs}


def run(catalog, **kwargs):
    return resolve_deadline_rule(process_context={"jurisdiction": "XX", "process_class": "CIVIL"},
        procedural_act_type="REPLY", relevant_date="2026-01-01", catalog=catalog, **kwargs)


def test_specific_rule_beats_residual_and_stable():
    catalog = [rule("R", "RESIDUAL_DEFAULT"), rule("S", "STATUTORY_SPECIFIC", precedence=80)]
    args = {"candidate_rule_ids": ["R", "S"]}
    assert run(catalog, **args) == run(catalog, **args)
    assert run(catalog, **args)["resolved_rule_id"] == "S"


def test_rejects_expired_or_wrong_act_and_ml_preference_is_only_hypothesis():
    catalog = [rule("OLD", "STATUTORY_SPECIFIC", effective_to="2020-12-31"),
               rule("OTHER", "STATUTORY_SPECIFIC", applicable_act_types=["APPEAL"])]
    result = run(catalog, candidate_rule_ids=[], model_preferred_rule_id="OLD")
    assert result["resolved_rule_id"] is None
    assert {x["reason"] for x in result["explanation"]["rejected"]} == {"OUTSIDE_EFFECTIVE_PERIOD"}


def test_explicit_term_only_when_explicit_rule_allows_override():
    catalog = [rule("J", "JUDICIAL_ORDER", allow_explicit_override=True)]
    result = run(catalog, candidate_rule_ids=["J"], explicit_term_value=3, explicit_term_unit="DAYS")
    assert result["resolved_rule_id"] == "J"
    assert result["term_value"] == 3
    assert "due_at" not in result


def test_explicit_term_does_not_depend_on_ml_candidate_nomination():
    catalog = [rule("J", "JUDICIAL_ORDER", applicable_act_types=["*"], allow_explicit_override=True)]
    result = run(catalog, candidate_rule_ids=[], explicit_term_value=9, explicit_term_unit="BUSINESS_DAYS")
    assert result["resolved_rule_id"] == "J"
    assert result["resolution_method"] == "JUDICIAL_EXPLICIT_TERM"
    assert result["term_value"] == 9


def test_hard_recipient_constraint():
    catalog = [rule("S", "STATUTORY_SPECIFIC", recipient_roles=["RESPONDENT"])]
    result = run(catalog, candidate_rule_ids=["S"], recipient_role="CLAIMANT")
    assert result["resolved_rule_id"] is None
    assert result["explanation"]["rejected"] == [{"rule_id": "S", "reason": "RECIPIENT_ROLE"}]
