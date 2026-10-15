import json
import sqlite3

from core.documentos.process_movement_linker_v1 import audit_links, materialize_links, read_provider_timeline


def _db():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
        CREATE TABLE process_movements(
          movement_id TEXT PRIMARY KEY, process_id TEXT NOT NULL, movement_type TEXT NOT NULL,
          occurred_at TEXT, content TEXT, source_movement_id TEXT, movement_code TEXT,
          signer TEXT, movement_fingerprint TEXT, provenance_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE movements(
          movement_id TEXT PRIMARY KEY, process_id TEXT NOT NULL, sequence INTEGER NOT NULL,
          movement_type TEXT, title TEXT, actor TEXT, occurred_at TEXT, protocol TEXT,
          page_start INTEGER, page_end INTEGER, page_count INTEGER,
          source_hash TEXT NOT NULL, payload_json TEXT NOT NULL,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE provider_artifacts(
          provider_artifact_id TEXT PRIMARY KEY, process_id TEXT NOT NULL, movement_id TEXT,
          source_artifact_id TEXT, artifact_fingerprint TEXT, artifact_type TEXT, title TEXT,
          signer TEXT, source_origin TEXT NOT NULL, provenance_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE provider_artifact_pages(
          provider_artifact_id TEXT NOT NULL, canonical_page_id TEXT NOT NULL, position INTEGER NOT NULL,
          PRIMARY KEY(provider_artifact_id, canonical_page_id)
        );
        CREATE TABLE canonical_page_observations(
          canonical_page_id TEXT NOT NULL, document_id TEXT NOT NULL
        );
        """
    )
    return db


def _add_provider(db, mid, typ, date, content):
    db.execute(
        "INSERT INTO process_movements(movement_id,process_id,movement_type,occurred_at,content,provenance_json) VALUES(?,?,?,?,?,?)",
        (mid, "P", typ, date, content, "{}"),
    )


def _add_derived(db, mid, typ, date, protocol=None, document_id=None):
    payload = {"components": [{"document_id": document_id}]} if document_id else {}
    db.execute(
        """INSERT INTO movements(
             movement_id,process_id,sequence,movement_type,title,actor,occurred_at,protocol,
             page_start,page_end,page_count,source_hash,payload_json,created_at,updated_at
           ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (mid, "P", 1, typ, typ, None, date, protocol, 1, 1, 1, "h", json.dumps(payload), "t", "t"),
    )


def test_exact_protocol_has_priority():
    db = _db()
    _add_provider(db, "pm1", "Manifestação Juntada", "2026-09-02",
                  "Nº Protocolo: WPRC.26.70018598-0")
    _add_derived(db, "dm1", "Petição (Outras)", "02/09/2026 08:23", "WPRC26700185980")
    result = audit_links(db, "P")
    assert result["link_count"] == 1
    assert result["links"][0]["match_method"] == "EXACT_PROTOCOL"
    assert result["links"][0]["derived_movement_id"] == "dm1"


def test_unique_date_type_links_without_protocol():
    db = _db()
    _add_provider(db, "pm1", "Proferidas Outras Decisões não Especificadas", "2026-08-25", "Decisão")
    _add_derived(db, "dm1", "Decisão", "25/08/2026 14:16")
    result = audit_links(db, "P")
    assert result["link_count"] == 1
    assert result["links"][0]["match_method"] == "DATE_TYPE_UNIQUE"
    assert result["links"][0]["confidence"] == "HIGH"


def test_ambiguous_same_date_type_is_not_linked():
    db = _db()
    _add_provider(db, "pm1", "Certidão de Publicação Expedida", "2026-08-26", "a")
    _add_provider(db, "pm2", "Certidão de Publicação Expedida", "2026-08-26", "b")
    _add_derived(db, "dm1", "Certidão de Publicação", "26/08/2026 10:00")
    result = audit_links(db, "P")
    assert result["link_count"] == 0
    assert result["provider_unmatched"] == 2
    assert result["derived_unmatched"] == 1


def test_status_only_provider_movement_stays_unlinked():
    db = _db()
    _add_provider(db, "pm1", "Conclusos para Decisão", "2026-09-02", "Conclusos para Decisão")
    _add_derived(db, "dm1", "Decisão", "02/09/2026 10:00")
    result = audit_links(db, "P")
    assert result["link_count"] == 0


def test_materialize_links_attaches_provider_artifact():
    db = _db()
    _add_provider(db, "pm1", "Manifestação Sobre a Impugnação Juntada", "2026-09-02",
                  "Nº Protocolo: WPRC.26.70018598-0")
    _add_derived(db, "dm1", "Petição (Outras)", "02/09/2026 08:23", "WPRC26700185980", "doc1")
    db.execute(
        """INSERT INTO provider_artifacts(
             provider_artifact_id,process_id,movement_id,source_origin,provenance_json,created_at,updated_at
           ) VALUES(?,?,?,?,?,?,?)""",
        ("art1", "P", None, "pastadigital_esaj", "{}", "t", "t"),
    )
    db.execute("INSERT INTO provider_artifact_pages VALUES(?,?,?)", ("art1", "cp1", 1))
    db.execute("INSERT INTO canonical_page_observations VALUES(?,?)", ("cp1", "doc1"))
    result = materialize_links(db, "P")
    assert result["links_materialized"] == 1
    assert result["artifacts_linked"] == 1
    assert result["artifact_conflicts"] == []
    row = db.execute("SELECT movement_id FROM provider_artifacts WHERE provider_artifact_id='art1'").fetchone()
    assert row["movement_id"] == "pm1"
    link = db.execute("SELECT match_method,confidence FROM process_movement_links").fetchone()
    assert dict(link) == {"match_method": "EXACT_PROTOCOL", "confidence": "EXACT"}


def test_provider_timeline_keeps_provider_only_state_and_enriches_linked_document():
    db = _db()
    _add_provider(db, "pm_status", "Conclusos para Decisão", "2026-09-02", "Conclusos para Decisão")
    _add_provider(db, "pm_doc", "Manifestação Sobre a Impugnação Juntada", "2026-09-02",
                  "Nº Protocolo: WPRC.26.70018598-0")
    _add_derived(db, "dm1", "Petição (Outras)", "02/09/2026 08:23", "WPRC26700185980", "doc1")
    db.execute(
        """INSERT INTO provider_artifacts(
             provider_artifact_id,process_id,movement_id,source_origin,provenance_json,created_at,updated_at
           ) VALUES(?,?,?,?,?,?,?)""",
        ("art1", "P", None, "pastadigital_esaj", "{}", "t", "t"),
    )
    db.execute("INSERT INTO provider_artifact_pages VALUES(?,?,?)", ("art1", "cp1", 1))
    db.execute("INSERT INTO canonical_page_observations VALUES(?,?)", ("cp1", "doc1"))
    materialize_links(db, "P")

    timeline = read_provider_timeline(db, "P")
    assert len(timeline) == 2
    status = next(item for item in timeline if item["movement_id"] == "pm_status")
    linked = next(item for item in timeline if item["movement_id"] == "pm_doc")
    assert status["provider_only"] is True
    assert status["summary_movement_id"] is None
    assert status["components"] == []
    assert linked["provider_only"] is False
    assert linked["summary_movement_id"] == "dm1"
    assert linked["protocol"] == "WPRC26700185980"
    assert linked["components"][0]["document_id"] == "doc1"
