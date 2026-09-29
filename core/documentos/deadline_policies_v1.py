"""Independent temporal policy contracts; no date arithmetic or real calendars."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

DayMode = Literal["BUSINESS", "CONTINUOUS"]
CalendarStatus = Literal["BUSINESS_DAY", "HOLIDAY", "SUSPENDED", "RECESS"]

# Reserved identifiers only. No real policy records or legal content are implied.
COUNTING_POLICY_IDENTITIES = (
    "CPC_BUSINESS_DAYS", "CPP_CONTINUOUS_DAYS", "CLT_BUSINESS_DAYS", "LAW_9099_BUSINESS_DAYS",
)
COMMUNICATION_METHODS = (
    "DJEN_PUBLICATION", "PERSONAL_ELECTRONIC_NOTICE", "SERVICE", "HEARING_NOTIFICATION", "OTHER",
)


@dataclass(frozen=True)
class CountingPolicy:
    policy_id: str
    policy_version: str
    legal_domain: str
    base_regime: str
    day_mode: DayMode
    include_start: bool
    include_end: bool
    expiry_adjustment: str
    suspension_policy_ids: tuple[str, ...]
    legal_basis: dict[str, Any]
    effective_from: str | None
    effective_to: str | None
    official_source: str | None


@dataclass(frozen=True)
class CommunicationPolicy:
    policy_id: str
    applicable_regimes: tuple[str, ...]
    communication_method: str
    trigger_event_type: str
    legal_basis: dict[str, Any]
    effective_from: str | None
    effective_to: str | None
    official_source: str | None


@dataclass(frozen=True)
class CourtCalendar:
    jurisdiction: str
    court: str | None
    locality_unit: str | None
    date: str
    status: CalendarStatus
    scope: str
    official_source: str
    verified_at: str
    version: str


COUNTING_POLICIES: tuple[CountingPolicy, ...] = ()
COMMUNICATION_POLICIES: tuple[CommunicationPolicy, ...] = ()


def validate_counting_policy(policy: CountingPolicy) -> None:
    if policy.day_mode not in {"BUSINESS", "CONTINUOUS"}:
        raise ValueError("day_mode inválido")


def validate_communication_policy(policy: CommunicationPolicy) -> None:
    if not policy.policy_id or not policy.trigger_event_type:
        raise ValueError("CommunicationPolicy exige identidade e trigger_event_type")
