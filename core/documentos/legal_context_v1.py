"""Structured, source-neutral legal context for temporal resolution."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

LEGAL_DOMAINS = frozenset({"CIVIL", "CRIMINAL", "LABOR", "SPECIAL_COURTS", "ADMINISTRATIVE", "OTHER"})


@dataclass(frozen=True)
class LegalContext:
    legal_domain: str
    base_regime: str
    procedure_class: str | None
    applicable_regimes: tuple[str, ...]
    jurisdiction: str | None
    procedural_phase: str | None = None

    def __post_init__(self) -> None:
        if self.legal_domain not in LEGAL_DOMAINS:
            raise ValueError("legal_domain inválido")
        if not self.base_regime.strip():
            raise ValueError("base_regime obrigatório")
        if not self.applicable_regimes:
            raise ValueError("applicable_regimes não pode ser vazio")
        if len(set(self.applicable_regimes)) != len(self.applicable_regimes):
            raise ValueError("applicable_regimes não pode conter duplicatas")
        if self.base_regime not in self.applicable_regimes:
            raise ValueError("base_regime deve constar em applicable_regimes")

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "LegalContext":
        """Accept the new contract and legacy process_context keys during rollout."""
        return cls(
            legal_domain=str(value.get("legal_domain") or "OTHER").upper(),
            base_regime=str(value.get("base_regime") or "OTHER").upper(),
            procedure_class=value.get("procedure_class", value.get("process_class")),
            applicable_regimes=tuple(str(x).upper() for x in value.get("applicable_regimes", [value.get("base_regime", "OTHER")]) if x),
            jurisdiction=value.get("jurisdiction"),
            procedural_phase=value.get("procedural_phase"),
        )

    def as_dict(self) -> dict[str, Any]:
        return {"legal_domain": self.legal_domain, "base_regime": self.base_regime,
                "procedure_class": self.procedure_class, "applicable_regimes": list(self.applicable_regimes),
                "jurisdiction": self.jurisdiction, "procedural_phase": self.procedural_phase}
