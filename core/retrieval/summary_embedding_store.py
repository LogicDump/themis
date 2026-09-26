"""Derived EmbeddingGemma vectors for CURRENT movement summaries."""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.retrieval.vector_store import (
    EMBEDDING_MODEL_NAME,
    EMBEDDING_MODEL_VERSION,
    pack_vector,
    unpack_vector,
)

MIGRATION_VERSION = "movement-summary-embeddings-v1"


def embedding_input(title: str | None, summary_text: str) -> str:
    return f"{title or ''}\n{summary_text}"


def embedding_input_hash(title: str | None, summary_text: str) -> str:
    return hashlib.sha256(embedding_input(title, summary_text).encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def migrate_connection(db: sqlite3.Connection) -> None:
    applied = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
    ).fetchone() and db.execute(
        "SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION,)
    ).fetchone()
    has_table = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='movement_summary_embeddings'"
    ).fetchone()
    if applied and has_table:
        return
    db.execute("""CREATE TABLE IF NOT EXISTS movement_summary_embeddings(
      movement_id TEXT PRIMARY KEY,
      summary_id TEXT NOT NULL,
      source_hash TEXT NOT NULL,
      input_hash TEXT NOT NULL,
      model TEXT NOT NULL,
      backend TEXT NOT NULL,
      model_version TEXT NOT NULL,
      quantization TEXT NOT NULL,
      dim INTEGER NOT NULL,
      vector_blob BLOB NOT NULL,
      updated_at TEXT NOT NULL,
      FOREIGN KEY(movement_id) REFERENCES movements(movement_id) ON DELETE CASCADE
    )""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_movement_summary_embeddings_model ON movement_summary_embeddings(model)")
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='movements'").fetchone():
        db.execute("""CREATE TRIGGER IF NOT EXISTS movement_summary_embeddings_movement_update
          AFTER UPDATE OF title,payload_json ON movements BEGIN
            DELETE FROM movement_summary_embeddings WHERE movement_id=NEW.movement_id;
          END""")
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='movement_summaries'").fetchone():
        db.execute("""CREATE TRIGGER IF NOT EXISTS movement_summary_embeddings_summary_delete
          AFTER DELETE ON movement_summaries BEGIN
            DELETE FROM movement_summary_embeddings
            WHERE movement_id=OLD.movement_id AND summary_id=OLD.summary_id;
          END""")
    db.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?,?)", (MIGRATION_VERSION, _now()))
    db.commit()


def _current_rows(db: sqlite3.Connection, movement_ids: set[str] | None = None) -> list[dict[str, Any]]:
    exists = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    required = {"movements", "movement_summaries", "movement_summary_source_state"}
    if not required.issubset(exists):
        return []
    movement_columns = {row[1] for row in db.execute("PRAGMA table_info(movements)")}
    title_expr = "m.title" if "title" in movement_columns else "'' AS title"
    where_ids = ""
    params: list[Any] = []
    if movement_ids is not None:
        if not movement_ids:
            return []
        where_ids = f" AND m.movement_id IN ({','.join('?' for _ in movement_ids)})"
        params.extend(sorted(movement_ids))
    rows = db.execute(
        f"""SELECT m.movement_id,{title_expr},s.summary_id,s.summary_text,s.source_hash
           FROM movements m JOIN movement_summary_source_state state ON state.movement_id=m.movement_id
           JOIN movement_summaries s ON s.movement_id=m.movement_id
           WHERE state.eligible=1 AND s.summary_version=(
             SELECT max(latest.summary_version) FROM movement_summaries latest
             WHERE latest.movement_id=m.movement_id
           ) AND s.source_hash=state.source_hash AND trim(s.summary_text)<>''""" + where_ids,
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def sync_current_embeddings(db: sqlite3.Connection, movement_ids: list[str] | set[str]) -> dict[str, int]:
    """Embed changed CURRENT summaries after the summary transaction commits."""
    ids = {str(item) for item in movement_ids}
    if not ids:
        return {"updated": 0, "removed": 0}
    db.commit()
    rows = _current_rows(db, ids)
    by_id = {row["movement_id"]: row for row in rows}
    stale_ids = ids - set(by_id)
    if stale_ids:
        db.executemany("DELETE FROM movement_summary_embeddings WHERE movement_id=?", [(item,) for item in stale_ids])
        db.commit()
    existing = {
        row[0]: (row[1], row[2], row[3], row[4], row[5])
        for row in db.execute(
            f"SELECT movement_id,summary_id,source_hash,input_hash,model,model_version FROM movement_summary_embeddings WHERE movement_id IN ({','.join('?' for _ in by_id)})",
            tuple(by_id),
        ).fetchall()
    } if by_id else {}
    pending = [row for row in rows if existing.get(row["movement_id"]) != (
        row["summary_id"], row["source_hash"], embedding_input_hash(row.get("title"), row["summary_text"]),
        EMBEDDING_MODEL_NAME, EMBEDDING_MODEL_VERSION,
    )]
    if not pending:
        return {"updated": 0, "removed": len(stale_ids)}
    from core.retrieval.onnx_embed import generate_embeddings_batch_onnx

    texts = [embedding_input(row.get("title"), row["summary_text"]) for row in pending]
    vectors: list[list[float] | None] = []
    for offset in range(0, len(texts), 24):
        vectors.extend(generate_embeddings_batch_onnx(texts[offset:offset + 24]))
    updated = 0
    try:
        db.execute("BEGIN")
        still_current = {row["movement_id"]: row for row in _current_rows(db, {row["movement_id"] for row in pending})}
        for row, vector in zip(pending, vectors):
            current = still_current.get(row["movement_id"])
            if not vector or not current or any(current[key] != row[key] for key in ("summary_id", "source_hash", "summary_text", "title")):
                continue
            db.execute("""INSERT INTO movement_summary_embeddings(
                movement_id,summary_id,source_hash,input_hash,model,backend,model_version,quantization,dim,vector_blob,updated_at
              ) VALUES(?,?,?,?,?,'onnx',?,'int8',?,?,?)
              ON CONFLICT(movement_id) DO UPDATE SET summary_id=excluded.summary_id,
                source_hash=excluded.source_hash,input_hash=excluded.input_hash,model=excluded.model,
                backend=excluded.backend,model_version=excluded.model_version,quantization=excluded.quantization,
                dim=excluded.dim,vector_blob=excluded.vector_blob,updated_at=excluded.updated_at""",
                (row["movement_id"], row["summary_id"], row["source_hash"],
                 embedding_input_hash(row.get("title"), row["summary_text"]), EMBEDDING_MODEL_NAME,
                 EMBEDDING_MODEL_VERSION, len(vector), pack_vector(vector), _now()))
            updated += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"updated": updated, "removed": len(stale_ids)}


def rebuild_index(db_path: Path | str, *, batch_size: int = 24) -> dict[str, Any]:
    """Rebuild all current vectors; reads/embeds outside any write transaction."""
    target = Path(db_path).resolve()
    db = sqlite3.connect(str(target))
    db.row_factory = sqlite3.Row
    try:
        migrate_connection(db)
        rows = _current_rows(db)
    finally:
        db.close()
    from core.retrieval.onnx_embed import generate_embeddings_batch_onnx

    vectors: list[list[float] | None] = []
    texts = [embedding_input(row.get("title"), row["summary_text"]) for row in rows]
    size = max(1, int(batch_size))
    for offset in range(0, len(texts), size):
        vectors.extend(generate_embeddings_batch_onnx(texts[offset:offset + size]))
    db = sqlite3.connect(str(target))
    db.row_factory = sqlite3.Row
    try:
        db.execute("BEGIN")
        current = {row["movement_id"]: row for row in _current_rows(db)}
        written = 0
        for row, vector in zip(rows, vectors):
            valid = current.get(row["movement_id"])
            if not vector or not valid or any(valid[key] != row[key] for key in ("summary_id", "source_hash", "summary_text", "title")):
                continue
            db.execute("""INSERT INTO movement_summary_embeddings(
                movement_id,summary_id,source_hash,input_hash,model,backend,model_version,quantization,dim,vector_blob,updated_at
              ) VALUES(?,?,?,?,?,'onnx',?,'int8',?,?,?)
              ON CONFLICT(movement_id) DO UPDATE SET summary_id=excluded.summary_id,
                source_hash=excluded.source_hash,input_hash=excluded.input_hash,model=excluded.model,
                backend=excluded.backend,model_version=excluded.model_version,quantization=excluded.quantization,
                dim=excluded.dim,vector_blob=excluded.vector_blob,updated_at=excluded.updated_at""",
                (row["movement_id"], row["summary_id"], row["source_hash"],
                 embedding_input_hash(row.get("title"), row["summary_text"]), EMBEDDING_MODEL_NAME,
                 EMBEDDING_MODEL_VERSION, len(vector), pack_vector(vector), _now()))
            written += 1
        # Anything no longer eligible/current is obsolete derived state.
        db.execute("""DELETE FROM movement_summary_embeddings WHERE NOT EXISTS(
          SELECT 1 FROM movements m JOIN movement_summary_source_state state ON state.movement_id=m.movement_id
          JOIN movement_summaries s ON s.movement_id=m.movement_id
          WHERE m.movement_id=movement_summary_embeddings.movement_id AND state.eligible=1
            AND s.summary_version=(SELECT max(latest.summary_version) FROM movement_summaries latest WHERE latest.movement_id=m.movement_id)
            AND s.summary_id=movement_summary_embeddings.summary_id AND s.source_hash=state.source_hash
            AND s.source_hash=movement_summary_embeddings.source_hash
        )""")
        removed = db.execute("SELECT changes()").fetchone()[0]
        db.commit()
        return {"current": len(rows), "written": written, "removed": removed}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def current_vectors(db: sqlite3.Connection, summaries: list[dict[str, Any]], query_dim: int) -> list[list[float] | None]:
    """Read vectors only when their summary/source/input identity still matches."""
    if not summaries or not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='movement_summary_embeddings'").fetchone():
        return [None] * len(summaries)
    ids = [row["movement_id"] for row in summaries]
    stored = {row["movement_id"]: row for row in db.execute(
        f"SELECT movement_id,summary_id,source_hash,input_hash,model,backend,model_version,quantization,dim,vector_blob FROM movement_summary_embeddings WHERE movement_id IN ({','.join('?' for _ in ids)})",
        ids,
    ).fetchall()}
    vectors: list[list[float] | None] = []
    for summary in summaries:
        item = stored.get(summary["movement_id"])
        expected_hash = embedding_input_hash(summary.get("title"), summary["summary_text"])
        if (not item or item["summary_id"] != summary.get("summary_id") or item["source_hash"] != summary.get("source_hash")
            or item["input_hash"] != expected_hash or item["model"] != EMBEDDING_MODEL_NAME
            or item["backend"] != "onnx" or item["model_version"] != EMBEDDING_MODEL_VERSION
            or item["quantization"] != "int8" or item["dim"] != query_dim):
            vectors.append(None)
            continue
        try:
            vectors.append(unpack_vector(item["vector_blob"], item["dim"]))
        except (ValueError, TypeError):
            vectors.append(None)
    return vectors
