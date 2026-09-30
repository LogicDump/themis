"""Semantic/rule enrichment pipeline for DeadlineObligation V2."""
from __future__ import annotations

import json
import sqlite3
import unicodedata
from typing import Any, Mapping

from core.documentos.deadline_obligation_store_v1 import (
    list_obligations,
    update_obligation_resolution,
)
from core.documentos.deadline_specialist_v1 import (
    analyze_deadline_text,
    derive_legal_context,
    resolve_specialist_rule,
)
from core.retrieval.onnx_embed import generate_embeddings_batch_onnx, generate_embedding_onnx

PIPELINE_VERSION = "deadline-resolution-pipeline-v1"

def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join("".join(ch for ch in text if not unicodedata.combining(ch)).split()).casefold()

def _participant_role_maps(db: sqlite3.Connection, process_id: str) -> tuple[dict[str, str], dict[str, str]]:
    by_name: dict[str, str] = {}
    by_id: dict[str, str] = {}
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='process_participants'").fetchone():
        return by_name, by_id
    for row in db.execute(
        "SELECT participant_id,display_name,base_role FROM process_participants WHERE process_id=?",
        (process_id,),
    ).fetchall():
        base = str(row["base_role"])
        role = {"CLAIMANT": "PLAINTIFF", "RESPONDENT": "DEFENDANT"}.get(base, base)
        by_name[_norm(row["display_name"])] = role
        by_id[str(row["participant_id"])] = role
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='representations'").fetchone():
        for row in db.execute(
            """SELECT rep.display_name AS representative_name, represented.base_role
                 FROM representations r
                 JOIN process_participants rep ON rep.participant_id=r.representative_participant_id
                 JOIN process_participants represented ON represented.participant_id=r.represented_participant_id
                WHERE r.process_id=?""",
            (process_id,),
        ).fetchall():
            role = {"CLAIMANT": "PLAINTIFF", "RESPONDENT": "DEFENDANT"}.get(str(row["base_role"]))
            if role:
                by_name[_norm(row["representative_name"])] = role
    return by_name, by_id

def _actor_role(actor: Any, by_name: Mapping[str, str]) -> str | None:
    value = _norm(actor)
    if not value:
        return None
    if any(token in value for token in ("autor", "autora", "requerente", "exequente")):
        return "PLAINTIFF"
    if any(token in value for token in ("reu", "requerido", "requerida", "executado", "executada")):
        return "DEFENDANT"
    exact = by_name.get(value)
    if exact in {"PLAINTIFF", "DEFENDANT"}:
        return exact
    matches = {role for name, role in by_name.items() if name and (name in value or value in name)}
    return next(iter(matches)) if len(matches) == 1 and next(iter(matches)) in {"PLAINTIFF", "DEFENDANT"} else None
def _summary_rows(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {"movements", "process_events"}.issubset(tables):
        return []
    summary_sql = "NULL AS summary_text"
    joins = ""
    if {"movement_summaries", "movement_summary_source_state"}.issubset(tables):
        summary_sql = "s.summary_text"
        joins = """LEFT JOIN movement_summary_source_state st ON st.movement_id=m.movement_id
                   LEFT JOIN movement_summaries s ON s.movement_id=m.movement_id
                    AND st.eligible=1 AND s.source_hash=st.source_hash
                    AND s.summary_version=(SELECT max(x.summary_version) FROM movement_summaries x WHERE x.movement_id=m.movement_id)"""
    rows = db.execute(
        f"""SELECT m.movement_id,m.sequence,m.movement_type,m.title,m.actor,m.occurred_at,
                   e.event_id,{summary_sql}
              FROM movements m
              LEFT JOIN process_events e ON e.process_id=m.process_id AND e.source_entity='MOVEMENT' AND e.source_id=m.movement_id
              {joins}
             WHERE m.process_id=? ORDER BY m.sequence""",
        (process_id,),
    ).fetchall()
    return [dict(row) for row in rows]

def _current_origin(db: sqlite3.Connection, obligation: Mapping[str, Any]) -> dict[str, Any] | None:
    return db.execute(
        """SELECT i.*,m.sequence,coalesce(m.occurred_at,e.event_date) AS occurred_at
             FROM deadline_instructions i
             LEFT JOIN movements m ON m.movement_id=i.movement_id
             LEFT JOIN process_events e ON e.event_id=i.source_event_id
            WHERE i.instruction_id=?""",
        (obligation["originating_instruction_id"],),
    ).fetchone()

def _antecedent_context(
    db: sqlite3.Connection,
    process_id: str,
    obligation: Mapping[str, Any],
    *,
    max_candidates: int = 8,
) -> list[dict[str, Any]]:
    origin = _current_origin(db, obligation)
    if not origin:
        return []
    by_name, _ = _participant_role_maps(db, process_id)
    rows = _summary_rows(db, process_id)
    current_sequence = origin["sequence"] if "sequence" in origin.keys() else None
    current_date = str(origin["occurred_at"] or "") if "occurred_at" in origin.keys() else ""
    candidates: list[dict[str, Any]] = []
    for row in rows:
        if current_sequence is not None and row["sequence"] >= current_sequence:
            continue
        if current_sequence is None and current_date and row.get("occurred_at") and str(row["occurred_at"]) > current_date:
            continue
        role = _actor_role(row.get("actor"), by_name)
        if role not in {"PLAINTIFF", "DEFENDANT"}:
            continue
        label = _norm(" ".join(str(row.get(k) or "") for k in ("movement_type", "title")))
        if not any(marker in label for marker in ("peticao", "contestacao", "manifestacao", "replica", "embargo", "recurso", "juntada")):
            continue
        text = str(row.get("summary_text") or row.get("title") or row.get("movement_type") or "")
        if not text:
            continue
        candidates.append({
            "type": "ANTECEDENT_CANDIDATE", "event_id": row.get("event_id"),
            "movement_id": row["movement_id"], "actor_role": role, "text": text,
            "sequence": row["sequence"],
        })
    if not candidates:
        return []
    query = str(origin["source_excerpt"] or origin["action_text"] or "")
    qvec = generate_embedding_onnx(query, is_query=True)
    vectors = generate_embeddings_batch_onnx([item["text"] for item in candidates[:max_candidates * 3]])
    scored = []
    if qvec and vectors:
        import numpy as np
        q = np.asarray(qvec, dtype=np.float32)
        for item, vector in zip(candidates[:max_candidates * 3], vectors):
            if vector:
                score = float(np.dot(q, np.asarray(vector, dtype=np.float32)))
                scored.append((score, item))
    if not scored:
        # Without embeddings there is no semantic evidence to prefer the
        # latest act. Preserve the plausible antecedents so the specialist
        # abstains when the relation is unresolved.
        return candidates[:max_candidates]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    top_score = scored[0][0]
    # Preserve close candidates; opposite poles within the semantic margin
    # deliberately become AMBIGUOUS_REVIEW instead of a guessed recipient.
    selected = [dict(item, semantic_score=score) for score, item in scored if top_score - score <= 0.025]
    return selected[:max_candidates]

def _resolution_method(output: Any) -> str:
    if output.antecedent_source_event_id:
        return "ANTECEDENT_RELATION"
    if output.recipient_role == "BOTH_PARTIES":
        return "ALL_PARTIES"
    if output.recipient_role not in {None, "UNRESOLVED"}:
        return "EXPLICIT_ROLE"
    return "UNRESOLVED"

def _candidate_rules(output: Any, rule_result: Mapping[str, Any]) -> list[str]:
    if output.explicit_term_value is not None and output.explicit_term_unit not in {"UNSPECIFIED", "DATE_CERTAIN"}:
        return ["JUDICIAL_EXPLICIT_TERM"]
    explanation = rule_result.get("explanation") or {}
    candidates = explanation.get("candidate_rule_ids") or []
    return sorted({str(item) for item in candidates})

def enrich_process_obligations(db: sqlite3.Connection, process_id: str) -> dict[str, Any]:
    """Resolve semantic facts and legal rule hypotheses for one process."""
    obligations = list_obligations(db, process_id)
    legal_context, legal_context_provenance = derive_legal_context(db, process_id)
    resolved = review = nonoperative = 0
    for obligation in obligations:
        instruction = db.execute(
            "SELECT source_excerpt,action_text,source_event_id,source_entity,source_id FROM deadline_instructions WHERE instruction_id=?",
            (obligation["originating_instruction_id"],),
        ).fetchone()
        if not instruction:
            continue
        text = str(instruction["source_excerpt"] or instruction["action_text"] or obligation.get("action_text") or "")
        context: list[dict[str, Any]] = []
        if any(marker in _norm(text) for marker in ("parte contraria", "parte adversa", "polo oposto", "ex advers")):
            context = _antecedent_context(db, process_id, obligation)
        output = analyze_deadline_text(text, context=context, db=db, process_id=process_id)
        relevant_date = db.execute(
            "SELECT event_date FROM process_events WHERE event_id=?", (instruction["source_event_id"],)
        ).fetchone()
        rule_result = resolve_specialist_rule(
            output, legal_context, context=context,
            relevant_date=relevant_date[0] if relevant_date else None,
        )
        candidate_rules = _candidate_rules(output, rule_result)
        semantic_review = output.review_required
        rule_review = bool(rule_result.get("review_required"))
        review_required = semantic_review or rule_review
        provenance = {
            "deadline_resolution_pipeline": {
                "version": PIPELINE_VERSION,
                "specialist_model_version": "deadline-specialist-encoder-heads-v1",
                "specialist": output.as_dict(),
                "antecedent_candidates": context,
                "legal_context": legal_context.as_dict() if legal_context else None,
                "legal_context_provenance": legal_context_provenance,
                "rule_resolution": rule_result,
            }
        }
        update_obligation_resolution(
            db, obligation["obligation_id"],
            antecedent_source_event_id=output.antecedent_source_event_id,
            recipient_role=output.recipient_role,
            recipient_participant_ids=list(output.recipient_participant_ids),
            recipient_resolution_method=_resolution_method(output),
            candidate_rule_ids=candidate_rules,
            model_preferred_rule_id=output.model_preferred_rule_id,
            resolved_rule_id=rule_result.get("resolved_rule_id"),
            review_required=review_required,
            provenance=provenance,
        )
        if not output.operative_instruction:
            nonoperative += 1
        elif review_required:
            review += 1
        else:
            resolved += 1
    return {
        "process_id": process_id, "obligations": len(obligations),
        "resolved": resolved, "review_required": review,
        "nonoperative": nonoperative,
        "legal_context": legal_context.as_dict() if legal_context else None,
    }
