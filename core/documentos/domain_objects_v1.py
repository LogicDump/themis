"""Objetos de domínio operacionais do Jurídico.

Este módulo mantém os dados canônicos fora de arquivos Markdown. Candidatos
extraídos continuam sendo candidatos até confirmação humana; provenance e
source refs são preservados como dados estruturados.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MIGRATION_VERSION = "domain-objects-v1"
MIGRATION_VERSION_2 = "domain-objects-v2-extraction-runs"
MIGRATION_VERSION_3 = "domain-objects-v3-deadline-term"
ID_NAMESPACE = uuid.UUID("b79b9bf0-9ccf-5f19-9d40-8a6ee0dbdc35")
OWNER_TYPES = {"MATTER": "matters", "PROCESS": "processes"}
DATE_PRECISIONS = {"EXACT", "DAY", "MONTH", "YEAR", "APPROXIMATE", "UNKNOWN"}
STATUSES = {"CANDIDATE", "CONFIRMED", "CONFLICTING"}


SCHEMA = """
CREATE TABLE IF NOT EXISTS matter_metadata(
  matter_id TEXT PRIMARY KEY,
  display_name TEXT,
  subject TEXT,
  status TEXT,
  description TEXT,
  summary TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  provenance_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(matter_id) REFERENCES matters(matter_id)
);
CREATE TABLE IF NOT EXISTS process_metadata(
  process_id TEXT PRIMARY KEY,
  classe TEXT,
  assunto TEXT,
  tribunal TEXT,
  comarca TEXT,
  unidade TEXT,
  grau TEXT,
  status TEXT,
  fase TEXT,
  summary TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  provenance_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(process_id) REFERENCES processes(process_id)
);
CREATE TABLE IF NOT EXISTS deadlines(
  deadline_id TEXT PRIMARY KEY,
  owner_type TEXT NOT NULL CHECK(owner_type IN ('MATTER','PROCESS')),
  owner_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  deadline_type TEXT,
  term TEXT,
  due_at TEXT,
  date_precision TEXT NOT NULL CHECK(date_precision IN ('EXACT','DAY','MONTH','YEAR','APPROXIMATE','UNKNOWN')),
  timezone TEXT,
  status TEXT NOT NULL,
  priority TEXT,
  responsible TEXT,
  triggering_event TEXT,
  legal_basis TEXT,
  confidence TEXT,
  extraction_run_id TEXT,
  confirmation_status TEXT NOT NULL,
  source_refs_json TEXT NOT NULL DEFAULT '[]',
  provenance_json TEXT NOT NULL DEFAULT '{}',
  fingerprint TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS strategy_entries(
  strategy_id TEXT PRIMARY KEY,
  owner_type TEXT NOT NULL CHECK(owner_type IN ('MATTER','PROCESS')),
  owner_id TEXT NOT NULL,
  entry_type TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  status TEXT NOT NULL,
  author_type TEXT NOT NULL CHECK(author_type IN ('HUMAN','AI')),
  confidence TEXT,
  version INTEGER NOT NULL,
  provenance_json TEXT NOT NULL DEFAULT '{}',
  fingerprint TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  extraction_run_id TEXT
);
CREATE TABLE IF NOT EXISTS hearings(
  hearing_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  hearing_type TEXT NOT NULL,
  scheduled_at TEXT,
  date_precision TEXT NOT NULL CHECK(date_precision IN ('EXACT','DAY','MONTH','YEAR','APPROXIMATE','UNKNOWN')),
  location TEXT,
  meeting_info TEXT,
  status TEXT NOT NULL,
  outcome_notes TEXT,
  extraction_run_id TEXT,
  source_refs_json TEXT NOT NULL DEFAULT '[]',
  provenance_json TEXT NOT NULL DEFAULT '{}',
  fingerprint TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(process_id) REFERENCES processes(process_id)
);
CREATE TABLE IF NOT EXISTS hearing_participants(
  hearing_id TEXT NOT NULL,
  participant TEXT NOT NULL,
  role TEXT,
  PRIMARY KEY(hearing_id, participant, role),
  FOREIGN KEY(hearing_id) REFERENCES hearings(hearing_id)
);
CREATE TABLE IF NOT EXISTS pending_items(
  pending_id TEXT PRIMARY KEY,
  owner_type TEXT NOT NULL CHECK(owner_type IN ('MATTER','PROCESS')),
  owner_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL,
  priority TEXT,
  responsible TEXT,
  due_at TEXT,
  source_origin TEXT,
  source_refs_json TEXT NOT NULL DEFAULT '[]',
  provenance_json TEXT NOT NULL DEFAULT '{}',
  resolved_at TEXT,
  extraction_run_id TEXT,
  fingerprint TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS deadlines_owner ON deadlines(owner_type, owner_id, due_at);
CREATE INDEX IF NOT EXISTS strategy_owner ON strategy_entries(owner_type, owner_id, version);
CREATE INDEX IF NOT EXISTS hearings_process ON hearings(process_id, scheduled_at);
CREATE INDEX IF NOT EXISTS pending_owner ON pending_items(owner_type, owner_id, due_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _list_json(value: Any) -> str:
    return json.dumps(value if isinstance(value, list) else [], ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(*values: Any) -> str:
    return hashlib.sha256("|".join(str(value if value is not None else "") for value in values).encode("utf-8")).hexdigest()


def _owner(db: sqlite3.Connection, owner_type: str, owner_id: str, *, process_only: bool = False) -> str:
    code = str(owner_type).upper()
    if code not in OWNER_TYPES or (process_only and code != "PROCESS"):
        raise ValueError("owner_type inválido")
    table = OWNER_TYPES[code]
    column = "matter_id" if code == "MATTER" else "process_id"
    if db.execute(f"SELECT 1 FROM {table} WHERE {column}=?", (owner_id,)).fetchone() is None:
        raise ValueError("owner inexistente")
    return code


def _date(value: Any, precision: Any = None) -> tuple[str | None, str]:
    if value is None or str(value).strip() == "":
        return None, "UNKNOWN"
    s_val = str(value).strip()
    p = str(precision or "").strip().upper()
    if not p or p == "NONE":
        if re.fullmatch(r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?$", s_val):
            p = "EXACT" if ("T" in s_val or " " in s_val) else "DAY"
        elif re.fullmatch(r"^\d{4}-\d{2}$", s_val):
            p = "MONTH"
        elif re.fullmatch(r"^\d{4}$", s_val):
            p = "YEAR"
        else:
            p = "UNKNOWN"
    if p not in DATE_PRECISIONS:
        raise ValueError("date_precision inválida")
    if p == "UNKNOWN":
        return None, p
    if not re.fullmatch(r"^\d{4}(?:-\d{2}(?:-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?)?)?$", s_val):
        raise ValueError("data incompatível com date_precision")
    return s_val, p


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
        v2 = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION_2,)).fetchone()
        if not v2:
            for table in ("deadlines", "strategy_entries", "hearings", "pending_items"):
                columns = {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
                if "extraction_run_id" not in columns:
                    db.execute(f"ALTER TABLE {table} ADD COLUMN extraction_run_id TEXT")
            db.execute("""CREATE TABLE IF NOT EXISTS domain_extraction_runs(
                extraction_run_id TEXT PRIMARY KEY,
                owner_type TEXT NOT NULL CHECK(owner_type IN ('MATTER','PROCESS')),
                owner_id TEXT NOT NULL,
                target TEXT NOT NULL CHECK(target IN ('DEADLINES','HEARINGS','PENDING','STRATEGY')),
                source_derived_content_id TEXT,
                source_content_version INTEGER,
                pipeline_version TEXT NOT NULL,
                model_provider TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                error TEXT
            )""")
            db.execute("INSERT INTO schema_migrations(version, applied_at) VALUES(?,?)", (MIGRATION_VERSION_2, _now()))
            db.commit()
        v3 = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION_3,)).fetchone()
        if not v3:
            columns = {row[1] for row in db.execute("PRAGMA table_info(deadlines)")}
            if "term" not in columns:
                db.execute("ALTER TABLE deadlines ADD COLUMN term TEXT")
            db.execute("INSERT INTO schema_migrations(version, applied_at) VALUES(?,?)", (MIGRATION_VERSION_3, _now()))
            db.commit()
        current_version = MIGRATION_VERSION_3 if v3 or not applied or not v2 else MIGRATION_VERSION_3
        return {"migration_version": MIGRATION_VERSION_3, "already_applied": bool(applied and v2 and v3)}
    finally:
        db.close()


def _metadata(db: sqlite3.Connection, table: str, key: str, owner_id: str, values: dict[str, Any]) -> dict[str, Any]:
    now = _now()
    old = db.execute(f"SELECT version,created_at FROM {table} WHERE {key}=?", (owner_id,)).fetchone()
    version = int(old["version"]) + 1 if old else 1
    columns = ["display_name", "subject", "status", "description", "summary"] if table == "matter_metadata" else ["classe", "assunto", "tribunal", "comarca", "unidade", "grau", "status", "fase", "summary"]
    data = [values.get(column) for column in columns]
    if old:
        current = db.execute(f"SELECT {','.join(columns)},provenance_json FROM {table} WHERE {key}=?", (owner_id,)).fetchone()
        requested_provenance = _json(values.get("provenance"))
        if all(current[column] == value for column, value in zip(columns, data)) and current["provenance_json"] == requested_provenance:
            return {"owner_id": owner_id, "version": int(old["version"]), "updated_at": old["created_at"], "unchanged": True}
    data.extend([version, _json(values.get("provenance")), old["created_at"] if old else now, now])
    if old:
        assignments = ",".join(f"{column}=?" for column in columns) + ",version=?,provenance_json=?,updated_at=?"
        db.execute(f"UPDATE {table} SET {assignments} WHERE {key}=?", (*data[:-2], data[-1], owner_id))
    else:
        db.execute(f"INSERT INTO {table}({key},{','.join(columns)},version,provenance_json,created_at,updated_at) VALUES({','.join('?' for _ in range(len(data)+1))})", (owner_id, *data))
    return {"owner_id": owner_id, "version": version, "updated_at": now}


def upsert_matter_metadata(db: sqlite3.Connection, matter_id: str, *, commit: bool = True, **values: Any) -> dict[str, Any]:
    _owner(db, "MATTER", matter_id)
    result = _metadata(db, "matter_metadata", "matter_id", matter_id, values)
    if commit: db.commit()
    return result


def upsert_process_metadata(db: sqlite3.Connection, process_id: str, *, commit: bool = True, **values: Any) -> dict[str, Any]:
    _owner(db, "PROCESS", process_id)
    result = _metadata(db, "process_metadata", "process_id", process_id, values)
    if commit: db.commit()
    return result


def submit_deadline_candidates(db: sqlite3.Connection, owner_type: str, owner_id: str, candidates: list[dict[str, Any]], *, extraction_run_id: str | None = None, commit: bool = True) -> list[str]:
    code = _owner(db, owner_type, owner_id)
    ids = []
    try:
        for item in candidates:
            due_at, precision = _date(item.get("due_at"), item.get("date_precision"))
            term = str(item.get("term")).strip() if item.get("term") is not None and str(item.get("term")).strip() else None
            refs = item.get("source_refs") or []
            if str(item.get("source_origin", "extracted")).lower() != "manual" and not refs:
                raise ValueError("prazo extraído exige source_refs")
            title = " ".join(str(item.get("title", "")).split())
            if not title:
                raise ValueError("title obrigatório")
            fp_parts = [code, owner_id, title, item.get("deadline_type"), due_at, item.get("triggering_event")]
            if term:
                fp_parts.append(term)
            fp = item.get("fingerprint") or _fingerprint(*fp_parts)
            existing = db.execute("SELECT deadline_id FROM deadlines WHERE fingerprint=?", (fp,)).fetchone()
            deadline_id = existing["deadline_id"] if existing else "deadline_" + uuid.uuid5(ID_NAMESPACE, fp).hex
            values = (
                deadline_id, code, owner_id, title, item.get("description"), item.get("deadline_type"),
                term, due_at, precision, item.get("timezone"), item.get("status", "CANDIDATE"),
                item.get("priority"), item.get("responsible"), item.get("triggering_event"),
                item.get("legal_basis"), item.get("confidence"), item.get("confirmation_status", "PENDING"),
                _list_json(refs), _json(item.get("provenance")), fp, _now(), _now(), extraction_run_id
            )
            if existing:
                db.execute(
                    """UPDATE deadlines SET title=?,description=?,deadline_type=?,term=?,due_at=?,date_precision=?,
                    timezone=?,status=?,priority=?,responsible=?,triggering_event=?,legal_basis=?,confidence=?,
                    confirmation_status=?,source_refs_json=?,provenance_json=?,extraction_run_id=?,updated_at=?
                    WHERE deadline_id=?""",
                    (title, item.get("description"), item.get("deadline_type"), term, due_at, precision,
                     item.get("timezone"), item.get("status", "CANDIDATE"), item.get("priority"), item.get("responsible"),
                     item.get("triggering_event"), item.get("legal_basis"), item.get("confidence"),
                     item.get("confirmation_status", "PENDING"), _list_json(refs), _json(item.get("provenance")),
                     extraction_run_id, values[-2], deadline_id)
                )
            else:
                db.execute("""INSERT INTO deadlines(
                    deadline_id,owner_type,owner_id,title,description,deadline_type,term,due_at,date_precision,
                    timezone,status,priority,responsible,triggering_event,legal_basis,confidence,
                    confirmation_status,source_refs_json,provenance_json,fingerprint,created_at,updated_at,extraction_run_id
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", values)
            ids.append(deadline_id)
        if commit: db.commit()
        return ids
    except Exception:
        db.rollback()
        raise


def submit_strategy_candidates(db: sqlite3.Connection, owner_type: str, owner_id: str, candidates: list[dict[str, Any]], *, extraction_run_id: str | None = None, commit: bool = True) -> list[str]:
    code = _owner(db, owner_type, owner_id)
    ids = []
    try:
        for item in candidates:
            title, content = " ".join(str(item.get("title", "")).split()), str(item.get("content", "")).strip()
            if not title or not content: raise ValueError("strategy title/content obrigatórios")
            author = str(item.get("author_type", "AI")).upper()
            if author not in {"HUMAN", "AI"}: raise ValueError("author_type inválido")
            fp = item.get("fingerprint") or _fingerprint(code, owner_id, item.get("entry_type", "note"), title, content)
            row = db.execute("SELECT strategy_id FROM strategy_entries WHERE fingerprint=?", (fp,)).fetchone()
            sid = row["strategy_id"] if row else "strategy_" + uuid.uuid5(ID_NAMESPACE, fp).hex
            version = db.execute("SELECT COALESCE(MAX(version),0)+1 FROM strategy_entries WHERE owner_type=? AND owner_id=? AND entry_type=? AND title=?", (code, owner_id, item.get("entry_type", "note"), title)).fetchone()[0] if not row else db.execute("SELECT version FROM strategy_entries WHERE strategy_id=?", (sid,)).fetchone()[0]
            if row:
                db.execute("UPDATE strategy_entries SET content=?,status=?,author_type=?,confidence=?,provenance_json=?,extraction_run_id=?,updated_at=? WHERE strategy_id=?", (content, item.get("status", "CANDIDATE"), author, item.get("confidence"), _json(item.get("provenance")), extraction_run_id, _now(), sid))
            else:
                db.execute("""INSERT INTO strategy_entries(
                    strategy_id,owner_type,owner_id,entry_type,title,content,status,author_type,confidence,
                    version,provenance_json,fingerprint,created_at,updated_at,extraction_run_id
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (sid, code, owner_id, item.get("entry_type", "note"), title, content, item.get("status", "CANDIDATE"), author, item.get("confidence"), version, _json(item.get("provenance")), fp, _now(), _now(), extraction_run_id))
            ids.append(sid)
        if commit: db.commit()
        return ids
    except Exception:
        db.rollback(); raise


def submit_hearing_candidates(db: sqlite3.Connection, process_id: str, candidates: list[dict[str, Any]], *, extraction_run_id: str | None = None, commit: bool = True) -> list[str]:
    _owner(db, "PROCESS", process_id, process_only=True); ids = []
    try:
        for item in candidates:
            scheduled, precision = _date(item.get("scheduled_at"), item.get("date_precision"))
            refs = item.get("source_refs") or []
            if str(item.get("source_origin", "extracted")).lower() != "manual" and not refs: raise ValueError("audiência extraída exige source_refs")
            htype = " ".join(str(item.get("hearing_type", "")).split())
            if not htype: raise ValueError("hearing_type obrigatório")
            fp = item.get("fingerprint") or _fingerprint(process_id, htype, scheduled, item.get("location"), item.get("meeting_info"))
            row = db.execute("SELECT hearing_id FROM hearings WHERE fingerprint=?", (fp,)).fetchone(); hid = row["hearing_id"] if row else "hearing_" + uuid.uuid5(ID_NAMESPACE, fp).hex
            if row:
                db.execute("UPDATE hearings SET scheduled_at=?,date_precision=?,location=?,meeting_info=?,status=?,outcome_notes=?,source_refs_json=?,provenance_json=?,extraction_run_id=?,updated_at=? WHERE hearing_id=?", (scheduled, precision, item.get("location"), item.get("meeting_info"), item.get("status", "CANDIDATE"), item.get("outcome_notes"), _list_json(refs), _json(item.get("provenance")), extraction_run_id, _now(), hid))
            else:
                db.execute("""INSERT INTO hearings(
                    hearing_id,process_id,hearing_type,scheduled_at,date_precision,location,meeting_info,status,
                    outcome_notes,source_refs_json,provenance_json,fingerprint,created_at,updated_at,extraction_run_id
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (hid, process_id, htype, scheduled, precision, item.get("location"), item.get("meeting_info"), item.get("status", "CANDIDATE"), item.get("outcome_notes"), _list_json(refs), _json(item.get("provenance")), fp, _now(), _now(), extraction_run_id))
            for participant in item.get("participants") or []:
                name = participant.get("name") if isinstance(participant, dict) else str(participant)
                role = participant.get("role") if isinstance(participant, dict) else None
                if name: db.execute("INSERT OR IGNORE INTO hearing_participants VALUES(?,?,?)", (hid, name, role))
            ids.append(hid)
        if commit: db.commit()
        return ids
    except Exception:
        db.rollback(); raise


def submit_pending_candidates(db: sqlite3.Connection, owner_type: str, owner_id: str, candidates: list[dict[str, Any]], *, extraction_run_id: str | None = None, commit: bool = True) -> list[str]:
    code = _owner(db, owner_type, owner_id); ids = []
    try:
        for item in candidates:
            title = " ".join(str(item.get("title", "")).split())
            if not title: raise ValueError("title obrigatório")
            refs = item.get("source_refs") or []
            origin = str(item.get("source_origin", "extracted")).lower()
            if origin != "manual" and not refs: raise ValueError("pendência extraída exige source_refs")
            fp = item.get("fingerprint") or _fingerprint(code, owner_id, title, item.get("description"), item.get("due_at"))
            row = db.execute("SELECT pending_id FROM pending_items WHERE fingerprint=?", (fp,)).fetchone(); pid = row["pending_id"] if row else "pending_" + uuid.uuid5(ID_NAMESPACE, fp).hex
            values = (pid, code, owner_id, title, item.get("description"), item.get("status", "OPEN"), item.get("priority"), item.get("responsible"), item.get("due_at"), origin, _list_json(refs), _json(item.get("provenance")), item.get("resolved_at"), fp, _now(), _now())
            if row:
                db.execute("UPDATE pending_items SET description=?,status=?,priority=?,responsible=?,due_at=?,source_origin=?,source_refs_json=?,provenance_json=?,resolved_at=?,extraction_run_id=?,updated_at=? WHERE pending_id=?", (item.get("description"), item.get("status", "OPEN"), item.get("priority"), item.get("responsible"), item.get("due_at"), origin, _list_json(refs), _json(item.get("provenance")), item.get("resolved_at"), extraction_run_id, values[-2], pid))
            else: db.execute("""INSERT INTO pending_items(
                pending_id,owner_type,owner_id,title,description,status,priority,responsible,due_at,source_origin,
                source_refs_json,provenance_json,resolved_at,fingerprint,created_at,updated_at,extraction_run_id
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (*values, extraction_run_id))
            ids.append(pid)
        if commit: db.commit()
        return ids
    except Exception:
        db.rollback(); raise


def _rows(db: sqlite3.Connection, table: str, owner_type: str, owner_id: str, where: str = "") -> list[dict[str, Any]]:
    rows = db.execute(f"SELECT * FROM {table} WHERE owner_type=? AND owner_id=? {where}", (_owner_code(owner_type), owner_id)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        for key in ("source_refs_json", "provenance_json"):
            if key in item:
                item[key.removesuffix("_json")] = json.loads(item.pop(key))
        result.append(item)
    return result


def _owner_code(owner_type: str) -> str:
    code = str(owner_type).upper()
    if code not in OWNER_TYPES: raise ValueError("owner_type inválido")
    return code


def deadline_view_items(db: sqlite3.Connection, owner_type: str, owner_id: str) -> list[dict[str, Any]]:
    return _rows(db, "deadlines", owner_type, owner_id, "ORDER BY CASE WHEN due_at IS NULL THEN 1 ELSE 0 END,due_at,deadline_id")


def strategy_view_items(db: sqlite3.Connection, owner_type: str, owner_id: str) -> list[dict[str, Any]]:
    return _rows(db, "strategy_entries", owner_type, owner_id, "ORDER BY version DESC,strategy_id")


def pending_view_items(db: sqlite3.Connection, owner_type: str, owner_id: str) -> list[dict[str, Any]]:
    return _rows(db, "pending_items", owner_type, owner_id, "ORDER BY CASE WHEN due_at IS NULL THEN 1 ELSE 0 END,due_at,pending_id")


def hearing_view_items(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    rows = db.execute("SELECT * FROM hearings WHERE process_id=? ORDER BY CASE WHEN scheduled_at IS NULL THEN 1 ELSE 0 END,scheduled_at,hearing_id", (process_id,)).fetchall()
    result = []
    for row in rows:
        item = dict(row); item["source_refs"] = json.loads(item.pop("source_refs_json")); item["provenance"] = json.loads(item.pop("provenance_json"))
        item["participants"] = [dict(x) for x in db.execute("SELECT participant,role FROM hearing_participants WHERE hearing_id=? ORDER BY participant", (row["hearing_id"],))]
        result.append(item)
    return result


def metadata_view(db: sqlite3.Connection, owner_type: str, owner_id: str) -> dict[str, Any] | None:
    table, key = ("matter_metadata", "matter_id") if str(owner_type).lower() == "matter" else ("process_metadata", "process_id")
    row = db.execute(f"SELECT * FROM {table} WHERE {key}=?", (owner_id,)).fetchone()
    if not row: return None
    item = dict(row); item["provenance"] = json.loads(item.pop("provenance_json")); return item
