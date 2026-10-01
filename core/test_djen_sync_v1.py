from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

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
