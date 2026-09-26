"""Movement-routed, passage-grounded retrieval for cited process answers.

Movement summaries are used only to select candidate Movements. Returned evidence
and citations are built exclusively from temporary blocks of ``pages.content``.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
import threading
import unicodedata
from collections import OrderedDict
from pathlib import Path
from typing import Any

from core.retrieval.hybrid_retrieval import search_hybrid, tokenize_query
from core.retrieval.vector_store import (
    EMBEDDING_MODEL_NAME,
    cosine_similarity,
    is_exact_space_match,
    unpack_vector,
)

_SUMMARY_QUERY_CACHE: OrderedDict[str, list[float]] = OrderedDict()
_SUMMARY_EMBED_CACHE_LOCK = threading.Lock()
_SUMMARY_QUERY_CACHE_LIMIT = 128
_SUMMARY_ROUTE_SHORTLIST = 20
_SUMMARY_SEMANTIC_SHORTLIST = 20
_VALUE_QUERY_WORDS = {"valor", "quanto"}
_INTENT_WORDS = {
    "qual", "quais", "quem", "quando", "onde", "como", "quanto", "quantos", "quantas",
    "me", "diga", "informe", "mostre", "data", "dia", "hora", "horario", "horarios",
    "valor", "valores", "numero", "nome", "existe", "houve", "ocorreu", "foi", "sao",
    "esta", "estao", "do", "da", "dos", "das", "de", "em", "no", "na", "nos", "nas",
    "para", "por", "com", "e", "o", "a", "os", "as", "um", "uma", "um", "pedido",
    "pedidos", "autora", "autor", "reu", "requerente", "requerido", "processo", "autos",
    "inicial", "inicialmente", "posterior", "posteriormente",
}
_SEMANTIC_STOP_WORDS = _INTENT_WORDS | {
    "que", "se", "ao", "aos", "foi", "ser", "sendo", "sido", "conforme", "termos", "autos",
    "processual", "processuais", "parte", "partes", "juizo", "juiz", "decisao", "documento",
    "documentos", "intimacao", "intimado", "intimadas", "certifico", "certidao", "presente",
    "seguinte", "seguida", "respectivo", "respectiva", "devidamente", "requer", "requerer",
    "manifesta", "manifestacao", "processo", "movimento", "movimentacao", "pedido", "pedidos",
}
_SUMMARY_FTS_STOP_WORDS = {
    "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas", "para", "por", "com",
    "sem", "ou", "se", "que", "ao", "aos", "as", "os", "um", "uma", "e", "o", "a",
}
_SUMMARY_DATE_RE = re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b|\b\d{1,2}:\d{2}\b")
_CNJ_NUMBER_RE = re.compile(r"\b\d{7}-\s?\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")
_AMOUNT_RE = re.compile(
    r"(?:\b\d[\d.,]*\s*%|\bR\$\s*\d[\d.,]*|\bsal[aá]rio[s]?[- ]m[ií]nimo[s]?)",
    re.IGNORECASE,
)
_INITIAL_AMOUNT_RE = re.compile(r"(?:\b\d[\d.,]*\s*%|\bsal[aá]rio[s]?[- ]m[ií]nimo[s]?)", re.IGNORECASE)
_REQUEST_ITEM_RE = re.compile(r"(?im)^\s*(?:[-*+]\s+|\d+[.)]\s+)(?:que\b|requer(?:-se)?\b)")
_REQUEST_STATEMENT_RE = re.compile(
    r"\b(?:requer(?:-se)?|pede(?:-se)?|pleiteia|pleiteado|solicita|postula|que\s+seja\s+(?:concedid[oa]|majorad[oa]|fixad[oa]))\b",
    re.IGNORECASE,
)
_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
_INITIAL_SCOPE_RE = re.compile(r"\b(?:peticao\s+inicial|pedido\s+inicial|inicialmente)\b")
_POSTERIOR_SCOPE_RE = re.compile(r"\b(?:pedido\s+posterior|posteriormente|posterior)\b")


def _fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).casefold()


def _has_date_or_time(text: str) -> bool:
    # CNJ identifiers contain dotted numeric groups and must not count as dates.
    without_process_ids = _CNJ_NUMBER_RE.sub(" ", text or "")
    return bool(_SUMMARY_DATE_RE.search(without_process_ids))


def _temporal_scope(query: str) -> str | None:
    folded = _fold(query)
    if _INITIAL_SCOPE_RE.search(folded):
        return "initial"
    if _POSTERIOR_SCOPE_RE.search(folded):
        return "posterior"
    return None


def _summary_lexical_score(query_tokens: list[str], text: str) -> float:
    folded = _fold(text)
    return sum(1.0 + min(folded.count(_fold(token)), 5) * 0.2
               for token in query_tokens if _fold(token) in folded)


def interpret_query_locally(query: str) -> dict[str, Any]:
    """Extract search intent/subject without answering or making a remote call."""
    folded = _fold(query)
    if re.search(r"\b(data|quando|que dia|horario|hora|agendad[oa])\b", folded):
        intent = "DATE_LOOKUP"
    elif re.search(r"\b(valor|quanto|percentual|montante|quantia)\b", folded):
        intent = "VALUE_LOOKUP"
    elif re.search(r"\b(numero|cnj|processo conexo|processo relacionado)\b", folded):
        intent = "IDENTIFIER_LOOKUP"
    elif re.search(r"\b(quem|parte|autor|autora|reu|requerente|requerido)\b", folded):
        intent = "PARTY_LOOKUP"
    else:
        intent = "FACT_LOOKUP"

    subject_tokens: list[str] = []
    for token in tokenize_query(query):
        normal = _fold(token)
        if normal not in _INTENT_WORDS and normal not in subject_tokens:
            subject_tokens.append(normal)
    return {"intent": intent, "subject": " ".join(subject_tokens), "terms": []}


def _markdown_blocks(content: str) -> list[dict[str, str]]:
    """Split materialized Markdown at blank lines and carry heading context."""
    blocks: list[dict[str, str]] = []
    heading_stack: list[tuple[int, str]] = []
    for raw in re.split(r"\n\s*\n", content or ""):
        text = raw.strip()
        if not text:
            continue
        lines = text.splitlines()
        heading = _HEADING_RE.match(lines[0]) if len(lines) == 1 else None
        if heading:
            level = len(heading.group(1))
            heading_stack = [(depth, name) for depth, name in heading_stack if depth < level]
            heading_stack.append((level, heading.group(2).strip()))
            continue
        # Headings can share a Markdown paragraph with following text.
        first_heading = _HEADING_RE.match(lines[0]) if lines else None
        if first_heading:
            level = len(first_heading.group(1))
            heading_stack = [(depth, name) for depth, name in heading_stack if depth < level]
            heading_stack.append((level, first_heading.group(2).strip()))
            body = "\n".join(lines[1:]).strip()
            if not body:
                continue
            text = body
        blocks.append({"text": text, "heading_path": " > ".join(name for _, name in heading_stack)})
    # Markdown list items are often separated by blank lines. Keep a contiguous
    # list section together so a citation can contain the complete alternatives.
    grouped: list[dict[str, str]] = []
    for block in blocks:
        is_list_item = bool(re.match(r"^\s*(?:[-*+] |\d+[.)] )", block["text"]))
        if (
            is_list_item and grouped
            and grouped[-1]["heading_path"] == block["heading_path"]
            and re.match(r"^\s*(?:[-*+] |\d+[.)] )", grouped[-1]["text"])
        ):
            grouped[-1]["text"] += "\n\n" + block["text"]
        else:
            grouped.append(dict(block))
    return grouped


def _current_summary_rows(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    required = {"movements", "movement_pieces", "movement_summaries", "movement_summary_source_state"}
    existing = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not required.issubset(existing):
        return []
    rows = db.execute(
        """SELECT m.movement_id,m.sequence,m.title,s.summary_id,s.summary_text,s.summary_version,
                  s.source_hash,state.source_hash AS current_source_hash
           FROM movements m
           JOIN movement_summary_source_state state ON state.movement_id=m.movement_id
           JOIN movement_summaries s ON s.movement_id=m.movement_id
           WHERE m.process_id=? AND state.eligible=1
             AND s.summary_version=(SELECT max(latest.summary_version)
                                   FROM movement_summaries latest WHERE latest.movement_id=m.movement_id)
             AND s.source_hash=state.source_hash AND trim(s.summary_text)<>''
           ORDER BY m.sequence,m.movement_id""",
        (process_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _local_query_embedding(query: str) -> list[float] | None:
    key = hashlib.sha256(query.strip().encode("utf-8")).hexdigest()
    with _SUMMARY_EMBED_CACHE_LOCK:
        cached = _SUMMARY_QUERY_CACHE.get(key)
        if cached is not None:
            _SUMMARY_QUERY_CACHE.move_to_end(key)
            return cached
    from core.retrieval.onnx_embed import generate_embedding_onnx

    vector = generate_embedding_onnx(query, is_query=True)
    if vector:
        with _SUMMARY_EMBED_CACHE_LOCK:
            _SUMMARY_QUERY_CACHE[key] = vector
            _SUMMARY_QUERY_CACHE.move_to_end(key)
            while len(_SUMMARY_QUERY_CACHE) > _SUMMARY_QUERY_CACHE_LIMIT:
                _SUMMARY_QUERY_CACHE.popitem(last=False)
    return vector


def _page_vector_compatibility(
    db: sqlite3.Connection, process_id: str, query_vector: list[float] | None,
) -> bool:
    if not query_vector or not db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='vector_index_metadata'"
    ).fetchone():
        return False
    row = db.execute(
        "SELECT model,backend,model_version,quantization,dim FROM vector_index_metadata WHERE process_id=? AND model=?",
        (process_id, EMBEDDING_MODEL_NAME),
    ).fetchone()
    if not row:
        return False
    return is_exact_space_match(dict(row), {
        "model": EMBEDDING_MODEL_NAME,
        "backend": "onnx",
        "model_version": "v1",
        "quantization": "int8",
        "dim": len(query_vector),
    })


def _summary_fts_routes(
    db: sqlite3.Connection, summaries: list[dict[str, Any]], terms: list[str], top_k: int,
) -> list[dict[str, Any]]:
    tokens = list(dict.fromkeys(
        _fold(token) for term in terms for token in tokenize_query(term)
        if _fold(token) not in _SUMMARY_FTS_STOP_WORDS
    ))
    if not tokens:
        return []
    rows_by_id = {row["movement_id"]: row for row in summaries}
    try:
        db.execute("DROP TABLE IF EXISTS temp.summary_query_fts")
        db.execute(
            "CREATE VIRTUAL TABLE temp.summary_query_fts USING fts5(movement_id UNINDEXED,title,summary_text,tokenize='unicode61 remove_diacritics 2')"
        )
        db.executemany(
            "INSERT INTO temp.summary_query_fts(movement_id,title,summary_text) VALUES(?,?,?)",
            [(row["movement_id"], row.get("title") or "", row["summary_text"]) for row in summaries],
        )
        match = " OR ".join('"' + token.replace('"', '""') + '"' for token in tokens)
        hits = db.execute(
            "SELECT movement_id,bm25(summary_query_fts) AS rank FROM summary_query_fts WHERE summary_query_fts MATCH ? ORDER BY rank,movement_id LIMIT ?",
            (match, max(top_k * 8, _SUMMARY_ROUTE_SHORTLIST)),
        ).fetchall()
        ranked = []
        for hit in hits:
            row = rows_by_id.get(hit["movement_id"])
            if row:
                text = f"{row.get('title') or ''}\n{row['summary_text']}"
                ranked.append((
                    _summary_lexical_score(tokens, text), float(hit["rank"]), row,
                ))
        ranked.sort(key=lambda item: (-item[0], item[1], int(item[2].get("sequence") or 0), item[2]["movement_id"]))
        return [dict(row, route_score=lexical, route_kind="summary_fts") for lexical, _, row in ranked[:top_k]]
    except sqlite3.OperationalError:
        # FTS5 is expected in SQLite, but lexical summary routing remains usable
        # if the extension is unavailable in a test/runtime build.
        ranked = []
        for row in summaries:
            text = f"{row.get('title') or ''}\n{row['summary_text']}"
            score = _summary_lexical_score(tokens, text)
            if score:
                ranked.append((score, row))
        ranked.sort(key=lambda item: (-item[0], int(item[1].get("sequence") or 0), item[1]["movement_id"]))
        return [dict(row, route_score=score, route_kind="summary_lexical") for score, row in ranked[:top_k]]


def _summary_subject_coverage(summaries: list[dict[str, Any]], subject: str) -> float:
    tokens = {_fold(token) for token in tokenize_query(subject)}
    if not tokens:
        return 1.0
    return max((
        len(tokens & {_fold(token) for token in tokenize_query(
            f"{row.get('title') or ''} {row['summary_text']}"
        )}) / len(tokens)
        for row in summaries
    ), default=0.0)


def _semantic_summary_neighbours(
    db: sqlite3.Connection, summaries: list[dict[str, Any]], query_vector: list[float] | None,
) -> list[dict[str, Any]]:
    if not query_vector:
        return []
    from core.retrieval.summary_embedding_store import current_vectors
    vectors = current_vectors(db, summaries, len(query_vector))
    ranked = []
    for row, vector in zip(summaries, vectors):
        if vector:
            score = cosine_similarity(query_vector, vector)
            ranked.append((score, row))
    ranked.sort(key=lambda item: (-item[0], int(item[1].get("sequence") or 0), item[1]["movement_id"]))
    if not ranked:
        return []
    threshold = max(0.30, ranked[0][0] * 0.82)
    return [dict(row, route_score=score, route_kind="summary_embedding")
            for score, row in ranked[:_SUMMARY_SEMANTIC_SHORTLIST] if score >= threshold]


def _semantic_terms_from_summaries(
    neighbours: list[dict[str, Any]], subject: str, limit: int = 8,
) -> list[str]:
    subject_words = {_fold(token) for token in tokenize_query(subject)}
    scores: dict[str, tuple[float, str]] = {}
    for neighbour in neighbours:
        relevance = float(neighbour.get("route_score") or 0.0)
        text = f"{neighbour.get('title') or ''}. {neighbour.get('summary_text') or ''}"
        words = re.findall(r"[A-ZÀ-ÖØ-Þ]{2,}|[\wÀ-ÿ]+", text)
        for size in (1, 2, 3, 4):
            for index in range(0, len(words) - size + 1):
                phrase_words = words[index:index + size]
                content = [_fold(word) for word in phrase_words if _fold(word) not in _SEMANTIC_STOP_WORDS]
                if not content or not any(word not in subject_words for word in content):
                    continue
                if size == 1 and not re.fullmatch(r"[A-ZÀ-ÖØ-Þ]{2,}", phrase_words[0]):
                    continue
                if size > 1 and len(content) < 2:
                    continue
                phrase = " ".join(phrase_words).strip(" ,;:.!?()[]{}\"'“”‘’")
                if re.search(r"\d", phrase):
                    continue
                key = _fold(phrase)
                if len(key) < 3:
                    continue
                score = relevance * (len(content) + (0.5 if size == 1 else 0.0))
                current = scores.get(key)
                if current is None or score > current[0]:
                    scores[key] = (score, phrase)
    ordered = sorted(scores.values(), key=lambda item: (-item[0], item[1].casefold()))
    return [phrase for _, phrase in ordered[:limit]]


def _movement_ids_for_sources(
    db: sqlite3.Connection, process_id: str, sources: list[dict[str, Any]],
) -> list[str]:
    document_ids = list(dict.fromkeys(
        str((source.get("source_ref") or {}).get("document_id") or "")
        for source in sources if (source.get("source_ref") or {}).get("document_id")
    ))
    if not document_ids:
        return []
    marks = ",".join("?" for _ in document_ids)
    rows = db.execute(
        f"""SELECT mp.movement_id FROM movement_pieces mp
            JOIN movements m ON m.movement_id=mp.movement_id
            WHERE m.process_id=? AND mp.document_id IN ({marks})
            ORDER BY m.sequence,mp.piece_order""",
        [process_id, *document_ids],
    ).fetchall()
    return list(dict.fromkeys(row[0] for row in rows))


def _candidate_pages(db: sqlite3.Connection, process_id: str, movement_ids: list[str]) -> list[dict[str, Any]]:
    if not movement_ids:
        return []
    marks = ",".join("?" for _ in movement_ids)
    rows = db.execute(
        f"""SELECT m.movement_id,m.sequence,m.title,mp.document_id,mp.piece_order,
                   p.page_id,p.page_number,p.process_folio,p.page_class,p.content
            FROM movements m JOIN movement_pieces mp ON mp.movement_id=m.movement_id
            JOIN documents d ON d.document_id=mp.document_id AND d.process_id=m.process_id
            JOIN pages p ON p.document_id=mp.document_id
              AND (mp.page_start IS NULL OR p.process_folio>=mp.page_start)
              AND (mp.page_end IS NULL OR p.process_folio<=mp.page_end)
            WHERE m.process_id=? AND m.movement_id IN ({marks})
              AND (m.sequence<>1 OR mp.piece_order=1)
            ORDER BY m.sequence,mp.piece_order,p.page_number""",
        [process_id, *movement_ids],
    ).fetchall()
    return [dict(row) for row in rows]


def _page_vectors(db: sqlite3.Connection, process_id: str, page_ids: list[str], compatible: bool) -> dict[str, list[float]]:
    if not compatible or not page_ids:
        return {}
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='page_embeddings'").fetchone():
        return {}
    vectors: dict[str, list[float]] = {}
    for offset in range(0, len(page_ids), 400):
        batch = page_ids[offset:offset + 400]
        marks = ",".join("?" for _ in batch)
        rows = db.execute(
            f"SELECT page_id,dim,vector_blob FROM page_embeddings WHERE process_id=? AND model=? AND page_id IN ({marks})",
            [process_id, EMBEDDING_MODEL_NAME, *batch],
        ).fetchall()
        for row in rows:
            try:
                vectors[row["page_id"]] = unpack_vector(row["vector_blob"], row["dim"])
            except (ValueError, TypeError):
                continue
    return vectors


def _passages(
    query: str, query_tokens: list[str], semantic_terms: list[str], intent: str,
    pages: list[dict[str, Any]],
    query_vector: list[float] | None, page_vectors: dict[str, list[float]],
    source_scores: dict[str, float],
) -> list[dict[str, Any]]:
    folded_query_tokens = {_fold(token) for token in query_tokens}
    semantic_tokens = {_fold(token) for term in semantic_terms for token in tokenize_query(term)}
    wants_value = (
        intent == "VALUE_LOOKUP"
        or bool(folded_query_tokens & _VALUE_QUERY_WORDS)
        or bool(folded_query_tokens & {"pedido", "pedidos"})
    )
    wants_date = intent == "DATE_LOOKUP"
    max_source_score = max(source_scores.values(), default=0.0) or 1.0
    ranked: list[dict[str, Any]] = []
    for page in pages:
        text = str(page.get("content") or "")
        page_vector = page_vectors.get(page["page_id"])
        semantic = cosine_similarity(query_vector, page_vector) if query_vector and page_vector else 0.0
        source_recall = source_scores.get(page["page_id"], 0.0) / max_source_score
        for block in _markdown_blocks(text):
            block_tokens = {_fold(token) for token in tokenize_query(block["text"])}
            coverage = len(folded_query_tokens & block_tokens) / max(1, len(folded_query_tokens))
            semantic_coverage = len(semantic_tokens & block_tokens) / max(1, len(semantic_tokens))
            initial_scope = _temporal_scope(query) == "initial"
            amount_pattern = _INITIAL_AMOUNT_RE if initial_scope else _AMOUNT_RE
            amount_signal = bool(wants_value and amount_pattern.search(block["text"]))
            request_section = bool(
                wants_value and (
                    "pedido" in _fold(block["heading_path"])
                    or len(_REQUEST_ITEM_RE.findall(block["text"])) >= 2
                    or bool(_REQUEST_STATEMENT_RE.search(block["text"]))
                )
            )
            topic_relevance = max(semantic, coverage, semantic_coverage)
            date_signal = bool(
                wants_date and _has_date_or_time(block["text"])
            )
            identifier_signal = bool(
                intent == "IDENTIFIER_LOOKUP" and _CNJ_NUMBER_RE.search(block["text"])
            )
            notice_signal = bool(wants_date and re.search(
                r"\b(?:ato ordinatorio|intimacao|designacao|agendamento)\b",
                _fold(page.get("title") or ""),
            ))
            if wants_date and (topic_relevance < 0.05 or not date_signal):
                continue
            if intent == "IDENTIFIER_LOOKUP":
                score = (
                    0.25 * semantic + 0.12 * coverage + 0.13 * semantic_coverage
                    + 0.45 * float(identifier_signal) + 0.05 * source_recall
                )
            elif wants_date:
                # For a date question, a passage that states a date/time in a
                # procedural notice is stronger than a lexical match to the
                # subject on a page with no scheduled event.
                score = (
                    0.20 * semantic + 0.08 * coverage + 0.22 * semantic_coverage
                    + 0.34 * float(date_signal) + 0.14 * float(notice_signal)
                    + 0.02 * source_recall
                )
            else:
                score = (
                    0.34 * semantic + 0.20 * coverage + 0.13 * semantic_coverage
                    + 0.15 * float(amount_signal) + 0.10 * float(request_section)
                    + 0.06 * float(date_signal) + 0.02 * source_recall
                )
            if score <= 0:
                continue
            ranked.append({
                "movement_id": page["movement_id"],
                "movement_sequence": page["sequence"],
                "movement_title": page["title"],
                "document_id": page["document_id"],
                "page_id": page["page_id"],
                "pdf_page": page["page_number"],
                "process_folio": page["process_folio"],
                "excerpt": block["text"],
                "heading_path": block["heading_path"],
                "score": score,
                "signals": {"semantic": semantic, "lexical_coverage": coverage,
                            "semantic_term_coverage": semantic_coverage,
                            "amount": amount_signal, "request_section": request_section,
                            "date": date_signal, "notice": notice_signal,
                            "identifier": identifier_signal,
                            "rrf_recall": source_recall},
            })
    ranked.sort(key=lambda row: (
        -row["score"], row["movement_sequence"], row["pdf_page"], row["document_id"], row["excerpt"]
    ))
    return ranked


def search_hierarchical_evidence(
    process_id: str,
    query: str,
    top_k: int = 5,
    *,
    db_path: Path | str,
    vector_db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Interpret locally, route through CURRENT summaries, then cite pages.content."""
    target = Path(db_path).resolve()
    db = sqlite3.connect(f"file:{target.as_posix()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        summaries = _current_summary_rows(db, process_id)
        if not summaries:
            db.close()
            return search_hybrid(
                process_id, query, top_k, db_path=db_path,
                vector_db_path=vector_db_path or db_path,
            )
        interpretation = interpret_query_locally(query)
        query_tokens = tokenize_query(query)
        folded_query_tokens = {_fold(token) for token in query_tokens}
        temporal_scope = _temporal_scope(query)
        summary_terms = [interpretation["subject"]] if interpretation["subject"] else []
        summary_candidates = _summary_fts_routes(db, summaries, summary_terms, top_k)
        query_vector: list[float] | None = None
        needs_semantic_route = (
            interpretation["intent"] == "DATE_LOOKUP"
            or interpretation["intent"] == "VALUE_LOOKUP"
            or bool(folded_query_tokens & {"pedido", "pedidos", "percentual", "valor", "valores"})
            or temporal_scope == "posterior"
            or not summary_candidates
            or _summary_subject_coverage(summaries, interpretation["subject"]) < 0.80
        )
        if needs_semantic_route:
            query_vector = _local_query_embedding(query)
            neighbours = _semantic_summary_neighbours(db, summaries, query_vector)
            interpretation["terms"] = _semantic_terms_from_summaries(
                neighbours, interpretation["subject"],
            )
            expanded_terms = list(dict.fromkeys(summary_terms + interpretation["terms"]))
            summary_candidates = _summary_fts_routes(db, summaries, expanded_terms, top_k)
            # Semantic neighbors remain eligible even if their natural language
            # terms are not present in a summary's FTS tokens.
            candidate_by_id = {row["movement_id"]: row for row in summary_candidates}
            for neighbour in neighbours:
                existing = candidate_by_id.get(neighbour["movement_id"])
                if existing is None or float(neighbour.get("route_score") or 0.0) > float(existing.get("route_score") or 0.0):
                    candidate_by_id[neighbour["movement_id"]] = neighbour
            summary_candidates = sorted(
                candidate_by_id.values(),
                key=lambda row: (
                    -float(row.get("route_score") or 0.0),
                    0 if row.get("route_kind") == "summary_fts" else 1,
                    int(row.get("sequence") or 0), row["movement_id"],
                ),
            )[:max(top_k * 2, _SUMMARY_SEMANTIC_SHORTLIST)]
        if not summary_candidates:
            db.close()
            return search_hybrid(
                process_id, query, top_k, db_path=db_path,
                vector_db_path=vector_db_path or db_path,
            )
        if query_vector is None:
            query_vector = _local_query_embedding(query)
        compatible = _page_vector_compatibility(db, process_id, query_vector)
        summary_ids = [row["movement_id"] for row in summary_candidates]
        if temporal_scope == "initial":
            first = db.execute(
                "SELECT movement_id FROM movements WHERE process_id=? ORDER BY sequence,movement_id LIMIT 1",
                (process_id,),
            ).fetchone()
            scoped_ids = [first["movement_id"]] if first else []
        elif temporal_scope == "posterior":
            # The singular posterior request means the latest matching
            # processual request. Keep the route candidates until their page
            # passages establish which one actually contains the request.
            scoped_ids = [row["movement_id"] for row in summary_candidates]
        else:
            scoped_ids = []
        if temporal_scope and scoped_ids:
            # Summaries route a temporal follow-up to a Movement. Evidence below
            # still comes exclusively from its pages.content passages.
            movement_ids = scoped_ids
        else:
            movement_ids = list(dict.fromkeys(summary_ids))
        pages = _candidate_pages(db, process_id, movement_ids)
        if not pages:
            db.close()
            return search_hybrid(
                process_id, query, top_k, db_path=db_path,
                vector_db_path=vector_db_path or db_path,
            )
        page_ids = list(dict.fromkeys(row["page_id"] for row in pages))
        vectors = _page_vectors(db, process_id, page_ids, compatible)
        source_scores: dict[str, float] = {}
        passages = _passages(
            query, query_tokens, interpretation["terms"], interpretation["intent"],
            pages, query_vector, vectors, source_scores,
        )
        if not passages:
            db.close()
            return search_hybrid(
                process_id, query, top_k, db_path=db_path,
                vector_db_path=vector_db_path or db_path,
            )
        if temporal_scope == "posterior":
            # Select the latest matching request in process order, while the
            # cited text remains exclusively sourced from pages.content.
            passages.sort(key=lambda row: (
                not row["signals"]["amount"],
                not row["signals"]["request_section"],
                -row["movement_sequence"], row["process_folio"],
                row["pdf_page"], -row["score"]
            ))

        # Prefer one source passage per Movement before filling additional slots.
        chosen: list[dict[str, Any]] = []
        used_movements: set[str] = set()
        for passage in passages:
            if passage["movement_id"] not in used_movements:
                chosen.append(passage)
                used_movements.add(passage["movement_id"])
                if len(chosen) >= top_k:
                    break
        if len(chosen) < top_k and not temporal_scope:
            used_pages = {row["page_id"] for row in chosen}
            for passage in passages:
                if passage["page_id"] in used_pages:
                    continue
                chosen.append(passage)
                used_pages.add(passage["page_id"])
                if len(chosen) >= top_k:
                    break

        # The retrieved passages remain ranked by relevance, but the answer
        # context is presented in the actual Movement sequence.
        if temporal_scope != "posterior" and interpretation["intent"] != "DATE_LOOKUP":
            chosen.sort(key=lambda row: (
                row["movement_sequence"], row["pdf_page"], row["document_id"], -row["score"]
            ))

        results = []
        for index, passage in enumerate(chosen, start=1):
            excerpt = passage["excerpt"]
            sref = {
                "process_id": process_id,
                "document_id": passage["document_id"],
                "pdf_page": passage["pdf_page"],
                "process_folio": passage["process_folio"],
            }
            results.append({
                "source_id": index,
                "source_ref": sref,
                "excerpt": excerpt,
                "score": round(passage["score"], 6),
                "page_id": passage["page_id"],
                "movement_id": passage["movement_id"],
                "movement_sequence": passage["movement_sequence"],
                "movement_title": passage["movement_title"],
                "evidence": [],
                "autos_navigation": {
                    "process_id": process_id,
                    "document_id": passage["document_id"],
                    "page": passage["pdf_page"],
                    "folio": passage["process_folio"],
                    "target_text": excerpt[:200],
                    "autos_path": f"/processes/{process_id}/autos",
                },
            })
        if results:
            return results
        db.close()
        return search_hybrid(
            process_id, query, top_k, db_path=db_path,
            vector_db_path=vector_db_path or db_path,
        )
    finally:
        db.close()
