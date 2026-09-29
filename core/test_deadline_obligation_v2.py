from __future__ import annotations

import sqlite3

import pytest

from core.documentos.deadline_instruction_store_v1 import create_from_event, migrate_connection as migrate_instructions
from core.documentos.deadline_obligation_store_v1 import migrate_connection, update_obligation_resolution
from core.documentos.process_event_store_v1 import migrate_connection as migrate_events


def database():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE processes(process_id TEXT PRIMARY KEY);
    INSERT INTO processes VALUES('p1');
    INSERT INTO processes VALUES('p2');
    CREATE TABLE movements(
      movement_id TEXT PRIMARY KEY, process_id TEXT, sequence INTEGER, movement_type TEXT,
      title TEXT, occurred_at TEXT, protocol TEXT, payload_json TEXT
    );
    CREATE TABLE process_participants(
      participant_id TEXT PRIMARY KEY, process_id TEXT NOT NULL
    );
    INSERT INTO process_participants VALUES('part_p1','p1');
    INSERT INTO process_participants VALUES('part_p2','p2');
    """)
    migrate_events(db)
    for event_id, process_id, source_id in (("ev1", "p1", "pub1"), ("ev2", "p2", "pub2")):
        db.execute(
            """INSERT INTO process_events(
              event_id,process_id,event_type,source_entity,source_id,date_precision,
              source_refs_json,provenance_json,created_at,updated_at
            ) VALUES(?,?,?,?,?,'UNKNOWN','[]','{}','t','t')""",
            (event_id, process_id, "PUBLICATION", "PUBLICATION", source_id),
        )
    migrate_instructions(db)
    instruction_id = create_from_event(
        db,
        process_id="p1",
        source_event_id="ev1",
        source_entity="PUBLICATION",
        source_id="pub1",
        source_excerpt="fixture",
        source_refs=[],
        source_hash="synthetic",
        action_text="Manifestar-se",
    )
    migrate_connection(db)
    db.execute(
        """INSERT INTO deadline_obligations(
          obligation_id,process_id,originating_instruction_id,supporting_instruction_ids_json,origin_role,
          action_text,recipient_text,term_value,term_unit,counting_qualifier,trigger_text,trigger_status,
          origin_movement_id,source_refs_json,source_hash,status,created_at,updated_at
        ) VALUES('ob1','p1',?,'[]','ORIGINATING_ORDER','Manifestar-se',NULL,NULL,'UNSPECIFIED',
                 NULL,NULL,'UNSPECIFIED',NULL,'[]','synthetic','AMBIGUOUS','t','t')""",
        (instruction_id,),
    )
    db.commit()
    return db


def test_legacy_movement_obligation_survives_nullable_origin_migration():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE processes(process_id TEXT PRIMARY KEY);
    INSERT INTO processes VALUES('p');
    CREATE TABLE movements(movement_id TEXT PRIMARY KEY, process_id TEXT);
    INSERT INTO movements VALUES('m','p');
    CREATE TABLE process_events(event_id TEXT PRIMARY KEY, process_id TEXT);
    INSERT INTO process_events VALUES('ev','p');
    CREATE TABLE deadline_instructions(instruction_id TEXT PRIMARY KEY);
    INSERT INTO deadline_instructions VALUES('i');
    CREATE TABLE deadline_obligations(
      obligation_id TEXT PRIMARY KEY,
      process_id TEXT NOT NULL,
      originating_instruction_id TEXT NOT NULL,
      supporting_instruction_ids_json TEXT NOT NULL,
      origin_role TEXT NOT NULL,
      action_text TEXT,
      recipient_text TEXT,
      term_value INTEGER,
      term_unit TEXT NOT NULL,
      counting_qualifier TEXT,
      trigger_text TEXT,
      trigger_status TEXT NOT NULL,
      origin_movement_id TEXT NOT NULL,
      source_refs_json TEXT NOT NULL,
      source_hash TEXT NOT NULL,
      status TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      FOREIGN KEY(originating_instruction_id) REFERENCES deadline_instructions(instruction_id) ON DELETE CASCADE,
      FOREIGN KEY(origin_movement_id) REFERENCES movements(movement_id) ON DELETE CASCADE
    );
    INSERT INTO deadline_obligations VALUES(
      'old','p','i','[]','ORIGINATING_ORDER','Ato',NULL,5,'DAYS',NULL,NULL,'UNSPECIFIED',
      'm','[]','h','ACTIVE','t','t'
    );
    """)
    migrate_connection(db)
    row = db.execute("SELECT origin_movement_id FROM deadline_obligations WHERE obligation_id='old'").fetchone()
    info = {item[1]: item for item in db.execute("PRAGMA table_info(deadline_obligations)")}
    assert row is not None and row["origin_movement_id"] == "m"
    assert info["origin_movement_id"][3] == 0
    assert not db.execute("PRAGMA foreign_key_check").fetchall()


def test_publication_obligation_does_not_require_fake_movement():
    db = database()
    info = {row[1]: row for row in db.execute("PRAGMA table_info(deadline_obligations)")}
    assert info["origin_movement_id"][3] == 0
    row = db.execute("SELECT origin_movement_id FROM deadline_obligations WHERE obligation_id='ob1'").fetchone()
    assert row["origin_movement_id"] is None
    assert not db.execute("PRAGMA foreign_key_check").fetchall()


def test_resolution_write_rejects_cross_process_participant_and_antecedent():
    db = database()
    with pytest.raises(ValueError):
        update_obligation_resolution(db, "ob1", recipient_participant_ids=["part_p2"])
    with pytest.raises(ValueError):
        update_obligation_resolution(db, "ob1", antecedent_source_event_id="ev2", recipient_participant_ids=["part_p1"])


def test_resolution_write_accepts_same_process_refs():
    db = database()
    update_obligation_resolution(
        db,
        "ob1",
        antecedent_source_event_id="ev1",
        recipient_role="RESPONDENT",
        recipient_participant_ids=["part_p1"],
        recipient_resolution_method="ANTECEDENT_RELATION",
        candidate_rule_ids=["R2", "R1", "R1"],
        model_preferred_rule_id="R2",
        resolved_rule_id="R1",
        review_required=False,
        provenance={"resolver": "fixture"},
    )
    row = db.execute(
        "SELECT antecedent_source_event_id,recipient_participant_ids_json,candidate_rule_ids_json,review_required "
        "FROM deadline_obligations WHERE obligation_id='ob1'"
    ).fetchone()
    assert row["antecedent_source_event_id"] == "ev1"
    assert row["recipient_participant_ids_json"] == '["part_p1"]'
    assert row["candidate_rule_ids_json"] == '["R1","R2"]'
    assert row["review_required"] == 0
