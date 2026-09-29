from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from urllib.parse import urlencode

import pytest

from core.documentos.court_calendar_composer_v1 import CalendarCompositionRequest, compose_calendar
from core.documentos.court_calendar_provider_v1 import RawSourceSnapshot
from core.documentos.court_calendar_store_v1 import migrate_connection
from core.documentos.providers.tjsp_calendar_acquisition_v1 import (
    HOLIDAYS_ENDPOINT, INSTITUTIONAL_SOURCE, PARSER_VERSION, SUSPENSIONS_ENDPOINT,
    TjspAcquisitionRequest, UnclassifiedCalendarDescription, acquire_tjsp_calendar,
    parse_holidays, parse_suspensions,
)

FIXTURES = Path(__file__).parent / "fixtures" / "court_calendars"
REQUEST = TjspAcquisitionRequest("Piracaia", "", 2026)


def snapshot_for(endpoint: str) -> RawSourceSnapshot:
    name = "feriados" if endpoint == HOLIDAYS_ENDPOINT else "suspensoes"
    content = (FIXTURES / f"tjsp_piracaia_2026_{name}.raw.json").read_bytes()
    meta = json.loads((FIXTURES / f"tjsp_piracaia_2026_{name}.meta.json").read_text(encoding="utf-8-sig"))
    assert meta["endpoint"] == endpoint
    return RawSourceSnapshot(
        endpoint + "?" + urlencode(meta["request_params"]), content, meta["fetched_at"],
        meta["parser_version"], hashlib.sha256(content).hexdigest(), meta["request_params"],
    )


def test_official_golden_holidays_use_text_date_and_comarca_scope():
    events = parse_holidays(snapshot_for(HOLIDAYS_ENDPOINT), REQUEST)
    indexed = {(item.date, item.notes): item for item in events}
    santo = indexed[("2026-06-13", "SANTO ANTÔNIO")]
    fundacao = indexed[("2026-06-16", "FUNDAÇÃO DA CIDADE E SÃO JULIANO")]
    assert santo.status == fundacao.status == "HOLIDAY"
    assert santo.scope == fundacao.scope == "COMARCA"
    assert santo.locality_unit == "Piracaia"
    assert santo.official_source == INSTITUTIONAL_SOURCE
    assert santo.provenance["data_original"] == "13/06/2026"
    assert santo.provenance["endpoint"] == HOLIDAYS_ENDPOINT
    assert "DataFeriado" in santo.provenance["raw_json_record"]


def test_holiday_date_ignores_dotnet_timestamp():
    snapshot = snapshot_for(HOLIDAYS_ENDPOINT)
    payload = json.loads(snapshot.content)
    row = next(row for row in payload["data"] if row["Descricao"] == "SANTO ANTÔNIO")
    row["DataFeriado"] = "/Date(0)/"
    altered = RawSourceSnapshot(snapshot.source_url, json.dumps(payload, ensure_ascii=False).encode(),
                                snapshot.fetched_at, snapshot.parser_version,
                                request_params=snapshot.request_params)
    event = next(item for item in parse_holidays(altered, REQUEST) if item.notes == "SANTO ANTÔNIO")
    assert event.date == "2026-06-13"


def test_suspension_intervals_expand_using_data_text_and_keep_originals():
    events = parse_suspensions(snapshot_for(SUSPENSIONS_ENDPOINT), REQUEST)
    recess = [item for item in events if item.status == "RECESS"]
    suspended = [item for item in events if item.status == "SUSPENDED"]
    assert len(recess) == 6 and [item.date for item in recess] == [f"2026-01-{day:02d}" for day in range(1, 7)]
    assert len(suspended) == 14 and suspended[0].date == "2026-01-07" and suspended[-1].date == "2026-01-20"
    item = suspended[0]
    assert item.scope == "COMARCA" and item.locality_unit == "Piracaia"
    assert item.provenance["data_original"] == "07/01/2026 a 20/01/2026"
    assert item.provenance["raw_json_record"]["DataInicial"].startswith("/Date(")
    assert item.provenance["dje_url"] == "http://www.tjsp.jus.br/Download/pdf/Mensagem.pdf"
    assert item.provenance["endpoint"] == SUSPENSIONS_ENDPOINT


def test_unknown_suspension_description_fails_closed():
    snapshot = snapshot_for(SUSPENSIONS_ENDPOINT)
    payload = json.loads(snapshot.content)
    payload["data"][0]["Descricao"] = "Recesso extraordinário e suspensão especial"
    altered = RawSourceSnapshot(snapshot.source_url, json.dumps(payload, ensure_ascii=False).encode(),
                                snapshot.fetched_at, snapshot.parser_version,
                                request_params=snapshot.request_params)
    with pytest.raises(UnclassifiedCalendarDescription):
        parse_suspensions(altered, REQUEST)


def test_endpoint_acquisition_persists_distinct_raw_snapshots_and_events_offline():
    db = sqlite3.connect(":memory:"); db.row_factory = sqlite3.Row
    migrate_connection(db)
    called = []

    def offline_fetcher(endpoint, *, allowed_hosts, parser_version, query_params):
        called.append((endpoint, dict(query_params)))
        assert allowed_hosts == ("www.tjsp.jus.br",)
        assert parser_version == PARSER_VERSION
        return snapshot_for(endpoint)

    result = acquire_tjsp_calendar(db, REQUEST, fetcher=offline_fetcher)
    assert [item[0] for item in called] == [HOLIDAYS_ENDPOINT, SUSPENSIONS_ENDPOINT]
    assert all(params == {"nomeMunicipio":"Piracaia", "codigoMunicipio":"", "ano":"2026"} for _, params in called)
    assert len(result["snapshots"]) == 2
    assert result["snapshots"][0]["snapshot_id"] != result["snapshots"][1]["snapshot_id"]
    assert result["snapshots"][0]["content_hash"] != result["snapshots"][1]["content_hash"]
    assert len(result["calendar_events"]) == 40
    snapshots = db.execute("SELECT source_endpoint,request_params_json,content,content_hash FROM court_calendar_snapshots ORDER BY source_endpoint").fetchall()
    assert len(snapshots) == 2
    assert {row["source_endpoint"] for row in snapshots} == {HOLIDAYS_ENDPOINT, SUSPENSIONS_ENDPOINT}
    for row in snapshots:
        assert json.loads(row["request_params_json"]) == REQUEST.query_params
        assert hashlib.sha256(row["content"]).hexdigest() == row["content_hash"]
    assert not db.execute("PRAGMA foreign_key_check").fetchall()
    again = acquire_tjsp_calendar(db, REQUEST, fetcher=offline_fetcher)
    assert [row["snapshot_id"] for row in again["snapshots"]] == [row["snapshot_id"] for row in result["snapshots"]]
    assert again["event_version_ids"] == result["event_version_ids"]
    assert db.execute("SELECT count(*) FROM court_calendar_snapshots").fetchone()[0] == 2
    assert db.execute("SELECT count(*) FROM court_calendar_events WHERE is_current=1").fetchone()[0] == 40


def test_no_absent_date_becomes_business_day_and_composition_reports_gap():
    events = (*parse_holidays(snapshot_for(HOLIDAYS_ENDPOINT), REQUEST),
              *parse_suspensions(snapshot_for(SUSPENSIONS_ENDPOINT), REQUEST))
    composition = compose_calendar(CalendarCompositionRequest("TJSP", "SP", "Piracaia",
        "2026-01-01", "2026-01-23"), events)
    states = {item.date: item.status for item in composition.entries}
    assert states["2026-01-01"] == "RECESS"
    assert states["2026-01-07"] == "SUSPENDED"
    assert "2026-01-21" in composition.missing_dates
    assert "2026-01-21" not in states
    assert composition.coverage_complete is False


def test_processes_physicos_endpoint_is_not_mixed_into_ordinary_snapshots():
    snapshots = (snapshot_for(HOLIDAYS_ENDPOINT), snapshot_for(SUSPENSIONS_ENDPOINT))
    assert all("ProcessosFisicos" not in snapshot.source_url for snapshot in snapshots)
    assert len({snapshot.source_endpoint for snapshot in snapshots}) == 2


def test_store_migrates_existing_v1_snapshot_schema_additively():
    db = sqlite3.connect(":memory:"); db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    db.execute("""CREATE TABLE court_calendar_snapshots(
      snapshot_id TEXT PRIMARY KEY,source_url TEXT NOT NULL,fetched_at TEXT NOT NULL,content_hash TEXT NOT NULL,
      parser_version TEXT NOT NULL,content BLOB NOT NULL,created_at TEXT NOT NULL,
      UNIQUE(source_url,content_hash,parser_version))""")
    db.execute("INSERT INTO court_calendar_snapshots VALUES('old','https://www.tjsp.jus.br/old','2026-01-01','h','p',x'00','t')")
    migrate_connection(db)
    columns = {row["name"] for row in db.execute("PRAGMA table_info(court_calendar_snapshots)")}
    assert {"source_endpoint", "request_params_json"} <= columns
    row = db.execute("SELECT source_endpoint,request_params_json FROM court_calendar_snapshots WHERE snapshot_id='old'").fetchone()
    assert row["source_endpoint"] == "https://www.tjsp.jus.br/old" and json.loads(row["request_params_json"]) == {}
    assert not db.execute("PRAGMA foreign_key_check").fetchall()
