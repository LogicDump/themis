"""Consolidação conservadora de DeadlineInstructions em V1.

Uma DeadlineObligation representa uma determinação temporal única originada
por uma ordem apta a determinar a providência. Comunicações, publicações e
reproduções só entram como suporte quando há vínculo textual determinístico;
pedidos das partes nunca originam obrigações.
"""
from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import Any

from core.documentos.deadline_instruction_store_v1 import list_instructions

MIGRATION_VERSION = "deadline-obligation-store-v1"
MIGRATION_V2 = "deadline-obligation-store-v2-rule-resolution"
ID_NAMESPACE = uuid.UUID("2e6bdc8c-01c9-43f4-9dbd-319f07e2b3c1")

SCHEMA = """
CREATE TABLE IF NOT EXISTS deadline_obligations(
  obligation_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  originating_instruction_id TEXT NOT NULL,
  supporting_instruction_ids_json TEXT NOT NULL,
  origin_role TEXT NOT NULL,
  action_text TEXT,
  recipient_text TEXT,
  term_value INTEGER,
  term_unit TEXT NOT NULL,
  counting_qualifier TEXT,
  trigger_text TEXT,
  trigger_status TEXT NOT NULL,
  origin_movement_id TEXT NOT NULL,
  source_refs_json TEXT NOT NULL,
  source_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(process_id, obligation_id),
  FOREIGN KEY(originating_instruction_id) REFERENCES deadline_instructions(instruction_id) ON DELETE CASCADE,
  FOREIGN KEY(origin_movement_id) REFERENCES movements(movement_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_deadline_obligations_process
  ON deadline_obligations(process_id, status);
CREATE INDEX IF NOT EXISTS idx_deadline_obligations_recipient
  ON deadline_obligations(process_id, recipient_text);
"""

_SPACE_RE = re.compile(r"\s+")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_recipient_participants(db: sqlite3.Connection, process_id: str, participant_ids: list[str]) -> list[str]:
    """Reject IDs that are not participants in this exact process package."""
    normalized = sorted({str(value) for value in participant_ids if str(value).strip()})
    for participant_id in normalized:
        if not db.execute("SELECT 1 FROM process_participants WHERE process_id=? AND participant_id=?", (process_id, participant_id)).fetchone():
            raise ValueError("recipient_participant_id não pertence ao processo")
    return normalized


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return _SPACE_RE.sub(" ", text).strip().casefold()


def _source_role(movement_type: str | None, title: str | None, excerpt: str | None) -> str:
    value = _norm(movement_type) + " " + _norm(title)
    text = _norm(excerpt)
    if "peticao" in value or "contestacao" in value or "manifestacao" in value or "parecer" in value:
        return "PARTY_REQUEST"
    if "decisao" in value or "despacho" in value:
        return "ORIGINATING_ORDER"
    if "certidao de publicacao" in value:
        return "PUBLICATION"
    if "movimento processual" in value:
        return "REPRODUCTION"
    if "certidao" in value:
        if any(marker in text for marker in ("data da intimacao", "data da intimacao", "intimado:", "teor do ato:")):
            return "COMMUNICATION"
        return "CERTIFICATION"
    return "UNKNOWN"


def _anchor(value: str | None) -> str:
    text = _norm(value)
    if len(text) <= 280:
        return text
    term = re.search(r"\b(?:prazo|dias|horas|meses)\b", text)
    if not term:
        return text[:280]
    start = max(0, term.start() - 120)
    return text[start : start + 280]


def _term_anchors(instruction: dict[str, Any]) -> list[str]:
    text = _norm(instruction.get("source_excerpt"))
    value = instruction.get("term_value")
    if value is None:
        return []
    pattern = re.compile(rf"\b0*{int(value)}\b.{{0,80}}\b(?:dias|horas|meses)\b")
    anchors = []
    for match in pattern.finditer(text):
        # Keep an exact window beginning at the normalized term. Different
        # provider projections may crop or vary the preceding sentence;
        # the term and its operative continuation remain the identity proof.
        anchors.append(text[max(0, match.start() - 20) : match.end()])
    return anchors


def _supports(origin: dict[str, Any], candidate: dict[str, Any], *, origin_sequence: int, candidate_sequence: int) -> bool:
    if candidate_sequence <= origin_sequence:
        return False
    if origin.get("term_value") != candidate.get("term_value") or origin.get("term_unit") != candidate.get("term_unit"):
        return False
    anchor = _anchor(origin.get("action_text"))
    excerpt = _norm(candidate.get("source_excerpt"))
    if not anchor:
        return False
    if anchor in excerpt:
        return True
    # The instruction extractor removes the numeric term from action_text;
    # compare the exact remaining phrase while ignoring only the unit word.
    strip_unit = lambda value: _norm(re.sub(r"\b(?:dias|horas|meses)\b", "", value))
    if strip_unit(anchor) in strip_unit(excerpt):
        return True
    return any(term_anchor in excerpt for term_anchor in _term_anchors(origin))


def migrate_connection(db: sqlite3.Connection) -> dict[str, Any]:
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    db.executescript(SCHEMA)
    columns = {str(row[1]) for row in db.execute("PRAGMA table_info(deadline_obligations)")}
    additions = {
        "antecedent_source_event_id": "TEXT", "recipient_role": "TEXT",
        "recipient_participant_ids_json": "TEXT NOT NULL DEFAULT '[]'",
        "recipient_resolution_method": "TEXT", "candidate_rule_ids_json": "TEXT NOT NULL DEFAULT '[]'",
        "model_preferred_rule_id": "TEXT", "resolved_rule_id": "TEXT",
        "review_required": "INTEGER NOT NULL DEFAULT 1", "provenance_json": "TEXT NOT NULL DEFAULT '{}'",
    }
    for name, declaration in additions.items():
        if name not in columns:
            db.execute(f"ALTER TABLE deadline_obligations ADD COLUMN {name} {declaration}")
    db.execute("CREATE INDEX IF NOT EXISTS idx_deadline_obligations_antecedent_event ON deadline_obligations(antecedent_source_event_id)")
    applied = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION,)).fetchone()
    db.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)", (MIGRATION_VERSION, _now()))
    db.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)", (MIGRATION_V2, _now()))
    db.commit()
    return {"migration_version": MIGRATION_VERSION, "already_applied": bool(applied)}


def _instructions_with_context(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    rows = list_instructions(db, process_id)
    movement_rows = db.execute(
        "SELECT movement_id, sequence, movement_type, title FROM movements WHERE process_id=?",
        (process_id,),
    ).fetchall()
    movements = {row["movement_id"]: dict(row) for row in movement_rows}
    for row in rows:
        movement = movements.get(row["movement_id"], {})
        row["sequence"] = movement.get("sequence", 0)
        row["movement_type"] = movement.get("movement_type")
        row["title"] = movement.get("title")
        row["source_role"] = _source_role(row["movement_type"], row["title"], row.get("source_excerpt"))
    return rows


def _obligation_id(process_id: str, origin: dict[str, Any]) -> str:
    basis = "\x00".join(
        str(origin.get(key) or "")
        for key in ("originating_instruction_id", "action_text", "recipient_text", "term_value", "term_unit", "counting_qualifier", "trigger_text")
    )
    seed = process_id + "\x00" + basis
    return f"do_{uuid.uuid5(ID_NAMESPACE, seed).hex}"


def _build_obligation(process_id: str, origin: dict[str, Any], supporting: list[dict[str, Any]]) -> dict[str, Any]:
    status = "ACTIVE" if origin["status"] == "EXPLICIT" else "AMBIGUOUS"
    source_refs = {"origin": origin.get("source_refs"), "supporting": [item.get("source_refs") for item in supporting]}
    return {
        "obligation_id": _obligation_id(process_id, origin),
        "process_id": process_id,
        "originating_instruction_id": origin["instruction_id"],
        "supporting_instruction_ids_json": _json([item["instruction_id"] for item in supporting]),
        "origin_role": origin["source_role"],
        "action_text": origin.get("action_text"),
        "recipient_text": origin.get("recipient_text"),
        "term_value": origin.get("term_value"),
        "term_unit": origin["term_unit"],
        "counting_qualifier": origin.get("counting_qualifier"),
        "trigger_text": origin.get("trigger_text"),
        "trigger_status": origin["trigger_status"],
        "origin_movement_id": origin["movement_id"],
        "antecedent_source_event_id": origin.get("source_event_id"),
        "recipient_role": None,
        "recipient_participant_ids_json": "[]",
        "recipient_resolution_method": None,
        "candidate_rule_ids_json": "[]",
        "model_preferred_rule_id": None,
        "resolved_rule_id": None,
        "review_required": 1,
        "provenance_json": _json({"source_event_id": origin.get("source_event_id"), "source_entity": origin.get("source_entity"), "source_id": origin.get("source_id"), "source_hash": origin.get("source_hash"), "source_refs": source_refs}),
        "source_refs_json": _json(source_refs),
        "source_hash": origin["source_hash"],
        "status": status,
    }


def materialize_process(db: sqlite3.Connection, process_id: str) -> dict[str, Any]:
    migrate_connection(db)
    instructions = _instructions_with_context(db, process_id)
    origins = [item for item in instructions if item["source_role"] == "ORIGINATING_ORDER"]
    supports = [item for item in instructions if item["source_role"] in {"COMMUNICATION", "PUBLICATION", "CERTIFICATION", "REPRODUCTION"}]
    desired: list[dict[str, Any]] = []
    support_map: dict[str, list[dict[str, Any]]] = {item["instruction_id"]: [] for item in origins}
    for candidate in supports:
        matches = [origin for origin in origins if _supports(origin, candidate, origin_sequence=origin["sequence"], candidate_sequence=candidate["sequence"])]
        if len(matches) == 1:
            support_map[matches[0]["instruction_id"]].append(candidate)
    for origin in origins:
        desired.append(_build_obligation(process_id, origin, support_map[origin["instruction_id"]]))

    now = _now()
    existing = {row["obligation_id"]: row for row in db.execute("SELECT * FROM deadline_obligations WHERE process_id=?", (process_id,)).fetchall()}
    for item in desired:
        old = existing.get(item["obligation_id"])
        values = (
            item["obligation_id"], item["process_id"], item["originating_instruction_id"], item["supporting_instruction_ids_json"], item["origin_role"],
            item["action_text"], item["recipient_text"], item["term_value"], item["term_unit"], item["counting_qualifier"], item["trigger_text"], item["trigger_status"],
            item["origin_movement_id"], item["source_refs_json"], item["source_hash"], item["status"], old["created_at"] if old else now, now,
        )
        db.execute(
            """INSERT INTO deadline_obligations(
              obligation_id, process_id, originating_instruction_id, supporting_instruction_ids_json, origin_role,
              action_text, recipient_text, term_value, term_unit, counting_qualifier, trigger_text, trigger_status,
              origin_movement_id, source_refs_json, source_hash, status, created_at, updated_at,
              antecedent_source_event_id, recipient_role, recipient_participant_ids_json, recipient_resolution_method,
              candidate_rule_ids_json, model_preferred_rule_id, resolved_rule_id, review_required, provenance_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(obligation_id) DO UPDATE SET
              process_id=excluded.process_id, originating_instruction_id=excluded.originating_instruction_id,
              supporting_instruction_ids_json=excluded.supporting_instruction_ids_json, origin_role=excluded.origin_role,
              action_text=excluded.action_text, recipient_text=excluded.recipient_text, term_value=excluded.term_value,
              term_unit=excluded.term_unit, counting_qualifier=excluded.counting_qualifier, trigger_text=excluded.trigger_text,
              trigger_status=excluded.trigger_status, origin_movement_id=excluded.origin_movement_id,
              source_refs_json=excluded.source_refs_json, source_hash=excluded.source_hash, status=excluded.status,
              updated_at=excluded.updated_at, antecedent_source_event_id=excluded.antecedent_source_event_id,
              provenance_json=excluded.provenance_json""",
            values + (item["antecedent_source_event_id"], item["recipient_role"], item["recipient_participant_ids_json"], item["recipient_resolution_method"], item["candidate_rule_ids_json"], item["model_preferred_rule_id"], item["resolved_rule_id"], item["review_required"], item["provenance_json"]),
        )
    desired_ids = {item["obligation_id"] for item in desired}
    stale = [obligation_id for obligation_id in existing if obligation_id not in desired_ids]
    if stale:
        db.executemany("DELETE FROM deadline_obligations WHERE obligation_id=?", [(value,) for value in stale])
    db.commit()
    return {
        "process_id": process_id,
        "instructions": len(instructions),
        "obligations": len(desired),
        "support_links": sum(len(value) for value in support_map.values()),
        "party_requests_excluded": sum(item["source_role"] == "PARTY_REQUEST" for item in instructions),
        "deleted": len(stale),
    }


def materialize_all(db: sqlite3.Connection) -> dict[str, Any]:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='processes'").fetchone():
        return {"processes": 0, "obligations": 0}
    results = [materialize_process(db, row[0]) for row in db.execute("SELECT process_id FROM processes ORDER BY process_id")]
    return {"processes": len(results), "obligations": sum(item["obligations"] for item in results)}


def list_obligations(db: sqlite3.Connection, process_id: str, *, status: str | None = None, recipient: str | None = None) -> list[dict[str, Any]]:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='deadline_obligations'").fetchone():
        return []
    query = "SELECT * FROM deadline_obligations WHERE process_id=?"
    params: list[Any] = [process_id]
    if status:
        query += " AND status=?"; params.append(status.upper())
    if recipient:
        query += " AND lower(recipient_text) LIKE lower(?)"; params.append(f"%{recipient}%")
    query += " ORDER BY obligation_id"
    result = []
    for row in db.execute(query, params).fetchall():
        value = dict(row)
        value["supporting_instruction_ids"] = json.loads(value.pop("supporting_instruction_ids_json"))
        value["source_refs"] = json.loads(value.pop("source_refs_json"))
        value["recipient_participant_ids"] = json.loads(value.pop("recipient_participant_ids_json", "[]") or "[]")
        value["candidate_rule_ids"] = json.loads(value.pop("candidate_rule_ids_json", "[]") or "[]")
        value["provenance"] = json.loads(value.pop("provenance_json", "{}") or "{}")
        result.append(value)
    return result
