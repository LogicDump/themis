from __future__ import annotations

from core.documentos.deadline_policies_v1 import (
    COMMUNICATION_POLICIES, COUNTING_POLICIES, SUSPENSION_POLICIES,
    validate_communication_policy, validate_counting_policy, validate_suspension_policy,
)
from core.documentos.deadline_rule_resolver_v1 import resolve_deadline_rule
from core.documentos.legal_deadline_rules_v1 import RULES, get_catalog, validate_rule


def test_counting_policy_mapping_is_regime_specific_and_versioned():
    expected = {"CPC": ("CIVIL", "BUSINESS"), "CPP": ("CRIMINAL", "CONTINUOUS"),
                "CLT": ("LABOR", "BUSINESS"), "LAW_9099": ("SPECIAL_COURTS", "BUSINESS")}
    actual = {p.base_regime: (p.legal_domain, p.day_mode) for p in COUNTING_POLICIES}
    assert actual == expected
    for policy in COUNTING_POLICIES:
        validate_counting_policy(policy)
        assert policy.policy_version and policy.official_source.startswith("https://www.planalto.gov.br/")
        assert policy.authority and policy.legal_basis and policy.effective_from and policy.verified_at
    jec = next(p for p in COUNTING_POLICIES if p.base_regime == "LAW_9099")
    assert jec.include_start is None and jec.include_end is None


def test_suspension_rules_are_separate_and_official():
    ids = {p.policy_id for p in SUSPENSION_POLICIES}
    assert ids == {"CPC_ART_220_GENERAL", "CPP_ART_798A_RECESS", "CLT_ART_775A_RECESS"}
    cpp = next(p for p in SUSPENSION_POLICIES if p.base_regime == "CPP")
    assert len(cpp.exceptions) == 3
    for policy in SUSPENSION_POLICIES:
        validate_suspension_policy(policy)


def test_djen_is_conditional_and_excludes_personal_notice():
    assert len(COMMUNICATION_POLICIES) == 1
    policy = COMMUNICATION_POLICIES[0]
    validate_communication_policy(policy)
    assert policy.policy_id == "DJEN_PUBLICATION"
    assert policy.applies(regime="CPC", requires_personal_notice=False)
    assert not policy.applies(regime="CPC", requires_personal_notice=True)
    assert all("atos.cnj.jus.br" in source for source in policy.official_source)


def test_all_material_rules_validate_and_point_to_pack_policy():
    assert get_catalog() and len(RULES) == len(get_catalog())
    policy_ids = {p.policy_id for p in COUNTING_POLICIES}
    ids = {r["rule_id"] for r in RULES}
    assert {"JUDICIAL_EXPLICIT_TERM", "CPC_ART_218_P3_RESIDUAL", "CPC_ART_437_P1_DOCUMENT_RESPONSE",
            "CPC_ART_350_REPLY_NEW_FACT", "CPC_ART_351_REPLY_PRELIMINARY", "CPC_ART_335_CONTESTATION",
            "CPC_ART_1023_DECLARATORY_EMBARGOS", "CPC_ART_1023_P2_EMBARGOS_RESPONSE"} <= ids
    assert {"CPP_ART_382_DECLARATORY_EMBARGOS", "CPP_ART_396_WRITTEN_ANSWER"} <= ids
    assert {"CLT_ART_884_EXECUTION_EMBARGOS", "CLT_ART_897A_DECLARATORY_EMBARGOS"} <= ids
    assert {"LAW_9099_ART_42_APPEAL", "LAW_9099_ART_49_DECLARATORY_EMBARGOS"} <= ids
    for rule in RULES:
        validate_rule(rule)
        assert rule["counting_policy_id"] in policy_ids
        assert rule["authority"] == "Presidência da República"
        assert rule["official_source"].startswith("https://www.planalto.gov.br/")
        assert rule["legal_basis"] and rule["effective_from"] and rule["verified_at"]
        assert "due_at" not in rule


def test_explicit_judicial_term_is_not_cpc_exclusive():
    cases = [
        ({"legal_domain": "CIVIL", "base_regime": "CPC", "applicable_regimes": ["CPC"], "jurisdiction": "BR"}, "CPC_BUSINESS_DAYS"),
        ({"legal_domain": "CRIMINAL", "base_regime": "CPP", "applicable_regimes": ["CPP"], "jurisdiction": "BR"}, None),
        ({"legal_domain": "LABOR", "base_regime": "CLT", "applicable_regimes": ["CLT"], "jurisdiction": "BR"}, None),
    ]
    for context, expected_policy in cases:
        result = resolve_deadline_rule(
            legal_context=context,
            procedural_act_type="ANY",
            explicit_term_value=5,
            explicit_term_unit="DAYS",
            catalog=get_catalog(),
        )
        assert result["resolved_rule_id"] == "JUDICIAL_EXPLICIT_TERM"
        assert result["term_value"] == 5
        assert result["counting_policy_id"] == expected_policy


def test_resolver_remains_pure_with_material_pack_and_explicit_term_is_ml_independent():
    context = {"legal_domain": "CIVIL", "base_regime": "CPC", "applicable_regimes": ["CPC"], "jurisdiction": "BR"}
    explicit = resolve_deadline_rule(legal_context=context, procedural_act_type="ANY", explicit_term_value=3,
        explicit_term_unit="DAYS", catalog=get_catalog())
    assert explicit["resolved_rule_id"] == "JUDICIAL_EXPLICIT_TERM"
    assert explicit["counting_policy_id"] == "CPC_BUSINESS_DAYS"
    assert "due_at" not in explicit and explicit["explanation"]["calendar_consulted"] is False

    personal_notice = next(p for p in COMMUNICATION_POLICIES if p.policy_id == "DJEN_PUBLICATION")
    assert not personal_notice.applies(regime="CPP", requires_personal_notice=True)
