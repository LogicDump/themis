from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import date, timedelta

import pytest

from core.documentos.deadline_calculation_store_v1 import (
    MIGRATION_VERSION,
    calculate_and_materialize,
    list_calculations,
    migrate_connection,
    persist_calculation,
)
from core.documentos.deadline_obligation_store_v1 import update_obligation_resolution
from core.documentos.deadline_policies_v1 import CourtCalendar
from core.documentos.domain_objects_v1 import SCHEMA as DOMAIN_SCHEMA
from core.documentos.legal_event_projection_v1 import LegalEventProjection
from core.documentos.publications_v1 import migrate_connection as migrate_publications
from core.test_deadline_obligation_v2 import database as obligation_database


def synthetic_calendar(start="2026-03-02", end="2026-03-12", non_business=()):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    values = []
    while first <= last:
        values.append(CourtCalendar("SYNTHETIC", "SYNTHETIC_COURT", "SYNTHETIC_UNIT",
            first.isoformat(), "HOLIDAY" if first.isoformat() in non_business else "BUSINESS_DAY", "SYNTHETIC_TEST_ONLY", "fixture://calendar",
            "2026-01-01", "fixture-v1"))
        first += timedelta(days=1)
    return tuple(values)


def setup_db(*, published_on=None, add_context=True):
    db = obligation_database()
    db.executescript(DOMAIN_SCHEMA)
    migrate_publications(db)
    migrate_connection(db)
    db.execute("""INSERT INTO publications(
      publication_id,process_id,provider,communication_id,certificate_code,tribunal,organ,
      publication_type,medium,available_on,published_on,publication_status,active,canceled_on,
      cancellation_reason,full_text,source_url,recipients_json,recipient_lawyers_json,payload_hash,
      provenance_json,created_at,updated_at
    ) VALUES('pub1','p1','DJEN_COMUNICA','comm1',NULL,'SYNTHETIC','SYNTHETIC','INTIMATION','D',
      '2026-03-02',?, 'ACTIVE',1,NULL,NULL,'fixture text','fixture://publication','[]','[]','synthetic','{}','t','t')""", (published_on,))
    db.execute("UPDATE process_events SET event_date='2026-03-02',date_precision='DATE' WHERE event_id='ev1'")
    db.execute("UPDATE deadline_obligations SET term_value=3,term_unit='DAYS',resolved_rule_id='JUDICIAL_EXPLICIT_TERM',review_required=0 WHERE obligation_id='ob1'")
    provenance = {"source_event_id": "ev1", "legal_context": {
        "legal_domain": "CIVIL", "base_regime": "CPC", "applicable_regimes": ["CPC"],
        "procedure_class": "SYNTHETIC", "jurisdiction": "SYNTHETIC"}}
    if not add_context:
        provenance.pop("legal_context")
    db.execute("UPDATE deadline_obligations SET provenance_json=? WHERE obligation_id='ob1'", (json.dumps(provenance),))
    db.commit()
    return db


def run(db, *, calendar_entries=None, **kwargs):
    return calculate_and_materialize(db, process_id="p1", obligation_id="ob1",
                                     calendar_entries=calendar_entries or synthetic_calendar(), **kwargs)


def test_migration_is_additive_idempotent_and_foreign_keys_hold():
    db = setup_db()
    first = migrate_connection(db)
    second = migrate_connection(db)
    assert first["migration_version"] == second["migration_version"] == MIGRATION_VERSION
    assert second["already_applied"] is True
    assert not db.execute("PRAGMA foreign_key_check").fetchall()
    assert db.execute("SELECT count(*) FROM deadline_obligations WHERE obligation_id='ob1'").fetchone()[0] == 1


def test_calculated_materializes_one_dated_deadline_and_projection():
    db = setup_db()
    out = run(db)
    assert out["status"] == "CALCULATED" and out["due_date"] == "2026-03-06"
    row = db.execute("SELECT due_at,date_precision,triggering_event FROM deadlines").fetchone()
    assert tuple(row) == ("2026-03-06", "DAY", "ev1")
    assert len(LegalEventProjection.project_deadlines(db, process_id="p1")) == 1
    assert LegalEventProjection.project_deadlines(db, process_id="p1")[0]["kind"] == "DEADLINE"
    assert all(row[0] != "DEADLINE" for row in db.execute("SELECT event_type FROM process_events"))


def test_reexecution_is_one_calculation_and_one_operational_projection():
    db = setup_db()
    first, second = run(db), run(db)
    assert first["calculation_id"] == second["calculation_id"]
    assert db.execute("SELECT count(*) FROM deadline_calculations").fetchone()[0] == 1
    assert db.execute("SELECT count(*) FROM deadlines").fetchone()[0] == 1


def test_new_communication_fact_reconciles_the_existing_projection_in_place():
    db = setup_db()
    first = run(db)
    db.execute("UPDATE publications SET published_on='2026-03-04' WHERE publication_id='pub1'")
    second = run(db)
    assert first["calculation_id"] != second["calculation_id"]
    assert db.execute("SELECT count(*) FROM deadline_calculations").fetchone()[0] == 2
    assert db.execute("SELECT count(*) FROM deadlines").fetchone()[0] == 1
    assert tuple(db.execute("SELECT due_at,status,confirmation_status FROM deadlines").fetchone()) == (
        "2026-03-07", "CANDIDATE", "PENDING")


def test_review_required_removes_previous_projection_but_keeps_calculation_history():
    db = setup_db()
    run(db)
    review = run(db, requires_personal_notice=True)
    assert review["status"] == "REVIEW_REQUIRED" and review["deadline_id"] is None
    assert db.execute("SELECT count(*) FROM deadlines").fetchone()[0] == 0
    stored = list_calculations(db, "p1", "ob1")
    assert len(stored) == 2
    assert {x["status"] for x in stored} == {"CALCULATED", "REVIEW_REQUIRED"}


def test_material_result_change_gets_new_calculation_identity_and_preserves_prior_version():
    db = setup_db()
    first = run(db)
    original = list_calculations(db, "p1", "ob1")[0]["calculation"]
    revised = dict(original)
    revised["status"] = "REVIEW_REQUIRED"
    revised["due_date"] = None
    revised["reason"] = {"code": "SUSPENSION_EXCEPTION_UNRESOLVED"}
    revised["applied_suspensions"] = [{"policy_id": "SYNTHETIC", "suspended": True}]
    second_id = persist_calculation(db, process_id="p1", obligation_id="ob1", result=revised)
    assert second_id != first["calculation_id"]
    stored = list_calculations(db, "p1", "ob1")
    assert len(stored) == 2
    assert {x["status"] for x in stored} == {"CALCULATED", "REVIEW_REQUIRED"}


def test_djen_available_observed_published_derived_without_mutating_publication():
    db = setup_db(published_on=None)
    result = run(db)
    calculation = list_calculations(db, "p1", "ob1")[0]["calculation"]
    dates = calculation["provenance"]["communication_date_epistemics"]
    assert dates["available_on"] == {"value": "2026-03-02", "epistemic_status": "OBSERVED", "source": "DJEN_API"}
    assert dates["published_on"]["epistemic_status"] == "DERIVED"
    assert dates["published_on"]["value"] == "2026-03-03"
    assert dates["counting_start"]["epistemic_status"] == "DERIVED"
    assert dates["counting_start"]["value"] == "2026-03-04"
    assert db.execute("SELECT published_on FROM publications WHERE publication_id='pub1'").fetchone()[0] is None
    assert result["due_date"] == "2026-03-06"


def test_djen_observed_published_date_is_used_and_remains_observed():
    db = setup_db(published_on="2026-03-04")
    result = run(db, calendar_entries=synthetic_calendar(non_business={"2026-03-07", "2026-03-08"}))
    calculation = list_calculations(db, "p1", "ob1")[0]["calculation"]
    dates = calculation["provenance"]["communication_date_epistemics"]
    assert result["due_date"] == "2026-03-09"
    assert dates["published_on"] == {"value": "2026-03-04", "epistemic_status": "OBSERVED", "source": "DJEN_API"}
    assert db.execute("SELECT published_on FROM publications WHERE publication_id='pub1'").fetchone()[0] == "2026-03-04"


def test_due_at_is_iso_day_only_and_trace_lists_counted_days():
    db = setup_db()
    run(db)
    row = db.execute("SELECT due_at FROM deadlines").fetchone()
    assert row[0] == "2026-03-06" and len(row[0]) == 10
    calc = list_calculations(db, "p1", "ob1")[0]["calculation"]
    assert calc["counted_days"] and calc["excluded_days"] and calc["calculation_trace"]
    assert "23:59:59" not in json.dumps(calc)


def test_legal_context_missing_is_persisted_unresolved_without_deadline():
    db = setup_db(add_context=False)
    result = run(db)
    assert result["status"] == "UNRESOLVED" and result["reason"]["code"] == "LEGAL_CONTEXT_MISSING"
    assert tuple(db.execute("SELECT status,due_date FROM deadline_calculations").fetchone()) == ("UNRESOLVED", None)
    assert db.execute("SELECT count(*) FROM deadlines").fetchone()[0] == 0


def test_obligation_cannot_be_calculated_from_another_process():
    db = setup_db()
    with pytest.raises(ValueError, match="não pertence"):
        calculate_and_materialize(db, process_id="p2", obligation_id="ob1", calendar_entries=synthetic_calendar())


def test_calculation_preserves_full_result_and_foreign_key_integrity():
    db = setup_db()
    run(db)
    stored = db.execute("SELECT calculation_json,provenance_json FROM deadline_calculations").fetchone()
    full = json.loads(stored["calculation_json"])
    assert {"counted_days", "excluded_days", "applied_suspensions", "calculation_trace", "reason", "calendar_provenance"} <= full.keys()
    assert not db.execute("PRAGMA foreign_key_check").fetchall()


def test_nested_resolution_pipeline_legal_context_is_accepted():
    db = setup_db()
    provenance = {"source_event_id": "ev1", "deadline_resolution_pipeline": {"legal_context": {
        "legal_domain": "CIVIL", "base_regime": "CPC", "applicable_regimes": ["CPC"],
        "procedure_class": "SYNTHETIC", "jurisdiction": "SYNTHETIC"}}}
    db.execute("UPDATE deadline_obligations SET provenance_json=? WHERE obligation_id='ob1'", (json.dumps(provenance),))
    db.commit()
    result = run(db)
    assert result["status"] == "CALCULATED"
    assert result["due_date"] == "2026-03-06"


def test_statutory_rule_supplies_term_when_instruction_has_no_explicit_number():
    db = setup_db()
    db.execute(
        "UPDATE deadline_obligations SET term_value=NULL,term_unit='UNSPECIFIED',"
        "resolved_rule_id='CPC_ART_437_P1_DOCUMENT_RESPONSE',recipient_role='DEFENDANT',review_required=0 "
        "WHERE obligation_id='ob1'"
    )
    db.commit()
    result = run(db, calendar_entries=synthetic_calendar(start="2026-03-02", end="2026-03-31"))
    assert result["status"] == "CALCULATED"
    calculation = list_calculations(db, "p1", "ob1")[-1]["calculation"]
    assert calculation["term_value"] == 15
    assert calculation["term_unit"] == "DAYS"


def test_explicit_hearing_trigger_is_not_replaced_by_djen_publication():
    db = setup_db()
    db.execute(
        "UPDATE deadline_obligations SET trigger_text='contados a partir da audiência',"
        "trigger_status='EXPLICIT',resolved_rule_id='CPC_ART_335_CONTESTATION',"
        "term_value=15,term_unit='BUSINESS_DAYS',counting_qualifier='BUSINESS_DAYS' "
        "WHERE obligation_id='ob1'"
    )
    db.commit()
    result = run(db, calendar_entries=synthetic_calendar(start="2026-03-02", end="2026-03-31"))
    assert result["status"] == "UNRESOLVED"
    assert result["reason"]["code"] == "HEARING_TRIGGER_NOT_CONFIRMED"
    assert result["deadline_id"] is None


def test_calculate_process_returns_fail_closed_status_summary():
    from core.documentos.deadline_calculation_store_v1 import calculate_process
    db = setup_db()
    result = calculate_process(db, process_id="p1", calendar_entries=synthetic_calendar())
    assert result["obligations"] == 1
    assert result["status_counts"] == {"CALCULATED": 1}
    assert result["results"][0]["due_date"] == "2026-03-06"
