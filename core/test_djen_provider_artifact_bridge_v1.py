import sqlite3
from core.documentos.provider_artifacts_v1 import migrate_connection
from core.documentos.provider_marker_pipeline_v1 import persist_djen_provider_artifacts
from core.documentos.djen_provider_marker_v1 import extract_djen_provider_document_markers

PID = "1000045-87.2026.8.26.0450"
DOC = "a" * 64

def _structures():
    return [
        {"page": 1, "regions": [{"region_id": "r1", "text": (
            "Poder Judiciário Tribunal de Justiça do Estado de São Paulo "
            "Diário de Justiça Eletrônico Nacional de 03/09/2026 "
            "Certidão de publicação 77118 Intimação Número do processo:" + PID
            + " Teor da Comunicação Disponibilizado em:03/09/2026")}]},
        {"page": 2, "regions": [{"region_id": "r2", "text": (
            "https://comunicaapi.pje.jus.br/api/v1/comunicacao/AbC123/certidao "
            "Código da certidão: AbC123")}]},
    ]

def test_djen_certificate_continuation_is_one_artifact():
    projection = extract_djen_provider_document_markers(DOC, _structures(), target_process_id=PID)
    assert len(projection["provider_artifact_groups"]) == 1
    group = projection["provider_artifact_groups"][0]
    assert group["pages"] == [1, 2]
    assert group["markers"][0]["available_on"] == "03/09/2026"
    assert group["markers"][0]["issuing_body"]
    assert "event_at" not in group["markers"][0]
