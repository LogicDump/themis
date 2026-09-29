"""Versioned declarative LegalRule pack (no inference/calculation)."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, TypedDict

CATALOG_VERSION = "1.0.0"


class LegalDeadlineRule(TypedDict, total=False):
    rule_id: str
    rule_version: str
    legal_domain: str
    base_regime: str
    applicable_regimes: list[str]
    regime_constraints: dict[str, Any]
    procedure_classes: list[str]
    procedural_act_types: list[str]
    jurisdiction_scope: str
    recipient_roles: list[str]
    term_value: int | None
    default_term_value: int | None
    term_unit: str
    counting_policy_id: str
    communication_policy_id: str | None
    category: str
    precedence: int
    allow_explicit_override: bool
    legal_basis: dict[str, Any]
    authority: str
    official_source: str | None
    effective_from: str | None
    effective_to: str | None
    verified_at: str | None
    # Transitional V1 fields remain accepted while old packs are read.
    applicable_act_types: list[str]
    counting_type: str
    process_classes: list[str]
    procedures: list[str]

_VERIFIED = "2026-09-29"
_CPC_SOURCE = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm"
_CPP_SOURCE = "https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm"
_CPP_AMENDMENT = "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/lei/l11719.htm"
_CLT_SOURCE = "https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm"
_CLT_AMENDMENT = "https://www.planalto.gov.br/ccivil_03/leis/l9957.htm"
_JEC_SOURCE = "https://www.planalto.gov.br/ccivil_03/leis/l9099.htm"
_JEC_AMENDMENT = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13728.htm"


def _rule(rule_id: str, legal_domain: str, regime: str, category: str, act_types: list[str],
          term: int | None, article: str, official_source: str, effective_from: str,
          *, conditions: str | None = None, paragraph: str | None = None,
          procedure_classes: list[str] | None = None, allow_override: bool = False,
          communication_policy_id: str | None = None) -> LegalDeadlineRule:
    return {
        "rule_id": rule_id, "rule_version": "1.0.0", "legal_domain": legal_domain,
        "base_regime": regime, "applicable_regimes": [regime], "regime_constraints": {"allowed_regimes": [regime]},
        "procedure_classes": procedure_classes or [], "procedural_act_types": act_types,
        "jurisdiction_scope": "BR", "recipient_roles": [], "term_value": term,
        "default_term_value": term, "term_unit": "DAYS", "counting_policy_id": {
            "CPC": "CPC_BUSINESS_DAYS", "CPP": "CPP_CONTINUOUS_DAYS",
            "CLT": "CLT_BUSINESS_DAYS", "LAW_9099": "LAW_9099_BUSINESS_DAYS",
        }[regime], "communication_policy_id": communication_policy_id,
        "category": category, "precedence": 100 if category == "JUDICIAL_ORDER" else 50,
        "allow_explicit_override": allow_override,
        "legal_basis": {"statute": {"CPC": "Lei 13.105/2015", "CPP": "Decreto-Lei 3.689/1941",
                         "CLT": "Decreto-Lei 5.452/1943", "LAW_9099": "Lei 9.099/1995"}[regime],
                        "article": article, "paragraph": paragraph, "conditions": conditions},
        "authority": "Presidência da República", "official_source": official_source,
        "effective_from": effective_from, "effective_to": None, "verified_at": _VERIFIED,
    }


# This pack contains only provisions whose act and numeric term appear expressly
# in the official legislation. The CPC block is not a universal fallback.
RULES: tuple[LegalDeadlineRule, ...] = (
    _rule("JUDICIAL_EXPLICIT_TERM", "CIVIL", "CPC", "JUDICIAL_ORDER", ["*"], None,
          "218", _CPC_SOURCE, "2016-03-18", conditions="prazo judicial expresso válido; regra específica pode impedir override",
          allow_override=True),
    _rule("CPC_ART_218_P3_RESIDUAL", "CIVIL", "CPC", "RESIDUAL_DEFAULT", ["RESIDUAL_PARTY_ACT"], 5,
          "218", _CPC_SOURCE, "2016-03-18", paragraph="§ 3º",
          conditions="inexistindo preceito legal ou prazo determinado pelo juiz", allow_override=True),
    _rule("CPC_ART_437_P1_DOCUMENT_RESPONSE", "CIVIL", "CPC", "STATUTORY_SPECIFIC", ["DOCUMENT_RESPONSE"], 15,
          "437", _CPC_SOURCE, "2016-03-18", paragraph="§ 1º",
          conditions="juntada de documento requerida por uma das partes; ouvir a outra parte"),
    _rule("CPC_ART_350_REPLY_NEW_FACT", "CIVIL", "CPC", "STATUTORY_SPECIFIC", ["REPLY_NEW_FACT"], 15,
          "350", _CPC_SOURCE, "2016-03-18",
          conditions="réu alega fato impeditivo, modificativo ou extintivo do direito do autor"),
    _rule("CPC_ART_351_REPLY_PRELIMINARY", "CIVIL", "CPC", "STATUTORY_SPECIFIC", ["REPLY_PRELIMINARY"], 15,
          "351", _CPC_SOURCE, "2016-03-18",
          conditions="réu alega matéria enumerada no art. 337"),
    _rule("CPC_ART_335_CONTESTATION", "CIVIL", "CPC", "STATUTORY_SPECIFIC", ["CONTESTATION"], 15,
          "335", _CPC_SOURCE, "2016-03-18",
          conditions="termo inicial segue uma das hipóteses dos incisos I a III"),
    _rule("CPC_ART_1023_DECLARATORY_EMBARGOS", "CIVIL", "CPC", "STATUTORY_SPECIFIC", ["DECLARATORY_EMBARGOS"], 5,
          "1023", _CPC_SOURCE, "2016-03-18", conditions="oposição de embargos de declaração"),
    _rule("CPC_ART_1023_P2_EMBARGOS_RESPONSE", "CIVIL", "CPC", "STATUTORY_SPECIFIC", ["DECLARATORY_EMBARGOS_RESPONSE"], 5,
          "1023", _CPC_SOURCE, "2016-03-18", paragraph="§ 2º",
          conditions="eventual acolhimento puder implicar modificação da decisão embargada"),

    _rule("CPP_ART_382_DECLARATORY_EMBARGOS", "CRIMINAL", "CPP", "STATUTORY_SPECIFIC", ["CRIMINAL_DECLARATORY_EMBARGOS"], 2,
          "382", _CPP_SOURCE, "1942-01-01", conditions="sentença com obscuridade, ambiguidade, contradição ou omissão"),
    _rule("CPP_ART_396_WRITTEN_ANSWER", "CRIMINAL", "CPP", "STATUTORY_SPECIFIC", ["CRIMINAL_ANSWER"], 10,
          "396", _CPP_AMENDMENT, "2008-08-22", conditions="procedimentos ordinário e sumário; denúncia/queixa recebida e citação ordenada",
          procedure_classes=["CPP_ORDINARIO", "CPP_SUMARIO"]),

    _rule("CLT_ART_884_EXECUTION_EMBARGOS", "LABOR", "CLT", "STATUTORY_SPECIFIC", ["EXECUTION_EMBARGOS"], 5,
          "884", _CLT_SOURCE, "1943-11-10", conditions="execução garantida ou bens penhorados"),
    _rule("CLT_ART_897A_DECLARATORY_EMBARGOS", "LABOR", "CLT", "STATUTORY_SPECIFIC", ["LABOR_DECLARATORY_EMBARGOS"], 5,
          "897-A", _CLT_AMENDMENT, "2000-03-13", conditions="embargos contra sentença ou acórdão"),

    _rule("LAW_9099_ART_42_APPEAL", "SPECIAL_COURTS", "LAW_9099", "SPECIAL_PROCEDURE", ["SMALL_CLAIMS_APPEAL"], 10,
          "42", _JEC_SOURCE, "2018-11-01", conditions="recurso contra sentença; contado da ciência da sentença"),
    _rule("LAW_9099_ART_49_DECLARATORY_EMBARGOS", "SPECIAL_COURTS", "LAW_9099", "SPECIAL_PROCEDURE", ["SMALL_CLAIMS_DECLARATORY_EMBARGOS"], 5,
          "49", _JEC_SOURCE, "2018-11-01", conditions="embargos contra decisão; contado da ciência da decisão"),
)

RULES_NOT_INCLUDED = (
    {"rule_id": "CPP_ART_593_APPEAL", "reason": "O conjunto inicial já cobre dois prazos CPP; este item depende de classificar a hipótese recursal específica do art. 593."},
    {"rule_id": "CPP_ART_600_APPEAL_REASONS", "reason": "O próprio caput diferencia contravenções (3 dias) das demais hipóteses (8 dias), e o § 1º traz prazo distinto para assistente."},
    {"rule_id": "CLT_ART_895_ORDINARY_APPEAL", "reason": "Adiado para uma rodada de vigência/versionamento específico do dispositivo recursal."},
    {"rule_id": "CLT_ART_897_AGRAVO", "reason": "O caput reúne agravo de petição e de instrumento, com atos de origem distintos."},
)

RULE_FIELDS = frozenset({
    "rule_id", "rule_version", "legal_domain", "base_regime", "applicable_regimes",
    "regime_constraints", "procedure_classes", "procedural_act_types", "jurisdiction_scope",
    "recipient_roles", "term_value", "default_term_value", "term_unit", "counting_policy_id",
    "communication_policy_id", "category", "precedence", "allow_explicit_override",
    "legal_basis", "authority", "official_source", "effective_from", "effective_to", "verified_at",
})


def get_catalog() -> tuple[LegalDeadlineRule, ...]:
    """Return defensive copies in stable rule_id/version order."""
    return tuple(sorted((deepcopy(rule) for rule in RULES), key=lambda r: (r["rule_id"], r["rule_version"])))


def validate_rule(rule: LegalDeadlineRule | dict[str, Any]) -> None:
    # Old V1 pack keys remain accepted during migration. New entries use the
    # LegalRule vocabulary and point to policy IDs instead of embedding counting.
    legacy = "counting_type" in rule and "applicable_act_types" in rule
    required = {"rule_id", "rule_version", "category", "precedence", "legal_basis"}
    if not legacy:
        required |= {
            "legal_domain", "base_regime", "term_unit", "allow_explicit_override",
            "authority", "official_source", "effective_from", "effective_to", "verified_at",
        }
        if rule.get("default_term_value") is not None or rule.get("term_value") is not None:
            required.add("counting_policy_id")
    missing = required - rule.keys()
    if missing:
        raise ValueError(f"campos ausentes na regra: {', '.join(sorted(missing))}")
    if not isinstance(rule["legal_basis"], dict):
        raise ValueError("legal_basis deve ser estruturado")
    if rule.get("applicable_regimes") is not None and not isinstance(rule["applicable_regimes"], (list, tuple)):
        raise ValueError("applicable_regimes deve ser uma lista ordenada")


def validate_pack(rules: tuple[LegalDeadlineRule, ...] | list[LegalDeadlineRule]) -> None:
    seen: set[tuple[str, str]] = set()
    for rule in rules:
        validate_rule(rule)
        identity = (str(rule["rule_id"]), str(rule["rule_version"]))
        if identity in seen:
            raise ValueError("rule_id/rule_version duplicado")
        seen.add(identity)
