"""Offline legal reconstruction from immutable CNJ DJEN and TJSP source evidence.

Never accesses the network. Publishes generated events, instructions, obligations,
legal-rule resolution and deadlines only in the supplied (staging) SQLite DB.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

from core.documentos.publications_v1 import (
    migrate_connection as migrate_publications,
    publication_from_item,
    upsert_publication,
)
from core.documentos.court_calendar_store_v1 import (
    get_snapshot, migrate_connection as migrate_calendar,
    store_calendar_events, store_snapshot,
)
from core.documentos.providers.tjsp_calendar_acquisition_v1 import (
    HOLIDAYS_ENDPOINT, SUSPENSIONS_ENDPOINT, TjspAcquisitionRequest,
    parse_holidays, parse_suspensions, compose_effective_tjsp_calendar,
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


def _source_publications(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
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
            raise LegalReplayIncomplete("DJEN sem raw_item/query_url reproduzível: " + source["publication_id"])
        rebuilt = publication_from_item(raw, process_id=process_id, request_url=request_url)
        if (rebuilt is None or rebuilt["payload_hash"] != source["payload_hash"]
                or rebuilt["communication_id"] != source["communication_id"]
                or rebuilt["certificate_code"] != source["certificate_code"]):
            raise LegalReplayIncomplete("DJEN raw_item não corresponde ao registro original: " + source["publication_id"])
        # An explicit verified publication date, when present, is independent
        # evidence not synthesized by the CNJ availability record.
        rebuilt["published_on"] = source["published_on"]
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


def _rebuild_calendar(db: sqlite3.Connection, sources: list[Any]) -> tuple[list[Any], list[dict]]:
    pairs: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(dict)
    for expected_id, snapshot in sources:
        actual_id = store_snapshot(db, snapshot)
        if actual_id != expected_id:
            raise LegalReplayIncomplete("Identidade do snapshot TJSP não reproduzida: " + expected_id)
        params = dict(snapshot.request_params)
        request = TjspAcquisitionRequest(
            params["nomeMunicipio"], params.get("codigoMunicipio"), int(params["ano"])
        )
        if snapshot.source_endpoint == HOLIDAYS_ENDPOINT:
            parser = parse_holidays
            role = "holidays"
        elif snapshot.source_endpoint == SUSPENSIONS_ENDPOINT:
            parser = parse_suspensions
            role = "suspensions"
        else:
            raise LegalReplayIncomplete("Endpoint TJSP desconhecido: " + snapshot.source_endpoint)
        entries = parser(snapshot, request)
        store_calendar_events(db, entries, snapshot_id=actual_id)
        key = (request.nome_municipio, request.codigo_municipio or "", str(request.ano))
        # Source may contain revisions: choose latest timestamp per endpoint.
        previous = pairs[key].get(role)
        if previous is None or snapshot.fetched_at >= previous.fetched_at:
            pairs[key][role] = snapshot
    composed: list[Any] = []
    diagnostics = []
    for (municipality, code, year), pair in sorted(pairs.items()):
        if "holidays" not in pair or "suspensions" not in pair:
            diagnostics.append({"year": int(year), "status": "INCOMPLETE_SOURCE"})
            continue
        request = TjspAcquisitionRequest(municipality, code, int(year))
        value = compose_effective_tjsp_calendar(
            pair["holidays"], pair["suspensions"], request,
            start_date=f"{year}-01-01", end_date=f"{year}-12-31",
            proceeding_medium="ELECTRONIC",
        )
        composed.extend(value.entries)
        diagnostics.append({"year": int(year), "status": "OK",
                            "version": value.calendar_version,
                            "coverage_complete": value.coverage_complete})
    return composed, diagnostics


def replay_legal_sources(
    source_path: Path,
    target_path: Path,
    process_id: str,
    *,
    recalculate: bool = True,
) -> dict[str, Any]:
    """Replay legal records in an *isolated staging DB*; fail closed without network.

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
        publications = _source_publications(source, process_id)
        snapshots = _calendar_source(source)
        expected_publication_ids = {r["communication_id"] for r in publications}
        source_calendars = (
            source.execute("SELECT count(*) FROM court_calendar_events").fetchone()[0]
            if _has(source, "court_calendar_events") else 0
        )
        if source_calendars and not snapshots:
            raise LegalReplayIncomplete("Calendário materializado sem snapshots oficiais")
        history = (
            [dict(row) for row in source.execute(
                "SELECT * FROM deadline_calculations WHERE process_id=? ORDER BY calculation_id",
                (process_id,),
            )]
            if _has(source, "deadline_calculations") else []
        )
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
            entries, calendar_report = _rebuild_calendar(target, snapshots)
            target.commit()
        else:
            entries, calendar_report = [], []
        actual_ids = {
            row[0] for row in target.execute(
                "SELECT communication_id FROM publications WHERE process_id=?", (process_id,)
            )
        } if _has(target, "publications") else set()
        if expected_publication_ids != actual_ids:
            raise LegalReplayIncomplete("DJEN replay incompleto")
        if not recalculate:
            return {"publications": len(publications), "snapshots": len(snapshots),
                    "calendar": calendar_report}

        events = materialize_process_events(target, process_id)
        movement_instructions = materialize_movement_instructions(target, process_id)
        publication_instructions = materialize_publication_instructions(target, process_id)
        obligations = materialize_obligations(target, process_id)
        resolution = enrich_process_obligations(target, process_id)
        calculated = calculate_process(
            target, process_id=process_id, calendar_entries=entries,
        )
        # Historical calculation versions are immutable audit evidence; they
        # are not reused to compute the new operative deadline. Carry them
        # only when both original obligation and communication remain valid.
        calculations_historic = 0
        if history:
            columns = list(history[0])
            current_obligations = {
                row[0] for row in target.execute(
                    "SELECT obligation_id FROM deadline_obligations WHERE process_id=?",
                    (process_id,),
                )
            }
            current_event_ids = {row[0] for row in target.execute(
                "SELECT event_id FROM process_events WHERE process_id=?", (process_id,)
            )}
            if any(item["obligation_id"] not in current_obligations or
                   (item["communication_event_id"] and
                    item["communication_event_id"] not in current_event_ids)
                   for item in history):
                raise LegalReplayIncomplete("Histórico de cálculos possui referências incompatíveis")
            insert = ("INSERT OR IGNORE INTO deadline_calculations (" +
                      ",".join(columns) + ") VALUES (" +
                      ",".join("?" for _ in columns) + ")")
            for item in history:
                if target.execute(
                    "SELECT 1 FROM deadline_calculations WHERE calculation_id=?",
                    (item["calculation_id"],),
                ).fetchone():
                    continue
                target.execute(insert, tuple(item[c] for c in columns))
                calculations_historic += 1
        foreign = target.execute("PRAGMA foreign_key_check").fetchall()
        if foreign:
            raise LegalReplayIncomplete(f"Replay gerou {len(foreign)} violações FK")
        target.commit()
        return {
            "publications": len(publications),
            "calendar_snapshots": len(snapshots),
            "calendar": calendar_report,
            "events": events,
            "movement_instructions": movement_instructions,
            "publication_instructions": publication_instructions,
            "obligations": obligations,
            "resolution": resolution,
            "calculated": {
                "obligations": calculated["obligations"],
                "status_counts": calculated["status_counts"],
                "historical_versions_preserved": calculations_historic,
            },
        }
