import json
from core.documentos.procedural_acts_v1 import _page_evidence

PID = "1000045-87.2026.8.26.0450"
FOREIGN = "0001901-50.2019.8.26.0450"

def record(process_refs, relationship, matched, timestamp="2026-04-28 10:47"):
    marker = {
        "provider": "ESAJ",
        "provider_identity": {"process_references": process_refs},
        "provenance_relationship": relationship,
        "target_process_match": matched,
        "event_at": timestamp,
        "signatory_literal": "Servidor",
        "bbox": [530.0, 5.0, 592.0, 835.0],
        "verification": {"code": "piece-code"},
    }
    return {
        "provider_artifact_id": "artifact1", "provenance_json": json.dumps({"marker": marker}),
        "process_id": PID, "signer": "Servidor", "artifact_type": "Petição",
        "title": "Documento", "source_origin": "ESAJ",
    }

def test_foreign_process_attestation_cannot_create_movement():
    evidence, reason = _page_evidence([record([FOREIGN], "embedded_source", False)])
    assert evidence is None
    assert reason == "NO_ARTIFACT_CONTEXT"

def test_embedded_mark_cannot_override_outer_mark():
    outer = record([PID], "outer_submission", True)
    foreign = record([FOREIGN], "embedded_source", False, timestamp="2024-01-01 09:00")
    evidence, reason = _page_evidence([foreign, outer])
    assert reason is None
    assert evidence["occurred_at"] == "28/04/2026 10:47"

def test_same_process_embedded_attestation_is_not_outer():
    assert _page_evidence([record([PID], "embedded_source", True)])[0] is None

def test_outer_requires_reference_to_current_process():
    assert _page_evidence([record([FOREIGN], "outer_submission", True)])[0] is None

def test_outer_release_for_current_process_is_accepted():
    evidence, reason = _page_evidence([record([PID], "outer_release", True)])
    assert reason is None
    assert evidence["occurred_at"] == "28/04/2026 10:47"
