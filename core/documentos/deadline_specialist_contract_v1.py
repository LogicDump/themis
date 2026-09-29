from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

CONTEXT_SUFFICIENCY = {"SUFFICIENT", "NEEDS_CONTEXT", "AMBIGUOUS_REVIEW"}
CONTEXT_NEEDS = {
    "ANTECEDENT_PLEADING",
    "COMMUNICATION_EVENT",
    "PROCESS_PARTICIPANTS",
    "LEGAL_CONTEXT",
    "PROCEDURAL_ACT_CONTEXT",
    "SOURCE_DOCUMENT",
}
RECIPIENT_ROLES = {
    "PLAINTIFF", "DEFENDANT", "BOTH_PARTIES", "THIRD_PARTY", "PROSECUTOR",
    "EXPERT", "WITNESS", "COURT_AUXILIARY", "OTHER", "UNRESOLVED",
}
TERM_UNITS = {"DAYS", "BUSINESS_DAYS", "HOURS", "MONTHS", "DATE_CERTAIN", "UNSPECIFIED"}


@dataclass(frozen=True)
class ContextRequest:
    kind: str
    reason: str
    query_hint: str | None = None
    candidate_event_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in CONTEXT_NEEDS:
            raise ValueError(f"context kind inválido: {self.kind}")
        if not self.reason.strip():
            raise ValueError("context request exige reason")

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "reason": self.reason,
            "query_hint": self.query_hint,
            "candidate_event_ids": list(self.candidate_event_ids),
        }


@dataclass(frozen=True)
class DeadlineSpecialistOutput:
    operative_instruction: bool
    context_sufficiency: str
    procedural_act_type: str | None = None
    action_text: str | None = None
    recipient_text: str | None = None
    recipient_role: str = "UNRESOLVED"
    explicit_term_value: int | None = None
    explicit_term_unit: str = "UNSPECIFIED"
    trigger_text: str | None = None
    antecedent_source_event_id: str | None = None
    candidate_antecedent_event_ids: tuple[str, ...] = ()
    candidate_rule_ids: tuple[str, ...] = ()
    model_preferred_rule_id: str | None = None
    context_requests: tuple[ContextRequest, ...] = ()
    source_spans: tuple[dict[str, Any], ...] = ()
    confidence: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.context_sufficiency not in CONTEXT_SUFFICIENCY:
            raise ValueError("context_sufficiency inválido")
        if self.recipient_role not in RECIPIENT_ROLES:
            raise ValueError("recipient_role inválido")
        if self.explicit_term_unit not in TERM_UNITS:
            raise ValueError("explicit_term_unit inválido")
        if self.explicit_term_value is not None and self.explicit_term_value <= 0:
            raise ValueError("explicit_term_value deve ser positivo")
        if self.context_sufficiency == "SUFFICIENT" and self.context_requests:
            raise ValueError("SUFFICIENT não pode pedir contexto adicional")
        if self.context_sufficiency == "NEEDS_CONTEXT" and not self.context_requests:
            raise ValueError("NEEDS_CONTEXT exige pelo menos um context_request")
        if self.antecedent_source_event_id and self.antecedent_source_event_id in self.candidate_antecedent_event_ids:
            raise ValueError("antecedente resolvido não deve permanecer como candidato")
        for name, value in self.confidence.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0 or value > 1:
                raise ValueError(f"confidence inválida para {name}")

    @property
    def review_required(self) -> bool:
        return self.context_sufficiency != "SUFFICIENT"

    def as_dict(self) -> dict[str, Any]:
        return {
            "operative_instruction": self.operative_instruction,
            "context_sufficiency": self.context_sufficiency,
            "procedural_act_type": self.procedural_act_type,
            "action_text": self.action_text,
            "recipient_text": self.recipient_text,
            "recipient_role": self.recipient_role,
            "explicit_term_value": self.explicit_term_value,
            "explicit_term_unit": self.explicit_term_unit,
            "trigger_text": self.trigger_text,
            "antecedent_source_event_id": self.antecedent_source_event_id,
            "candidate_antecedent_event_ids": list(self.candidate_antecedent_event_ids),
            "candidate_rule_ids": list(self.candidate_rule_ids),
            "model_preferred_rule_id": self.model_preferred_rule_id,
            "context_requests": [item.as_dict() for item in self.context_requests],
            "source_spans": list(self.source_spans),
            "confidence": dict(self.confidence),
            "review_required": self.review_required,
        }


def context_request_kinds(output: DeadlineSpecialistOutput) -> set[str]:
    return {item.kind for item in output.context_requests}


def score_specialist_output(expected: DeadlineSpecialistOutput,
                            actual: DeadlineSpecialistOutput) -> dict[str, Any]:
    """Deterministic benchmark scorer. No legal inference happens here."""
    fields = (
        "operative_instruction", "context_sufficiency", "procedural_act_type",
        "recipient_role", "explicit_term_value", "explicit_term_unit",
        "antecedent_source_event_id", "model_preferred_rule_id",
    )
    field_results = {name: getattr(expected, name) == getattr(actual, name) for name in fields}
    expected_needs = context_request_kinds(expected)
    actual_needs = context_request_kinds(actual)
    need_recall = 1.0 if not expected_needs else len(expected_needs & actual_needs) / len(expected_needs)
    need_precision = 1.0 if not actual_needs else len(expected_needs & actual_needs) / len(actual_needs)
    dangerous_false_resolution = (
        expected.context_sufficiency != "SUFFICIENT"
        and actual.context_sufficiency == "SUFFICIENT"
    )
    return {
        "field_results": field_results,
        "field_accuracy": sum(field_results.values()) / len(field_results),
        "context_need_recall": need_recall,
        "context_need_precision": need_precision,
        "dangerous_false_resolution": dangerous_false_resolution,
        "safe_abstention": expected.context_sufficiency != "SUFFICIENT" and actual.context_sufficiency != "SUFFICIENT",
    }
