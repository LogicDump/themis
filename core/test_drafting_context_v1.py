import json
import sqlite3
from pathlib import Path

from core.drafting.context_pack_v1 import (
    DraftingTask,
    apply_context_selection,
    build_legal_context_pack,
    build_process_frame,
    load_related_documents,
    load_target_document,
)
from core.drafting.issue_map_v1 import (
    build_issue_mapper_input,
    validate_issue_map,
)
from core.drafting.context_selector_v1 import (
    build_selector_input,
    validate_selection,
)


def _db(tmp_path: Path) -> Path:
    path = tmp_path / "process.db"
    db = sqlite3.connect(path)
    db.executescript("""
        CREATE TABLE processes(
            process_id TEXT PRIMARY KEY,
            status TEXT NOT NULL
        );
        CREATE TABLE process_metadata(
            process_id TEXT PRIMARY KEY,
            classe TEXT,
            assunto TEXT,
            tribunal TEXT,
            comarca TEXT,
            unidade TEXT,
            grau TEXT,
            status TEXT,
            fase TEXT,
            version INTEGER
        );
        CREATE TABLE movements(
            movement_id TEXT PRIMARY KEY,
            process_id TEXT NOT NULL,
            sequence INTEGER,
            title TEXT,
            actor TEXT,
            occurred_at TEXT,
            movement_type TEXT,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE pages(
            page_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            content TEXT,
            movement_id TEXT,
            process_folio INTEGER
        );
    """)
    db.execute("INSERT INTO processes VALUES(?,?)", ("proc", "ACTIVE"))
    db.execute(
        "INSERT INTO process_metadata VALUES(?,?,?,?,?,?,?,?,?,?)",
        ("proc", "Cumprimento de sentença", "Cobrança", "TJSP", "Piracaia", "Vara Cível", "1", "ACTIVE", "EXECUÇÃO", 1),
    )
    payload = json.dumps({
        "pieces": [{
            "pages": [
                {"document_id": "doc1", "pdf_page": 1},
                {"document_id": "doc1", "pdf_page": 2},
            ]
        }]
    }, ensure_ascii=False)
    db.execute(
        "INSERT INTO movements VALUES(?,?,?,?,?,?,?,?)",
        ("mov_target", "proc", 10, "Petição", "AUTORA", "2026-10-02", "Petição", payload),
    )
    db.execute(
        "INSERT INTO pages VALUES(?,?,?,?,?,?)",
        ("p1", "doc1", 1, "A autora alega pagamento de R$ 500,00.", "mov_target", 100),
    )
    db.execute(
        "INSERT INTO pages VALUES(?,?,?,?,?,?)",
        ("p2", "doc1", 2, "Requer a restituição integral do valor.", "mov_target", 101),
    )
    related_payload = json.dumps({
        "pieces": [{
            "pages": [{"document_id": "doc2", "pdf_page": 1}]
        }]
    }, ensure_ascii=False)
    db.execute(
        "INSERT INTO movements VALUES(?,?,?,?,?,?,?,?)",
        ("mov_related", "proc", 3, "Decisão anterior", "JUÍZO", "2026-09-20", "Decisão", related_payload),
    )
    db.execute(
        "INSERT INTO pages VALUES(?,?,?,?,?,?)",
        ("p3", "doc2", 1, "O juízo determinou a intimação para pagamento.", "mov_related", 50),
    )
    db.commit()
    db.close()
    return path


def test_target_document_is_full_canonical(tmp_path):
    path = _db(tmp_path)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    target = load_target_document(db, "proc", "mov_target")
    db.close()

    assert target["source_mode"] == "FULL_CANONICAL"
    assert target["full_text"] == (
        "A autora alega pagamento de R$ 500,00.\n\n"
        "Requer a restituição integral do valor."
    )
    assert [p["pdf_page"] for p in target["pages"]] == [1, 2]


def test_issue_map_requires_source_grounding(tmp_path):
    path = _db(tmp_path)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    target = load_target_document(db, "proc", "mov_target")
    db.close()

    payload = build_issue_mapper_input(target)
    assert "full_text" not in payload
    assert payload["pages"][0]["content"].startswith("A autora")

    issues = validate_issue_map(
        {
            "issues": [{
                "issue_id": "issue_1",
                "kind": "FACTUAL_ASSERTION",
                "text": "A autora alega pagamento.",
                "retrieval_query": "pagamento R$ 500",
                "target_source_refs": [{
                    "document_id": "doc1",
                    "pdf_page": 1,
                    "quote": "A autora alega pagamento de R$ 500,00.",
                }],
            }]
        },
        target,
    )
    assert issues[0]["issue_id"] == "issue_1"


def test_issue_map_rejects_unverifiable_quote(tmp_path):
    path = _db(tmp_path)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    target = load_target_document(db, "proc", "mov_target")
    db.close()

    try:
        validate_issue_map(
            {
                "issues": [{
                    "issue_id": "issue_1",
                    "kind": "REQUEST",
                    "text": "Pedido",
                    "retrieval_query": "pedido",
                    "target_source_refs": [{
                        "document_id": "doc1",
                        "pdf_page": 2,
                        "quote": "trecho inventado",
                    }],
                }]
            },
            target,
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "não conferível" in str(exc)


def test_context_pack_requires_full_target_for_directed_task(tmp_path):
    path = _db(tmp_path)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    target = load_target_document(db, "proc", "mov_target")
    db.close()
    task = DraftingTask(
        task_id="task1",
        process_id="proc",
        task_kind="RESPOND_TO_MOVEMENT",
        goal="Responder à petição",
        target_movement_id="mov_target",
    )
    issues = [{
        "issue_id": "issue_1",
        "kind": "FACTUAL_ASSERTION",
        "text": "Alega pagamento.",
        "retrieval_query": "pagamento",
        "target_source_refs": [{
            "document_id": "doc1", "pdf_page": 1,
            "quote": "A autora alega pagamento de R$ 500,00.",
        }],
    }]
    pack = build_legal_context_pack(
        task,
        target,
        process_frame={"process_id": "proc"},
        issues=issues,
        related_sources=[],
    )
    assert pack["target_document"]["full_text"] == target["full_text"]
    assert pack["source_policy"]["summaries"] == "ROUTING_ONLY"


def test_context_pack_rejects_missing_full_target():
    task = DraftingTask(
        task_id="task1",
        process_id="proc",
        task_kind="RESPOND_TO_MOVEMENT",
        goal="Responder",
        target_movement_id="mov_target",
    )
    try:
        build_legal_context_pack(
            task,
            {"movement_id": "mov_target", "source_mode": "RETRIEVED_EXCERPT"},
            process_frame={},
            issues=[],
            related_sources=[],
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "integralmente" in str(exc)


def test_process_frame_is_minimal_and_structured(tmp_path):
    path = _db(tmp_path)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    frame = build_process_frame(db, "proc")
    db.close()

    assert frame["process_id"] == "proc"
    assert frame["status"] == "ACTIVE"
    assert frame["metadata"]["classe"] == "Cumprimento de sentença"
    assert frame["metadata"]["comarca"] == "Piracaia"
    assert frame["participants"] == []
    assert frame["representations"] == []


def test_retrieval_uses_issue_retrieval_query_and_excludes_target(monkeypatch, tmp_path):
    from core.drafting import context_pack_v1 as ctx

    calls = []

    def fake_search(process_id, query, top_k, **kwargs):
        calls.append((process_id, query, top_k))
        return [
            {
                "movement_id": "mov_target",
                "movement_title": "Alvo",
                "excerpt": "Trecho do alvo",
                "score": 1.0,
                "source_ref": {"document_id": "doc1", "pdf_page": 1},
                "autos_navigation": {},
            },
            {
                "movement_id": "mov_related",
                "movement_title": "Decisão anterior",
                "excerpt": "Antecedente relevante",
                "score": 0.9,
                "source_ref": {"document_id": "doc2", "pdf_page": 4},
                "autos_navigation": {"page": 4},
            },
        ]

    monkeypatch.setattr(ctx, "search_hierarchical_evidence", fake_search)
    task = DraftingTask(
        task_id="task1",
        process_id="proc",
        task_kind="RESPOND_TO_MOVEMENT",
        goal="Responder",
        target_movement_id="mov_target",
    )
    sources = ctx.retrieve_related_sources(
        task,
        [{"issue_id": "i1", "retrieval_query": "pagamento anterior"}],
        db_path=tmp_path / "process.db",
        top_k_per_issue=1,
    )

    assert calls == [("proc", "pagamento anterior", 2)]
    assert [item["movement_id"] for item in sources] == ["mov_related"]
    assert sources[0]["source_mode"] == "RETRIEVED_EXCERPT"


def test_retrieval_falls_back_when_hierarchical_only_finds_target(monkeypatch, tmp_path):
    from core.drafting import context_pack_v1 as ctx

    task = DraftingTask(
        task_id="task2",
        process_id="proc",
        task_kind="RESPOND_TO_MOVEMENT",
        goal="Responder",
        target_movement_id="mov_target",
    )
    monkeypatch.setattr(
        ctx,
        "search_hierarchical_evidence",
        lambda *a, **k: [{
            "movement_id": "mov_target",
            "movement_title": "Alvo",
            "excerpt": "Texto do alvo",
            "score": 1.0,
            "source_ref": {"document_id": "doc1", "pdf_page": 1},
            "autos_navigation": {},
        }],
    )
    monkeypatch.setattr(
        ctx,
        "_own_page_movement_index",
        lambda *a, **k: {
            ("doc2", 4): {
                "movement_id": "mov_related",
                "movement_title": "Decisão anterior",
                "movement_sequence": 3,
            }
        },
    )
    monkeypatch.setattr(
        ctx,
        "search_hybrid",
        lambda *a, **k: [{
            "excerpt": "Decisão anterior relevante",
            "score": 0.5,
            "source_ref": {"document_id": "doc2", "pdf_page": 4},
            "autos_navigation": {"page": 4},
        }],
    )

    sources = ctx.retrieve_related_sources(
        task,
        [{"issue_id": "i1", "retrieval_query": "decisão anterior"}],
        db_path=tmp_path / "process.db",
        top_k_per_issue=1,
    )

    assert len(sources) == 1
    assert sources[0]["movement_id"] == "mov_related"
    assert sources[0]["retrieval_route"] == "HYBRID_FALLBACK"


def test_selector_only_accepts_candidates_from_same_issue():
    issues = [{
        "issue_id": "i1",
        "kind": "REQUEST",
        "text": "Pedido de restituição",
        "retrieval_query": "restituição",
        "target_source_refs": [{
            "document_id": "doc1", "pdf_page": 2,
            "quote": "Requer a restituição integral do valor.",
        }],
    }]
    candidates = [{
        "candidate_id": "ctx_1",
        "issue_id": "i1",
        "movement_id": "mov_related",
        "movement_title": "Decisão anterior",
        "excerpt": "O juízo determinou a intimação para pagamento.",
        "score": 0.5,
        "source_ref": {"document_id": "doc2", "pdf_page": 1},
        "retrieval_route": "HYBRID_FALLBACK",
    }]
    selector_input = build_selector_input(
        {"task_kind": "RESPOND_TO_MOVEMENT", "goal": "Responder"},
        issues,
        candidates,
    )
    assert selector_input["candidates"][0]["candidate_id"] == "ctx_1"

    validated = validate_selection(
        {
            "selections": [{
                "issue_id": "i1",
                "candidate_ids": ["ctx_1"],
                "promote_movement_ids": ["mov_related"],
                "unresolved": False,
            }]
        },
        issues,
        candidates,
    )
    assert validated[0]["promote_movement_ids"] == ["mov_related"]


def test_selector_rejects_promotion_without_selected_candidate():
    issues = [{
        "issue_id": "i1",
        "kind": "REQUEST",
        "text": "Pedido",
        "retrieval_query": "pedido",
        "target_source_refs": [{
            "document_id": "doc1", "pdf_page": 2,
            "quote": "Requer a restituição integral do valor.",
        }],
    }]
    candidates = [{
        "candidate_id": "ctx_1",
        "issue_id": "i1",
        "movement_id": "mov_related",
        "movement_title": "Decisão",
        "excerpt": "Trecho",
        "score": 0.5,
        "source_ref": {"document_id": "doc2", "pdf_page": 1},
        "retrieval_route": "HYBRID_FALLBACK",
    }]
    try:
        validate_selection(
            {
                "selections": [{
                    "issue_id": "i1",
                    "candidate_ids": [],
                    "promote_movement_ids": ["mov_related"],
                    "unresolved": True,
                }]
            },
            issues,
            candidates,
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "promoção sem candidate selecionado" in str(exc)


def test_apply_selection_and_promote_full_related_document(tmp_path):
    path = _db(tmp_path)
    candidates = [{
        "candidate_id": "ctx_1",
        "issue_id": "i1",
        "movement_id": "mov_related",
        "movement_title": "Decisão anterior",
        "excerpt": "O juízo determinou a intimação para pagamento.",
        "score": 0.5,
        "source_ref": {"document_id": "doc2", "pdf_page": 1},
        "retrieval_route": "HYBRID_FALLBACK",
    }]
    selections = [{
        "issue_id": "i1",
        "candidate_ids": ["ctx_1"],
        "promote_movement_ids": ["mov_related"],
        "unresolved": False,
    }]
    selected, promote, unresolved = apply_context_selection(candidates, selections)
    assert selected == candidates
    assert promote == ["mov_related"]
    assert unresolved == []

    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    docs = load_related_documents(
        db, "proc", promote, target_movement_id="mov_target"
    )
    db.close()
    assert docs[0]["source_mode"] == "FULL_CANONICAL"
    assert docs[0]["movement_id"] == "mov_related"
    assert docs[0]["full_text"] == "O juízo determinou a intimação para pagamento."


def test_context_builder_orchestrates_issue_retrieval_selection_and_promotion(monkeypatch, tmp_path):
    import asyncio
    from core.drafting import context_builder_v1 as builder

    path = _db(tmp_path)

    issue_result = {
        "parsed": {
            "issues": [{
                "issue_id": "i1",
                "kind": "REQUEST",
                "text": "Pedido de restituição",
                "retrieval_query": "restituição pagamento",
                "target_source_refs": [{
                    "document_id": "doc1",
                    "pdf_page": 2,
                    "quote": "Requer a restituição integral do valor.",
                }],
            }]
        },
        "provider": "test",
        "model": "test-model",
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }
    selector_result = {
        "parsed": {
            "selections": [{
                "issue_id": "i1",
                "candidate_ids": ["ctx_real"],
                "promote_movement_ids": ["mov_related"],
                "unresolved": False,
            }]
        },
        "provider": "test",
        "model": "test-model",
        "usage": {"input_tokens": 8, "output_tokens": 3},
    }

    class FakeLlm:
        def __init__(self):
            self.responses = [issue_result, selector_result]

        async def acomplete_structured(self, **kwargs):
            return self.responses.pop(0)

    monkeypatch.setattr(
        builder,
        "retrieve_related_sources",
        lambda *a, **k: [{
            "candidate_id": "ctx_real",
            "issue_id": "i1",
            "query": "restituição pagamento",
            "movement_id": "mov_related",
            "movement_title": "Decisão anterior",
            "excerpt": "O juízo determinou a intimação para pagamento.",
            "score": 0.5,
            "source_ref": {
                "process_id": "proc",
                "document_id": "doc2",
                "pdf_page": 1,
                "process_folio": 50,
            },
            "autos_navigation": {"page": 1},
            "source_mode": "RETRIEVED_EXCERPT",
            "retrieval_route": "HYBRID_FALLBACK",
        }],
    )
    task = DraftingTask(
        task_id="task-builder",
        process_id="proc",
        task_kind="RESPOND_TO_MOVEMENT",
        goal="Responder à petição",
        target_movement_id="mov_target",
    )
    result = asyncio.run(
        builder.build_context_pack(
            FakeLlm(),
            task,
            db_path=path,
            provider="test",
            model="test-model",
            top_k_per_issue=3,
        )
    )

    pack = result["pack"]
    assert pack["target_document"]["movement_id"] == "mov_target"
    assert pack["related_sources"][0]["candidate_id"] == "ctx_real"
    assert pack["related_documents"][0]["movement_id"] == "mov_related"
    assert pack["unresolved_points"] == []
    assert result["trace"]["retrieval_candidate_count"] == 1
