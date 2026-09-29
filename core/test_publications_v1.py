from __future__ import annotations

import sqlite3

from core.documentos.legal_event_projection_v1 import LegalEventProjection
from core.documentos.process_event_store_v1 import (
    list_process_events,
    materialize_process_events,
)
from core.documentos.publications_v1 import (
    list_publications,
    migrate_connection,
    sync_djen,
)

PROCESS_ID = "1234567-89.2026.8.26.0001"


def _db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute(
        "CREATE TABLE processes(process_id TEXT PRIMARY KEY, status TEXT)"
    )
    db.execute(
        "INSERT INTO processes(process_id,status) VALUES(?,?)",
        (PROCESS_ID, "READY"),
    )
    db.commit()
    return db


class FakeDjenClient:
    def communications(
        self,
        *,
        process_id: str,
        available_from: str,
        available_to: str,
        page: int = 1,
        page_size: int = 100,
    ):
        assert process_id == PROCESS_ID
        assert available_from == "2026-09-01"
        assert available_to == "2026-09-29"
        assert page == 1
        return {
            "payload": {
                "items": [
                    {
                        "id": 998877,
                        "hash": "cert-hash-1",
                        "numero_processo": PROCESS_ID,
                        "meio": "D",
                        "data_disponibilizacao": "2026-09-28",
                        "siglaTribunal": "TJXX",
                        "nomeOrgao": "Vara de Teste",
                        "tipoComunicacao": "Intimação",
                        "status": "P",
                        "ativo": True,
                        "data_cancelamento": None,
                        "motivo_cancelamento": None,
                        "texto": "Texto factual da publicação.",
                        "link": "https://example.invalid/publicacao/998877",
                        "destinatarios": [
                            {"nome": "PARTE TESTE", "polo": "D"}
                        ],
                        "destinatarioadvogados": [
                            {"advogado": {"nome": "ADVOGADO TESTE", "numero_oab": "12345"}}
                        ],
                    }
                ]
            },
            "headers": {"x-ratelimit-remaining": "99"},
            "request_url": "https://example.invalid/api/v1/comunicacao",
        }


def test_djen_sync_is_idempotent_and_projects_publication_event():
    db = _db()
    try:
        first = sync_djen(
            db,
            process_id=PROCESS_ID,
            available_from="2026-09-01",
            available_to="2026-09-29",
            client=FakeDjenClient(),
        )
        second = sync_djen(
            db,
            process_id=PROCESS_ID,
            available_from="2026-09-01",
            available_to="2026-09-29",
            client=FakeDjenClient(),
        )

        assert first["count"] == 1
        assert second["count"] == 1
        assert db.execute("SELECT count(*) FROM publications").fetchone()[0] == 1

        publications = list_publications(db, PROCESS_ID)
        assert len(publications) == 1
        publication = publications[0]
        assert publication["available_on"] == "2026-09-28"
        assert publication["published_on"] is None
        assert publication["publication_status"] == "P"
        assert publication["active"] == 1
        assert publication["canceled_on"] is None
        assert publication["recipients"][0]["nome"] == "PARTE TESTE"
        assert publication["recipient_lawyers"][0]["advogado"]["numero_oab"] == "12345"

        materialize_process_events(db, PROCESS_ID)
        events = list_process_events(
            db,
            PROCESS_ID,
            event_type="PUBLICATION",
        )
        assert len(events) == 1
        assert events[0]["event_subtype"] == "AVAILABLE"
        assert events[0]["event_date"] == "2026-09-28"
        assert events[0]["source_entity"] == "PUBLICATION"
        assert not db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='deadlines'"
        ).fetchone()
    finally:
        db.close()


def test_publications_migration_upgrades_legacy_table():
    db = _db()
    try:
        db.execute(
            """CREATE TABLE publications(
              publication_id TEXT PRIMARY KEY, process_id TEXT NOT NULL,
              provider TEXT NOT NULL, communication_id TEXT,
              certificate_code TEXT, tribunal TEXT, organ TEXT,
              publication_type TEXT, medium TEXT NOT NULL,
              available_on TEXT, published_on TEXT, full_text TEXT,
              source_url TEXT, payload_hash TEXT NOT NULL,
              provenance_json TEXT NOT NULL DEFAULT '{}',
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              UNIQUE(provider, communication_id)
            )"""
        )
        db.commit()
        result = migrate_connection(db)
        columns = {
            row[1] for row in db.execute("PRAGMA table_info(publications)")
        }
        assert result["migration_version"] == "publications-v1"
        assert "recipients_json" in columns
        assert "recipient_lawyers_json" in columns
        assert "publication_status" in columns
        assert "active" in columns
        assert "canceled_on" in columns
        assert "cancellation_reason" in columns
    finally:
        db.close()


def test_legal_event_projection_uses_djen_availability_when_publication_date_is_unknown():
    db = _db()
    try:
        sync_djen(
            db,
            process_id=PROCESS_ID,
            available_from="2026-09-01",
            available_to="2026-09-29",
            client=FakeDjenClient(),
        )
        events = LegalEventProjection.project_publications(db, process_id=PROCESS_ID)
        assert len(events) == 1
        event = events[0]
        assert event["published_at"] is None
        assert event["available_at"] == "2026-09-28"
        assert event["date_basis"] == "AVAILABLE"
        assert event["relevant_at"] == "2026-09-28"
        assert event["status"] == "P"
        assert event["active"] is True
        assert event["recipients"][0]["nome"] == "PARTE TESTE"
        assert event["recipient_lawyers"][0]["advogado"]["numero_oab"] == "12345"
    finally:
        db.close()
