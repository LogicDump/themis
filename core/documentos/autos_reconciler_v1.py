"""Composição determinística e versionada dos Autos.

Esta unidade reconcilia observações já presentes no Canonical Store. Não lê
PDFs, não infere pertencimento por CNJ textual e não usa IA.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MIGRATION_VERSION = "autos-reconciler-v1"
RECONCILER_VERSION = "autos-reconciler-v1-deterministic"
ID_NAMESPACE = uuid.UUID("f4a0e42a-3c17-5cf7-8e5a-91a7d3aaf501")
STATUSES = {"EXACT", "OVERLAPPING", "CONTINUATION", "INTERCALATED", "DUPLICATE", "VERSION_VARIANT", "UNRESOLVED"}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _id(kind: str, *parts: object) -> str:
    return f"{kind}_{uuid.uuid5(ID_NAMESPACE, '|'.join(map(str, parts))).hex}"


def _fingerprint(text: str | None, content_fingerprint: str | None = None) -> str:
    if content_fingerprint:
        return content_fingerprint
    normalized = " ".join((text or "").split()).strip().casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _source_fingerprint(candidates: list[dict[str, Any]]) -> str:
    values = sorted(
        f"{item['document_id']}:{item['pdf_page']}:{item.get('canonical_page_id', '')}:{_fingerprint(item.get('text'), item.get('content_fingerprint'))}"
        for item in candidates
    )
    return hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()


def reconcile_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Reconcile page candidates without assuming any global page offset.

    Candidates with the same content fingerprint and compatible folio collapse
    into one logical page while retaining all source observations. When there
    is no reliable anchor across multiple documents, positions stay unresolved.
    """
    prepared = []
    for item in candidates:
        if not item.get("document_id") or not item.get("pdf_page"):
            raise ValueError("candidate exige document_id e pdf_page")
        value = dict(item)
        value["pdf_page"] = int(value["pdf_page"])
        value["process_folio"] = int(value["process_folio"]) if value.get("process_folio") is not None else None
        value["fingerprint"] = _fingerprint(value.get("text"), value.get("content_fingerprint"))
        prepared.append(value)

    groups: dict[tuple[str, int | None], list[dict[str, Any]]] = {}
    fingerprints: dict[str, set[int]] = {}
    for item in prepared:
        fingerprints.setdefault(item["fingerprint"], set()).add(item["process_folio"])
    for item in prepared:
        folios = fingerprints[item["fingerprint"]]
        conflicting_folios = len({f for f in folios if f is not None}) > 1
        # Conflicting folios are version variants, not silently merged pages.
        key = (item["fingerprint"], item["process_folio"] if conflicting_folios else None)
        groups.setdefault(key, []).append(item)

    logical = []
    for key, sources in groups.items():
        known_folios = {s["process_folio"] for s in sources if s.get("process_folio") is not None}
        representative = sorted(sources, key=lambda s: (s.get("source_order", 10**9), s["document_id"], s["pdf_page"]))[0]
        logical.append({
            "key": key,
            "canonical_page_id": representative.get("canonical_page_id"),
            "document_id": representative["document_id"],
            "pdf_page": representative["pdf_page"],
            "process_folio": min(known_folios) if len(known_folios) == 1 else None,
            "content_fingerprint": key[0],
            "text": representative.get("text", ""),
            "sources": sources,
            "status": "DUPLICATE" if len(sources) > 1 and len(known_folios) <= 1 else ("VERSION_VARIANT" if len(known_folios) > 1 else "EXACT"),
            "confidence": "HIGH" if len(known_folios) == 1 or len(sources) == 1 else "MEDIUM",
        })

    variant_fingerprints = {
        fingerprint for fingerprint, folios in fingerprints.items()
        if len({folio for folio in folios if folio is not None}) > 1
    }
    for item in logical:
        if item["content_fingerprint"] in variant_fingerprints:
            item["status"] = "VERSION_VARIANT"
            item["confidence"] = "MEDIUM"

    multiple_documents = len({s["document_id"] for s in prepared}) > 1
    all_have_folio = bool(logical) and all(item["process_folio"] is not None for item in logical)
    has_canonical_order = bool(logical) and all(item["sources"][0].get("source_order") is not None for item in logical)
    one_document = not multiple_documents
    if all_have_folio:
        ordered = sorted(logical, key=lambda item: (item["process_folio"], item["document_id"], item["pdf_page"]))
    elif one_document or has_canonical_order:
        ordered = sorted(logical, key=lambda item: (item["sources"][0].get("source_order", 10**9), item["pdf_page"]))
    else:
        ordered = sorted(logical, key=lambda item: (item["process_folio"] is None, item["process_folio"] or 10**9, item["document_id"], item["pdf_page"]))

    resolved = all_have_folio or one_document or has_canonical_order
    for index, item in enumerate(ordered, 1):
        item["autos_position"] = index if resolved else None
        if not resolved:
            item["status"] = "UNRESOLVED"
            item["confidence"] = "LOW"

    return {
        "source_fingerprint": _source_fingerprint(prepared),
        "resolved": resolved,
        "pages": ordered,
        "counts": {
            status: sum(1 for item in ordered if item["status"] == status)
            for status in sorted(STATUSES)
        },
    }


SCHEMA = """
CREATE TABLE IF NOT EXISTS autos_compositions(
  composition_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  version INTEGER NOT NULL,
  reconciler_version TEXT NOT NULL,
  source_fingerprint TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('RESOLVED','PARTIAL','UNRESOLVED')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(process_id, version),
  FOREIGN KEY(process_id) REFERENCES processes(process_id)
);
CREATE TABLE IF NOT EXISTS autos_page_memberships(
  membership_id TEXT PRIMARY KEY,
  composition_id TEXT NOT NULL,
  canonical_page_id TEXT,
  document_id TEXT NOT NULL,
  pdf_page INTEGER NOT NULL,
  process_folio INTEGER,
  autos_position INTEGER,
  status TEXT NOT NULL CHECK(status IN ('EXACT','OVERLAPPING','CONTINUATION','INTERCALATED','DUPLICATE','VERSION_VARIANT','UNRESOLVED')),
  confidence TEXT NOT NULL,
  content_fingerprint TEXT NOT NULL,
  provenance_json TEXT NOT NULL DEFAULT '{}',
  UNIQUE(composition_id, content_fingerprint, process_folio),
  FOREIGN KEY(composition_id) REFERENCES autos_compositions(composition_id),
  FOREIGN KEY(canonical_page_id) REFERENCES canonical_pages(canonical_page_id),
  FOREIGN KEY(document_id, pdf_page) REFERENCES pages(document_id, page_number)
);
CREATE TABLE IF NOT EXISTS autos_page_sources(
  membership_id TEXT NOT NULL,
  canonical_page_id TEXT,
  document_id TEXT NOT NULL,
  pdf_page INTEGER NOT NULL,
  process_folio INTEGER,
  source_ref_json TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY(membership_id, document_id, pdf_page),
  FOREIGN KEY(membership_id) REFERENCES autos_page_memberships(membership_id),
  FOREIGN KEY(canonical_page_id) REFERENCES canonical_pages(canonical_page_id),
  FOREIGN KEY(document_id, pdf_page) REFERENCES pages(document_id, page_number)
);
CREATE INDEX IF NOT EXISTS autos_compositions_process ON autos_compositions(process_id, version DESC);
CREATE INDEX IF NOT EXISTS autos_memberships_order ON autos_page_memberships(composition_id, autos_position);
"""


def migrate(db_path: Path) -> dict[str, Any]:
    db = sqlite3.connect(db_path)
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript("BEGIN IMMEDIATE;\n" + SCHEMA)
        db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
        applied = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION,)).fetchone()
        if not applied:
            db.execute("INSERT INTO schema_migrations(version, applied_at) VALUES(?,?)", (MIGRATION_VERSION, _now()))
        db.commit()
        return {"migration_version": MIGRATION_VERSION, "already_applied": bool(applied)}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _process_candidates(db: sqlite3.Connection, process_id: str, document_ids: list[str] | None = None) -> list[dict[str, Any]]:
    cols = [r[1] for r in db.execute("PRAGMA table_info(pages)").fetchall()]
    page_col = "page_number" if "page_number" in cols else "page"
    content_col = "content" if "content" in cols else "content_markdown"
    params: list[Any] = [process_id]
    extra = ""
    if document_ids:
        extra = " AND o.document_id IN (" + ",".join("?" for _ in document_ids) + ")"
        params.extend(document_ids)
    rows = db.execute(
        f"""SELECT cp.canonical_page_id,o.document_id,o.pdf_page,cp.process_folio_label,
        o.content_id,p.{content_col} as content_markdown,cp.canonical_order,cp.provenance_json
        FROM canonical_pages cp JOIN canonical_page_observations o USING(canonical_page_id)
        JOIN pages p ON p.document_id=o.document_id AND p.{page_col}=o.pdf_page
        WHERE cp.process_id=? AND cp.lifecycle_status='ACTIVE'{extra}
        ORDER BY o.document_id,o.pdf_page""",
        params,
    ).fetchall()
    candidates = []
    for row in rows:
        folio = row["process_folio_label"]
        candidates.append({
            "canonical_page_id": row["canonical_page_id"],
            "document_id": row["document_id"],
            "pdf_page": row["pdf_page"],
            "process_folio": int(folio) if str(folio or "").strip().isdigit() else None,
            "content_fingerprint": row["content_id"],
            "text": row["content_markdown"],
            "source_order": row["canonical_order"] or row["pdf_page"],
            "source_ref": {"canonical_page_id": row["canonical_page_id"], "document_id": row["document_id"], "pdf_page": row["pdf_page"]},
        })
    return candidates


def _ensure_process(db: sqlite3.Connection, process_id: str) -> None:
    has_processes = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='processes'").fetchone()
    if has_processes:
        db.execute("INSERT OR IGNORE INTO processes VALUES(?,?,?)", (process_id, "ACTIVE", _now()))


def reconcile_process_autos(process_id: str, document_ids: list[str] | None = None, db_path: Path | None = None) -> dict[str, Any]:
    target = Path(db_path) if db_path else None
    if target is None:
        raise ValueError("db_path é obrigatório para reconciliação persistente")
    migrate(target)
    db = sqlite3.connect(target)
    db.row_factory = sqlite3.Row
    try:
        candidates = _process_candidates(db, process_id, document_ids)
        result = reconcile_candidates(candidates)
        latest = db.execute("SELECT version,source_fingerprint,status FROM autos_compositions WHERE process_id=? ORDER BY version DESC LIMIT 1", (process_id,)).fetchone()
        target_status = "RESOLVED" if result["resolved"] else "UNRESOLVED"
        if latest and latest["source_fingerprint"] == result["source_fingerprint"] and latest["status"] == target_status:
            return composition_for_process(db, process_id)
        version = (latest["version"] if latest else 0) + 1
        composition_id = _id("ac", process_id, version, result["source_fingerprint"])
        now = _now()
        db.execute("BEGIN")
        _ensure_process(db, process_id)
        db.execute("INSERT INTO autos_compositions VALUES(?,?,?,?,?,?,?,?)", (composition_id, process_id, version, RECONCILER_VERSION, result["source_fingerprint"], "RESOLVED" if result["resolved"] else "UNRESOLVED", now, now))
        for page in result["pages"]:
            membership_id = _id("am", composition_id, page["content_fingerprint"], page["process_folio"])
            db.execute("INSERT INTO autos_page_memberships VALUES(?,?,?,?,?,?,?,?,?,?,?)", (membership_id, composition_id, page.get("canonical_page_id"), page["document_id"], page["pdf_page"], page["process_folio"], page["autos_position"], page["status"], page["confidence"], page["content_fingerprint"], json.dumps({"source_count": len(page["sources"])}, ensure_ascii=False)))
            for source in page["sources"]:
                db.execute("INSERT INTO autos_page_sources VALUES(?,?,?,?,?,?)", (membership_id, source.get("canonical_page_id"), source["document_id"], source["pdf_page"], source.get("process_folio"), json.dumps(source.get("source_ref") or {}, ensure_ascii=False)))
        db.commit()
        return composition_for_process(db, process_id)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def composition_for_process(db: sqlite3.Connection, process_id: str) -> dict[str, Any] | None:
    composition = db.execute("SELECT * FROM autos_compositions WHERE process_id=? ORDER BY version DESC LIMIT 1", (process_id,)).fetchone()
    if not composition:
        return None
    rows = db.execute("""SELECT m.* FROM autos_page_memberships m
        WHERE m.composition_id=? ORDER BY CASE WHEN m.autos_position IS NULL THEN 1 ELSE 0 END,m.autos_position,m.document_id,m.pdf_page""", (composition["composition_id"],)).fetchall()
    pages = []
    for row in rows:
        item = dict(row)
        item["sources"] = [dict(source) for source in db.execute("SELECT * FROM autos_page_sources WHERE membership_id=? ORDER BY document_id,pdf_page", (row["membership_id"],)).fetchall()]
        pages.append(item)
    return {"composition": dict(composition), "pages": pages}
