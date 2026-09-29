"""Compose date-level court calendars with explicit scope precedence/provenance."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
import hashlib
import json
from typing import Any, Iterable, Mapping

from core.documentos.deadline_policies_v1 import CourtCalendar

# Declared precedence: a blocking status beats a business-day declaration;
# within the same status, narrower scope wins. Every tie remains in provenance.
STATUS_PRECEDENCE = {"BUSINESS_DAY": 10, "HOLIDAY": 20, "RECESS": 30, "SUSPENDED": 40}
SCOPE_PRECEDENCE = {"NATIONAL": 10, "STATE": 20, "COURT": 30, "COMARCA": 40,
                    "FORUM": 50, "UNIT": 60, "SYSTEM": 70}
APPLICABILITY = frozenset({"ALL", "PHYSICAL", "ELECTRONIC"})


@dataclass(frozen=True)
class CalendarCompositionRequest:
    court: str
    jurisdiction: str
    locality_unit: str
    start_date: str
    end_date: str
    forum: str | None = None
    unit: str | None = None
    system: str | None = None
    proceeding_medium: str | None = None


@dataclass(frozen=True)
class CalendarComposition:
    entries: tuple[CourtCalendar, ...]
    missing_dates: tuple[str, ...]
    conflicts: tuple[dict[str, Any], ...]
    coverage_complete: bool
    precedence: dict[str, Any]
    calendar_version: str


def _row(value: Any) -> dict[str, Any]:
    return asdict(value) if hasattr(value, "__dataclass_fields__") else dict(value)


def _scope_matches(row: Mapping[str, Any], request: CalendarCompositionRequest) -> bool:
    scope = str(row.get("scope", "")).upper()
    if scope not in SCOPE_PRECEDENCE:
        return False
    if row.get("jurisdiction") not in (None, "*", request.jurisdiction):
        return False
    if row.get("court") not in (None, "*", request.court):
        return False
    if scope == "NATIONAL":
        return True
    if scope == "STATE":
        return True
    if scope == "COURT":
        return row.get("court") in (None, "*", request.court)
    if scope == "COMARCA":
        return row.get("locality_unit") == request.locality_unit
    if scope == "FORUM":
        return bool(request.forum) and row.get("locality_unit") == request.locality_unit and row.get("forum") == request.forum
    if scope == "UNIT":
        return bool(request.unit) and row.get("locality_unit") == request.locality_unit and row.get("unit") == request.unit
    return bool(request.system) and row.get("system_id", row.get("system")) == request.system


def _applicability_matches(row: Mapping[str, Any], medium: str | None) -> bool | None:
    applicability = str(row.get("applicability", "ALL")).upper()
    if applicability not in APPLICABILITY:
        return None
    if applicability == "ALL":
        return True
    if medium is None:
        return None
    return applicability == medium.upper()


def compose_calendar(request: CalendarCompositionRequest,
                     events: Iterable[CourtCalendar | Mapping[str, Any]]) -> CalendarComposition:
    start, end = date.fromisoformat(request.start_date), date.fromisoformat(request.end_date)
    if start > end:
        raise ValueError("start_date deve ser anterior ou igual a end_date")
    by_date: dict[str, list[dict[str, Any]]] = {}
    uncertain: set[str] = set()
    for raw in events:
        row = _row(raw)
        day = date.fromisoformat(str(row["date"]))
        if not start <= day <= end or not _scope_matches(row, request):
            continue
        applies = _applicability_matches(row, request.proceeding_medium)
        if applies is None:
            uncertain.add(day.isoformat())
        elif applies:
            by_date.setdefault(day.isoformat(), []).append(row)

    source_versions = sorted({str(row.get("event_version_id") or row.get("version") or
                                   (row.get("provenance") or {}).get("version") or "unknown")
                              for rows in by_date.values() for row in rows})
    version_material = {"request": asdict(request), "source_versions": source_versions,
                        "events": sorted((str(row.get("event_version_id") or row.get("version") or ""),
                                          str(row.get("date")), str(row.get("status")),
                                          str(row.get("scope")), str(row.get("applicability", "ALL")),
                                          hashlib.sha256(json.dumps(row, sort_keys=True, default=str,
                                              separators=(",", ":")).encode("utf-8")).hexdigest())
                                         for rows in by_date.values() for row in rows)}
    calendar_version = "calendar-composition-v1:" + hashlib.sha256(
        json.dumps(version_material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:20]

    effective: list[CourtCalendar] = []
    conflicts: list[dict[str, Any]] = []
    missing: list[str] = []
    current = start
    while current <= end:
        key = current.isoformat()
        rows = by_date.get(key, [])
        # Weekend is an ephemeral deterministic classification, never persisted
        # as an official source event and never labelled as one.
        if current.weekday() >= 5:
            rows = [*rows, {"jurisdiction": request.jurisdiction, "court": request.court,
                            "locality_unit": request.locality_unit, "date": key, "status": "HOLIDAY",
                            "scope": "NATIONAL", "official_source": "algorithm:iso-weekend-v1",
                            "verified_at": "derived", "version": calendar_version,
                            "source_type": "DERIVED_WEEKEND", "authority": "deterministic calendar composer",
                            "applicability": "ALL", "notes": "Fim de semana derivado por weekday ISO; não é evento oficial persistido.",
                            "provenance": {"derivation": "weekday() in {5,6}"}}]
        if not rows:
            missing.append(key)
            current += timedelta(days=1)
            continue
        ordered = sorted(rows, key=lambda row: (
            STATUS_PRECEDENCE.get(str(row.get("status", "")).upper(), -1),
            SCOPE_PRECEDENCE.get(str(row.get("scope", "")).upper(), -1),
            str(row.get("official_source", "")), str(row.get("act_number", "")),
        ), reverse=True)
        winner = ordered[0]
        descriptions = [{"scope": row.get("scope"), "status": row.get("status"),
                         "applicability": row.get("applicability", "ALL"),
                         "official_source": row.get("official_source"), "act_number": row.get("act_number"),
                         "version": row.get("version"), "provenance": row.get("provenance")}
                        for row in ordered]
        different = len({(row.get("status"), row.get("scope"), row.get("applicability", "ALL")) for row in rows}) > 1
        conflict = {"date": key, "winner": descriptions[0], "candidates": descriptions,
                    "precedence_applied": {"status": STATUS_PRECEDENCE, "scope": SCOPE_PRECEDENCE}}
        if len(rows) > 1:
            conflict["conflict"] = different
            conflicts.append(conflict)
        provenance = dict(winner.get("provenance") or {})
        provenance["composition"] = {"precedence_applied": {"status": STATUS_PRECEDENCE, "scope": SCOPE_PRECEDENCE},
                                      "candidates": descriptions, "conflict": different}
        effective.append(CourtCalendar(
            jurisdiction=str(winner.get("jurisdiction") or request.jurisdiction), court=winner.get("court"),
            locality_unit=winner.get("locality_unit"), date=key, status=winner["status"],
            scope=winner["scope"], official_source=winner["official_source"],
            verified_at=str(winner.get("verified_at", "")), version=calendar_version,
            source_type=winner.get("source_type"), authority=winner.get("authority"),
            act_number=winner.get("act_number"), act_date=winner.get("act_date"),
            applicability=winner.get("applicability", "ALL"), proceeding_medium=winner.get("proceeding_medium"),
            notes=winner.get("notes"), provenance=provenance, forum=winner.get("forum"),
            unit=winner.get("unit"), system_id=winner.get("system_id"),
        ))
        current += timedelta(days=1)
    for key in sorted(uncertain):
        if key not in {entry.date for entry in effective} and key not in missing:
            missing.append(key)
    missing.sort()
    return CalendarComposition(tuple(effective), tuple(missing), tuple(conflicts), not missing,
        {"status": STATUS_PRECEDENCE, "scope": SCOPE_PRECEDENCE,
         "statement": "Blocking status wins; ties resolve to narrower scope. All candidates remain in provenance."},
        calendar_version)
