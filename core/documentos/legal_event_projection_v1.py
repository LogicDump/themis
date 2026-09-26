"""Projeção unificada de leitura (Read Model) de LegalEvent.

Este módulo implementa a projeção somente-leitura dos eventos jurídicos a partir
das tabelas de domínio canônicas existentes (deadlines, hearings, pending_items),
sem criar ou duplicar persistência no SQLite.

Conforme auditoria do Core:
- DEADLINE -> projetado a partir de 'deadlines'
- HEARING  -> projetado a partir de 'hearings' (+ 'hearing_participants')
- PENDING  -> projetado a partir de 'pending_items'
- PUBLICATION -> não projetado neste momento devido à ausência de regra determinística
                 comprovada em chronology_events / process_movements.

O Core retorna estritamente dados de domínio limpos, sem propriedades visuais
(como tone, codicon, dot_class ou formatações de interface).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from core.runtime_paths import index_db_path

SUPPORTED_KINDS = {"DEADLINE", "HEARING", "PENDING", "PUBLICATION"}

KIND_ALIASES = {
    "DEADLINE": "DEADLINE",
    "DEADLINES": "DEADLINE",
    "PRAZO": "DEADLINE",
    "PRAZOS": "DEADLINE",
    "HEARING": "HEARING",
    "HEARINGS": "HEARING",
    "AUDIENCIA": "HEARING",
    "AUDIENCIAS": "HEARING",
    "PENDING": "PENDING",
    "PENDING_ITEMS": "PENDING",
    "PENDENCIA": "PENDING",
    "PENDENCIAS": "PENDING",
    "PUBLICATION": "PUBLICATION",
    "PUBLICATIONS": "PUBLICATION",
    "PUBLICACAO": "PUBLICATION",
    "PUBLICACOES": "PUBLICATION",
}


def _json_or_default(raw: Any, default: Any) -> Any:
    if raw is None or raw == "":
        return default
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(str(raw))
    except Exception:
        return default


def _has_table(db: sqlite3.Connection, table_name: str) -> bool:
    row = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


class LegalEventProjection:
    """Projeção de leitura que agrega eventos de múltiplas entidades canônicas."""

    @classmethod
    def _ensure_row_factory(cls, db: sqlite3.Connection) -> None:
        if db.row_factory is None:
            db.row_factory = sqlite3.Row

    @classmethod
    def project_deadlines(
        cls,
        db: sqlite3.Connection,
        *,
        process_id: str | None = None,
    ) -> list[dict[str, Any]]:
        cls._ensure_row_factory(db)
        if not _has_table(db, "deadlines"):
            return []

        query = """
            SELECT
                deadline_id,
                owner_type,
                owner_id,
                title,
                description,
                deadline_type,
                term,
                due_at,
                date_precision,
                timezone,
                status,
                priority,
                responsible,
                triggering_event,
                legal_basis,
                confidence,
                confirmation_status,
                source_refs_json,
                provenance_json,
                created_at,
                updated_at
            FROM deadlines
        """
        params: list[Any] = []
        if process_id:
            query += " WHERE owner_id=? OR (owner_type='PROCESS' AND owner_id=?)"
            params.extend([process_id, process_id])
        query += " ORDER BY due_at ASC, deadline_id ASC"

        rows = db.execute(query, params).fetchall()
        events: list[dict[str, Any]] = []

        for r in rows:
            due_at = r["due_at"]
            date_str = str(due_at)[:10] if due_at else None
            events.append({
                "id": f"deadline:{r['deadline_id']}",
                "kind": "DEADLINE",
                "source_entity": "deadlines",
                "source_id": r["deadline_id"],
                "owner_type": r["owner_type"],
                "owner_id": r["owner_id"],
                "process_id": r["owner_id"] if r["owner_type"] == "PROCESS" else None,
                "title": r["title"],
                "description": r["description"],
                "term": r["term"],
                "deadline_type": r["deadline_type"],
                "due_at": due_at,
                "relevant_at": due_at,
                "date": date_str,
                "date_precision": r["date_precision"],
                "timezone": r["timezone"],
                "status": r["status"],
                "priority": r["priority"],
                "responsible": r["responsible"],
                "triggering_event": r["triggering_event"],
                "legal_basis": r["legal_basis"],
                "confidence": r["confidence"],
                "confirmation_status": r["confirmation_status"],
                "source_refs": _json_or_default(r["source_refs_json"], []),
                "provenance": _json_or_default(r["provenance_json"], {}),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            })

        return events

    @classmethod
    def project_hearings(
        cls,
        db: sqlite3.Connection,
        *,
        process_id: str | None = None,
    ) -> list[dict[str, Any]]:
        cls._ensure_row_factory(db)
        if not _has_table(db, "hearings"):
            return []

        query = """
            SELECT
                hearing_id,
                process_id,
                hearing_type,
                scheduled_at,
                date_precision,
                location,
                meeting_info,
                status,
                outcome_notes,
                source_refs_json,
                provenance_json,
                created_at,
                updated_at
            FROM hearings
        """
        params: list[Any] = []
        if process_id:
            query += " WHERE process_id=?"
            params.append(process_id)
        query += " ORDER BY scheduled_at ASC, hearing_id ASC"

        rows = db.execute(query, params).fetchall()
        has_participants = _has_table(db, "hearing_participants")
        events: list[dict[str, Any]] = []

        for r in rows:
            scheduled_at = r["scheduled_at"]
            date_str = str(scheduled_at)[:10] if scheduled_at else None
            h_type = r["hearing_type"] or "Audiência"
            h_id = r["hearing_id"]

            participants = []
            if has_participants:
                p_rows = db.execute(
                    "SELECT participant, role FROM hearing_participants WHERE hearing_id=? ORDER BY participant",
                    (h_id,),
                ).fetchall()
                participants = [{"name": p["participant"], "role": p["role"]} for p in p_rows]

            events.append({
                "id": f"hearing:{h_id}",
                "kind": "HEARING",
                "source_entity": "hearings",
                "source_id": h_id,
                "owner_type": "PROCESS",
                "owner_id": r["process_id"],
                "process_id": r["process_id"],
                "title": f"Audiência ({h_type})" if r["hearing_type"] else "Audiência",
                "hearing_type": r["hearing_type"],
                "description": r["outcome_notes"],
                "scheduled_at": scheduled_at,
                "relevant_at": scheduled_at,
                "date": date_str,
                "date_precision": r["date_precision"],
                "location": r["location"],
                "meeting_info": r["meeting_info"],
                "status": r["status"],
                "outcome_notes": r["outcome_notes"],
                "participants": participants,
                "source_refs": _json_or_default(r["source_refs_json"], []),
                "provenance": _json_or_default(r["provenance_json"], {}),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            })

        return events

    @classmethod
    def project_pending_items(
        cls,
        db: sqlite3.Connection,
        *,
        process_id: str | None = None,
    ) -> list[dict[str, Any]]:
        cls._ensure_row_factory(db)
        if not _has_table(db, "pending_items"):
            return []

        query = """
            SELECT
                pending_id,
                owner_type,
                owner_id,
                title,
                description,
                status,
                priority,
                responsible,
                due_at,
                source_origin,
                source_refs_json,
                provenance_json,
                resolved_at,
                created_at,
                updated_at
            FROM pending_items
        """
        params: list[Any] = []
        if process_id:
            query += " WHERE owner_id=? OR (owner_type='PROCESS' AND owner_id=?)"
            params.extend([process_id, process_id])
        query += " ORDER BY due_at ASC, pending_id ASC"

        rows = db.execute(query, params).fetchall()
        events: list[dict[str, Any]] = []

        for r in rows:
            due_at = r["due_at"]
            date_str = str(due_at)[:10] if due_at else None
            events.append({
                "id": f"pending:{r['pending_id']}",
                "kind": "PENDING",
                "source_entity": "pending_items",
                "source_id": r["pending_id"],
                "owner_type": r["owner_type"],
                "owner_id": r["owner_id"],
                "process_id": r["owner_id"] if r["owner_type"] == "PROCESS" else None,
                "title": r["title"],
                "description": r["description"],
                "due_at": due_at,
                "relevant_at": due_at,
                "date": date_str,
                "status": r["status"],
                "priority": r["priority"],
                "responsible": r["responsible"],
                "source_origin": r["source_origin"],
                "resolved_at": r["resolved_at"],
                "source_refs": _json_or_default(r["source_refs_json"], []),
                "provenance": _json_or_default(r["provenance_json"], {}),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            })

        return events

    @classmethod
    def project_publications(cls, db: sqlite3.Connection, *, process_id: str | None = None) -> list[dict[str, Any]]:
        cls._ensure_row_factory(db)
        if not _has_table(db, "publications"):
            return []
        query = "SELECT * FROM publications WHERE published_on IS NOT NULL"
        params: list[Any] = []
        if process_id:
            query += " AND process_id=?"; params.append(process_id)
        query += " ORDER BY published_on, publication_id"
        return [{"id": f"publication:{r['publication_id']}", "kind": "PUBLICATION", "source_entity": "publications", "source_id": r["publication_id"], "owner_type": "PROCESS", "owner_id": r["process_id"], "process_id": r["process_id"], "title": r["publication_type"] or "Publicação", "description": r["full_text"], "published_at": r["published_on"], "relevant_at": r["published_on"], "date": r["published_on"], "tribunal": r["tribunal"], "organ": r["organ"], "medium": r["medium"], "source_url": r["source_url"], "provenance": _json_or_default(r["provenance_json"], {}), "created_at": r["created_at"], "updated_at": r["updated_at"]} for r in db.execute(query, params).fetchall()]

    @classmethod
    def list_events(
        cls,
        db: sqlite3.Connection,
        *,
        process_id: str | None = None,
        kind: str | None = None,
        query: str | None = None,
    ) -> list[dict[str, Any]]:
        normalized_kind = None
        if kind:
            k_upper = str(kind).strip().upper()
            if k_upper and k_upper not in {"ALL", "TODOS"}:
                normalized_kind = KIND_ALIASES.get(k_upper)
                if not normalized_kind:
                    return []

        all_events: list[dict[str, Any]] = []

        if normalized_kind is None or normalized_kind == "DEADLINE":
            all_events.extend(cls.project_deadlines(db, process_id=process_id))

        if normalized_kind is None or normalized_kind == "HEARING":
            all_events.extend(cls.project_hearings(db, process_id=process_id))

        if normalized_kind is None or normalized_kind == "PENDING":
            all_events.extend(cls.project_pending_items(db, process_id=process_id))

        if normalized_kind is None or normalized_kind == "PUBLICATION":
            all_events.extend(cls.project_publications(db, process_id=process_id))

        if query:
            q_lower = query.strip().lower()
            filtered: list[dict[str, Any]] = []
            for evt in all_events:
                title = str(evt.get("title") or "").lower()
                desc = str(evt.get("description") or "").lower()
                owner = str(evt.get("owner_id") or "").lower()
                extra = str(evt.get("legal_basis") or evt.get("location") or "").lower()
                if q_lower in title or q_lower in desc or q_lower in owner or q_lower in extra:
                    filtered.append(evt)
            all_events = filtered

        # Ordenação cronológica estável por relevant_at canônico (com chaves nulas ao final) e ID
        def _sort_key(item: dict[str, Any]) -> tuple[int, str, str]:
            t = item.get("relevant_at") or item.get("date") or ""
            return (0 if t else 1, t, item.get("id", ""))

        all_events.sort(key=_sort_key)
        return all_events

    @classmethod
    def get_event(
        cls,
        db: sqlite3.Connection,
        event_id: str,
    ) -> dict[str, Any] | None:
        if not event_id:
            return None

        clean_id = str(event_id).strip()

        if clean_id.startswith("deadline:"):
            raw_id = clean_id.split(":", 1)[1]
            for evt in cls.project_deadlines(db):
                if evt["source_id"] == raw_id or evt["id"] == clean_id:
                    return evt
            return None

        if clean_id.startswith("hearing:"):
            raw_id = clean_id.split(":", 1)[1]
            for evt in cls.project_hearings(db):
                if evt["source_id"] == raw_id or evt["id"] == clean_id:
                    return evt
            return None

        if clean_id.startswith("pending:"):
            raw_id = clean_id.split(":", 1)[1]
            for evt in cls.project_pending_items(db):
                if evt["source_id"] == raw_id or evt["id"] == clean_id:
                    return evt
            return None

        if clean_id.startswith("publication:"):
            raw_id = clean_id.split(":", 1)[1]
            return next((evt for evt in cls.project_publications(db) if evt["source_id"] == raw_id), None)

        # Busca irrestrita sem prefixo
        for evt in cls.list_events(db):
            if evt["id"] == clean_id or evt["source_id"] == clean_id:
                return evt

        return None


def list_events(
    *,
    process_id: str | None = None,
    kind: str | None = None,
    query: str | None = None,
    db_path: Path | str | None = None,
    db: sqlite3.Connection | None = None,
) -> list[dict[str, Any]]:
    """Função pública de conveniência para listar LegalEvents."""
    if db is not None:
        return LegalEventProjection.list_events(db, process_id=process_id, kind=kind, query=query)

    target = Path(db_path or index_db_path()).resolve()
    if not target.is_file():
        return []

    conn = sqlite3.connect(target.as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return LegalEventProjection.list_events(conn, process_id=process_id, kind=kind, query=query)
    finally:
        conn.close()


def get_event(
    event_id: str,
    *,
    db_path: Path | str | None = None,
    db: sqlite3.Connection | None = None,
) -> dict[str, Any] | None:
    """Função pública de conveniência para buscar um único LegalEvent pelo ID."""
    if db is not None:
        return LegalEventProjection.get_event(db, event_id)

    target = Path(db_path or index_db_path()).resolve()
    if not target.is_file():
        return None

    conn = sqlite3.connect(target.as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return LegalEventProjection.get_event(conn, event_id)
    finally:
        conn.close()
