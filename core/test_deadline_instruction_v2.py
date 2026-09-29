from __future__ import annotations

import sqlite3

import pytest

from core.documentos.deadline_instruction_store_v1 import create_from_event, migrate_connection
from core.documentos.process_event_store_v1 import migrate_connection as migrate_events


def database():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("CREATE TABLE processes(process_id TEXT PRIMARY KEY); INSERT INTO processes VALUES('p'); CREATE TABLE movements(movement_id TEXT PRIMARY KEY,process_id TEXT,sequence INTEGER,movement_type TEXT,title TEXT,occurred_at TEXT,protocol TEXT,payload_json TEXT);")
    migrate_events(db)
    db.execute("INSERT INTO process_events(event_id,process_id,event_type,source_entity,source_id,date_precision,source_refs_json,provenance_json,created_at,updated_at) VALUES('ev_pub','p','PUBLICATION','PUBLICATION','pub','UNKNOWN','[]','{}','t','t')")
    migrate_connection(db)
    return db


def test_publication_origin_does_not_invent_movement_and_has_event_fk():
    db = database()
    instruction_id = create_from_event(db, process_id="p", source_event_id="ev_pub", source_entity="PUBLICATION", source_id="pub", source_excerpt="fixture", source_refs=[], source_hash="synthetic")
    item = db.execute("SELECT * FROM deadline_instructions WHERE instruction_id=?", (instruction_id,)).fetchone()
    assert item["movement_id"] is None
    assert item["source_entity"] == "PUBLICATION"
    assert not db.execute("PRAGMA foreign_key_check").fetchall()


def test_publication_instruction_survives_movement_materialization():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE processes(process_id TEXT PRIMARY KEY);
    INSERT INTO processes VALUES('p');
    CREATE TABLE movements(movement_id TEXT PRIMARY KEY,process_id TEXT,sequence INTEGER,movement_type TEXT,title TEXT,occurred_at TEXT,protocol TEXT,payload_json TEXT);
    CREATE TABLE publications(
      publication_id TEXT PRIMARY KEY, process_id TEXT NOT NULL, published_on TEXT, available_on TEXT,
      publication_type TEXT, full_text TEXT, communication_id TEXT, source_url TEXT, provenance_json TEXT NOT NULL
    );
    INSERT INTO publications VALUES('pub','p',NULL,'2026-01-02','Intimação','fixture','c',NULL,'{}');
    """)
    from core.documentos.process_event_store_v1 import materialize_process_events
    materialize_process_events(db, "p")
    event_id = db.execute("SELECT event_id FROM process_events WHERE source_entity='PUBLICATION' AND source_id='pub'").fetchone()[0]
    migrate_connection(db)
    instruction_id = create_from_event(
        db, process_id="p", source_event_id=event_id, source_entity="PUBLICATION", source_id="pub",
        source_excerpt="fixture", source_refs=[], source_hash="synthetic",
    )
    from core.documentos.deadline_instruction_store_v1 import materialize_process
    materialize_process(db, "p")
    row = db.execute("SELECT source_entity,movement_id FROM deadline_instructions WHERE instruction_id=?", (instruction_id,)).fetchone()
    assert row is not None and row["source_entity"] == "PUBLICATION" and row["movement_id"] is None


def test_invalid_event_anchor_is_rejected():
    db = database()
    with pytest.raises(ValueError):
        create_from_event(db, process_id="p", source_event_id="missing", source_entity="PUBLICATION", source_id="pub", source_excerpt="fixture", source_refs=[], source_hash="synthetic")


def test_existing_movement_instruction_survives_migration():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript("CREATE TABLE processes(process_id TEXT PRIMARY KEY); INSERT INTO processes VALUES('p'); CREATE TABLE movements(movement_id TEXT PRIMARY KEY,process_id TEXT,sequence INTEGER,movement_type TEXT,title TEXT,occurred_at TEXT,protocol TEXT,payload_json TEXT); INSERT INTO movements VALUES('m','p',1,'Despacho','Despacho',NULL,NULL,'{}');")
    db.executescript("""CREATE TABLE deadline_instructions(instruction_id TEXT PRIMARY KEY,process_id TEXT NOT NULL,movement_id TEXT NOT NULL,action_text TEXT,recipient_text TEXT,term_value INTEGER,term_unit TEXT NOT NULL,counting_qualifier TEXT,trigger_text TEXT,trigger_status TEXT NOT NULL,source_excerpt TEXT NOT NULL,source_refs_json TEXT NOT NULL,source_hash TEXT NOT NULL,extraction_method TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL); INSERT INTO deadline_instructions VALUES('i','p','m',NULL,NULL,NULL,'UNSPECIFIED',NULL,NULL,'UNSPECIFIED','fixture','[]','h','V1','AMBIGUOUS','t','t');""")
    migrate_events(db)
    migrate_connection(db)
    row = db.execute("SELECT * FROM deadline_instructions WHERE instruction_id='i'").fetchone()
    assert row["source_entity"] == "MOVEMENT" and row["movement_id"] == "m" and row["source_event_id"]
    assert not db.execute("PRAGMA foreign_key_check").fetchall()
