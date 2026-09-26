"""Persistência versionada da síntese processual baseada em Movement summaries."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

MIGRATION_VERSION = "case-synthesis-store-v1"
JOBS_MIGRATION_VERSION = "case-synthesis-jobs-v2"
PURPOSE = "themis.case_synthesis"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def migrate_connection(db: sqlite3.Connection) -> dict[str, Any]:
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    db.execute(
        """CREATE TABLE IF NOT EXISTS case_syntheses(
          synthesis_id TEXT PRIMARY KEY,
          process_id TEXT NOT NULL,
          synthesis_version INTEGER NOT NULL,
          case_synthesis TEXT NOT NULL,
          current_status TEXT NOT NULL,
          pending_issues_json TEXT NOT NULL,
          supporting_movement_ids_json TEXT NOT NULL,
          provider TEXT,
          model TEXT,
          prompt_version TEXT NOT NULL,
          dependency_hash TEXT NOT NULL,
          usage_json TEXT,
          generated_at TEXT NOT NULL,
          UNIQUE(process_id, synthesis_version)
        )"""
    )
    db.execute("CREATE INDEX IF NOT EXISTS idx_case_syntheses_current ON case_syntheses(process_id, synthesis_version DESC)")
    db.execute(
        """CREATE TABLE IF NOT EXISTS case_synthesis_jobs(
          job_id TEXT PRIMARY KEY,
          process_id TEXT NOT NULL,
          status TEXT NOT NULL CHECK(status IN ('PENDING','RUNNING','COMPLETED','FAILED')),
          provider TEXT,
          model TEXT,
          dependency_hash TEXT,
          synthesis_id TEXT,
          error TEXT,
          llm_diagnostics_json TEXT NOT NULL DEFAULT '[]',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          started_at TEXT,
          completed_at TEXT,
          worker_pid INTEGER,
          worker_started_at TEXT,
          worker_token TEXT,
          cancel_requested INTEGER NOT NULL DEFAULT 0
        )"""
    )
    job_columns = {row[1] for row in db.execute("PRAGMA table_info(case_synthesis_jobs)")}
    if "llm_diagnostics_json" not in job_columns:
        db.execute("ALTER TABLE case_synthesis_jobs ADD COLUMN llm_diagnostics_json TEXT NOT NULL DEFAULT '[]'")
    db.execute("CREATE INDEX IF NOT EXISTS idx_case_synthesis_jobs_process ON case_synthesis_jobs(process_id, created_at DESC)")
    applied = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION,)).fetchone()
    db.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)", (MIGRATION_VERSION, _now()))
    jobs_applied = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (JOBS_MIGRATION_VERSION,)).fetchone()
    db.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)", (JOBS_MIGRATION_VERSION, _now()))
    db.commit()
    return {
        "migration_version": MIGRATION_VERSION,
        "already_applied": bool(applied),
        "jobs_migration_version": JOBS_MIGRATION_VERSION,
        "jobs_already_applied": bool(jobs_applied),
    }


def _job_record(row: sqlite3.Row | dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    record = dict(row)
    record["cancel_requested"] = bool(record.get("cancel_requested"))
    try:
        record["llm_diagnostics"] = json.loads(record.pop("llm_diagnostics_json", "[]") or "[]")
    except (TypeError, ValueError):
        record["llm_diagnostics"] = []
    return record


def job(db: sqlite3.Connection, process_id: str, job_id: str) -> dict[str, Any] | None:
    return _job_record(db.execute(
        "SELECT * FROM case_synthesis_jobs WHERE process_id=? AND job_id=?",
        (process_id, job_id),
    ).fetchone())


def latest_job(db: sqlite3.Connection, process_id: str) -> dict[str, Any] | None:
    return _job_record(db.execute(
        "SELECT * FROM case_synthesis_jobs WHERE process_id=? ORDER BY created_at DESC, rowid DESC LIMIT 1",
        (process_id,),
    ).fetchone())


def create_job_if_absent(db: sqlite3.Connection, record: dict[str, Any]) -> tuple[dict[str, Any] | None, bool]:
    db.execute("BEGIN IMMEDIATE")
    try:
        if not db.execute(
            "SELECT 1 FROM processes WHERE process_id=?", (record["process_id"],)
        ).fetchone():
            db.commit()
            return None, False
        existing = db.execute(
            "SELECT * FROM case_synthesis_jobs WHERE process_id=? AND status IN ('PENDING','RUNNING') ORDER BY created_at DESC LIMIT 1",
            (record["process_id"],),
        ).fetchone()
        if existing is not None:
            db.commit()
            return _job_record(existing) or {}, False
        db.execute(
            """INSERT INTO case_synthesis_jobs(
              job_id, process_id, status, provider, model, dependency_hash, synthesis_id,
              error, created_at, updated_at, started_at, completed_at, worker_pid,
              worker_started_at, worker_token, cancel_requested, llm_diagnostics_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                record["job_id"], record["process_id"], record.get("status", "PENDING"),
                record.get("provider"), record.get("model"), record.get("dependency_hash"),
                record.get("synthesis_id"), record.get("error"), record["created_at"],
                record.get("updated_at", record["created_at"]), record.get("started_at"),
                record.get("completed_at"), record.get("worker_pid"),
                record.get("worker_started_at"), record.get("worker_token"),
                int(bool(record.get("cancel_requested"))),
                json.dumps(record.get("llm_diagnostics", []), ensure_ascii=False, sort_keys=True),
            ),
        )
        db.commit()
        return job(db, str(record["process_id"]), str(record["job_id"])) or {}, True
    except Exception:
        db.rollback()
        raise


def save_job(db: sqlite3.Connection, record: dict[str, Any], *, commit: bool = True) -> dict[str, Any]:
    cursor = db.execute(
        """UPDATE case_synthesis_jobs SET status=?, provider=?, model=?, dependency_hash=?,
          synthesis_id=?, error=?, updated_at=?, started_at=?, completed_at=?, worker_pid=?,
          worker_started_at=?, worker_token=?, cancel_requested=?, llm_diagnostics_json=?
          WHERE process_id=? AND job_id=?""",
        (
            record["status"], record.get("provider"), record.get("model"),
            record.get("dependency_hash"), record.get("synthesis_id"), record.get("error"),
            record.get("updated_at") or _now(), record.get("started_at"),
            record.get("completed_at"), record.get("worker_pid"),
            record.get("worker_started_at"), record.get("worker_token"),
            int(bool(record.get("cancel_requested"))),
            json.dumps(record.get("llm_diagnostics", []), ensure_ascii=False, sort_keys=True),
            record["process_id"], record["job_id"],
        ),
    )
    if cursor.rowcount != 1:
        raise KeyError(f"Job de síntese não encontrado: {record.get('job_id')}")
    if commit:
        db.commit()
    return job(db, str(record["process_id"]), str(record["job_id"])) or {}


def dependency_hash(records: list[dict[str, Any]]) -> str:
    """Hash the ordered Movement/current-summary version dependency exactly."""
    dependency = [
        {
            "movement_id": str(record["movement_id"]),
            "summary_id": str(record["summary_id"]),
            "summary_version": int(record["summary_version"]),
        }
        for record in records
    ]
    payload = json.dumps(dependency, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def current(db: sqlite3.Connection, process_id: str) -> dict[str, Any] | None:
    row = db.execute(
        """SELECT synthesis_id, process_id, synthesis_version, case_synthesis, current_status,
                  pending_issues_json, supporting_movement_ids_json, provider, model,
                  prompt_version, dependency_hash, usage_json, generated_at
           FROM case_syntheses WHERE process_id=?
           ORDER BY synthesis_version DESC LIMIT 1""",
        (process_id,),
    ).fetchone()
    if not row:
        return None
    value = dict(row)
    value["pending_issues"] = json.loads(value.pop("pending_issues_json"))
    value["supporting_movement_ids"] = json.loads(value.pop("supporting_movement_ids_json"))
    value["usage"] = json.loads(value.pop("usage_json")) if value["usage_json"] else None
    return value


def versions(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    rows = db.execute(
        """SELECT synthesis_id, process_id, synthesis_version, provider, model,
                  prompt_version, dependency_hash, generated_at
           FROM case_syntheses WHERE process_id=? ORDER BY synthesis_version DESC""",
        (process_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def save(
    db: sqlite3.Connection,
    process_id: str,
    *,
    case_synthesis: str,
    current_status: str,
    pending_issues: list[dict[str, Any]],
    supporting_movement_ids: list[str],
    provider: str | None,
    model: str | None,
    prompt_version: str,
    dependency_hash_value: str,
    usage: Any,
    commit: bool = True,
) -> dict[str, Any]:
    if not case_synthesis.strip() or not current_status.strip():
        raise ValueError("Síntese e situação atual não podem ser vazias")
    row = db.execute("SELECT coalesce(max(synthesis_version), 0) FROM case_syntheses WHERE process_id=?", (process_id,)).fetchone()
    version = int(row[0]) + 1
    synthesis_id = f"{process_id}:case-synthesis:{version}"
    db.execute(
        """INSERT INTO case_syntheses(
          synthesis_id, process_id, synthesis_version, case_synthesis, current_status,
          pending_issues_json, supporting_movement_ids_json, provider, model,
          prompt_version, dependency_hash, usage_json, generated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            synthesis_id, process_id, version, case_synthesis.strip(), current_status.strip(),
            json.dumps(pending_issues, ensure_ascii=False, sort_keys=True),
            json.dumps(supporting_movement_ids, ensure_ascii=False), provider, model,
            prompt_version, dependency_hash_value,
            json.dumps(usage, ensure_ascii=False, sort_keys=True) if usage is not None else None,
            _now(),
        ),
    )
    if commit:
        db.commit()
    return current(db, process_id) or {}


def complete_job_with_synthesis(
    db: sqlite3.Connection,
    record: dict[str, Any],
    *,
    case_synthesis: str,
    current_status: str,
    pending_issues: list[dict[str, Any]],
    supporting_movement_ids: list[str],
    prompt_version: str,
    dependency_hash_value: str,
    usage: Any,
) -> dict[str, Any]:
    db.execute("BEGIN IMMEDIATE")
    try:
        saved = save(
            db, str(record["process_id"]), case_synthesis=case_synthesis,
            current_status=current_status, pending_issues=pending_issues,
            supporting_movement_ids=supporting_movement_ids,
            provider=record.get("provider"), model=record.get("model"),
            prompt_version=prompt_version, dependency_hash_value=dependency_hash_value,
            usage=usage, commit=False,
        )
        record.update(
            status="COMPLETED", synthesis_id=saved.get("synthesis_id"), error=None,
            dependency_hash=dependency_hash_value, updated_at=_now(), completed_at=_now(),
        )
        job_record = save_job(db, record, commit=False)
        db.commit()
        return {"synthesis": saved, "job": job_record}
    except Exception:
        db.rollback()
        raise
