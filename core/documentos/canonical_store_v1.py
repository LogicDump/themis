"""Migração aditiva Canonical Store V1 para o índice SQLite do Jurídico.

Esta unidade não lê PDFs, não toca manifestos e não depende do runtime publicado.
Ela existe para migrar uma cópia controlada do banco de dados.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MIGRATION_VERSION = "canonical-store-v1"
ID_NAMESPACE = uuid.UUID("2bb5c31c-7a37-5b9e-899f-2230e1141111")
MIN_CONTENT_CHARS = 25


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _id(kind: str, *parts: object) -> str:
    value = "|".join(str(part) for part in parts)
    return f"{kind}_{uuid.uuid5(ID_NAMESPACE, value).hex}"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _one_folio(db: sqlite3.Connection, document_id: str, pdf_page: int) -> tuple[int | None, str | None]:
    """Use only an unambiguous numeric folio already present in legacy evidence."""
    values = [
        row[0].strip()
        for row in db.execute(
            """SELECT DISTINCT coalesce(e.folio, e.value) FROM evidence e
               JOIN pages p ON p.page_id=e.page_id
               WHERE p.document_id=? AND p.page_number=? AND (e.field='folha' OR e.folio IS NOT NULL)""",
            (document_id, pdf_page),
        )
        if row[0] is not None and str(row[0]).strip().isdigit() and int(str(row[0]).strip()) > 0
    ]
    values = sorted(set(values), key=int)
    return (int(values[0]), str(values[0])) if len(values) == 1 else (None, None)


SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations(
  version TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS canonical_pages(
  canonical_page_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  process_page_number INTEGER,
  process_folio_label TEXT,
  canonical_order INTEGER,
  numbering_status TEXT NOT NULL CHECK(numbering_status IN ('KNOWN','UNNUMBERED','CONFLICTED','UNRESOLVED')),
  numbering_confidence TEXT NOT NULL CHECK(numbering_confidence IN ('CONFIRMED','HIGH','MEDIUM','LOW','NONE')),
  lifecycle_status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(lifecycle_status IN ('ACTIVE','MERGED','CONFLICTED')),
  superseded_by_canonical_page_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  provenance_json TEXT NOT NULL DEFAULT '{}',
  FOREIGN KEY(process_id) REFERENCES processes(process_id),
  FOREIGN KEY(superseded_by_canonical_page_id) REFERENCES canonical_pages(canonical_page_id)
);

CREATE TABLE IF NOT EXISTS canonical_page_observations(
  canonical_page_observation_id TEXT PRIMARY KEY,
  canonical_page_id TEXT NOT NULL,
  document_id TEXT NOT NULL,
  pdf_page INTEGER NOT NULL,
  content_id TEXT NOT NULL,
  observation_role TEXT NOT NULL CHECK(observation_role IN ('PRIMARY','DUPLICATE','ALTERNATIVE','CONFLICTING')),
  equivalence_status TEXT NOT NULL CHECK(equivalence_status IN ('CONFIRMED','PROBABLE','UNRESOLVED')),
  equivalence_confidence TEXT NOT NULL CHECK(equivalence_confidence IN ('CONFIRMED','HIGH','MEDIUM','LOW','NONE')),
  match_method TEXT NOT NULL,
  provenance_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  UNIQUE(document_id, pdf_page),
  FOREIGN KEY(canonical_page_id) REFERENCES canonical_pages(canonical_page_id),
  FOREIGN KEY(document_id, pdf_page) REFERENCES pages(document_id, page_number)
);

CREATE TABLE IF NOT EXISTS canonical_page_equivalences(
  canonical_page_equivalence_id TEXT PRIMARY KEY,
  left_observation_id TEXT NOT NULL,
  right_observation_id TEXT NOT NULL,
  relation_status TEXT NOT NULL CHECK(relation_status IN ('SAME','PROBABLE_SAME','CONFLICTS','UNRESOLVED')),
  confidence TEXT NOT NULL CHECK(confidence IN ('CONFIRMED','HIGH','MEDIUM','LOW','NONE')),
  match_method TEXT NOT NULL,
  evidence_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  CHECK(left_observation_id < right_observation_id),
  UNIQUE(left_observation_id, right_observation_id),
  FOREIGN KEY(left_observation_id) REFERENCES canonical_page_observations(canonical_page_observation_id),
  FOREIGN KEY(right_observation_id) REFERENCES canonical_page_observations(canonical_page_observation_id)
);

CREATE TABLE IF NOT EXISTS logical_documents(
  logical_document_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  document_type TEXT NOT NULL,
  title TEXT,
  status TEXT NOT NULL,
  confidence TEXT NOT NULL,
  start_canonical_page_id TEXT,
  end_canonical_page_id TEXT,
  provenance_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(process_id) REFERENCES processes(process_id),
  FOREIGN KEY(start_canonical_page_id) REFERENCES canonical_pages(canonical_page_id),
  FOREIGN KEY(end_canonical_page_id) REFERENCES canonical_pages(canonical_page_id)
);

CREATE TABLE IF NOT EXISTS logical_document_pages(
  logical_document_id TEXT NOT NULL,
  canonical_page_id TEXT NOT NULL,
  position INTEGER NOT NULL CHECK(position > 0),
  PRIMARY KEY(logical_document_id, canonical_page_id),
  UNIQUE(logical_document_id, position),
  FOREIGN KEY(logical_document_id) REFERENCES logical_documents(logical_document_id),
  FOREIGN KEY(canonical_page_id) REFERENCES canonical_pages(canonical_page_id)
);

CREATE TABLE IF NOT EXISTS derived_content(
  derived_content_id TEXT PRIMARY KEY,
  owner_type TEXT NOT NULL CHECK(owner_type IN ('PROCESS','MATTER','CANONICAL_PAGE','LOGICAL_DOCUMENT')),
  owner_id TEXT NOT NULL,
  process_id TEXT,
  matter_id TEXT,
  canonical_page_id TEXT,
  logical_document_id TEXT,
  content_format TEXT NOT NULL,
  content TEXT NOT NULL,
  content_version INTEGER NOT NULL CHECK(content_version > 0),
  generated_at TEXT NOT NULL,
  generator TEXT NOT NULL,
  provenance_json TEXT NOT NULL DEFAULT '{}',
  content_hash TEXT NOT NULL,
  FOREIGN KEY(process_id) REFERENCES processes(process_id),
  FOREIGN KEY(matter_id) REFERENCES matters(matter_id),
  FOREIGN KEY(canonical_page_id) REFERENCES canonical_pages(canonical_page_id),
  FOREIGN KEY(logical_document_id) REFERENCES logical_documents(logical_document_id),
  UNIQUE(owner_type, owner_id, content_version)
);

CREATE TABLE IF NOT EXISTS source_refs(
  source_ref_id TEXT PRIMARY KEY,
  derived_content_id TEXT NOT NULL,
  start_canonical_page_id TEXT,
  end_canonical_page_id TEXT,
  source_start_offset INTEGER,
  source_end_offset INTEGER,
  block_locator TEXT,
  quote_hash TEXT,
  provenance_json TEXT NOT NULL DEFAULT '{}',
  FOREIGN KEY(derived_content_id) REFERENCES derived_content(derived_content_id),
  FOREIGN KEY(start_canonical_page_id) REFERENCES canonical_pages(canonical_page_id),
  FOREIGN KEY(end_canonical_page_id) REFERENCES canonical_pages(canonical_page_id)
);

CREATE TABLE IF NOT EXISTS internal_references(
  internal_reference_id TEXT PRIMARY KEY,
  source_logical_document_id TEXT NOT NULL,
  source_ref_id TEXT,
  literal TEXT NOT NULL,
  target_process_id TEXT,
  target_folio_start TEXT,
  target_folio_end TEXT,
  target_relation TEXT NOT NULL CHECK(target_relation IN ('RANGE','SINGLE','FOLLOWING')),
  target_start_canonical_page_id TEXT,
  target_end_canonical_page_id TEXT,
  status TEXT NOT NULL CHECK(status IN ('CONFIRMED','PROBABLE','UNRESOLVED')),
  confidence TEXT NOT NULL CHECK(confidence IN ('CONFIRMED','HIGH','MEDIUM','LOW','NONE')),
  provenance_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  FOREIGN KEY(source_logical_document_id) REFERENCES logical_documents(logical_document_id),
  FOREIGN KEY(source_ref_id) REFERENCES source_refs(source_ref_id),
  FOREIGN KEY(target_process_id) REFERENCES processes(process_id),
  FOREIGN KEY(target_start_canonical_page_id) REFERENCES canonical_pages(canonical_page_id),
  FOREIGN KEY(target_end_canonical_page_id) REFERENCES canonical_pages(canonical_page_id)
);

CREATE INDEX IF NOT EXISTS canonical_pages_process_number ON canonical_pages(process_id, process_page_number);
CREATE UNIQUE INDEX IF NOT EXISTS canonical_pages_confirmed_number ON canonical_pages(process_id, process_page_number)
  WHERE process_page_number IS NOT NULL AND numbering_status='KNOWN' AND numbering_confidence='CONFIRMED' AND lifecycle_status='ACTIVE';
CREATE INDEX IF NOT EXISTS cpo_canonical_page ON canonical_page_observations(canonical_page_id);
CREATE INDEX IF NOT EXISTS cpo_process_content ON canonical_page_observations(content_id, canonical_page_id);
CREATE INDEX IF NOT EXISTS cpe_left ON canonical_page_equivalences(left_observation_id);
CREATE INDEX IF NOT EXISTS cpe_right ON canonical_page_equivalences(right_observation_id);
CREATE INDEX IF NOT EXISTS logical_documents_process_status ON logical_documents(process_id, status);
CREATE INDEX IF NOT EXISTS logical_document_pages_page ON logical_document_pages(canonical_page_id, logical_document_id);
CREATE INDEX IF NOT EXISTS derived_content_owner_version ON derived_content(owner_type, owner_id, content_version DESC);
CREATE INDEX IF NOT EXISTS source_refs_content_page ON source_refs(derived_content_id, start_canonical_page_id);
CREATE INDEX IF NOT EXISTS internal_references_source ON internal_references(source_logical_document_id, status);
CREATE INDEX IF NOT EXISTS internal_references_target ON internal_references(target_process_id, target_start_canonical_page_id);
"""


def _pages_with_process(db: sqlite3.Connection) -> list[sqlite3.Row]:
    cols = [r[1] for r in db.execute("PRAGMA table_info(pages)").fetchall()]
    page_col = "page_number" if "page_number" in cols else "page"
    content_col = "content" if "content" in cols else "content_markdown"
    return db.execute(
        f"""SELECT p.document_id, p.{page_col} AS pdf_page, p.content_id, p.{content_col} AS content_markdown, d.process_id
             FROM pages p JOIN documents d USING(document_id)
             WHERE d.process_id IS NOT NULL AND d.process_id <> 'unresolved'
             ORDER BY d.process_id, p.document_id, p.{page_col}"""
    ).fetchall()


def _ensure_process(db: sqlite3.Connection, process_id: str) -> None:
    has_processes = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='processes'").fetchone()
    if has_processes:
        db.execute("INSERT OR IGNORE INTO processes VALUES(?,?,?)", (process_id, "ACTIVE", _now()))


def _backfill(db: sqlite3.Connection) -> dict[str, Any]:
    rows = _pages_with_process(db)
    observations: list[dict[str, Any]] = []
    timestamp = _now()
    for row in rows:
        document_id, pdf_page, content_id, content_markdown, process_id = row
        _ensure_process(db, process_id)
        canonical_id = _id("cp", process_id, document_id, pdf_page)
        observation_id = _id("cpo", document_id, pdf_page)
        folio_number, folio_label = _one_folio(db, document_id, pdf_page)
        numbering_status = "KNOWN" if folio_number is not None else "UNRESOLVED"
        numbering_confidence = "LOW" if folio_number is not None else "NONE"
        provenance = json.dumps({"source": "canonical-store-v1-backfill", "document_id": document_id, "pdf_page": pdf_page}, ensure_ascii=False, separators=(",", ":"))
        db.execute(
            """INSERT OR IGNORE INTO canonical_pages VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (canonical_id, process_id, folio_number, folio_label, None, numbering_status, numbering_confidence,
             "ACTIVE", None, timestamp, timestamp, provenance),
        )
        db.execute(
            """INSERT OR IGNORE INTO canonical_page_observations VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (observation_id, canonical_id, document_id, pdf_page, content_id, "PRIMARY", "UNRESOLVED", "NONE",
             "backfill_one_observation_per_canonical_page", provenance, timestamp),
        )
        observations.append({"id": observation_id, "canonical_id": canonical_id, "process_id": process_id,
                             "content_id": content_id, "text": content_markdown, "folio": folio_number})

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for observation in observations:
        if len((observation["text"] or "").strip()) >= MIN_CONTENT_CHARS:
            groups[(observation["process_id"], observation["content_id"])].append(observation)

    candidates = conflicts = 0
    for (process_id, content_id), group in groups.items():
        if len(group) < 2:
            continue
        for index, left in enumerate(group):
            for right in group[index + 1:]:
                ordered = sorted((left["id"], right["id"]))
                folios = {value for value in (left["folio"], right["folio"]) if value is not None}
                conflict = len(folios) == 2
                status = "CONFLICTS" if conflict else "PROBABLE_SAME"
                confidence = "MEDIUM" if conflict else "HIGH"
                evidence = json.dumps({"process_id": process_id, "content_id": content_id,
                                       "left_folio": left["folio"], "right_folio": right["folio"]},
                                      ensure_ascii=False, separators=(",", ":"))
                db.execute(
                    """INSERT OR IGNORE INTO canonical_page_equivalences VALUES(?,?,?,?,?,?,?,?)""",
                    (_id("cpe", *ordered), ordered[0], ordered[1], status, confidence,
                     "same_process_same_content_id", evidence, timestamp),
                )
                candidates += 1
                conflicts += int(conflict)
    return {"pages_with_process": len(rows), "candidates": candidates, "conflicts": conflicts}


def migration_metrics(db: sqlite3.Connection) -> dict[str, Any]:
    total = db.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
    with_process = db.execute("""SELECT COUNT(*) FROM pages p JOIN documents d USING(document_id)
        WHERE d.process_id IS NOT NULL AND d.process_id <> 'unresolved'""").fetchone()[0]
    folio = db.execute("SELECT COUNT(*) FROM canonical_pages WHERE process_page_number IS NOT NULL").fetchone()[0]
    distribution = [dict(row) for row in db.execute("""SELECT process_id, COUNT(*) AS canonical_pages
        FROM canonical_pages GROUP BY process_id ORDER BY process_id""").fetchall()]
    statuses = dict(db.execute("SELECT relation_status, COUNT(*) FROM canonical_page_equivalences GROUP BY relation_status").fetchall())
    return {
        "pages_total": total,
        "pages_with_process": with_process,
        "pages_without_process": total - with_process,
        "canonical_pages": db.execute("SELECT COUNT(*) FROM canonical_pages").fetchone()[0],
        "observations": db.execute("SELECT COUNT(*) FROM canonical_page_observations").fetchone()[0],
        "content_id_candidates": statuses.get("PROBABLE_SAME", 0) + statuses.get("SAME", 0),
        "conflicts": statuses.get("CONFLICTS", 0),
        "pages_with_folio": folio,
        "pages_without_folio": with_process - folio,
        "distribution_by_process": distribution,
    }


def migrate(db_path: Path) -> dict[str, Any]:
    """Apply V1 once. The caller must supply a disposable/test database path."""
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript("BEGIN IMMEDIATE;\n" + SCHEMA)
        already_applied = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION,)).fetchone()
        backfill = {"pages_with_process": 0, "candidates": 0, "conflicts": 0}
        if not already_applied:
            backfill = _backfill(db)
            db.execute("INSERT INTO schema_migrations(version, applied_at) VALUES(?,?)", (MIGRATION_VERSION, _now()))
        db.commit()
        return {"migration_version": MIGRATION_VERSION, "already_applied": bool(already_applied),
                "backfill": backfill, **migration_metrics(db)}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Aplica Canonical Store V1 em banco SQLite de teste.")
    parser.add_argument("database", type=Path)
    args = parser.parse_args()
    print(json.dumps(migrate(args.database), ensure_ascii=False, indent=2))
