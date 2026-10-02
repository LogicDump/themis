"""Persistência versionada e fonte textual de resumos de Movements."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

MIGRATION_VERSION = "movement-summary-store-v1"
FORWARD_MIGRATION_VERSION = "movement-summary-store-v2"
ANALYSIS_V2_MIGRATION_VERSION = "movement-analysis-v2"
PURPOSE = "themis.movement_summary"
PROMPT_VERSION = "movement-summary-v4"

SUMMARY_COLUMNS = {
    "summary_id", "movement_id", "summary_version", "summary_text",
    "prompt_version", "purpose", "provider", "model", "usage_json",
    "source_hash", "generated_at",
}
ANALYSIS_COLUMNS = {"analysis_schema_version", "analysis_json"}
ANALYSIS_V2_JOBS_MIGRATION_VERSION = "movement-analysis-v2-jobs-v1"
ANALYSIS_V2_WORKER_MIGRATION_VERSION = "movement-summary-worker-v2"
STATUS_SOURCE_MIGRATION_VERSION = "movement-summary-status-source-v1"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _create_summary_table(db: sqlite3.Connection, table_name: str = "movement_summaries") -> None:
    if table_name not in {"movement_summaries", "movement_summaries_new"}:
        raise ValueError("invalid summary table name")
    db.execute(
        f"""CREATE TABLE {table_name}(
          summary_id TEXT PRIMARY KEY,
          movement_id TEXT NOT NULL,
          summary_version INTEGER NOT NULL,
          summary_text TEXT NOT NULL,
          prompt_version TEXT NOT NULL,
          purpose TEXT NOT NULL,
          provider TEXT,
          model TEXT,
          usage_json TEXT,
          source_hash TEXT NOT NULL,
          generated_at TEXT NOT NULL,
          analysis_schema_version TEXT,
          analysis_json TEXT,
          FOREIGN KEY(movement_id) REFERENCES movements(movement_id) ON DELETE CASCADE,
          UNIQUE(movement_id, summary_version)
        )"""
    )


def _table_columns(db: sqlite3.Connection) -> set[str]:
    return {row[1] for row in db.execute("PRAGMA table_info(movement_summaries)").fetchall()}


def _legacy_rows(db: sqlite3.Connection, columns: set[str]) -> list[dict[str, Any]]:
    cursor = db.execute("SELECT rowid, * FROM movement_summaries ORDER BY rowid")
    names = [description[0] for description in cursor.description or ()]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def _normalise_legacy_row(row: dict[str, Any], next_versions: dict[str, int], used_ids: set[str], used_versions: set[tuple[str, int]]) -> tuple[Any, ...]:
    movement_id = str(row.get("movement_id") or "")
    if not movement_id:
        raise ValueError("movement_summaries row without movement_id")

    raw_version = row.get("summary_version")
    try:
        version = int(raw_version) if raw_version is not None else 0
    except (TypeError, ValueError):
        version = 0
    if version < 1:
        version = next_versions.get(movement_id, 0) + 1
    while (movement_id, version) in used_versions:
        version += 1
    next_versions[movement_id] = max(next_versions.get(movement_id, 0), version)
    used_versions.add((movement_id, version))

    summary_id = str(row.get("summary_id") or f"legacy_{movement_id}_{version}")
    if summary_id in used_ids:
        summary_id = f"{summary_id}_{row.get('rowid', version)}"
    used_ids.add(summary_id)
    return (
        summary_id,
        movement_id,
        version,
        str(row.get("summary_text") or row.get("summary") or ""),
        str(row.get("prompt_version") or row.get("model_version") or "legacy"),
        str(row.get("purpose") or PURPOSE),
        row.get("provider"),
        row.get("model"),
        row.get("usage_json"),
        str(row.get("source_hash") or ""),
        str(row.get("generated_at") or _now()),
    )


def _rebuild_summary_table(db: sqlite3.Connection, columns: set[str]) -> None:
    rows = _legacy_rows(db, columns)
    db.execute("DROP TABLE IF EXISTS movement_summaries_new")
    _create_summary_table(db, "movement_summaries_new")
    next_versions: dict[str, int] = {}
    used_ids: set[str] = set()
    used_versions: set[tuple[str, int]] = set()
    for row in rows:
        db.execute(
            """INSERT INTO movement_summaries_new(
              summary_id, movement_id, summary_version, summary_text, prompt_version,
              purpose, provider, model, usage_json, source_hash, generated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            _normalise_legacy_row(row, next_versions, used_ids, used_versions),
        )
    db.execute("DROP TABLE movement_summaries")
    db.execute("ALTER TABLE movement_summaries_new RENAME TO movement_summaries")


def migrate_connection(db: sqlite3.Connection) -> dict[str, Any]:
    db.execute("PRAGMA foreign_keys=ON")
    from core.retrieval.summary_embedding_store import migrate_connection as migrate_summary_embeddings
    migrate_summary_embeddings(db)
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'").fetchone() and db.execute(
        "SELECT 1 FROM schema_migrations WHERE version=?", (ANALYSIS_V2_WORKER_MIGRATION_VERSION,)
    ).fetchone():
        if db.execute("PRAGMA journal_mode").fetchone()[0] != "wal":
            db.execute("PRAGMA journal_mode=WAL")
        return {"migration_version": FORWARD_MIGRATION_VERSION, "already_applied": True}
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    db.commit()
    db.execute("BEGIN")
    try:
        old_exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='movement_summaries'"
        ).fetchone()
        if old_exists:
            columns = _table_columns(db)
            if not SUMMARY_COLUMNS.issubset(columns):
                _rebuild_summary_table(db, columns)
            columns = _table_columns(db)
            if not ANALYSIS_COLUMNS.issubset(columns):
                db.execute("ALTER TABLE movement_summaries ADD COLUMN analysis_schema_version TEXT")
                db.execute("ALTER TABLE movement_summaries ADD COLUMN analysis_json TEXT")
            columns = _table_columns(db)
            if not ANALYSIS_COLUMNS.issubset(columns):
                db.execute("ALTER TABLE movement_summaries ADD COLUMN analysis_schema_version TEXT")
                db.execute("ALTER TABLE movement_summaries ADD COLUMN analysis_json TEXT")
        else:
            _create_summary_table(db)

        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_movement_summaries_current "
            "ON movement_summaries(movement_id, summary_version DESC)"
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS movement_analysis_v2_jobs(
              job_id TEXT PRIMARY KEY,
              process_id TEXT NOT NULL,
              status TEXT NOT NULL CHECK(status IN ('PENDING','RUNNING','COMPLETED','PARTIAL','FAILED')),
              total_eligible INTEGER NOT NULL,
              completed INTEGER NOT NULL,
              pending INTEGER NOT NULL,
              failed INTEGER NOT NULL,
              current_batch_json TEXT,
              batch_count INTEGER NOT NULL DEFAULT 0,
              movement_ids_json TEXT NOT NULL,
              errors_json TEXT NOT NULL,
              error TEXT,
              llm_diagnostics_json TEXT NOT NULL DEFAULT '[]',
              provider TEXT,
              model TEXT,
              force_all INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              completed_at TEXT
            )"""
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_movement_analysis_v2_jobs_latest "
            "ON movement_analysis_v2_jobs(process_id, created_at DESC)"
        )
        job_columns = {row[1] for row in db.execute("PRAGMA table_info(movement_analysis_v2_jobs)")}
        for name, declaration in (
            ("worker_pid", "INTEGER"),
            ("worker_started_at", "TEXT"),
            ("worker_token", "TEXT"),
            ("cancel_requested", "INTEGER NOT NULL DEFAULT 0"),
            ("llm_diagnostics_json", "TEXT NOT NULL DEFAULT '[]'"),
        ):
            if name not in job_columns:
                db.execute(f"ALTER TABLE movement_analysis_v2_jobs ADD COLUMN {name} {declaration}")
        db.execute("""CREATE TABLE IF NOT EXISTS movement_summary_source_state(
          movement_id TEXT PRIMARY KEY REFERENCES movements(movement_id) ON DELETE CASCADE,
          source_hash TEXT,
          eligible INTEGER NOT NULL DEFAULT 0 CHECK(eligible IN (0,1))
        )""")
        source_state_applied = db.execute(
            "SELECT 1 FROM schema_migrations WHERE version=?", (STATUS_SOURCE_MIGRATION_VERSION,)
        ).fetchone()
        has_pages = bool(db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='pages'"
        ).fetchone())
        has_documents = bool(db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='documents'"
        ).fetchone())
        if not source_state_applied and has_pages and has_documents:
            refresh_source_state(db)
            db.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)",
                (STATUS_SOURCE_MIGRATION_VERSION, _now()),
            )
        if has_pages and has_documents:
            for event, reference in (("INSERT", "NEW"), ("UPDATE OF content, content_id", "NEW"), ("DELETE", "OLD")):
                suffix = event.split()[0].lower()
                db.execute(f"""CREATE TRIGGER IF NOT EXISTS movement_summary_source_pages_{suffix}
                  AFTER {event} ON pages BEGIN
                    UPDATE movement_summary_source_state SET source_hash=NULL
                    WHERE movement_id IN (
                      SELECT m.movement_id FROM movements m JOIN documents d ON d.process_id=m.process_id
                      WHERE d.document_id={reference}.document_id
                    );
                  END""")
        db.execute("""CREATE TRIGGER IF NOT EXISTS movement_summary_source_movement_update
          AFTER UPDATE OF payload_json ON movements BEGIN
            UPDATE movement_summary_source_state SET source_hash=NULL WHERE movement_id=NEW.movement_id;
          END""")
        applied = db.execute(
            "SELECT 1 FROM schema_migrations WHERE version=?", (FORWARD_MIGRATION_VERSION,)
        ).fetchone()
        db.execute(
            "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)",
            (MIGRATION_VERSION, _now()),
        )
        db.execute(
            "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)",
            (FORWARD_MIGRATION_VERSION, _now()),
        )
        db.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)", (ANALYSIS_V2_MIGRATION_VERSION, _now()))
        db.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)", (ANALYSIS_V2_JOBS_MIGRATION_VERSION, _now()))
        db.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)", (ANALYSIS_V2_WORKER_MIGRATION_VERSION, _now()))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"migration_version": FORWARD_MIGRATION_VERSION, "already_applied": bool(applied)}


def save_analysis_v2_job(db: sqlite3.Connection, job: dict[str, Any], *, commit: bool = True) -> dict[str, Any]:
    """Upsert a durable process-local V2 generation job snapshot."""
    current_batch = job.get("current_batch")
    db.execute(
        """INSERT INTO movement_analysis_v2_jobs(
          job_id, process_id, status, total_eligible, completed, pending, failed,
          current_batch_json, batch_count, movement_ids_json, errors_json, error,
          provider, model, force_all, created_at, updated_at, completed_at, llm_diagnostics_json,
          worker_pid, worker_started_at, worker_token, cancel_requested
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(job_id) DO UPDATE SET
          status=excluded.status, total_eligible=excluded.total_eligible,
          completed=excluded.completed, pending=excluded.pending, failed=excluded.failed,
          current_batch_json=excluded.current_batch_json, batch_count=excluded.batch_count,
          movement_ids_json=excluded.movement_ids_json, errors_json=excluded.errors_json,
          error=excluded.error, llm_diagnostics_json=excluded.llm_diagnostics_json,
          provider=excluded.provider, model=excluded.model,
          force_all=excluded.force_all, updated_at=excluded.updated_at,
          completed_at=excluded.completed_at,
          worker_pid=excluded.worker_pid, worker_started_at=excluded.worker_started_at,
          worker_token=excluded.worker_token,
          cancel_requested=max(movement_analysis_v2_jobs.cancel_requested, excluded.cancel_requested)""",
        (
            str(job["job_id"]), str(job["process_id"]), str(job["status"]),
            int(job.get("total_eligible", job.get("total", 0))), int(job.get("completed", 0)),
            int(job.get("pending", 0)), int(job.get("failed", 0)),
            json.dumps(current_batch, ensure_ascii=False, sort_keys=True) if current_batch is not None else None,
            int(job.get("batch_count", 0)),
            json.dumps(job.get("movement_ids", []), ensure_ascii=False),
            json.dumps(job.get("errors", []), ensure_ascii=False), job.get("error"),
            job.get("provider"), job.get("model"), int(bool(job.get("force_all"))),
            str(job["created_at"]), str(job.get("updated_at") or _now()), job.get("completed_at"),
            json.dumps(job.get("llm_diagnostics", []), ensure_ascii=False, sort_keys=True),
            job.get("worker_pid"), job.get("worker_started_at"), job.get("worker_token"),
            int(bool(job.get("cancel_requested", False))),
        ),
    )
    if commit:
        db.commit()
    return dict(job)


def _analysis_v2_job_from_row(row: sqlite3.Row | tuple[Any, ...], columns: list[str]) -> dict[str, Any]:
    value = dict(zip(columns, row))
    value["total"] = value["total_eligible"]
    value["movement_ids"] = json.loads(value.pop("movement_ids_json") or "[]")
    value["errors"] = json.loads(value.pop("errors_json") or "[]")
    batch_json = value.pop("current_batch_json")
    value["current_batch"] = json.loads(batch_json) if batch_json else None
    value["force_all"] = bool(value.get("force_all"))
    try:
        value["llm_diagnostics"] = json.loads(value.pop("llm_diagnostics_json", "[]") or "[]")
    except (TypeError, ValueError):
        value["llm_diagnostics"] = []
    return value


def analysis_v2_job(db: sqlite3.Connection, process_id: str, job_id: str | None = None) -> dict[str, Any] | None:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='movement_analysis_v2_jobs'").fetchone():
        return None
    if job_id:
        row = db.execute(
            "SELECT * FROM movement_analysis_v2_jobs WHERE process_id=? AND job_id=?",
            (process_id, job_id),
        ).fetchone()
    else:
        row = db.execute(
            "SELECT * FROM movement_analysis_v2_jobs WHERE process_id=? ORDER BY created_at DESC, rowid DESC LIMIT 1",
            (process_id,),
        ).fetchone()
    return _analysis_v2_job_from_row(row, [item[1] for item in db.execute("PRAGMA table_info(movement_analysis_v2_jobs)").fetchall()]) if row else None


def request_analysis_v2_job_cancel(db: sqlite3.Connection, process_id: str, job_id: str) -> dict[str, Any] | None:
    """Persist a cancellation request; the one-shot worker stops at a batch boundary."""
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='movement_analysis_v2_jobs'").fetchone():
        return None
    db.execute(
        """UPDATE movement_analysis_v2_jobs
           SET cancel_requested=1, updated_at=?
           WHERE process_id=? AND job_id=? AND status IN ('PENDING','RUNNING')""",
        (_now(), process_id, job_id),
    )
    db.commit()
    return analysis_v2_job(db, process_id, job_id)


def save_analysis_v2_batch(db: sqlite3.Connection, records: list[dict[str, Any]], *, provider: str | None, model: str | None, usage: Any) -> dict[str, Any]:
    """Persist a fully validated V2 response with the UI-compatible summary."""
    if not records:
        return {"imported": 0, "movement_ids": []}
    from core.documentos.movement_analysis_v2 import SCHEMA_VERSION
    inserted: list[str] = []
    try:
        db.execute("BEGIN")
        for record in records:
            movement_id = str(record["movement_id"])
            summary = str(record["summary"]).strip()
            source_hash = str(record["source_hash"])
            analysis = dict(record["analysis"])
            if (
                not summary or not source_hash
                or analysis.get("movement_id") != movement_id
                or analysis.get("summary") != summary
            ):
                raise ValueError(f"análise V2 incompleta para {movement_id}")
            version = int(db.execute("SELECT coalesce(max(summary_version),0)+1 FROM movement_summaries WHERE movement_id=?", (movement_id,)).fetchone()[0])
            db.execute("""INSERT INTO movement_summaries(summary_id,movement_id,summary_version,summary_text,prompt_version,purpose,provider,model,usage_json,source_hash,generated_at,analysis_schema_version,analysis_json)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                f"{movement_id}:summary:{version}", movement_id, version, summary, "movement-summary-v5-analysis-v2", PURPOSE,
                provider, model, json.dumps(usage, ensure_ascii=False, sort_keys=True) if usage is not None else None,
                source_hash, _now(), SCHEMA_VERSION, json.dumps(analysis, ensure_ascii=False, sort_keys=True)))
            inserted.append(movement_id)
        db.commit()
    except Exception:
        db.rollback()
        raise
    _sync_summary_embeddings(db, inserted)
    return {"imported": len(inserted), "movement_ids": inserted}


def save_analysis_v3_batch(db: sqlite3.Connection, records: list[dict[str, Any]], *, provider: str | None, model: str | None, usage: Any) -> dict[str, Any]:
    """Persist a fully validated V3 analysis with its UI-compatible summary."""
    if not records:
        return {"imported": 0, "movement_ids": []}
    from core.documentos.movement_analysis_v3 import SCHEMA_VERSION
    inserted: list[str] = []
    try:
        db.execute("BEGIN")
        for record in records:
            movement_id = str(record["movement_id"])
            summary = str(record["summary"]).strip()
            source_hash = str(record["source_hash"])
            analysis = dict(record["analysis"])
            if (
                not summary or not source_hash
                or analysis.get("movement_id") != movement_id
                or analysis.get("summary") != summary
            ):
                raise ValueError(f"analise V3 incompleta para {movement_id}")
            version = int(db.execute(
                "SELECT coalesce(max(summary_version),0)+1 FROM movement_summaries WHERE movement_id=?",
                (movement_id,),
            ).fetchone()[0])
            db.execute(
                """INSERT INTO movement_summaries(
                  summary_id,movement_id,summary_version,summary_text,prompt_version,purpose,provider,model,
                  usage_json,source_hash,generated_at,analysis_schema_version,analysis_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    f"{movement_id}:summary:{version}", movement_id, version, summary,
                    "movement-summary-v6-analysis-v3", PURPOSE, provider, model,
                    json.dumps(usage, ensure_ascii=False, sort_keys=True) if usage is not None else None,
                    source_hash, _now(), SCHEMA_VERSION,
                    json.dumps(analysis, ensure_ascii=False, sort_keys=True),
                ),
            )
            inserted.append(movement_id)
        db.commit()
    except Exception:
        db.rollback()
        raise
    _sync_summary_embeddings(db, inserted)
    return {"imported": len(inserted), "movement_ids": inserted}


def _sync_summary_embeddings(db: sqlite3.Connection, movement_ids: list[str]) -> None:
    """Maintain the rebuildable index after summary persistence, without failing the summary save."""
    try:
        from core.retrieval.summary_embedding_store import sync_current_embeddings
        sync_current_embeddings(db, movement_ids)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Falha ao atualizar índice derivado de movement_summary")


def persisted_analyses(db: sqlite3.Connection) -> list[dict[str, Any]]:
    """Latest V2 analyses in deterministic order; callers derive known from these rows."""
    if not ANALYSIS_COLUMNS.issubset(_table_columns(db)):
        return []
    rows = db.execute("""SELECT m.process_id,s.movement_id,s.source_hash,s.analysis_json
        FROM movement_summaries s JOIN movements m ON m.movement_id=s.movement_id
        JOIN (SELECT movement_id,max(summary_version) v FROM movement_summaries GROUP BY movement_id) c
        ON c.movement_id=s.movement_id AND c.v=s.summary_version
        WHERE s.analysis_schema_version=? ORDER BY s.movement_id""", ("movement-analysis-v2",)).fetchall()
    return [{"process_id": row["process_id"], "movement_id": row["movement_id"], "source_hash": row["source_hash"], "analysis": json.loads(row["analysis_json"])} for row in rows]


def persisted_analyses_v3(db: sqlite3.Connection) -> list[dict[str, Any]]:
    """Latest V3 analyses in deterministic order."""
    if not ANALYSIS_COLUMNS.issubset(_table_columns(db)):
        return []
    rows = db.execute(
        """SELECT m.process_id,s.movement_id,s.source_hash,s.analysis_json
           FROM movement_summaries s JOIN movements m ON m.movement_id=s.movement_id
           JOIN (SELECT movement_id,max(summary_version) v FROM movement_summaries GROUP BY movement_id) c
             ON c.movement_id=s.movement_id AND c.v=s.summary_version
           WHERE s.analysis_schema_version=? ORDER BY s.movement_id""",
        ("movement-analysis-v3",),
    ).fetchall()
    return [
        {"process_id": row["process_id"], "movement_id": row["movement_id"],
         "source_hash": row["source_hash"], "analysis": json.loads(row["analysis_json"])}
        for row in rows
    ]


def _movement_payload(db: sqlite3.Connection, movement_id: str) -> dict[str, Any] | None:
    row = db.execute(
        "SELECT payload_json FROM movements WHERE movement_id=?", (movement_id,)
    ).fetchone()
    if not row:
        return None
    return json.loads(row[0])


def source_pages(db: sqlite3.Connection, movement_id: str) -> list[dict[str, Any]]:
    """Return only the first (own) piece's pages, never child attachments."""
    movement = _movement_payload(db, movement_id)
    if movement is None:
        return []
    pieces = movement.get("pieces") or movement.get("components") or []
    own_piece = pieces[0] if pieces else None
    refs = (own_piece or {}).get("pages") or []
    pages: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for ref in refs:
        document_id = ref.get("document_id")
        pdf_page = ref.get("pdf_page")
        try:
            pdf_page = int(pdf_page)
        except (TypeError, ValueError):
            pdf_page = None
        if not document_id or pdf_page is None or pdf_page < 1:
            continue
        key = (document_id, pdf_page)
        if key in seen:
            continue
        row = db.execute(
            "SELECT document_id, page_number, content FROM pages WHERE document_id=? AND page_number=?",
            key,
        ).fetchone()
        if row:
            pages.append(dict(row))
            seen.add(key)
    return pages


def source_text_and_hash(db: sqlite3.Connection, movement_id: str) -> tuple[str, str]:
    text = "\n\n".join(page["content"] for page in source_pages(db, movement_id))
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest()


def refresh_source_state(db: sqlite3.Connection, process_id: str | None = None) -> None:
    """Materialize own-piece source metadata during migration/ingestion, never on status reads."""
    if not db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='movement_summary_source_state'"
    ).fetchone():
        return
    if process_id is None:
        rows = db.execute("SELECT movement_id FROM movements").fetchall()
    else:
        rows = db.execute("SELECT movement_id FROM movements WHERE process_id=?", (process_id,)).fetchall()
    for row in rows:
        movement_id = str(row[0])
        text, source_hash = source_text_and_hash(db, movement_id)
        db.execute(
            """INSERT INTO movement_summary_source_state(movement_id, source_hash, eligible)
               VALUES(?,?,?) ON CONFLICT(movement_id) DO UPDATE SET
               source_hash=excluded.source_hash, eligible=excluded.eligible""",
            (movement_id, source_hash, int(bool(text.strip()))),
        )
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='movement_summary_embeddings'").fetchone():
            if not text.strip():
                db.execute("DELETE FROM movement_summary_embeddings WHERE movement_id=?", (movement_id,))
            else:
                db.execute(
                    """DELETE FROM movement_summary_embeddings WHERE movement_id=? AND NOT EXISTS(
                     SELECT 1 FROM movement_summaries s
                     WHERE s.movement_id=? AND s.summary_version=(
                       SELECT max(latest.summary_version) FROM movement_summaries latest
                       WHERE latest.movement_id=s.movement_id
                     ) AND s.source_hash=? AND trim(s.summary_text)<>''
                   )""",
                    (movement_id, movement_id, source_hash),
                )


def current(db: sqlite3.Connection, movement_id: str) -> dict[str, Any] | None:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='movement_summaries'").fetchone():
        return None
    row = db.execute(
        """SELECT summary_id, movement_id, summary_version, summary_text, prompt_version,
                  purpose, provider, model, usage_json, source_hash, generated_at
           FROM movement_summaries WHERE movement_id=?
           ORDER BY summary_version DESC LIMIT 1""",
        (movement_id,),
    ).fetchone()
    if not row:
        return None
    value = dict(row)
    value["usage"] = json.loads(value.pop("usage_json")) if value["usage_json"] else None
    return value


def current_v2_analysis(db: sqlite3.Connection, movement_id: str) -> dict[str, Any] | None:
    """Return the latest summary only when that version carries a V2 analysis."""
    columns = _table_columns(db)
    if not ANALYSIS_COLUMNS.issubset(columns):
        return None
    row = db.execute(
        """SELECT summary_id, movement_id, summary_version, summary_text, source_hash,
                  generated_at, analysis_schema_version, analysis_json
           FROM movement_summaries WHERE movement_id=?
           ORDER BY summary_version DESC LIMIT 1""",
        (movement_id,),
    ).fetchone()
    if not row or row["analysis_schema_version"] != "movement-analysis-v2" or not row["analysis_json"]:
        return None
    value = dict(row)
    try:
        value["analysis"] = json.loads(value.pop("analysis_json"))
    except (TypeError, json.JSONDecodeError):
        return None
    return value


def current_v3_analysis(db: sqlite3.Connection, movement_id: str) -> dict[str, Any] | None:
    """Return the latest summary only when that version carries a V3 analysis."""
    columns = _table_columns(db)
    if not ANALYSIS_COLUMNS.issubset(columns):
        return None
    row = db.execute(
        """SELECT summary_id, movement_id, summary_version, summary_text, source_hash,
                  generated_at, analysis_schema_version, analysis_json
           FROM movement_summaries WHERE movement_id=?
           ORDER BY summary_version DESC LIMIT 1""",
        (movement_id,),
    ).fetchone()
    if not row or row["analysis_schema_version"] != "movement-analysis-v3" or not row["analysis_json"]:
        return None
    value = dict(row)
    try:
        value["analysis"] = json.loads(value.pop("analysis_json"))
    except (TypeError, json.JSONDecodeError):
        return None
    return value


def versions(db: sqlite3.Connection, movement_id: str) -> list[dict[str, Any]]:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='movement_summaries'").fetchone():
        return []
    rows = db.execute(
        "SELECT summary_id, movement_id, summary_version, prompt_version, purpose, provider, model, source_hash, generated_at FROM movement_summaries WHERE movement_id=? ORDER BY summary_version DESC",
        (movement_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def save(
    db: sqlite3.Connection,
    movement_id: str,
    *,
    summary_text: str,
    source_hash: str,
    provider: str | None,
    model: str | None,
    usage: Any,
) -> dict[str, Any]:
    row = db.execute(
        "SELECT coalesce(max(summary_version), 0) FROM movement_summaries WHERE movement_id=?",
        (movement_id,),
    ).fetchone()
    version = int(row[0]) + 1
    summary_id = f"{movement_id}:summary:{version}"
    db.execute(
        """INSERT INTO movement_summaries(
          summary_id, movement_id, summary_version, summary_text, prompt_version,
          purpose, provider, model, usage_json, source_hash, generated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (
            summary_id, movement_id, version, summary_text, PROMPT_VERSION, PURPOSE,
            provider, model, json.dumps(usage, ensure_ascii=False, sort_keys=True) if usage is not None else None,
            source_hash, _now(),
        ),
    )
    db.commit()
    _sync_summary_embeddings(db, [movement_id])
    return current(db, movement_id) or {}


def save_batch(
    db: sqlite3.Connection,
    records: list[dict[str, Any]],
    *,
    provider: str | None,
    model: str | None,
    usage: Any,
) -> dict[str, Any]:
    """Persist a pre-validated batch as new versions in one transaction."""
    if not records:
        return {"imported": 0, "movement_ids": []}
    inserted: list[str] = []
    try:
        db.execute("BEGIN")
        for record in records:
            movement_id = str(record["movement_id"])
            summary_text = str(record["summary_text"] or "").strip()
            if not summary_text:
                raise ValueError(f"summary vazio para {movement_id}")
            source_hash = str(record["source_hash"] or "")
            if not source_hash:
                raise ValueError(f"source_hash ausente para {movement_id}")
            row = db.execute(
                "SELECT coalesce(max(summary_version), 0) FROM movement_summaries WHERE movement_id=?",
                (movement_id,),
            ).fetchone()
            version = int(row[0]) + 1
            summary_id = f"{movement_id}:summary:{version}"
            db.execute(
                """INSERT INTO movement_summaries(
                  summary_id, movement_id, summary_version, summary_text, prompt_version,
                  purpose, provider, model, usage_json, source_hash, generated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    summary_id, movement_id, version, summary_text, PROMPT_VERSION, PURPOSE,
                    provider, model,
                    json.dumps(usage, ensure_ascii=False, sort_keys=True) if usage is not None else None,
                    source_hash, _now(),
                ),
            )
            inserted.append(movement_id)
        db.commit()
    except Exception:
        db.rollback()
        raise
    _sync_summary_embeddings(db, inserted)
    return {"imported": len(inserted), "movement_ids": inserted}
