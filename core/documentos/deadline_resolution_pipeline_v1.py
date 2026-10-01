"""Semantic/rule enrichment pipeline for DeadlineObligation V2."""
from __future__ import annotations

import json
import re
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
        f"""SELECT m.movement_id,m.sequence,m.movement_type,m.title,m.actor,m.occurred_at,m.payload_json,
                   e.event_id,{summary_sql}
              FROM movements m
              LEFT JOIN process_events e ON e.process_id=m.process_id AND e.source_entity='MOVEMENT' AND e.source_id=m.movement_id
              {joins}
             WHERE m.process_id=? ORDER BY m.sequence""",
        (process_id,),
    ).fetchall()
    return [dict(row) for row in rows]

def _movement_folio_range(row: Mapping[str, Any]) -> tuple[int, int] | None:
    try:
        payload = json.loads(str(row.get("payload_json") or "{}"))
    except (TypeError, ValueError):
        return None
    values: list[int] = []
    for component in payload.get("components") or payload.get("documents") or ():
        if not isinstance(component, Mapping):
            continue
        for key in ("folha_inicial", "folha_final", "page_start", "page_end"):
            raw = component.get(key)
            if isinstance(raw, int):
                values.append(raw)
            elif str(raw or "").isdigit():
                values.append(int(raw))
        for page in component.get("pages") or ():
            if not isinstance(page, Mapping):
                continue
            raw = page.get("process_folio_label") or page.get("process_folio")
            if str(raw or "").isdigit():
                values.append(int(raw))
    return (min(values), max(values)) if values else None


_FOLIO_REF = re.compile(
    r"(?:\bfls?\.?\s*|^\s*)(\d{1,6})(?:\s*[/\-–]\s*(\d{1,6}))?\s*(?=:|\b)",
    re.I,
)


def _referenced_folio_range(text: str) -> tuple[int, int] | None:
    match = _FOLIO_REF.search(text or "")
    if not match:
        return None
    start = int(match.group(1))
    end = int(match.group(2) or start)
    return (min(start, end), max(start, end))


def _movement_rule_features(db: sqlite3.Connection, row: Mapping[str, Any]) -> dict[str, bool]:
    label = _norm(" ".join(str(row.get(k) or "") for k in ("movement_type", "title", "summary_text")))
    features = {
        "is_contestation": "contestacao" in label,
        "is_declaratory_embargos": "embargos de declaracao" in label,
        "mentions_preliminary": "preliminar" in label or "art. 337" in label or "artigo 337" in label,
        "mentions_new_fact": any(x in label for x in ("impeditivo", "modificativo", "extintivo")),
        "document_submission": any(x in label for x in ("juntada", "juntando", "documentos", "documento novo")),
    }
    # Generic provider titles such as "Petição (Outras)" hide the act subtype.
    # Inspect canonical pages to derive only compact rule features.
    try:
        payload = json.loads(str(row.get("payload_json") or "{}"))
    except (TypeError, ValueError):
        return features
    document_ids: list[str] = []
    for component in payload.get("components") or payload.get("documents") or ():
        if isinstance(component, Mapping) and component.get("document_id"):
            document_ids.append(str(component["document_id"]))
    if not document_ids:
        return features
    placeholders = ",".join("?" for _ in document_ids)
    parts = db.execute(
        f"SELECT content FROM pages WHERE document_id IN ({placeholders}) ORDER BY document_id,page_number",
        document_ids,
    ).fetchall()
    normalized = _norm(" ".join(str(part[0] or "") for part in parts))
    features["is_contestation"] = features["is_contestation"] or "contestacao" in normalized
    features["is_declaratory_embargos"] = features["is_declaratory_embargos"] or "embargos de declaracao" in normalized
    features["mentions_preliminary"] = features["mentions_preliminary"] or "preliminar" in normalized or "art. 337" in normalized or "artigo 337" in normalized
    features["mentions_new_fact"] = features["mentions_new_fact"] or any(x in normalized for x in ("impeditivo", "modificativo", "extintivo"))
    return features


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
            "sequence": row["sequence"], "movement_type": row.get("movement_type"),
            "title": row.get("title"), "folio_range": _movement_folio_range(row),
            "rule_features": _movement_rule_features(db, row),
        })
    if not candidates:
        return []
    query = str(origin["source_excerpt"] or origin["action_text"] or "")
    referenced = _referenced_folio_range(query)
    if referenced:
        start, end = referenced
        folio_matches = [
            item for item in candidates
            if item.get("folio_range")
            and not (item["folio_range"][1] < start or item["folio_range"][0] > end)
        ]
        if folio_matches:
            # Explicit folio references are documentary evidence and outrank
            # semantic similarity. Preserve multiple matching party acts if the
            # referenced range is genuinely ambiguous.
            return [dict(item, retrieval_method="EXPLICIT_FOLIO_REFERENCE") for item in folio_matches[:max_candidates]]
    normalized_query = _norm(query)
    if "embargos de declaracao" in normalized_query:
        declaratory = [
            item for item in candidates
            if bool((item.get("rule_features") or {}).get("is_declaratory_embargos"))
        ]
        if declaratory:
            nearest_sequence = max(int(item.get("sequence") or 0) for item in declaratory)
            nearest = [item for item in declaratory if int(item.get("sequence") or 0) == nearest_sequence]
            if len(nearest) == 1:
                return [dict(nearest[0], retrieval_method="EXPLICIT_ACT_REFERENCE")]
    if "contestacao" in normalized_query:
        contestations = [
            item for item in candidates
            if bool((item.get("rule_features") or {}).get("is_contestation"))
        ]
        if len(contestations) == 1:
            return [dict(contestations[0], retrieval_method="EXPLICIT_ACT_REFERENCE")]
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
        resolved = str(rule_result.get("resolved_rule_id") or "")
        if resolved and resolved != "JUDICIAL_EXPLICIT_TERM":
            return [resolved]
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
            "SELECT instruction_id,source_excerpt,action_text,source_event_id,source_entity,source_id FROM deadline_instructions WHERE instruction_id=?",
            (obligation["originating_instruction_id"],),
        ).fetchone()
        if not instruction:
            continue

        # A uniquely matched DJEN publication is cleaner semantic evidence than
        # a wide PDF window/header, while the Movement remains the canonical
        # origin of the obligation. Prefer that support for classification.
        semantic_instruction = instruction
        support_ids = list(obligation.get("supporting_instruction_ids") or ())
        publication_supports = []
        if support_ids:
            placeholders = ",".join("?" for _ in support_ids)
            publication_supports = db.execute(
                f"""SELECT instruction_id,source_excerpt,action_text,source_event_id,source_entity,source_id
                      FROM deadline_instructions
                     WHERE instruction_id IN ({placeholders}) AND source_entity='PUBLICATION'""",
                support_ids,
            ).fetchall()
        if len(publication_supports) == 1:
            semantic_instruction = publication_supports[0]

        text = str(
            semantic_instruction["source_excerpt"]
            or semantic_instruction["action_text"]
            or obligation.get("action_text")
            or ""
        )
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
                "semantic_evidence": {
                    "instruction_id": semantic_instruction["instruction_id"],
                    "source_entity": semantic_instruction["source_entity"],
                    "source_id": semantic_instruction["source_id"],
                },
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
