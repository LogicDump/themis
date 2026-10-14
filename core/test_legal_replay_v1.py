"""Focused safety tests for the offline legal replay evidence contract."""
import json
import sqlite3

import pytest

from core.documentos.legal_replay_v1 import (
    LegalReplayIncomplete, _source_publications, _calendar_source,
    replay_legal_sources,
)
from core.documentos.publications_v1 import (
    migrate_connection, publication_from_item, upsert_publication,
)


PID = "1000045-87.2026.8.26.0450"


def _djen_item():
    return {
        "numero_processo": PID,
        "id": 1234,
        "meio": "D",
        "data_disponibilizacao": "2026-09-03",
        "tipoComunicacao": "Intimação",
        "texto": "Intimação publicada no DJEN",
    }


def test_djen_raw_item_is_sufficient_for_offline_replay(tmp_path):
    path = tmp_path / "pub.db"
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("CREATE TABLE processes(process_id TEXT PRIMARY KEY)")
        db.execute("INSERT INTO processes VALUES(?)", (PID,))
        migrate_connection(db)
        record = publication_from_item(
            _djen_item(), process_id=PID, request_url="https://comunicaapi.pje.jus.br/api/v1/comunicacao"
        )
        upsert_publication(db, record)
        db.commit()
        records = _source_publications(db, PID)
        assert len(records) == 1
        assert records[0]["payload_hash"] == record["payload_hash"]
        db.execute("UPDATE publications SET payload_hash='wrong'")
        db.commit()
        with pytest.raises(LegalReplayIncomplete, match="não corresponde"):
            _source_publications(db, PID)


def test_replay_requires_isolated_target(tmp_path):
    path = tmp_path / "a.db"
    path.touch()
    with pytest.raises(ValueError, match="bancos diferentes"):
        replay_legal_sources(path, path, PID, recalculate=False)


def test_tjsp_snapshot_detects_payload_tampering(tmp_path):
    path = tmp_path / "cal.db"
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        db.execute("CREATE TABLE court_calendar_snapshots("
                   "snapshot_id TEXT, source_url TEXT, source_endpoint TEXT,"
                   "request_params_json TEXT, fetched_at TEXT, content_hash TEXT,"
                   "parser_version TEXT, content BLOB)")
        db.execute("INSERT INTO court_calendar_snapshots VALUES(?,?,?,?,?,?,?,?)",
                   ("ccs_x", "https://www.tjsp.jus.br/x", "https://www.tjsp.jus.br/x",
                    json.dumps({"ano": "2026", "nomeMunicipio": "Piracaia"}),
                    "2026-09-30T00:00:00Z", "not_the_hash", "v1", b"{}"))
        with pytest.raises(LegalReplayIncomplete, match="hash inválido"):
            _calendar_source(db)


def test_replay_does_not_transplant_projected_publication_date(tmp_path):
    from contextlib import closing
    path = tmp_path / "primary.db"
    with closing(sqlite3.connect(path)) as db:
        db.row_factory = sqlite3.Row
        db.execute("CREATE TABLE processes(process_id TEXT PRIMARY KEY)")
        db.execute("INSERT INTO processes VALUES(?)", (PID,))
        migrate_connection(db)
        record = publication_from_item(_djen_item(), process_id=PID,
            request_url="https://comunicaapi.pje.jus.br/api/v1/comunicacao")
        upsert_publication(db, record)
        db.execute("UPDATE publications SET published_on='2026-09-07'")
        db.commit()
        assert _source_publications(db, PID)[0]["published_on"] is None
        db.execute("UPDATE publications SET provenance_json='{}'")
        with pytest.raises(LegalReplayIncomplete, match="raw_item"):
            _source_publications(db, PID)
        assert _source_publications(db, PID, allow_missing=True) == []


def test_unrelated_historical_gap_does_not_block_valid_2026_deadline(monkeypatch):
    from core.documentos import legal_replay_v1 as legal
    from core.documentos import participant_context_store_v1 as participants
    monkeypatch.setattr(participants, "materialize_all", lambda *_: None)
    monkeypatch.setattr(legal, "_has", lambda *_: False)
    monkeypatch.setattr(legal, "materialize_process_events", lambda *_: {})
    monkeypatch.setattr(legal, "materialize_publication_instructions", lambda *_: {})
    rows = [{"status": "CALCULATED", "due_date": "2026-07-07", "reason": None},
            {"status": "UNRESOLVED", "due_date": None,
             "reason": {"code": "CALENDAR_COVERAGE_MISSING", "date": "2025-03-10"}}]
    monkeypatch.setattr(legal, "calculate_process", lambda *a, **k: {"results": rows})
    with sqlite3.connect(":memory:") as db:
        report = {"status": "PARTIAL", "calendar_errors": [{"year": 2025}]}
        result = legal.project_legal_state(db, PID, calendar_entries=["verified-2026"],
                                           calendar_report=report)
        assert result["status"] == "READY"
        assert result["legal_status"] == result["calculated"]["status"] == "PARTIAL"
        assert result["calculated"]["results"][0]["due_date"] == "2026-07-07"
        assert len(result["calculated"]["coverage_failures"]) == 1
        blocked = legal.project_legal_state(db, PID, calendar_entries=[],
                                            calendar_report={"status": "INCOMPLETE"})
        assert blocked["status"] == "INCOMPLETE"
