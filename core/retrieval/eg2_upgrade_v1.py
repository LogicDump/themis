"""Resumable EG2 indexing for existing Process Packages; no PDF/AI regeneration."""
from __future__ import annotations

import hashlib
import logging
import math
import os
import sqlite3
import struct
from contextlib import contextmanager
from pathlib import Path

from core.retrieval import embeddinggemma2_litert as eg2
from core.retrieval import summary_embedding_store
from core.retrieval.vector_store import VectorStore, is_exact_space_match, pack_vector

_LOG = logging.getLogger(__name__)
_FIELDS = ("model", "backend", "model_version", "quantization", "dim")


def _source_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def _matches(row, signature, source_hash: str) -> bool:
    if row is None or not is_exact_space_match(dict(row), signature):
        return False
    blob = row["vector_blob"]
    if row["content_hash"] != source_hash or len(blob or b"") != eg2.DIM * 4:
        return False
    return all(math.isfinite(v) for v in struct.unpack(f"{eg2.DIM}f", blob))


def _sources(db: sqlite3.Connection, process_id: str) -> list[dict]:
    return [dict(row) for row in db.execute(
        """SELECT p.page_id,p.document_id,p.page_number,
                  coalesce(p.content,'') AS content
           FROM pages p JOIN documents d ON d.document_id=p.document_id
           WHERE d.process_id=? ORDER BY p.page_id""", (process_id,)
    )]


def _indexed(db: sqlite3.Connection, process_id: str) -> dict:
    return {row["page_id"]: row for row in db.execute(
        """SELECT page_id,model,backend,model_version,quantization,dim,
                  content_hash,vector_blob FROM page_embeddings
           WHERE process_id=? AND model=?""", (process_id, eg2.MODEL)
    )}


def upgrade_process(db_path: Path, process_id: str, *, batch_size: int = 16) -> dict:
    """Build EG2 pages in resumable batches, then atomically publish metadata."""
    target = Path(db_path).resolve()
    if not target.is_file():
        raise FileNotFoundError(target)
    # Creates only the two derived vector tables, never edits legal source tables.
    VectorStore(target)
    db = sqlite3.connect(str(target), timeout=30)
    db.row_factory = sqlite3.Row
    try:
        names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"pages", "documents"}.issubset(names):
            return {"status": "NO_DOCUMENTS"}
        pages = _sources(db, process_id)
        if not pages:
            return {"status": "EMPTY", "pages": 0}
        published = db.execute(
            """SELECT model,backend,model_version,quantization,dim
               FROM vector_index_metadata WHERE process_id=? AND model=?""",
            (process_id, eg2.MODEL),
        ).fetchone()
        staging = [dict(r) for r in db.execute(
            """SELECT DISTINCT model,backend,model_version,quantization,dim
               FROM page_embeddings WHERE process_id=? AND model=?""",
            (process_id, eg2.MODEL),
        )]
        if len(staging) > 1:
            return {"status": "INCOMPATIBLE_INDEX"}
        pinned = dict(published) if published else (staging[0] if staging else None)
        if pinned and (pinned["model"] != eg2.MODEL or pinned["model_version"] != eg2.VERSION
                       or pinned["quantization"] != eg2.QUANTIZATION or pinned["dim"] != eg2.DIM):
            return {"status": "INCOMPATIBLE_INDEX"}
        if staging and published and not is_exact_space_match(staging[0], dict(published)):
            return {"status": "INCOMPATIBLE_INDEX"}
        indexed = _indexed(db, process_id)
        if published and all(_matches(indexed.get(p["page_id"]), dict(published), _source_hash(p["content"])) for p in pages) and len(indexed) == len(pages):
            summaries_written = _upgrade_summaries(db)
            return {"status": "READY", "pages": len(pages), "written": 0,
                    "summaries_written": summaries_written}
        if published:
            # An already published index must never be repaired in-place.
            return {"status": "PUBLISHED_INDEX_STALE", "pages": len(pages)}
        signature = eg2.active_signature(pinned["backend"] if pinned else None)
        if pinned and not is_exact_space_match(pinned, signature):
            return {"status": "INCOMPATIBLE_INDEX"}
        pending = [p for p in pages if not _matches(indexed.get(p["page_id"]), signature, _source_hash(p["content"]))]
        written = 0
        for offset in range(0, len(pending), max(1, batch_size)):
            batch = pending[offset:offset + max(1, batch_size)]
            texts = [p["content"].strip() or "Página sem texto reconhecido." for p in batch]
            vectors, batch_sig = eg2.embed_many(texts, required_backend=signature["backend"])
            if not is_exact_space_match(signature, batch_sig) or len(vectors) != len(batch):
                raise RuntimeError("Lote EG2 ou assinatura incompatível")
            if any(v is None or len(v) != eg2.DIM or not all(math.isfinite(x) for x in v) for v in vectors):
                raise RuntimeError("Vetor EG2 inválido")
            db.execute("BEGIN IMMEDIATE")
            try:
                live = {p["page_id"]: p for p in _sources(db, process_id)}
                if any(p["page_id"] not in live or _source_hash(live[p["page_id"]]["content"]) != _source_hash(p["content"]) for p in batch):
                    db.rollback()
                    return {"status": "SOURCES_CHANGED", "written": written}
                db.executemany(
                    """INSERT INTO page_embeddings(
                         page_id,document_id,process_id,page_number,model,backend,
                         model_version,quantization,dim,vector_blob,content_hash,updated_at
                       ) VALUES (?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
                       ON CONFLICT(page_id,model) DO UPDATE SET
                         document_id=excluded.document_id,process_id=excluded.process_id,
                         page_number=excluded.page_number,backend=excluded.backend,
                         model_version=excluded.model_version,quantization=excluded.quantization,
                         dim=excluded.dim,vector_blob=excluded.vector_blob,
                         content_hash=excluded.content_hash,updated_at=excluded.updated_at""",
                    [(p["page_id"], p["document_id"], process_id, p["page_number"],
                      eg2.MODEL, signature["backend"], eg2.VERSION, eg2.QUANTIZATION,
                      eg2.DIM, pack_vector(vec), _source_hash(p["content"]))
                     for p, vec in zip(batch, vectors)],
                )
                db.commit()
            except Exception:
                db.rollback()
                raise
            written += len(batch)

        # Publication and source recheck take one write transaction.
        # Readers can never observe the EG2 metadata while rows are incomplete.
        db.execute("BEGIN IMMEDIATE")
        try:
            current = _sources(db, process_id)
            staged = _indexed(db, process_id)
            if (len(current) != len(pages) or len(staged) != len(current)
                or any(not _matches(staged.get(p["page_id"]), signature, _source_hash(p["content"])) for p in current)):
                db.rollback()
                return {"status": "SOURCES_CHANGED", "written": written}
            if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise RuntimeError("Integridade SQLite inválida")
            db.execute(
                """INSERT INTO vector_index_metadata(
                     process_id,model,backend,model_version,quantization,dim,created_at,updated_at
                   ) VALUES (?,?,?,?,?,?,datetime('now'),datetime('now'))""",
                (process_id, *[signature[k] for k in _FIELDS]),
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        summary_result = _upgrade_summaries(db)
        return {"status": "READY", "pages": len(pages), "written": written,
                "summaries_written": summary_result}
    finally:
        db.close()


def _upgrade_summaries(db: sqlite3.Connection) -> int:
    # No change to text, summary versions or any AI-generated artifacts.
    summary_embedding_store.migrate_connection(db)
    rows = summary_embedding_store._current_rows(db)
    if not rows:
        return 0
    result = summary_embedding_store.sync_current_embeddings(
        db, [r["movement_id"] for r in rows],
    )
    return result["updated"]


@contextmanager
def _exclusive(root: Path):
    """Cross-process Windows/Linux update lock, held while building all indices."""
    path = root / "config" / "eg2-upgrade.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                yield False
                return
            try:
                yield True
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                yield False
                return
            try:
                yield True
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def upgrade_installed_processes(*, root: Path | None = None) -> dict:
    """Canonical startup worker: auto-discover Process Packages, never PDF/LLM."""
    from core.migration_manager import _materialized_process_ids
    from core.runtime_paths import process_db_path, themis_data_root

    data_root = (root or themis_data_root()).resolve()
    reports = {}
    with _exclusive(data_root) as acquired:
        if not acquired:
            return {"status": "ALREADY_RUNNING", "processes": {}}
        for process_id in _materialized_process_ids(data_root):
            target = process_db_path(process_id, data_root)
            if not target.is_file():
                continue
            try:
                from core.process_operation_lock import process_operation_lock
                with process_operation_lock(process_id, data_root) as acquired_process:
                    reports[process_id] = (upgrade_process(target, process_id) if acquired_process
                                           else {"status": "PROCESS_BUSY"})
            except Exception as exc:
                _LOG.exception("EG2 upgrade: %s precisa de retomada", process_id)
                reports[process_id] = {"status": "RETRY_REQUIRED", "error": str(exc)}
    return {"status": "COMPLETE", "processes": reports}
