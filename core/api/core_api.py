"""API read-only do banco process-centric v2."""
from __future__ import annotations
import json
import re
import sqlite3
from pathlib import Path
from core.runtime_paths import index_db_path, process_db_path
from core.documentos.themis_documentos import Store
from core.documentos.procedural_acts_v1 import project_procedural_acts
from core.documentos.movement_store_v1 import read_movements
from core.documentos.movement_summary_store_v1 import current as current_movement_summary, current_v2_analysis as current_movement_v2_analysis, source_pages, source_text_and_hash, versions as movement_summary_versions, save as save_movement_summary
from core.documentos.case_synthesis_store_v1 import (
    JOBS_MIGRATION_VERSION as CASE_SYNTHESIS_JOBS_MIGRATION_VERSION,
    complete_job_with_synthesis as complete_case_synthesis_job,
    create_job_if_absent as create_case_synthesis_job_if_absent,
    current as current_case_synthesis,
    dependency_hash as case_synthesis_dependency_hash,
    job as current_case_synthesis_job,
    latest_job as latest_case_synthesis_job,
    migrate_connection as migrate_case_synthesis,
    save as save_case_synthesis,
    save_job as save_case_synthesis_job,
    versions as case_synthesis_versions,
)
from core.documentos.process_event_store_v1 import list_process_events as list_temporal_events
from core.documentos.deadline_instruction_store_v1 import list_instructions as list_deadline_instructions
from core.documentos.deadline_obligation_store_v1 import list_obligations as list_deadline_obligations
from core.documentos.participant_context_store_v1 import (
    migrate_connection as migrate_participant_context,
    list_participants as list_process_participants,
    list_representations as list_process_representations,
    get_profile as get_professional_profile,
    save_profile as save_professional_profile,
    get_context as get_user_process_context,
    save_context as save_user_process_context,
)
from core.documentos.pecas_manifest_v1 import load_pecas_manifest
from core.documentos.autos_context_v1 import decode as decode_autos_context, process_is_complete

def _db(path: Path | None = None):
    target = (path or index_db_path()).resolve().as_uri() + "?mode=ro"
    db = sqlite3.connect(target, uri=True); db.row_factory = sqlite3.Row; return db

def _process_db(pid: str, path: Path | None = None):
    if path is not None:
        return _db(path)
    try:
        return _db(process_db_path(pid))
    except ValueError:
        # Keep synthetic/non-CNJ fixture and legacy adapter compatibility;
        # real process identities always route to their isolated package.
        return _db(index_db_path())

def _record_db(table: str, key: str, value: str, path: Path | None = None):
    if path is not None:
        return _db(path)
    process_id = _record_process_id(table, key, value)
    if process_id is None:
        raise FileNotFoundError(f"Registro {table}.{key} não localizado em nenhum Process Package")
    return _process_db(process_id)

def _record_process_id(table: str, key: str, value: str) -> str | None:
    from core.process_storage import locate_process_for_record
    return locate_process_for_record(table, key, value)

def _process_package_schema_is_current(target: Path) -> bool:
    """Check migration markers without taking a writer lock on a healthy package."""
    from core.documentos import (
        case_synthesis_store_v1,
        deadline_calculation_store_v1,
        deadline_instruction_store_v1,
        deadline_obligation_store_v1,
        participant_context_store_v1,
        process_event_store_v1,
        publications_v1,
    )
    from core.documentos import movement_summary_store_v1 as summary_store
    from core.retrieval import summary_embedding_store

    expected = {
        summary_store.MIGRATION_VERSION,
        summary_store.FORWARD_MIGRATION_VERSION,
        summary_store.ANALYSIS_V2_MIGRATION_VERSION,
        summary_store.ANALYSIS_V2_JOBS_MIGRATION_VERSION,
        summary_store.ANALYSIS_V2_WORKER_MIGRATION_VERSION,
        summary_embedding_store.MIGRATION_VERSION,
        case_synthesis_store_v1.MIGRATION_VERSION,
        case_synthesis_store_v1.JOBS_MIGRATION_VERSION,
        process_event_store_v1.MIGRATION_VERSION,
        deadline_instruction_store_v1.MIGRATION_VERSION,
        deadline_obligation_store_v1.MIGRATION_VERSION,
        deadline_calculation_store_v1.MIGRATION_VERSION,
        participant_context_store_v1.MIGRATION_VERSION,
        publications_v1.MIGRATION,
    }
    uri = target.resolve().as_uri() + "?mode=ro"
    try:
        db = sqlite3.connect(uri, uri=True)
    except sqlite3.Error:
        return False
    try:
        if not db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        ).fetchone():
            return False
        applied = {str(row[0]) for row in db.execute("SELECT version FROM schema_migrations")}
        has_source_tables = all(
            db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
            for name in ("pages", "documents")
        )
        if has_source_tables:
            expected.add(summary_store.STATUS_SOURCE_MIGRATION_VERSION)
        return expected.issubset(applied) and str(db.execute("PRAGMA journal_mode").fetchone()[0]).lower() == "wal"
    except sqlite3.Error:
        return False
    finally:
        db.close()


def bootstrap_database() -> dict:
    """Bring all materialized Themis stores to the current schema.

    Compatibility facade: dashboard/plugin_api.py historically invokes this
    during plugin import. Migration orchestration now lives in one module.
    """
    from core.migration_manager import migrate_all
    return migrate_all()

def _movement_node(row: dict, process_id: str) -> dict:
    source_datetime = row.get("source_datetime")
    occurred = source_datetime
    date_str = str(occurred)[:10] if occurred else "Data s/ ref"
    m_type = row.get("movement_type") or "Movimentação"
    source_ref = row.get("source_ref") or {}
    return {
        "id": f"movement:{row['movement_id']}",
        "node_type": "movement_item",
        "process_id": process_id,
        "movement_id": row["movement_id"],
        "label": f"{date_str} - {m_type}",
        "kind": "movement",
        "movement_type": row.get("movement_type"),
        "source_datetime": source_datetime,
        "content": row.get("description") or row.get("content"),
        "source_ref": source_ref,
    }


def _data_root_for_db(path: Path | None) -> Path | None:
    if path:
        db_path = Path(path).resolve()
        for candidate in (db_path.parent, db_path.parent.parent, db_path.parent.parent.parent):
            if (candidate / "processos").is_dir():
                return candidate
        if db_path.parent.name == "index":
            return db_path.parent.parent
    try:
        from core.runtime_paths import themis_data_root
        return themis_data_root()
    except Exception:
        return None


def _file_node(row: sqlite3.Row, process_id: str) -> dict:
    filename = Path(row["path"]).name or f"documento_{row['document_id'][:8]}"
    return {"id": f"file:{row['document_id']}", "node_type": "document", "document_id": row["document_id"], "process_id": process_id, "label": filename, "kind": "file", "mime_type": "application/pdf", "size_bytes": row["size_bytes"], "page_count": row["page_count"], "url": f"/api/v1/themis/documents/{row['document_id']}/raw"}

def health(path=None):
    db=_db(path)
    try: return {"status":"ok","database":"process-centric-v2","integrity_check":db.execute("PRAGMA integrity_check").fetchone()[0]}
    finally: db.close()

def _process_node(db: sqlite3.Connection, pid: str) -> dict:
    process_row = db.execute(
        "SELECT status FROM processes WHERE process_id=?", (pid,)
    ).fetchone()
    doc_rows=db.execute("SELECT d.document_id,f.size_bytes,d.page_count,d.status,f.path FROM documents d JOIN files f USING(file_id) WHERE d.process_id=? ORDER BY f.path",(pid,)).fetchall()
    db_path_row = db.execute("PRAGMA database_list").fetchone()
    db_path = Path(db_path_row[2]) if db_path_row and db_path_row[2] else None
    mov_rows = movements(pid, path=db_path) or []
    autos={"id":f"folder:process:{pid}:autos","node_type":"process_autos","label":"Autos","kind":"autos","process_id":pid}
    movement_collection={
        "id":f"folder:process:{pid}:movements",
        "node_type":"movement_collection",
        "label":"Movimentações",
        "kind":"folder",
        "process_id":pid,
        "children":[_movement_node(row,pid) for row in mov_rows],
    }
    docs={"id":f"folder:process:{pid}:documents","node_type":"document_collection","process_id":pid,"label":"Documentos","kind":"folder","children":[_file_node(row,pid) for row in doc_rows]}
    pipeline_status = process_row["status"] if process_row else None
    pipeline_revision = None
    pipeline_error = None
    pipeline_progress = {}
    data_root = _data_root_for_db(db_path)
    if data_root:
        manifest_path = data_root / "processos" / pid / "manifest.json"
        if manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                progress = manifest.get("pipeline_progress") or {}
                pipeline_progress = progress
                pipeline_status = progress.get("pipeline_status") or manifest.get("pipeline_status") or pipeline_status
                pipeline_revision = progress.get("updated_at")
                pipeline_error = progress.get("error")
            except Exception:
                pass
    return {
        "id": pid,
        "node_type": "process",
        "process_id": pid,
        "label": pid,
        "kind": "process",
        "status": process_row["status"] if process_row else None,
        "pipeline_status": pipeline_status,
        "pipeline_revision": pipeline_revision,
        "pipeline_error": pipeline_error,
        "pipeline_progress": pipeline_progress,
        "children": [autos, movement_collection, docs],
    }

def tree(path=None):
    if path is not None:
        db=_db(path)
        try: return {"processes":[_process_node(db,row["process_id"]) for row in db.execute("SELECT process_id FROM processes ORDER BY process_id")],"read_only":True}
        finally: db.close()
    from core.process_storage import known_process_ids
    nodes=[]
    for pid in known_process_ids():
        db=_process_db(pid)
        try:
            if db.execute("SELECT 1 FROM processes WHERE process_id=?",(pid,)).fetchone(): nodes.append(_process_node(db,pid))
        finally: db.close()
    return {"processes":nodes,"read_only":True}

def overview(pid: str, path: Path | None = None) -> dict | None:
    db = _process_db(pid,path)
    try:
        proc_row = db.execute("SELECT process_id, status, created_at FROM processes WHERE process_id=?", (pid,)).fetchone()
        if not proc_row:
            return None
        has_party_relations = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='party_relations'").fetchone() is not None
        has_legal_entities = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='legal_entities'").fetchone() is not None
        participants = []
        if has_party_relations and has_legal_entities:
            pr_rows = db.execute(
                """SELECT pr.role, pr.role_raw, le.entity_id, le.entity_type, le.display_name, le.identifiers_json
                FROM party_relations pr
                JOIN legal_entities le USING(entity_id)
                WHERE pr.owner_type='PROCESS' AND pr.owner_id=?
                ORDER BY pr.role, le.display_name""",
                (pid,),
            ).fetchall()
            participant_by_entity: dict[str, dict] = {}
            for r in pr_rows:
                role = r["role"] or r["role_raw"] or "PARTE"
                role_raw = str(r["role_raw"] or "")
                role_text = re.sub(r"[^A-Z]", "", str(role).upper())
                is_lawyer = role_text in {"ADVOGADO", "ADVOGADA", "LAWYER"} or role_raw.upper().startswith("ADVOGAD")
                entity_key = str(r["entity_id"])
                p_item = participant_by_entity.get(entity_key)
                if p_item is None:
                    try:
                        identifiers = json.loads(r["identifiers_json"]) if r["identifiers_json"] else {}
                    except Exception:
                        identifiers = {}
                    p_item = {
                        "role": "ADVOGADO" if is_lawyer else role,
                        "role_raw": role_raw,
                        "entity_id": r["entity_id"],
                        "entity_type": r["entity_type"],
                        "display_name": r["display_name"],
                        "identifiers": identifiers,
                        "additional_roles": [],
                        "role_raws": [],
                        "represented_parties": [],
                        "_roles": [],
                    }
                    participant_by_entity[entity_key] = p_item
                    participants.append(p_item)

                normalized_role = "ADVOGADO" if is_lawyer else str(role)
                if normalized_role not in p_item["_roles"]:
                    p_item["_roles"].append(normalized_role)
                if is_lawyer:
                    if role_raw and role_raw not in p_item["role_raws"]:
                        p_item["role_raws"].append(role_raw)
                    represented = re.search(r"\(([^()]*)\)", role_raw)
                    if represented:
                        represented_name = represented.group(1).strip()
                        if represented_name and represented_name.casefold() not in {
                            item.casefold() for item in p_item["represented_parties"]
                        }:
                            p_item["represented_parties"].append(represented_name)
                elif p_item["role"] == "ADVOGADO":
                    # Keep the process-party role as the primary label when an
                    # entity is both a party and counsel; expose counsel below
                    # as an additional role on the same rendered participant.
                    p_item["role"] = role
                    p_item["role_raw"] = role_raw

            for p_item in participants:
                primary_role = re.sub(r"[^A-Z]", "", str(p_item.get("role") or "").upper())
                p_item["additional_roles"] = [role for role in p_item.pop("_roles") if re.sub(r"[^A-Z]", "", role.upper()) != primary_role]

            # Preserve the cover's semantic order: claimant + lawyer,
            # respondent + lawyer, legal representative, then other parties.
            # One entity is one displayed participant even when it has multiple
            # roles. This only shapes the overview projection, not persisted facts.
            def _base_rank(item):
                role = re.sub(r"[^A-Z]", "", str(item.get("role") or "").upper())
                if role in {"REQTE", "REQUERENTE", "AUTOR", "CLAIMANT"}:
                    return 0
                if role in {"REQDA", "REQUERIDO", "REU", "RESPONDENT"}:
                    return 1
                if role in {"REPRELEG", "REPRESENTANTE", "LEGALGUARDIAN"}:
                    return 2
                return 3

            def _participant_group(item):
                role = re.sub(r"[^A-Z]", "", str(item.get("role") or "").upper())
                raw = str(item.get("role_raw") or "")
                if role in {"ADVOGADO", "ADVOGADA", "LAWYER"} or raw.upper().startswith("ADVOGAD"):
                    targets = [str(name).casefold() for name in item.get("represented_parties", [])]
                    parent_rank = min((base_rank_by_name.get(target, 3) for target in targets), default=3)
                    return (parent_rank, 1, targets[0] if targets else "", item.get("display_name", "").casefold())
                return (_base_rank(item), 0, "", item.get("display_name", "").casefold())

            base_rank_by_name = {
                item["display_name"].casefold()
                : _base_rank(item)
                for item in participants
                if not str(item.get("role_raw") or "").upper().startswith("ADVOGAD")
            }
            ordered = []
            for item in participants:
                key = _participant_group(item)
                if key[1] == 1 and key[2] not in base_rank_by_name:
                    key = (3, 1, key[2], key[3])
                ordered.append((key, item))
            participants = [item for _, item in sorted(ordered, key=lambda pair: pair[0])]
        has_sources = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='process_sources'").fetchone() is not None
        sources = []
        if has_sources:
            sources_rows = db.execute(
                "SELECT source_type, source_id, created_at FROM process_sources WHERE process_id=? ORDER BY created_at",
                (pid,),
            ).fetchall()
            sources = [dict(r) for r in sources_rows]

        doc_count = db.execute("SELECT count(*), coalesce(sum(page_count), 0) FROM documents WHERE process_id=?", (pid,)).fetchone()
        db_path_row = db.execute("PRAGMA database_list").fetchone()
        db_path = Path(db_path_row[2]) if db_path_row and db_path_row[2] else path
        mov_count = len(movements(pid, db_path) or [])

        has_strategy = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='strategy_entries'").fetchone() is not None
        strategy_items = []
        if has_strategy:
            strat_rows = db.execute(
                "SELECT strategy_id, title, content, entry_type, status, author_type, confidence, version FROM strategy_entries WHERE owner_type='PROCESS' AND owner_id=? ORDER BY version DESC, rowid",
                (pid,),
            ).fetchall()
            strategy_items = [dict(r) for r in strat_rows]

        has_pending = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='pending_items'").fetchone() is not None
        pending_items = []
        if has_pending:
            pend_rows = db.execute(
                "SELECT pending_id, title, description, status, priority, due_at FROM pending_items WHERE owner_type='PROCESS' AND owner_id=? ORDER BY rowid",
                (pid,),
            ).fetchall()
            pending_items = [dict(r) for r in pend_rows]

        has_deadlines = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='deadlines'").fetchone() is not None
        deadlines = []
        if has_deadlines:
            dead_rows = db.execute(
                "SELECT deadline_id, title, description, due_at, status, priority, term FROM deadlines WHERE owner_type='PROCESS' AND owner_id=? ORDER BY rowid",
                (pid,),
            ).fetchall()
            deadlines = [dict(r) for r in dead_rows]

        has_hearings = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='hearings'").fetchone() is not None
        hearings = []
        if has_hearings:
            h_rows = db.execute(
                "SELECT hearing_id, hearing_type, scheduled_at, location, meeting_info, status, outcome_notes FROM hearings WHERE process_id=? ORDER BY scheduled_at",
                (pid,),
            ).fetchall()
            hearings = [dict(r) for r in h_rows]

        has_metadata = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='process_metadata'").fetchone() is not None
        metadata = {}
        if has_metadata:
            meta_row = db.execute("SELECT * FROM process_metadata WHERE process_id=?", (pid,)).fetchone()
            if meta_row:
                metadata = dict(meta_row)
                try:
                    metadata["provenance"] = json.loads(meta_row["provenance_json"]) if meta_row["provenance_json"] else {}
                except Exception:
                    metadata["provenance"] = {}

        pipeline_progress = None
        data_root = None
        if path:
            candidate_roots = [path.parent, path.parent.parent, path.parent.parent.parent]
            for cr in candidate_roots:
                if (cr / "processos").exists():
                    data_root = cr
                    break
        if data_root is None and not path:
            try:
                from core.runtime_paths import themis_data_root
                data_root = themis_data_root()
            except Exception:
                data_root = None

        if data_root:
            proc_manifest = data_root / "processos" / pid / "manifest.json"
            if proc_manifest.is_file():
                try:
                    mdata = json.loads(proc_manifest.read_text(encoding="utf-8"))
                    pipeline_progress = mdata.get("pipeline_progress")
                except Exception:
                    pass

        return {
            "process_id": pid,
            "status": proc_row["status"],
            "pipeline_progress": pipeline_progress,
            "pipeline_status": pipeline_progress.get("pipeline_status") if pipeline_progress else ("READY" if proc_row["status"] == "ACTIVE" else proc_row["status"]),
            "created_at": proc_row["created_at"],
            "document_count": doc_count[0] if doc_count else 0,
            "total_pages": doc_count[1] if doc_count else 0,
            "movement_count": mov_count,
            "strategy_count": len(strategy_items),
            "pending_count": len(pending_items),
            "deadline_count": len(deadlines),
            "hearing_count": len(hearings),
            "metadata": metadata,
            "strategy_items": strategy_items,
            "pending_items": pending_items,
            "deadlines": deadlines,
            "hearings": hearings,
            "participants": participants,
            "sources": sources,
        }
    finally:
        db.close()

def process(pid, path=None):
    db=_process_db(pid,path)
    try:
        return _process_node(db,pid) if db.execute("SELECT 1 FROM processes WHERE process_id=?",(pid,)).fetchone() else None
    finally: db.close()

def movements(pid: str, path: Path | None = None) -> list[dict] | None:
    db = _process_db(pid,path)
    try:
        if not db.execute("SELECT 1 FROM processes WHERE process_id=?", (pid,)).fetchone():
            return None
        return read_movements(db, pid)
    finally:
        db.close()

def process_participants(pid: str, path: Path | None = None) -> list[dict] | None:
    db = _process_db(pid,path)
    try:
        if not db.execute("SELECT 1 FROM processes WHERE process_id=?", (pid,)).fetchone():
            return None
        return list_process_participants(db, pid)
    finally:
        db.close()

def process_representations(pid: str, path: Path | None = None) -> list[dict] | None:
    db = _process_db(pid,path)
    try:
        if not db.execute("SELECT 1 FROM processes WHERE process_id=?", (pid,)).fetchone():
            return None
        return list_process_representations(db, pid)
    finally:
        db.close()

def professional_profile(profile_id: str = "profile_local_default", path: Path | None = None) -> dict | None:
    if path is None:
        from core.process_storage import connect_workspace
        db=connect_workspace(create=True)
    else:
        db = _db(path)
    try:
        return get_professional_profile(db, profile_id)
    finally:
        db.close()

def save_professional_profile_record(payload: dict[str, Any], path: Path | None = None) -> dict:
    if path is None:
        from core.process_storage import connect_workspace
        db=connect_workspace(create=True)
    else:
        db = sqlite3.connect(str(path)); db.row_factory = sqlite3.Row
    try:
        return save_professional_profile(db, payload)
    finally:
        db.close()

def user_process_context(pid: str, profile_id: str, path: Path | None = None) -> dict | None:
    db = _process_db(pid,path)
    try:
        if not db.execute("SELECT 1 FROM processes WHERE process_id=?", (pid,)).fetchone():
            return None
        return get_user_process_context(db, pid, profile_id)
    finally:
        db.close()

def save_user_process_context_record(pid: str, payload: dict[str, Any], path: Path | None = None) -> dict:
    db_path = path or process_db_path(pid)
    db = sqlite3.connect(str(db_path)); db.row_factory = sqlite3.Row
    try:
        migrate_participant_context(db)
        from core.process_storage import sync_workspace_profiles
        sync_workspace_profiles(db, root=path.parent.parent if path else None)
        return save_user_process_context(db, pid, payload)
    finally:
        db.close()

def movement_summary(movement_id: str, path: Path | None = None) -> dict | None:
    db = _record_db("movements","movement_id",movement_id,path)
    try:
        return current_movement_summary(db, movement_id)
    finally:
        db.close()


def process_movement_summaries(pid: str, path: Path | None = None) -> dict[str, dict] | None:
    """Read current Movement summaries with one process-local read connection."""
    db = _process_db(pid, path)
    try:
        if not db.execute("SELECT 1 FROM processes WHERE process_id=?", (pid,)).fetchone():
            return None
        rows = db.execute("""SELECT s.summary_id,s.movement_id,s.summary_version,s.summary_text,
                    s.prompt_version,s.purpose,s.provider,s.model,s.usage_json,s.source_hash,s.generated_at
                FROM movement_summaries s JOIN movements m ON m.movement_id=s.movement_id
                WHERE m.process_id=? AND s.summary_version=(
                    SELECT max(latest.summary_version) FROM movement_summaries latest
                    WHERE latest.movement_id=s.movement_id)""", (pid,)).fetchall()
        result = {}
        for row in rows:
            item = dict(row)
            item["usage"] = json.loads(item.pop("usage_json")) if item["usage_json"] else None
            result[item["movement_id"]] = item
        return result
    finally:
        db.close()


def process_summary_status(pid: str, path: Path | None = None) -> dict | None:
    """Read persisted source metadata, latest summaries and job without source text or reconciliation."""
    from core.documentos.movement_summary_store_v1 import analysis_v2_job
    db = _process_db(pid, path)
    try:
        db.execute("PRAGMA busy_timeout=250")
        if not db.execute("SELECT 1 FROM processes WHERE process_id=?", (pid,)).fetchone():
            return None
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='movement_summary_source_state'").fetchone():
            raise RuntimeError("movement_summary_source_state migration is required")
        rows = db.execute("""SELECT m.movement_id, state.eligible, state.source_hash AS current_source_hash,
                    s.source_hash AS summary_source_hash, s.summary_text
                FROM movements m LEFT JOIN movement_summary_source_state state ON state.movement_id=m.movement_id
                LEFT JOIN movement_summaries s ON s.movement_id=m.movement_id AND s.summary_version=(
                    SELECT max(latest.summary_version) FROM movement_summaries latest
                    WHERE latest.movement_id=m.movement_id)
                WHERE m.process_id=?""", (pid,)).fetchall()
        counts = {"total": len(rows), "current": 0, "missing": 0, "stale": 0,
                  "total_eligible": 0, "v2_completed": 0, "v2_pending": 0}
        for row in rows:
            current = bool(
                row["summary_source_hash"]
                and row["current_source_hash"]
                and row["summary_source_hash"] == row["current_source_hash"]
                and str(row["summary_text"] or "").strip()
            )
            if row["summary_source_hash"] is None:
                counts["missing"] += 1
            elif current:
                counts["current"] += 1
            else:
                counts["stale"] += 1
            if not row["eligible"]:
                continue
            counts["total_eligible"] += 1
            if current:
                counts["v2_completed"] += 1
        counts["v2_pending"] = counts["total_eligible"] - counts["v2_completed"]
        counts["job"] = analysis_v2_job(db, pid)
        return counts
    finally:
        db.close()

def movement_analysis_v2_current(movement_id: str, path: Path | None = None) -> dict | None:
    db = _record_db("movements", "movement_id", movement_id, path)
    try:
        return current_movement_v2_analysis(db, movement_id)
    finally:
        db.close()

def movement_summary_versions_list(movement_id: str, path: Path | None = None) -> list[dict]:
    db = _record_db("movements","movement_id",movement_id,path)
    try:
        return movement_summary_versions(db, movement_id)
    finally:
        db.close()

def movement_summary_source(movement_id: str, path: Path | None = None) -> tuple[str, str] | None:
    db = _record_db("movements","movement_id",movement_id,path)
    try:
        if not db.execute("SELECT 1 FROM movements WHERE movement_id=?", (movement_id,)).fetchone():
            return None
        return source_text_and_hash(db, movement_id)
    finally:
        db.close()

def movement_summary_source_record(movement_id: str, path: Path | None = None) -> dict | None:
    """Return structured input using the canonical own-page source."""
    db = _record_db("movements","movement_id",movement_id,path)
    try:
        row = db.execute("SELECT process_id, payload_json FROM movements WHERE movement_id=?", (movement_id,)).fetchone()
        if not row:
            return None
        payload = json.loads(row["payload_json"])
        pages = source_pages(db, movement_id)
        source_text, source_hash = source_text_and_hash(db, movement_id)
        return {
            "movement_id": movement_id,
            "process_id": row["process_id"],
            "label": payload.get("movement_type") or "Movimentação",
            "source_pages": [{"document_id": p["document_id"], "page_number": p["page_number"]} for p in pages],
            "source_text": source_text,
            "source_hash": source_hash,
        }
    finally:
        db.close()

def movement_analysis_v2_source_record(movement_id: str, path: Path | None = None) -> dict | None:
    """Own-piece V2 input; provider origin is metadata, never an identity assertion."""
    db = _record_db("movements", "movement_id", movement_id, path)
    try:
        row = db.execute("SELECT process_id,payload_json,actor,occurred_at,movement_type FROM movements WHERE movement_id=?", (movement_id,)).fetchone()
        if not row:
            return None
        payload = json.loads(row["payload_json"])
        pages = source_pages(db, movement_id)
        return {
            "movement_id": movement_id,
            "origin": row["actor"],
            "occurred_at": row["occurred_at"],
            "movement_type": row["movement_type"],
            "pages": [{"document_id": p["document_id"], "page_number": p["page_number"]} for p in pages],
            "source_text": "\n\n".join(p["content"] for p in pages),
            "source_hash": source_text_and_hash(db, movement_id)[1],
            "_source_pages": {(p["document_id"], p["page_number"]): p["content"] for p in pages},
            "process_id": row["process_id"],
        }
    finally:
        db.close()

def movement_analysis_v2_context(process_id: str, path: Path | None = None) -> dict | None:
    """Small process-local identity context plus deterministic persisted analysis references."""
    from core.documentos.movement_summary_store_v1 import persisted_analyses
    from core.documentos.movement_analysis_v2 import build_known
    db = _process_db(process_id, path)
    try:
        process = db.execute("SELECT status FROM processes WHERE process_id=?", (process_id,)).fetchone()
        if not process:
            return None
        participants = list_process_participants(db, process_id)
        representations = list_process_representations(db, process_id)
        people = [{"id": item["participant_id"], "name": item["display_name"], "role": item["base_role"]} for item in participants]
        rep_links = [{"representative_id": item["representative_participant_id"], "represented_id": item["represented_participant_id"], "kind": item["representation_kind"]} for item in representations]
        rows = persisted_analyses(db)
        fresh = []
        for item in rows:
            source_hash = source_text_and_hash(db, item["movement_id"])[1]
            if source_hash == item["source_hash"]:
                fresh.append(item)
        return {"main": {"process_id": process_id, "status": process["status"], "parties": people, "representations": rep_links},
                "main_ids": {process_id, *(p["id"] for p in people)},
                "known": build_known(fresh), "known_ids": {obj["id"] for obj in build_known(fresh)}}
    finally:
        db.close()

def save_movement_summary_record(
    movement_id: str,
    *,
    summary_text: str,
    source_hash: str,
    provider: str | None,
    model: str | None,
    usage: object,
    path: Path | None = None,
) -> dict:
    db_path = path or process_db_path(_record_process_id("movements","movement_id",movement_id))
    db = sqlite3.connect(str(db_path))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        from core.documentos.movement_summary_store_v1 import migrate_connection
        migrate_connection(db)
        return save_movement_summary(
            db, movement_id, summary_text=summary_text, source_hash=source_hash,
            provider=provider, model=model, usage=usage,
        )
    finally:
        db.close()


def save_movement_summary_batch_record(
    records: list[dict],
    *,
    provider: str | None,
    model: str | None,
    usage: object,
    path: Path | None = None,
) -> dict:
    from core.documentos.movement_summary_store_v1 import migrate_connection, save_batch
    db_path = path or process_db_path(_record_process_id("movements","movement_id",records[0]["movement_id"]))
    db = sqlite3.connect(str(db_path))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        migrate_connection(db)
        return save_batch(db, records, provider=provider, model=model, usage=usage)
    finally:
        db.close()

def save_movement_analysis_v2_batch_record(records: list[dict], *, provider: str | None, model: str | None, usage: object, path: Path | None = None) -> dict:
    from core.documentos.movement_summary_store_v1 import migrate_connection, save_analysis_v2_batch
    if not records:
        return {"imported": 0, "movement_ids": []}
    db_path = path or process_db_path(_record_process_id("movements", "movement_id", records[0]["movement_id"]))
    db = sqlite3.connect(str(db_path)); db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        migrate_connection(db)
        return save_analysis_v2_batch(db, records, provider=provider, model=model, usage=usage)
    finally:
        db.close()

def save_movement_analysis_v2_job_record(job: dict, path: Path | None = None) -> dict:
    from core.documentos.movement_summary_store_v1 import migrate_connection, save_analysis_v2_job
    process_id = str(job["process_id"])
    db_path = path or process_db_path(process_id)
    db = sqlite3.connect(str(db_path)); db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        migrate_connection(db)
        return save_analysis_v2_job(db, job)
    finally:
        db.close()

def create_movement_analysis_v2_job_if_absent(job: dict, path: Path | None = None) -> dict:
    """Atomically reuse an active process job or create one durable PENDING row."""
    from core.documentos.movement_summary_store_v1 import migrate_connection, analysis_v2_job, save_analysis_v2_job
    db_path = path or process_db_path(str(job["process_id"]))
    db = sqlite3.connect(str(db_path), timeout=10)
    db.row_factory = sqlite3.Row
    try:
        migrate_connection(db)
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            "SELECT job_id FROM movement_analysis_v2_jobs WHERE process_id=? AND status IN ('PENDING','RUNNING') ORDER BY created_at DESC, rowid DESC LIMIT 1",
            (str(job["process_id"]),),
        ).fetchone()
        if row:
            active = analysis_v2_job(db, str(job["process_id"]), str(row[0]))
            db.commit()
            return active
        saved = save_analysis_v2_job(db, job, commit=False)
        db.commit()
        return saved
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def movement_analysis_v2_job(process_id: str, job_id: str | None = None, path: Path | None = None) -> dict | None:
    from core.documentos.movement_summary_store_v1 import analysis_v2_job
    db = _process_db(process_id, path)
    try:
        return analysis_v2_job(db, process_id, job_id)
    finally:
        db.close()

def request_movement_analysis_v2_job_cancel(process_id: str, job_id: str, path: Path | None = None) -> dict | None:
    from core.documentos.movement_summary_store_v1 import request_analysis_v2_job_cancel
    db = _process_db(process_id, path)
    try:
        return request_analysis_v2_job_cancel(db, process_id, job_id)
    finally:
        db.close()

def process_movement_summary_targets(pid: str, *, force_all: bool = False, path: Path | None = None) -> dict:
    """Return eligible count and pending Movement IDs using persisted source metadata only."""
    db = _process_db(pid, path)
    try:
        if not db.execute("SELECT 1 FROM processes WHERE process_id=?", (pid,)).fetchone():
            return {"total_eligible": 0, "movement_ids": None}
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='movement_summary_source_state'").fetchone():
            raise RuntimeError("movement_summary_source_state migration is required")
        total = int(db.execute(
            """SELECT count(*) FROM movements m JOIN movement_summary_source_state state
                 ON state.movement_id=m.movement_id
               WHERE m.process_id=? AND state.eligible=1""",
            (pid,),
        ).fetchone()[0])
        sql = """SELECT m.movement_id
                 FROM movements m JOIN movement_summary_source_state state
                   ON state.movement_id=m.movement_id
                 LEFT JOIN movement_summaries s ON s.movement_id=m.movement_id AND s.summary_version=(
                   SELECT max(latest.summary_version) FROM movement_summaries latest
                   WHERE latest.movement_id=m.movement_id)
                 WHERE m.process_id=? AND state.eligible=1"""
        if not force_all:
            sql += " AND (s.movement_id IS NULL OR s.source_hash IS NULL OR s.source_hash<>state.source_hash OR trim(s.summary_text)='')"
        sql += " ORDER BY m.sequence"
        movement_ids = [str(row[0]) for row in db.execute(sql, (pid,)).fetchall()]
        return {"total_eligible": total, "movement_ids": movement_ids}
    finally:
        db.close()

def case_synthesis_dependencies(process_id: str, path: Path | None = None) -> tuple[list[dict], str] | None:
    db = _process_db(process_id,path)
    try:
        if not db.execute("SELECT 1 FROM processes WHERE process_id=?", (process_id,)).fetchone():
            return None
        movements_rows = read_movements(db, process_id)
        records = []
        for movement in movements_rows:
            row = db.execute(
                """SELECT summary_id, movement_id, summary_version, summary_text
                   FROM movement_summaries WHERE movement_id=?
                   ORDER BY summary_version DESC LIMIT 1""",
                (movement["movement_id"],),
            ).fetchone()
            if row is None or not str(row["summary_text"] or "").strip():
                continue
            records.append(dict(row))
        return records, case_synthesis_dependency_hash(records)
    finally:
        db.close()

def case_synthesis(process_id: str, path: Path | None = None) -> dict | None:
    db = _process_db(process_id,path)
    try:
        return current_case_synthesis(db, process_id)
    finally:
        db.close()

def case_synthesis_versions_list(process_id: str, path: Path | None = None) -> list[dict]:
    db = _process_db(process_id,path)
    try:
        return case_synthesis_versions(db, process_id)
    finally:
        db.close()

def case_synthesis_job(process_id: str, job_id: str, path: Path | None = None) -> dict | None:
    db = _process_db(process_id, path)
    try:
        return current_case_synthesis_job(db, process_id, job_id)
    finally:
        db.close()

def latest_case_synthesis_job_record(process_id: str, path: Path | None = None) -> dict | None:
    db = _process_db(process_id, path)
    try:
        return latest_case_synthesis_job(db, process_id)
    finally:
        db.close()

def create_case_synthesis_job_record(record: dict, path: Path | None = None) -> tuple[dict | None, bool]:
    db_path = path or process_db_path(str(record["process_id"]))
    if not db_path.is_file():
        return None, False
    db = sqlite3.connect(str(db_path), timeout=10)
    db.row_factory = sqlite3.Row
    try:
        migrate_case_synthesis(db)
        return create_case_synthesis_job_if_absent(db, record)
    finally:
        db.close()

def save_case_synthesis_job_record(record: dict, path: Path | None = None) -> dict:
    db_path = path or process_db_path(str(record["process_id"]))
    db = sqlite3.connect(str(db_path), timeout=10)
    db.row_factory = sqlite3.Row
    try:
        migrate_case_synthesis(db)
        return save_case_synthesis_job(db, record)
    finally:
        db.close()

def save_case_synthesis_record(
    process_id: str,
    *,
    case_synthesis_text: str,
    current_status: str,
    pending_issues: list[dict],
    supporting_movement_ids: list[str],
    provider: str | None,
    model: str | None,
    prompt_version: str,
    dependency_hash_value: str,
    usage: object,
    path: Path | None = None,
) -> dict:
    db_path = path or process_db_path(process_id)
    db = sqlite3.connect(str(db_path))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        migrate_case_synthesis(db)
        return save_case_synthesis(
            db, process_id, case_synthesis=case_synthesis_text, current_status=current_status,
            pending_issues=pending_issues, supporting_movement_ids=supporting_movement_ids,
            provider=provider, model=model, prompt_version=prompt_version,
            dependency_hash_value=dependency_hash_value, usage=usage,
        )
    finally:
        db.close()

def complete_case_synthesis_job_record(
    record: dict,
    *,
    case_synthesis_text: str,
    current_status: str,
    pending_issues: list[dict],
    supporting_movement_ids: list[str],
    prompt_version: str,
    dependency_hash_value: str,
    usage: object,
    path: Path | None = None,
) -> dict:
    db_path = path or process_db_path(str(record["process_id"]))
    db = sqlite3.connect(str(db_path), timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        migrate_case_synthesis(db)
        return complete_case_synthesis_job(
            db, record,
            case_synthesis=case_synthesis_text,
            current_status=current_status,
            pending_issues=pending_issues,
            supporting_movement_ids=supporting_movement_ids,
            prompt_version=prompt_version,
            dependency_hash_value=dependency_hash_value,
            usage=usage,
        )
    finally:
        db.close()

def procedural_acts(pid: str, path: Path | None = None) -> list[dict] | None:
    db = _process_db(pid,path)
    try:
        if not db.execute("SELECT 1 FROM processes WHERE process_id=?", (pid,)).fetchone():
            return None
        required_tables = {
            "provider_artifacts", "provider_artifact_pages", "canonical_pages",
            "canonical_page_observations", "pages", "documents",
        }
        present_tables = {
            row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if required_tables.issubset(present_tables):
            pecas_map = None
            data_root = _data_root_for_db(path)
            if data_root:
                try:
                    pecas_map = load_pecas_manifest(data_root, pid)
                except Exception:
                    pecas_map = None
            return project_procedural_acts(db, pid, pecas_map=pecas_map)
        return []
    finally:
        db.close()

def autos(pid, path=None, offset=0, limit=None):
    db=_process_db(pid,path)
    data_root = None
    if path:
        p_obj = Path(path).resolve()
def _document_integral_offsets(process_id: str, db: sqlite3.Connection) -> dict[str, int]:
    pages = db.execute("""
        SELECT json_extract(provenance_json, '$.document_id') as doc_id
        FROM canonical_pages
        WHERE process_id = ?
        ORDER BY process_page_number
    """, (process_id,)).fetchall()
    seen = set()
    doc_ids = []
    for p in pages:
        d = p["doc_id"]
        if d and d not in seen:
            seen.add(d)
            doc_ids.append(d)
    if not doc_ids:
        doc_rows = db.execute("SELECT document_id FROM documents WHERE process_id=? ORDER BY rowid", (process_id,)).fetchall()
        doc_ids = [r["document_id"] for r in doc_rows]

    doc_counts = {
        r["document_id"]: r["page_count"]
        for r in db.execute("SELECT document_id, page_count FROM documents WHERE process_id=?", (process_id,)).fetchall()
    }
    offsets = {}
    current = 0
    for d in doc_ids:
        offsets[d] = current
        current += doc_counts.get(d, 1)
    return offsets


def _materialized_autos_payload(
    db: sqlite3.Connection,
    pid: str,
    snapshot_id: str,
    rows: list[sqlite3.Row],
    doc_offsets: dict[str, int],
    offset: int,
    limit: int | None,
    total_pages: int,
) -> dict:
    """Build the public payload from the page-scoped persisted read model."""
    pages = []
    for page_row in rows:
        document_context = decode_autos_context(page_row["document_context_json"])
        visual_ref = decode_autos_context(page_row["visual_ref_json"])
        source_ref = decode_autos_context(page_row["source_ref_json"]) or {}
        pages.append({
            "page": int(page_row["page_number"]),
            "process_page_number": page_row["process_page_number"],
            "integral_pdf_page": page_row["integral_pdf_page"] if page_row["integral_pdf_page"] is not None else doc_offsets.get(page_row["document_id"], 0) + int(page_row["page_number"]),
            "content": page_row["content"],
            "quality": page_row["quality"],
            "category": page_row["category"],
            "visual_ref": visual_ref,
            "document_id": page_row["document_id"],
            "document_context": document_context,
            "source_ref": source_ref,
        })
    payload = {"process_id": pid, "snapshot_id": snapshot_id, "pages": pages, "status": "ready"}
    if limit is not None:
        payload["autos_page_offset"] = offset
        payload["autos_total_pages"] = total_pages
    return payload


def autos(
    pid: str,
    path: Path | None = None,
    offset: int = 0,
    limit: int | None = None,
    anchor_document_id: str | None = None,
    anchor_pdf_page: int | None = None,
    window_before: int = 10,
    window_after: int = 10,
) -> dict | None:
    db = _process_db(pid,path)
    data_root = _data_root_for_db(path)
    if not data_root:
        try:
            from core.runtime_paths import themis_data_root
            data_root = themis_data_root()
        except Exception:
            data_root = None

    try:
        row=db.execute("SELECT snapshot_id FROM docket_snapshots WHERE process_id=? ORDER BY created_at DESC LIMIT 1",(pid,)).fetchone()
        if not row:
            if data_root:
                proc_manifest = data_root / "processos" / pid / "manifest.json"
                if proc_manifest.is_file():
                    try:
                        mdata = json.loads(proc_manifest.read_text(encoding="utf-8"))
                        p_prog = mdata.get("pipeline_progress")
                        if p_prog:
                            return {
                                "process_id": pid,
                                "snapshot_id": None,
                                "pages": [],
                                "markdown": "",
                                "status": "processing",
                                "pipeline_progress": p_prog,
                                "message": p_prog.get("message", "Processando documentos..."),
                            }
                    except Exception:
                        pass
            return None
        if anchor_document_id and anchor_pdf_page is not None:
            anchor_row = db.execute(
                """SELECT dd.ordinal
                   FROM docket_documents dd
                   JOIN documents d ON d.document_id=dd.document_id
                   WHERE dd.snapshot_id=? AND d.document_id=?""",
                (row["snapshot_id"], anchor_document_id),
            ).fetchone()
            if anchor_row:
                before_count = db.execute(
                    """SELECT count(*)
                       FROM docket_documents dd
                       JOIN documents d ON d.document_id=dd.document_id
                       JOIN pages p ON p.document_id=d.document_id
                       WHERE dd.snapshot_id=?
                         AND (dd.ordinal < ? OR (dd.ordinal = ? AND p.page_number < ?))""",
                    (row["snapshot_id"], anchor_row["ordinal"], anchor_row["ordinal"], int(anchor_pdf_page)),
                ).fetchone()[0]
                offset = max(0, before_count - max(0, int(window_before)))
                limit = max(1, int(window_before)) + max(0, int(window_after)) + 1
        doc_offsets = _document_integral_offsets(pid, db)
        total_pages = db.execute(
            "SELECT count(*) FROM docket_documents dd JOIN documents d ON d.document_id=dd.document_id JOIN pages p ON p.document_id=d.document_id WHERE dd.snapshot_id=?",
            (row["snapshot_id"],),
        ).fetchone()[0]
        hot_context_ready = process_is_complete(db, pid, int(total_pages))
        params=[row["snapshot_id"]]
        page_cols = {r["name"] for r in db.execute("PRAGMA table_info(pages)").fetchall()}
        engine_col = "p.engine" if "engine" in page_cols else "'pdfium' as engine"
        fallback_col = "p.fallback_used" if "fallback_used" in page_cols else "0 as fallback_used"
        if hot_context_ready:
            sql=f"""SELECT p.page_number,p.content,p.quality,p.process_folio,p.page_class,{engine_col},{fallback_col},d.document_id,
                           p.process_folio AS process_page_number,ac.integral_pdf_page,p.page_class AS category,
                           ac.visual_ref_json,ac.document_context_json,ac.source_ref_json
                    FROM docket_documents dd
                    JOIN documents d ON d.document_id=dd.document_id
                    JOIN pages p ON p.document_id=d.document_id
                    LEFT JOIN canonical_page_observations cpo
                      ON cpo.document_id=d.document_id AND cpo.pdf_page=p.page_number
                    LEFT JOIN canonical_page_autos_context ac
                      ON ac.canonical_page_id=cpo.canonical_page_id AND ac.process_id=?
                    WHERE dd.snapshot_id=?
                    ORDER BY dd.ordinal,p.page_number"""
            params=[pid, row["snapshot_id"]]
        else:
            sql=f"SELECT p.page_number,p.content,p.quality,p.process_folio,p.page_class,{engine_col},{fallback_col},d.document_id FROM docket_documents dd JOIN documents d ON d.document_id=dd.document_id JOIN pages p ON p.document_id=d.document_id WHERE dd.snapshot_id=? ORDER BY dd.ordinal,p.page_number"
        # The first Autos paint must not wait for the expensive full-document
        # context/fólio preparation.  A bounded request is intentionally a
        # lightweight textual page slice; the normal unbounded request below
        # still produces the complete canonical payload in the background.
        bounded_request = limit is not None
        fast_first_block = offset == 0 and bounded_request and limit <= 10
        if bounded_request:
            sql += " LIMIT ? OFFSET ?"
            params.extend([max(1, int(limit)), max(0, int(offset))])
        all_rows = db.execute(sql, params).fetchall()
        if fast_first_block:
            pages = []
            for page_row in all_rows:
                doc_id = page_row["document_id"]
                p_num = int(page_row["page_number"])
                integral_pdf_page = doc_offsets.get(doc_id, 0) + p_num
                pages.append({
                    "page": p_num,
                    "process_page_number": page_row["process_folio"],
                    "integral_pdf_page": integral_pdf_page,
                    "content": page_row["content"],
                    "quality": page_row["quality"],
                    "category": page_row["page_class"],
                    "visual_ref": ({
                        "kind": "pdf_page_raster",
                        "url": f"/api/v1/juridico/documents/{doc_id}/pages/{p_num}/raster",
                        "raw_pdf_url": f"/api/v1/juridico/documents/{doc_id}/raw#page={p_num}",
                        "document_id": doc_id,
                        "pdf_page": p_num,
                        "process_folio": page_row["process_folio"],
                    } if page_row["page_class"] == "VISUAL_ASSET" else None),
                    "document_id": doc_id,
                    "document_context": None,
                    "source_ref": {
                        "document_id": doc_id,
                        "pdf_page": p_num,
                        "process_folio": page_row["process_folio"],
                        "process_page_number": None,
                        "integral_pdf_page": integral_pdf_page,
                        "folio_resolution": "PENDING_FULL_AUTOS",
                    },
                })
            return {
                "process_id": pid,
                "snapshot_id": row["snapshot_id"],
                "pages": pages,
                "status": "ready",
                "autos_page_offset": offset,
                "autos_total_pages": db.execute(
                    "SELECT count(*) FROM docket_documents dd JOIN documents d ON d.document_id=dd.document_id JOIN pages p ON p.document_id=d.document_id WHERE dd.snapshot_id=?",
                    (row["snapshot_id"],),
                ).fetchone()[0],
            }
        if hot_context_ready:
            return _materialized_autos_payload(
                db, pid, row["snapshot_id"], all_rows, doc_offsets,
                offset, limit, int(total_pages),
            )
        pecas_manifest_map = {}
        if data_root:
            try:
                from core.documentos.pecas_manifest_v1 import load_pecas_manifest
                pecas_manifest_map = load_pecas_manifest(data_root, pid)
            except Exception:
                pecas_manifest_map = {}

        has_provider_artifacts = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='provider_artifacts'").fetchone() is not None
        context_by_page = {}
        submission_members = {}
        if has_provider_artifacts:
            context_sql = """SELECT o.document_id,o.pdf_page,a.provider_artifact_id,a.artifact_type,a.signer,a.source_origin,a.provenance_json
                FROM provider_artifact_pages ap
                JOIN provider_artifacts a ON a.provider_artifact_id=ap.provider_artifact_id
                JOIN canonical_page_observations o ON o.canonical_page_id=ap.canonical_page_id
                JOIN canonical_pages cp ON cp.canonical_page_id=o.canonical_page_id
                WHERE cp.process_id=?"""
            context_params: list[Any] = [pid]
            if bounded_request:
                requested_keys = {(row["document_id"], int(row["page_number"])) for row in all_rows}
                if requested_keys:
                    context_sql += " AND (" + " OR ".join("(o.document_id=? AND o.pdf_page=?)" for _ in requested_keys) + ")"
                    for document_id, page_number in sorted(requested_keys):
                        context_params.extend([document_id, page_number])
                else:
                    context_sql += " AND 1=0"
            context_rows = db.execute(context_sql, context_params).fetchall()
            for context_row in context_rows:
                doc_id = context_row["document_id"]
                p_num = context_row["pdf_page"]
                piece_meta = pecas_manifest_map.get(doc_id)
                piece_context = piece_meta.to_dict() if piece_meta else None

                try:
                    provenance = json.loads(context_row["provenance_json"] or "{}")
                except (TypeError, ValueError):
                    provenance = {}
                all_markers = provenance.get("markers") if isinstance(provenance.get("markers"), list) else []
                marker = next(
                    (item for item in all_markers if isinstance(item, dict) and (item.get("source_map") or {}).get("pdf_page") == p_num),
                    provenance.get("marker") if isinstance(provenance.get("marker"), dict) else {},
                )
                provenance_doc_type = provenance.get("document_type") if isinstance(provenance.get("document_type"), dict) else {}
                structural_heading = provenance.get("structural_heading")
                if not structural_heading and provenance_doc_type.get("classification_source") == "STRUCTURAL_HEADING_V1":
                    structural_heading = provenance_doc_type

                artifact_context = {
                    "provider_artifact_id": context_row["provider_artifact_id"],
                    "actor": context_row["signer"],
                    # A clock time without its calendar date is not promoted to datetime.
                    "datetime": marker.get("event_at"),
                    "event_time": marker.get("event_time"),
                    "protocol": (marker.get("provider_identity") or {}).get("document_or_movement_or_protocol", {}).get("value"),
                    "verification_status": provenance.get("provider_verification_status") or "PROVIDER_ATTESTED",
                    "source": {
                        "provider": context_row["source_origin"],
                        "source_map": marker.get("source_map"),
                    },
                    "structural_heading": structural_heading if structural_heading else None,
                }

                group_ids = provenance.get("provider_marker_group_ids") if isinstance(provenance.get("provider_marker_group_ids"), list) else []
                page_key = (doc_id, p_num)
                context_by_page.setdefault(page_key, {
                    "piece_context": piece_context,
                    "artifact_context": artifact_context,
                    "submission_context": None,
                })
                for group_id in group_ids:
                    if not isinstance(group_id, str):
                        continue
                    group = submission_members.setdefault(group_id, [])
                    group.append({
                        "page_key": page_key,
                        "artifact_context": artifact_context,
                        "document_type": provenance_doc_type,
                        "provider": context_row["source_origin"],
                        "provider_identity": (marker.get("provider_identity") or {}).get("document_or_movement_or_protocol") or {},
                        "provider_event": marker.get("event"),
                        "movement_fingerprint_basis": marker.get("movement_fingerprint_basis"),
                    })
            for group_id, members in submission_members.items():
                # A structural heading identifies its own artifact, not every
                # attachment in a provider envelope.  Only an explicitly
                # audited CORE_REFERENCED type can identify the submission.
                candidates = [
                    item["document_type"] for item in members
                    if item["document_type"].get("verification_status") == "CONFIRMED"
                    and item["document_type"].get("classification_source") == "CORE_REFERENCED"
                    and item["document_type"].get("artifact_type")
                ]
                candidate_types = {item["artifact_type"] for item in candidates}
                submission_type = None
                classification_source = None
                evidence = None
                if len(candidate_types) == 1:
                    candidate = candidates[0]
                    submission_type = candidate["artifact_type"]
                    classification_source = "CORE_REFERENCED"
                    evidence = candidate.get("evidence")
                else:
                    # A WPRC number is the e-SAJ submission identity.  A
                    # continuous group whose outer markers all say
                    # PROTOCOLADO is therefore a provider-confirmed filing;
                    # it does not change the identity of its attachments.
                    protocols = {
                        item["provider_identity"].get("value") for item in members
                        if item["provider_identity"].get("kind") == "PROTOCOL"
                        and str(item["provider_identity"].get("value") or "").upper().startswith("WPRC")
                    }
                    marker_events = {
                        item["provider_event"] for item in members if item["provider_event"]
                    }
                    if len(protocols) != 1 or marker_events != {"PROTOCOLADO"}:
                        continue
                    protocol = next(iter(protocols))
                    submission_type = "PETICAO_PROTOCOLADA"
                    classification_source = "PROVIDER_PROTOCOL_GROUP_V1"
                    evidence = {
                        "provider_marker_group_id": group_id,
                        "protocol": protocol,
                        "method": "PROVIDER_PROTOCOL_GROUP_V1",
                    }
                actors = {item["artifact_context"].get("actor") for item in members if item["artifact_context"].get("actor")}
                datetimes = {item["artifact_context"].get("datetime") for item in members if item["artifact_context"].get("datetime")}
                provider_values = sorted({
                    item["provider_identity"].get("value") for item in members
                    if item["provider_identity"].get("value")
                })
                submission_context = {
                    "submission_id": group_id,
                    "submission_type": submission_type,
                    "verification_status": "CONFIRMED",
                    "classification_source": classification_source,
                    "evidence": evidence,
                    "identity": {
                        "provider": next(iter({item["provider"] for item in members})),
                        "provider_marker_group_id": group_id,
                        "provider_identity_values": provider_values,
                        "signer": next(iter(actors)) if len(actors) == 1 else None,
                        "datetime": next(iter(datetimes)) if len(datetimes) == 1 else None,
                        "continuity": "provider_marker_group_v1",
                        "fingerprint_basis": next(iter({item["movement_fingerprint_basis"] for item in members if item["movement_fingerprint_basis"]}), None),
                    },
                }
                for member in members:
                    context_by_page[member["page_key"]]["submission_context"] = submission_context

        known_folios = {
            (row["document_id"], int(row["page_number"])): int(row["process_folio"])
            for row in all_rows if row["process_folio"] is not None
        }
        page_metadata_by_key = {}
        for page_row in all_rows:
            document_id = page_row["document_id"]
            p_num = int(page_row["page_number"])
            key = (document_id, p_num)
            content = page_row["content"]
            is_visual_comment = content.startswith("<!-- visual-asset:") or content.startswith("*[Página digitalizada") or content == "[Página digitalizada / Anexo visual]"
            is_ocr = page_row["quality"] == "OCR" or page_row["engine"] in ("faster_paddle_small", "ocr") or (page_row["fallback_used"] == 1 and bool(content.strip()))

            page_class = page_row["page_class"]
            is_visual_asset = page_class == "VISUAL_ASSET"
            if page_class not in {"NATIVE_VALID", "CORRUPTED_TEXT_LAYER", "TEXTUAL_VISUAL", "VISUAL_ASSET", "BLANK_PAGE", "BLANK_BODY", "MISSING_FOLIO"}:
                page_class = "NATIVE_VALID"
            is_ocr = page_class == "CORRUPTED_TEXT_LAYER" or page_row["quality"] == "OCR" or page_row["engine"] in ("faster_paddle_small", "ocr") or (page_row["fallback_used"] == 1 and bool(page_row["content"].strip()))

            page_metadata_by_key[key] = {
                "is_ocr": is_ocr,
                "is_visual_asset": is_visual_asset,
            }
        for page_row in all_rows:
            doc_id = page_row["document_id"]
            p_num = int(page_row["page_number"])
            key = (doc_id, p_num)
            if key in context_by_page:
                if context_by_page[key].get("piece_context") is None and doc_id in pecas_manifest_map:
                    context_by_page[key]["piece_context"] = pecas_manifest_map[doc_id].to_dict()
            elif doc_id in pecas_manifest_map:
                context_by_page[key] = {
                    "piece_context": pecas_manifest_map[doc_id].to_dict(),
                    "artifact_context": None,
                    "submission_context": None,
                }
        rows = all_rows if bounded_request else all_rows[offset: offset + limit if limit is not None else None]
        pages = []
        for page_row in rows:
            doc_id = page_row["document_id"]
            p_num = int(page_row["page_number"])
            key = (doc_id, p_num)

            official_folio = known_folios.get(key)
            resolution_val = "MATERIALIZED" if official_folio is not None else "UNKNOWN"

            page_metadata = page_metadata_by_key[key]
            is_ocr = page_metadata["is_ocr"]
            is_visual_asset = page_metadata["is_visual_asset"]

            visual_ref = None
            if is_visual_asset:
                visual_ref = {
                    "kind": "pdf_page_raster",
                    "url": f"/api/v1/juridico/documents/{doc_id}/pages/{p_num}/raster",
                    "raw_pdf_url": f"/api/v1/juridico/documents/{doc_id}/raw#page={p_num}",
                    "document_id": doc_id,
                    "pdf_page": p_num,
                    "process_folio": official_folio,
                }

            integral_pdf_page = doc_offsets.get(doc_id, 0) + p_num
            category = "CORRUPTED_TEXT_LAYER" if is_ocr else page_class
            pages.append({
                "page": p_num,
                "process_page_number": official_folio,
                "integral_pdf_page": integral_pdf_page,
                "content": page_row["content"],
                "quality": page_row["quality"],
                "category": category,
                "visual_ref": visual_ref,
                "document_id": doc_id,
                "document_context": context_by_page.get((doc_id, p_num)),
                "source_ref": {
                    "document_id": doc_id,
                    "pdf_page": p_num,
                    "process_folio": official_folio,
                    "process_page_number": official_folio,
                    "integral_pdf_page": integral_pdf_page,
                    "folio_resolution": resolution_val,
                },
            })
        payload = {"process_id":pid,"snapshot_id":row["snapshot_id"],"pages":pages,"status":"ready"}
        if bounded_request:
            payload["autos_page_offset"] = offset
            payload["autos_total_pages"] = db.execute(
                "SELECT count(*) FROM docket_documents dd JOIN documents d ON d.document_id=dd.document_id JOIN pages p ON p.document_id=d.document_id WHERE dd.snapshot_id=?",
                (row["snapshot_id"],),
            ).fetchone()[0]
        return payload
    finally: db.close()

def view(owner_kind: str, owner_id: str, view_name: str, path: Path | None = None) -> dict[str, Any]:
    from core.documentos.canonical_service_facade_v1 import CanonicalServiceFacade
    norm_owner = str(owner_kind).lower()
    norm_view = str(view_name).lower()
    mapping = {
        "timeline": "CHRONOLOGY",
        "chronology": "CHRONOLOGY",
        "parties": "PARTIES",
        "deadlines": "DEADLINES",
        "hearings": "HEARINGS",
        "pending": "PENDING",
        "strategy": "STRATEGY",
    }
    if norm_view not in mapping:
        raise ValueError(f"view_name desconhecido: {view_name}")
    target = mapping[norm_view]
    target_db = (path or process_db_path(owner_id) if norm_owner == "process" else path or index_db_path()).resolve()
    facade = CanonicalServiceFacade(target_db)
    res = facade.knowledge_get(norm_owner, owner_id, target)
    items = res.get("items", [])
    status = "ready" if items else "empty"
    source_refs = list(res.get("source_refs", []))
    if not source_refs:
        for item in items:
            for ev in item.get("evidence", []):
                ref = ev.get("source_ref") or ev.get("source_ref_json")
                if isinstance(ref, str):
                    try:
                        ref = json.loads(ref)
                    except Exception:
                        pass
                if ref:
                    source_refs.append(ref)
    return {
        "owner_kind": norm_owner,
        "owner_id": owner_id,
        "view_name": norm_view,
        "status": status,
        "items": items,
        "source_refs": source_refs,
    }

def matter(mid, path=None): return None
def document(doc_id, path=None):
    db=_record_db("documents","document_id",doc_id,path)
    try:
        row=db.execute("SELECT d.document_id,d.process_id,f.size_bytes,d.page_count,d.status,d.created_at,f.path FROM documents d JOIN files f USING(file_id) WHERE d.document_id=?",(doc_id,)).fetchone()
        return dict(row) if row else None
    finally: db.close()
def document_path(doc_id, path=None):
    doc = document(doc_id, path)
    if doc is None:
        return None
    data_root = _data_root_for_db(Path(path)) if path else None
    package_dir = (
        data_root / "processos" / doc["process_id"]
        if data_root is not None
        else process_db_path(doc["process_id"]).parent
    )
    candidate = package_dir / "fontes" / "objetos" / f"{doc['document_id']}.pdf"
    if candidate.is_file():
        return candidate
    raw_path = doc.get("path")
    if raw_path and Path(raw_path).is_file():
        return Path(raw_path).resolve()
    return None

def process_pdf_path(process_id: str, path: Path | None = None) -> Path | None:
    """Resolve or assemble the complete integral PDF for a given process."""
    db = _process_db(process_id,path)
    try:
        doc_rows = db.execute(
            "SELECT document_id FROM documents WHERE process_id = ? ORDER BY rowid",
            (process_id,)
        ).fetchall()
        if not doc_rows:
            return None
        if len(doc_rows) == 1:
            return document_path(doc_rows[0]["document_id"], path)

        data_root = _data_root_for_db(path)
        if not data_root:
            return None
        proc_dir = data_root / "processos" / process_id
        derivados = proc_dir / "derivados"
        derivados.mkdir(parents=True, exist_ok=True)
        cached_pdf = derivados / "processo_integral.pdf"

        if cached_pdf.is_file() and cached_pdf.stat().st_size > 0:
            return cached_pdf

        pages = db.execute("""
            SELECT json_extract(provenance_json, '$.document_id') as doc_id, process_page_number
            FROM canonical_pages
            WHERE process_id = ?
            ORDER BY process_page_number
        """, (process_id,)).fetchall()

        seen = set()
        doc_ids = []
        for p in pages:
            d = p["doc_id"]
            if d and d not in seen:
                seen.add(d)
                doc_ids.append(d)

        if not doc_ids:
            doc_ids = [r["document_id"] for r in doc_rows]

        import pypdfium2 as pdfium
        dest = pdfium.PdfDocument.new()
        for d in doc_ids:
            p_path = document_path(d, path)
            if p_path and p_path.is_file():
                src = pdfium.PdfDocument(str(p_path))
                dest.import_pages(src)
                src.close()

        dest.save(str(cached_pdf))
        dest.close()
        return cached_pdf
    finally:
        db.close()

def process_pdf_bytes(process_id: str, path: Path | None = None) -> bytes | None:
    p_path = process_pdf_path(process_id, path)
    if not p_path or not p_path.is_file():
        return None
    return p_path.read_bytes()

def document_page_raster(doc_id: str, page_number: int, scale: float = 2.0, path: Path | None = None) -> bytes | None:
    """Render a single PDF page to PNG bytes lazily on-demand."""
    doc_p = document_path(doc_id, path)
    if not doc_p or not doc_p.is_file():
        return None
    try:
        import io
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(doc_p))
        if page_number < 1 or page_number > len(doc):
            doc.close()
            return None
        page = doc[page_number - 1]
        bitmap = page.render(scale=scale)
        pil_img = bitmap.to_pil()
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        doc.close()
        return buf.getvalue()
    except Exception:
        return None

def retrieval_search(process_id: str, query: str, top_k: int = 5, path: Path | None = None, vector_path: Path | None = None) -> dict[str, Any]:
    from core.retrieval.hybrid_retrieval import search_hybrid
    target_db = (path or process_db_path(process_id)).resolve()
    sources = search_hybrid(process_id, query, top_k, db_path=target_db, vector_db_path=vector_path or target_db)
    return {
        "process_id": process_id,
        "query": query,
        "sources": sources,
    }


def retrieval_answer(
    process_id: str,
    query: str,
    top_k: int = 5,
    llm_caller: Any = None,
    path: Path | None = None,
    vector_path: Path | None = None,
) -> dict[str, Any]:
    """Gera resposta fundamentada com citações verificáveis e vinculadas aos Autos."""
    from core.retrieval.hierarchical_retrieval import search_hierarchical_evidence
    from core.retrieval.citations import synthesize_answer_with_citations
    target_db = (path or process_db_path(process_id)).resolve()
    sources = search_hierarchical_evidence(
        process_id, query, top_k, db_path=target_db,
        vector_db_path=vector_path or target_db,
    )
    return synthesize_answer_with_citations(
        process_id=process_id,
        query=query,
        sources=sources,
        llm_caller=llm_caller,
    )



def analyze_process(
    process_id: str,
    path: Path | None = None,
    vector_path: Path | None = None,
    llm_caller: Any = None,
) -> dict[str, Any]:
    """Executa a análise processual canônica e persiste via capabilities."""
    from core.ai.process_analyzer import ProcessAnalyzer
    local_db = path or process_db_path(process_id)
    analyzer = ProcessAnalyzer(db_path=local_db, vector_db_path=vector_path or local_db, llm_caller=llm_caller)
    return analyzer.analyze_process(process_id)


def list_events(
    *,
    process_id: str | None = None,
    kind: str | None = None,
    query: str | None = None,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """Projeção de leitura unificada para listar LegalEvents."""
    from core.documentos.legal_event_projection_v1 import LegalEventProjection
    if process_id:
        db = _process_db(process_id,path)
        try: return LegalEventProjection.list_events(db, process_id=process_id, kind=kind, query=query)
        finally: db.close()
    from core.process_storage import known_process_ids
    results=[]
    for pid in known_process_ids():
        db=_process_db(pid,path)
        try: results.extend(LegalEventProjection.list_events(db,process_id=pid,kind=kind,query=query))
        finally: db.close()
    return results


def process_events(
    process_id: str,
    *,
    event_type: str | None = None,
    date_precision: str | None = None,
    path: Path | None = None,
) -> list[dict]:
    """Read-only diagnostic read model for deterministic ProcessEvent V1."""
    db = _process_db(process_id,path)
    try:
        return list_temporal_events(db, process_id, event_type=event_type, date_precision=date_precision)
    finally:
        db.close()


def deadline_instructions(
    process_id: str,
    *,
    status: str | None = None,
    trigger_status: str | None = None,
    path: Path | None = None,
) -> list[dict]:
    """Read-only diagnostic read model for explicit temporal instructions."""
    db = _process_db(process_id,path)
    try:
        return list_deadline_instructions(db, process_id, status=status, trigger_status=trigger_status)
    finally:
        db.close()


def deadline_obligations(
    process_id: str,
    *,
    status: str | None = None,
    recipient: str | None = None,
    path: Path | None = None,
) -> list[dict]:
    """Read-only diagnostic read model for consolidated obligations."""
    db = _process_db(process_id,path)
    try:
        return list_deadline_obligations(db, process_id, status=status, recipient=recipient)
    finally:
        db.close()


def get_event(
    event_id: str,
    path: Path | None = None,
) -> dict[str, Any] | None:
    """Busca um LegalEvent individual por seu ID canônico."""
    from core.documentos.legal_event_projection_v1 import LegalEventProjection
    if path is not None:
        db = _db(path)
        try: return LegalEventProjection.get_event(db,event_id)
        finally: db.close()
    from core.process_storage import known_process_ids
    for pid in known_process_ids():
        db=_process_db(pid)
        try:
            result=LegalEventProjection.get_event(db,event_id)
            if result: return result
        finally: db.close()
    return None


def djen_status() -> dict[str, Any]:
    from core.documentos.djen_sync_v1 import status
    value = status()
    from core.process_storage import connect_workspace
    from core.documentos import djen_sync_job_store_v1 as jobs
    try:
        db = connect_workspace()
    except FileNotFoundError:
        value.update(active_job=None, latest_job=None)
        return value
    try:
        jobs.migrate(db)
        active, latest = jobs.latest(db)
        value.update(active_job=active, latest_job=latest)
        return value
    finally:
        db.close()


def create_djen_sync_job(process_id: str | None = None, available_to: str | None = None) -> tuple[dict, bool]:
    from datetime import date
    from core.process_storage import connect_workspace, process_db_path
    from core.documentos import djen_sync_job_store_v1 as jobs
    target_date = str(available_to or date.today().isoformat())
    try:
        date.fromisoformat(target_date)
    except ValueError as exc:
        raise ValueError("available_to deve usar YYYY-MM-DD") from exc
    if process_id and not process_db_path(process_id).is_file():
        raise FileNotFoundError(f"Process Package ausente para {process_id}")
    db = connect_workspace(create=True)
    try:
        jobs.migrate(db)
        return jobs.create_or_reuse(db, process_id, target_date)
    finally:
        db.close()


def djen_sync_job(job_id: str) -> dict | None:
    from core.process_storage import connect_workspace
    from core.documentos import djen_sync_job_store_v1 as jobs
    db = connect_workspace()
    try:
        jobs.migrate(db)
        return jobs.get(db, job_id)
    finally:
        db.close()


def sync_djen_now(process_id: str | None = None) -> dict[str, Any]:
    from core.documentos.djen_sync_v1 import sync_now
    return sync_now(process_id=process_id)


def publications(process_id: str, path: Path | None = None) -> list[dict[str, Any]] | None:
    from core.documentos.publications_v1 import list_publications
    db = _process_db(process_id,path)
    try:
        if not db.execute("SELECT 1 FROM processes WHERE process_id=?", (process_id,)).fetchone():
            return None
        return list_publications(db, process_id)
    finally:
        db.close()


def sync_publications(
    process_id: str,
    *,
    available_from: str,
    available_to: str,
) -> dict[str, Any]:
    from core.documentos.process_event_store_v1 import materialize_process_events
    from core.documentos.publications_v1 import sync_djen
    from core.process_storage import connect_process

    db = connect_process(process_id)
    try:
        result = sync_djen(
            db,
            process_id=process_id,
            available_from=available_from,
            available_to=available_to,
        )
        result["process_events"] = materialize_process_events(db, process_id)
        return result
    finally:
        db.close()


def reprocess_page(
    document_id_or_process_id: str,
    page_number: int,
    *,
    pdf_path: Path | str | None = None,
    enable_heron_fallback: bool | None = None,
    update_embedding: bool = True,
    backend: str | None = None,
    path: Path | None = None,
    vector_db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Reprocessa de forma incremental uma única página preservando o restante do índice."""
    from core.documentos.themis_documentos import Store, reprocess_page as _reprocess_page
    from core.runtime_paths import themis_data_root
    process_id = document_id_or_process_id
    if not re.fullmatch(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", str(process_id)):
        record = document(document_id_or_process_id,path)
        if not record:
            raise FileNotFoundError(f"Documento não localizado: {document_id_or_process_id}")
        process_id=record["process_id"]
    store_root = _data_root_for_db(path) if path else themis_data_root()
    if store_root is None:
        raise RuntimeError("Não foi possível determinar o data root do Process Package")
    store = Store(store_root, process_id=process_id)
    return _reprocess_page(
        document_id_or_process_id=document_id_or_process_id,
        page_number=page_number,
        store=store,
        pdf_path=pdf_path,
        enable_heron_fallback=enable_heron_fallback,
        update_embedding=update_embedding,
        backend=backend,
        vector_db_path=vector_db_path,
    )


def delete_process(
    process_id: str,
    confirm_process_id: str,
    path: Path | None = None,
) -> dict[str, Any]:
    """Exclui nativa e atomicamente um processo, seus registros SQL, índices e arquivos."""
    from core.documentos.themis_documentos import Store, delete_process as _delete_process
    from core.runtime_paths import themis_data_root
    store = Store(path.parent.parent if path else themis_data_root(), process_id=process_id)
    return _delete_process(
        store=store,
        process_id=process_id,
        confirm_process_id=confirm_process_id,
    )
