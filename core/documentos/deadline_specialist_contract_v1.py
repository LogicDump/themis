from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

CONTEXT_SUFFICIENCY = {"SUFFICIENT", "NEEDS_CONTEXT", "AMBIGUOUS_REVIEW"}
CONTEXT_PURPOSES = {"SEMANTIC_RESOLUTION", "TRIGGER_RESOLUTION", "RULE_RESOLUTION"}
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
    purpose: str = "SEMANTIC_RESOLUTION"
    query_hint: str | None = None
    candidate_event_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in CONTEXT_NEEDS:
            raise ValueError(f"context kind inválido: {self.kind}")
        if self.purpose not in CONTEXT_PURPOSES:
            raise ValueError(f"context purpose inválido: {self.purpose}")
        if not self.reason.strip():
            raise ValueError("context request exige reason")

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "reason": self.reason,
            "purpose": self.purpose,
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
    recipient_participant_ids: tuple[str, ...] = ()
    explicit_term_value: int | None = None
    explicit_term_unit: str = "UNSPECIFIED"
    explicit_term_date: str | None = None
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
        semantic_requests = tuple(item for item in self.context_requests if item.purpose == "SEMANTIC_RESOLUTION")
        if self.context_sufficiency == "SUFFICIENT" and semantic_requests:
            raise ValueError("SUFFICIENT não pode pedir contexto de resolução semântica")
        if self.context_sufficiency == "NEEDS_CONTEXT" and not semantic_requests:
            raise ValueError("NEEDS_CONTEXT exige context_request de SEMANTIC_RESOLUTION")
        if self.antecedent_source_event_id and self.antecedent_source_event_id in self.candidate_antecedent_event_ids:
            raise ValueError("antecedente resolvido não deve permanecer como candidato")
        for name, value in self.confidence.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0 or value > 1:
                raise ValueError(f"confidence inválida para {name}")

    @property
    def review_required(self) -> bool:
        """Compatibility alias: semantic review, not downstream trigger/rule lookup."""
        return self.context_sufficiency != "SUFFICIENT"

    @property
    def downstream_context_required(self) -> bool:
        return any(item.purpose in {"TRIGGER_RESOLUTION", "RULE_RESOLUTION"} for item in self.context_requests)

    def as_dict(self) -> dict[str, Any]:
        return {
            "operative_instruction": self.operative_instruction,
            "context_sufficiency": self.context_sufficiency,
            "procedural_act_type": self.procedural_act_type,
            "action_text": self.action_text,
            "recipient_text": self.recipient_text,
            "recipient_role": self.recipient_role,
            "recipient_participant_ids": list(self.recipient_participant_ids),
            "explicit_term_value": self.explicit_term_value,
            "explicit_term_unit": self.explicit_term_unit,
            "explicit_term_date": self.explicit_term_date,
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


def context_request_keys(output: DeadlineSpecialistOutput) -> set[tuple[str, str]]:
    return {(item.purpose, item.kind) for item in output.context_requests}


def score_specialist_output(expected: DeadlineSpecialistOutput,
                            actual: DeadlineSpecialistOutput) -> dict[str, Any]:
    """Deterministic benchmark scorer. No legal inference happens here."""
    fields = (
        "operative_instruction", "context_sufficiency", "procedural_act_type",
        "recipient_role", "recipient_participant_ids", "explicit_term_value", "explicit_term_unit", "explicit_term_date",
        "antecedent_source_event_id", "model_preferred_rule_id",
    )
    field_results = {name: getattr(expected, name) == getattr(actual, name) for name in fields}
    expected_needs = context_request_keys(expected)
    actual_needs = context_request_keys(actual)
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
