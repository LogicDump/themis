"""ProcessEvent V1: fatos temporais observados, sem cálculo jurídico.

Este store não representa prazos nem pendências. Ele apenas normaliza datas
que já existem em fontes estruturadas do processo e preserva o valor bruto.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

MIGRATION_VERSION = "process-event-store-v1"
ID_NAMESPACE = uuid.UUID("5f49cb37-c4d8-4d13-9f68-2d8a6d8d8f01")

SCHEMA = """
CREATE TABLE IF NOT EXISTS process_events(
  event_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_subtype TEXT,
  source_entity TEXT NOT NULL,
  source_id TEXT NOT NULL,
  title TEXT,
  description TEXT,
  event_date TEXT,
  event_time TEXT,
  date_precision TEXT NOT NULL,
  raw_datetime TEXT,
  timezone TEXT,
  source_refs_json TEXT NOT NULL,
  provenance_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(process_id, source_entity, source_id)
);
CREATE INDEX IF NOT EXISTS idx_process_events_process_date
  ON process_events(process_id, event_date, event_time, event_id);
CREATE INDEX IF NOT EXISTS idx_process_events_process_type
  ON process_events(process_id, event_type, date_precision);
"""

_LOCAL_DATETIME = re.compile(r"^\s*(\d{2})/(\d{2})/(\d{4})\s+(\d{2}):(\d{2})(?::(\d{2}))?\s*$")
_LOCAL_DATE = re.compile(r"^\s*(\d{2})/(\d{2})/(\d{4})\s*$")
_DISTRIBUTION = re.compile(
    r"Distribui(?:ção|cao)\s*:\s*(\d{2}/\d{2}/\d{4})(?:\s+às?\s+(\d{2}:\d{2}))?",
    re.IGNORECASE,
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _decode_json(value: Any, default: Any) -> Any:
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except (TypeError, ValueError):
        return default


def _event_id(process_id: str, source_entity: str, source_id: str) -> str:
    value = f"{process_id}\x00{source_entity}\x00{source_id}"
    return f"pe_{uuid.uuid5(ID_NAMESPACE, value).hex}"


def _normalize_datetime(raw: Any) -> dict[str, Any]:
    """Normalize only recognizable representations; never invent timezone."""
    if raw is None or str(raw).strip() == "":
        return {"event_date": None, "event_time": None, "date_precision": "UNKNOWN", "raw_datetime": None, "timezone": None}
    text = str(raw).strip()
    match = _LOCAL_DATETIME.match(text)
    if match:
        day, month, year, hour, minute, second = match.groups()
        try:
            datetime(int(year), int(month), int(day), int(hour), int(minute), int(second or 0))
        except ValueError:
            return {"event_date": None, "event_time": None, "date_precision": "UNKNOWN", "raw_datetime": text, "timezone": None}
        return {
            "event_date": f"{year}-{month}-{day}",
            "event_time": f"{hour}:{minute}" + (f":{second}" if second else ""),
            "date_precision": "DATETIME",
            "raw_datetime": text,
            "timezone": None,
        }
    match = _LOCAL_DATE.match(text)
    if match:
        day, month, year = match.groups()
        try:
            datetime(int(year), int(month), int(day))
        except ValueError:
            return {"event_date": None, "event_time": None, "date_precision": "UNKNOWN", "raw_datetime": text, "timezone": None}
        return {"event_date": f"{year}-{month}-{day}", "event_time": None, "date_precision": "DATE", "raw_datetime": text, "timezone": None}

    iso_text = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(iso_text)
    except ValueError:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            try:
                datetime.fromisoformat(text)
                return {"event_date": text, "event_time": None, "date_precision": "DATE", "raw_datetime": text, "timezone": None}
            except ValueError:
                pass
        return {"event_date": None, "event_time": None, "date_precision": "UNKNOWN", "raw_datetime": text, "timezone": None}
    timezone_value = None
    if parsed.tzinfo is not None:
        timezone_value = "UTC" if text.endswith("Z") else (text[-6:] if re.search(r"[+-]\d{2}:\d{2}$", text) else None)
    return {
        "event_date": parsed.date().isoformat(),
        "event_time": parsed.strftime("%H:%M:%S") if parsed.second else parsed.strftime("%H:%M"),
        "date_precision": "DATETIME",
        "raw_datetime": text,
        "timezone": timezone_value,
    }


def _base_event(process_id: str, event_type: str, subtype: str | None, source_entity: str, source_id: str, title: Any, description: Any, raw: Any, source_refs: Any, provenance: Any) -> dict[str, Any]:
    return {
        "event_id": _event_id(process_id, source_entity, source_id),
        "process_id": process_id,
        "event_type": event_type,
        "event_subtype": subtype,
        "source_entity": source_entity,
        "source_id": source_id,
        "title": title,
        "description": description,
        **_normalize_datetime(raw),
        "source_refs_json": _json(source_refs if source_refs is not None else []),
        "provenance_json": _json(provenance if provenance is not None else {}),
    }


def migrate_connection(db: sqlite3.Connection) -> dict[str, Any]:
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    db.executescript(SCHEMA)
    applied = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION,)).fetchone()
    db.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)", (MIGRATION_VERSION, _now()))
    db.commit()
    return {"migration_version": MIGRATION_VERSION, "already_applied": bool(applied)}


def _movement_events(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='movements'").fetchone():
        return []
    result = []
    rows = db.execute("SELECT * FROM movements WHERE process_id=? ORDER BY sequence", (process_id,)).fetchall()
    for row in rows:
        payload = _decode_json(row["payload_json"], {})
        source_refs = {
            "sequence": row["sequence"],
            "source_ref": payload.get("source_ref"),
            "protocol": row["protocol"],
        }
        provenance = payload.get("provenance") or payload.get("provenance_json") or {}
        result.append(_base_event(
            process_id, "MOVEMENT", row["movement_type"], "MOVEMENT", row["movement_id"],
            row["title"] or row["movement_type"] or "Movimentação",
            payload.get("description") or payload.get("content"),
            row["occurred_at"] or payload.get("source_datetime") or payload.get("occurred_at"),
            source_refs, provenance,
        ))
    return result


def _hearing_events(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='hearings'").fetchone():
        return []
    result = []
    for row in db.execute("SELECT * FROM hearings WHERE process_id=? ORDER BY hearing_id", (process_id,)).fetchall():
        event = _base_event(
            process_id, "HEARING", row["hearing_type"], "HEARING", row["hearing_id"],
            f"Audiência ({row['hearing_type']})" if row["hearing_type"] else "Audiência",
            row["outcome_notes"], row["scheduled_at"], _decode_json(row["source_refs_json"], []), _decode_json(row["provenance_json"], {}),
        )
        raw_scheduled = str(row["scheduled_at"] or "").strip()
        source_precision = str(row["date_precision"] or "").upper()
        explicit_time = bool(re.search(r"(?:\s|T)\d{2}:\d{2}(?::\d{2})?", raw_scheduled))
        if raw_scheduled and not explicit_time:
            # HEARING is the source of temporal precision here. A date-only
            # scheduled_at must never become an invented midnight datetime.
            if source_precision in {"DAY", "DATE"}:
                event["date_precision"] = source_precision
            elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_scheduled):
                event["date_precision"] = "DAY"
            event["event_time"] = None
        result.append(event)
    return result


def _distribution_events(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='process_metadata'").fetchone():
        return []
    row = db.execute("SELECT summary, provenance_json FROM process_metadata WHERE process_id=?", (process_id,)).fetchone()
    if not row:
        return []
    provenance = _decode_json(row["provenance_json"], {})
    basic = provenance.get("basic_data") if isinstance(provenance, dict) else {}
    candidates = [row["summary"], basic.get("distribuicao") if isinstance(basic, dict) else None]
    for candidate in candidates:
        match = _DISTRIBUTION.search(str(candidate or ""))
        if match:
            raw = match.group(1) + (f" {match.group(2)}" if match.group(2) else "")
            return [_base_event(process_id, "DISTRIBUTION", None, "PROCESS_METADATA", process_id, "Distribuição", str(candidate), raw, {"field": "summary/provenance_json.basic_data.distribuicao", "raw_value": candidate}, provenance)]
    return []


def _publication_events(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='publications'").fetchone():
        return []
    result = []
    for row in db.execute("SELECT * FROM publications WHERE process_id=? AND (published_on IS NOT NULL OR available_on IS NOT NULL) ORDER BY publication_id", (process_id,)).fetchall():
        published = row["published_on"]
        raw = published or row["available_on"]
        subtype = "PUBLISHED" if published else "AVAILABLE"
        result.append(_base_event(
            process_id, "PUBLICATION", subtype, "PUBLICATION", row["publication_id"],
            row["publication_type"] or "Publicação", row["full_text"], raw,
            {"available_on": row["available_on"], "published_on": row["published_on"], "communication_id": row["communication_id"], "source_url": row["source_url"]},
            _decode_json(row["provenance_json"], {}),
        ))
    return result


def materialize_process_events(db: sqlite3.Connection, process_id: str) -> dict[str, Any]:
    """Reconcile all V1 observed temporal facts for one process."""
    migrate_connection(db)
    desired = _movement_events(db, process_id) + _hearing_events(db, process_id) + _distribution_events(db, process_id) + _publication_events(db, process_id)
    now = _now()
    existing = {row["event_id"]: row for row in db.execute("SELECT * FROM process_events WHERE process_id=?", (process_id,)).fetchall()}
    for item in desired:
        old = existing.get(item["event_id"])
        values = (
            item["event_id"], item["process_id"], item["event_type"], item["event_subtype"], item["source_entity"], item["source_id"],
            item["title"], item["description"], item["event_date"], item["event_time"], item["date_precision"], item["raw_datetime"], item["timezone"],
            item["source_refs_json"], item["provenance_json"], old["created_at"] if old else now, now,
        )
        db.execute("""INSERT INTO process_events(
          event_id, process_id, event_type, event_subtype, source_entity, source_id, title, description,
          event_date, event_time, date_precision, raw_datetime, timezone, source_refs_json, provenance_json, created_at, updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(event_id) DO UPDATE SET
          event_type=excluded.event_type, event_subtype=excluded.event_subtype, source_entity=excluded.source_entity,
          source_id=excluded.source_id, title=excluded.title, description=excluded.description, event_date=excluded.event_date,
          event_time=excluded.event_time, date_precision=excluded.date_precision, raw_datetime=excluded.raw_datetime,
          timezone=excluded.timezone, source_refs_json=excluded.source_refs_json, provenance_json=excluded.provenance_json,
          updated_at=excluded.updated_at""", values)
    desired_ids = {item["event_id"] for item in desired}
    stale = [event_id for event_id in existing if event_id not in desired_ids]
    if stale:
        db.executemany("DELETE FROM process_events WHERE event_id=?", [(event_id,) for event_id in stale])
    db.commit()
    return {"process_id": process_id, "materialized": len(desired), "inserted_or_updated": len(desired), "deleted": len(stale)}


def materialize_all(db: sqlite3.Connection) -> dict[str, Any]:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='processes'").fetchone():
        return {"processes": 0, "events": 0}
    results = [materialize_process_events(db, row[0]) for row in db.execute("SELECT process_id FROM processes ORDER BY process_id")]
    return {"processes": len(results), "events": sum(item["materialized"] for item in results)}


def list_process_events(db: sqlite3.Connection, process_id: str, *, event_type: str | None = None, date_precision: str | None = None) -> list[dict[str, Any]]:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='process_events'").fetchone():
        return []
    query = "SELECT * FROM process_events WHERE process_id=?"
    params: list[Any] = [process_id]
    if event_type:
        query += " AND event_type=?"; params.append(event_type.upper())
    if date_precision:
        query += " AND date_precision=?"; params.append(date_precision.upper())
    query += " ORDER BY CASE WHEN event_date IS NULL THEN 1 ELSE 0 END, event_date, event_time, event_id"
    rows = db.execute(query, params).fetchall()
    result = []
    for row in rows:
        value = dict(row)
        value["source_refs"] = _decode_json(value.pop("source_refs_json"), [])
        value["provenance"] = _decode_json(value.pop("provenance_json"), {})
        result.append(value)
    return result
