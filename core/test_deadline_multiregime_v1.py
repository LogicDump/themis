from __future__ import annotations

import pytest

from core.documentos.deadline_policies_v1 import CountingPolicy, validate_counting_policy
from core.documentos.legal_context_v1 import LegalContext
from core.documentos.deadline_rule_resolver_v1 import resolve_deadline_rule
from core.documentos.legal_deadline_rules_v1 import get_catalog, validate_rule


def context(domain, regime, regimes=None):
    return {"legal_domain": domain, "base_regime": regime, "procedure_class": "SYNTHETIC_CLASS",
            "applicable_regimes": regimes or [regime], "jurisdiction": "SYNTHETIC_COURT"}


def rule(rule_id, domain, regime, policy, **extra):
    return {"rule_id": rule_id, "rule_version": "1", "legal_domain": domain, "base_regime": regime,
            "applicable_regimes": [regime], "procedure_classes": ["SYNTHETIC_CLASS"],
            "procedural_act_types": ["SYNTHETIC_ACT"], "jurisdiction_scope": "SYNTHETIC_COURT",
            "recipient_roles": ["RESPONDENT"], "term_value": 5, "term_unit": "DAYS",
            "counting_policy_id": policy, "communication_policy_id": None,
            "category": "STATUTORY_SPECIFIC", "precedence": 50,
            "allow_explicit_override": False, "legal_basis": {"fixture": "synthetic"},
            "authority": "synthetic-fixture", "official_source": None,
            "effective_from": "2020-01-01", "effective_to": None, "verified_at": None, **extra}


def resolve(ctx, rules, **kwargs):
    return resolve_deadline_rule(legal_context=ctx, procedural_act_type="SYNTHETIC_ACT",
        recipient_role="RESPONDENT", relevant_date="2026-01-01", catalog=rules, **kwargs)


def test_civil_rule_rejected_for_criminal_and_reverse():
    cpc = rule("CPC_RULE", "CIVIL", "CPC", "CPC_BUSINESS_DAYS")
    cpp = rule("CPP_RULE", "CRIMINAL", "CPP", "CPP_CONTINUOUS_DAYS")
    assert resolve(context("CRIMINAL", "CPP"), [cpc], candidate_rule_ids=["CPC_RULE"])["resolved_rule_id"] is None
    assert resolve(context("CIVIL", "CPC"), [cpp], candidate_rule_ids=["CPP_RULE"])["resolved_rule_id"] is None


def test_special_regime_precedes_declared_base_regime():
    base = rule("BASE", "SPECIAL_COURTS", "CPC", "CPC_BUSINESS_DAYS", applicable_regimes=["CPC"], precedence=999)
    special = rule("SPECIAL", "SPECIAL_COURTS", "LAW_9099", "LAW_9099_BUSINESS_DAYS", applicable_regimes=["LAW_9099"], precedence=1)
    result = resolve(context("SPECIAL_COURTS", "CPC", ["LAW_9099", "CPC"]), [base, special], candidate_rule_ids=["BASE", "SPECIAL"])
    assert result["resolved_rule_id"] == "SPECIAL"


def test_counting_policy_is_separate_and_domains_can_coexist():
    cpc = rule("CPC", "CIVIL", "CPC", "CPC_BUSINESS_DAYS")
    cpp = rule("CPP", "CRIMINAL", "CPP", "CPP_CONTINUOUS_DAYS")
    clt = rule("CLT", "LABOR", "CLT", "CLT_BUSINESS_DAYS")
    policies = [
        CountingPolicy("CPC_BUSINESS_DAYS", "1", "CIVIL", "CPC", "BUSINESS", False, True, "NONE", (), {}, "2020-01-01", None, "https://fixture.invalid/cpc", "synthetic", "2026-09-29"),
        CountingPolicy("CPP_CONTINUOUS_DAYS", "1", "CRIMINAL", "CPP", "CONTINUOUS", False, True, "NONE", (), {}, "2020-01-01", None, "https://fixture.invalid/cpp", "synthetic", "2026-09-29"),
        CountingPolicy("CLT_BUSINESS_DAYS", "1", "LABOR", "CLT", "BUSINESS", False, True, "NONE", (), {}, "2020-01-01", None, "https://fixture.invalid/clt", "synthetic", "2026-09-29"),
    ]
    for policy in policies:
        validate_counting_policy(policy)
    for ctx, r, expected in [(context("CIVIL", "CPC"), cpc, "CPC_BUSINESS_DAYS"),
                             (context("CRIMINAL", "CPP"), cpp, "CPP_CONTINUOUS_DAYS"),
                             (context("LABOR", "CLT"), clt, "CLT_BUSINESS_DAYS")]:
        result = resolve(ctx, [r], candidate_rule_ids=[r["rule_id"]])
        assert result["counting_policy_id"] == expected
        assert result["term_value"] == 5 and result["term_unit"] == "DAYS"
        assert "due_at" not in result and result["explanation"]["calendar_consulted"] is False


def test_ml_incompatible_candidate_does_not_force_resolution():
    cpc = rule("CPC", "CIVIL", "CPC", "CPC_BUSINESS_DAYS")
    result = resolve(context("CRIMINAL", "CPP"), [cpc], candidate_rule_ids=[], model_preferred_rule_id="CPC")
    assert result["resolved_rule_id"] is None
    assert result["explanation"]["model_preference_authoritative"] is False


def test_explicit_term_needs_no_candidate_or_model():
    result = resolve(context("CRIMINAL", "CPP"), [], explicit_term_value=4, explicit_term_unit="DAYS")
    assert result["resolved_rule_id"] == "JUDICIAL_EXPLICIT_TERM"
    assert result["term_value"] == 4


def test_invalid_or_disallowed_explicit_term_requires_review():
    invalid = resolve(context("CIVIL", "CPC"), [], explicit_term_value=0, explicit_term_unit="DAYS")
    disallowed = resolve(context("CIVIL", "CPC"), [], explicit_term_value=3,
                         explicit_term_unit="DAYS", explicit_term_permitted=False)
    assert invalid["resolved_rule_id"] is None and invalid["review_required"]
    assert disallowed["resolved_rule_id"] is None and disallowed["review_required"]


def test_legal_context_requires_base_regime_in_applicable_regimes():
    with pytest.raises(ValueError):
        LegalContext(
            legal_domain="SPECIAL_COURTS",
            base_regime="CPC",
            procedure_class="SYNTHETIC_CLASS",
            applicable_regimes=("LAW_9099",),
            jurisdiction="SYNTHETIC_COURT",
        )


def test_new_rule_requires_official_provenance_fields():
    incomplete = rule("NEW", "CIVIL", "CPC", "CPC_BUSINESS_DAYS")
    incomplete.pop("official_source")
    with pytest.raises(ValueError):
        validate_rule(incomplete)


def test_effective_period_and_empty_legacy_pack():
    old = rule("OLD", "CIVIL", "CPC", "CPC_BUSINESS_DAYS", effective_to="2020-12-31")
    result = resolve(context("CIVIL", "CPC"), [old], candidate_rule_ids=["OLD"])
    assert result["resolved_rule_id"] is None
    assert result["explanation"]["rejected"][0]["reason"] == "OUTSIDE_EFFECTIVE_PERIOD"
    assert get_catalog()
    validate_rule({"rule_id": "V1", "rule_version": "1", "category": "RESIDUAL_DEFAULT",
                   "applicable_act_types": ["*"], "jurisdiction_scope": "*", "default_term_value": 5,
                   "term_unit": "DAYS", "counting_type": "LEGACY", "precedence": 1,
                   "allow_explicit_override": False, "legal_basis": {}})
