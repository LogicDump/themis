"""Autos remain searchable even when movement summaries omit evidence."""
import sqlite3
from core.retrieval.hybrid_retrieval import search_hybrid

def test_autos_lexical_retrieval_without_eg2_does_not_write(tmp_path):
    db_path=tmp_path/"process.db"
    with sqlite3.connect(db_path) as db:
        db.executescript("""
            CREATE TABLE documents(document_id TEXT,process_id TEXT,created_at TEXT);
            CREATE TABLE pages(page_id TEXT,document_id TEXT,page_number INTEGER,
              content TEXT,quality TEXT,process_folio INTEGER,page_class TEXT);
            INSERT INTO documents VALUES('doc1','synthetic','2026-01-01');
            INSERT INTO pages VALUES('doc1:1','doc1',1,
              'A prova da quitação consta do comprovante original.','OK',1,'text');
        """)
    before=db_path.read_bytes()
    result=search_hybrid("synthetic","quitação",db_path=db_path,vector_db_path=db_path)
    assert result and result[0]["page_id"]=="doc1:1"
    assert "quitação" in result[0]["excerpt"]
    assert result[0]["source_ref"]["document_id"]=="doc1"
    assert before==db_path.read_bytes()

def test_direct_page_not_excluded_by_summary_and_ownership_preserved(tmp_path):
    from core.retrieval.hierarchical_retrieval import search_hierarchical_evidence
    path=tmp_path/"case.db"
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE documents(document_id TEXT PRIMARY KEY,process_id TEXT,created_at TEXT);
        CREATE TABLE pages(page_id TEXT PRIMARY KEY,document_id TEXT,page_number INTEGER,content TEXT,
          quality TEXT,process_folio INTEGER,page_class TEXT);
        CREATE TABLE movements(movement_id TEXT PRIMARY KEY,process_id TEXT,sequence INTEGER,title TEXT);
        CREATE TABLE movement_pieces(movement_id TEXT,document_id TEXT,piece_order INTEGER,page_start INTEGER,page_end INTEGER);
        CREATE TABLE movement_summaries(summary_id TEXT,movement_id TEXT,summary_version INTEGER,summary_text TEXT,source_hash TEXT);
        CREATE TABLE movement_summary_source_state(movement_id TEXT,eligible INTEGER,source_hash TEXT);
        INSERT INTO documents VALUES('d1','synthetic','2026-01-01'),('d2','synthetic','2026-01-02');
        INSERT INTO pages VALUES('d1:1','d1',1,'Despacho ordinário.','OK',1,'text'),
                                ('d2:1','d2',1,'A quitação integral está comprovada pelo recibo.','OK',2,'text');
        INSERT INTO movements VALUES('m1','synthetic',1,'Despacho'),('m2','synthetic',2,'Recibo');
        INSERT INTO movement_pieces VALUES('m1','d1',1,1,1),('m2','d2',1,2,2);
        INSERT INTO movement_summaries VALUES('s1','m1',1,'Despacho ordinário.','h1');
        INSERT INTO movement_summary_source_state VALUES('m1',1,'h1');
        """)
    before=path.read_bytes()
    result=search_hierarchical_evidence("synthetic","quitação",top_k=1,db_path=path,vector_db_path=path)
    assert result and result[0]["page_id"]=="d2:1"
    assert result[0]["movement_id"]=="m2"
    assert result[0]["source_ref"]["document_id"]=="d2"
    assert result[0]["autos_navigation"]["page"]==1
    assert before==path.read_bytes()
