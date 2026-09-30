"""Durable workspace-level jobs for asynchronous DJEN synchronization."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def migrate(db: sqlite3.Connection) -> None:
    db.execute("""CREATE TABLE IF NOT EXISTS djen_sync_jobs(
      job_id TEXT PRIMARY KEY,
      scope_key TEXT NOT NULL,
      process_id TEXT,
      available_to TEXT NOT NULL,
      status TEXT NOT NULL CHECK(status IN ('PENDING','RUNNING','COMPLETED','FAILED')),
      created_at TEXT NOT NULL,
      started_at TEXT,
      completed_at TEXT,
      error TEXT,
      result_json TEXT,
      worker_pid INTEGER,
      worker_started_at TEXT,
      worker_token TEXT
    )""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_djen_sync_jobs_scope ON djen_sync_jobs(scope_key, available_to, created_at DESC)")
    db.commit()


def decode(row: sqlite3.Row | dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    value = dict(row)
    try:
        value["result"] = json.loads(value.pop("result_json")) if value.get("result_json") else None
    except (TypeError, ValueError):
        value["result"] = None
    return value


def create_or_reuse(db: sqlite3.Connection, process_id: str | None, available_to: str) -> tuple[dict[str, Any], bool]:
    scope_key = process_id or "*"
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute(
            "SELECT * FROM djen_sync_jobs WHERE scope_key=? AND available_to=? AND status IN ('PENDING','RUNNING') ORDER BY created_at DESC LIMIT 1",
            (scope_key, available_to),
        ).fetchone()
        if row:
            db.commit()
            return decode(row) or {}, False
        job_id, created_at = uuid.uuid4().hex, now()
        db.execute(
            "INSERT INTO djen_sync_jobs(job_id,scope_key,process_id,available_to,status,created_at) VALUES(?,?,?,?,?,?)",
            (job_id, scope_key, process_id, available_to, "PENDING", created_at),
        )
        result = decode(db.execute("SELECT * FROM djen_sync_jobs WHERE job_id=?", (job_id,)).fetchone()) or {}
        db.commit()
        return result, True
    except Exception:
        db.rollback()
        raise


def get(db: sqlite3.Connection, job_id: str) -> dict[str, Any] | None:
    return decode(db.execute("SELECT * FROM djen_sync_jobs WHERE job_id=?", (job_id,)).fetchone())


def latest(db: sqlite3.Connection) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    active = db.execute("SELECT * FROM djen_sync_jobs WHERE status IN ('PENDING','RUNNING') ORDER BY created_at DESC LIMIT 1").fetchone()
    last = db.execute("SELECT * FROM djen_sync_jobs ORDER BY created_at DESC LIMIT 1").fetchone()
    return decode(active), decode(last)


def save(db: sqlite3.Connection, job: dict[str, Any]) -> dict[str, Any]:
    db.execute(
        """UPDATE djen_sync_jobs SET status=?,started_at=?,completed_at=?,error=?,result_json=?,
           worker_pid=?,worker_started_at=?,worker_token=? WHERE job_id=?""",
        (job["status"], job.get("started_at"), job.get("completed_at"), job.get("error"),
         json.dumps(job.get("result"), ensure_ascii=False) if job.get("result") is not None else None,
         job.get("worker_pid"), job.get("worker_started_at"), job.get("worker_token"), job["job_id"]),
    )
    db.commit()
    return get(db, str(job["job_id"])) or job
