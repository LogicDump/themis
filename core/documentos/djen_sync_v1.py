"""Operational DJEN synchronization state and daily/manual orchestration."""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from typing import Any

from core.process_storage import connect_process, connect_workspace, known_process_ids
from core.runtime_paths import process_db_path, workspace_db_path
from core.documentos.process_event_store_v1 import materialize_process_events
from core.documentos.publications_v1 import sync_djen

DEADLINE_PIPELINE_REVISION = "deadline-pipeline-v4"

SYNC_STATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS djen_sync_state(
  process_id TEXT PRIMARY KEY,
  last_successful_sync_date TEXT,
  last_successful_sync_at TEXT,
  last_available_from TEXT,
  last_available_to TEXT,
  last_count INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  deadline_pipeline_revision TEXT
);
"""


def _ensure_sync_state_schema(db: sqlite3.Connection) -> None:
    db.executescript(SYNC_STATE_SCHEMA)
    columns = {str(row[1]) for row in db.execute("PRAGMA table_info(djen_sync_state)").fetchall()}
    if "deadline_pipeline_revision" not in columns:
        db.execute("ALTER TABLE djen_sync_state ADD COLUMN deadline_pipeline_revision TEXT")
        db.commit()

def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _materialized_process_ids() -> list[str]:
    return [pid for pid in known_process_ids() if process_db_path(pid).is_file()]

def _parse_distribution_date(raw: object) -> str | None:
    text = str(raw or "").strip()
    if len(text) < 10:
        return None
    try:
        return datetime.strptime(text[:10], "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None
def _initial_available_from(process_id: str) -> str:
    db = connect_process(process_id)
    try:
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='process_metadata'").fetchone():
            row = db.execute(
                "SELECT provenance_json FROM process_metadata WHERE process_id=?",
                (process_id,),
            ).fetchone()
            if row and row[0]:
                provenance = json.loads(str(row[0]))
                basic = provenance.get("basic_data") if isinstance(provenance, dict) else None
                value = _parse_distribution_date(
                    basic.get("distribuicao") if isinstance(basic, dict) else None
                )
                if value:
                    return value

        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='publications'").fetchone():
            row = db.execute(
                "SELECT min(available_on) FROM publications WHERE process_id=? AND available_on IS NOT NULL",
                (process_id,),
            ).fetchone()
            if row and row[0]:
                return str(row[0])

        row = db.execute("SELECT created_at FROM processes WHERE process_id=?", (process_id,)).fetchone()
        if row and row[0]:
            try:
                return datetime.fromisoformat(str(row[0]).replace("Z", "+00:00")).date().isoformat()
            except ValueError:
                pass
    finally:
        db.close()
    return date.today().replace(month=1, day=1).isoformat()

def _read_state(process_id: str) -> dict[str, Any] | None:
    target = workspace_db_path()
    if not target.is_file():
        return None
    db = connect_workspace()
    try:
        _ensure_sync_state_schema(db)
        row = db.execute(
            "SELECT * FROM djen_sync_state WHERE process_id=?",
            (process_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        db.close()

def _write_success(
    process_id: str, *, available_from: str, available_to: str, count: int
) -> dict[str, Any]:
    db = connect_workspace(create=True)
    try:
        _ensure_sync_state_schema(db)
        now = _now()
        db.execute(
            """INSERT INTO djen_sync_state(
                 process_id,last_successful_sync_date,last_successful_sync_at,
                 last_available_from,last_available_to,last_count,last_error,deadline_pipeline_revision
               ) VALUES(?,?,?,?,?,?,NULL,?)
               ON CONFLICT(process_id) DO UPDATE SET
                 last_successful_sync_date=excluded.last_successful_sync_date,
                 last_successful_sync_at=excluded.last_successful_sync_at,
                 last_available_from=excluded.last_available_from,
                 last_available_to=excluded.last_available_to,
                 last_count=excluded.last_count,
                 last_error=NULL,
                 deadline_pipeline_revision=excluded.deadline_pipeline_revision""",
            (process_id, available_to, now, available_from, available_to, int(count), DEADLINE_PIPELINE_REVISION),
        )
        db.commit()
        return dict(db.execute(
            "SELECT * FROM djen_sync_state WHERE process_id=?", (process_id,)
        ).fetchone())
    finally:
        db.close()
def _write_error(process_id: str, message: str) -> None:
    db = connect_workspace(create=True)
    try:
        _ensure_sync_state_schema(db)
        db.execute(
            """INSERT INTO djen_sync_state(process_id,last_count,last_error)
               VALUES(?,0,?)
               ON CONFLICT(process_id) DO UPDATE SET last_error=excluded.last_error""",
            (process_id, str(message)[:2000]),
        )
        db.commit()
    finally:
        db.close()

def status(*, as_of: str | None = None) -> dict[str, Any]:
    today = as_of or date.today().isoformat()
    process_ids = _materialized_process_ids()
    states = []
    for process_id in process_ids:
        state = _read_state(process_id) or {"process_id": process_id}
        state["deadline_pipeline_revision_current"] = DEADLINE_PIPELINE_REVISION
        state["needs_sync"] = (
            state.get("last_successful_sync_date") != today
            or state.get("deadline_pipeline_revision") != DEADLINE_PIPELINE_REVISION
        )
        states.append(state)
    return {
        "date": today,
        "process_count": len(process_ids),
        "all_successful_today": bool(process_ids) and all(not s["needs_sync"] for s in states),
        "needs_sync": any(s["needs_sync"] for s in states),
        "processes": states,
    }


def _calculate_tjsp_deadlines(db: sqlite3.Connection, process_id: str, *, target_date: str) -> dict[str, Any]:
    """Acquire the official TJSP calendar and calculate all current obligations.

    Calendar failure is reported to the caller and must not invalidate a
    successful DJEN synchronization.
    """
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='process_metadata'").fetchone():
        return {"process_id": process_id, "status": "SKIPPED", "reason": "PROCESS_METADATA_MISSING"}
    columns = {str(row[1]) for row in db.execute("PRAGMA table_info(process_metadata)").fetchall()}
    if not {"tribunal", "comarca"} <= columns:
        return {"process_id": process_id, "status": "SKIPPED", "reason": "COURT_METADATA_MISSING"}
    metadata = db.execute(
        "SELECT tribunal,comarca FROM process_metadata WHERE process_id=?", (process_id,)
    ).fetchone()
    if not metadata or str(metadata["tribunal"] or "").upper().strip() != "TJSP":
        return {"process_id": process_id, "status": "SKIPPED", "reason": "UNSUPPORTED_COURT"}

    locality = str(metadata["comarca"] or "").strip()
    for prefix in ("Foro de ", "Comarca de "):
        if locality.casefold().startswith(prefix.casefold()):
            locality = locality[len(prefix):].strip()
            break
    if not locality:
        return {"process_id": process_id, "status": "SKIPPED", "reason": "LOCALITY_MISSING"}

    from core.documentos.court_calendar_store_v1 import get_snapshot, migrate_connection as migrate_calendar
    from core.documentos.deadline_calculation_store_v1 import calculate_process
    from core.documentos.providers.tjsp_calendar_acquisition_v1 import (
        HOLIDAYS_ENDPOINT, SUSPENSIONS_ENDPOINT, TjspAcquisitionRequest,
        acquire_tjsp_calendar, compose_effective_tjsp_calendar,
    )

    migrate_calendar(db)
    years: set[int] = {int(target_date[:4])}
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='publications'").fetchone():
        rows = db.execute(
            """SELECT DISTINCT coalesce(p.published_on,p.available_on) AS communication_date
                 FROM deadline_instructions i
                 JOIN publications p ON p.publication_id=i.source_id
                WHERE i.process_id=? AND i.source_entity='PUBLICATION'
                  AND coalesce(p.active,1)<>0
                  AND coalesce(p.published_on,p.available_on) IS NOT NULL""",
            (process_id,),
        ).fetchall()
        for row in rows:
            value = str(row["communication_date"] or "")
            if len(value) >= 4 and value[:4].isdigit():
                years.add(int(value[:4]))

    # A deadline communicated late in December may resume only after the CPC
    # art. 220 suspension and therefore requires the following year's official
    # calendar. Calendar acquisition is evidence-scoped, so include the
    # immediately following year for every relevant communication/target year.
    years |= {year + 1 for year in tuple(years)}

    entries = []
    calendars = []
    calendar_errors = []
    for year in sorted(years):
        request = TjspAcquisitionRequest(locality, "", year)
        try:
            acquired = acquire_tjsp_calendar(db, request)
            snapshots = {item["endpoint"]: get_snapshot(db, item["snapshot_id"]) for item in acquired["snapshots"]}
            composition = compose_effective_tjsp_calendar(
                snapshots[HOLIDAYS_ENDPOINT], snapshots[SUSPENSIONS_ENDPOINT], request,
                start_date=f"{year:04d}-01-01", end_date=f"{year:04d}-12-31",
                proceeding_medium="ELECTRONIC",
            )
        except Exception as exc:
            # Calendar evidence is year-scoped. A malformed/uncertain registry
            # for one year must fail closed for obligations depending on that
            # year, but it must not suppress independently calculable deadlines
            # from another year in the same process.
            calendar_errors.append({"year": year, "error": str(exc)[:2000]})
            continue
        entries.extend(composition.entries)
        calendars.append({
            "year": year, "calendar_version": composition.calendar_version,
            "coverage_complete": composition.coverage_complete,
            "missing_dates": list(composition.missing_dates),
            "snapshots": acquired["snapshots"],
        })

    result = calculate_process(db, process_id=process_id, calendar_entries=entries)
    return {
        "process_id": process_id,
        "status": "PARTIAL" if calendar_errors else "OK",
        "locality": locality,
        "calendars": calendars,
        "calendar_errors": calendar_errors,
        **result,
    }


def sync_now(
    *, process_id: str | None = None, available_to: str | None = None
) -> dict[str, Any]:
    target_date = available_to or date.today().isoformat()
    targets = [process_id] if process_id else _materialized_process_ids()
    results: list[dict[str, Any]] = []
    for pid in targets:
        state = _read_state(pid)
        available_from = (
            str(state["last_successful_sync_date"])
            if state and state.get("last_successful_sync_date")
            else _initial_available_from(pid)
        )
        if available_from > target_date:
            available_from = target_date
        db = connect_process(pid)
        try:
            result = sync_djen(
                db,
                process_id=pid,
                available_from=available_from,
                available_to=target_date,
            )
            changed_count = int(result.get("changed_count", result.get("count") or 0))
            pipeline_stale = not state or state.get("deadline_pipeline_revision") != DEADLINE_PIPELINE_REVISION
            should_rebuild = changed_count > 0 or pipeline_stale
            if not should_rebuild:
                event_result = {"process_id": pid, "materialized": 0, "deleted": 0, "skipped": "NO_DJEN_DELTA"}
                movement_instruction_result = {"process_id": pid, "materialized": 0, "deleted": 0, "skipped": "NO_DJEN_DELTA"}
                instruction_result = {"process_id": pid, "materialized": 0, "deleted": 0, "skipped": "NO_DJEN_DELTA"}
                obligation_result = {"process_id": pid, "instructions": 0, "obligations": 0, "skipped": "NO_DJEN_DELTA"}
                resolution_result = {"process_id": pid, "resolved": 0, "review_required": 0, "nonoperative": 0, "skipped": "NO_DJEN_DELTA"}
                calculation_result = {"process_id": pid, "status": "SKIPPED", "reason": "NO_DJEN_DELTA"}
            else:
                from core.documentos.participant_context_store_v1 import materialize_all as materialize_participant_context
                materialize_participant_context(db)
                event_result = materialize_process_events(db, pid)
            if should_rebuild:
                from core.documentos.deadline_instruction_store_v1 import (
                    materialize_process as materialize_movement_instructions,
                    materialize_publication_instructions,
                )
                from core.documentos.deadline_obligation_store_v1 import materialize_process as materialize_deadline_obligations
                from core.documentos.deadline_resolution_pipeline_v1 import enrich_process_obligations
                has_movements = db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='movements'"
                ).fetchone()
                if has_movements:
                    movement_instruction_result = materialize_movement_instructions(db, pid)
                else:
                    movement_instruction_result = {"process_id": pid, "materialized": 0, "deleted": 0}
                instruction_result = materialize_publication_instructions(db, pid)
                if has_movements:
                    obligation_result = materialize_deadline_obligations(db, pid)
                    resolution_result = enrich_process_obligations(db, pid)
                    try:
                        calculation_result = _calculate_tjsp_deadlines(db, pid, target_date=target_date)
                    except Exception as calculation_exc:
                        calculation_result = {
                            "process_id": pid, "status": "ERROR",
                            "error": str(calculation_exc)[:2000],
                        }
                else:
                    obligation_result = {"process_id": pid, "instructions": 0, "obligations": 0}
                    resolution_result = {"process_id": pid, "obligations": 0, "resolved": 0, "review_required": 0, "nonoperative": 0, "legal_context": None}
                    calculation_result = {"process_id": pid, "status": "SKIPPED", "reason": "MOVEMENTS_MISSING"}
        except Exception as exc:
            _write_error(pid, str(exc))
            results.append({
                "process_id": pid,
                "ok": False,
                "available_from": available_from,
                "available_to": target_date,
                "error": str(exc),
            })
            continue
        finally:
            db.close()

        sync_state = _write_success(
            pid,
            available_from=available_from,
            available_to=target_date,
            count=int(result.get("count") or 0),
        )
        results.append({
            "process_id": pid,
            "ok": True,
            "available_from": available_from,
            "available_to": target_date,
            "count": int(result.get("count") or 0),
            "process_events": event_result,
            "deadline_movement_instructions": movement_instruction_result,
            "deadline_instructions": instruction_result,
            "deadline_obligations": obligation_result,
            "deadline_resolution": resolution_result,
            "deadline_calculation": calculation_result,
            "state": sync_state,
        })
    return {
        "date": target_date,
        "ok": all(item.get("ok") for item in results) if results else True,
        "results": results,
        "status": status(as_of=target_date),
    }
