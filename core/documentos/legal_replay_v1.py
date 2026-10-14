"""Verified primary source import and the shared deterministic legal projection.

Raw source import is offline; optional recalculation dispatches to the Core cycle,
which acquires missing official evidence. Never transplants derived legal rows.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from core.documentos.publications_v1 import (
    migrate_connection as migrate_publications,
    publication_from_item,
    upsert_publication,
)
from core.documentos.court_calendar_store_v1 import (
    migrate_connection as migrate_calendar, store_snapshot,
)
from core.documentos.process_event_store_v1 import materialize_process_events
from core.documentos.deadline_instruction_store_v1 import (
    materialize_process as materialize_movement_instructions,
    materialize_publication_instructions,
)
from core.documentos.deadline_obligation_store_v1 import materialize_process as materialize_obligations
from core.documentos.deadline_resolution_pipeline_v1 import enrich_process_obligations
from core.documentos.deadline_calculation_store_v1 import calculate_process


class LegalReplayIncomplete(RuntimeError):
    """Source evidence insufficient to reconstruct a legal domain safely."""


def _has(db: sqlite3.Connection, table: str) -> bool:
    return db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _source_publications(db: sqlite3.Connection, process_id: str, *, allow_missing: bool = False) -> list[dict[str, Any]]:
    if not _has(db, "publications"):
        return []
    rows = db.execute(
        "SELECT * FROM publications WHERE process_id=? ORDER BY publication_id", (process_id,)
    ).fetchall()
    checked: list[dict[str, Any]] = []
    for row in rows:
        source = dict(row)
        provenance = json.loads(source["provenance_json"] or "{}")
        raw = provenance.get("raw_item")
        request_url = provenance.get("query_url")
        if not isinstance(raw, dict) or not isinstance(request_url, str):
            if allow_missing:
                continue
            raise LegalReplayIncomplete("DJEN sem raw_item/query_url reproduzível: " + source["publication_id"])
        rebuilt = publication_from_item(raw, process_id=process_id, request_url=request_url)
        if (rebuilt is None or rebuilt["payload_hash"] != source["payload_hash"]
                or rebuilt["communication_id"] != source["communication_id"]
                or rebuilt["certificate_code"] != source["certificate_code"]):
            raise LegalReplayIncomplete("DJEN raw_item não corresponde ao registro original: " + source["publication_id"])
        # Only raw official facts are inputs; an old projected date is not evidence.
        checked.append(rebuilt)
    return checked


def _calendar_source(db: sqlite3.Connection) -> list[Any]:
    if not _has(db, "court_calendar_snapshots"):
        return []
    from core.documentos.court_calendar_provider_v1 import RawSourceSnapshot
    result = []
    for row in db.execute("SELECT * FROM court_calendar_snapshots ORDER BY snapshot_id"):
        raw = bytes(row["content"])
        if hashlib.sha256(raw).hexdigest() != row["content_hash"]:
            raise LegalReplayIncomplete("Snapshot TJSP com hash inválido: " + row["snapshot_id"])
        snapshot = RawSourceSnapshot(
            source_url=row["source_url"],
            request_params=json.loads(row["request_params_json"] or "{}"),
            fetched_at=row["fetched_at"], content_hash=row["content_hash"],
            parser_version=row["parser_version"], content=raw,
        )
        result.append((str(row["snapshot_id"]), snapshot))
    return result


def replay_legal_sources(
    source_path: Path,
    target_path: Path,
    process_id: str,
    *,
    recalculate: bool = True,
) -> dict[str, Any]:
    """Import primary facts into isolated staging; optionally invoke the Core cycle.

    The caller owns both DB paths and must never pass the active package as target.
    No legacy derived deadline rows are transplanted.
    """
    source_path, target_path = Path(source_path).resolve(), Path(target_path).resolve()
    if source_path == target_path:
        raise ValueError("Legal replay exige bancos diferentes: original e staging")
    if not source_path.is_file() or not target_path.is_file():
        raise FileNotFoundError("Legal replay exige original e staging existentes")

    from contextlib import closing
    with closing(sqlite3.connect("file:" + source_path.as_posix() + "?mode=ro", uri=True)) as source:
        source.row_factory = sqlite3.Row
        publications = _source_publications(source, process_id, allow_missing=True)
        original_count = source.execute("SELECT count(*) FROM publications WHERE process_id=?", (process_id,)).fetchone()[0] if _has(source, "publications") else 0
        expected_sources = [tuple(row) for row in source.execute(
            "SELECT communication_id,certificate_code FROM publications WHERE process_id=?", (process_id,),
        )] if _has(source, "publications") else []
        snapshots = _calendar_source(source)
        expected_publication_ids = {(r["communication_id"], r["certificate_code"]) for r in publications}
    with closing(sqlite3.connect(target_path)) as target:
        target.row_factory = sqlite3.Row
        target.execute("PRAGMA foreign_keys=ON")
        if not target.execute("SELECT 1 FROM processes WHERE process_id=?", (process_id,)).fetchone():
            raise LegalReplayIncomplete("Processo ausente no staging")
        if publications:
            migrate_publications(target)
            for item in publications:
                upsert_publication(target, item)
            target.commit()
        if snapshots:
            migrate_calendar(target)
            for expected_id, snapshot in snapshots:
                if store_snapshot(target, snapshot) != expected_id:
                    raise LegalReplayIncomplete("Identidade do snapshot TJSP não reproduzida")
            target.commit()
        calendar_report = []
        actual_ids = {
            tuple(row) for row in target.execute(
                "SELECT communication_id,certificate_code FROM publications WHERE process_id=?", (process_id,)
            )
        } if _has(target, "publications") else set()
        if expected_publication_ids != actual_ids:
            raise LegalReplayIncomplete("DJEN replay incompleto")
        if not recalculate:
            return {"publications": len(publications), "snapshots": len(snapshots),
                    "missing_publications": original_count - len(publications),
                    "expected_sources": expected_sources, "calendar": calendar_report}

        from core.process_cycle import sync_process_legal
        from datetime import date
        return sync_process_legal(target, process_id, available_to=date.today().isoformat(), acquire=False)


def project_legal_state(db: sqlite3.Connection, process_id: str, *, calendar_entries=None,
                        calendar_report=None) -> dict[str, Any]:
    """One deterministic legal projection chain for acquired process evidence."""
    from core.documentos.participant_context_store_v1 import materialize_all

    materialize_all(db)
    events = materialize_process_events(db, process_id)
    has_movements = _has(db, "movements")
    movement_instructions = materialize_movement_instructions(db, process_id) if has_movements else {"materialized": 0, "deleted": 0}
    publication_instructions = materialize_publication_instructions(db, process_id)
    obligations = materialize_obligations(db, process_id) if has_movements else {"obligations": 0}
    resolution = enrich_process_obligations(db, process_id) if has_movements else {"resolved": 0}
    if calendar_entries is None or calendar_report is None:
        raise ValueError("A projeção exige evidência preparada pelo ciclo Core")
    calculated = calculate_process(db, process_id=process_id, calendar_entries=calendar_entries)
    # The deadline engine validates day-by-day coverage. Reject any obligation
    # that needs a missing/conflicting day; unrelated historical gaps are
    # visible warnings, not a reason to block independent computed deadlines.
    coverage_failures = [item for item in calculated["results"]
                         if isinstance(item.get("reason"), dict) and item["reason"].get("code") in {
                             "CALENDAR_COVERAGE_MISSING", "CALENDAR_ENTRY_CONFLICT",
                             "CALENDAR_VERSION_MISMATCH",
                         }]
    calculated["calendar_errors"] = calendar_report.get("calendar_errors", [])
    calculated["coverage_failures"] = coverage_failures
    if calendar_report["status"] not in {"OK", "PARTIAL"} or (not calendar_entries and calculated["results"]):
        calculated["status"] = "INCOMPLETE"
    elif coverage_failures or calendar_report["status"] == "PARTIAL":
        calculated["status"] = "PARTIAL"
    else:
        calculated["status"] = "OK"
    foreign = db.execute("PRAGMA foreign_key_check").fetchall()
    if foreign:
        raise LegalReplayIncomplete(f"Projeção gerou {len(foreign)} violações FK")
    db.commit()
    return {
        "status": "READY" if calculated["status"] in {"OK", "PARTIAL"} else "INCOMPLETE",
        "legal_status": calculated["status"],
        "events": events, "movement_instructions": movement_instructions,
        "publication_instructions": publication_instructions, "obligations": obligations,
        "resolution": resolution, "calculated": calculated,
    }
