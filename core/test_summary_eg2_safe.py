"""EG2 summary vectors: strict signature, legacy rejection, no generated text changes."""
import sqlite3
from core.retrieval import summary_embedding_store as store
from core.retrieval.embeddinggemma2_litert import MODEL, VERSION, QUANTIZATION, BACKEND_CPU

def _fixture(tmp_path):
    path = tmp_path / "fixture.db"
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE movements(movement_id TEXT PRIMARY KEY, title TEXT, payload_json TEXT);
        CREATE TABLE movement_summaries(summary_id TEXT PRIMARY KEY,movement_id TEXT,summary_version INTEGER,summary_text TEXT,source_hash TEXT);
        CREATE TABLE movement_summary_source_state(movement_id TEXT PRIMARY KEY, eligible INTEGER,source_hash TEXT);
        INSERT INTO movements VALUES('m1','Despacho','{}');
        INSERT INTO movement_summaries VALUES('s1','m1',1,'Intime-se o autor.','hash1');
        INSERT INTO movement_summary_source_state VALUES('m1',1,'hash1');
    """)
    db.commit()
    return path, db

def test_rebuild_replaces_legacy_vectors_without_changing_summary(monkeypatch,tmp_path):
    path, db = _fixture(tmp_path)
    store.migrate_connection(db)
    sig = dict(model=MODEL,model_version=VERSION,backend=BACKEND_CPU,quantization=QUANTIZATION,dim=768)
    monkeypatch.setattr(store,"active_signature",lambda backend=None: sig)
    monkeypatch.setattr(store,"embed_many",lambda texts,required_backend=None: ([[1.0]+[0.0]*767 for _ in texts],sig))
    db.execute("""INSERT INTO movement_summary_embeddings VALUES(
        'm1','s1','hash1',?,'embeddinggemma:300m','onnx','v1','int8',768,?,'now')""",
        (store.embedding_input_hash("Despacho","Intime-se o autor."),store.pack_vector([0.0]*768)))
    db.commit()
    assert store.current_vectors(db,[dict(store._current_rows(db)[0])],sig)==[None]
    db.close()
    result=store.rebuild_index(path)
    assert result["written"]==1
    with sqlite3.connect(path) as check:
        row=check.execute("SELECT model,backend,model_version,quantization,dim FROM movement_summary_embeddings").fetchone()
        assert row==(MODEL,BACKEND_CPU,VERSION,QUANTIZATION,768)
        summary=check.execute("SELECT summary_text FROM movement_summaries").fetchone()[0]
        assert summary=="Intime-se o autor."
