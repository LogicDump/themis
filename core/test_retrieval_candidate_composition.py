"""Synthetic regression evidence; original case data must stay out of Git."""
import copy
import json
from pathlib import Path
import sqlite3

import pytest

from core.retrieval.candidate_composition import compose_candidates
from core.retrieval.citations import (
    resolve_verifiable_citations, synthesize_answer_with_citations,
)
from core.retrieval import hierarchical_retrieval as retrieval


def source(key, movement=None, text="Prova documental", score=1):
    return {"page_id": key, "excerpt": text, "score": score,
            "movement_id": movement or key,
            "source_ref": {"document_id": key, "pdf_page": 1}}


def test_both_routes_survive_and_repeated_movement_does_not_fill_slots():
    direct = [source(str(i), "same") for i in range(5)]
    hierarchy = [source("other1"), source("other2"), source("other3")]
    result = compose_candidates(hierarchy, direct, 5)
    assert len(result) == 5
    assert any(row["page_id"].startswith("other") for row in result)
    assert any(row["movement_id"] == "same" for row in result)
    assert len({row["movement_id"] for row in result}) >= 3


def test_equal_rank_votes_are_independent_of_score_scale_and_route_order():
    a = [source("a", score=9000), source("b", score=0.1)]
    b = [source("c", score=0.001), source("b", score=0.002)]
    first = compose_candidates(a, b, 3)
    second = compose_candidates(b, a, 3)
    assert [x["page_id"] for x in first] == [x["page_id"] for x in second]
    assert first[0]["page_id"] == "b"  # Support from both routes.


def test_dedup_preserves_passage_owner_navigation_and_inputs():
    hierarchy = [source("a", text="Passagem integral com comprovação")]
    direct = [source("a", text="Prefixo..."), source("a"), source("b")]
    direct[0].pop("movement_id")
    direct[-1].pop("movement_id")
    original = copy.deepcopy((hierarchy, direct))
    result = compose_candidates(hierarchy, direct, 4, owners={"b": {"movement_id": "m2"}})
    assert len(result) == 2
    assert result[0]["excerpt"] == hierarchy[0]["excerpt"]
    assert result[1]["movement_id"] == "m2"
    assert [x["source_id"] for x in result] == [1, 2]
    assert (hierarchy, direct) == original


@pytest.mark.parametrize("limit", [0, -1, 1, 3, 10])
def test_limits_empty_sources_and_single_route(limit):
    hits = [source("a"), source("b")]
    assert len(compose_candidates(hits, [], limit)) == max(0, min(limit, 2))
    assert len(compose_candidates([], hits, limit)) == max(0, min(limit, 2))
    assert compose_candidates([], [], limit) == []
    assert compose_candidates([source("empty", text=" ")], [], limit) == []


def dna_fixture():
    return json.loads((Path(__file__).parent / "fixtures/retrieval_dated_notice_synthetic.json").read_text(encoding="utf-8"))


def database_from_fixture(path, fixture):
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE documents(document_id TEXT PRIMARY KEY,process_id TEXT,created_at TEXT);
        CREATE TABLE pages(page_id TEXT PRIMARY KEY,document_id TEXT,page_number INTEGER,
          content TEXT,quality TEXT,process_folio INTEGER,page_class TEXT);
        CREATE TABLE movements(movement_id TEXT PRIMARY KEY,process_id TEXT,sequence INTEGER,title TEXT);
        CREATE TABLE movement_pieces(movement_id TEXT,document_id TEXT,piece_order INTEGER,page_start INTEGER,page_end INTEGER);
        CREATE TABLE movement_summaries(summary_id TEXT,movement_id TEXT,summary_version INTEGER,summary_text TEXT,source_hash TEXT);
        CREATE TABLE movement_summary_source_state(movement_id TEXT,eligible INTEGER,source_hash TEXT);
        """)
        for page in fixture["pages"]:
            db.execute("INSERT OR IGNORE INTO documents VALUES(?,?,?)", (page["document_id"], fixture["process_id"], "2026-01-01"))
            db.execute("INSERT INTO pages VALUES(?,?,?,?,?,?,?)", (page["page_id"], page["document_id"], page["page_number"], page["content"], "OK", page["process_folio"], "text"))
            db.execute("INSERT OR IGNORE INTO movements VALUES(?,?,?,?)", (page["movement_id"], fixture["process_id"], page["sequence"], page["title"]))
            if not db.execute("SELECT 1 FROM movement_pieces WHERE document_id=?", (page["document_id"],)).fetchone():
                db.execute("INSERT INTO movement_pieces VALUES(?,?,1,NULL,NULL)", (page["movement_id"], page["document_id"]))
        for summary in fixture["summaries"]:
            db.execute("INSERT INTO movement_summaries VALUES(?,?,1,?,'hash')", (summary["movement_id"] + ':s', summary["movement_id"], summary["summary_text"]))
            db.execute("INSERT INTO movement_summary_source_state VALUES(?,1,'hash')", (summary["movement_id"],))


def test_dna_integration_restores_imesc_document_and_citation(tmp_path, monkeypatch):
    fixture = dna_fixture()
    path = tmp_path / "process.db"
    database_from_fixture(path, fixture)
    # Freeze summary routing, not evidence selection: this regression exercises
    # the composition boundary after the real EG2 route has found these acts.
    monkeypatch.setattr(retrieval, "_summary_fts_routes", lambda db, summaries, terms, k: summaries)
    before_bytes = path.read_bytes()
    original = compose_candidates
    import core.retrieval.candidate_composition as composition
    monkeypatch.setattr(composition, "compose_candidates", lambda hierarchical, direct, top_k, **kw: direct[:top_k])
    before = retrieval.search_hierarchical_evidence(fixture["process_id"], fixture["query"], 3, db_path=path)
    monkeypatch.setattr(composition, "compose_candidates", original)
    after = retrieval.search_hierarchical_evidence(fixture["process_id"], fixture["query"], 3, db_path=path)
    assert 374 not in [x["source_ref"]["process_folio"] for x in before]
    imesc = next(x for x in after if x["source_ref"]["process_folio"] == 374)
    assert imesc["movement_sequence"] == 68
    assert imesc["source_ref"]["document_id"] == fixture["source_document_id"]
    assert imesc["source_ref"]["pdf_page"] == 1
    assert "08/09/2026" in imesc["excerpt"] and "07:00h" in imesc["excerpt"]
    assert "08/05/2026" not in imesc["excerpt"]
    assert "21/05" not in imesc["excerpt"]
    # The earlier act proves deferment, rather than the scheduled collection.
    deferment = next(p for p in fixture["pages"] if p["process_folio"] == 269)
    hearing = next(p for p in fixture["pages"] if p["process_folio"] == 270)
    assert "08/05/2026 foi deferida" in deferment["content"]
    assert "21/05" in hearing["content"] and "audiência" in hearing["content"]
    assert imesc["excerpt"] == next(p["content"] for p in fixture["pages"] if p["process_folio"] == 374)
    answer = synthesize_answer_with_citations(fixture["process_id"], fixture["query"], after)
    assert "08/09/2026" in answer["answer"] and "07:00h" in answer["answer"]
    assert any(c["document_id"] == fixture["source_document_id"] and c["process_folio"] == 374 for c in answer["citations"])
    assert before_bytes == path.read_bytes()


def test_heading_recovery_is_not_subject_specific_and_requires_documentary_match():
    page = {"page_id": "p", "movement_id": "m", "document_id": "d", "sequence": 4,
            "title": "Comunicação", "page_number": 2, "process_folio": 20,
            "content": "## Agendamento em 12/11/2026\n\nCompareça às 09:00h para vistoria."}
    summary = {"movement_id": "m", "summary_text": "Vistoria designada para 12/11/2026."}
    result = compose_candidates([], [], 2, query="Qual é a data da vistoria?", routed_pages=[page], summaries=[summary], process_id="case")
    assert result[0]["excerpt"] == page["content"]
    assert result[0]["autos_navigation"]["page"] == 2
    for summaries in ([], [dict(summary, summary_text="Vistoria em 15/11/2026.")]):
        assert compose_candidates([], [], 2, query="Qual a data?", routed_pages=[page], summaries=summaries) == []


def test_missing_evidence_abstains_without_invented_dates():
    result = synthesize_answer_with_citations("case", "Qual a data da vistoria?", [])
    assert "suficiente" in result["answer"]
    assert result["citations"] == []
    assert not __import__("re").search(r"\d{2}/\d{2}/\d{4}", result["answer"])
    # Citation identity alone does not establish support for a claimed date.
    unrelated = [source("a", text="O pedido foi deferido em 08/05/2026.")]
    verified = resolve_verifiable_citations("Exame em 21/05/2026 [1]", unrelated, "case")
    assert verified["all_citations_verified"]
    assert "21/05/2026" not in verified["citations"][0]["excerpt"]
    captured = []
    def abstain(system, prompt):
        captured.append((system, prompt))
        return "Não foi localizada evidência suficiente da data do exame."
    answer = synthesize_answer_with_citations("case", "Qual a data do exame?", unrelated, abstain)
    assert "suficiente" in answer["answer"] and answer["citations"] == []
    assert "Se o contexto não contiver dados suficientes" in captured[0][0]


def test_nonempty_context_does_not_create_a_scheduled_date():
    # Exercise the actual deterministic answer path, without an LLM stub.
    hits = compose_candidates(
        [source("a", text="Foi solicitada a designação da vistoria, sem data marcada.")],
        [source("b", text="Aguarda-se resposta ao ofício.")], 5,
        query="Qual é a data da vistoria?",
    )
    answer = synthesize_answer_with_citations("case", "Qual é a data da vistoria?", hits)
    assert "sem data marcada" in answer["answer"]
    assert not __import__("re").search(r"\d{2}/\d{2}/\d{4}", answer["answer"])
    assert {c["excerpt"] for c in answer["citations"]} == {hit["excerpt"] for hit in hits}


@pytest.mark.parametrize("query,text", [
    ("Qual o valor da quitação?", "A quitação foi de R$ 500,00."),
    ("Quem assinou o recibo?", "O recibo foi assinado por Maria."),
    ("Qual o processo relacionado?", "Processo relacionado: 0000000-00.2026.8.26.0000."),
])
def test_other_questions_keep_literal_evidence_and_citations(query, text):
    hits = compose_candidates([source("a", text=text)], [source("b", text="Outra informação.")], 2, query=query)
    answer = synthesize_answer_with_citations("case", query, hits)
    assert text in answer["answer"]
    assert answer["citations"][0]["document_id"] == "a"


def test_hierarchical_relevance_order_is_not_replaced_by_movement_chronology(tmp_path, monkeypatch):
    """A later, better-supported fact must keep its retrieval rank before fusion."""
    fixture = {
        "process_id": "synthetic-chronology",
        "pages": [
            {"page_id": "early:1", "document_id": "early", "page_number": 1,
             "process_folio": 100, "content": "O processo foi distribuído e houve uma certidão.",
             "movement_id": "m1", "sequence": 1, "title": "Distribuição"},
            {"page_id": "late:1", "document_id": "late", "page_number": 1,
             "process_folio": 300,
             "content": "O fundamento da extinção do processo foi a quitação integral da dívida.",
             "movement_id": "m3", "sequence": 3, "title": "Sentença de extinção"}
        ],
        "summaries": [
            {"movement_id": "m1", "summary_text": "Distribuição do processo."},
            {"movement_id": "m3", "summary_text": "Sentença de extinção por quitação integral da dívida."}
        ],
    }
    path = tmp_path / "chronology.db"
    database_from_fixture(path, fixture)
    monkeypatch.setattr(retrieval, "_summary_fts_routes", lambda _db, summaries, _terms, _k: summaries)
    monkeypatch.setattr(retrieval, "search_hybrid", lambda *_args, **_kwargs: [])
    before = path.read_bytes()
    results = retrieval.search_hierarchical_evidence(
        fixture["process_id"], "Qual o fundamento da extinção do processo?",
        top_k=2, db_path=path, vector_db_path=path,
    )
    assert [r["source_ref"]["document_id"] for r in results] == ["late", "early"]
    assert [r["source_id"] for r in results] == [1, 2]
    assert results[0]["autos_navigation"]["folio"] == 300
    assert before == path.read_bytes()
