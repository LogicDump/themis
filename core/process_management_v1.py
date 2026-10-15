"""Independent Process Package management operations.

Archiving changes only a private workspace-level visibility marker.
Deletion delegates to the existing canonical Process Package remover.
No changes to the acquisition, indexing, rebuild or legal pipelines.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from core.process_operation_lock import ProcessBusyError, process_operation_lock
from core.runtime_paths import process_db_path, themis_data_root, validate_process_id, workspace_db_path


_ARCHIVE_SCHEMA = """
CREATE TABLE IF NOT EXISTS themis_archived_processes(
    process_id TEXT PRIMARY KEY,
    archived_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


def _root(root: Path | str | None) -> Path:
    return Path(root).resolve() if root is not None else themis_data_root().resolve()


def list_archived_processes(*, root: Path | str | None = None) -> list[str]:
    """Read archived CNJs; no migrations or writes during listing."""
    target = workspace_db_path(_root(root))
    if not target.is_file():
        return []
    with closing(sqlite3.connect(f"file:{target.as_posix()}?mode=ro", uri=True)) as db:
        if not db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='themis_archived_processes'"
        ).fetchone():
            return []
        return [r[0] for r in db.execute(
            "SELECT process_id FROM themis_archived_processes ORDER BY process_id"
        )]


def archive_process(process_id: str, *, root: Path | str | None = None) -> dict[str, Any]:
    """Archive a locally materialized process without changing its contents."""
    cnj, data_root = validate_process_id(process_id), _root(root)
    with process_operation_lock(cnj, data_root) as acquired:
        if not acquired:
            raise ProcessBusyError(f"Processo {cnj} ocupado")
        if not process_db_path(cnj, data_root).is_file():
            raise FileNotFoundError(f"Processo não encontrado: {cnj}")
        target = workspace_db_path(data_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(target)) as db:
            db.execute(_ARCHIVE_SCHEMA)
            exists = db.execute(
                "SELECT 1 FROM themis_archived_processes WHERE process_id=?", (cnj,)
            ).fetchone()
            if not exists:
                db.execute("INSERT INTO themis_archived_processes(process_id) VALUES(?)", (cnj,))
            db.commit()
        return {"status": "archived", "process_id": cnj, "changed": not bool(exists)}


def restore_process(process_id: str, *, root: Path | str | None = None) -> dict[str, Any]:
    """Restore a previously archived process to the active list."""
    cnj, data_root = validate_process_id(process_id), _root(root)
    with process_operation_lock(cnj, data_root) as acquired:
        if not acquired:
            raise ProcessBusyError(f"Processo {cnj} ocupado")
        if not process_db_path(cnj, data_root).is_file():
            raise FileNotFoundError(f"Processo não encontrado: {cnj}")
        target = workspace_db_path(data_root)
        if not target.is_file():
            return {"status": "active", "process_id": cnj, "changed": False}
        with closing(sqlite3.connect(target)) as db:
            db.execute(_ARCHIVE_SCHEMA)
            deleted = db.execute(
                "DELETE FROM themis_archived_processes WHERE process_id=?", (cnj,)
            ).rowcount
            db.commit()
        return {"status": "active", "process_id": cnj, "changed": bool(deleted)}


def delete_process_permanently(
    process_id: str, confirm_process_id: str, *, root: Path | str | None = None,
) -> dict[str, Any]:
    """Independent entry: invoke, never reimplement, the canonical deletion."""
    cnj, data_root = validate_process_id(process_id), _root(root)
    if confirm_process_id != cnj:
        raise ValueError("Confirme a exclusão informando exatamente o CNJ completo")
    from core.documentos.themis_documentos import Store
    with process_operation_lock(cnj, data_root) as acquired:
        if not acquired:
            raise ProcessBusyError(f"Processo {cnj} ocupado")
        # Reuse the already implemented and tested remover exactly as-is.
        result = Store(data_root, process_id=cnj).delete_process(cnj, cnj)
        target = workspace_db_path(data_root)
        if target.is_file():
            with closing(sqlite3.connect(target)) as db:
                table = db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='themis_archived_processes'"
                ).fetchone()
                if table:
                    db.execute("DELETE FROM themis_archived_processes WHERE process_id=?", (cnj,))
                    db.commit()
        return result
