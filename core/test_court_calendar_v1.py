from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from core.documentos.court_calendar_composer_v1 import CalendarCompositionRequest, compose_calendar
from core.documentos.court_calendar_provider_v1 import (
    CalendarProviderRequest, RawSourceSnapshot,
)
from core.documentos.court_calendar_store_v1 import (
    MIGRATION_VERSION, load_events, migrate_connection, store_calendar_events, store_snapshot,
)
from core.documentos.deadline_engine_v1 import DeadlineCalculationInput, CommunicationFact, calculate_deadline
from core.documentos.deadline_policies_v1 import CourtCalendar
from core.documentos.providers.tjam_calendar_provider_v1 import parse_snapshot as parse_tjam
from core.documentos.providers.tjsp_calendar_provider_v1 import parse_snapshot as parse_tjsp

FIXTURES = Path(__file__).parent / "fixtures" / "court_calendars"


def fixture(name: str):
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    content = value["raw_excerpt"].encode("utf-8")
    snapshot = RawSourceSnapshot(value["source_url"], content, value["fetched_at"], value["parser_version"],
                                 hashlib.sha256(content).hexdigest())
    return value, snapshot


def test_provider_contract_is_tribunal_neutral():
    source = (Path(__file__).parent / "documentos" / "court_calendar_provider_v1.py").read_text(encoding="utf-8")
    assert "TJSP" not in source and "TJAM" not in source
    assert "class CourtCalendarProvider(Protocol)" in source


def _providers():
    tjsp_data, tjsp_snapshot = fixture("tjsp_piracaia_2026.json")
    tjam_data, tjam_snapshot = fixture("tjam_parintins_2026.json")
    tjsp_request = CalendarProviderRequest("TJSP", "SP", "Piracaia", "2026-08-31", "2026-08-31",
                                           proceeding_medium="PHYSICAL")
    tjam_request = CalendarProviderRequest("TJAM", "AM", "Parintins", "2026-05-14", "2026-10-15")
    return (
        parse_tjsp(tjsp_snapshot, tjsp_request, tuple(tjsp_data["records"])),
        parse_tjam(tjam_snapshot, tjam_request, tuple(tjam_data["records"])),
        tjsp_data, tjsp_snapshot, tjam_data, tjam_snapshot,
    )


def test_parintins_portaria_1320_dates_are_comarca_suspensions():
    _, tjam, *_ = _providers()
    by_date = {entry.date: entry for entry in tjam}
    assert set(by_date) == {"2026-05-14", "2026-06-29", "2026-07-16", "2026-10-15"}
    item = by_date["2026-07-16"]
    assert item.status == "SUSPENDED" and item.scope == "COMARCA"
    assert item.locality_unit == "Parintins" and item.act_number == "Portaria TJAM Presidência 1320/2026"
    assert "tjam.jus.br" in item.official_source


def test_parintins_local_suspension_does_not_leak_to_another_comarca():
    _, tjam, *_ = _providers()
    result = compose_calendar(CalendarCompositionRequest("TJAM", "AM", "Manaus", "2026-07-16", "2026-07-16"), tjam)
    assert result.entries == ()
    assert result.missing_dates == ("2026-07-16",)


def test_tjsp_physical_only_suspension_does_not_affect_electronic_case():
    tjsp, *_ = _providers()
    physical = compose_calendar(CalendarCompositionRequest("TJSP", "SP", "Piracaia", "2026-08-31", "2026-08-31",
                                                           proceeding_medium="PHYSICAL"), tjsp)
    electronic = compose_calendar(CalendarCompositionRequest("TJSP", "SP", "Piracaia", "2026-08-31", "2026-08-31",
                                                             proceeding_medium="ELECTRONIC"), tjsp)
    assert physical.entries[0].status == "SUSPENDED"
    assert electronic.entries == () and electronic.missing_dates == ("2026-08-31",)


def test_unit_suspension_does_not_affect_other_unit():
    event = CourtCalendar("SP", "TJSP", "Piracaia", "2026-03-03", "SUSPENDED", "UNIT", "fixture://unit",
                          "2026-03-01", "unit-v1", applicability="ALL", provenance={"fixture": True}, unit="1a-vara")
    same = compose_calendar(CalendarCompositionRequest("TJSP", "SP", "Piracaia", "2026-03-03", "2026-03-03", unit="1a-vara"), [event])
    other = compose_calendar(CalendarCompositionRequest("TJSP", "SP", "Piracaia", "2026-03-03", "2026-03-03", unit="2a-vara"), [event])
    assert same.entries[0].status == "SUSPENDED"
    assert other.entries == () and other.missing_dates == ("2026-03-03",)


@pytest.mark.parametrize("scope,fields", [
    ("NATIONAL", {"jurisdiction":"*"}),
    ("STATE", {"jurisdiction":"SP"}),
    ("COURT", {"jurisdiction":"SP", "court":"TJSP"}),
    ("COMARCA", {"jurisdiction":"SP", "court":"TJSP", "locality_unit":"Piracaia"}),
    ("FORUM", {"jurisdiction":"SP", "court":"TJSP", "locality_unit":"Piracaia", "forum":"F1"}),
    ("UNIT", {"jurisdiction":"SP", "court":"TJSP", "locality_unit":"Piracaia", "unit":"U1"}),
    ("SYSTEM", {"jurisdiction":"SP", "court":"TJSP", "system_id":"eproc"}),
])
def test_each_declared_scope_can_be_composed(scope, fields):
    row = {"date":"2026-03-03", "status":"SUSPENDED", "scope":scope,
           "official_source":"fixture://scope", "verified_at":"2026-03-01", "version":"scope-v1",
           "applicability":"ALL", **fields}
    request = CalendarCompositionRequest("TJSP", "SP", "Piracaia", "2026-03-03", "2026-03-03",
                                        forum="F1", unit="U1", system="eproc")
    result = compose_calendar(request, [row])
    assert len(result.entries) == 1 and result.entries[0].status == "SUSPENDED"


def test_store_retification_adds_version_and_preserves_old_provenance():
    (tjsp, _, tjsp_data, tjsp_snapshot, *_rest) = _providers()
    import sqlite3
    db = sqlite3.connect(":memory:"); db.row_factory = sqlite3.Row
    migrate_connection(db)
    snap_id = store_snapshot(db, tjsp_snapshot)
    first_id = store_calendar_events(db, tjsp, snapshot_id=snap_id)[0]
    revised_snapshot = RawSourceSnapshot(tjsp_snapshot.source_url, tjsp_snapshot.content + b" revised",
        "2026-09-30T12:00:00Z", tjsp_snapshot.parser_version)
    revised_snap_id = store_snapshot(db, revised_snapshot)
    revised = dict(tjsp[0].__dict__); revised["notes"] = "Retificação sintética para validar versionamento."
    revised["applicability"] = "ALL"; revised["provenance"] = {"revision_fixture": True}
    revised_id = store_calendar_events(db, [revised], snapshot_id=revised_snap_id)[0]
    history = load_events(db, jurisdiction="SP", include_history=True)
    assert first_id != revised_id and len(history) == 2
    assert [item["version_number"] for item in history] == [1, 2]
    assert history[0]["is_current"] is False and history[1]["is_current"] is True
    assert history[0]["provenance"]["provider_id"] == "TJSP_CALENDAR_V1"
    assert history[1]["source_snapshots"][0]["content_hash"] == revised_snapshot.content_hash
    assert history[1]["source_snapshots"][0]["parser_version"] == revised_snapshot.parser_version
    assert not db.execute("PRAGMA foreign_key_check").fetchall()


def test_store_migration_is_idempotent():
    import sqlite3
    db = sqlite3.connect(":memory:"); db.row_factory = sqlite3.Row
    first, second = migrate_connection(db), migrate_connection(db)
    assert first["migration_version"] == second["migration_version"] == MIGRATION_VERSION
    assert second["already_applied"] is True
    assert not db.execute("PRAGMA foreign_key_check").fetchall()


def test_composer_emits_one_effective_state_and_audits_conflict():
    broad = CourtCalendar("SP", None, None, "2026-03-03", "HOLIDAY", "STATE", "fixture://state", "2026-03-01", "state-v1")
    local = CourtCalendar("SP", "TJSP", "Piracaia", "2026-03-03", "SUSPENDED", "COMARCA", "fixture://local", "2026-03-01", "local-v1")
    result = compose_calendar(CalendarCompositionRequest("TJSP", "SP", "Piracaia", "2026-03-03", "2026-03-03"), [broad, local])
    assert len(result.entries) == 1 and result.entries[0].status == "SUSPENDED"
    assert result.conflicts[0]["conflict"] is True
    assert len(result.entries[0].provenance["composition"]["candidates"]) == 2


def test_coverage_gaps_remain_explicit_and_weekend_is_derived_not_official():
    result = compose_calendar(CalendarCompositionRequest("TJSP", "SP", "Piracaia", "2026-03-06", "2026-03-08"), [])
    assert result.missing_dates == ("2026-03-06",)
    assert [entry.status for entry in result.entries] == ["HOLIDAY", "HOLIDAY"]
    assert all(entry.source_type == "DERIVED_WEEKEND" and entry.official_source.startswith("algorithm:") for entry in result.entries)


def test_engine_uses_composed_dates_without_knowing_tribunal():
    days = [CourtCalendar("SP", "TJSP", "Piracaia", day.isoformat(), "BUSINESS_DAY", "COMARCA",
                          "fixture://base", "2026-03-01", "base-v1")
            for day in (date(2026, 3, 3), date(2026, 3, 4), date(2026, 3, 5))]
    holiday = CourtCalendar("SP", "TJSP", "Piracaia", "2026-03-04", "HOLIDAY", "COMARCA",
                            "fixture://holiday", "2026-03-01", "holiday-v1")
    request = CalendarCompositionRequest("TJSP", "SP", "Piracaia", "2026-03-03", "2026-03-05")
    calendars = [compose_calendar(request, days), compose_calendar(request, [*days, holiday])]

    def calculate(calendar):
        fact = CommunicationFact("event-synthetic", "PUBLICATION", "DJEN_PUBLICATION", published_on="2026-03-02")
        return calculate_deadline(DeadlineCalculationInput(
            legal_context={"legal_domain":"CIVIL", "base_regime":"CPC", "procedure_class":"TEST",
                           "applicable_regimes":["CPC"], "jurisdiction":"SP"},
            resolved_rule_id="JUDICIAL_EXPLICIT_TERM", term_value=2, term_unit="DAYS",
            counting_policy_id=None, communication_policy_id="DJEN_PUBLICATION", communication_fact=fact,
            calendar_entries=calendar.entries, relevant_date="2026-03-02",
            resolved_rule_provenance={"source_event_id":"judicial-event-synthetic", "source_refs":[{"fixture":True}]}))
    first, second = map(calculate, calendars)
    assert first.due_date == "2026-03-04" and second.due_date == "2026-03-05"
    assert first.calendar_version != second.calendar_version
    assert first.calendar_provenance[0]["provenance"]["composition"]["candidates"]
