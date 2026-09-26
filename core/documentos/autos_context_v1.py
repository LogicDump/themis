"""Read model persistido para o caminho quente de GET /autos.

The complete structural/provenance payload remains in its source tables. This
module stores only the small, page-scoped projection consumed by the Autos
contract, so opening an already materialized process is a read-only join.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MIGRATION_VERSION = "autos-context-v1"

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations(
  version TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS canonical_page_autos_context(
  canonical_page_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  document_id TEXT NOT NULL,
  pdf_page INTEGER NOT NULL,
  process_page_number INTEGER,
  integral_pdf_page INTEGER,
  process_folio INTEGER,
  folio_resolution TEXT NOT NULL,
  category TEXT NOT NULL,
  visual_ref_json TEXT,
  document_context_json TEXT,
  source_ref_json TEXT NOT NULL,
  source_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(canonical_page_id) REFERENCES canonical_pages(canonical_page_id)
);

CREATE INDEX IF NOT EXISTS canonical_page_autos_context_process
  ON canonical_page_autos_context(process_id, pdf_page);
"""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _dump(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _hash(row: dict[str, Any]) -> str:
    material = json.dumps(row, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def ensure_schema(db: sqlite3.Connection) -> None:
    db.executescript(SCHEMA)
    db.execute(
        "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)",
        (MIGRATION_VERSION, _now()),
    )


def table_exists(db: sqlite3.Connection) -> bool:
    return db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='canonical_page_autos_context'"
    ).fetchone() is not None


def process_is_complete(db: sqlite3.Connection, process_id: str, expected_pages: int) -> bool:
    if not table_exists(db):
        return False
    row = db.execute(
        "SELECT count(*) FROM canonical_page_autos_context WHERE process_id=?",
        (process_id,),
    ).fetchone()
    return int(row[0]) == int(expected_pages) and int(expected_pages) > 0


def materialize_process(db_path: Path, process_id: str) -> dict[str, int | str]:
    """Materialize the exact current Autos payload once, then upsert its rows."""
    target = Path(db_path).resolve()
    db = sqlite3.connect(str(target))
    db.row_factory = sqlite3.Row
    try:
        ensure_schema(db)
        from core.api.core_api import autos

        payload = autos(process_id, path=target)
        if not payload or payload.get("status") != "ready":
            db.rollback()
            return {"inserted": 0, "updated": 0, "unchanged": 0, "deleted": 0, "status": "not-ready"}

        mapping_rows = db.execute(
            """SELECT o.document_id, o.pdf_page, o.canonical_page_id
               FROM canonical_page_observations o
               JOIN canonical_pages cp ON cp.canonical_page_id=o.canonical_page_id
               WHERE cp.process_id=?""",
            (process_id,),
        ).fetchall()
        canonical_by_page = {(r["document_id"], int(r["pdf_page"])): r["canonical_page_id"] for r in mapping_rows}
        now = _now()
        inserted = updated = unchanged = 0
        current_ids: list[str] = []
        for page in payload.get("pages", []):
            key = (page["document_id"], int(page["page"]))
            canonical_id = canonical_by_page.get(key)
            if not canonical_id:
                raise RuntimeError(f"canonical page ausente para {key!r}")
            current_ids.append(canonical_id)
            source_ref = page.get("source_ref") or {}
            record: dict[str, Any] = {
                "canonical_page_id": canonical_id,
                "process_id": process_id,
                "document_id": page["document_id"],
                "pdf_page": int(page["page"]),
                "process_page_number": page.get("process_page_number"),
                "integral_pdf_page": page.get("integral_pdf_page"),
                "process_folio": source_ref.get("process_folio"),
                "folio_resolution": source_ref.get("folio_resolution") or "UNKNOWN",
                "category": page.get("category") or "NATIVE_VALID",
                "visual_ref_json": _dump(page.get("visual_ref")),
                "document_context_json": _dump(page.get("document_context")),
                "source_ref_json": _dump(source_ref) or "{}",
            }
            source_hash = _hash(record)
            old = db.execute(
                "SELECT source_hash FROM canonical_page_autos_context WHERE canonical_page_id=?",
                (canonical_id,),
            ).fetchone()
            if old and old[0] == source_hash:
                unchanged += 1
                continue
            db.execute(
                """INSERT INTO canonical_page_autos_context(
                    canonical_page_id,process_id,document_id,pdf_page,
                    process_page_number,integral_pdf_page,process_folio,
                    folio_resolution,category,visual_ref_json,document_context_json,
                    source_ref_json,source_hash,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(canonical_page_id) DO UPDATE SET
                    process_id=excluded.process_id, document_id=excluded.document_id,
                    pdf_page=excluded.pdf_page, process_page_number=excluded.process_page_number,
                    integral_pdf_page=excluded.integral_pdf_page, process_folio=excluded.process_folio,
                    folio_resolution=excluded.folio_resolution, category=excluded.category,
                    visual_ref_json=excluded.visual_ref_json,
                    document_context_json=excluded.document_context_json,
                    source_ref_json=excluded.source_ref_json, source_hash=excluded.source_hash,
                    updated_at=excluded.updated_at""",
                (*record.values(), source_hash, now, now),
            )
            if old:
                updated += 1
            else:
                inserted += 1

        if current_ids:
            placeholders = ",".join("?" for _ in current_ids)
            deleted = db.execute(
                f"DELETE FROM canonical_page_autos_context WHERE process_id=? AND canonical_page_id NOT IN ({placeholders})",
                (process_id, *current_ids),
            ).rowcount
        else:
            deleted = db.execute(
                "DELETE FROM canonical_page_autos_context WHERE process_id=?",
                (process_id,),
            ).rowcount
        db.commit()
        return {
            "inserted": inserted,
            "updated": updated,
            "unchanged": unchanged,
            "deleted": deleted,
            "pages": len(payload.get("pages", [])),
            "status": "ready",
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def decode(value: str | None) -> Any:
    if not value:
        return None
    return json.loads(value)
