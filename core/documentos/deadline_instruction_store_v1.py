"""DeadlineInstruction V1: determinações temporais explícitas, sem vencimento.

A fonte desta camada é exclusivamente o texto das páginas próprias do primeiro
componente de cada Movement. Nenhum resumo, anexo ou calendário participa da
extração.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import Any

from core.documentos.movement_summary_store_v1 import source_pages, source_text_and_hash

MIGRATION_VERSION = "deadline-instruction-store-v1"
MIGRATION_V2 = "deadline-instruction-store-v2-process-event"
ID_NAMESPACE = uuid.UUID("f9abf7bb-c7d8-4e53-bf16-6e87e4a4df64")
EXTRACTION_METHOD = "DETERMINISTIC_V1"

SCHEMA = """
CREATE TABLE IF NOT EXISTS deadline_instructions(
  instruction_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  movement_id TEXT,
  source_event_id TEXT NOT NULL,
  source_entity TEXT NOT NULL,
  source_id TEXT NOT NULL,
  action_text TEXT,
  recipient_text TEXT,
  term_value INTEGER,
  term_unit TEXT NOT NULL,
  counting_qualifier TEXT,
  trigger_text TEXT,
  trigger_status TEXT NOT NULL,
  source_excerpt TEXT NOT NULL,
  source_refs_json TEXT NOT NULL,
  source_hash TEXT NOT NULL,
  extraction_method TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(process_id, instruction_id),
  FOREIGN KEY(movement_id) REFERENCES movements(movement_id) ON DELETE CASCADE,
  FOREIGN KEY(source_event_id) REFERENCES process_events(event_id)
);
CREATE INDEX IF NOT EXISTS idx_deadline_instructions_process
  ON deadline_instructions(process_id, status, trigger_status);
CREATE INDEX IF NOT EXISTS idx_deadline_instructions_movement
  ON deadline_instructions(movement_id, instruction_id);
"""

_NUMBER = r"(?:\d{1,3}(?:\s*\([^\n;)]{1,24}\))?|\(\s*\d{1,3}\s*\))"
_UNIT = r"dias\s+uteis|dias\s+corridos|dias|horas|meses"
_TERM_RE = re.compile(rf"(?P<number>{_NUMBER})\s*(?P<unit>{_UNIT})", re.IGNORECASE)
_PORTAL_RE = re.compile(
    rf"Data\s+da\s+intima(?:ção|cao)\s*:\s*(?P<trigger>[^\n]+).*?Prazo\s*:\s*(?P<number>{_NUMBER})\s*(?P<unit>{_UNIT}).*?Intimad[oa]\s*:\s*(?P<recipient>[^\n]+).*?Teor\s+do\s+Ato\s*:\s*(?P<action>.+?)(?=(?:\n|$))",
    re.IGNORECASE | re.DOTALL,
)
_ORDER_RE = re.compile(
    rf"(?P<prefix>.{{0,260}}?)(?:no\s+prazo\s+de|prazo\s+(?:comum\s+)?de|dentro\s+de)\s*(?P<number>{_NUMBER})\s*(?P<unit>{_UNIT})(?P<suffix>.{{0,320}})",
    re.IGNORECASE | re.DOTALL,
)
_UNTIL_RE = re.compile(
    r"(?P<prefix>.{0,260}?)(?:até|ate)\s+(?P<date>\d{1,2}/\d{1,2}/\d{2,4})(?P<suffix>.{0,220})",
    re.IGNORECASE | re.DOTALL,
)
_UNSPECIFIED_RE = re.compile(
    r"(?P<prefix>.{0,260}?)(?:aguarde-se\s+o\s+decurso\s+do\s+prazo|decorrido\s+o\s+prazo|prazo\s+para\s+(?:manifestação|resposta|cumprimento))(?P<suffix>.{0,260})",
    re.IGNORECASE | re.DOTALL,
)
_TRIGGER_RE = re.compile(
    r"(?:a\s+contar\s+de|contad[oa]s?\s+a\s+partir\s+d[aeo]|após|apos|"
    r"da\s+intima(?:ção|cao)|da\s+ciência|da\s+ciencia|da\s+publicação|da\s+publicacao)"
    r"([^.;\n]{0,160})",
    re.IGNORECASE,
)
_ROLE_RECIPIENT_RE = re.compile(r"(?:o|a)?\s*(requerido|requerente|partes?|minist[eé]rio\s+p[úu]blico|genitor|genitora)\b", re.IGNORECASE)
_RECIPIENT_RE = re.compile(r"(?:intimad[oa]|destinatário|destinatario)\s*[:\s]+([^,.;\n]{2,120})", re.IGNORECASE)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _number(value: str) -> int | None:
    match = re.search(r"\d+", value or "")
    return int(match.group(0)) if match else None


def _unit(value: str) -> str:
    normalized = " ".join((value or "").lower().split())
    if "dia" in normalized and "útil" in normalized or "dia" in normalized and "util" in normalized:
        return "BUSINESS_DAYS"
    if "dia" in normalized:
        return "DAYS"
    if "hora" in normalized:
        return "HOURS"
    if "mês" in normalized or "mes" in normalized:
        return "MONTHS"
    return "UNSPECIFIED"


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    result = " ".join(str(value).replace("\ufffe", "").split())
    return result or None


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.split()).casefold()


def _excerpt(text: str, start: int, end: int) -> str:
    left = max(0, start - 180)
    right = min(len(text), end + 260)
    return _clean(text[left:right]) or ""


def _trigger(text: str, window: str, *, portal_trigger: str | None = None) -> tuple[str | None, str]:
    if portal_trigger:
        return _clean(portal_trigger), "EXPLICIT"
    match = _TRIGGER_RE.search(window)
    if match:
        return _clean(match.group(0)), "EXPLICIT"
    if re.search(r"(?:intim|cita|publica|ciên|cien|notifica)", window, re.IGNORECASE):
        return _clean(window), "PARTIAL"
    return None, "UNSPECIFIED"


def _counting_qualifier(window: str, raw_unit: str | None, trigger_text: str | None) -> str | None:
    unit = " ".join((raw_unit or "").split()).lower()
    if any(marker in unit for marker in ("útil", "util", "úteis", "uteis")):
        return "BUSINESS_DAYS"
    if "corrido" in unit:
        return "CONTINUOUS_DAYS"
    return None


def _recipient(window: str, explicit: str | None = None) -> str | None:
    if explicit:
        return _clean(explicit)
    match = _RECIPIENT_RE.search(window)
    if match:
        return _clean(match.group(1))
    match = _ROLE_RECIPIENT_RE.search(window)
    return _clean(match.group(1)) if match else None


def _action(window: str, number: int | None) -> str | None:
    value = _clean(window)
    if not value:
        return None
    # Keep the act's operative clause, avoiding a large preceding narrative.
    for marker in ("intime-se", "intime", "cite-se", "faculto", "determino", "determina", "providencie", "apresente", "responda", "vista ao", "vista à", "vista a"):
        idx = value.lower().rfind(marker)
        if idx >= 0:
            value = value[idx:]
            break
    if number is not None:
        value = re.sub(rf"(?:no\s+prazo\s+de|prazo\s+(?:comum\s+)?de|dentro\s+de)\s*{_NUMBER}\s*{_UNIT}", "", value, flags=re.IGNORECASE)
    value = _clean(value.strip(" -:;,."))
    return value[:600] if value else None


def _candidate_id(process_id: str, movement_id: str, candidate: dict[str, Any]) -> str:
    basis = "\x00".join(str(candidate.get(key) or "") for key in ("movement_id", "source_excerpt", "action_text", "term_value", "term_unit", "trigger_text"))
    seed = f"{process_id}\x00{movement_id}\x00{basis}"
    return f"di_{uuid.uuid5(ID_NAMESPACE, seed).hex}"


def migrate_connection(db: sqlite3.Connection) -> dict[str, Any]:
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    db.executescript(SCHEMA)
    columns = {str(row[1]) for row in db.execute("PRAGMA table_info(deadline_instructions)")}
    if "source_event_id" not in columns:
        # SQLite has no DROP NOT NULL; rebuild transactionally while preserving
        # all V1 columns and rows. movement_id remains populated for old rows.
        from core.documentos.process_event_store_v1 import materialize_process_events
        old_processes = [str(row[0]) for row in db.execute("SELECT DISTINCT process_id FROM deadline_instructions")]
        for old_process_id in old_processes:
            materialize_process_events(db, old_process_id)
        db.execute("PRAGMA foreign_keys=OFF")
        db.execute("PRAGMA legacy_alter_table=ON")
        db.execute("ALTER TABLE deadline_instructions RENAME TO deadline_instructions_v1_backup")
        db.executescript("""
        CREATE TABLE deadline_instructions(
          instruction_id TEXT PRIMARY KEY, process_id TEXT NOT NULL, movement_id TEXT,
          source_event_id TEXT NOT NULL, source_entity TEXT NOT NULL, source_id TEXT NOT NULL,
          action_text TEXT, recipient_text TEXT, term_value INTEGER, term_unit TEXT NOT NULL,
          counting_qualifier TEXT, trigger_text TEXT, trigger_status TEXT NOT NULL,
          source_excerpt TEXT NOT NULL, source_refs_json TEXT NOT NULL, source_hash TEXT NOT NULL,
          extraction_method TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          UNIQUE(process_id,instruction_id),
          FOREIGN KEY(movement_id) REFERENCES movements(movement_id) ON DELETE CASCADE,
          FOREIGN KEY(source_event_id) REFERENCES process_events(event_id)
        );
        INSERT INTO deadline_instructions SELECT instruction_id,process_id,movement_id,
          (SELECT event_id FROM process_events e WHERE e.process_id=old.process_id AND e.source_entity='MOVEMENT' AND e.source_id=old.movement_id),
          'MOVEMENT',movement_id,action_text,recipient_text,term_value,term_unit,counting_qualifier,trigger_text,
          trigger_status,source_excerpt,source_refs_json,source_hash,extraction_method,status,created_at,updated_at
          FROM deadline_instructions_v1_backup old
          WHERE EXISTS(SELECT 1 FROM process_events e WHERE e.process_id=old.process_id AND e.source_entity='MOVEMENT' AND e.source_id=old.movement_id);
        DROP TABLE deadline_instructions_v1_backup;
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_deadline_instructions_process ON deadline_instructions(process_id,status,trigger_status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_deadline_instructions_movement ON deadline_instructions(movement_id,instruction_id)")
        db.execute("PRAGMA legacy_alter_table=OFF")
        db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE INDEX IF NOT EXISTS idx_deadline_instructions_event ON deadline_instructions(source_event_id)")
    applied = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION,)).fetchone()
    db.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)", (MIGRATION_VERSION, _now()))
    db.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)", (MIGRATION_V2, _now()))
    db.commit()
    return {"migration_version": MIGRATION_VERSION, "already_applied": bool(applied)}


def create_from_event(db: sqlite3.Connection, *, process_id: str, source_event_id: str,
                      source_entity: str, source_id: str, source_excerpt: str,
                      source_refs: Any, source_hash: str, action_text: str | None = None,
                      recipient_text: str | None = None, term_value: int | None = None,
                      term_unit: str = "UNSPECIFIED", counting_qualifier: str | None = None,
                      trigger_text: str | None = None, trigger_status: str = "UNSPECIFIED",
                      status: str = "AMBIGUOUS", extraction_method: str = EXTRACTION_METHOD) -> str:
    """Persist an instruction only when its generic event anchor is valid."""
    event = db.execute("SELECT process_id,source_entity,source_id FROM process_events WHERE event_id=?", (source_event_id,)).fetchone()
    if not event or event["process_id"] != process_id or event["source_entity"] != source_entity or event["source_id"] != source_id:
        raise ValueError("source_event_id não corresponde à origem no processo")
    if source_entity not in {"MOVEMENT", "PUBLICATION"}:
        raise ValueError("source_entity inválida para instrução")
    movement_id = source_id if source_entity == "MOVEMENT" else None
    seed = "\x00".join((process_id, source_event_id, source_excerpt, action_text or "", str(term_value), term_unit))
    instruction_id = "di_" + uuid.uuid5(ID_NAMESPACE, seed).hex
    now = _now()
    db.execute("""INSERT INTO deadline_instructions(
      instruction_id,process_id,movement_id,source_event_id,source_entity,source_id,action_text,recipient_text,
      term_value,term_unit,counting_qualifier,trigger_text,trigger_status,source_excerpt,source_refs_json,
      source_hash,extraction_method,status,created_at,updated_at)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(instruction_id) DO NOTHING""",
      (instruction_id,process_id,movement_id,source_event_id,source_entity,source_id,action_text,recipient_text,
       term_value,term_unit,counting_qualifier,trigger_text,trigger_status,source_excerpt,_json(source_refs),
       source_hash,extraction_method,status,now,now))
    return instruction_id


def _source_for_movement(db: sqlite3.Connection, movement_id: str) -> tuple[str, str, list[dict[str, Any]]] | None:
    row = db.execute("SELECT process_id FROM movements WHERE movement_id=?", (movement_id,)).fetchone()
    if not row:
        return None
    pages = source_pages(db, movement_id)
    text, source_hash = source_text_and_hash(db, movement_id)
    return row["process_id"], text, pages


def _candidate_from_match(process_id: str, movement_id: str, text: str, pages: list[dict[str, Any]], match: re.Match[str], *, portal: bool = False, non_determinative: bool = False) -> dict[str, Any] | None:
    groups = match.groupdict()
    number = _number(groups.get("number"))
    raw_unit = groups.get("unit")
    if groups.get("date"):
        term_value = None
        term_unit = "DATE_CERTAIN"
    else:
        term_value = number
        term_unit = _unit(raw_unit or "")
    window = _clean(match.group(0)) or ""
    explicit_recipient = groups.get("recipient")
    trigger_text, trigger_status = _trigger(window, window, portal_trigger=groups.get("trigger") if portal else None)
    action = _action(" ".join(value for value in (groups.get("prefix"), groups.get("action"), groups.get("suffix"), window) if value), number)
    recipient = _recipient(window, explicit_recipient)
    if not action and not recipient and term_value is None:
        return None
    excerpt = _excerpt(text, match.start(), match.end())
    status = "EXPLICIT" if action and (term_value is not None or term_unit == "DATE_CERTAIN") else "AMBIGUOUS"
    if non_determinative and not portal:
        status = "AMBIGUOUS"
    if trigger_status == "UNSPECIFIED" and status == "EXPLICIT":
        status = "AMBIGUOUS" if not action else status
    return {
        "process_id": process_id,
        "movement_id": movement_id,
        "action_text": action,
        "recipient_text": recipient,
        "term_value": term_value,
        "term_unit": term_unit,
        "counting_qualifier": _counting_qualifier(window, raw_unit, trigger_text),
        "trigger_text": trigger_text,
        "trigger_status": trigger_status,
        "source_excerpt": excerpt,
        "source_refs_json": _json({"pages": [{"document_id": p["document_id"], "page_number": p["page_number"]} for p in pages], "extraction_method": EXTRACTION_METHOD}),
        "source_hash": None,
        "extraction_method": EXTRACTION_METHOD,
        "status": status,
    }


def extract_for_movement(db: sqlite3.Connection, movement_id: str) -> list[dict[str, Any]]:
    source = _source_for_movement(db, movement_id)
    if source is None:
        return []
    process_id, text, pages = source
    movement_row = db.execute("SELECT movement_type FROM movements WHERE movement_id=?", (movement_id,)).fetchone()
    movement_type = str(movement_row["movement_type"] or "") if movement_row else ""
    non_determinative = bool(re.search(r"peti|contesta|manifesta|parecer", movement_type, re.IGNORECASE))
    _, source_hash = source_text_and_hash(db, movement_id)
    candidates: list[dict[str, Any]] = []
    occupied: list[tuple[int, int]] = []

    for match in _PORTAL_RE.finditer(text):
        item = _candidate_from_match(process_id, movement_id, text, pages, match, portal=True)
        if item:
            item["source_hash"] = source_hash
            candidates.append(item); occupied.append((match.start(), match.end()))

    for pattern in (_ORDER_RE, _UNTIL_RE, _UNSPECIFIED_RE):
        for match in pattern.finditer(text):
            if any(start <= match.start() < end for start, end in occupied):
                continue
            item = _candidate_from_match(process_id, movement_id, text, pages, match, non_determinative=non_determinative)
            if not item:
                continue
            item["source_hash"] = source_hash
            # Ignore legal quotations and argumentative references unless the
            # same window contains an operative/determination verb.
            window = (item.get("source_excerpt") or "").lower()
            operative = re.search(r"(?:intim|cite-se|faculto|determ|providenc|apresent|responda|vista ao|aguarde-se|decorrido)", window)
            if pattern is not _UNSPECIFIED_RE and not operative:
                continue
            candidates.append(item); occupied.append((match.start(), match.end()))

    # The legacy regex layer remains authoritative for explicit terms. The
    # semantic specialist adds operative candidates that have no numeric term
    # without changing the canonical source text or PDF pipeline.
    from core.documentos.deadline_specialist_v1 import analyze_deadline_text, deadline_candidate_windows, is_party_deadline_candidate
    existing_excerpts = {_norm(item.get("source_excerpt")) for item in candidates}
    for window in deadline_candidate_windows(text):
        normalized_window = _norm(window)
        if any(normalized_window in excerpt or excerpt in normalized_window for excerpt in existing_excerpts if excerpt):
            continue
        output = analyze_deadline_text(window)
        if not output.operative_instruction or not is_party_deadline_candidate(window):
            continue
        candidates.append({
            "process_id": process_id,
            "movement_id": movement_id,
            "action_text": output.action_text,
            "recipient_text": output.recipient_text,
            "term_value": output.explicit_term_value,
            "term_unit": output.explicit_term_unit,
            "counting_qualifier": "BUSINESS_DAYS" if output.explicit_term_unit == "BUSINESS_DAYS" else None,
            "trigger_text": output.trigger_text,
            "trigger_status": "UNSPECIFIED",
            "source_excerpt": window,
            "source_refs_json": _json({"pages": [{"document_id": p["document_id"], "page_number": p["page_number"]} for p in pages], "extraction_method": "DEADLINE_SPECIALIST_V1"}),
            "source_hash": source_hash,
            "extraction_method": "DEADLINE_SPECIALIST_V1",
            "status": "INFERRED" if output.explicit_term_value is None and output.explicit_term_unit != "DATE_CERTAIN" else "EXPLICIT",
        })

    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for item in candidates:
        key = (item["action_text"], item["recipient_text"], item["term_value"], item["term_unit"], item["trigger_text"], item["source_excerpt"])
        unique.setdefault(key, item)
    for item in unique.values():
        item["instruction_id"] = _candidate_id(process_id, movement_id, item)
    return list(unique.values())


def materialize_process(db: sqlite3.Connection, process_id: str) -> dict[str, Any]:
    migrate_connection(db)
    from core.documentos.process_event_store_v1 import materialize_process_events
    materialize_process_events(db, process_id)
    movement_rows = db.execute("SELECT movement_id FROM movements WHERE process_id=? ORDER BY sequence", (process_id,)).fetchall()
    desired = [item for row in movement_rows for item in extract_for_movement(db, row["movement_id"])]
    now = _now()
    existing = {row["instruction_id"]: row for row in db.execute("SELECT * FROM deadline_instructions WHERE process_id=?", (process_id,)).fetchall()}
    for item in desired:
        old = existing.get(item["instruction_id"])
        values = (
            item["instruction_id"], item["process_id"], item["movement_id"],
            db.execute("SELECT event_id FROM process_events WHERE process_id=? AND source_entity='MOVEMENT' AND source_id=?", (process_id,item["movement_id"])).fetchone()[0],
            "MOVEMENT", item["movement_id"], item["action_text"], item["recipient_text"], item["term_value"], item["term_unit"], item["counting_qualifier"], item["trigger_text"], item["trigger_status"], item["source_excerpt"], item["source_refs_json"], item["source_hash"], item["extraction_method"], item["status"], old["created_at"] if old else now, now,
        )
        db.execute("""INSERT INTO deadline_instructions(
          instruction_id, process_id, movement_id, source_event_id, source_entity, source_id, action_text, recipient_text, term_value, term_unit,
          counting_qualifier, trigger_text, trigger_status, source_excerpt, source_refs_json, source_hash,
          extraction_method, status, created_at, updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(instruction_id) DO UPDATE SET
          process_id=excluded.process_id, movement_id=excluded.movement_id, action_text=excluded.action_text,
          recipient_text=excluded.recipient_text, term_value=excluded.term_value, term_unit=excluded.term_unit,
          counting_qualifier=excluded.counting_qualifier, trigger_text=excluded.trigger_text,
          trigger_status=excluded.trigger_status, source_excerpt=excluded.source_excerpt,
          source_refs_json=excluded.source_refs_json, source_hash=excluded.source_hash,
          extraction_method=excluded.extraction_method, status=excluded.status, updated_at=excluded.updated_at""", values)
    desired_ids = {item["instruction_id"] for item in desired}
    # This materializer owns only Movement-derived instructions. Generic
    # instructions (notably DJEN PUBLICATION) are managed by their own source
    # pipeline and must survive a Movement refresh.
    stale = [
        instruction_id
        for instruction_id, row in existing.items()
        if row["source_entity"] == "MOVEMENT" and instruction_id not in desired_ids
    ]
    if stale:
        db.executemany("DELETE FROM deadline_instructions WHERE instruction_id=?", [(value,) for value in stale])
    db.commit()
    return {"process_id": process_id, "materialized": len(desired), "deleted": len(stale)}


def materialize_publication_instructions(db: sqlite3.Connection, process_id: str) -> dict[str, Any]:
    """Materialize semantic instructions anchored directly in DJEN publications."""
    migrate_connection(db)
    from core.documentos.deadline_specialist_v1 import analyze_deadline_text, deadline_candidate_windows, is_party_deadline_candidate

    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='publications'").fetchone():
        return {"process_id": process_id, "materialized": 0, "deleted": 0}

    desired: set[str] = set()
    rows = db.execute(
        """SELECT p.publication_id,p.full_text,p.source_url,p.payload_hash,p.communication_id,e.event_id
             FROM publications p JOIN process_events e
               ON e.process_id=p.process_id AND e.source_entity='PUBLICATION' AND e.source_id=p.publication_id
            WHERE p.process_id=? AND coalesce(p.active,1)<>0""",
        (process_id,),
    ).fetchall()
    for row in rows:
        for window in deadline_candidate_windows(row["full_text"] or ""):
            output = analyze_deadline_text(window)
            if not output.operative_instruction or not is_party_deadline_candidate(window):
                continue
            instruction_id = create_from_event(
                db, process_id=process_id, source_event_id=row["event_id"],
                source_entity="PUBLICATION", source_id=row["publication_id"],
                source_excerpt=window,
                source_refs={"source_url": row["source_url"], "communication_id": row["communication_id"]},
                source_hash=row["payload_hash"] or hashlib.sha256((row["full_text"] or "").encode("utf-8")).hexdigest(),
                action_text=output.action_text, recipient_text=output.recipient_text,
                term_value=output.explicit_term_value, term_unit=output.explicit_term_unit,
                counting_qualifier="BUSINESS_DAYS" if output.explicit_term_unit == "BUSINESS_DAYS" else None,
                trigger_text=output.trigger_text,
                trigger_status="EXPLICIT" if output.trigger_text else "UNSPECIFIED",
                status="INFERRED" if output.explicit_term_value is None and output.explicit_term_unit != "DATE_CERTAIN" else "EXPLICIT",
                extraction_method="DEADLINE_SPECIALIST_V1",
            )
            desired.add(instruction_id)
    existing = db.execute(
        "SELECT instruction_id FROM deadline_instructions WHERE process_id=? AND source_entity='PUBLICATION'",
        (process_id,),
    ).fetchall()
    stale = [row[0] for row in existing if row[0] not in desired]
    if stale:
        db.executemany("DELETE FROM deadline_instructions WHERE instruction_id=?", [(item,) for item in stale])
    db.commit()
    return {"process_id": process_id, "materialized": len(desired), "deleted": len(stale)}


def materialize_all(db: sqlite3.Connection) -> dict[str, Any]:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='processes'").fetchone():
        return {"processes": 0, "instructions": 0}
    results = [materialize_process(db, row[0]) for row in db.execute("SELECT process_id FROM processes ORDER BY process_id")]
    return {"processes": len(results), "instructions": sum(item["materialized"] for item in results)}


def list_instructions(db: sqlite3.Connection, process_id: str, *, status: str | None = None, trigger_status: str | None = None) -> list[dict[str, Any]]:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='deadline_instructions'").fetchone():
        return []
    query = "SELECT * FROM deadline_instructions WHERE process_id=?"; params: list[Any] = [process_id]
    if status:
        query += " AND status=?"; params.append(status.upper())
    if trigger_status:
        query += " AND trigger_status=?"; params.append(trigger_status.upper())
    query += " ORDER BY movement_id, instruction_id"
    result = []
    for row in db.execute(query, params).fetchall():
        value = dict(row)
        value["source_refs"] = json.loads(value.pop("source_refs_json"))
        result.append(value)
    return result
