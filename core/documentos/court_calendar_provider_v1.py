"""Tribunal-neutral contracts for acquiring and normalizing court calendars.

Acquisition and parsing live outside the Deadline Engine. Providers accept an
audited structured extraction plus the raw snapshot that supports it; source
specific HTML/PDF scraping is deliberately left to separately reviewable
acquisition adapters.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping, Protocol, runtime_checkable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from core.documentos.deadline_policies_v1 import CourtCalendar

PARSER_CONTRACT_VERSION = "court-calendar-provider-contract-v1"


@dataclass(frozen=True)
class CalendarProviderRequest:
    court: str
    jurisdiction: str
    locality_unit: str
    start_date: str
    end_date: str
    forum: str | None = None
    unit: str | None = None
    system: str | None = None
    proceeding_medium: str | None = None

    def __post_init__(self) -> None:
        start, end = date.fromisoformat(self.start_date), date.fromisoformat(self.end_date)
        if start > end:
            raise ValueError("start_date deve ser anterior ou igual a end_date")


@dataclass(frozen=True)
class RawSourceSnapshot:
    source_url: str
    content: bytes
    fetched_at: str
    parser_version: str
    content_hash: str | None = None

    def __post_init__(self) -> None:
        digest = hashlib.sha256(self.content).hexdigest()
        if self.content_hash and self.content_hash != digest:
            raise ValueError("content_hash não corresponde aos bytes do snapshot")
        object.__setattr__(self, "content_hash", digest)


@runtime_checkable
class CourtCalendarProvider(Protocol):
    provider_id: str

    def provide(self, request: CalendarProviderRequest,
                records: tuple[Mapping[str, Any], ...]) -> tuple[CourtCalendar, ...]: ...


def validate_request(provider_court: str, request: CalendarProviderRequest) -> None:
    if request.court != provider_court:
        raise ValueError(f"provider {provider_court} não atende {request.court}")


def fetch_official_snapshot(url: str, *, allowed_hosts: tuple[str, ...],
                            parser_version: str, timeout_seconds: int = 20) -> RawSourceSnapshot:
    """Fetch exact HTTPS bytes; caller persists the returned snapshot before parsing."""
    parsed = urlparse(url)
    hosts = {host.lower() for host in allowed_hosts}
    if parsed.scheme != "https" or not parsed.hostname or parsed.hostname.lower() not in hosts:
        raise ValueError("fonte de calendário deve ser HTTPS e host oficial allowlisted")
    request = Request(url, headers={"User-Agent": "Themis-CourtCalendar/1.0"})
    with urlopen(request, timeout=timeout_seconds) as response:
        final_url = response.geturl()
        final = urlparse(final_url)
        if final.scheme != "https" or not final.hostname or final.hostname.lower() not in hosts:
            raise ValueError("redirect de snapshot saiu dos hosts oficiais allowlisted")
        content = response.read()
    return RawSourceSnapshot(final_url, content, datetime.now(timezone.utc).isoformat(timespec="seconds"), parser_version)


def normalize_records(*, provider_id: str, authority: str, source_url: str,
                      verified_at: str, version: str,
                      request: CalendarProviderRequest,
                      records: tuple[Mapping[str, Any], ...]) -> tuple[CourtCalendar, ...]:
    """Normalize explicit, source-reviewed rows; never infer omitted dates."""
    normalized: list[CourtCalendar] = []
    first, last = date.fromisoformat(request.start_date), date.fromisoformat(request.end_date)
    for row in records:
        day = date.fromisoformat(str(row["date"]))
        if not first <= day <= last:
            continue
        scope = str(row["scope"]).upper()
        if row.get("jurisdiction") not in (None, "*", request.jurisdiction):
            continue
        if row.get("court") not in (None, "*", request.court):
            continue
        if scope == "COMARCA" and row.get("locality_unit", request.locality_unit) != request.locality_unit:
            continue
        applicability = str(row.get("applicability", "ALL")).upper()
        if applicability not in {"ALL", "PHYSICAL", "ELECTRONIC"}:
            raise ValueError(f"applicability inválida: {applicability}")
        status = str(row["status"]).upper()
        if status not in {"BUSINESS_DAY", "HOLIDAY", "SUSPENDED", "RECESS"}:
            raise ValueError(f"status de calendário inválido: {status}")
        if scope not in {"NATIONAL", "STATE", "COURT", "COMARCA", "FORUM", "UNIT", "SYSTEM"}:
            raise ValueError(f"scope inválido: {scope}")
        default_jurisdiction = "*" if scope == "NATIONAL" else request.jurisdiction
        default_court = request.court if scope in {"COURT", "COMARCA", "FORUM", "UNIT", "SYSTEM"} else None
        normalized.append(CourtCalendar(
            jurisdiction=str(row.get("jurisdiction") or default_jurisdiction),
            court=row.get("court", default_court),
            locality_unit=(row.get("locality_unit") or
                           (request.locality_unit if scope == "COMARCA" else None)),
            date=day.isoformat(), status=status, scope=scope,
            official_source=source_url, verified_at=verified_at, version=version,
            source_type=row.get("source_type", "OFFICIAL_ACT"), authority=authority,
            act_number=row.get("act_number"), act_date=row.get("act_date"),
            applicability=applicability, proceeding_medium=row.get("proceeding_medium"),
            notes=row.get("notes"),
            provenance={"provider_id": provider_id, "source_row": dict(row),
                        "source_url": source_url, "parser_version": PARSER_CONTRACT_VERSION},
            forum=row.get("forum"), unit=row.get("unit"), system_id=row.get("system_id"),
        ))
    return tuple(sorted(normalized, key=lambda entry: (entry.date, entry.scope, entry.status)))
