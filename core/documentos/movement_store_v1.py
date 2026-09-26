"""Materialização persistente do read model de Movimentos.

`movement_projection()` continua sendo a autoridade de projeção; este módulo
apenas materializa e reconcilia seu resultado no índice process-centric.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MIGRATION_VERSION = "movement-store-v1"
ID_NAMESPACE = uuid.UUID("d9f2e8e6-0e5a-5b91-8c72-5c6e5f3c7a11")

SCHEMA = """
CREATE TABLE IF NOT EXISTS movements(
  movement_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  movement_type TEXT,
  title TEXT,
  actor TEXT,
  occurred_at TEXT,
  protocol TEXT,
  page_start INTEGER,
  page_end INTEGER,
  page_count INTEGER,
  source_hash TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(process_id) REFERENCES processes(process_id)
);

CREATE INDEX IF NOT EXISTS idx_movements_process_sequence
  ON movements(process_id, sequence);
CREATE INDEX IF NOT EXISTS idx_movements_process_source_hash
  ON movements(process_id, source_hash);

CREATE TABLE IF NOT EXISTS movement_pieces(
  movement_id TEXT NOT NULL,
  document_id TEXT,
  piece_order INTEGER NOT NULL,
  page_start INTEGER,
  page_end INTEGER,
  provider_item_identity TEXT,
  provider_document_id TEXT,
  verification_code TEXT,
  piece_json TEXT NOT NULL,
  PRIMARY KEY(movement_id, piece_order),
  FOREIGN KEY(movement_id) REFERENCES movements(movement_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_movement_pieces_document
  ON movement_pieces(document_id);

CREATE TABLE IF NOT EXISTS movement_summaries(
  movement_id TEXT PRIMARY KEY,
  summary TEXT,
  model TEXT,
  model_version TEXT,
  source_hash TEXT,
  generated_at TEXT,
  FOREIGN KEY(movement_id) REFERENCES movements(movement_id) ON DELETE CASCADE
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _piece_identity(piece: dict[str, Any]) -> dict[str, Any]:
    """Return only source facts used to identify a constituent piece."""
    return {
        "document_id": piece.get("document_id") or piece.get("sha256"),
        "provider_item_identity": piece.get("provider_item_identity"),
        "provider_document_id": piece.get("provider_document_id"),
        "page_start": piece.get("page_start", piece.get("folha_inicial")),
        "page_end": piece.get("page_end", piece.get("folha_final")),
        "verification_code": piece.get("verification_code"),
    }


def _stable_id(process_id: str, movement: dict[str, Any]) -> str:
    pieces = [_piece_identity(piece) for piece in movement.get("pieces", [])]
    identity = {
        "process_id": process_id,
        "actor": movement.get("actor"),
        "occurred_at": movement.get("occurred_at", movement.get("source_datetime")),
        "protocol": movement.get("protocol"),
        "movement_type": movement.get("movement_type"),
        "pieces": pieces,
    }
    return f"mov_{uuid.uuid5(ID_NAMESPACE, _json(identity)).hex}"


def _source_hash(movement: dict[str, Any]) -> str:
    # Sequence is a presentation/order attribute, not a source fact.  It must
    # not invalidate an unchanged Movement when a new one is inserted before it.
    factual = {
        key: value for key, value in movement.items()
        if key not in {"movement_id", "act_id", "sequence"}
    }
    return _hash(factual)


def migrate_connection(db: sqlite3.Connection) -> dict[str, Any]:
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    db.executescript(SCHEMA)
    applied = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION,)).fetchone()
    if not applied:
        db.execute("INSERT INTO schema_migrations(version, applied_at) VALUES(?, ?)", (MIGRATION_VERSION, _now()))
    db.commit()
    return {"migration_version": MIGRATION_VERSION, "already_applied": bool(applied)}


def migrate(db_path: Path | str) -> dict[str, Any]:
    db = sqlite3.connect(str(db_path))
    try:
        db.row_factory = sqlite3.Row
        return migrate_connection(db)
    finally:
        db.close()


def _payload(movement: dict[str, Any], movement_id: str) -> dict[str, Any]:
    value = dict(movement)
    value["movement_id"] = movement_id
    value["act_id"] = movement_id
    return value


def materialize_movements(
    db: sqlite3.Connection,
    process_id: str,
    *,
    manifest_or_root: Any = None,
    prune_stale: bool = True,
) -> dict[str, Any]:
    """Project and persist one process without rebuilding unchanged rows.

    Incremental syncs pass ``prune_stale=False`` because a partial delta must
    never be interpreted as deletion of older Movements.
    """
    from core.documentos.procedural_acts_v1 import movement_projection

    migrate_connection(db)
    projected = movement_projection(db, process_id, manifest_or_root=manifest_or_root)
    now = _now()
    desired: dict[str, tuple[dict[str, Any], str]] = {}
    for sequence, raw in enumerate(projected, 1):
        movement_id = _stable_id(process_id, raw)
        value = _payload(raw, movement_id)
        value["sequence"] = sequence
        desired[movement_id] = (value, _source_hash(value))

    existing = {
        row["movement_id"]: row
        for row in db.execute("SELECT * FROM movements WHERE process_id=?", (process_id,)).fetchall()
    }
    inserted = updated = unchanged = 0
    changed_ids: list[str] = []
    for sequence, (movement_id, (value, source_hash)) in enumerate(desired.items(), 1):
        old = existing.get(movement_id)
        if old and old["source_hash"] == source_hash and old["sequence"] == sequence:
            unchanged += 1
            continue
        columns = (
            process_id, sequence, value.get("movement_type"), value.get("title"), value.get("actor"),
            value.get("occurred_at", value.get("source_datetime")), value.get("protocol"),
            value.get("page_start"), value.get("page_end"), value.get("page_count"),
            source_hash, _json(value), old["created_at"] if old else now, now, movement_id,
        )
        db.execute(
            """INSERT INTO movements(
              process_id, sequence, movement_type, title, actor, occurred_at, protocol,
              page_start, page_end, page_count, source_hash, payload_json, created_at, updated_at, movement_id
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(movement_id) DO UPDATE SET
              sequence=excluded.sequence, movement_type=excluded.movement_type, title=excluded.title,
              actor=excluded.actor, occurred_at=excluded.occurred_at, protocol=excluded.protocol,
              page_start=excluded.page_start, page_end=excluded.page_end, page_count=excluded.page_count,
              source_hash=excluded.source_hash, payload_json=excluded.payload_json, updated_at=excluded.updated_at""",
            columns,
        )
        db.execute("DELETE FROM movement_pieces WHERE movement_id=?", (movement_id,))
        for piece_order, piece in enumerate(value.get("pieces", []), 1):
            db.execute(
                """INSERT INTO movement_pieces(
                  movement_id, document_id, piece_order, page_start, page_end,
                  provider_item_identity, provider_document_id, verification_code, piece_json
                ) VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    movement_id, piece.get("document_id") or piece.get("sha256"), piece_order,
                    piece.get("page_start", piece.get("folha_inicial")),
                    piece.get("page_end", piece.get("folha_final")),
                    piece.get("provider_item_identity"), piece.get("provider_document_id"),
                    piece.get("verification_code"), _json(piece),
                ),
            )
        if old:
            updated += 1
        else:
            inserted += 1
        changed_ids.append(movement_id)

    stale = set(existing) - set(desired) if prune_stale else set()
    if stale:
        db.executemany("DELETE FROM movements WHERE movement_id=?", [(movement_id,) for movement_id in stale])
    from core.documentos.movement_summary_store_v1 import refresh_source_state
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='pages'").fetchone():
        refresh_source_state(db, process_id)
    db.commit()
    try:
        from core.retrieval.summary_embedding_store import sync_current_embeddings
        sync_current_embeddings(db, changed_ids)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Falha ao sincronizar índice de embeddings dos summaries após projeção de Movements")
    from core.documentos.process_event_store_v1 import materialize_process_events
    materialize_process_events(db, process_id)
    from core.documentos.deadline_instruction_store_v1 import materialize_process
    materialize_process(db, process_id)
    from core.documentos.deadline_obligation_store_v1 import materialize_process as materialize_deadline_obligations
    materialize_deadline_obligations(db, process_id)
    return {
        "process_id": process_id,
        "projected": len(projected),
        "inserted": inserted,
        "updated": updated,
        "unchanged": unchanged,
        "deleted": len(stale),
        "movement_pieces": db.execute(
            "SELECT count(*) FROM movement_pieces mp JOIN movements m ON m.movement_id=mp.movement_id WHERE m.process_id=?",
            (process_id,),
        ).fetchone()[0],
    }


def read_movements(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    """Read the exact projection contract from persisted payloads only."""
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='movements'").fetchone():
        return []
    rows = db.execute(
        "SELECT payload_json FROM movements WHERE process_id=? ORDER BY sequence", (process_id,)
    ).fetchall()
    return [json.loads(row[0]) for row in rows]
