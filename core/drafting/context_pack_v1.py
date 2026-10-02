"""DraftingTask + LegalContextPack V1.

The target act is always carried in full canonical text. Retrieval is used only
for the rest of the process and never replaces the target source.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.documentos.movement_summary_store_v1 import source_pages, source_text_and_hash
from core.documentos.participant_context_store_v1 import list_participants, list_representations
from core.retrieval.hierarchical_retrieval import search_hierarchical_evidence
from core.retrieval.hybrid_retrieval import search_hybrid

SCHEMA_VERSION = "legal-context-pack-v1"
TASK_KINDS = frozenset({
    "RESPOND_TO_MOVEMENT",
    "CHALLENGE_MOVEMENT",
    "GENERAL_PETITION",
})


@dataclass(frozen=True)
class DraftingTask:
    task_id: str
    process_id: str
    task_kind: str
    goal: str
    target_movement_id: str | None = None

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id obrigatório")
        if not self.process_id.strip():
            raise ValueError("process_id obrigatório")
        if self.task_kind not in TASK_KINDS:
            raise ValueError("task_kind inválido")
        if not self.goal.strip():
            raise ValueError("goal obrigatório")
        if self.task_kind != "GENERAL_PETITION" and not (self.target_movement_id or "").strip():
            raise ValueError("target_movement_id obrigatório para tarefa dirigida a ato")


def load_target_document(
    db: sqlite3.Connection,
    process_id: str,
    movement_id: str,
) -> dict[str, Any]:
    """Load the full own-piece canonical text of the target Movement."""
    row = db.execute(
        """SELECT movement_id,process_id,sequence,title,actor,occurred_at,movement_type
           FROM movements WHERE movement_id=? AND process_id=?""",
        (movement_id, process_id),
    ).fetchone()
    if not row:
        raise ValueError("Movement alvo não pertence ao processo")
    row = dict(row)
    pages = source_pages(db, movement_id)
    if not pages:
        raise ValueError("Movement alvo sem páginas próprias canônicas")
    full_text, source_hash = source_text_and_hash(db, movement_id)
    if not full_text.strip():
        raise ValueError("Movement alvo sem texto canônico")
    return {
        "process_id": process_id,
        "movement_id": movement_id,
        "sequence": row.get("sequence"),
        "title": row.get("title"),
        "actor": row.get("actor"),
        "occurred_at": row.get("occurred_at"),
        "movement_type": row.get("movement_type"),
        "source_mode": "FULL_CANONICAL",
        "source_hash": source_hash,
        "full_text": full_text,
        "pages": [
            {
                "document_id": page["document_id"],
                "pdf_page": int(page["page_number"]),
                "content": page["content"],
            }
            for page in pages
        ],
    }


def build_process_frame(db: sqlite3.Connection, process_id: str) -> dict[str, Any]:
    """Build the smallest stable process frame needed by drafting."""
    row = db.execute(
        "SELECT process_id,status FROM processes WHERE process_id=?",
        (process_id,),
    ).fetchone()
    if not row:
        raise ValueError("Processo não encontrado")
    frame: dict[str, Any] = {
        "process_id": str(row["process_id"]),
        "status": row["status"],
        "metadata": {},
        "participants": [],
        "representations": [],
    }
    tables = {
        str(item[0])
        for item in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    if "process_metadata" in tables:
        metadata = db.execute(
            "SELECT * FROM process_metadata WHERE process_id=?",
            (process_id,),
        ).fetchone()
        if metadata:
            allowed = {
                "classe", "assunto", "tribunal", "comarca", "unidade",
                "grau", "status", "fase", "version",
            }
            frame["metadata"] = {
                key: metadata[key]
                for key in metadata.keys()
                if key in allowed and metadata[key] not in (None, "")
            }
            try:
                provenance_raw = metadata["provenance_json"] if "provenance_json" in metadata.keys() else "{}"
                frame["metadata"]["provenance"] = json.loads(provenance_raw or "{}")
            except (TypeError, json.JSONDecodeError):
                frame["metadata"]["provenance"] = {}
    if "process_participants" in tables:
        frame["participants"] = [
            {
                "participant_id": item["participant_id"],
                "display_name": item["display_name"],
                "base_role": item["base_role"],
                "status": item.get("status"),
                "confidence": item.get("confidence"),
                "source_refs": item.get("source_refs") or [],
                "provenance": item.get("provenance") or {},
            }
            for item in list_participants(db, process_id)
        ]
    if "representations" in tables:
        frame["representations"] = [
            {
                "representation_id": item["representation_id"],
                "representative_participant_id": item["representative_participant_id"],
                "represented_participant_id": item["represented_participant_id"],
                "representation_kind": item["representation_kind"],
                "oab_number": item.get("oab_number"),
                "oab_uf": item.get("oab_uf"),
                "status": item.get("status"),
                "confidence": item.get("confidence"),
                "source_refs": item.get("source_refs") or [],
                "provenance": item.get("provenance") or {},
            }
            for item in list_representations(db, process_id)
        ]
    return frame


def _own_page_movement_index(
    process_id: str,
    db_path: Path | str,
) -> dict[tuple[str, int], dict[str, Any]]:
    """Map canonical own-piece pages to their Movement; ambiguous ownership is excluded."""
    target = Path(db_path).resolve()
    db = sqlite3.connect(f"file:{target.as_posix()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        rows = db.execute(
            "SELECT movement_id,title,sequence FROM movements WHERE process_id=? ORDER BY sequence,movement_id",
            (process_id,),
        ).fetchall()
        index: dict[tuple[str, int], dict[str, Any] | None] = {}
        for row in rows:
            owner = {
                "movement_id": str(row["movement_id"]),
                "movement_title": row["title"],
                "movement_sequence": row["sequence"],
            }
            for page in source_pages(db, owner["movement_id"]):
                key = (str(page["document_id"]), int(page["page_number"]))
                current = index.get(key)
                if current is None and key in index:
                    continue
                if current and current["movement_id"] != owner["movement_id"]:
                    index[key] = None
                else:
                    index[key] = owner
        return {key: value for key, value in index.items() if value is not None}
    finally:
        db.close()


def retrieve_related_sources(
    task: DraftingTask,
    issues: list[dict[str, str]],
    *,
    db_path: Path | str,
    vector_db_path: Path | str | None = None,
    top_k_per_issue: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve source-grounded context from the rest of the process."""
    if top_k_per_issue < 1:
        raise ValueError("top_k_per_issue deve ser positivo")
    seen_issue_ids: set[str] = set()
    output: list[dict[str, Any]] = []
    dedupe: set[tuple[str, str, int, str]] = set()
    ownership_index: dict[tuple[str, int], dict[str, Any]] | None = None

    def append_hit(
        issue_id: str,
        query: str,
        hit: dict[str, Any],
        *,
        route: str,
    ) -> bool:
        movement_id = hit.get("movement_id")
        if task.target_movement_id and movement_id == task.target_movement_id:
            return False
        source_ref = hit.get("source_ref") or {}
        key = (
            issue_id,
            str(source_ref.get("document_id") or ""),
            int(source_ref.get("pdf_page") or 0),
            str(hit.get("excerpt") or ""),
        )
        if key in dedupe:
            return False
        dedupe.add(key)
        candidate_raw = "\0".join((
            issue_id,
            str(movement_id or ""),
            str(source_ref.get("document_id") or ""),
            str(source_ref.get("pdf_page") or ""),
            str(hit.get("excerpt") or ""),
        ))
        candidate_id = "ctx_" + hashlib.sha256(candidate_raw.encode("utf-8")).hexdigest()[:24]
        output.append({
            "candidate_id": candidate_id,
            "issue_id": issue_id,
            "query": query,
            "movement_id": movement_id,
            "movement_title": hit.get("movement_title"),
            "excerpt": hit.get("excerpt"),
            "score": hit.get("score"),
            "source_ref": source_ref,
            "autos_navigation": hit.get("autos_navigation"),
            "source_mode": "RETRIEVED_EXCERPT",
            "retrieval_route": route,
        })
        return True

    for issue in issues:
        issue_id = str(issue.get("issue_id") or "").strip()
        query = str(issue.get("retrieval_query") or issue.get("query") or "").strip()
        if not issue_id or not query or issue_id in seen_issue_ids:
            raise ValueError("issues exigem issue_id/retrieval_query únicos e não vazios")
        seen_issue_ids.add(issue_id)
        accepted = 0
        hits = search_hierarchical_evidence(
            task.process_id,
            query,
            max(top_k_per_issue * 2, top_k_per_issue),
            db_path=db_path,
            vector_db_path=vector_db_path,
        )
        for hit in hits:
            if append_hit(issue_id, query, hit, route="HIERARCHICAL"):
                accepted += 1
                if accepted >= top_k_per_issue:
                    break

        # The hierarchical route may concentrate entirely on the target act.
        # For drafting context, the target is already included in full, so fall
        # back to process-wide hybrid retrieval and map only canonical own-piece
        # pages back to their Movements.
        if accepted < top_k_per_issue:
            if ownership_index is None:
                ownership_index = _own_page_movement_index(task.process_id, db_path)
            hybrid_hits = search_hybrid(
                task.process_id,
                query,
                max(top_k_per_issue * 8, 20),
                db_path=db_path,
                vector_db_path=vector_db_path,
            )
            for hit in hybrid_hits:
                source_ref = hit.get("source_ref") or {}
                owner = ownership_index.get((
                    str(source_ref.get("document_id") or ""),
                    int(source_ref.get("pdf_page") or 0),
                ))
                if not owner:
                    continue
                enriched = {
                    **hit,
                    "movement_id": owner["movement_id"],
                    "movement_title": owner["movement_title"],
                    "movement_sequence": owner["movement_sequence"],
                }
                if append_hit(issue_id, query, enriched, route="HYBRID_FALLBACK"):
                    accepted += 1
                    if accepted >= top_k_per_issue:
                        break
    return output



def apply_context_selection(
    candidates: list[dict[str, Any]],
    selections: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    """Apply a validated selector result without creating new semantic content."""
    by_id = {
        str(item.get("candidate_id") or ""): item
        for item in candidates
        if str(item.get("candidate_id") or "").strip()
    }
    selected: list[dict[str, Any]] = []
    seen_candidates: set[str] = set()
    promote: list[str] = []
    seen_promote: set[str] = set()
    unresolved: list[dict[str, Any]] = []
    for selection in selections:
        issue_id = str(selection.get("issue_id") or "")
        for candidate_id in selection.get("candidate_ids") or []:
            candidate = by_id.get(str(candidate_id))
            if candidate is None:
                raise ValueError(f"selector referenciou candidate inexistente: {candidate_id}")
            if str(candidate.get("issue_id") or "") != issue_id:
                raise ValueError(f"candidate pertence a outra issue: {candidate_id}")
            if candidate_id not in seen_candidates:
                selected.append(candidate)
                seen_candidates.add(candidate_id)
        for movement_id in selection.get("promote_movement_ids") or []:
            value = str(movement_id)
            if value and value not in seen_promote:
                promote.append(value)
                seen_promote.add(value)
        if selection.get("unresolved"):
            unresolved.append({
                "issue_id": issue_id,
                "reason": "NO_SUFFICIENT_RETRIEVED_CONTEXT",
            })
    return selected, promote, unresolved


def load_related_documents(
    db: sqlite3.Connection,
    process_id: str,
    movement_ids: list[str],
    *,
    target_movement_id: str | None = None,
) -> list[dict[str, Any]]:
    """Promote selected related Movements to full canonical text."""
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for movement_id in movement_ids:
        movement_id = str(movement_id).strip()
        if not movement_id or movement_id in seen:
            continue
        if target_movement_id and movement_id == target_movement_id:
            raise ValueError("ato-alvo já está integralmente no pacote e não deve ser promovido")
        result.append(load_target_document(db, process_id, movement_id))
        seen.add(movement_id)
    return result


def build_legal_context_pack(
    task: DraftingTask,
    target_document: dict[str, Any] | None,
    *,
    process_frame: dict[str, Any],
    issues: list[dict[str, Any]],
    related_sources: list[dict[str, Any]],
    related_documents: list[dict[str, Any]] | None = None,
    unresolved_points: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the handoff consumed later by a drafting model."""
    if task.task_kind != "GENERAL_PETITION":
        if not target_document or target_document.get("source_mode") != "FULL_CANONICAL":
            raise ValueError("ato alvo deve entrar integralmente no LegalContextPack")
        if target_document.get("movement_id") != task.target_movement_id:
            raise ValueError("target_document divergente do DraftingTask")
    if str(process_frame.get("process_id") or "") != task.process_id:
        raise ValueError("process_frame divergente do DraftingTask")
    issue_ids = [str(item.get("issue_id") or "") for item in issues]
    if any(not item for item in issue_ids) or len(issue_ids) != len(set(issue_ids)):
        raise ValueError("issues inválidos/duplicados")
    issue_set = set(issue_ids)
    if any(str(item.get("issue_id") or "") not in issue_set for item in related_sources):
        raise ValueError("related_source sem issue correspondente")
    documents = related_documents or []
    for document in documents:
        if (
            document.get("source_mode") != "FULL_CANONICAL"
            or document.get("process_id") != task.process_id
            or not str(document.get("movement_id") or "").strip()
        ):
            raise ValueError("related_document deve ser Movement integral do mesmo processo")
        if task.target_movement_id and document.get("movement_id") == task.target_movement_id:
            raise ValueError("related_document não pode duplicar o ato-alvo")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task": asdict(task),
        "target_document": target_document,
        "process_frame": process_frame,
        "issues": issues,
        "related_sources": related_sources,
        "related_documents": documents,
        "unresolved_points": unresolved_points or [],
        "source_policy": {
            "target": "FULL_CANONICAL_REQUIRED",
            "related_excerpts": "SOURCE_GROUNDED_RETRIEVAL",
            "related_documents": "FULL_CANONICAL_WHEN_PROMOTED",
            "process_frame": "ORIENTATION_ONLY_REVALIDATE_IF_MATERIAL",
            "summaries": "ROUTING_ONLY",
            "final_material_claims": "REVALIDATE_AGAINST_SOURCE",
        },
    }
    payload["pack_fingerprint"] = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return payload
