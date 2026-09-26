"""Mecanismo de Retrieval Híbrido (Lexical FTS5 + Semantic EmbeddingGemma + RRF)."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from core.retrieval.ollama_embed import generate_embedding, generate_embedding_with_meta
from core.retrieval.vector_store import EMBEDDING_MODEL_NAME, VectorStore, cosine_similarity
from core.runtime_paths import index_db_path, process_db_path


STOP_WORDS = {"de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas", "para", "por", "com", "sem", "ou", "se", "que", "ao", "aos", "as", "os", "um", "uma"}


def tokenize_query(query: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[\wÀ-ÿ]{2,}", query) if len(t) >= 2 and t.lower() not in STOP_WORDS]


def load_process_pages(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    sql = """SELECT p.page_id, p.document_id, p.page_number, p.content, p.quality, p.process_folio, p.page_class
        FROM pages p
        JOIN documents d USING(document_id)
        WHERE d.process_id=?
        ORDER BY d.created_at, p.page_number"""
    rows = db.execute(sql, (process_id,)).fetchall()

    has_evidence = (
        db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='evidence'").fetchone()
        is not None
    )
    evidence_by_page: dict[str, list[dict[str, Any]]] = {}
    if has_evidence:
        ev_rows = db.execute(
            """SELECT e.page_id, e.field, e.value, e.context, e.folio, e.act_date
            FROM evidence e
            JOIN pages p USING(page_id)
            JOIN documents d USING(document_id)
            WHERE d.process_id=?""",
            (process_id,),
        ).fetchall()
        for ev in ev_rows:
            evidence_by_page.setdefault(ev["page_id"], []).append({
                "field": ev["field"],
                "value": ev["value"],
                "context": ev["context"],
                "folio": ev["folio"],
                "act_date": ev["act_date"],
            })

    resolved_pages: list[dict[str, Any]] = []
    for row in rows:
        pr = dict(row)
        resolved_pages.append({
            "page_id": pr["page_id"],
            "document_id": pr["document_id"],
            "page_number": pr["page_number"],
            "content": pr["content"],
            "quality": pr["quality"],
            "page_class": pr["page_class"],
            "evidence": evidence_by_page.get(pr["page_id"], []),
            "process_folio": pr["process_folio"],
            "folio_resolution": "MATERIALIZED" if pr["process_folio"] is not None else "UNKNOWN",
        })
    return resolved_pages



def ensure_process_embeddings(
    process_id: str,
    pages: list[dict[str, Any]],
    vector_store: VectorStore,
    *,
    ollama_url: str = "http://127.0.0.1:11434",
    backend: str | None = None,
) -> None:
    indexed_ids = vector_store.get_indexed_page_ids(process_id, EMBEDDING_MODEL_NAME)
    for p in pages:
        if p["page_id"] not in indexed_ids:
            text = (p.get("content") or "").strip()
            if not text:
                continue
            vec, meta = generate_embedding_with_meta(
                text,
                is_query=False,
                model=EMBEDDING_MODEL_NAME,
                ollama_url=ollama_url,
                backend=backend,
            )
            if vec:
                vector_store.save_embedding(
                    page_id=p["page_id"],
                    document_id=p["document_id"],
                    process_id=process_id,
                    page_number=p["page_number"],
                    vector=vec,
                    model=meta.get("model", EMBEDDING_MODEL_NAME),
                    backend=meta.get("backend", "onnx"),
                    model_version=meta.get("model_version", "v1"),
                    quantization=meta.get("quantization", "int8"),
                )


def search_hybrid(
    process_id: str,
    query: str,
    top_k: int = 5,
    *,
    db_path: Path | str | None = None,
    vector_db_path: Path | str | None = None,
    ollama_url: str = "http://127.0.0.1:11434",
) -> list[dict[str, Any]]:
    clean_query = query.strip()
    if not clean_query:
        return []

    if db_path is not None:
        target_db = Path(db_path).resolve()
    else:
        try:
            target_db = process_db_path(process_id).resolve()
        except ValueError:
            # Synthetic/non-CNJ fixtures retain the explicit legacy adapter.
            target_db = index_db_path().resolve()
    if not target_db.is_file():
        return []

    if vector_db_path:
        vec_path = Path(vector_db_path).resolve()
    else:
        probe = sqlite3.connect(f"file:{target_db.as_posix()}?mode=ro", uri=True)
        try:
            local_vectors = probe.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='page_embeddings'").fetchone()
        finally:
            probe.close()
        if local_vectors:
            vec_path = target_db
        else:
            themis_vec = target_db.parent / "themis_vectors.db"
            juridico_vec = target_db.parent / "juridico_vectors.db"
            vec_path = themis_vec if themis_vec.exists() else (juridico_vec if juridico_vec.exists() else themis_vec)
    vector_store = VectorStore(vec_path)

    conn = sqlite3.connect(str(target_db))
    try:
        conn.row_factory = sqlite3.Row
        pages = load_process_pages(conn, process_id)
    finally:
        conn.close()

    if not pages:
        return []

    # 1. Lexical Scoring (FTS5 / Term Matching)
    tokens = tokenize_query(clean_query)
    lexical_scores: dict[str, float] = {}
    for p in pages:
        content_lower = (p.get("content") or "").lower()
        score = 0.0
        # Exact match bonus
        if clean_query.lower() in content_lower:
            score += 10.0
        # Token match
        for t in tokens:
            count = content_lower.count(t)
            if count > 0:
                score += 1.0 + min(count, 5) * 0.2
        lexical_scores[p["page_id"]] = score

    # Sort lexical ranks
    sorted_lex = sorted(pages, key=lambda p: lexical_scores.get(p["page_id"], 0.0), reverse=True)
    lex_ranks = {p["page_id"]: rank for rank, p in enumerate(sorted_lex, start=1)}

    # 2. Semantic Scoring (EmbeddingGemma)
    ensure_process_embeddings(process_id, pages, vector_store, ollama_url=ollama_url)
    stored_vectors = {v["page_id"]: v["vector"] for v in vector_store.get_process_vectors(process_id, EMBEDDING_MODEL_NAME)}

    query_vec, query_meta = generate_embedding_with_meta(clean_query, is_query=True, model=EMBEDDING_MODEL_NAME, ollama_url=ollama_url)

    # Validar correspondência exata de espaço vetorial entre a query e o índice gravado
    idx_meta = vector_store.get_index_metadata(process_id, EMBEDDING_MODEL_NAME)
    is_compatible = True
    if query_vec and idx_meta:
        from core.retrieval.vector_store import is_exact_space_match
        query_sig = {
            "model": query_meta.get("model", EMBEDDING_MODEL_NAME),
            "model_version": query_meta.get("model_version", "v1"),
            "backend": query_meta.get("backend", "onnx"),
            "quantization": query_meta.get("quantization", "int8"),
            "dim": len(query_vec),
        }
        is_compatible = is_exact_space_match(idx_meta, query_sig)
        if not is_compatible:
            import logging
            logging.getLogger(__name__).warning(
                f"Isolamento vetorial: backend/quantização da query ({query_sig.get('backend')}/{query_sig.get('quantization')}) "
                f"não corresponde exatamente ao índice gravado ({idx_meta.get('backend')}/{idx_meta.get('quantization')}) no processo {process_id}. "
                f"Desativando busca semântica para esta consulta."
            )

    sem_scores: dict[str, float] = {}
    if query_vec and stored_vectors and is_compatible:
        for p in pages:
            vec = stored_vectors.get(p["page_id"])
            if vec:
                sem_scores[p["page_id"]] = cosine_similarity(query_vec, vec)
            else:
                sem_scores[p["page_id"]] = 0.0

    sorted_sem = sorted(pages, key=lambda p: sem_scores.get(p["page_id"], 0.0), reverse=True)
    sem_ranks = {p["page_id"]: rank for rank, p in enumerate(sorted_sem, start=1)}

    # 3. Reciprocal Rank Fusion (RRF k=60)
    rrf_scores: dict[str, float] = {}
    has_semantic = bool(query_vec and stored_vectors)

    for p in pages:
        pid = p["page_id"]
        r_lex = lex_ranks.get(pid, len(pages))
        r_sem = sem_ranks.get(pid, len(pages))

        lex_component = 1.0 / (60.0 + r_lex) if lexical_scores.get(pid, 0.0) > 0 else 0.0
        sem_component = 1.0 / (60.0 + r_sem) if has_semantic and pid in stored_vectors else 0.0

        rrf_scores[pid] = lex_component + sem_component

    # Filter pages with some signal
    candidates = [p for p in pages if rrf_scores.get(p["page_id"], 0.0) > 0]
    if not candidates:
        candidates = pages

    ranked = sorted(candidates, key=lambda p: rrf_scores.get(p["page_id"], 0.0), reverse=True)

    results: list[dict[str, Any]] = []
    for idx, p in enumerate(ranked[:top_k], start=1):
        raw_text = (p.get("content") or "").strip()
        excerpt = raw_text[:400] + ("..." if len(raw_text) > 400 else "")
        score = rrf_scores.get(p["page_id"], 0.0)
        results.append({
            "source_id": idx,
            "source_ref": {
                "process_id": process_id,
                "document_id": p["document_id"],
                "pdf_page": p["page_number"],
                "process_folio": p["process_folio"],
            },
            "excerpt": excerpt,
            "score": round(score, 6),
            "page_id": p["page_id"],
            "evidence": p.get("evidence", []),
            "autos_navigation": {
                "process_id": process_id,
                "document_id": p["document_id"],
                "page": p["page_number"],
                "folio": p["process_folio"],
                "target_text": excerpt[:200],
                "autos_path": f"/processes/{process_id}/autos",
            },
        })
    return results
