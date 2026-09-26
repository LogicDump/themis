"""Fachada pública e autorizável para operações de domínio do Jurídico.

Callers recebem contratos sem conexão SQLite, nomes de tabela ou paths. A
fachada separa leituras read-only, escritas transacionais e manutenção técnica.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.documentos.domain_objects_v1 import (
    deadline_view_items,
    hearing_view_items,
    pending_view_items,
    strategy_view_items,
    submit_deadline_candidates,
    submit_hearing_candidates,
    submit_pending_candidates,
    submit_strategy_candidates,
    upsert_matter_metadata,
    upsert_process_metadata,
)
from core.documentos.knowledge_objects_v1 import (
    chronology_view_items,
    party_view_items,
    submit_chronology_candidates,
    submit_party_candidates,
)

ORIGINS = {"HUMAN", "AI", "LEGACY_IMPORT"}
READ_TARGETS = {"PARTIES", "CHRONOLOGY", "DEADLINES", "HEARINGS", "PENDING", "STRATEGY"}
WRITE_TARGETS = {"PARTIES", "CHRONOLOGY", "DEADLINES", "HEARINGS", "PENDING"}
CONFIRMATION_VALUES = {"PENDING", "CONFIRMED", "CONFLICTING"}


class CanonicalServiceFacade:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path).resolve()

    def _read(self) -> sqlite3.Connection:
        if not self.db_path.is_file():
            raise ValueError("banco canônico não encontrado")
        db = sqlite3.connect(self.db_path.resolve().as_uri() + "?mode=ro", uri=True)
        db.row_factory = sqlite3.Row
        return db

    def _write(self) -> sqlite3.Connection:
        if not self.db_path.is_file():
            raise ValueError("banco canônico não encontrado")
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @staticmethod
    def _owner(db: sqlite3.Connection, owner_type: str, owner_id: str, *, process_only: bool = False) -> str:
        code = str(owner_type).upper()
        if code not in {"MATTER", "PROCESS"} or (process_only and code != "PROCESS"):
            raise ValueError("owner_type inválido")
        table, column = ("matters", "matter_id") if code == "MATTER" else ("processes", "process_id")
        if db.execute(f"SELECT 1 FROM {table} WHERE {column}=?", (owner_id,)).fetchone() is None:
            raise ValueError("owner inexistente")
        return code

    @classmethod
    def _origin(cls, value: str) -> str:
        origin = str(value or "").upper()
        if origin not in ORIGINS:
            raise ValueError("origin inválida")
        return origin

    @staticmethod
    def _validate_source(db: sqlite3.Connection, owner_type: str, owner_id: str, source_ref: dict[str, Any]) -> dict[str, Any]:
        document_id = source_ref.get("document_id")
        canonical_page_id = source_ref.get("canonical_page_id")
        if not document_id or not canonical_page_id:
            raise ValueError("source_ref exige document_id e canonical_page_id")
        pdf_page = source_ref.get("pdf_page")
        query = """SELECT d.document_id,d.process_id,o.canonical_page_id,o.pdf_page
            FROM documents d JOIN canonical_page_observations o
              ON o.document_id=d.document_id
            JOIN canonical_pages cp ON cp.canonical_page_id=o.canonical_page_id
            WHERE d.document_id=? AND o.canonical_page_id=? AND cp.lifecycle_status='ACTIVE'"""
        params: list[Any] = [document_id, canonical_page_id]
        if pdf_page is not None:
            try: pdf_page = int(pdf_page)
            except (TypeError, ValueError): raise ValueError("source_ref.pdf_page inválido")
            query += " AND o.pdf_page=?"; params.append(pdf_page)
        row = db.execute(query, params).fetchone()
        if not row: raise ValueError("source_ref não corresponde a página canônica")
        code = str(owner_type).upper()
        if code == "PROCESS" and row["process_id"] != owner_id:
            raise ValueError("source_ref pertence a outro processo")
        if code == "MATTER":
            related = db.execute("SELECT 1 FROM matter_processes WHERE matter_id=? AND process_id=?", (owner_id, row["process_id"])).fetchone()
            if not related: raise ValueError("source_ref pertence a outra matéria")
        return {**source_ref, "document_id": row["document_id"], "canonical_page_id": row["canonical_page_id"], "pdf_page": row["pdf_page"]}

    @staticmethod
    def _ensure_extraction_run(db: sqlite3.Connection, owner_type: str, owner_id: str, target: str,
                               origin: str, supplied_id: str | None, pipeline_version: str) -> str | None:
        if origin == "HUMAN":
            if supplied_id:
                raise ValueError("extraction_run_id não se aplica a operação HUMAN")
            return None
        target = target.upper()
        has_domain_runs = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='domain_extraction_runs'").fetchone() is not None
        table = "domain_extraction_runs" if (has_domain_runs and target in {"STRATEGY", "DEADLINES", "PENDING", "HEARINGS"}) else "extraction_runs"
        if supplied_id:
            row = db.execute(f"SELECT extraction_run_id,owner_type,owner_id,target FROM {table} WHERE extraction_run_id=?", (supplied_id,)).fetchone()
            if row and (row["owner_type"] != owner_type or row["owner_id"] != owner_id or row["target"] != target):
                raise ValueError("extraction_run_id incompatível com owner/target")
            if row:
                return supplied_id
        run_id = supplied_id or str(uuid.uuid4())
        db.execute(f"""INSERT INTO {table}(
            extraction_run_id,owner_type,owner_id,target,pipeline_version,started_at,status
        ) VALUES(?,?,?,?,?,?,?)""", (run_id, owner_type, owner_id, target, pipeline_version, datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "STARTED"))
        return run_id

    def context_get(self, *, matter_id: str | None = None, process_id: str | None = None) -> dict[str, Any]:
        if bool(matter_id) == bool(process_id): raise ValueError("informe exatamente matter_id ou process_id")
        db = self._read()
        try:
            if matter_id:
                if self._owner(db, "MATTER", matter_id) != "MATTER": raise ValueError("owner inválido")
                metadata = db.execute("SELECT * FROM matter_metadata WHERE matter_id=?", (matter_id,)).fetchone()
                processes = [dict(x) for x in db.execute("SELECT p.* FROM processes p JOIN matter_processes mp USING(process_id) WHERE mp.matter_id=? ORDER BY p.process_id", (matter_id,))]
                documents = [dict(x) for x in db.execute("SELECT d.document_id,d.process_id,d.page_count,d.status FROM documents d JOIN matter_processes mp USING(process_id) WHERE mp.matter_id=? ORDER BY d.document_id", (matter_id,))]
                return {"owner_type":"MATTER","owner_id":matter_id,"metadata":dict(metadata) if metadata else None,"processes":processes,"documents":documents}
            if self._owner(db, "PROCESS", process_id) != "PROCESS": raise ValueError("owner inválido")
            metadata = db.execute("SELECT * FROM process_metadata WHERE process_id=?", (process_id,)).fetchone()
            matter = db.execute("SELECT m.* FROM matters m JOIN matter_processes mp USING(matter_id) WHERE mp.process_id=? LIMIT 1", (process_id,)).fetchone()
            documents = [dict(x) for x in db.execute("SELECT document_id,process_id,page_count,status FROM documents WHERE process_id=? ORDER BY document_id", (process_id,))]
            return {"owner_type":"PROCESS","owner_id":process_id,"metadata":dict(metadata) if metadata else None,"matter":dict(matter) if matter else None,"documents":documents}
        finally: db.close()

    def knowledge_get(self, owner_type: str, owner_id: str, target: str) -> dict[str, Any]:
        target = str(target).upper()
        if target not in READ_TARGETS: raise ValueError("target inválido")
        db = self._read()
        try:
            code = self._owner(db, owner_type, owner_id, process_only=target == "HEARINGS")
            if target == "PARTIES": items = party_view_items(db, owner_type, owner_id)
            elif target == "CHRONOLOGY": items = chronology_view_items(db, owner_type, owner_id)
            elif target == "DEADLINES": items = deadline_view_items(db, owner_type, owner_id)
            elif target == "STRATEGY": items = strategy_view_items(db, owner_type, owner_id)
            elif target == "PENDING": items = pending_view_items(db, owner_type, owner_id)
            else: items = hearing_view_items(db, owner_id)
            return {"owner_type": code, "owner_id": owner_id, "target": target, "items": items, "source_refs": [ref for item in items for ref in item.get("source_refs", [])]}
        finally: db.close()

    def knowledge_submit(self, owner_type: str, owner_id: str, target: str, candidates: list[dict[str, Any]], *, origin: str, extraction_run_id: str | None = None, pipeline_version: str = "facade-v1") -> dict[str, Any]:
        target, origin = str(target).upper(), self._origin(origin)
        if target == "STRATEGY": raise ValueError("STRATEGY deve usar strategy_propose")
        if target not in WRITE_TARGETS or not isinstance(candidates, list): raise ValueError("target/candidates inválidos")
        db = self._write()
        try:
            code = self._owner(db, owner_type, owner_id, process_only=target == "HEARINGS")
            prepared = []
            for original in candidates:
                item = dict(original)
                if origin != "HUMAN":
                    if item.get("status") in {"CONFIRMED"} or item.get("confirmation_status") == "CONFIRMED": raise ValueError("operação automática não pode confirmar candidato")
                    item["status"] = "CANDIDATE"
                item["provenance"] = {**(item.get("provenance") or {}), "origin": origin, "pipeline_version": pipeline_version}
                refs = item.get("source_refs") or []
                for ref in refs: self._validate_source(db, owner_type, owner_id, ref)
                if target in {"PARTIES", "CHRONOLOGY"} and refs and not item.get("evidence"):
                    item["evidence"] = [{"source_ref": ref, "extraction_method": origin.lower()} for ref in refs]
                prepared.append(item)
            run_id = extraction_run_id
            run_id = self._ensure_extraction_run(db, code, owner_id, target, origin, run_id, pipeline_version)
            if target == "PARTIES": ids = submit_party_candidates(db, owner_type, owner_id, prepared, extraction_run_id=run_id, commit=False)
            elif target == "CHRONOLOGY": ids = submit_chronology_candidates(db, owner_type, owner_id, prepared, extraction_run_id=run_id, commit=False)
            elif target == "DEADLINES": ids = submit_deadline_candidates(db, owner_type, owner_id, prepared, extraction_run_id=run_id, commit=False)
            elif target == "HEARINGS": ids = submit_hearing_candidates(db, owner_id, prepared, extraction_run_id=run_id, commit=False)
            else: ids = submit_pending_candidates(db, owner_type, owner_id, prepared, extraction_run_id=run_id, commit=False)
            db.commit(); return {"owner_type": code, "owner_id": owner_id, "target": target, "origin": origin, "ids": ids, "extraction_run_id": run_id}
        except Exception:
            db.rollback(); raise
        finally: db.close()

    def strategy_propose(self, owner_type: str, owner_id: str, *, title: str, content: str, entry_type: str = "note", author_type: str, confidence: str | None = None, provenance: dict[str, Any] | None = None, source_refs: list[dict[str, Any]] | None = None, extraction_run_id: str | None = None, pipeline_version: str = "facade-v1") -> dict[str, Any]:
        author = str(author_type).upper()
        if author not in {"HUMAN", "AI"}: raise ValueError("author_type inválido")
        origin = "AI" if author == "AI" else "HUMAN"
        db = self._write()
        try:
            code = self._owner(db, owner_type, owner_id)
            refs = source_refs or []
            for ref in refs: self._validate_source(db, owner_type, owner_id, ref)
            run_id = self._ensure_extraction_run(db, code, owner_id, "STRATEGY", origin, extraction_run_id, pipeline_version)
            item = {"title": title, "content": content, "entry_type": entry_type, "author_type": author,
                    "confidence": confidence, "status": "CANDIDATE",
                    "provenance": {**(provenance or {}), "origin": origin, "source_refs": refs}}
            ids = submit_strategy_candidates(db, owner_type, owner_id, [item], extraction_run_id=run_id, commit=False)
            db.commit()
            return {"owner_type": code, "owner_id": owner_id, "target": "STRATEGY", "origin": origin, "ids": ids, "extraction_run_id": run_id}
        except Exception:
            db.rollback(); raise
        finally: db.close()

    def matter_process_update(self, operation: str, *, matter_id: str, process_id: str | None = None, metadata: dict[str, Any] | None = None, relation: dict[str, Any] | None = None, origin: str = "HUMAN", actor: str | None = None) -> dict[str, Any]:
        operation = str(operation).upper()
        origin = self._origin(origin)
        db = self._write()
        try:
            if operation == "MATTER_METADATA":
                self._owner(db, "MATTER", matter_id); result = upsert_matter_metadata(db, matter_id, commit=False, **(metadata or {}))
            elif operation == "PROCESS_METADATA":
                if not process_id: raise ValueError("process_id obrigatório")
                self._owner(db, "PROCESS", process_id); result = upsert_process_metadata(db, process_id, commit=False, **(metadata or {}))
            elif operation == "ASSOCIATE_PROCESS":
                if not process_id: raise ValueError("process_id obrigatório")
                self._owner(db, "MATTER", matter_id); self._owner(db, "PROCESS", process_id)
                existing = db.execute("SELECT confirmation_status FROM matter_processes WHERE matter_id=? AND process_id=?", (matter_id, process_id)).fetchone()
                requested = str((relation or {}).get("confirmation_status", "PENDING")).upper()
                if requested not in CONFIRMATION_VALUES: raise ValueError("confirmation_status inválido")
                if existing and existing["confirmation_status"] == "CONFLICTING" and origin != "HUMAN": raise ValueError("associação conflitante exige transição humana explícita")
                if origin != "HUMAN" and requested == "CONFIRMED": requested = "PENDING"
                db.execute("INSERT INTO matter_processes(matter_id,process_id,process_role,evidence,document_id,page,confirmation_status) VALUES(?,?,?,?,?,?,?) ON CONFLICT(matter_id,process_id) DO UPDATE SET process_role=excluded.process_role,evidence=excluded.evidence,document_id=excluded.document_id,page=excluded.page,confirmation_status=excluded.confirmation_status", (matter_id, process_id, (relation or {}).get("role"), (relation or {}).get("evidence"), (relation or {}).get("document_id"), (relation or {}).get("page"), requested))
                result = {"matter_id": matter_id, "process_id": process_id, "confirmation_status": requested}
            else: raise ValueError("operation inválida")
            db.commit(); return result
        except Exception:
            db.rollback(); raise
        finally: db.close()
