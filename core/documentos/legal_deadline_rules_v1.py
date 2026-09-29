"""Versioned declarative LegalRule pack (no inference/calculation)."""
from __future__ import annotations

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

# The initial catalog intentionally contains no asserted statutory values.
# Legal rule contents require authoritative review before they can be used.
RULES: tuple[LegalDeadlineRule, ...] = ()

RULE_FIELDS = frozenset({
    "rule_id", "rule_version", "legal_domain", "base_regime", "applicable_regimes",
    "regime_constraints", "procedure_classes", "procedural_act_types", "jurisdiction_scope",
    "recipient_roles", "term_value", "default_term_value", "term_unit", "counting_policy_id",
    "communication_policy_id", "category", "precedence", "allow_explicit_override",
    "legal_basis", "authority", "official_source", "effective_from", "effective_to", "verified_at",
})


def get_catalog() -> tuple[LegalDeadlineRule, ...]:
    """Return defensive copies in stable rule_id/version order."""
    return tuple(sorted((dict(rule) for rule in RULES), key=lambda r: (r["rule_id"], r["rule_version"])))


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
