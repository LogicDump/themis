"""EmbeddingGemma 2 isolated vector signature, safe chunking and device pinning."""
import math

import pytest

from core.retrieval import embeddinggemma2_litert as v2


class DummyEngine:
    def __init__(self):
        self.calls = []

    def compute_embedding(self, text):
        self.calls.append(text)
        class Output:
            embedding = [1.0] + [0.0] * 767
        return Output()


def test_prefixes_chunking_and_unit_vectors(monkeypatch):
    engine = DummyEngine()
    monkeypatch.setattr(v2, "_get_engine", lambda device=None: (engine, v2.BACKEND_GPU))
    vectors, signature = v2.embed_many(["Texto " * 330, "Intimação"], required_backend=v2.BACKEND_GPU)
    assert signature["model"] == v2.MODEL
    assert signature["backend"] == v2.BACKEND_GPU
    assert signature["model_version"] == v2.VERSION
    assert signature["dim"] == 768
    assert all(len(vec) == 768 and math.isclose(sum(x*x for x in vec), 1.0) for vec in vectors)
    assert len(engine.calls) >= 3
    assert all(c.startswith("task: search result | text: ") and len(c) <= len("task: search result | text: ") + v2.MAX_CHARS for c in engine.calls)
    q, query_signature = v2.embed_query("prazo para embargos", required_backend=v2.BACKEND_GPU)
    assert engine.calls[-1].startswith("task: search query | text: ")
    assert query_signature == signature
    assert len(q) == 768


def test_v2_backend_must_be_pinned_or_auto():
    assert v2._desired_backend("gpu") == [v2.BACKEND_GPU]
    assert v2._desired_backend("cpu") == [v2.BACKEND_CPU]
    assert v2._desired_backend("auto") == [v2.BACKEND_GPU, v2.BACKEND_CPU]
    assert v2._desired_backend(v2.BACKEND_GPU) == [v2.BACKEND_GPU]
    assert v2._desired_backend(v2.BACKEND_CPU) == [v2.BACKEND_CPU]
    with pytest.raises(ValueError):
        v2._desired_backend("invalid")


def test_v2_rejects_invalid_vector(monkeypatch):
    class Invalid:
        def compute_embedding(self, text):
            class Output:
                embedding = [float("nan")] * 768
            return Output()
    monkeypatch.setattr(v2, "_get_engine", lambda device=None: (Invalid(), v2.BACKEND_CPU))
    with pytest.raises(RuntimeError, match="vetor inválido"):
        v2.embed_many(["fato"])


def test_hybrid_chooses_v2_index_and_query(monkeypatch, tmp_path):
    import sqlite3
    from core.retrieval import hybrid_retrieval as hybrid
    from core.retrieval.vector_store import VectorStore, pack_vector
    pid = "1000045-87.2026.8.26.0450"
    path = tmp_path / "process.db"
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE documents(document_id TEXT,process_id TEXT,created_at TEXT);
            CREATE TABLE pages(page_id TEXT,document_id TEXT,page_number INTEGER,
                content TEXT,quality TEXT,process_folio INTEGER,page_class TEXT);
        """)
        db.execute("INSERT INTO documents VALUES(?,?,?)", ("doc1", pid, "2026-01-01"))
        db.execute("INSERT INTO pages VALUES(?,?,?,?,?,?,?)",
                   ("doc1:1", "doc1", 1, "intimação para pagamento em quinze dias", "OK", 1, "text"))
    vs = VectorStore(path)
    with vs.connect() as db:
        db.execute("""INSERT INTO page_embeddings VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                   ("doc1:1", "doc1", pid, 1, v2.MODEL, v2.BACKEND_GPU,
                    v2.VERSION, v2.QUANTIZATION, 768, pack_vector([1.0]+[0.0]*767), "hash", "2026-01-01"))
        db.execute("INSERT INTO vector_index_metadata VALUES(?,?,?,?,?,?,?,?)",
                   (pid, v2.MODEL, v2.BACKEND_GPU, v2.VERSION, v2.QUANTIZATION, 768, "2026-01-01", "2026-01-01"))
        db.commit()
    call_log = []
    def fake_query(query, required_backend=None):
        call_log.append(required_backend)
        return [1.0]+[0.0]*767, {
            "model": v2.MODEL, "backend": v2.BACKEND_GPU,
            "model_version": v2.VERSION, "quantization": v2.QUANTIZATION, "dim": 768,
        }
    monkeypatch.setattr(v2, "embed_query", fake_query)
    monkeypatch.setattr(hybrid, "ensure_process_embeddings",
                        lambda *args, **kwargs: pytest.fail("Legacy index must not be built"))
    result = hybrid.search_hybrid(pid, "intimação", db_path=path, vector_db_path=path)
    assert call_log == [v2.BACKEND_GPU]
    assert result and result[0]["page_id"] == "doc1:1"
