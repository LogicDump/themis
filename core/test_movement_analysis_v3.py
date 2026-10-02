from copy import deepcopy

from core.documentos.movement_analysis_v3 import validate_analysis


MID = "mov_test"
DOC = "doc_test"
SOURCE = "A autora afirma que pagou R$ 500,00 em 10/09/2026. Requer a restituição do valor."


def _payload():
    ref = {"document_id": DOC, "page_number": 1, "quote": "pagou R$ 500,00 em 10/09/2026"}
    evidence = {
        "key": "fact_payment",
        "semantic_role": "FACTUAL_ASSERTION",
        "text": "A autora afirma ter pago R$ 500,00 em 10/09/2026.",
        "actor": {"mode": "SOURCE_TEXT", "value": "A autora"},
        "epistemic_status": "UNILATERAL",
        "support_status": "NONE_IN_CONTEXT",
        "temporal_reference": "10/09/2026",
        "material_qualifiers": ["A autora afirma", "R$ 500,00", "10/09/2026"],
        "source_refs": [ref],
    }
    return {
        "movements": [{
            "movement_id": MID,
            "summary": "A autora afirma pagamento e requer restituição.",
            "summary_source_refs": [ref],
            "evidence": [evidence],
            "drafting_extracts": [{
                "key": "draft_payment",
                "evidence_key": "fact_payment",
                "text": "Segundo a autora, houve pagamento de R$ 500,00 em 10/09/2026.",
                "semantic_role": evidence["semantic_role"],
                "actor": evidence["actor"],
                "epistemic_status": evidence["epistemic_status"],
                "support_status": evidence["support_status"],
                "material_qualifiers": evidence["material_qualifiers"],
                "source_refs": evidence["source_refs"],
            }],
            "relations": [],
        }]
    }


def _validate(payload):
    return validate_analysis(
        payload,
        [MID],
        sources={MID: {(DOC, 1): SOURCE}},
        known_ids=set(),
        main_ids={"proc_test", "party_author"},
        actor_ids={"party_author"},
    )


def test_v3_accepts_source_verifiable_factual_assertion_and_drafting_extract():
    result = _validate(_payload())
    assert result[0]["evidence"][0]["epistemic_status"] == "UNILATERAL"


def test_v3_rejects_drafting_extract_that_changes_epistemic_status():
    payload = _payload()
    payload["movements"][0]["drafting_extracts"][0]["epistemic_status"] = "JUDICIALLY_FOUND"
    try:
        _validate(payload)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "diverge da evidence" in str(exc)


def test_v3_rejects_unverifiable_quote():
    payload = _payload()
    payload["movements"][0]["evidence"][0]["source_refs"][0]["quote"] = "texto inexistente"
    try:
        _validate(payload)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "provenance não conferível" in str(exc)


def test_v3_rejects_judicial_finding_without_judicially_found_status():
    payload = _payload()
    evidence = payload["movements"][0]["evidence"][0]
    evidence["semantic_role"] = "JUDICIAL_FINDING"
    evidence["epistemic_status"] = "UNILATERAL"
    evidence["support_status"] = "NOT_APPLICABLE"
    draft = payload["movements"][0]["drafting_extracts"][0]
    draft["semantic_role"] = "JUDICIAL_FINDING"
    draft["epistemic_status"] = "UNILATERAL"
    draft["support_status"] = "NOT_APPLICABLE"
    try:
        _validate(payload)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "JUDICIAL_FINDING exige JUDICIALLY_FOUND" in str(exc)


def test_v3_rejects_non_literal_material_qualifier():
    payload = _payload()
    payload["movements"][0]["evidence"][0]["material_qualifiers"][0] = "qualificador inventado"
    payload["movements"][0]["drafting_extracts"][0]["material_qualifiers"][0] = "qualificador inventado"
    try:
        _validate(payload)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "material_qualifier não conferível" in str(exc)


def test_v3_rejects_nonfactual_role_with_factual_epistemic_status():
    payload = _payload()
    evidence = payload["movements"][0]["evidence"][0]
    evidence["semantic_role"] = "REQUEST"
    evidence["epistemic_status"] = "UNILATERAL"
    evidence["support_status"] = "NOT_APPLICABLE"
    draft = payload["movements"][0]["drafting_extracts"][0]
    draft["semantic_role"] = "REQUEST"
    draft["epistemic_status"] = "UNILATERAL"
    draft["support_status"] = "NOT_APPLICABLE"
    try:
        _validate(payload)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "papel não factual exige estado NOT_APPLICABLE" in str(exc)


def test_summary_targets_require_current_v3_analysis(tmp_path):
    import sqlite3
    from core.api import core_api

    db_path = tmp_path / "process.db"
    db = sqlite3.connect(db_path)
    db.executescript("""
        CREATE TABLE processes(process_id TEXT PRIMARY KEY);
        CREATE TABLE movements(movement_id TEXT PRIMARY KEY, process_id TEXT NOT NULL, sequence INTEGER);
        CREATE TABLE movement_summary_source_state(
            movement_id TEXT PRIMARY KEY, source_hash TEXT, eligible INTEGER NOT NULL
        );
        CREATE TABLE movement_summaries(
            movement_id TEXT NOT NULL, summary_version INTEGER NOT NULL,
            source_hash TEXT, summary_text TEXT, analysis_schema_version TEXT
        );
    """)
    db.execute("INSERT INTO processes VALUES('proc')")
    db.execute("INSERT INTO movements VALUES('mov','proc',1)")
    db.execute("INSERT INTO movement_summary_source_state VALUES('mov','hash',1)")
    db.execute(
        "INSERT INTO movement_summaries VALUES('mov',1,'hash','Resumo legado',NULL)"
    )
    db.commit()
    db.close()

    pending = core_api.process_movement_summary_targets("proc", path=db_path)
    assert pending["movement_ids"] == ["mov"]

    db = sqlite3.connect(db_path)
    db.execute(
        "UPDATE movement_summaries SET analysis_schema_version='movement-analysis-v3'"
    )
    db.commit()
    db.close()
    current = core_api.process_movement_summary_targets("proc", path=db_path)
    assert current["movement_ids"] == []


def test_summary_worker_persists_v3_analysis(monkeypatch):
    import asyncio
    from dashboard import movement_summary_worker as worker

    ref = {"document_id": DOC, "page_number": 1, "quote": "pagou R$ 500,00 em 10/09/2026"}
    parsed = {
        "movements": [{
            "movement_id": MID,
            "summary": "A autora afirma pagamento.",
            "summary_source_refs": [ref],
            "evidence": [],
            "drafting_extracts": [],
            "relations": [],
        }]
    }

    class FakeLlm:
        async def acomplete_structured(self, **kwargs):
            return {
                "parsed": parsed,
                "provider": "test-provider",
                "model": "test-model",
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }

    async def direct_call(llm, method, **kwargs):
        return await getattr(llm, method)(**kwargs)

    saved = []
    monkeypatch.setattr(worker, "call_long_job_llm", direct_call)
    monkeypatch.setattr(worker, "begin_call_diagnostic", lambda *a, **k: ({}, 0.0))
    monkeypatch.setattr(worker, "finish_call_diagnostic", lambda *a, **k: None)
    monkeypatch.setattr(worker, "_persist", lambda job: job)
    monkeypatch.setattr(worker, "_is_cancel_requested", lambda job: False)
    monkeypatch.setattr(worker.core_api, "movement_analysis_v3_current", lambda movement_id: None)
    monkeypatch.setattr(
        worker.core_api,
        "movement_analysis_v3_context",
        lambda process_id: {
            "main": {"process_id": process_id, "status": "ACTIVE", "parties": [], "representations": []},
            "main_ids": {process_id},
            "actor_ids": set(),
            "known": [],
            "known_ids": set(),
        },
    )
    monkeypatch.setattr(
        worker.core_api,
        "save_movement_analysis_v3_batch_record",
        lambda records, **kwargs: saved.extend(records) or {"imported": len(records)},
    )

    record = {
        "movement_id": MID,
        "origin": None,
        "occurred_at": "2026-09-10",
        "movement_type": "Petição",
        "pages": [{"document_id": DOC, "page_number": 1}],
        "source_text": SOURCE,
        "source_hash": "hash",
        "_source_pages": {(DOC, 1): SOURCE},
        "process_id": "proc",
    }
    job = {
        "process_id": "proc",
        "job_id": "job",
        "provider": "test-provider",
        "model": "test-model",
        "force_all": False,
        "completed": 0,
        "failed": 0,
        "errors": [],
    }
    counters = {"completed": 0, "failed": 0, "errors": []}

    asyncio.run(worker._run_summary_unit(job, [MID], {MID: record}, FakeLlm(), counters, 1))

    assert counters == {"completed": 1, "failed": 0, "errors": []}
    assert saved[0]["analysis"]["movement_id"] == MID
    assert saved[0]["summary"] == "A autora afirma pagamento."


def test_v3_rejects_numeric_hallucination_in_drafting_extract():
    payload = _payload()
    payload["movements"][0]["drafting_extracts"][0]["text"] = (
        "Segundo a autora, houve pagamento de R$ 900,00 em 10/09/2026."
    )
    try:
        _validate(payload)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "dado numérico não conferível" in str(exc)


def test_v3_persistence_keeps_summary_and_analysis_version(monkeypatch):
    import sqlite3
    from core.documentos import movement_summary_store_v1 as store

    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE movements(movement_id TEXT PRIMARY KEY)")
    db.execute("INSERT INTO movements VALUES(?)", (MID,))
    store._create_summary_table(db)
    db.commit()
    monkeypatch.setattr(store, "_sync_summary_embeddings", lambda db, ids: None)

    analysis = _payload()["movements"][0]
    result = store.save_analysis_v3_batch(
        db,
        [{
            "movement_id": MID,
            "summary": analysis["summary"],
            "source_hash": "hash",
            "analysis": analysis,
        }],
        provider="test-provider",
        model="test-model",
        usage={"input_tokens": 1},
    )

    current = store.current_v3_analysis(db, MID)
    assert result["imported"] == 1
    assert current is not None
    assert current["analysis_schema_version"] == "movement-analysis-v3"
    assert current["summary_text"] == analysis["summary"]
    assert current["analysis"]["drafting_extracts"][0]["evidence_key"] == "fact_payment"


def test_v3_model_input_carries_page_local_content_and_not_flat_source_text():
    from core.documentos.movement_analysis_v3 import build_analysis_input

    record = {
        "movement_id": MID,
        "origin": None,
        "occurred_at": "2026-09-10",
        "movement_type": "Petição",
        "pages": [
            {"document_id": DOC, "page_number": 1, "content": "Página um."},
            {"document_id": DOC, "page_number": 2, "content": "Página dois."},
        ],
        "source_text": "Página um.\n\nPágina dois.",
    }
    payload = build_analysis_input(
        {"process_id": "proc"}, [], [record]
    )
    movement = payload["movements"][0]
    assert movement["pages"][1]["page_number"] == 2
    assert movement["pages"][1]["content"] == "Página dois."
    assert "source_text" not in movement
