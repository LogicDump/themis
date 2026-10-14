"""Core orchestration after acquisition, shared by creation and staged rebuild."""
from __future__ import annotations

import json
import os
import uuid
from contextlib import closing
from datetime import date
from pathlib import Path

from core.documentos.legal_replay_v1 import (
    LegalReplayIncomplete, _source_publications, project_legal_state, replay_legal_sources,
)


def sync_process_legal(db, cnj: str, *, available_to: str,
                       available_from: str | None = None, acquire: bool = True,
                       project: bool = True) -> dict:
    """Compatibility adapter; the Core facade owns every domain's orchestration."""
    return process_after_acquisition(None, cnj, db=db, documents=False, available_to=available_to,
                                     available_from=available_from, acquire=acquire, project=project)


def _sync_process_legal(db, cnj: str, *, available_to: str,
                        available_from: str | None = None, acquire: bool = True,
                        project: bool = True) -> dict:
    from core.documentos.djen_sync_v1 import _calculate_tjsp_deadlines
    from core.documentos.djen_sync_v1 import sync_djen
    result = {}
    if acquire:
        result = sync_djen(db, process_id=cnj, available_from=available_from or _initial_date(db, cnj),
                           available_to=available_to)
    if project:
        _source_publications(db, cnj)
        evidence = _calculate_tjsp_deadlines(db, cnj, target_date=available_to, prepare_only=True)
        projection = project_legal_state(db, cnj, calendar_entries=evidence.get("calendar_entries", []),
                                         calendar_report=evidence)
        result.update(projection)
        result["process_events"] = projection["events"]
    return result


def _initial_date(db, cnj: str) -> str:
    from core.documentos.djen_sync_v1 import _parse_distribution_date
    row = db.execute("SELECT provenance_json FROM process_metadata WHERE process_id=?", (cnj,)).fetchone()
    metadata = json.loads(row[0] or "{}") if row else {}
    initial = _parse_distribution_date((metadata.get("basic_data") or {}).get("distribuicao"))
    if initial is None:
        raise LegalReplayIncomplete("DJEN sem intervalo inicial comprovado por fonte primária")
    return initial


def process_after_acquisition(store, cnj: str, *, source_db: Path | None = None,
                              db=None, documents: bool = True, available_to: str | None = None,
                              available_from: str | None = None, acquire: bool = True,
                              project: bool = True) -> dict:
    """Single Core facade: source acquisition, requested domains and projection."""
    from core.runtime_paths import validate_process_id
    cnj = validate_process_id(cnj)
    today = available_to or date.today().isoformat()
    if not documents:
        if db is None:
            raise ValueError("Conexão do Process Package obrigatória para domínio jurídico")
        return _sync_process_legal(db, cnj, available_to=today, available_from=available_from,
                                   acquire=acquire, project=project)
    from core.bridge.sync_service import _process_captured_documents, _finalize_process_package
    from core.documentos.djen_sync_v1 import _calculate_tjsp_deadlines

    store = store.for_process(cnj)
    evidence = {"status": "INCOMPLETE"}
    try:
        seeded = None
        if source_db is not None and Path(source_db).is_file():
            seeded = replay_legal_sources(source_db, store.db_path, cnj, recalculate=False)
        with closing(store.connect()) as db:
            publications = _source_publications(db, cnj, allow_missing=source_db is None)
            if source_db is None or not publications or (seeded and seeded.get("missing_publications")):
                _sync_process_legal(db, cnj, available_to=today, available_from=available_from, project=False)
                recovered = _source_publications(db, cnj)
                recovered_keys = {(item["communication_id"], item["certificate_code"]) for item in recovered}
                if seeded and set(map(tuple, seeded.get("expected_sources", []))) - recovered_keys:
                    raise LegalReplayIncomplete("DJEN: fontes primárias faltantes não recuperadas na consulta oficial")
            evidence = _calculate_tjsp_deadlines(db, cnj, target_date=today, prepare_only=True)
    except (LegalReplayIncomplete, ValueError, KeyError) as exc:
        evidence = {"status": "INCOMPLETE", "error": str(exc)}
    except Exception as exc:
        # Acquisition failures are evidence gaps, never permission to invent dates.
        evidence = {"status": "INCOMPLETE", "error": str(exc)}

    if evidence["status"] not in {"OK", "PARTIAL"}:
        result = {"status": "INCOMPLETE", "cnj": cnj, "legal_evidence": evidence}
        # Use the canonical calculator to withdraw operative dates when the
        # official inputs cannot support them (not an alternative deadline rule).
        from core.documentos.deadline_calculation_store_v1 import calculate_process
        with closing(store.connect()) as db:
            result["abstention"] = calculate_process(db, process_id=cnj, calendar_entries=[])
            db.execute("UPDATE processes SET status='INCOMPLETE' WHERE process_id=?", (cnj,))
            db.commit()
    else:
        result = _process_captured_documents(store, cnj)
        with closing(store.connect()) as db:
            legal = project_legal_state(
                db, cnj, calendar_entries=evidence["calendar_entries"], calendar_report=evidence,
            )
        result["legal"] = legal
        result["status"] = legal["status"]
    path = store.process_manifest_path(cnj)
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    manifest["legal_status"] = result.get("legal", {}).get("legal_status", result["status"])
    manifest["state"] = result["status"]
    manifest["legal_evidence"] = {k: v for k, v in evidence.items() if k != "calendar_entries"}
    if result["status"] == "INCOMPLETE":
        manifest["status"] = manifest["pipeline_status"] = "INCOMPLETE"
        manifest["pipeline_progress"] = {"phase": "INCOMPLETE", "pipeline_status": "INCOMPLETE",
                                         "error": "Evidência jurídica oficial insuficiente"}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    if result["status"] == "READY":
        package = _finalize_process_package(store, cnj)
        if "stages" in result:
            result["stages"]["PACKAGE"] = {"status": "OK", **package}
            result["stages"]["READY"] = {"status": "OK"}
    return result
