"""Persistência factual de movements e provider artifacts no Jurídico.

Este módulo implementa a camada factual de proveniência de provedores (e-SAJ, DJEN,
PJe, etc.), desacoplando o envelope processual (movement) e o upload bruto
(provider_artifact) da extração física (documents/pages) e das unidades
intelectuais/semânticas (logical_documents).
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

MIGRATION_VERSION = "provider-artifacts-v1"
ID_NAMESPACE = uuid.UUID("7f3e098a-2481-5c8e-a9b1-6a2c1e847392")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _id(kind: str, *parts: object) -> str:
    value = "|".join(str(part) for part in parts)
    return f"{kind}_{uuid.uuid5(ID_NAMESPACE, value).hex}"


SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations(
  version TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS process_movements(
  movement_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  movement_type TEXT NOT NULL,
  occurred_at TEXT,
  content TEXT,
  source_movement_id TEXT,
  movement_code TEXT,
  signer TEXT,
  movement_fingerprint TEXT,
  provenance_json TEXT NOT NULL DEFAULT '{}',
  FOREIGN KEY(process_id) REFERENCES processes(process_id)
);

CREATE TABLE IF NOT EXISTS provider_artifacts(
  provider_artifact_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  movement_id TEXT,
  source_artifact_id TEXT,
  artifact_fingerprint TEXT,
  artifact_type TEXT,
  title TEXT,
  signer TEXT,
  source_origin TEXT NOT NULL,
  provenance_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(process_id) REFERENCES processes(process_id),
  FOREIGN KEY(movement_id) REFERENCES process_movements(movement_id)
);

CREATE INDEX IF NOT EXISTS idx_provider_artifacts_process ON provider_artifacts(process_id);
CREATE INDEX IF NOT EXISTS idx_provider_artifacts_movement ON provider_artifacts(movement_id);

CREATE TABLE IF NOT EXISTS provider_artifact_pages(
  provider_artifact_id TEXT NOT NULL,
  canonical_page_id TEXT NOT NULL,
  position INTEGER NOT NULL CHECK(position > 0),
  PRIMARY KEY(provider_artifact_id, canonical_page_id),
  UNIQUE(provider_artifact_id, position),
  FOREIGN KEY(provider_artifact_id) REFERENCES provider_artifacts(provider_artifact_id),
  FOREIGN KEY(canonical_page_id) REFERENCES canonical_pages(canonical_page_id)
);

CREATE INDEX IF NOT EXISTS idx_provider_artifact_pages_canonical ON provider_artifact_pages(canonical_page_id);
"""


def migrate_connection(db: sqlite3.Connection) -> dict[str, Any]:
    """Aplica a migração provider-artifacts-v1 na conexão fornecida."""
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    
    # 1. Garante que process_movements tenha as novas colunas
    has_movements = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='process_movements'").fetchone()
    if has_movements:
        cols = {row[1] for row in db.execute("PRAGMA table_info(process_movements)")}
        alterations = [
            ("source_movement_id", "TEXT"),
            ("movement_code", "TEXT"),
            ("signer", "TEXT"),
            ("movement_fingerprint", "TEXT"),
            ("provenance_json", "TEXT NOT NULL DEFAULT '{}'"),
        ]
        for col_name, col_type in alterations:
            if col_name not in cols:
                db.execute(f"ALTER TABLE process_movements ADD COLUMN {col_name} {col_type}")
    
    # 2. Executa o DDL aditivo
    db.executescript(SCHEMA)

    # 3. Registra a versão de migração
    applied = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION,)).fetchone()
    if not applied:
        db.execute("INSERT INTO schema_migrations(version, applied_at) VALUES(?,?)", (MIGRATION_VERSION, _now()))
        db.commit()
        return {"migration_version": MIGRATION_VERSION, "already_applied": False}
    
    db.commit()
    return {"migration_version": MIGRATION_VERSION, "already_applied": True}


def migrate(db_path: Path | str) -> dict[str, Any]:
    """Aplica a migração provider-artifacts-v1 no caminho de banco de dados SQLite."""
    conn = sqlite3.connect(str(db_path))
    try:
        return migrate_connection(conn)
    finally:
        conn.close()


def _ensure_process(db: sqlite3.Connection, process_id: str) -> None:
    has_processes = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='processes'").fetchone()
    if has_processes:
        db.execute("INSERT OR IGNORE INTO processes VALUES(?,?,?)", (process_id, "ACTIVE", _now()))


def register_movement(
    db: sqlite3.Connection,
    *,
    process_id: str,
    movement_type: str,
    occurred_at: str | None = None,
    content: str | None = None,
    source_movement_id: str | None = None,
    movement_code: str | None = None,
    signer: str | None = None,
    movement_fingerprint: str | None = None,
    provenance: dict[str, Any] | None = None,
    movement_id: str | None = None,
) -> str:
    """Registra ou atualiza uma movimentação processual com metadados de proveniência."""
    _ensure_process(db, process_id)
    mid = movement_id or _id("mov", process_id, source_movement_id or movement_fingerprint or f"{movement_type}|{occurred_at}")
    prov_str = json.dumps(provenance or {}, ensure_ascii=False)
    db.execute(
        """INSERT INTO process_movements(
            movement_id, process_id, movement_type, occurred_at, content,
            source_movement_id, movement_code, signer, movement_fingerprint, provenance_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(movement_id) DO UPDATE SET
            movement_type=excluded.movement_type,
            occurred_at=coalesce(excluded.occurred_at, process_movements.occurred_at),
            content=coalesce(excluded.content, process_movements.content),
            source_movement_id=coalesce(excluded.source_movement_id, process_movements.source_movement_id),
            movement_code=coalesce(excluded.movement_code, process_movements.movement_code),
            signer=coalesce(excluded.signer, process_movements.signer),
            movement_fingerprint=coalesce(excluded.movement_fingerprint, process_movements.movement_fingerprint),
            provenance_json=excluded.provenance_json
        """,
        (mid, process_id, movement_type, occurred_at, content, source_movement_id, movement_code, signer, movement_fingerprint, prov_str),
    )
    return mid


def register_provider_artifact(
    db: sqlite3.Connection,
    *,
    process_id: str,
    source_origin: str,
    movement_id: str | None = None,
    source_artifact_id: str | None = None,
    artifact_fingerprint: str | None = None,
    artifact_type: str | None = None,
    title: str | None = None,
    signer: str | None = None,
    provenance: dict[str, Any] | None = None,
    provider_artifact_id: str | None = None,
) -> str:
    """Registra um artefato/upload factual de provedor com identidade independente de arquivos físicos."""
    _ensure_process(db, process_id)
    if movement_id:
        has_mov = db.execute("SELECT 1 FROM process_movements WHERE movement_id=?", (movement_id,)).fetchone()
        if not has_mov:
            movement_id = None
    now = _now()
    identity_key = source_artifact_id or artifact_fingerprint or title or "artifact"
    aid = provider_artifact_id or _id(
        "art",
        source_origin,
        process_id,
        identity_key,
    )
    prov_str = json.dumps(provenance or {}, ensure_ascii=False)
    db.execute(
        """INSERT INTO provider_artifacts(
            provider_artifact_id, process_id, movement_id,
            source_artifact_id, artifact_fingerprint,
            artifact_type, title, signer, source_origin, provenance_json,
            created_at, updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(provider_artifact_id) DO UPDATE SET
            movement_id=coalesce(excluded.movement_id, provider_artifacts.movement_id),
            source_artifact_id=coalesce(excluded.source_artifact_id, provider_artifacts.source_artifact_id),
            artifact_fingerprint=coalesce(excluded.artifact_fingerprint, provider_artifacts.artifact_fingerprint),
            artifact_type=coalesce(excluded.artifact_type, provider_artifacts.artifact_type),
            title=coalesce(excluded.title, provider_artifacts.title),
            signer=coalesce(excluded.signer, provider_artifacts.signer),
            source_origin=excluded.source_origin,
            provenance_json=excluded.provenance_json,
            updated_at=excluded.updated_at
        """,
        (
            aid, process_id, movement_id,
            source_artifact_id, artifact_fingerprint,
            artifact_type, title, signer, source_origin, prov_str,
            now, now,
        ),
    )
    return aid


def link_provider_artifact_pages(
    db: sqlite3.Connection,
    provider_artifact_id: str,
    canonical_page_ids: Sequence[str],
) -> int:
    """Associa em ordem sequencial um conjunto de canonical_pages ao artefato factual."""
    db.execute("DELETE FROM provider_artifact_pages WHERE provider_artifact_id=?", (provider_artifact_id,))
    count = 0
    for idx, cp_id in enumerate(canonical_page_ids, start=1):
        db.execute(
            """INSERT INTO provider_artifact_pages(provider_artifact_id, canonical_page_id, position)
            VALUES(?,?,?)""",
            (provider_artifact_id, cp_id, idx),
        )
        count += 1
    return count
