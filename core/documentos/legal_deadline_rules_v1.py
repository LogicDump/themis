"""Versioned, declarative legal deadline rule catalog (no inference/calculation)."""
from __future__ import annotations

from typing import Any

CATALOG_VERSION = "1.0.0"

# The initial catalog intentionally contains no asserted statutory values.
# Legal rule contents require authoritative review before they can be used.
RULES: tuple[dict[str, Any], ...] = ()


def get_catalog() -> tuple[dict[str, Any], ...]:
    """Return defensive copies in stable rule_id/version order."""
    return tuple(sorted((dict(rule) for rule in RULES), key=lambda r: (r["rule_id"], r["rule_version"])))


def validate_rule(rule: dict[str, Any]) -> None:
    required = {
        "rule_id", "rule_version", "category", "name", "applicable_act_types",
        "jurisdiction_scope", "default_term_value", "term_unit", "counting_type",
        "precedence", "allow_explicit_override", "legal_basis", "authority",
        "official_source", "effective_from", "effective_to", "verified_at",
    }
    missing = required - rule.keys()
    if missing:
        raise ValueError(f"campos ausentes na regra: {', '.join(sorted(missing))}")
    if not isinstance(rule["legal_basis"], dict):
        raise ValueError("legal_basis deve ser estruturado")
