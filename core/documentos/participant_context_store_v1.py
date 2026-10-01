"""V1 read/write model for process participants and user perspective.

The process tables are documentary and neutral.  Professional profiles and
user contexts are local product overlays and never change the process facts.
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

MIGRATION_VERSION = "participant-context-store-v1"
ID_NAMESPACE = uuid.UUID("a2f5c3da-60d8-5f44-9ad8-5d9edc17c0c4")
BASE_ROLES = {"CLAIMANT", "RESPONDENT", "REPRESENTATIVE", "PUBLIC_PROSECUTOR", "EXPERT", "THIRD_PARTY", "OTHER"}
REPRESENTATION_KINDS = {"LAWYER", "LEGAL_GUARDIAN", "PUBLIC_PROSECUTOR", "OTHER"}
PROFILE_TYPES = {"LAWYER", "PARTY", "OTHER"}
RELATIONS = {"ACTING", "PARTY", "FOLLOWING"}
CONTEXT_SOURCES = {"USER_CONFIRMED", "DOCUMENTARY_MATCH"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS process_participants(
  participant_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  display_name TEXT NOT NULL,
  base_role TEXT NOT NULL CHECK(base_role IN ('CLAIMANT','RESPONDENT','REPRESENTATIVE','PUBLIC_PROSECUTOR','EXPERT','THIRD_PARTY','OTHER')),
  source_refs_json TEXT NOT NULL,
  provenance_json TEXT NOT NULL,
  status TEXT NOT NULL,
  confidence TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(process_id, entity_id, base_role),
  FOREIGN KEY(process_id) REFERENCES processes(process_id),
  FOREIGN KEY(entity_id) REFERENCES legal_entities(entity_id)
);
CREATE INDEX IF NOT EXISTS idx_process_participants_process ON process_participants(process_id);

CREATE TABLE IF NOT EXISTS representations(
  representation_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  representative_participant_id TEXT NOT NULL,
  represented_participant_id TEXT NOT NULL,
  representation_kind TEXT NOT NULL CHECK(representation_kind IN ('LAWYER','LEGAL_GUARDIAN','PUBLIC_PROSECUTOR','OTHER')),
  oab_number TEXT,
  oab_uf TEXT,
  source_refs_json TEXT NOT NULL,
  source_excerpt TEXT NOT NULL,
  provenance_json TEXT NOT NULL,
  status TEXT NOT NULL,
  confidence TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(process_id, representative_participant_id, represented_participant_id, representation_kind, oab_number, oab_uf),
  FOREIGN KEY(process_id) REFERENCES processes(process_id),
  FOREIGN KEY(representative_participant_id) REFERENCES process_participants(participant_id),
  FOREIGN KEY(represented_participant_id) REFERENCES process_participants(participant_id)
);
CREATE INDEX IF NOT EXISTS idx_representations_process ON representations(process_id);
CREATE INDEX IF NOT EXISTS idx_representations_represented ON representations(represented_participant_id);

CREATE TABLE IF NOT EXISTS professional_profiles(
  profile_id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  profile_type TEXT NOT NULL CHECK(profile_type IN ('LAWYER','PARTY','OTHER')),
  oab_number TEXT,
  oab_uf TEXT,
  future_identity_ref TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_process_contexts(
  context_id TEXT PRIMARY KEY,
  process_id TEXT NOT NULL,
  profile_id TEXT NOT NULL,
  relation TEXT NOT NULL CHECK(relation IN ('ACTING','PARTY','FOLLOWING')),
  participant_id TEXT,
  represented_participant_ids_json TEXT NOT NULL,
  source TEXT NOT NULL CHECK(source IN ('USER_CONFIRMED','DOCUMENTARY_MATCH')),
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(process_id, profile_id),
  FOREIGN KEY(process_id) REFERENCES processes(process_id),
  FOREIGN KEY(profile_id) REFERENCES professional_profiles(profile_id),
  FOREIGN KEY(participant_id) REFERENCES process_participants(participant_id)
);
CREATE INDEX IF NOT EXISTS idx_user_process_context_process ON user_process_contexts(process_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _norm_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join(re.sub(r"[^A-Za-z0-9\s]", " ", normalized.encode("ascii", "ignore").decode("ascii")).upper().split())


def _stable(prefix: str, *values: Any) -> str:
    raw = "|".join(str(value or "") for value in values)
    return f"{prefix}_{uuid.uuid5(ID_NAMESPACE, raw).hex}"


def _role(raw: str | None) -> str:
    value = _norm_name(raw or "")
    if value in {"REQTE", "REQUERENTE", "AUTOR", "AUTORA", "EXEQTE", "EXEQUENTE", "CLAIMANT"}:
        return "CLAIMANT"
    if value in {"REQDO", "REQDA", "REQUERIDO", "REQUERIDA", "REU", "RE", "EXECTDO", "EXECUTADO", "EXECUTADA", "RESPONDENT"}:
        return "RESPONDENT"
    if "PROMOTOR" in value or "MINISTERIO PUBLICO" in value or value in {"MP", "PUBLIC PROSECUTOR"}:
        return "PUBLIC_PROSECUTOR"
    if "PERITO" in value or value == "EXPERT":
        return "EXPERT"
    if "TERCEIRO" in value or value == "THIRD PARTY":
        return "THIRD_PARTY"
    if "REPRESENT" in value or "ADVOG" in value or value in {"REPRELEG", "LEGAL GUARDIAN"}:
        return "REPRESENTATIVE"
    return "OTHER"


def migrate_connection(db: sqlite3.Connection) -> dict[str, Any]:
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    db.executescript(SCHEMA)
    applied = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION_VERSION,)).fetchone()
    if not applied:
        db.execute("INSERT INTO schema_migrations(version, applied_at) VALUES(?, ?)", (MIGRATION_VERSION, _now()))
    db.commit()
    return {"migration_version": MIGRATION_VERSION, "already_applied": bool(applied)}


def _participant_id(process_id: str, entity_id: str, base_role: str) -> str:
    return _stable("participant", process_id, entity_id, base_role)


def _entity_oab(db: sqlite3.Connection, entity_id: str) -> tuple[str, str] | None:
    row = db.execute("SELECT identifiers_json FROM legal_entities WHERE entity_id=?", (entity_id,)).fetchone()
    if not row:
        return None
    try:
        identifiers = json.loads(row["identifiers_json"] or "{}")
    except (TypeError, json.JSONDecodeError):
        identifiers = {}
    number = re.sub(r"\D", "", str(identifiers.get("oab_number") or identifiers.get("oab") or identifiers.get("OAB") or ""))
    uf = str(identifiers.get("oab_uf") or identifiers.get("UF") or "").upper()
    return (number, uf) if number else None


def _merge_representative_participant(db: sqlite3.Connection, winner: sqlite3.Row, loser: sqlite3.Row) -> None:
    """Merge compatible representative projections without merging legal entities globally."""
    loser_id = loser["participant_id"]
    winner_id = winner["participant_id"]
    for row in db.execute("SELECT * FROM representations WHERE representative_participant_id=? OR represented_participant_id=?", (loser_id, loser_id)).fetchall():
        is_rep = row["representative_participant_id"] == loser_id
        existing = db.execute(
            """SELECT representation_id FROM representations
               WHERE process_id=? AND representative_participant_id=? AND represented_participant_id=?
                 AND representation_kind=? AND oab_number IS ? AND oab_uf IS ?""",
            (row["process_id"], winner_id if is_rep else row["representative_participant_id"],
             row["represented_participant_id"] if is_rep else winner_id, row["representation_kind"],
             row["oab_number"], row["oab_uf"]),
        ).fetchone()
        if existing:
            db.execute("DELETE FROM representations WHERE representation_id=?", (row["representation_id"],))
        elif is_rep:
            db.execute("UPDATE representations SET representative_participant_id=? WHERE representation_id=?", (winner_id, row["representation_id"]))
        else:
            db.execute("UPDATE representations SET represented_participant_id=? WHERE representation_id=?", (winner_id, row["representation_id"]))
    db.execute("DELETE FROM process_participants WHERE participant_id=?", (loser_id,))


def _reconcile_representative_duplicates(db: sqlite3.Connection, process_id: str) -> None:
    rows = db.execute(
        """SELECT pp.*,le.normalized_name,le.identifiers_json
             FROM process_participants pp JOIN legal_entities le USING(entity_id)
            WHERE pp.process_id=? AND pp.base_role='REPRESENTATIVE'
            ORDER BY pp.participant_id""",
        (process_id,),
    ).fetchall()
    groups: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        groups.setdefault(str(row["normalized_name"] or _norm_name(row["display_name"])), []).append(row)
    for candidates in groups.values():
        if len(candidates) < 2:
            continue
        oabs = {_entity_oab(db, row["entity_id"]) for row in candidates}
        oabs.discard(None)
        if len(oabs) > 1:
            continue
        # Prefer documentary OAB evidence, then an explicit structured party
        # role (for example RepreLeg), then the stable participant id.
        def score(row: sqlite3.Row) -> tuple[int, int, str]:
            role_count = db.execute(
                "SELECT COUNT(*) FROM party_relations WHERE owner_type='PROCESS' AND owner_id=? AND entity_id=? AND role NOT IN ('ADVOGADO','Advogado')",
                (process_id, row["entity_id"]),
            ).fetchone()[0]
            source = str(row["provenance_json"] or "")
            return (1 if _entity_oab(db, row["entity_id"]) else 0, min(role_count, 1), "" if "DOCUMENTARY_EVIDENCE" in source else "z")
        winner = max(candidates, key=score)
        for loser in candidates:
            if loser["participant_id"] == winner["participant_id"]:
                continue
            # Migrate only process-scoped structured relations. The legal entity
            # itself remains intact for other processes and global references.
            old_relations = db.execute(
                "SELECT party_relation_id,role,role_raw FROM party_relations WHERE owner_type='PROCESS' AND owner_id=? AND entity_id=?",
                (process_id, loser["entity_id"]),
            ).fetchall()
            for relation in old_relations:
                new_fp = _stable("process", process_id, winner["entity_id"], relation["role"], relation["role_raw"])
                conflict = db.execute("SELECT party_relation_id FROM party_relations WHERE relation_fingerprint=?", (new_fp,)).fetchone()
                if conflict and conflict["party_relation_id"] != relation["party_relation_id"]:
                    db.execute("DELETE FROM party_relations WHERE party_relation_id=?", (relation["party_relation_id"],))
                else:
                    db.execute("UPDATE party_relations SET entity_id=?,relation_fingerprint=? WHERE party_relation_id=?", (winner["entity_id"], new_fp, relation["party_relation_id"]))
            _merge_representative_participant(db, winner, loser)


def materialize_participants(db: sqlite3.Connection, process_id: str | None = None) -> int:
    """Project only structured party_relations; never scan page text for parties."""
    where = "WHERE pr.owner_type='PROCESS'" + (" AND pr.owner_id=?" if process_id else "")
    params = (process_id,) if process_id else ()
    rows = db.execute(
        """SELECT pr.owner_id AS process_id, pr.party_relation_id, pr.entity_id, pr.role, pr.role_raw,
                  pr.status, pr.confidence, le.display_name
           FROM party_relations pr JOIN legal_entities le USING(entity_id) """ + where,
        params,
    ).fetchall()
    stamp = _now()
    for row in rows:
        base_role = _role(row["role"] or row["role_raw"])
        pid = _participant_id(row["process_id"], row["entity_id"], base_role)
        # Reconcile the pre-fix fallback role without leaving a duplicate.
        # Only remove an obsolete OTHER row when no representation/context
        # still references it; referenced rows remain untouched for safety.
        target = db.execute(
            "SELECT participant_id FROM process_participants WHERE process_id=? AND entity_id=? AND base_role=?",
            (row["process_id"], row["entity_id"], base_role),
        ).fetchone()
        legacy = db.execute(
            "SELECT participant_id FROM process_participants WHERE process_id=? AND entity_id=? AND base_role='OTHER'",
            (row["process_id"], row["entity_id"]),
        ).fetchone() if base_role != "OTHER" else None
        if legacy:
            dependencies = 0
            tables = {item[0] for item in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "representations" in tables:
                dependencies += db.execute(
                    "SELECT COUNT(*) FROM representations WHERE representative_participant_id=? OR represented_participant_id=?",
                    (legacy["participant_id"], legacy["participant_id"]),
                ).fetchone()[0]
            if "user_process_contexts" in tables:
                dependencies += db.execute(
                    "SELECT COUNT(*) FROM user_process_contexts WHERE participant_id=? OR represented_participant_ids_json LIKE ?",
                    (legacy["participant_id"], f"%{legacy['participant_id']}%"),
                ).fetchone()[0]
            if target and target["participant_id"] != legacy["participant_id"] and dependencies == 0:
                # OTHER is a compatibility fallback. Once the same legal
                # entity has a structured role, remove only that fallback;
                # participants with other explicit roles remain untouched.
                db.execute("DELETE FROM process_participants WHERE participant_id=?", (legacy["participant_id"],))
            elif not target and dependencies == 0:
                db.execute("DELETE FROM process_participants WHERE participant_id=?", (legacy["participant_id"],))
            elif not target:
                # Keep existing foreign-key references valid. The corrected
                # role is authoritative; the legacy id is retained only for
                # this compatibility transition.
                db.execute(
                    "UPDATE process_participants SET base_role=?, updated_at=? WHERE participant_id=? AND base_role IS NOT ?",
                    (base_role, stamp, legacy["participant_id"], base_role),
                )
                pid = legacy["participant_id"]
        existing_projection = db.execute(
            "SELECT source_refs_json,provenance_json FROM process_participants WHERE participant_id=?",
            (pid,),
        ).fetchone()
        source = _merge_refs(
            existing_projection["source_refs_json"] if existing_projection else None,
            [{"source": "party_relations", "party_relation_id": row["party_relation_id"]}],
        )
        provenance = {}
        if existing_projection:
            try:
                parsed = json.loads(existing_projection["provenance_json"] or "{}")
                if isinstance(parsed, dict):
                    provenance = parsed
            except (TypeError, json.JSONDecodeError):
                pass
        provenance.update({"source": "structured_party_relation", "role": row["role"], "role_raw": row["role_raw"]})
        db.execute(
            """INSERT INTO process_participants(participant_id,process_id,entity_id,display_name,base_role,source_refs_json,provenance_json,status,confidence,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(process_id,entity_id,base_role) DO UPDATE SET display_name=excluded.display_name,
             source_refs_json=excluded.source_refs_json,provenance_json=excluded.provenance_json,
             status=excluded.status,confidence=excluded.confidence,updated_at=excluded.updated_at
           WHERE process_participants.display_name IS NOT excluded.display_name
              OR process_participants.source_refs_json IS NOT excluded.source_refs_json
              OR process_participants.provenance_json IS NOT excluded.provenance_json
              OR process_participants.status IS NOT excluded.status
              OR process_participants.confidence IS NOT excluded.confidence""",
            (pid, row["process_id"], row["entity_id"], row["display_name"], base_role, _json(source), _json(provenance), row["status"], row["confidence"], stamp, stamp),
        )
    process_ids = {str(row["process_id"]) for row in rows}
    for current_process_id in process_ids:
        _reconcile_representative_duplicates(db, current_process_id)
    db.commit()
    return len(rows)


def _page_ref(row: sqlite3.Row, movement_id: str | None = None) -> dict[str, Any]:
    result = {"page_id": row["page_id"], "document_id": row["document_id"], "page_number": row["page_number"]}
    if movement_id:
        result["movement_id"] = movement_id
    return result


def _excerpt(text: str, start: int, end: int, radius: int = 120) -> str:
    return " ".join(str(text[max(0, start - radius):end + radius]).split())


_OAB_RE = re.compile(
    r"(?P<name>[A-ZÀ-Ý][A-Za-zÀ-ÿ.'-]+(?:\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ.'-]+){1,7})"
    r"\s*(?:\(\s*|[-,:]\s*)?OAB\s*(?:[/\\-]{1,3}\s*(?P<uf_prefix>[A-Z]{2})\s*)?"
    r"(?P<number>\d[\d.\s]{2,10})\s*(?:[/\\-]{1,3}\s*(?P<uf>[A-Z]{2}))?\)?",
    re.IGNORECASE,
)
_REPRESENTED_RE = re.compile(
    r"(?P<represented>[A-ZÀ-Ý][A-ZÀ-Ý ]{3,100}),\s*"
    r"(?P<context>(?:menor e incapaz,?\s*)?(?:representad[ao](?:\s+e\s+(?:defendid[ao]|defesa|assistid[ao]))?|assistid[ao])\s+por(?: sua genitora)?\s+)"
    r"(?P<representative>[A-ZÀ-Ý][A-ZÀ-Ý ]{3,100})\s*,",
    re.IGNORECASE,
)
_LAWYER_CONTEXT_RE = re.compile(r"\bpor\s+seu?s?\s+advogad(?:o|a)s?\b", re.IGNORECASE)


def _oab_value(match: re.Match[str]) -> tuple[str, str | None]:
    return re.sub(r"\D", "", match.group("number")), (match.group("uf") or match.group("uf_prefix") or "").upper() or None


def _oab_from_entity(db: sqlite3.Connection, entity_id: str) -> tuple[str | None, str | None]:
    row = db.execute("SELECT identifiers_json FROM legal_entities WHERE entity_id=?", (entity_id,)).fetchone()
    if not row:
        return None, None
    try:
        identifiers = json.loads(row["identifiers_json"] or "{}")
    except (TypeError, json.JSONDecodeError):
        identifiers = {}
    number = re.sub(r"\D", "", str(identifiers.get("oab_number") or identifiers.get("oab") or identifiers.get("OAB") or ""))
    uf = str(identifiers.get("oab_uf") or identifiers.get("UF") or "").upper() or None
    return number or None, uf


def _clean_lawyer_name(raw: str) -> str:
    """Keep the trailing person-name run, dropping OCR/header prose."""
    tokens = re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ.'-]*", raw)
    runs: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        is_name_token = token.isupper() or token[:1].isupper() or token.casefold() in {"de", "da", "do", "dos", "das", "e"}
        if is_name_token:
            current.append(token)
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    selected = runs[-1] if runs else tokens
    return " ".join(selected[-7:]).strip(" ,;:-")


def _merge_refs(old_json: str | None, refs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        old = json.loads(old_json or "[]")
    except (TypeError, json.JSONDecodeError):
        old = []
    result = old if isinstance(old, list) else []
    seen = {json.dumps(item, ensure_ascii=False, sort_keys=True) for item in result}
    for item in refs:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True)
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result


def _entity_for_documentary_lawyer(db: sqlite3.Connection, name: str, oab_number: str, oab_uf: str | None) -> str:
    normalized = _norm_name(name)
    for row in db.execute("SELECT entity_id,identifiers_json FROM legal_entities"):
        try:
            identifiers = json.loads(row["identifiers_json"] or "{}")
        except json.JSONDecodeError:
            continue
        number = re.sub(r"\D", "", str(identifiers.get("oab_number") or identifiers.get("OAB") or ""))
        uf = str(identifiers.get("oab_uf") or identifiers.get("UF") or "").upper()
        if number == oab_number and uf in {"", oab_uf or ""}:
            return row["entity_id"]
    rows = db.execute("SELECT entity_id,display_name,normalized_name,identifiers_json FROM legal_entities WHERE normalized_name=?", (normalized,)).fetchall()
    for row in rows:
        try:
            identifiers = json.loads(row["identifiers_json"] or "{}")
        except json.JSONDecodeError:
            identifiers = {}
        if not identifiers or (
            re.sub(r"\D", "", str(identifiers.get("oab_number") or identifiers.get("OAB") or "")) == oab_number
            and str(identifiers.get("oab_uf") or identifiers.get("UF") or "").upper() in {"", oab_uf or ""}
        ):
            return row["entity_id"]
    for row in db.execute("SELECT entity_id,identifiers_json FROM legal_entities"):
        try:
            identifiers = json.loads(row["identifiers_json"] or "{}")
        except json.JSONDecodeError:
            continue
        number = re.sub(r"\D", "", str(identifiers.get("oab_number") or identifiers.get("OAB") or ""))
        uf = str(identifiers.get("oab_uf") or identifiers.get("UF") or "").upper()
        if number == oab_number and uf == (oab_uf or ""):
            return row["entity_id"]
    identity = f"PERSON|OAB|{oab_number}|{oab_uf or ''}|{normalized}"
    entity_id = _stable("entity", identity)
    stamp = _now()
    try:
        db.execute(
            """INSERT INTO legal_entities(entity_id,entity_type,display_name,normalized_name,identifiers_json,identity_fingerprint,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (entity_id, "PERSON", " ".join(name.split()), normalized,
             _json({"oab_number": oab_number, "oab_uf": oab_uf}), identity, stamp, stamp),
        )
    except sqlite3.IntegrityError:
        existing = db.execute("SELECT entity_id FROM legal_entities WHERE identity_fingerprint=? OR entity_id=?", (identity, entity_id)).fetchone()
        if not existing:
            raise
    row = db.execute("SELECT entity_id FROM legal_entities WHERE identity_fingerprint=?", (identity,)).fetchone()
    return row["entity_id"]


def _documentary_participant(db: sqlite3.Connection, process_id: str, name: str, oab_number: str,
                             oab_uf: str | None, refs: list[dict[str, Any]], excerpt: str) -> sqlite3.Row:
    normalized_name = _norm_name(name)
    existing_participant = next(
        (row for row in db.execute(
            "SELECT * FROM process_participants WHERE process_id=? AND base_role='REPRESENTATIVE'",
            (process_id,),
        ) if _norm_name(row["display_name"]) == normalized_name),
        None,
    )
    if existing_participant:
        try:
            provenance = json.loads(existing_participant["provenance_json"] or "{}")
        except json.JSONDecodeError:
            provenance = {}
        provenance["documentary_evidence"] = {
            "extraction_method": "same_movement_bilateral_link",
            "oab_number": oab_number,
            "oab_uf": oab_uf,
        }
        source_refs_json = _json(_merge_refs(existing_participant["source_refs_json"], refs))
        provenance_json = _json(provenance)
        db.execute(
            """UPDATE process_participants SET source_refs_json=?,provenance_json=?,updated_at=?
               WHERE participant_id=? AND (source_refs_json IS NOT ? OR provenance_json IS NOT ?)""",
            (source_refs_json, provenance_json, _now(), existing_participant["participant_id"], source_refs_json, provenance_json),
        )
        return db.execute("SELECT * FROM process_participants WHERE participant_id=?", (existing_participant["participant_id"],)).fetchone()
    entity_id = _entity_for_documentary_lawyer(db, name, oab_number, oab_uf)
    participant_id = _participant_id(process_id, entity_id, "REPRESENTATIVE")
    stamp = _now()
    existing = db.execute("SELECT * FROM process_participants WHERE participant_id=?", (participant_id,)).fetchone()
    merged = _merge_refs(existing["source_refs_json"] if existing else None, refs)
    provenance = {"source": "DOCUMENTARY_EVIDENCE", "extraction_method": "same_movement_bilateral_link", "oab_number": oab_number, "oab_uf": oab_uf}
    db.execute(
        """INSERT INTO process_participants(participant_id,process_id,entity_id,display_name,base_role,source_refs_json,provenance_json,status,confidence,created_at,updated_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(process_id,entity_id,base_role) DO UPDATE SET source_refs_json=excluded.source_refs_json,
             provenance_json=excluded.provenance_json,status=excluded.status,confidence=excluded.confidence,updated_at=excluded.updated_at
           WHERE process_participants.source_refs_json IS NOT excluded.source_refs_json
              OR process_participants.provenance_json IS NOT excluded.provenance_json
              OR process_participants.status IS NOT excluded.status
              OR process_participants.confidence IS NOT excluded.confidence""",
        (participant_id, process_id, entity_id, " ".join(name.split()), "REPRESENTATIVE", _json(merged), _json(provenance), "CONFIRMED", "HIGH", stamp, stamp),
    )
    return db.execute("SELECT * FROM process_participants WHERE participant_id=?", (participant_id,)).fetchone()


def _candidate_parties(text: str, participants: list[sqlite3.Row], marker_start: int, marker_end: int) -> list[sqlite3.Row]:
    window_start = max(0, marker_start - 900)
    window_end = min(len(text), marker_end + 350)
    window = text[window_start:window_end]
    matched = [row for row in participants if _norm_name(row["display_name"]) in _norm_name(window)]
    if len(matched) == 1:
        return matched
    role_words = re.sub(r"\s+", " ", window).lower()
    role = "RESPONDENT" if re.search(r"\brequerid[oa]\b|\br[eéu]\b", role_words) else "CLAIMANT" if re.search(r"\bautor[ao]\b|\brequerente\b", role_words) else None
    if role:
        role_matches = [row for row in participants if row["base_role"] == role and _norm_name(row["display_name"]) in _norm_name(window)]
        if len(role_matches) == 1:
            return role_matches
    return []


def materialize_representations(db: sqlite3.Connection, process_id: str | None = None) -> int:
    """Materialize only bilateral documentary links from one Movement.

    A lawyer name/OAB is never enough by itself: a party and an explicit
    advocacy context must also be found in the same Movement, with page
    provenance.  A document/container is not a semantic piece boundary.
    """
    present = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    total = 0
    # A relação capturada diretamente da capa é estruturada e não depende de
    # redescoberta textual nos Autos. O role_raw preserva o vínculo bilateral
    # fornecido pelo provider: "Advogado (nome da parte)".
    if {"party_relations", "legal_entities", "process_participants"}.issubset(present):
        cover_params = () if process_id is None else (process_id,)
        cover_rows = db.execute(
            """SELECT pr.owner_id AS process_id,pr.party_relation_id,pr.entity_id,pr.role_raw,
                      le.display_name AS representative_name
               FROM party_relations pr JOIN legal_entities le ON le.entity_id=pr.entity_id
              WHERE pr.owner_type='PROCESS' AND pr.role='ADVOGADO'"""
            + (" AND pr.owner_id=?" if process_id else ""),
            cover_params,
        ).fetchall()
        for row in cover_rows:
            match = re.match(r"^Advogad[ao]\s*\((.+)\)\s*$", str(row["role_raw"] or ""), re.IGNORECASE)
            if not match:
                continue
            represented_name = match.group(1).strip()
            representatives = db.execute(
                "SELECT * FROM process_participants WHERE process_id=? AND entity_id=? AND base_role='REPRESENTATIVE'",
                (row["process_id"], row["entity_id"]),
            ).fetchall()
            represented = db.execute(
                "SELECT * FROM process_participants WHERE process_id=? AND base_role IN ('CLAIMANT','RESPONDENT','THIRD_PARTY','OTHER') AND display_name=?",
                (row["process_id"], represented_name),
            ).fetchall()
            if len(representatives) != 1 or len(represented) != 1:
                continue
            refs = [{"source": "cpopg_cover", "party_relation_id": row["party_relation_id"]}]
            excerpt = f"Capa e-SAJ: {row['role_raw']}"
            number, uf = _oab_from_entity(db, row["entity_id"])
            total += _upsert_representation(db, row["process_id"], representatives[0], represented[0], "LAWYER", number, uf, refs, excerpt)

    if not {"pages", "documents", "movement_pieces", "movements"}.issubset(present):
        # Movement is the required semantic boundary for documentary fallback.
        db.commit()
        return total
    params = () if process_id is None else (process_id,)
    page_rows = db.execute(
        "SELECT p.page_id,p.document_id,p.page_number,p.content,d.process_id FROM pages p JOIN documents d USING(document_id)"
        + (" WHERE d.process_id=?" if process_id else "") + " ORDER BY d.process_id,p.document_id,p.page_number",
        params,
    ).fetchall()
    pages_by_key = {(row["document_id"], int(row["page_number"])): row for row in page_rows}
    movement_rows = db.execute(
        """SELECT mp.movement_id,mp.document_id,mp.piece_json,
                  m.process_id,m.sequence,m.movement_type,m.title
           FROM movement_pieces mp JOIN movements m ON m.movement_id=mp.movement_id"""
        + (" WHERE m.process_id=?" if process_id else "") + " ORDER BY m.process_id,m.sequence,mp.piece_order",
        params,
    ).fetchall()
    pages: list[dict[str, Any]] = []
    for piece in movement_rows:
        try:
            payload = json.loads(piece["piece_json"] or "{}")
        except json.JSONDecodeError:
            continue
        for item in payload.get("pages") or []:
            document_id = item.get("document_id") or piece["document_id"]
            try:
                pdf_page = int(item.get("pdf_page"))
            except (TypeError, ValueError):
                continue
            source = pages_by_key.get((document_id, pdf_page))
            if not source:
                # An incomplete piece map is a gap, not permission to use the container.
                continue
            pages.append({**dict(source), "movement_id": piece["movement_id"], "sequence": piece["sequence"],
                          "movement_type": piece["movement_type"], "title": piece["title"]})
    participants = db.execute("SELECT participant_id,process_id,display_name,base_role FROM process_participants" + (" WHERE process_id=?" if process_id else ""), params).fetchall()
    by_process: dict[str, list[sqlite3.Row]] = {}
    for row in participants:
        by_process.setdefault(row["process_id"], []).append(row)
    by_movement: dict[str, list[sqlite3.Row]] = {}
    for page in pages:
        by_movement.setdefault(page["movement_id"], []).append(page)
    for movement_id, document_pages in by_movement.items():
        process = document_pages[0]["process_id"]
        candidates = by_process.get(process, [])
        movement_type = " ".join(str(document_pages[0]["movement_type"] or "").split())
        movement_title = " ".join(str(document_pages[0]["title"] or "").split())
        movement_label = f"{movement_type} {movement_title}".casefold()
        if re.search(r"certid[aã]o|publica[cç][aã]o|di[aá]rio|djen", movement_label):
            continue
        full_text = "\n".join(page["content"] or "" for page in document_pages)
        lawyer_hits: list[tuple[str, str, str | None, sqlite3.Row]] = []
        for page in document_pages:
            text = page["content"] or ""
            for hit in _OAB_RE.finditer(text):
                number, uf = _oab_value(hit)
                if len(number) < 4:
                    continue
                surrounding = text[max(0, hit.start() - 180):min(len(text), hit.end() + 180)]
                lower_surrounding = surrounding.casefold()
                # OAB in a publication/certification roster is not a signature.
                if ("publicação" in lower_surrounding or "djen" in lower_surrounding or "certidão" in lower_surrounding or "adv:" in lower_surrounding) and not re.search(r"pede\s+deferimento|termos\s+em|assina", lower_surrounding):
                    continue
                if not re.search(r"pede\s+deferimento|termos\s+em|assina|por\s+seu\s+advogado", text.casefold()):
                    continue
                name = _clean_lawyer_name(hit.group("name"))
                lawyer_hits.append((name, number, uf, page))
        if not lawyer_hits:
            continue
        seen_links: set[tuple[str, str, str, str | None]] = set()
        # Explicit “X, representada por Y” links remain valid for guardian and lawyer roles.
        for match in _REPRESENTED_RE.finditer(full_text):
            represented = next((row for row in candidates if _norm_name(row["display_name"]) == _norm_name(match.group("represented"))), None)
            named_representative = _norm_name(match.group("representative"))
            if not represented:
                continue
            for name, number, uf, page in lawyer_hits:
                if named_representative not in _norm_name(name):
                    continue
                representative = _documentary_participant(db, process, name, number, uf, [_page_ref(page, movement_id)], _excerpt(full_text, match.start(), match.end()))
                refs = [_page_ref(page, movement_id)]
                excerpt = _excerpt(full_text, match.start(), match.end())
                total += _upsert_representation(db, process, representative, represented, "LEGAL_GUARDIAN", None, None, refs, excerpt)
                total += _upsert_representation(db, process, representative, represented, "LAWYER", number, uf, refs, excerpt)
                seen_links.add((representative["participant_id"], represented["participant_id"], number, uf))
        # “Party ... por seu advogado(s)” links the signed OAB lawyer to the party.
        for marker in _LAWYER_CONTEXT_RE.finditer(full_text):
            parties = _candidate_parties(full_text, candidates, marker.start(), marker.end())
            if len(parties) != 1:
                continue
            represented = parties[0]
            for name, number, uf, page in lawyer_hits:
                key = (_norm_name(name), number, uf)
                if key not in {(_norm_name(x[0]), x[1], x[2]) for x in lawyer_hits}:
                    continue
                representative = _documentary_participant(db, process, name, number, uf, [_page_ref(page, movement_id)], _excerpt(full_text, marker.start(), marker.end()))
                link_key = (representative["participant_id"], represented["participant_id"], number, uf)
                if link_key in seen_links:
                    continue
                refs = [_page_ref(page, movement_id)]
                excerpt = _excerpt(full_text, marker.start(), marker.end())
                total += _upsert_representation(db, process, representative, represented, "LAWYER", number, uf, refs, excerpt)
                seen_links.add(link_key)
    db.commit()
    return total


def _upsert_representation(db: sqlite3.Connection, process_id: str, representative: sqlite3.Row, represented: sqlite3.Row, kind: str, oab_number: str | None, oab_uf: str | None, refs: list[dict], excerpt: str) -> int:
    stamp = _now()
    rid = _stable("representation", process_id, representative["participant_id"], represented["participant_id"], kind, oab_number, oab_uf)
    if oab_number and oab_uf:
        legacy = db.execute(
            "SELECT representation_id FROM representations WHERE process_id=? AND representative_participant_id=? AND represented_participant_id=? AND representation_kind=? AND oab_number=? AND oab_uf IS NULL",
            (process_id, representative["participant_id"], represented["participant_id"], kind, oab_number),
        ).fetchone()
        if legacy and legacy["representation_id"] != rid:
            target = db.execute("SELECT 1 FROM representations WHERE representation_id=?", (rid,)).fetchone()
            if target:
                db.execute("DELETE FROM representations WHERE representation_id=?", (legacy["representation_id"],))
            else:
                db.execute("UPDATE representations SET representation_id=?,oab_uf=? WHERE representation_id=?", (rid, oab_uf, legacy["representation_id"]))
    db.execute(
        """INSERT INTO representations(representation_id,process_id,representative_participant_id,represented_participant_id,representation_kind,oab_number,oab_uf,source_refs_json,source_excerpt,provenance_json,status,confidence,created_at,updated_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(representation_id)
           DO UPDATE SET source_refs_json=excluded.source_refs_json,source_excerpt=excluded.source_excerpt,provenance_json=excluded.provenance_json,updated_at=excluded.updated_at
           WHERE representations.source_refs_json IS NOT excluded.source_refs_json
              OR representations.source_excerpt IS NOT excluded.source_excerpt
              OR representations.provenance_json IS NOT excluded.provenance_json""",
        (rid, process_id, representative["participant_id"], represented["participant_id"], kind, oab_number, oab_uf, _json(refs), excerpt, _json({"extraction_method": "same_movement_bilateral_link", "representation_kind": kind}), "CONFIRMED", "HIGH", stamp, stamp),
    )
    return 1


def materialize_all(db: sqlite3.Connection) -> dict[str, int]:
    required = {"party_relations", "legal_entities", "processes"}
    present = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not required.issubset(present):
        return {"participants": 0, "representations": 0}
    participants = materialize_participants(db)
    representations = materialize_representations(db) if {"pages", "documents"}.issubset(present) else 0
    return {"participants": participants, "representations": representations}


def list_participants(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    rows = db.execute("SELECT * FROM process_participants WHERE process_id=? ORDER BY base_role,display_name", (process_id,)).fetchall()
    return [{**dict(row), "source_refs": json.loads(row["source_refs_json"]), "provenance": json.loads(row["provenance_json"])} for row in rows]


def list_representations(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    rows = db.execute("SELECT * FROM representations WHERE process_id=? ORDER BY representation_kind,representation_id", (process_id,)).fetchall()
    return [{**dict(row), "source_refs": json.loads(row["source_refs_json"]), "provenance": json.loads(row["provenance_json"])} for row in rows]


def get_profile(db: sqlite3.Connection, profile_id: str) -> dict[str, Any] | None:
    row = db.execute("SELECT * FROM professional_profiles WHERE profile_id=?", (profile_id,)).fetchone()
    return dict(row) if row else None


def save_profile(db: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    profile_id = str(payload.get("profile_id") or "profile_local_default").strip()
    display_name = " ".join(str(payload.get("display_name") or "").split())
    profile_type = str(payload.get("profile_type") or "OTHER").upper()
    if not display_name or profile_type not in PROFILE_TYPES:
        raise ValueError("display_name e profile_type válidos são obrigatórios")
    stamp = _now()
    db.execute(
        """INSERT INTO professional_profiles(profile_id,display_name,profile_type,oab_number,oab_uf,future_identity_ref,created_at,updated_at)
           VALUES(?,?,?,?,?,?,?,?)
           ON CONFLICT(profile_id) DO UPDATE SET display_name=excluded.display_name,profile_type=excluded.profile_type,oab_number=excluded.oab_number,oab_uf=excluded.oab_uf,future_identity_ref=excluded.future_identity_ref,updated_at=excluded.updated_at""",
        (profile_id, display_name, profile_type, payload.get("oab_number"), payload.get("oab_uf"), payload.get("future_identity_ref"), stamp, stamp),
    )
    db.commit()
    return get_profile(db, profile_id) or {}


def get_context(db: sqlite3.Connection, process_id: str, profile_id: str) -> dict[str, Any] | None:
    row = db.execute("SELECT * FROM user_process_contexts WHERE process_id=? AND profile_id=?", (process_id, profile_id)).fetchone()
    if not row:
        return None
    result = dict(row)
    result["represented_participant_ids"] = json.loads(result.pop("represented_participant_ids_json") or "[]")
    return result


def save_context(db: sqlite3.Connection, process_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    profile_id = str(payload.get("profile_id") or "").strip()
    relation = str(payload.get("relation") or "").upper()
    participant_id = payload.get("participant_id")
    represented = [str(x) for x in (payload.get("represented_participant_ids") or []) if str(x).strip()]
    source = str(payload.get("source") or "USER_CONFIRMED").upper()
    if not profile_id or relation not in RELATIONS or source not in CONTEXT_SOURCES:
        raise ValueError("profile_id, relation e source inválidos")
    if not db.execute("SELECT 1 FROM processes WHERE process_id=?", (process_id,)).fetchone():
        raise ValueError("processo inexistente")
    if relation == "FOLLOWING" and (participant_id or represented):
        raise ValueError("FOLLOWING não possui participante ou parte representada")
    if relation == "ACTING" and not represented:
        raise ValueError("ACTING exige ao menos um participante representado")
    if relation == "PARTY" and not participant_id:
        raise ValueError("PARTY exige participant_id")
    ids = ([participant_id] if participant_id else []) + represented
    if any(not db.execute("SELECT 1 FROM process_participants WHERE participant_id=? AND process_id=?", (value, process_id)).fetchone() for value in ids):
        raise ValueError("participante não pertence ao processo")
    context_id = _stable("context", process_id, profile_id)
    stamp = _now()
    db.execute(
        """INSERT INTO user_process_contexts(context_id,process_id,profile_id,relation,participant_id,represented_participant_ids_json,source,status,created_at,updated_at)
           VALUES(?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(process_id,profile_id) DO UPDATE SET relation=excluded.relation,participant_id=excluded.participant_id,represented_participant_ids_json=excluded.represented_participant_ids_json,source=excluded.source,status=excluded.status,updated_at=excluded.updated_at""",
        (context_id, process_id, profile_id, relation, participant_id, json.dumps(represented, ensure_ascii=False), source, "ACTIVE", stamp, stamp),
    )
    db.commit()
    return get_context(db, process_id, profile_id) or {}
