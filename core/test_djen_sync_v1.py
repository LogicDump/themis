from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

import core.documentos.djen_sync_v1 as djen

PROCESS_ID = "1234567-89.2026.8.26.0001"


def _connect(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    return db


def test_daily_state_uses_distribution_date_and_marks_success():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        workspace = root / "workspace.db"
        process_db = root / "process.db"
        db = _connect(process_db)
        db.execute(
            "CREATE TABLE processes(process_id TEXT PRIMARY KEY,status TEXT,created_at TEXT)"
        )
        db.execute(
            "INSERT INTO processes VALUES(?,?,?)",
            (PROCESS_ID, "ACTIVE", "2026-09-01T00:00:00+00:00"),
        )
        db.execute(
            "CREATE TABLE process_metadata(process_id TEXT PRIMARY KEY,provenance_json TEXT)"
        )
        db.execute(
            "INSERT INTO process_metadata VALUES(?,?)",
            (
                PROCESS_ID,
                json.dumps({"basic_data": {"distribuicao": "29/01/2026 às 19:00 - Livre"}}),
            ),
        )
        db.commit()
        db.close()

        def connect_workspace(*, create=False):
            if not workspace.exists() and not create:
                raise FileNotFoundError(workspace)
            connection = _connect(workspace)
            connection.executescript(djen.SYNC_STATE_SCHEMA)
            return connection

        def connect_process(process_id):
            assert process_id == PROCESS_ID
            return _connect(process_db)
        calls = []

        def fake_sync(db, **kwargs):
            calls.append(kwargs)
            return {"count": 0}

        with (
            patch.object(djen, "workspace_db_path", return_value=workspace),
            patch.object(djen, "connect_workspace", side_effect=connect_workspace),
            patch.object(djen, "connect_process", side_effect=connect_process),
            patch.object(djen, "known_process_ids", return_value=[PROCESS_ID]),
            patch.object(djen, "process_db_path", return_value=process_db),
            patch.object(djen, "sync_djen", side_effect=fake_sync),
            patch.object(
                djen,
                "materialize_process_events",
                return_value={"materialized": 0},
            ),
        ):
            assert djen.status(as_of="2026-09-29")["needs_sync"] is True
            result = djen.sync_now(available_to="2026-09-29")
            assert result["ok"] is True
            assert calls[0]["available_from"] == "2026-01-29"
            assert result["status"]["needs_sync"] is False
            state = result["status"]["processes"][0]
            assert state["last_successful_sync_date"] == "2026-09-29"
            assert state["deadline_pipeline_revision"] == djen.DEADLINE_PIPELINE_REVISION


def test_same_day_state_from_older_pipeline_requires_resync():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        workspace = root / "workspace.db"
        process_db = root / "process.db"
        process_db.touch()

        db = _connect(workspace)
        db.execute("""CREATE TABLE djen_sync_state(
          process_id TEXT PRIMARY KEY,
          last_successful_sync_date TEXT,
          last_successful_sync_at TEXT,
          last_available_from TEXT,
          last_available_to TEXT,
          last_count INTEGER NOT NULL DEFAULT 0,
          last_error TEXT
        )""")
        db.execute(
            "INSERT INTO djen_sync_state VALUES(?,?,?,?,?,?,?)",
            (PROCESS_ID, "2026-10-01", "2026-10-01T12:00:00+00:00",
             "2026-09-01", "2026-10-01", 0, None),
        )
        db.commit()
        db.close()

        def connect_workspace(*, create=False):
            return _connect(workspace)

        with (
            patch.object(djen, "workspace_db_path", return_value=workspace),
            patch.object(djen, "connect_workspace", side_effect=connect_workspace),
            patch.object(djen, "known_process_ids", return_value=[PROCESS_ID]),
            patch.object(djen, "process_db_path", return_value=process_db),
        ):
            status = djen.status(as_of="2026-10-01")

        state = status["processes"][0]
        assert state["last_successful_sync_date"] == "2026-10-01"
        assert state["deadline_pipeline_revision"] is None
        assert state["deadline_pipeline_revision_current"] == djen.DEADLINE_PIPELINE_REVISION
        assert state["needs_sync"] is True


def test_no_djen_delta_skips_full_rebuild():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        workspace = root / "workspace.db"
        process_db = root / "process.db"
        db = _connect(process_db)
        db.execute("CREATE TABLE processes(process_id TEXT PRIMARY KEY,status TEXT,created_at TEXT)")
        db.execute("INSERT INTO processes VALUES(?,?,?)", (PROCESS_ID, "ACTIVE", "2026-09-01T00:00:00+00:00"))
        db.commit(); db.close()
        db = _connect(workspace)
        db.executescript(djen.SYNC_STATE_SCHEMA)
        db.execute(
            "INSERT INTO djen_sync_state(process_id,last_successful_sync_date,last_successful_sync_at,last_available_from,last_available_to,last_count,deadline_pipeline_revision) VALUES(?,?,?,?,?,?,?)",
            (PROCESS_ID, "2026-10-05", "2026-10-05T10:00:00+00:00", "2026-10-05", "2026-10-05", 1, djen.DEADLINE_PIPELINE_REVISION),
        )
        db.commit(); db.close()

        def connect_workspace(*, create=False):
            return _connect(workspace)

        def connect_process(process_id):
            assert process_id == PROCESS_ID
            return _connect(process_db)

        with (
            patch.object(djen, "workspace_db_path", return_value=workspace),
            patch.object(djen, "connect_workspace", side_effect=connect_workspace),
            patch.object(djen, "connect_process", side_effect=connect_process),
            patch.object(djen, "known_process_ids", return_value=[PROCESS_ID]),
            patch.object(djen, "process_db_path", return_value=process_db),
            patch.object(djen, "sync_djen", return_value={"count": 1, "changed_count": 0}),
            patch.object(djen, "materialize_process_events", side_effect=AssertionError("full rebuild called")),
        ):
            result = djen.sync_now(process_id=PROCESS_ID, available_to="2026-10-05")

        assert result["ok"] is True
        row = result["results"][0]
        assert row["process_events"]["skipped"] == "NO_DJEN_DELTA"
        assert row["deadline_calculation"]["reason"] == "NO_DJEN_DELTA"


def test_global_djen_skips_reference_only_processes():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        materialized = root / "materialized.db"
        materialized.touch()
        missing = root / "missing.db"
        reference_id = "7654321-00.2020.8.26.0001"

        with (
            patch.object(djen, "known_process_ids", return_value=[PROCESS_ID, reference_id]),
            patch.object(
                djen,
                "process_db_path",
                side_effect=lambda pid: materialized if pid == PROCESS_ID else missing,
            ),
        ):
            assert djen._materialized_process_ids() == [PROCESS_ID]



def test_calendar_failure_is_isolated_to_its_year():
    from core.documentos.providers import tjsp_calendar_acquisition_v1 as acquisition
    from core.documentos import court_calendar_store_v1 as calendar_store
    from core.documentos import deadline_calculation_store_v1 as calculation_store

    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute(
        "CREATE TABLE process_metadata(process_id TEXT PRIMARY KEY,tribunal TEXT,comarca TEXT)"
    )
    db.execute(
        "INSERT INTO process_metadata VALUES(?,?,?)",
        (PROCESS_ID, "TJSP", "Foro de Piracaia"),
    )
    db.execute(
        "CREATE TABLE publications(publication_id TEXT PRIMARY KEY,available_on TEXT,published_on TEXT,active INTEGER)"
    )
    db.execute(
        "INSERT INTO publications VALUES('pub-2025','2025-09-01',NULL,1)"
    )
    db.execute(
        "CREATE TABLE deadline_instructions(process_id TEXT,source_entity TEXT,source_id TEXT)"
    )
    db.execute(
        "INSERT INTO deadline_instructions VALUES(?,?,?)",
        (PROCESS_ID, "PUBLICATION", "pub-2025"),
    )
    db.commit()

    calls = []

    def fake_acquire(_db, request):
        calls.append(request.ano)
        if request.ano == 2025:
            raise ValueError("uncertain 2025 calendar record")
        return {"snapshots": [
            {"endpoint": acquisition.HOLIDAYS_ENDPOINT, "snapshot_id": f"hol-{request.ano}"},
            {"endpoint": acquisition.SUSPENSIONS_ENDPOINT, "snapshot_id": f"sus-{request.ano}"},
        ]}

    def fake_compose(_holidays, _suspensions, request, **_kwargs):
        return SimpleNamespace(
            entries=(f"calendar-{request.ano}",),
            calendar_version=f"calendar-{request.ano}",
            coverage_complete=True,
            missing_dates=(),
        )
    captured = {}

    def fake_calculate(_db, *, process_id, calendar_entries):
        captured["process_id"] = process_id
        captured["entries"] = tuple(calendar_entries)
        return {"obligations": 1, "status_counts": {"CALCULATED": 1}, "results": []}

    with (
        patch.object(calendar_store, "migrate_connection", return_value={}),
        patch.object(calendar_store, "get_snapshot", side_effect=lambda _db, sid: sid),
        patch.object(acquisition, "acquire_tjsp_calendar", side_effect=fake_acquire),
        patch.object(acquisition, "compose_effective_tjsp_calendar", side_effect=fake_compose),
        patch.object(calculation_store, "calculate_process", side_effect=fake_calculate),
    ):
        result = djen._calculate_tjsp_deadlines(db, PROCESS_ID, target_date="2026-10-01")

    assert calls == [2025, 2026, 2027]
    assert result["status"] == "PARTIAL"
    assert result["calendar_errors"] == [{"year": 2025, "error": "uncertain 2025 calendar record"}]
    assert [item["year"] for item in result["calendars"]] == [2026, 2027]
    assert captured == {"process_id": PROCESS_ID, "entries": ("calendar-2026", "calendar-2027")}
