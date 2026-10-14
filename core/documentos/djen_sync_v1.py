"""Operational DJEN synchronization state and daily/manual orchestration."""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from typing import Any

from core.process_storage import connect_process, connect_workspace, known_process_ids
from core.runtime_paths import process_db_path, workspace_db_path
from core.documentos.publications_v1 import sync_djen

DEADLINE_PIPELINE_REVISION = "deadline-pipeline-v5"

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


def _calculate_tjsp_deadlines(db: sqlite3.Connection, process_id: str, *, target_date: str, prepare_only: bool = False) -> dict[str, Any]:
    """Reuse verified official evidence, acquire gaps and abstain on any gap."""
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='process_metadata'").fetchone():
        return {"process_id": process_id, "status": "INCOMPLETE", "reason": "PROCESS_METADATA_MISSING"}
    columns = {str(row[1]) for row in db.execute("PRAGMA table_info(process_metadata)").fetchall()}
    if not {"tribunal", "comarca"} <= columns:
        return {"process_id": process_id, "status": "INCOMPLETE", "reason": "COURT_METADATA_MISSING"}
    metadata = db.execute(
        "SELECT tribunal,comarca FROM process_metadata WHERE process_id=?", (process_id,)
    ).fetchone()
    if not metadata or str(metadata["tribunal"] or "").upper().strip() != "TJSP":
        return {"process_id": process_id, "status": "INCOMPLETE", "reason": "UNSUPPORTED_COURT"}

    locality = str(metadata["comarca"] or "").strip()
    for prefix in ("Foro de ", "Comarca de "):
        if locality.casefold().startswith(prefix.casefold()):
            locality = locality[len(prefix):].strip()
            break
    if not locality:
        return {"process_id": process_id, "status": "INCOMPLETE", "reason": "LOCALITY_MISSING"}

    from core.documentos.court_calendar_store_v1 import get_snapshot, migrate_connection as migrate_calendar
    from core.documentos.deadline_calculation_store_v1 import calculate_process
    from core.documentos.providers.tjsp_calendar_acquisition_v1 import (
        HOLIDAYS_ENDPOINT, SUSPENSIONS_ENDPOINT, TjspAcquisitionRequest,
        acquire_tjsp_calendar, compose_effective_tjsp_calendar,
    )

    migrate_calendar(db)
    years: set[int] = {int(target_date[:4])}
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='publications'").fetchone():
        columns = {row[1] for row in db.execute("PRAGMA table_info(publications)")}
        if "process_id" in columns:
            rows = db.execute(
                "SELECT DISTINCT coalesce(published_on,available_on) AS communication_date "
                "FROM publications WHERE process_id=? AND coalesce(active,1)<>0", (process_id,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT DISTINCT coalesce(p.published_on,p.available_on) AS communication_date "
                "FROM deadline_instructions i JOIN publications p ON p.publication_id=i.source_id "
                "WHERE i.process_id=? AND i.source_entity='PUBLICATION' AND coalesce(p.active,1)<>0",
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
            from core.documentos.legal_replay_v1 import _calendar_source
            cached = {}
            for sid, snapshot in _calendar_source(db):
                if dict(snapshot.request_params) == request.query_params:
                    previous = cached.get(snapshot.source_endpoint)
                    if previous is None or snapshot.fetched_at >= previous[1].fetched_at:
                        cached[snapshot.source_endpoint] = (sid, snapshot)
            acquired = acquire_tjsp_calendar(db, request, cached_snapshots={
                endpoint: value[1] for endpoint, value in cached.items()
            })
            snapshots = {item["endpoint"]: get_snapshot(db, item["snapshot_id"]) for item in acquired["snapshots"]}
            composition = compose_effective_tjsp_calendar(
                snapshots[HOLIDAYS_ENDPOINT], snapshots[SUSPENSIONS_ENDPOINT], request,
                start_date=f"{year:04d}-01-01", end_date=f"{year:04d}-12-31",
                proceeding_medium="ELECTRONIC",
            )
        except Exception as exc:
            calendar_errors.append({"year": year, "error": str(exc)[:2000]})
            continue
        if not composition.coverage_complete:
            calendar_errors.append({"year": year, "error": "INCOMPLETE_CALENDAR_COVERAGE"})
            continue
        entries.extend(composition.entries)
        calendars.append({
            "year": year, "calendar_version": composition.calendar_version,
            "coverage_complete": composition.coverage_complete,
            "missing_dates": list(composition.missing_dates),
            "snapshots": acquired["snapshots"],
        })

    # Keep verified years available to the canonical deadline engine: it
    # already abstains, per obligation, when any date it needs is uncovered.
    # An unrelated historical gap must not invalidate a proven calculation.
    result = ({"calendar_entries": entries} if prepare_only else
              calculate_process(db, process_id=process_id, calendar_entries=entries))
    return {
        "process_id": process_id,
        "status": ("PARTIAL" if entries else "INCOMPLETE") if calendar_errors else "OK",
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
        available_from = None
        db = connect_process(pid)
        try:
            from core.process_cycle import sync_process_legal, _initial_date
            available_from = (str(state["last_successful_sync_date"])
                              if state and state.get("last_successful_sync_date") else _initial_date(db, pid))
            if available_from > target_date:
                available_from = target_date
            result = sync_process_legal(db, pid, available_from=available_from, available_to=target_date,
                                        project=False)
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
                projection = sync_process_legal(db, pid, available_to=target_date, acquire=False)
                event_result = projection["events"]
                movement_instruction_result = projection["movement_instructions"]
                instruction_result = projection["publication_instructions"]
                obligation_result = projection["obligations"]
                resolution_result = projection["resolution"]
                calculation_result = projection["calculated"]
                if projection["status"] != "READY":
                    raise RuntimeError("Evidência jurídica incompleta: " + json.dumps(calculation_result, ensure_ascii=False))
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
