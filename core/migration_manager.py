"""Central migration orchestration for Themis persistent SQLite stores.

This module owns *when* schema migrations run. Individual domain modules still
own their schema and migration implementation.

Scopes:
- catalog.db: global process discovery index
- workspace.db: user/workspace state and background jobs
- process.db: one isolated Process Package

Design constraints:
- idempotent;
- safe to run on every plugin startup;
- no derived-data materialization;
- no network access;
- no provider re-download;
- existing schema_migrations(version, applied_at) remains authoritative.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.process_storage import (
    CATALOG_SCHEMA,
    WORKSPACE_SCHEMA,
    known_process_ids,
)
from core.runtime_paths import (
    catalog_db_path,
    process_db_path,
    themis_data_root,
    workspace_db_path,
)

CATALOG_BASELINE_MIGRATION = "catalog-schema-v1"
WORKSPACE_BASELINE_MIGRATION = "workspace-schema-v1"
WORKSPACE_DJEN_JOBS_MIGRATION = "workspace-djen-sync-jobs-v1"
MIGRATION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations(
  version TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def backup_database(path: Path, *, label: str = "migration") -> Path:
    """Create a consistent SQLite backup for a future destructive migration.

    Schema-only/idempotent migrations do not call this automatically. Migrations
    that rebuild/drop/transform existing structures must call it before changing
    the source database.
    """
    source = Path(path).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_label = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)
    backup_dir = source.parent / ".migration-backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"{source.name}.{stamp}.{safe_label}.bak"

    src = sqlite3.connect(str(source))
    dst = sqlite3.connect(str(target))
    try:
        src.backup(dst)
        dst.commit()
        integrity = dst.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Backup SQLite inválido: integrity={integrity}")
    except Exception:
        dst.close()
        src.close()
        target.unlink(missing_ok=True)
        raise
    else:
        dst.close()
        src.close()
    return target


def _open_writable(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def _record(db: sqlite3.Connection, version: str) -> bool:
    db.execute(MIGRATION_TABLE_SQL)
    exists = db.execute(
        "SELECT 1 FROM schema_migrations WHERE version=?",
        (version,),
    ).fetchone()
    if exists:
        return False
    db.execute(
        "INSERT INTO schema_migrations(version, applied_at) VALUES(?, ?)",
        (version, _now()),
    )
    return True


def applied_versions(db: sqlite3.Connection) -> set[str]:
    if not db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
    ).fetchone():
        return set()
    return {str(row[0]) for row in db.execute("SELECT version FROM schema_migrations")}


def migrate_catalog(*, root: Path | None = None) -> dict[str, Any]:
    target = catalog_db_path(root)
    db = _open_writable(target)
    try:
        db.executescript(CATALOG_SCHEMA)
        changed = _record(db, CATALOG_BASELINE_MIGRATION)
        db.commit()
        return {
            "scope": "catalog",
            "path": str(target),
            "changed": changed,
            "versions": sorted(applied_versions(db)),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def migrate_workspace(*, root: Path | None = None) -> dict[str, Any]:
    target = workspace_db_path(root)
    db = _open_writable(target)
    try:
        db.executescript(WORKSPACE_SCHEMA)

        baseline_changed = _record(db, WORKSPACE_BASELINE_MIGRATION)
        db.commit()

        # DJEN sync jobs live in workspace.db and historically commit their own
        # schema. Keep that behavior compatible and record the orchestration
        # marker after the domain migration succeeds.
        from core.documentos import djen_sync_job_store_v1
        djen_sync_job_store_v1.migrate(db)
        jobs_changed = _record(db, WORKSPACE_DJEN_JOBS_MIGRATION)
        db.commit()

        return {
            "scope": "workspace",
            "path": str(target),
            "changed": baseline_changed or jobs_changed,
            "versions": sorted(applied_versions(db)),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def migrate_process_db(path: Path, *, process_id: str | None = None) -> dict[str, Any]:
    """Apply the schema-only Process Package migrations required by Core/API."""
    target = Path(path).resolve()
    if not target.is_file():
        raise FileNotFoundError(target)

    db = _open_writable(target)
    try:
        before = applied_versions(db)

        from core.documentos import (
            case_synthesis_store_v1,
            deadline_calculation_store_v1,
            deadline_instruction_store_v1,
            deadline_obligation_store_v1,
            movement_summary_store_v1,
            participant_context_store_v1,
            process_event_store_v1,
            publications_v1,
        )
        from core.retrieval import summary_embedding_store

        results: dict[str, Any] = {}
        results["movement_summary"] = movement_summary_store_v1.migrate_connection(db)
        summary_embedding_store.migrate_connection(db)
        results["summary_embeddings"] = {"migration_version": summary_embedding_store.MIGRATION_VERSION}
        results["case_synthesis"] = case_synthesis_store_v1.migrate_connection(db)
        results["process_events"] = process_event_store_v1.migrate_connection(db)
        results["deadline_instructions"] = deadline_instruction_store_v1.migrate_connection(db)
        results["deadline_obligations"] = deadline_obligation_store_v1.migrate_connection(db)
        results["participant_context"] = participant_context_store_v1.migrate_connection(db)
        results["publications"] = publications_v1.migrate_connection(db)
        results["deadline_calculations"] = deadline_calculation_store_v1.migrate_connection(db)

        # Migration modules own their transaction boundaries historically.
        db.commit()

        after = applied_versions(db)
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        fk_errors = db.execute("PRAGMA foreign_key_check").fetchall()
        if integrity != "ok" or fk_errors:
            raise RuntimeError(
                f"Process Package inválido após migration: integrity={integrity}; "
                f"foreign_keys={len(fk_errors)}"
            )

        return {
            "scope": "process",
            "process_id": process_id,
            "path": str(target),
            "changed": before != after,
            "applied_now": sorted(after - before),
            "versions": sorted(after),
            "integrity": integrity,
            "foreign_key_errors": 0,
            "components": results,
        }
    finally:
        db.close()


def _materialized_process_ids(data_root: Path) -> list[str]:
    """Union catalog discovery with valid on-disk Process Packages."""
    ids = set(known_process_ids(root=data_root))
    processos = data_root / "processos"
    if processos.is_dir():
        from core.runtime_paths import validate_process_id
        for child in processos.iterdir():
            if not child.is_dir() or not (child / "process.db").is_file():
                continue
            try:
                ids.add(validate_process_id(child.name))
            except ValueError:
                continue
    return sorted(ids)


def migrate_all(*, root: Path | None = None) -> dict[str, Any]:
    """Bring all currently materialized Themis databases to the current schema."""
    data_root = (root or themis_data_root()).resolve()
    data_root.mkdir(parents=True, exist_ok=True)
    (data_root / "processos").mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "root": str(data_root),
        "catalog": migrate_catalog(root=data_root),
        "workspace": migrate_workspace(root=data_root),
        "processes": {},
    }

    for process_id in _materialized_process_ids(data_root):
        target = process_db_path(process_id, data_root)
        if not target.is_file():
            continue
        result["processes"][process_id] = migrate_process_db(
            target,
            process_id=process_id,
        )
    return result
