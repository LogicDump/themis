"""Canonical structured knowledge objects and deterministic candidate services."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MIGRATION_VERSION = "knowledge-objects-v1"
ID_NAMESPACE = uuid.UUID("3d87b7a5-8bd9-5d62-93cb-5a0dbcc1b17f")
OWNER_TYPES = {"matter": "matter_id", "process": "process_id"}
DATE_PRECISIONS = {"EXACT", "DAY", "MONTH", "YEAR", "APPROXIMATE", "UNKNOWN"}
STATUSES = {"CANDIDATE", "CONFIRMED", "CONFLICTING"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS extraction_runs(
  extraction_run_id TEXT PRIMARY KEY,
  owner_type TEXT NOT NULL CHECK(owner_type IN ('MATTER','PROCESS')),
  owner_id TEXT NOT NULL,
  target TEXT NOT NULL CHECK(target IN ('PARTIES','CHRONOLOGY','STRATEGY','DEADLINES','PENDING','HEARINGS')),
  source_derived_content_id TEXT,
  source_content_version INTEGER,
  pipeline_version TEXT NOT NULL,
  model_provider TEXT,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  status TEXT NOT NULL,
  error TEXT
);

CREATE TABLE IF NOT EXISTS legal_entities(
  entity_id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL CHECK(entity_type IN ('PERSON','ORGANIZATION','UNKNOWN')),
  display_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  identifiers_json TEXT NOT NULL DEFAULT '{}',
  identity_fingerprint TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS party_relations(
  party_relation_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  owner_type TEXT NOT NULL CHECK(owner_type IN ('MATTER','PROCESS')),
  owner_id TEXT NOT NULL,
  role TEXT,
  role_raw TEXT,
  status TEXT NOT NULL CHECK(status IN ('CANDIDATE','CONFIRMED','CONFLICTING')),
  confidence TEXT NOT NULL,
  relation_fingerprint TEXT NOT NULL UNIQUE,
  extraction_run_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(entity_id) REFERENCES legal_entities(entity_id),
  FOREIGN KEY(extraction_run_id) REFERENCES extraction_runs(extraction_run_id)
);

CREATE TABLE IF NOT EXISTS party_evidence(
  party_evidence_id TEXT PRIMARY KEY,
  party_relation_id TEXT NOT NULL,
  document_id TEXT NOT NULL,
  canonical_page_id TEXT NOT NULL,
  pdf_page INTEGER NOT NULL,
  process_folio TEXT,
  source_ref_json TEXT NOT NULL,
  excerpt TEXT,
  extraction_method TEXT NOT NULL,
  confidence TEXT NOT NULL,
  evidence_fingerprint TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(party_relation_id, evidence_fingerprint),
  FOREIGN KEY(party_relation_id) REFERENCES party_relations(party_relation_id),
  FOREIGN KEY(document_id, pdf_page) REFERENCES pages(document_id, page_number),
  FOREIGN KEY(canonical_page_id) REFERENCES canonical_pages(canonical_page_id)
);

CREATE TABLE IF NOT EXISTS chronology_events(
  chronology_event_id TEXT PRIMARY KEY,
  owner_type TEXT NOT NULL CHECK(owner_type IN ('MATTER','PROCESS')),
  owner_id TEXT NOT NULL,
  occurred_at TEXT,
  date_precision TEXT NOT NULL CHECK(date_precision IN ('EXACT','DAY','MONTH','YEAR','APPROXIMATE','UNKNOWN')),
  event_type TEXT,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL CHECK(status IN ('CANDIDATE','CONFIRMED','CONFLICTING')),
  confidence TEXT NOT NULL,
  source_fingerprint TEXT,
  extraction_run_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(extraction_run_id) REFERENCES extraction_runs(extraction_run_id)
);

CREATE TABLE IF NOT EXISTS chronology_evidence(
  chronology_evidence_id TEXT PRIMARY KEY,
  chronology_event_id TEXT NOT NULL,
  document_id TEXT NOT NULL,
  canonical_page_id TEXT NOT NULL,
  pdf_page INTEGER NOT NULL,
  process_folio TEXT,
  source_ref_json TEXT NOT NULL,
  excerpt TEXT,
  extraction_method TEXT NOT NULL,
  confidence TEXT NOT NULL,
  evidence_fingerprint TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(chronology_event_id, evidence_fingerprint),
  FOREIGN KEY(chronology_event_id) REFERENCES chronology_events(chronology_event_id),
  FOREIGN KEY(document_id, pdf_page) REFERENCES pages(document_id, page_number),
  FOREIGN KEY(canonical_page_id) REFERENCES canonical_pages(canonical_page_id)
);

CREATE INDEX IF NOT EXISTS party_relations_owner ON party_relations(owner_type, owner_id);
CREATE INDEX IF NOT EXISTS chronology_events_owner_date ON chronology_events(owner_type, owner_id, occurred_at);
CREATE UNIQUE INDEX IF NOT EXISTS chronology_event_source_identity
  ON chronology_events(owner_type, owner_id, source_fingerprint)
  WHERE source_fingerprint IS NOT NULL;
"""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(*values: Any) -> str:
    raw = "|".join(str(value or "") for value in values)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return " ".join(value.casefold().split())


def _owner_code(owner_type: str) -> str:
    code = owner_type.upper()
    if code not in {"MATTER", "PROCESS"}:
        raise ValueError("owner_type inválido")
    return code


def _validate_owner(db: sqlite3.Connection, owner_type: str, owner_id: str) -> None:
    owner_type = owner_type.lower()
    if owner_type not in OWNER_TYPES:
        raise ValueError("owner_type inválido")
    table = "matters" if owner_type == "matter" else "processes"
    column = OWNER_TYPES[owner_type]
    if db.execute(f"SELECT 1 FROM {table} WHERE {column}=?", (owner_id,)).fetchone() is None:
        raise ValueError("owner inexistente")


def _source_context(db: sqlite3.Connection, owner_type: str, owner_id: str, source_ref: dict[str, Any]) -> dict[str, Any]:
    document_id = source_ref.get("document_id")
    try:
        pdf_page = int(source_ref.get("pdf_page"))
    except (TypeError, ValueError):
        raise ValueError("source_ref.pdf_page inválido")
    if not document_id or pdf_page < 1:
        raise ValueError("source_ref exige document_id e pdf_page")
    row = db.execute(
        """SELECT d.document_id,d.process_id,o.canonical_page_id
        FROM documents d JOIN canonical_page_observations o
          ON o.document_id=d.document_id AND o.pdf_page=?
        JOIN canonical_pages cp ON cp.canonical_page_id=o.canonical_page_id
        WHERE d.document_id=? AND cp.lifecycle_status='ACTIVE'""",
        (pdf_page, document_id),
    ).fetchone()
    if not row:
        raise ValueError("source_ref não corresponde a uma página canônica")
    if owner_type.lower() == "process" and row["process_id"] != owner_id:
        raise ValueError("source_ref pertence a outro processo")
    if owner_type.lower() == "matter":
        related = db.execute(
            "SELECT 1 FROM matter_processes WHERE matter_id=? AND process_id=?",
            (owner_id, row["process_id"]),
        ).fetchone()
        if not related:
            raise ValueError("source_ref pertence a outra matéria")
    if source_ref.get("canonical_page_id") and source_ref["canonical_page_id"] != row["canonical_page_id"]:
        raise ValueError("canonical_page_id divergente do source_ref")
    return {
        "document_id": document_id,
        "pdf_page": pdf_page,
        "canonical_page_id": row["canonical_page_id"],
        "process_folio": source_ref.get("process_folio"),
    }


def migrate(db_path: Path) -> dict[str, Any]:
    db = sqlite3.connect(str(db_path))
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
        applied = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION,)).fetchone()
        if not applied:
            db.executescript(SCHEMA)
            db.execute("INSERT INTO schema_migrations(version, applied_at) VALUES(?,?)", (MIGRATION_VERSION, _now()))
            db.commit()

        # Garante suporte aos alvos de domínio canônicos em extraction_runs
        curr_sql = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='extraction_runs'").fetchone()
        if curr_sql and "STRATEGY" not in curr_sql[0]:
            db.execute("PRAGMA foreign_keys=OFF")
            db.execute("""CREATE TABLE IF NOT EXISTS extraction_runs_migrated(
              extraction_run_id TEXT PRIMARY KEY,
              owner_type TEXT NOT NULL CHECK(owner_type IN ('MATTER','PROCESS')),
              owner_id TEXT NOT NULL,
              target TEXT NOT NULL CHECK(target IN ('PARTIES','CHRONOLOGY','STRATEGY','DEADLINES','PENDING','HEARINGS')),
              source_derived_content_id TEXT,
              source_content_version INTEGER,
              pipeline_version TEXT NOT NULL,
              model_provider TEXT,
              started_at TEXT NOT NULL,
              completed_at TEXT,
              status TEXT NOT NULL,
              error TEXT
            )""")
            db.execute("INSERT INTO extraction_runs_migrated SELECT * FROM extraction_runs")
            db.execute("DROP TABLE extraction_runs")
            db.execute("ALTER TABLE extraction_runs_migrated RENAME TO extraction_runs")
            db.execute("PRAGMA foreign_keys=ON")
            db.commit()

        return {"migration_version": MIGRATION_VERSION, "already_applied": bool(applied)}
    finally:
        db.close()


def create_extraction_run(db: sqlite3.Connection, owner_type: str, owner_id: str, target: str, *,
                          source_derived_content_id: str | None = None, source_content_version: int | None = None,
                          pipeline_version: str = "knowledge-objects-v1", model_provider: str | None = None) -> str:
    _validate_owner(db, owner_type.lower(), owner_id)
    target = target.upper()
    if target not in {"PARTIES", "CHRONOLOGY"}:
        raise ValueError("target inválido")
    run_id = str(uuid.uuid4())
    db.execute(
        """INSERT INTO extraction_runs(extraction_run_id,owner_type,owner_id,target,source_derived_content_id,
        source_content_version,pipeline_version,model_provider,started_at,status) VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (run_id, _owner_code(owner_type), owner_id, target, source_derived_content_id, source_content_version,
         pipeline_version, model_provider, _now(), "STARTED"),
    )
    return run_id


def _entity(db: sqlite3.Connection, candidate: dict[str, Any], now: str) -> str:
    display_name = " ".join(str(candidate.get("display_name", "")).split())
    if not display_name:
        raise ValueError("display_name obrigatório")
    entity_type = str(candidate.get("entity_type", "UNKNOWN")).upper()
    if entity_type not in {"PERSON", "ORGANIZATION", "UNKNOWN"}:
        raise ValueError("entity_type inválido")
    normalized = normalize_name(display_name)
    identifiers = candidate.get("identifiers") or {}
    identity = _fingerprint(entity_type, _json(identifiers) if identifiers else normalized)
    row = db.execute("SELECT entity_id FROM legal_entities WHERE identity_fingerprint=?", (identity,)).fetchone()
    if row:
        db.execute("UPDATE legal_entities SET updated_at=? WHERE entity_id=?", (now, row["entity_id"]))
        return row["entity_id"]
    entity_id = "entity_" + uuid.uuid5(ID_NAMESPACE, identity).hex
    db.execute(
        """INSERT INTO legal_entities(entity_id,entity_type,display_name,normalized_name,identifiers_json,
        identity_fingerprint,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)""",
        (entity_id, entity_type, display_name, normalized, _json(identifiers), identity, now, now),
    )
    return entity_id


def submit_party_candidates(db: sqlite3.Connection, owner_type: str, owner_id: str,
                            candidates: list[dict[str, Any]], *, extraction_run_id: str | None = None,
                            commit: bool = True) -> list[str]:
    _validate_owner(db, owner_type, owner_id)
    now = _now()
    result: list[str] = []
    try:
        for candidate in candidates:
            entity_id = _entity(db, candidate, now)
            role_raw = candidate.get("role_raw") or candidate.get("role")
            role = str(candidate.get("role") or role_raw or "").strip() or None
            relation_fp = _fingerprint(owner_type.lower(), owner_id, entity_id, role, role_raw)
            relation_id = "party_" + uuid.uuid5(ID_NAMESPACE, relation_fp).hex
            db.execute(
                """INSERT INTO party_relations(party_relation_id,entity_id,owner_type,owner_id,role,role_raw,
                status,confidence,relation_fingerprint,extraction_run_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(relation_fingerprint) DO UPDATE SET status=excluded.status,confidence=excluded.confidence,
                extraction_run_id=COALESCE(excluded.extraction_run_id,party_relations.extraction_run_id),updated_at=excluded.updated_at""",
                (relation_id, entity_id, _owner_code(owner_type), owner_id, role, role_raw,
                 candidate.get("status", "CANDIDATE"), str(candidate.get("confidence", "NONE")), relation_fp,
                 extraction_run_id, now, now),
            )
            result.append(relation_id)
            evidence = candidate.get("evidence") or []
            if not evidence and candidate.get("extraction_method", "candidate") != "manual":
                raise ValueError("candidato extraído exige evidence")
            for item in evidence:
                source = _source_context(db, owner_type, owner_id, item.get("source_ref") or item)
                ev_fp = _fingerprint(source["document_id"], source["pdf_page"], item.get("excerpt"), item.get("extraction_method"))
                db.execute(
                    """INSERT OR IGNORE INTO party_evidence(party_evidence_id,party_relation_id,document_id,canonical_page_id,
                    pdf_page,process_folio,source_ref_json,excerpt,extraction_method,confidence,evidence_fingerprint,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    ("pe_" + uuid.uuid5(ID_NAMESPACE, relation_id + ev_fp).hex, relation_id, source["document_id"],
                     source["canonical_page_id"], source["pdf_page"], source["process_folio"], _json(item.get("source_ref") or item),
                     item.get("excerpt"), item.get("extraction_method", "candidate"), item.get("confidence", candidate.get("confidence", "NONE")), ev_fp, now),
                )
        if commit: db.commit()
        return result
    except Exception:
        db.rollback()
        raise


def submit_chronology_candidates(db: sqlite3.Connection, owner_type: str, owner_id: str,
                                 candidates: list[dict[str, Any]], *, extraction_run_id: str | None = None,
                                 commit: bool = True) -> list[str]:
    _validate_owner(db, owner_type, owner_id)
    now = _now()
    result: list[str] = []
    try:
        for candidate in candidates:
            precision = str(candidate.get("date_precision", "UNKNOWN")).upper()
            if precision not in DATE_PRECISIONS:
                raise ValueError("date_precision inválida")
            occurred_at = candidate.get("occurred_at")
            if precision == "UNKNOWN":
                occurred_at = None
            if precision != "UNKNOWN" and occurred_at is not None and not re.match(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$", str(occurred_at)):
                raise ValueError("occurred_at deve preservar precisão documental")
            title = " ".join(str(candidate.get("title", "")).split())
            if not title:
                raise ValueError("title obrigatório")
            evidence = candidate.get("evidence") or []
            if not evidence and candidate.get("extraction_method", "candidate") != "manual":
                raise ValueError("evento extraído exige evidence")
            source_identity = candidate.get("source_fingerprint") or _fingerprint(owner_type.lower(), owner_id, occurred_at, precision,
                                                                                     candidate.get("event_type"), title, candidate.get("description"))
            event_id = "event_" + uuid.uuid5(ID_NAMESPACE, _fingerprint(owner_type.lower(), owner_id, source_identity)).hex
            existing = db.execute(
                "SELECT chronology_event_id FROM chronology_events WHERE owner_type=? AND owner_id=? AND source_fingerprint=?",
                (_owner_code(owner_type), owner_id, source_identity),
            ).fetchone()
            if existing:
                event_id = existing["chronology_event_id"]
                db.execute(
                    """UPDATE chronology_events SET status=?,confidence=?,extraction_run_id=COALESCE(?,extraction_run_id),updated_at=?
                    WHERE chronology_event_id=?""",
                    (candidate.get("status", "CANDIDATE"), str(candidate.get("confidence", "NONE")), extraction_run_id, now, event_id),
                )
            else:
                db.execute(
                    """INSERT INTO chronology_events(chronology_event_id,owner_type,owner_id,occurred_at,date_precision,event_type,
                    title,description,status,confidence,source_fingerprint,extraction_run_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (event_id, _owner_code(owner_type), owner_id, occurred_at, precision, candidate.get("event_type"), title,
                     candidate.get("description"), candidate.get("status", "CANDIDATE"), str(candidate.get("confidence", "NONE")),
                     source_identity, extraction_run_id, now, now),
                )
            result.append(event_id)
            for item in evidence:
                source = _source_context(db, owner_type, owner_id, item.get("source_ref") or item)
                ev_fp = _fingerprint(source["document_id"], source["pdf_page"], item.get("excerpt"), item.get("extraction_method"))
                db.execute(
                    """INSERT OR IGNORE INTO chronology_evidence(chronology_evidence_id,chronology_event_id,document_id,
                    canonical_page_id,pdf_page,process_folio,source_ref_json,excerpt,extraction_method,confidence,evidence_fingerprint,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    ("ce_" + uuid.uuid5(ID_NAMESPACE, event_id + ev_fp).hex, event_id, source["document_id"], source["canonical_page_id"],
                     source["pdf_page"], source["process_folio"], _json(item.get("source_ref") or item), item.get("excerpt"),
                     item.get("extraction_method", "candidate"), item.get("confidence", candidate.get("confidence", "NONE")), ev_fp, now),
                )
        if commit: db.commit()
        return result
    except Exception:
        db.rollback()
        raise


def _evidence_rows(db: sqlite3.Connection, table: str, key: str, value: str) -> list[dict]:
    rows = db.execute(f"SELECT * FROM {table} WHERE {key}=? ORDER BY created_at", (value,)).fetchall()
    return [dict(row) for row in rows]


def party_view_items(db: sqlite3.Connection, owner_type: str, owner_id: str) -> list[dict]:
    rows = db.execute(
        """SELECT pr.*,le.entity_type,le.display_name,le.normalized_name,le.identifiers_json
        FROM party_relations pr JOIN legal_entities le USING(entity_id)
        WHERE pr.owner_type=? AND pr.owner_id=? ORDER BY COALESCE(pr.role,''),le.display_name""",
        (_owner_code(owner_type), owner_id),
    ).fetchall()
    return [{**dict(row), "identifiers": json.loads(row["identifiers_json"]),
             "evidence": _evidence_rows(db, "party_evidence", "party_relation_id", row["party_relation_id"])} for row in rows]


def chronology_view_items(db: sqlite3.Connection, owner_type: str, owner_id: str) -> list[dict]:
    rows = db.execute(
        """SELECT * FROM chronology_events WHERE owner_type=? AND owner_id=?
        ORDER BY CASE WHEN occurred_at IS NULL THEN 1 ELSE 0 END, occurred_at, created_at, chronology_event_id""",
        (_owner_code(owner_type), owner_id),
    ).fetchall()
    return [{**dict(row), "evidence": _evidence_rows(db, "chronology_evidence", "chronology_event_id", row["chronology_event_id"])} for row in rows]
