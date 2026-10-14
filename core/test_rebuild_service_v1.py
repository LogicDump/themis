"""Offline preflight must never touch installed process data."""
import hashlib
import json
from pathlib import Path
from contextlib import closing
import pytest

from core.rebuild_service import audit_rebuild, rebuild_process

PID = "1000045-87.2026.8.26.0450"


def _package(root: Path):
    process = root / "processos" / PID
    objects = process / "fontes" / "objetos"
    objects.mkdir(parents=True)
    blob = b"%PDF-test fixture"
    digest = hashlib.sha256(blob).hexdigest()
    (objects / (digest + ".pdf")).write_bytes(blob)
    (process / "fontes" / "pecas_manifest.json").write_text(
        json.dumps({"pecas": [{"sha256": digest, "document_id": digest}]}),
        encoding="utf-8")
    (process / "source_snapshot.json").write_text(
        json.dumps({"documents": [{"cdDocumento": "abc"}]}), encoding="utf-8")
    return process, digest


def test_rebuild_dry_run_preserves_sources(tmp_path):
    package, digest = _package(tmp_path)
    old = (package / "fontes" / "objetos" / (digest + ".pdf")).read_bytes()
    result = rebuild_process(tmp_path, PID, dry_run=True)
    assert result["status"] == "DRY_RUN"
    assert result["pdfs"] == result["pieces"] == 1
    assert (package / "fontes" / "objetos" / (digest + ".pdf")).read_bytes() == old
    assert not (tmp_path / ".rebuild").exists()


def test_rebuild_refuses_bad_sha(tmp_path):
    package, digest = _package(tmp_path)
    (package / "fontes" / "objetos" / (digest + ".pdf")).write_bytes(b"bad")
    with pytest.raises(ValueError, match="corrompido"):
        audit_rebuild(tmp_path, PID)


def test_failed_rebuild_leaves_original_untouched(tmp_path, monkeypatch):
    from core.bridge import sync_service
    package, digest = _package(tmp_path)
    marker = package / "manifest.json"
    marker.write_text('{"state":"ORIGINAL"}', encoding="utf-8")
    monkeypatch.setattr(sync_service, "plan_process_sync", lambda *a, **k: None)

    def broken_pipeline(*args):
        raise RuntimeError("simulated indexing failure")

    with pytest.raises(RuntimeError, match="simulated indexing"):
        rebuild_process(tmp_path, PID, pipeline=broken_pipeline)
    assert marker.read_text(encoding="utf-8") == '{"state":"ORIGINAL"}'
    assert (package / "fontes" / "objetos" / (digest + ".pdf")).exists()


def test_rebuild_rejects_invalid_cnj(tmp_path):
    with pytest.raises(ValueError):
        audit_rebuild(tmp_path, "../../evil")


def test_rebuild_swap_fixture(tmp_path, monkeypatch):
    import sqlite3
    from core.bridge import sync_service
    package, digest = _package(tmp_path)
    (package / "manifest.json").write_text('{"state":"OLD"}', encoding="utf-8")
    monkeypatch.setattr(sync_service, "plan_process_sync", lambda *a, **k: None)
    monkeypatch.setattr(sync_service, "_finalize_process_package", lambda *a, **k: None)

    def simulate_pipeline(store, cnj):
        with closing(store.connect()) as db:
            db.execute("INSERT OR IGNORE INTO processes VALUES(?,?,?)", (cnj, "ACTIVE", "now"))
            db.execute("INSERT INTO files VALUES(?,?,?,?,?)",
                       ("f", str(store.source_path(digest)), digest, 17, "now"))
            db.execute("INSERT INTO documents VALUES(?,?,?,?,?,?,?)",
                       (digest, cnj, "f", "PDF", "complete", 1, "now"))
            db.commit()
            db.execute("INSERT INTO pages(page_id,document_id,page_number,content,quality,content_id) "
                       "VALUES(?,?,?,?,?,?)", ("p1", digest, 1, "test", "OK", "c"))
            db.commit()

    result = rebuild_process(tmp_path, PID, pipeline=simulate_pipeline)
    assert result["changed"] and result["documents"] == 1
    assert (Path(result["backup"]) / "manifest.json").read_text(encoding="utf-8") == '{"state":"OLD"}'
    with sqlite3.connect(package / "process.db") as db:
        saved = db.execute("SELECT path FROM files").fetchone()[0]
    assert saved == str(package / "fontes" / "objetos" / (digest + ".pdf"))


def test_vector_validation_rejects_missing_rows(tmp_path):
    import sqlite3
    from core.rebuild_service import _validate_result
    db_path = tmp_path / 'vectors.db'
    with sqlite3.connect(db_path) as db:
        db.execute('CREATE TABLE documents(process_id TEXT)')
        db.execute('CREATE TABLE pages(page_id TEXT)')
        db.execute('INSERT INTO documents VALUES(?)', (PID,))
        db.execute('INSERT INTO pages VALUES(?)', ('p1',))
    with pytest.raises(RuntimeError, match='Embeddings incompletos'):
        _validate_result(db_path, 1, PID, require_vectors=True)


def test_ai_derivatives_need_explicit_confirmation(tmp_path):
    import sqlite3
    package, _ = _package(tmp_path)
    with sqlite3.connect(package / 'process.db') as db:
        db.execute('CREATE TABLE movement_summaries(summary_id TEXT)')
        db.execute('INSERT INTO movement_summaries VALUES(?)', ('existing',))
    with pytest.raises(ValueError, match='discard-ai'):
        rebuild_process(tmp_path, PID)
    assert (package / 'process.db').is_file()
    assert audit_rebuild(tmp_path, PID)['ai_derivatives']['movement_summaries'] == 1


def test_swap_denied_restores_original_and_preserves_stage(tmp_path, monkeypatch):
    from core.rebuild_service import _swap_packages
    original = tmp_path / "processos" / PID
    original.mkdir(parents=True)
    (original / "original.txt").write_text("original", encoding="utf-8")
    staged = tmp_path / ".rebuild" / "job" / "processos" / PID
    staged.mkdir(parents=True)
    (staged / "rebuilt.txt").write_text("new", encoding="utf-8")
    backup = tmp_path / ".rebuild-backups" / PID / "job"
    backup.parent.mkdir(parents=True)
    real_rename = Path.rename

    def fail_final_rename(path, target):
        if Path(path) == staged and Path(target) == original:
            raise PermissionError(5, "Windows file is locked")
        return real_rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_final_rename)
    with pytest.raises(RuntimeError, match="original restaurado"):
        _swap_packages(original, staged, backup)
    assert (original / "original.txt").read_text(encoding="utf-8") == "original"
    assert (staged / "rebuilt.txt").read_text(encoding="utf-8") == "new"
    assert not backup.exists()


def test_partial_staging_cannot_be_installed(tmp_path):
    from core.rebuild_service import inspect_staged_package
    token = "a" * 32
    stage = tmp_path / ".rebuild" / token / "processos" / PID
    stage.mkdir(parents=True)
    (stage / "process.db").write_bytes(b"not enough")
    result = inspect_staged_package(tmp_path, PID, token)
    assert result["eligible"] is False
    assert "fontes/objetos" in result["missing"]
    assert "manifest.json" in result["missing"]
    assert stage.exists()


def test_legal_guard_blocks_missing_djen_and_deadlines(tmp_path):
    import sqlite3
    from core.rebuild_service import _legal_rebuild_guard
    original, rebuilt = tmp_path / "original.db", tmp_path / "rebuilt.db"
    for path, count in ((original, 2), (rebuilt, 0)):
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE publications(process_id TEXT)")
            db.execute("CREATE TABLE deadline_calculations(process_id TEXT)")
            db.execute("CREATE TABLE deadlines(owner_type TEXT,owner_id TEXT)")
            db.execute("CREATE TABLE process_events(process_id TEXT)")
            for _ in range(count):
                db.execute("INSERT INTO publications VALUES(?)", (PID,))
                db.execute("INSERT INTO deadline_calculations VALUES(?)", (PID,))
                db.execute("INSERT INTO deadlines VALUES('PROCESS',?)", (PID,))
                db.execute("INSERT INTO process_events VALUES(?)", (PID,))
    with pytest.raises(RuntimeError, match="REBUILD_BLOQUEADO"):
        _legal_rebuild_guard(original, rebuilt, PID)


def test_legal_guard_preserves_complete_reconstruction(tmp_path):
    import sqlite3
    from core.rebuild_service import _legal_rebuild_guard
    original, rebuilt = tmp_path / "old.db", tmp_path / "new.db"
    for path in (original, rebuilt):
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE publications(process_id TEXT)")
            db.execute("INSERT INTO publications VALUES(?)", (PID,))
    report = _legal_rebuild_guard(original, rebuilt, PID)
    assert report["missing"] == {}
    assert report["legal_before"]["publications"] == 1


def test_malformed_legal_source_is_incomplete_before_pipeline(tmp_path):
    import sqlite3
    package, _ = _package(tmp_path)
    with sqlite3.connect(package / "process.db") as db:
        db.execute("CREATE TABLE publications(process_id TEXT)")
        db.execute("INSERT INTO publications VALUES(?)", (PID,))
    result = rebuild_process(tmp_path, PID, allow_ai_loss=True)
    assert result["status"] == "INCOMPLETE" and not result["changed"]
    assert (package / "process.db").is_file()
    assert Path(result["staging"]).is_dir()


def test_reclassified_document_event_requires_preserved_autos_and_no_deadline(tmp_path):
    import sqlite3
    from core.rebuild_service import _legal_rebuild_guard
    original, rebuilt = tmp_path / "old_events.db", tmp_path / "new_events.db"

    def create(path):
        db = sqlite3.connect(path)
        db.executescript("""
            CREATE TABLE process_events(event_id TEXT,process_id TEXT,event_type TEXT,
                source_entity TEXT,source_id TEXT,title TEXT,event_date TEXT,
                event_time TEXT,date_precision TEXT);
            CREATE TABLE movements(movement_id TEXT,process_id TEXT);
            CREATE TABLE movement_pieces(movement_id TEXT,document_id TEXT);
            CREATE TABLE documents(document_id TEXT,process_id TEXT);
            CREATE TABLE chronology_events(owner_type TEXT,owner_id TEXT);
            CREATE TABLE deadline_instructions(process_id TEXT,movement_id TEXT);
            CREATE TABLE deadline_obligations(process_id TEXT,origin_movement_id TEXT);
        """)
        db.execute("INSERT INTO documents VALUES('sha256_document',?)", (PID,))
        db.execute("INSERT INTO chronology_events VALUES('PROCESS',?)", (PID,))
        db.commit()
        return db

    with create(original) as old, create(rebuilt) as stage:
        old.execute("INSERT INTO movements VALUES('legacy_movement',?)", (PID,))
        old.execute("INSERT INTO movement_pieces VALUES('legacy_movement','sha256_document')")
        old.execute("""INSERT INTO process_events VALUES(
            'old_event',?,'MOVEMENT','MOVEMENT','legacy_movement',
            'Documentos diversos',NULL,NULL,'UNKNOWN')""", (PID,))
        old.commit()
        result = _legal_rebuild_guard(original, rebuilt, PID)
        assert result["missing"] == {}
        assert result["movement_reclassification"]["reclassified"] == 1
        stage.execute("DELETE FROM documents")
        stage.commit()
        with pytest.raises(RuntimeError, match="peça documental"):
            _legal_rebuild_guard(original, rebuilt, PID)
        stage.execute("INSERT INTO documents VALUES('sha256_document',?)", (PID,))
        old.execute("INSERT INTO deadline_instructions VALUES(?,'legacy_movement')", (PID,))
        old.commit()
        with pytest.raises(RuntimeError, match="REBUILD_BLOQUEADO"):
            _legal_rebuild_guard(original, rebuilt, PID)


def test_legal_guard_rejects_changed_existing_event_date(tmp_path):
    import sqlite3
    from core.rebuild_service import _legal_rebuild_guard
    old_path, new_path = tmp_path / "events_old.db", tmp_path / "events_new.db"
    for path, day in ((old_path, "2026-09-03"), (new_path, "2026-09-04")):
        with sqlite3.connect(path) as db:
            db.execute("""CREATE TABLE process_events(
                event_id TEXT,process_id TEXT,event_type TEXT,source_entity TEXT,
                source_id TEXT,title TEXT,event_date TEXT,event_time TEXT,
                date_precision TEXT)""")
            db.execute("INSERT INTO process_events VALUES(?,?,?,?,?,?,?,?,?)",
                       ("same_event", PID, "PUBLICATION", "PUBLICATION", "pub_x",
                        "Intimação", day, None, "DAY"))
    with pytest.raises(RuntimeError, match="eventos existentes alterados"):
        _legal_rebuild_guard(old_path, new_path, PID)


def test_vector_validation_accepts_only_complete_litert_signature(tmp_path):
    import sqlite3
    from core.rebuild_service import _validate_result
    from core.retrieval.embeddinggemma2_litert import (
        MODEL, VERSION, QUANTIZATION, DIM, BACKEND_GPU,
    )
    from core.retrieval.vector_store import pack_vector
    path = tmp_path / "litert.db"
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE documents(document_id TEXT,process_id TEXT);
            CREATE TABLE pages(page_id TEXT,document_id TEXT,page_number INTEGER);
            CREATE TABLE page_embeddings(page_id TEXT,document_id TEXT,process_id TEXT,
              page_number INTEGER,model TEXT,backend TEXT,model_version TEXT,
              quantization TEXT,dim INTEGER,vector_blob BLOB);
            CREATE TABLE vector_index_metadata(process_id TEXT,model TEXT,
              backend TEXT,model_version TEXT,quantization TEXT,dim INTEGER);
        """)
        db.execute("INSERT INTO documents VALUES('doc',?)", (PID,))
        db.execute("INSERT INTO pages VALUES('doc:1','doc',1)")
        db.execute("INSERT INTO page_embeddings VALUES(?,?,?,?,?,?,?,?,?,?)",
                   ("doc:1", "doc", PID, 1, MODEL, BACKEND_GPU, VERSION,
                    QUANTIZATION, DIM, pack_vector([1.0] + [0.0] * (DIM-1))))
        db.execute("INSERT INTO vector_index_metadata VALUES(?,?,?,?,?,?)",
                   (PID, MODEL, BACKEND_GPU, VERSION, QUANTIZATION, DIM))
        db.commit()
        assert _validate_result(path, 1, PID, require_vectors=True)["embeddings"] == 1
        db.execute("UPDATE page_embeddings SET model_version='v1'")
        db.commit()
        with pytest.raises(RuntimeError, match="LiteRT inválidos"):
            _validate_result(path, 1, PID, require_vectors=True)


def test_rebuild_refuses_swap_when_original_changes(tmp_path, monkeypatch):
    from core.bridge import sync_service
    from core import rebuild_service
    package, digest = _package(tmp_path)
    marker = package / "manifest.json"
    marker.write_text('{"state":"ORIGINAL"}', encoding="utf-8")
    monkeypatch.setattr(sync_service, "plan_process_sync", lambda *a, **k: None)
    monkeypatch.setattr(sync_service, "_finalize_process_package", lambda *a, **k: None)
    monkeypatch.setattr(rebuild_service, "_validate_result", lambda *a, **k: {"documents": 1, "pages": 1})
    monkeypatch.setattr(rebuild_service, "_swap_packages", lambda *a: pytest.fail("source changed; swap forbidden"))
    def pipeline(store, cnj):
        marker.write_text('{"state":"CONCURRENT_UPDATE"}', encoding="utf-8")
        return {"status": "READY"}
    with pytest.raises(RuntimeError, match="alterado durante staging"):
        rebuild_process(tmp_path, PID, pipeline=pipeline)
    assert marker.read_text(encoding="utf-8") == '{"state":"CONCURRENT_UPDATE"}'
    assert list((tmp_path / ".rebuild").glob("*/processos/" + PID))
    assert not list((tmp_path / ".rebuild-backups").glob("*/*/process.db"))
