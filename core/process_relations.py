"""Global process-relation registry.

Relations belong to catalog.db because either endpoint may be a lightweight
reference with no materialized Process Package.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.process_storage import catalog_discovery, connect_catalog, register_discovery
from core.runtime_paths import validate_process_id

MIGRATION_VERSION = "catalog-process-relations-v1"
_CNJ = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")

SCHEMA = """
CREATE TABLE IF NOT EXISTS process_relations(
  relation_id TEXT PRIMARY KEY,
  from_process_id TEXT NOT NULL,
  to_process_id TEXT NOT NULL,
  relation_kind TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'CONFIRMED',
  confidence TEXT NOT NULL DEFAULT 'HIGH',
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  UNIQUE(from_process_id,to_process_id,relation_kind)
);
CREATE INDEX IF NOT EXISTS idx_process_relations_from
  ON process_relations(from_process_id, relation_kind);
CREATE INDEX IF NOT EXISTS idx_process_relations_to
  ON process_relations(to_process_id, relation_kind);

CREATE TABLE IF NOT EXISTS process_relation_evidence(
  evidence_id TEXT PRIMARY KEY,
  relation_id TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_process_id TEXT,
  source_ref_json TEXT NOT NULL DEFAULT '{}',
  excerpt TEXT,
  observed_at TEXT NOT NULL,
  FOREIGN KEY(relation_id) REFERENCES process_relations(relation_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_process_relation_evidence_relation
  ON process_relation_evidence(relation_id, observed_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def extract_cnj(value: Any) -> str | None:
    match = _CNJ.search(str(value or ""))
    if not match:
        return None
    try:
        return validate_process_id(match.group(0))
    except ValueError:
        return None


def migrate_connection(db: sqlite3.Connection) -> dict[str, Any]:
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    before = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION,)).fetchone()
    db.executescript(SCHEMA)
    db.execute(
        "INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES(?,?)",
        (MIGRATION_VERSION, _now()),
    )
    db.commit()
    return {"migration_version": MIGRATION_VERSION, "already_applied": bool(before)}


def _relation_id(from_process_id: str, to_process_id: str, relation_kind: str) -> str:
    raw = f"{from_process_id}|{to_process_id}|{relation_kind}".encode("utf-8")
    return "prel_" + hashlib.sha256(raw).hexdigest()[:32]


def _evidence_id(relation_id: str, source_type: str, source_process_id: str | None, source_ref: dict[str, Any]) -> str:
    raw = json.dumps(
        [relation_id, source_type, source_process_id, source_ref],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "prev_" + hashlib.sha256(raw).hexdigest()[:32]


def upsert_relation(
    from_process_id: str,
    to_process_id: str,
    relation_kind: str,
    *,
    root: Path | None = None,
    status: str = "CONFIRMED",
    confidence: str = "HIGH",
    source_type: str,
    source_process_id: str | None = None,
    source_ref: dict[str, Any] | None = None,
    excerpt: str | None = None,
    observed_at: str | None = None,
) -> dict[str, Any]:
    source_ref = source_ref or {}
    stamp = observed_at or _now()
    src = validate_process_id(from_process_id)
    dst = validate_process_id(to_process_id)
    kind = str(relation_kind or "").strip().upper()
    if src == dst:
        raise ValueError("process relation cannot point to itself")
    if not kind:
        raise ValueError("relation_kind is required")

    # Endpoints may remain lightweight references forever, but discovering a
    # relation must never downgrade an already materialized/KNOWN process.
    if catalog_discovery(src, root=root) is None:
        register_discovery(src, root=root, discovery_status="REFERENCE", observed_at=stamp)
    if catalog_discovery(dst, root=root) is None:
        register_discovery(dst, root=root, discovery_status="REFERENCE", observed_at=stamp)

    db = connect_catalog(root=root, create=True)
    try:
        migrate_connection(db)
        relation_id = _relation_id(src, dst, kind)
        db.execute(
            """INSERT INTO process_relations(
                 relation_id,from_process_id,to_process_id,relation_kind,status,
                 confidence,first_seen_at,last_seen_at)
               VALUES(?,?,?,?,?,?,?,?)
               ON CONFLICT(from_process_id,to_process_id,relation_kind)
               DO UPDATE SET status=excluded.status,confidence=excluded.confidence,
                             last_seen_at=excluded.last_seen_at""",
            (relation_id, src, dst, kind, status, confidence, stamp, stamp),
        )
        evidence_id = _evidence_id(relation_id, source_type, source_process_id, source_ref)
        db.execute(
            """INSERT INTO process_relation_evidence(
                 evidence_id,relation_id,source_type,source_process_id,
                 source_ref_json,excerpt,observed_at)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(evidence_id) DO UPDATE SET excerpt=excluded.excerpt,
                                                     observed_at=excluded.observed_at""",
            (
                evidence_id,
                relation_id,
                source_type,
                source_process_id,
                json.dumps(source_ref, ensure_ascii=False, sort_keys=True),
                excerpt,
                stamp,
            ),
        )
        db.commit()
        return {
            "relation_id": relation_id,
            "from_process_id": src,
            "to_process_id": dst,
            "relation_kind": kind,
            "status": status,
            "confidence": confidence,
            "evidence_id": evidence_id,
        }
    finally:
        db.close()


def list_relations(process_id: str | None = None, *, root: Path | None = None) -> list[dict[str, Any]]:
    db = connect_catalog(root=root, create=True)
    try:
        migrate_connection(db)
        sql = "SELECT * FROM process_relations"
        params: tuple[Any, ...] = ()
        if process_id:
            pid = validate_process_id(process_id)
            sql += " WHERE from_process_id=? OR to_process_id=?"
            params = (pid, pid)
        sql += " ORDER BY first_seen_at, relation_id"
        rows = db.execute(sql, params).fetchall()
        out = []
        for row in rows:
            item = dict(row)
            evidences = db.execute(
                "SELECT * FROM process_relation_evidence WHERE relation_id=? ORDER BY observed_at,evidence_id",
                (row["relation_id"],),
            ).fetchall()
            item["evidence"] = [
                {
                    **dict(ev),
                    "source_ref": json.loads(ev["source_ref_json"] or "{}"),
                }
                for ev in evidences
            ]
            out.append(item)
        return out
    finally:
        db.close()


def _cnj_from_sanitized_dom(cpopg: dict[str, Any], class_name: str) -> str | None:
    fragments = cpopg.get("sanitized_dom_fragments") or {}
    if not isinstance(fragments, dict):
        return None
    for fragment in fragments.values():
        text = str(fragment or "")
        marker = text.find(class_name)
        if marker < 0:
            continue
        candidate = extract_cnj(text[marker:marker + 600])
        if candidate:
            return candidate
    return None


def relations_from_cpopg(
    process_id: str,
    cpopg: dict[str, Any],
    *,
    root: Path | None = None,
    observed_at: str | None = None,
) -> list[dict[str, Any]]:
    """Materialize explicit CPOPG cover relations without fetching other cases."""
    current = validate_process_id(process_id)
    stamp = observed_at or str(cpopg.get("captured_at") or _now())
    created: list[dict[str, Any]] = []

    basic = cpopg.get("basic_data") or {}
    principal = extract_cnj(basic.get("processo_principal"))
    if not principal or principal == current:
        principal = _cnj_from_sanitized_dom(cpopg, "processoPrinc")
    if principal and principal != current:
        created.append(
            upsert_relation(
                current,
                principal,
                "HAS_PRINCIPAL",
                root=root,
                source_type="PROCESS_COVER",
                source_process_id=current,
                source_ref={"provider": "TJSP_CPOPG", "field": "processo_principal"},
                excerpt=principal,
                observed_at=stamp,
            )
        )

    attached_to = extract_cnj(basic.get("apensado_ao"))
    if not attached_to or attached_to == current:
        attached_to = _cnj_from_sanitized_dom(cpopg, "processoPaiApenso")
    if attached_to and attached_to != current:
        created.append(
            upsert_relation(
                current,
                attached_to,
                "ATTACHED_TO",
                root=root,
                source_type="PROCESS_COVER",
                source_process_id=current,
                source_ref={"provider": "TJSP_CPOPG", "field": "apensado_ao"},
                excerpt=attached_to,
                observed_at=stamp,
            )
        )

    for raw in cpopg.get("related_processes") or []:
        related = extract_cnj(raw.get("numero"))
        if not related or related == current:
            continue
        raw_label = str(raw.get("tipo") or "").casefold()
        if "apensad" in raw_label and " ao" in raw_label:
            relation_from, relation_to = current, related
        else:
            relation_from, relation_to = related, current
        created.append(
            upsert_relation(
                relation_from,
                relation_to,
                "ATTACHED_TO",
                root=root,
                source_type="PROCESS_COVER",
                source_process_id=current,
                source_ref={"provider": "TJSP_CPOPG", "section": "related_processes", "raw": raw},
                excerpt=f"{raw.get('tipo') or 'Apenso'}: {raw.get('numero') or ''}".strip(),
                observed_at=stamp,
            )
        )

    for raw in cpopg.get("incidents") or []:
        related = extract_cnj(raw.get("numero"))
        if not related or related == current:
            continue
        label = str(raw.get("tipo") or raw.get("descricao") or "").casefold()
        if "recurso" in label or "agrav" in label or "apela" in label:
            kind = "APPEAL_OF"
        elif "cumpr" in label or "execu" in label:
            kind = "ENFORCEMENT_OF"
        else:
            kind = "INCIDENT_OF"
        created.append(
            upsert_relation(
                related,
                current,
                kind,
                root=root,
                source_type="PROCESS_COVER",
                source_process_id=current,
                source_ref={"provider": "TJSP_CPOPG", "section": "incidents", "raw": raw},
                excerpt=f"{raw.get('tipo') or ''}: {raw.get('numero') or ''} {raw.get('descricao') or ''}".strip(),
                observed_at=stamp,
            )
        )

    return created
