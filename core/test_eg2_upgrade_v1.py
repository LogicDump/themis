"""Upgrade existing EG1 Process Packages without reprocessing legal source data."""
import sqlite3
import struct

import pytest
from core.retrieval import eg2_upgrade_v1 as up
from core.retrieval import embeddinggemma2_litert as eg2
from core.retrieval.vector_store import VectorStore


CNJ = "1234567-89.2026.8.26.0123"
SIG = {"model": eg2.MODEL, "backend": eg2.BACKEND_CPU,
       "model_version": eg2.VERSION, "quantization": eg2.QUANTIZATION, "dim": eg2.DIM}
VECTOR = [1.0] + [0.0] * (eg2.DIM - 1)


def _fixture(tmp_path):
    path = tmp_path / "process.db"
    with sqlite3.connect(path) as db:
        db.executescript("""
          CREATE TABLE documents(document_id TEXT PRIMARY KEY,process_id TEXT);
          CREATE TABLE pages(page_id TEXT PRIMARY KEY,document_id TEXT,
              page_number INTEGER,content TEXT);
          CREATE TABLE movements(movement_id TEXT PRIMARY KEY, title TEXT,payload_json TEXT);
          CREATE TABLE movement_summaries(summary_id TEXT,movement_id TEXT,
              summary_version INTEGER,summary_text TEXT,source_hash TEXT);
          CREATE TABLE movement_summary_source_state(movement_id TEXT,eligible INTEGER,source_hash TEXT);
          INSERT INTO documents VALUES('doc','1234567-89.2026.8.26.0123');
          INSERT INTO pages VALUES('doc:1','doc',1,'Decisão favorável.'),
                                   ('doc:2','doc',2,'Intimação válida.');
          INSERT INTO movements VALUES('mov','Despacho','{}');
          INSERT INTO movement_summaries VALUES('sum','mov',1,'Resumo jurídico persistido','hash');
          INSERT INTO movement_summary_source_state VALUES('mov',1,'hash');
        """)
    store = VectorStore(path)
    with store.connect() as db:
        db.execute("""INSERT INTO page_embeddings
          (page_id,document_id,process_id,page_number,model,backend,model_version,
           quantization,dim,vector_blob,content_hash,updated_at)
           VALUES('doc:1','doc',?,1,'embeddinggemma:300m','onnx','v1',
                  'int8',768,?,'legacy','now')""",(CNJ,struct.pack("768f",*VECTOR)))
        db.execute("""INSERT INTO vector_index_metadata VALUES
            (?,'embeddinggemma:300m','onnx','v1','int8',768,'now','now')""",(CNJ,))
        db.commit()
    return path


def _fake(monkeypatch, fail_on=None):
    calls = []
    monkeypatch.setattr(up.eg2, "active_signature", lambda required=None: dict(SIG))
    def embed(texts, *, required_backend=None, is_query=False):
        assert required_backend == eg2.BACKEND_CPU
        calls.append(list(texts))
        if fail_on == len(calls):
            raise RuntimeError("Interrupted")
        return [list(VECTOR) for _ in texts], dict(SIG)
    monkeypatch.setattr(up.eg2, "embed_many", embed)
    monkeypatch.setattr(up.summary_embedding_store, "embed_many", embed)
    monkeypatch.setattr(up.summary_embedding_store, "active_signature", lambda backend=None: dict(SIG))
    return calls


def test_upgrade_preserves_legal_sources_and_legacy_vectors(tmp_path,monkeypatch):
    path=_fixture(tmp_path)
    calls=_fake(monkeypatch)
    with sqlite3.connect(path) as db:
        original=db.execute("SELECT content FROM pages ORDER BY page_id").fetchall()
        summary=db.execute("SELECT summary_text FROM movement_summaries").fetchone()[0]
    first=up.upgrade_process(path,CNJ,batch_size=1)
    assert first["status"] == "READY" and first["written"]==2
    assert first["summaries_written"]==1
    assert len(calls)==3
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT content FROM pages ORDER BY page_id").fetchall()==original
        assert db.execute("SELECT summary_text FROM movement_summaries").fetchone()[0]==summary
        assert db.execute("SELECT count(*) FROM page_embeddings WHERE model='embeddinggemma:300m'").fetchone()[0]==1
        assert db.execute("SELECT count(*) FROM page_embeddings WHERE model=?",(eg2.MODEL,)).fetchone()[0]==2
    again=up.upgrade_process(path,CNJ,batch_size=1)
    assert again["status"]=="READY" and again["written"]==0 and again["summaries_written"]==0
    assert len(calls)==3


def test_interrupted_upgrade_never_publishes_partial_index(tmp_path,monkeypatch):
    path=_fixture(tmp_path)
    _fake(monkeypatch,fail_on=2)
    with pytest.raises(RuntimeError,match="Interrupted"):
        up.upgrade_process(path,CNJ,batch_size=1)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM page_embeddings WHERE model=?",(eg2.MODEL,)).fetchone()[0]==1
        assert not db.execute("SELECT 1 FROM vector_index_metadata WHERE model=?",(eg2.MODEL,)).fetchone()
    calls=_fake(monkeypatch)
    report=up.upgrade_process(path,CNJ,batch_size=1)
    assert report["status"]=="READY" and report["written"]==1
    assert len(calls)==2  # remaining page + summary; first page reused


def test_upgrade_rejects_incompatible_staging(tmp_path,monkeypatch):
    path=_fixture(tmp_path)
    _fake(monkeypatch)
    with sqlite3.connect(path) as db:
        db.execute("""INSERT INTO page_embeddings(page_id,document_id,process_id,page_number,
           model,backend,model_version,quantization,dim,vector_blob,content_hash,updated_at)
           VALUES ('doc:1','doc',?,1,?,?,?,?,?,?,?, 'now')""",
           (CNJ,eg2.MODEL,eg2.BACKEND_GPU,eg2.VERSION,eg2.QUANTIZATION,eg2.DIM,
            struct.pack("768f",*VECTOR),up._source_hash("Decisão favorável.")))
        db.commit()
    assert up.upgrade_process(path,CNJ)["status"]=="INCOMPATIBLE_INDEX"  # never mix GPU and CPU signatures


def test_vector_store_accepts_legacy_model_as_isolated_space(tmp_path):
    from core.retrieval.vector_store import IncompatibleEmbeddingSpaceError
    import pytest
    path=_fixture(tmp_path)
    store=VectorStore(path)
    store.save_embedding(
        "doc:2","doc",CNJ,2,VECTOR,
        model=eg2.MODEL,backend=eg2.BACKEND_CPU,
        model_version=eg2.VERSION,quantization=eg2.QUANTIZATION,
    )
    with pytest.raises(IncompatibleEmbeddingSpaceError):
        store.save_embedding(
            "doc:2","doc",CNJ,2,VECTOR,
            model=eg2.MODEL,backend=eg2.BACKEND_GPU,
            model_version=eg2.VERSION,quantization=eg2.QUANTIZATION,
        )
