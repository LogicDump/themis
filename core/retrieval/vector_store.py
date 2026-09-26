"""Armazenamento vetorial derivado e desacoplado em SQLite com validação estrita de espaço vetorial."""
from __future__ import annotations

import logging
import math
import sqlite3
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.runtime_paths import index_db_path

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "embeddinggemma:300m"
EMBEDDING_MODEL_FAMILY = "embeddinggemma"
EMBEDDING_MODEL_VERSION = "v1"
EMBEDDING_DIM = 768


class IncompatibleEmbeddingSpaceError(ValueError):
    """Lançado quando há tentativa de misturar embeddings de modelos ou dimensões incompatíveis."""
    pass


SCHEMA = """
CREATE TABLE IF NOT EXISTS page_embeddings(
  page_id TEXT NOT NULL,
  document_id TEXT NOT NULL,
  process_id TEXT NOT NULL,
  page_number INTEGER NOT NULL,
  model TEXT NOT NULL,
  backend TEXT NOT NULL DEFAULT 'onnx',
  model_version TEXT NOT NULL DEFAULT 'v1',
  quantization TEXT NOT NULL DEFAULT 'int8',
  dim INTEGER NOT NULL,
  vector_blob BLOB NOT NULL,
  content_hash TEXT,
  updated_at TEXT NOT NULL,
  PRIMARY KEY(page_id, model)
);
CREATE INDEX IF NOT EXISTS page_embeddings_process ON page_embeddings(process_id, model);

CREATE TABLE IF NOT EXISTS vector_index_metadata(
  process_id TEXT NOT NULL,
  model TEXT NOT NULL,
  backend TEXT NOT NULL,
  model_version TEXT NOT NULL,
  quantization TEXT NOT NULL,
  dim INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY(process_id, model)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_vector_db_path(base_index_db: Path | None = None) -> Path:
    if base_index_db is not None:
        cand = base_index_db.parent / "themis_vectors.db"
        if cand.exists():
            return cand
        cand_leg = base_index_db.parent / "juridico_vectors.db"
        if cand_leg.exists():
            return cand_leg
        return cand
    try:
        from core.runtime_paths import vector_db_path
        return vector_db_path()
    except Exception:
        return Path("themis_vectors.db").resolve()


def normalize_model_family(model_name: str) -> str:
    """Extrai a família do modelo (ex: 'embeddinggemma:300m' -> 'embeddinggemma')."""
    lower = model_name.strip().lower()
    if ":" in lower:
        return lower.split(":", 1)[0]
    return lower


def is_exact_space_match(
    sig_a: dict[str, Any],
    sig_b: dict[str, Any],
) -> bool:
    """Exige correspondência exata de model + model_version + backend + quantization + dim."""
    return (
        str(sig_a.get("model", "")).strip().lower() == str(sig_b.get("model", "")).strip().lower()
        and str(sig_a.get("model_version", "")).strip().lower() == str(sig_b.get("model_version", "")).strip().lower()
        and str(sig_a.get("backend", "")).strip().lower() == str(sig_b.get("backend", "")).strip().lower()
        and str(sig_a.get("quantization", "")).strip().lower() == str(sig_b.get("quantization", "")).strip().lower()
        and int(sig_a.get("dim", 0)) == int(sig_b.get("dim", 0))
    )


def are_spaces_compatible(model_a: str, dim_a: int, model_b: str, dim_b: int) -> bool:
    """Verifica se dois modelos pertencem à mesma família e dimensão."""
    if dim_a != dim_b:
        return False
    family_a = normalize_model_family(model_a)
    family_b = normalize_model_family(model_b)
    return family_a == family_b


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


def pack_vector(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


def unpack_vector(blob: bytes, dim: int) -> list[float]:
    return list(struct.unpack(f"{dim}f", blob))


class VectorStore:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path or default_vector_db_path()).resolve()
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.executescript(SCHEMA)
            # Migração dinâmica de colunas para bancos pré-existentes
            cursor = conn.execute("PRAGMA table_info(page_embeddings)")
            cols = {row[1] for row in cursor.fetchall()}
            if "backend" not in cols:
                conn.execute("ALTER TABLE page_embeddings ADD COLUMN backend TEXT NOT NULL DEFAULT 'onnx'")
            if "model_version" not in cols:
                conn.execute("ALTER TABLE page_embeddings ADD COLUMN model_version TEXT NOT NULL DEFAULT 'v1'")
            if "quantization" not in cols:
                conn.execute("ALTER TABLE page_embeddings ADD COLUMN quantization TEXT NOT NULL DEFAULT 'int8'")
            if "content_hash" not in cols:
                conn.execute("ALTER TABLE page_embeddings ADD COLUMN content_hash TEXT")
            conn.commit()
        finally:
            conn.close()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def get_process_index_metadata(self, process_id: str) -> list[dict[str, Any]]:
        conn = self.connect()
        try:
            rows = conn.execute(
                """SELECT process_id, model, backend, model_version, quantization, dim, created_at, updated_at
                FROM vector_index_metadata
                WHERE process_id=?""",
                (process_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_index_metadata(self, process_id: str, model: str = EMBEDDING_MODEL_NAME) -> dict[str, Any] | None:
        conn = self.connect()
        try:
            row = conn.execute(
                """SELECT process_id, model, backend, model_version, quantization, dim, created_at, updated_at
                FROM vector_index_metadata
                WHERE process_id=? AND model=?""",
                (process_id, model),
            ).fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def save_embedding(
        self,
        page_id: str,
        document_id: str,
        process_id: str,
        page_number: int,
        vector: list[float],
        model: str = EMBEDDING_MODEL_NAME,
        backend: str = "onnx",
        model_version: str = EMBEDDING_MODEL_VERSION,
        quantization: str = "int8",
    ) -> None:
        if len(vector) != EMBEDDING_DIM:
            raise IncompatibleEmbeddingSpaceError(
                f"Dimensão vetorial incompatível: esperado {EMBEDDING_DIM}, recebido {len(vector)}"
            )

        incoming_sig = {
            "model": model,
            "model_version": model_version,
            "backend": backend,
            "quantization": quantization,
            "dim": len(vector),
        }

        # Validação estrita de isolamento vetorial: exige correspondência exata de model+version+backend+quantization+dim
        existing_metas = self.get_process_index_metadata(process_id)
        for existing in existing_metas:
            if not is_exact_space_match(existing, incoming_sig):
                raise IncompatibleEmbeddingSpaceError(
                    f"Isolamento vetorial estrito violado para o processo {process_id}: "
                    f"índice existente gravado com (model='{existing['model']}', version='{existing['model_version']}', backend='{existing['backend']}', quant='{existing['quantization']}', dim={existing['dim']}), "
                    f"tentativa de gravar com (model='{model}', version='{model_version}', backend='{backend}', quant='{quantization}', dim={len(vector)}). "
                    f"Nunca é permitida a mistura de backends/quantizações no mesmo índice. Mudança de backend exige reindexação explícita (clear_process_embeddings)."
                )

        blob = pack_vector(vector)
        now = _now()
        conn = self.connect()
        try:
            conn.execute(
                """INSERT INTO page_embeddings(
                    page_id, document_id, process_id, page_number,
                    model, backend, model_version, quantization, dim, vector_blob, updated_at
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(page_id, model) DO UPDATE SET
                  document_id=excluded.document_id,
                  process_id=excluded.process_id,
                  page_number=excluded.page_number,
                  backend=excluded.backend,
                  model_version=excluded.model_version,
                  quantization=excluded.quantization,
                  dim=excluded.dim,
                  vector_blob=excluded.vector_blob,
                  updated_at=excluded.updated_at""",
                (page_id, document_id, process_id, page_number, model, backend, model_version, quantization, len(vector), blob, now),
            )

            # Upsert nos metadados do índice
            conn.execute(
                """INSERT INTO vector_index_metadata(
                    process_id, model, backend, model_version, quantization, dim, created_at, updated_at
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(process_id, model) DO UPDATE SET
                  backend=excluded.backend,
                  model_version=excluded.model_version,
                  quantization=excluded.quantization,
                  dim=excluded.dim,
                  updated_at=excluded.updated_at""",
                (process_id, model, backend, model_version, quantization, len(vector), now, now),
            )
            conn.commit()
        finally:
            conn.close()

    def get_process_vectors(
        self,
        process_id: str,
        model: str = EMBEDDING_MODEL_NAME,
    ) -> list[dict[str, Any]]:
        conn = self.connect()
        try:
            rows = conn.execute(
                """SELECT page_id, document_id, process_id, page_number, model, backend, model_version, quantization, dim, vector_blob
                FROM page_embeddings
                WHERE process_id=? AND model=?""",
                (process_id, model),
            ).fetchall()
            results = []
            for r in rows:
                vec = unpack_vector(r["vector_blob"], r["dim"])
                results.append({
                    "page_id": r["page_id"],
                    "document_id": r["document_id"],
                    "process_id": r["process_id"],
                    "page_number": r["page_number"],
                    "model": r["model"],
                    "backend": r["backend"],
                    "model_version": r["model_version"],
                    "quantization": r["quantization"],
                    "dim": r["dim"],
                    "vector": vec,
                })
            return results
        finally:
            conn.close()

    def get_indexed_page_ids(
        self,
        process_id: str,
        model: str = EMBEDDING_MODEL_NAME,
    ) -> set[str]:
        conn = self.connect()
        try:
            rows = conn.execute(
                "SELECT page_id FROM page_embeddings WHERE process_id=? AND model=?",
                (process_id, model),
            ).fetchall()
            return {r[0] for r in rows}
        finally:
            conn.close()

    def clear_process_embeddings(
        self,
        process_id: str,
        model: str = EMBEDDING_MODEL_NAME,
    ) -> None:
        """Remove todos os embeddings de um processo para reindexação limpa."""
        conn = self.connect()
        try:
            conn.execute("DELETE FROM page_embeddings WHERE process_id=? AND model=?", (process_id, model))
            conn.execute("DELETE FROM vector_index_metadata WHERE process_id=? AND model=?", (process_id, model))
            conn.commit()
        finally:
            conn.close()
