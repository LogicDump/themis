"""Core cycle safety: identical projections and abstention before expensive work."""
import json
import sqlite3

import pytest

from core import process_cycle
from core.documentos.themis_documentos import Store

PID = "1000045-87.2026.8.26.0450"


@pytest.mark.parametrize("rebuild", [False, True])
def test_creation_and_rebuild_share_projection_after_evidence(tmp_path, monkeypatch, rebuild):
    from core.bridge import sync_service
    from core.documentos import djen_sync_v1
    store = Store(tmp_path, process_id=PID)
    with store.connect() as db:
        db.execute("INSERT INTO processes VALUES(?,?,?)", (PID, "ACTIVE", "now"))
        db.commit()
    calls = []
    source = tmp_path / "old.db"
    source.touch()
    monkeypatch.setattr(process_cycle, "replay_legal_sources", lambda *a, **k: calls.append("sources"))
    monkeypatch.setattr(process_cycle, "_source_publications", lambda *a, **k: [{"communication_id": "1234", "certificate_code": None}])
    monkeypatch.setattr(process_cycle, "_sync_process_legal", lambda *a, **k: {})

    def prepare(*a, **k):
        assert k["prepare_only"]
        calls.append("evidence")
        return {"status": "OK", "calendar_entries": ["verified-calendar"]}

    def pipeline(*a):
        calls.append("pdfs")
        return {"status": "READY"}

    def project(*a, **k):
        assert k["calendar_entries"] == ["verified-calendar"]
        calls.append("legal")
        return {"status": "READY"}

    monkeypatch.setattr(djen_sync_v1, "_calculate_tjsp_deadlines", prepare)
    monkeypatch.setattr(sync_service, "_process_captured_documents", pipeline)
    monkeypatch.setattr(process_cycle, "project_legal_state", project)
    monkeypatch.setattr(sync_service, "_finalize_process_package", lambda *a: calls.append("seal"))
    result = process_cycle.process_after_acquisition(store, PID, source_db=source if rebuild else None)
    assert result["status"] == "READY"
    assert calls == (["sources"] if rebuild else []) + ["evidence", "pdfs", "legal", "seal"]


def test_incomplete_calendar_preserves_original_and_staging(tmp_path, monkeypatch):
    from core.test_rebuild_service_v1 import _package
    from core.rebuild_service import rebuild_process
    from core.documentos import djen_sync_v1
    from core.bridge import sync_service

    package, _ = _package(tmp_path)
    original = package / "manifest.json"
    original.write_text('{"state":"ORIGINAL"}', encoding="utf-8")
    monkeypatch.setattr(process_cycle, "_source_publications", lambda *a, **k: [{"communication_id": "1234", "certificate_code": None}])
    monkeypatch.setattr(process_cycle, "_sync_process_legal", lambda *a, **k: {})
    monkeypatch.setattr(djen_sync_v1, "_calculate_tjsp_deadlines", lambda *a, **k: {
        "status": "INCOMPLETE", "calendar_errors": [{"year": 2025, "error": "official table missing"}],
    })
    monkeypatch.setattr(sync_service, "_process_captured_documents", lambda *a: pytest.fail("PDF pipeline must not run"))
    result = rebuild_process(tmp_path, PID)
    assert result["status"] == "INCOMPLETE" and not result["changed"]
    assert original.read_text(encoding="utf-8") == '{"state":"ORIGINAL"}'
    from pathlib import Path
    staged = Path(result["staging"])
    assert json.loads((staged / "manifest.json").read_text(encoding="utf-8"))["legal_status"] == "INCOMPLETE"
    assert not (tmp_path / ".rebuild-backups").exists()
    with sqlite3.connect(staged / "process.db") as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_persisted_creation_update_rebuild_equivalence(tmp_path, monkeypatch):
    """Real Core persistence/projectors; extraction, model and HTTP are test doubles."""
    from contextlib import closing
    from pathlib import Path
    from core.test_rebuild_service_v1 import _package
    from core.rebuild_service import rebuild_process
    from core.bridge import sync_service
    from core.pdf import themis_pdf
    from core.documentos import djen_sync_v1, publications_v1, deadline_specialist_v1
    from core.documentos.providers import tjsp_calendar_acquisition_v1 as acquisition
    from core.documentos.court_calendar_provider_v1 import RawSourceSnapshot
    from core.retrieval import embeddinggemma2_litert as embeddings
    from core.test_tjsp_calendar_acquisition_v1 import snapshot_for

    package, digest = _package(tmp_path)
    inventory = package / "fontes" / "pecas_manifest.json"
    pieces = json.loads(inventory.read_text(encoding="utf-8"))
    pieces["captured_at"] = "2026-10-01T00:00:00Z"
    pieces["pecas"][0].update({
        "order": 1, "object_path": f"fontes/objetos/{digest}.pdf", "size_bytes": 17,
        "page_count": 1, "provider_document_id": "abc", "provider_item_identity": "esaj:abc:1",
        "source_filename_literal": "peca.pdf", "folha_inicial": 1, "folha_final": 1,
    })
    inventory.write_text(json.dumps(pieces), encoding="utf-8")
    snapshot = {"documents": [{"cdDocumento": "abc", "title": "Peça documental"}]}
    (package / "source_snapshot.json").write_text(json.dumps(snapshot), encoding="utf-8")
    store = Store(tmp_path, process_id=PID)
    cpopg = {"basic_data": {"foro": "Foro de Piracaia", "distribuicao": "01/01/2026"}}
    sync_service.plan_process_sync(store, PID, **snapshot, cpopg=cpopg)

    class FixedDate:
        @staticmethod
        def today():
            from datetime import date
            return date(2026, 10, 1)
    monkeypatch.setattr(process_cycle, "date", FixedDate)
    http = []
    def fetch(endpoint, **kwargs):
        params = kwargs["query_params"]
        http.append((endpoint, params["ano"]))
        if params["ano"] == "2026":
            return snapshot_for(endpoint)
        # Synthetic empty future registry is a fixture, never a product fallback.
        return RawSourceSnapshot(endpoint, b'{"data":[]}', "2026-10-01T00:00:00Z",
                                 acquisition.PARSER_VERSION, request_params=params)
    real_acquire = acquisition.acquire_tjsp_calendar
    monkeypatch.setattr(acquisition, "acquire_tjsp_calendar", lambda *a, **k: real_acquire(*a, fetcher=fetch, **k))
    djen_calls = []
    def sync(db, **kwargs):
        publications_v1.migrate_connection(db)
        item = {"numero_processo": PID, "id": 1234, "meio": "D", "data_disponibilizacao": "2026-09-03",
                "texto": "Intime-se o autor para juntar documentos em 5 dias."}
        record = publications_v1.publication_from_item(item, process_id=PID,
            request_url="https://comunicaapi.pje.jus.br/api/v1/comunicacao")
        publications_v1.upsert_publication(db, record)
        db.commit()
        djen_calls.append(kwargs)
        return {"count": 1, "changed_count": 0}
    monkeypatch.setattr(djen_sync_v1, "sync_djen", sync)
    monkeypatch.setattr(deadline_specialist_v1, "_model_predictions", lambda text: ({}, {}))
    extracted = []
    def extract(path):
        extracted.append(path.read_bytes())
        return [{"page": 1, "text": "Peça documental", "content_markdown": "Peça documental", "quality": "OK"}]
    monkeypatch.setattr(themis_pdf, "hybrid_pages", extract)
    signature = {"model": embeddings.MODEL, "backend": embeddings.BACKEND_CPU,
                 "model_version": embeddings.VERSION, "quantization": embeddings.QUANTIZATION, "dim": embeddings.DIM}
    monkeypatch.setattr(embeddings, "active_signature", lambda: signature)
    monkeypatch.setattr(embeddings, "embed_many", lambda texts, **k: ([[0.125]*768 for _ in texts], signature))

    def canonical_state():
        with closing(sqlite3.connect(package / "process.db")) as db:
            return {
                "pages": db.execute("SELECT page_id,content,process_folio FROM pages ORDER BY page_id").fetchall(),
                "vectors": db.execute("SELECT page_id,model,backend,model_version,vector_blob FROM page_embeddings ORDER BY page_id").fetchall(),
                "events": db.execute("SELECT event_id,event_type,event_date FROM process_events ORDER BY event_id").fetchall(),
                "calendar": db.execute("SELECT logical_key,payload_json FROM court_calendar_events ORDER BY logical_key").fetchall(),
                "publications": db.execute("SELECT publication_id,payload_hash FROM publications ORDER BY publication_id").fetchall(),
                "instructions": db.execute("SELECT instruction_id FROM deadline_instructions ORDER BY instruction_id").fetchall(),
                "obligations": db.execute("SELECT obligation_id FROM deadline_obligations ORDER BY obligation_id").fetchall(),
                "calculations": db.execute("SELECT calculation_id,status,due_date FROM deadline_calculations ORDER BY calculation_id").fetchall(),
                "deadlines": db.execute("SELECT deadline_id,due_at FROM deadlines ORDER BY deadline_id").fetchall(),
            }
    created = process_cycle.process_after_acquisition(store, PID)
    assert created["status"] == "READY", created
    expected = canonical_state()
    assert len(expected["pages"]) == len(expected["vectors"]) == 1
    assert len(expected["events"]) >= 1 and expected["calendar"]
    assert len(expected["instructions"]) == len(expected["obligations"]) == len(expected["calculations"]) == 1
    assert expected["calculations"][0][1:] == ("CALCULATED", "2026-09-14")
    assert len(expected["deadlines"]) == 1 and expected["deadlines"][0][1] == "2026-09-14"
    assert len(http) == 4 and len(djen_calls) == 1
    updated = process_cycle.process_after_acquisition(store, PID)
    assert updated["status"] == "READY" and canonical_state() == expected
    assert len(http) == 4 and len(djen_calls) == 2 and len(extracted) == 1
    from core.api import core_api
    from core import process_storage
    monkeypatch.setattr(process_storage, "connect_process", lambda pid: store.connect())
    api_result = core_api.sync_publications(PID, available_from="2026-01-01", available_to="2026-10-01")
    assert api_result["status"] == "READY" and canonical_state() == expected
    assert len(djen_calls) == 3
    # Old calculations and corrupt old vectors cannot become inputs to rebuild.
    with closing(sqlite3.connect(package / "process.db")) as db:
        db.execute("DROP TABLE deadline_calculations")
        db.execute("CREATE TABLE deadline_calculations(calculation_id TEXT)")
        db.execute("INSERT INTO deadline_calculations VALUES('old-result-must-not-be-read')")
        db.execute("UPDATE page_embeddings SET vector_blob=x'00'")
        db.commit()
    (package / "derivados" / "old-result.json").write_text('{"legal_result":"obsolete"}', encoding="utf-8")
    rebuilt = rebuild_process(tmp_path, PID)
    assert rebuilt["status"] == "READY", rebuilt
    current = canonical_state()
    for name in expected:
        assert current[name] == expected[name], (name, current[name] if name != "vectors" else "vector divergence", expected[name] if name != "vectors" else "expected vectors")
    assert len(http) == 4 and len(djen_calls) == 3 and len(extracted) == 2
    assert extracted[0] == extracted[1]
    assert not (package / "derivados" / "old-result.json").exists()
    backup = Path(rebuilt["backup"])
    assert (backup / "derivados" / "old-result.json").exists()
    with closing(sqlite3.connect(backup / "process.db")) as db:
        assert db.execute("SELECT calculation_id FROM deadline_calculations").fetchone()[0] == "old-result-must-not-be-read"
    with closing(sqlite3.connect(package / "process.db")) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert not db.execute("PRAGMA foreign_key_check").fetchall()


def test_core_abstains_on_2025_unit_notice_and_keeps_raw_source(tmp_path, monkeypatch):
    from contextlib import closing
    from core.bridge import sync_service
    from core.documentos import djen_sync_v1, publications_v1
    from core.documentos.providers import tjsp_calendar_acquisition_v1 as acquisition
    from core.documentos.court_calendar_provider_v1 import RawSourceSnapshot
    store = Store(tmp_path, process_id=PID)
    sync_service.plan_process_sync(store, PID, documents=[{"cdDocumento": "abc"}], cpopg={"basic_data": {
        "foro": "Foro de Piracaia", "distribuicao": "01/01/2019"}})
    with closing(store.connect()) as db:
        publications_v1.migrate_connection(db)
        record = publications_v1.publication_from_item({"numero_processo": PID, "id": 2025,
            "meio": "D", "data_disponibilizacao": "2025-03-07"}, process_id=PID,
            request_url="https://comunicaapi.pje.jus.br/api/v1/comunicacao")
        publications_v1.upsert_publication(db, record)
        db.commit()
    monkeypatch.setattr(djen_sync_v1, "sync_djen", lambda *a, **k: {"count": 1})
    notice = json.dumps({"data": [{"Data": "10/03/2025 a 14/03/2025",
        "Descricao": "Comunicado Conjunto 138/2025 - suspensão nas unidades elencadas em tabela"}]}).encode()
    def fetch(endpoint, **kwargs):
        params = kwargs["query_params"]
        raw = notice if params["ano"] == "2025" and endpoint == acquisition.SUSPENSIONS_ENDPOINT else b'{"data":[]}'
        return RawSourceSnapshot(endpoint, raw, "2026-10-01T00:00:00Z", acquisition.PARSER_VERSION,
                                 request_params=params)
    real_acquire = acquisition.acquire_tjsp_calendar
    monkeypatch.setattr(acquisition, "acquire_tjsp_calendar", lambda *a, **k: real_acquire(*a, fetcher=fetch, **k))
    monkeypatch.setattr(sync_service, "_process_captured_documents", lambda *a: pytest.fail("evidence gap precedes PDFs"))
    result = process_cycle.process_after_acquisition(store, PID, available_to="2026-10-01")
    assert result["status"] == "INCOMPLETE"
    manifest = json.loads(store.process_manifest_path(PID).read_text(encoding="utf-8"))
    assert manifest["status"] == manifest["pipeline_status"] == manifest["legal_status"] == "INCOMPLETE"
    with closing(store.connect()) as db:
        assert any(bytes(row[0]) == notice for row in db.execute("SELECT content FROM court_calendar_snapshots"))
        assert db.execute("SELECT count(*) FROM deadlines WHERE owner_id=?", (PID,)).fetchone()[0] == 0
        assert db.execute("SELECT status FROM processes WHERE process_id=?", (PID,)).fetchone()[0] == "INCOMPLETE"


def test_missing_djen_raw_item_is_automatically_reacquired(tmp_path, monkeypatch):
    from contextlib import closing
    from core.bridge import sync_service
    from core.documentos import djen_sync_v1, publications_v1
    source = Store(tmp_path / "original", process_id=PID)
    target = Store(tmp_path / "staged", process_id=PID)
    for store in (source, target):
        sync_service.plan_process_sync(store, PID, documents=[{"cdDocumento": "abc"}], cpopg={"basic_data": {
            "foro": "Foro de Piracaia", "distribuicao": "01/01/2026"}})
    item = {"numero_processo": PID, "id": 1234, "meio": "D", "data_disponibilizacao": "2026-09-03"}
    record = publications_v1.publication_from_item(item, process_id=PID,
        request_url="https://comunicaapi.pje.jus.br/api/v1/comunicacao")
    with closing(source.connect()) as db:
        publications_v1.migrate_connection(db)
        publications_v1.upsert_publication(db, record)
        db.execute("UPDATE publications SET provenance_json='{}'")
        db.commit()
    original = source.db_path.read_bytes()
    calls = []
    def sync(db, **kwargs):
        calls.append(kwargs)
        publications_v1.migrate_connection(db)
        publications_v1.upsert_publication(db, record)
        db.commit()
        return {"count": 1}
    monkeypatch.setattr(djen_sync_v1, "sync_djen", sync)
    monkeypatch.setattr(djen_sync_v1, "_calculate_tjsp_deadlines", lambda *a, **k: {"status": "OK", "calendar_entries": []})
    monkeypatch.setattr(sync_service, "_process_captured_documents", lambda *a: {"status": "DOCUMENTS_READY"})
    result = process_cycle.process_after_acquisition(target, PID, source_db=source.db_path, available_to="2026-10-01")
    assert result["status"] == "READY" and len(calls) == 1
    assert calls[0]["available_from"] == "2026-01-01"
    assert source.db_path.read_bytes() == original
    with closing(target.connect()) as db:
        restored = process_cycle._source_publications(db, PID)
        assert len(restored) == 1 and restored[0]["payload_hash"] == record["payload_hash"]
