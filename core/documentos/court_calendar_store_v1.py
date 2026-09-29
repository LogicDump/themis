"""Versioned local cache for official court-calendar source snapshots/events."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from core.documentos.court_calendar_provider_v1 import RawSourceSnapshot

MIGRATION_VERSION = "court-calendar-store-v1"
_NAMESPACE = uuid.UUID("98343335-269a-440e-a997-3bb673459ead")
_SCHEMA = """
CREATE TABLE IF NOT EXISTS court_calendar_snapshots(
  snapshot_id TEXT PRIMARY KEY,
  source_url TEXT NOT NULL,
  fetched_at TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  parser_version TEXT NOT NULL,
  content BLOB NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(source_url,content_hash,parser_version)
);
CREATE TABLE IF NOT EXISTS court_calendar_events(
  event_version_id TEXT PRIMARY KEY,
  logical_key TEXT NOT NULL,
  version INTEGER NOT NULL CHECK(version > 0),
  supersedes_event_version_id TEXT,
  is_current INTEGER NOT NULL CHECK(is_current IN (0,1)),
  jurisdiction TEXT NOT NULL,
  court TEXT,
  locality_unit TEXT,
  date TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('BUSINESS_DAY','HOLIDAY','SUSPENDED','RECESS')),
  scope TEXT NOT NULL CHECK(scope IN ('NATIONAL','STATE','COURT','COMARCA','FORUM','UNIT','SYSTEM')),
  applicability TEXT NOT NULL CHECK(applicability IN ('ALL','PHYSICAL','ELECTRONIC')),
  snapshot_id TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(logical_key,version),
  FOREIGN KEY(snapshot_id) REFERENCES court_calendar_snapshots(snapshot_id),
  FOREIGN KEY(supersedes_event_version_id) REFERENCES court_calendar_events(event_version_id)
);
CREATE INDEX IF NOT EXISTS idx_court_calendar_effective
  ON court_calendar_events(jurisdiction,court,locality_unit,date,is_current);
CREATE INDEX IF NOT EXISTS idx_court_calendar_logical_history
  ON court_calendar_events(logical_key,version);
CREATE TABLE IF NOT EXISTS court_calendar_event_snapshots(
  event_version_id TEXT NOT NULL,
  snapshot_id TEXT NOT NULL,
  PRIMARY KEY(event_version_id,snapshot_id),
  FOREIGN KEY(event_version_id) REFERENCES court_calendar_events(event_version_id),
  FOREIGN KEY(snapshot_id) REFERENCES court_calendar_snapshots(snapshot_id)
);
"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def migrate_connection(db: sqlite3.Connection) -> dict[str, Any]:
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    was_applied = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION,)).fetchone()
    db.executescript(_SCHEMA)
    db.execute("INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES(?,?)", (MIGRATION_VERSION, _now()))
    db.commit()
    return {"migration_version": MIGRATION_VERSION, "already_applied": bool(was_applied)}


def store_snapshot(db: sqlite3.Connection, snapshot: RawSourceSnapshot, *, commit: bool = True) -> str:
    digest = hashlib.sha256(snapshot.content).hexdigest()
    if digest != snapshot.content_hash:
        raise ValueError("snapshot content hash inválido")
    snapshot_id = "ccs_" + uuid.uuid5(_NAMESPACE, f"{snapshot.source_url}\0{digest}\0{snapshot.parser_version}").hex
    db.execute("""INSERT OR IGNORE INTO court_calendar_snapshots
      (snapshot_id,source_url,fetched_at,content_hash,parser_version,content,created_at)
      VALUES(?,?,?,?,?,?,?)""", (snapshot_id, snapshot.source_url, snapshot.fetched_at, digest,
        snapshot.parser_version, sqlite3.Binary(snapshot.content), _now()))
    if commit:
        db.commit()
    return snapshot_id


def _record(value: Any) -> dict[str, Any]:
    return asdict(value) if is_dataclass(value) else dict(value)


def _logical_key(row: Mapping[str, Any]) -> str:
    identity = {key: row.get(key) for key in (
        "jurisdiction", "court", "locality_unit", "date", "scope",
        "act_number", "official_source", "source_type", "system_id")}
    return hashlib.sha256(_json(identity).encode("utf-8")).hexdigest()


def store_calendar_events(db: sqlite3.Connection, events: Iterable[Any], *,
                          snapshot_id: str, commit: bool = True) -> tuple[str, ...]:
    if not db.execute("SELECT 1 FROM court_calendar_snapshots WHERE snapshot_id=?", (snapshot_id,)).fetchone():
        raise ValueError("snapshot_id inexistente")
    snapshot = db.execute("SELECT source_url FROM court_calendar_snapshots WHERE snapshot_id=?", (snapshot_id,)).fetchone()
    stored: list[str] = []
    for event in events:
        row = _record(event)
        if row.get("official_source") != snapshot["source_url"]:
            raise ValueError("official_source do evento diverge do snapshot associado")
        logical_key = _logical_key(row)
        latest = db.execute("SELECT * FROM court_calendar_events WHERE logical_key=? ORDER BY version DESC LIMIT 1",
                            (logical_key,)).fetchone()
        payload = _json(row)
        if latest and latest["payload_json"] == payload:
            db.execute("INSERT OR IGNORE INTO court_calendar_event_snapshots(event_version_id,snapshot_id) VALUES(?,?)",
                       (latest["event_version_id"], snapshot_id))
            stored.append(str(latest["event_version_id"]))
            continue
        version = int(latest["version"]) + 1 if latest else 1
        event_id = "cce_" + uuid.uuid5(_NAMESPACE, f"{logical_key}\0{version}\0{hashlib.sha256(payload.encode()).hexdigest()}").hex
        if latest:
            db.execute("UPDATE court_calendar_events SET is_current=0 WHERE event_version_id=?", (latest["event_version_id"],))
        db.execute("""INSERT INTO court_calendar_events(
          event_version_id,logical_key,version,supersedes_event_version_id,is_current,
          jurisdiction,court,locality_unit,date,status,scope,applicability,snapshot_id,payload_json,created_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (event_id, logical_key, version,
            latest["event_version_id"] if latest else None, 1, row["jurisdiction"], row.get("court"),
            row.get("locality_unit"), row["date"], row["status"], row["scope"],
            row.get("applicability", "ALL"), snapshot_id, payload, _now()))
        db.execute("INSERT INTO court_calendar_event_snapshots(event_version_id,snapshot_id) VALUES(?,?)",
                   (event_id, snapshot_id))
        stored.append(event_id)
    if commit:
        db.commit()
    return tuple(stored)


def load_events(db: sqlite3.Connection, *, jurisdiction: str | None = None,
                start_date: str | None = None, end_date: str | None = None,
                include_history: bool = False) -> tuple[dict[str, Any], ...]:
    clauses, args = [], []
    if jurisdiction:
        clauses.append("jurisdiction=?"); args.append(jurisdiction)
    if start_date:
        clauses.append("date>=?"); args.append(start_date)
    if end_date:
        clauses.append("date<=?"); args.append(end_date)
    if not include_history:
        clauses.append("is_current=1")
    sql = "SELECT * FROM court_calendar_events" + (" WHERE " + " AND ".join(clauses) if clauses else "") + " ORDER BY date,logical_key,version"
    output = []
    for row in db.execute(sql, args).fetchall():
        snapshots = [dict(item) for item in db.execute("""SELECT s.snapshot_id,s.source_url,s.fetched_at,
          s.content_hash,s.parser_version FROM court_calendar_event_snapshots x
          JOIN court_calendar_snapshots s ON s.snapshot_id=x.snapshot_id
          WHERE x.event_version_id=? ORDER BY s.fetched_at,s.snapshot_id""", (row["event_version_id"],)).fetchall()]
        output.append({**dict(row), **json.loads(row["payload_json"]),
                       "event_version_id": row["event_version_id"], "logical_key": row["logical_key"],
                       "version_number": row["version"], "snapshot_id": row["snapshot_id"],
                       "source_snapshots": snapshots, "is_current": bool(row["is_current"])})
    return tuple(output)
