"""EG2-only deadline guardrails: no EG1 heads and no invented role/due date."""
from core.documentos import deadline_specialist_v1 as specialist
from core.retrieval import embeddinggemma2_litert as eg2

def test_specialist_never_calls_legacy_encoder(monkeypatch):
    observations = (
        ("O autor requer prazo de 15 dias para juntar documentos.", False, "UNRESOLVED"),
        ("Intime-se a parte autora para apresentar documentos em 3 dias úteis.", True, "PLAINTIFF"),
        ("Intime-se a parte ré para contestar em 15 dias úteis.", True, "DEFENDANT"),
        ("Manifeste-se a parte contrária sobre os embargos de declaração.", True, "UNRESOLVED"),
        ("Certifico que os autos foram conclusos.", False, "UNRESOLVED"),
        ("Intime-se o perito para prestar esclarecimentos em 10 dias.", True, "EXPERT"),
    )
    for text, operative, role in observations:
        result = specialist.analyze_deadline_text(text)
        assert result.operative_instruction is operative
        assert result.recipient_role == role
        if operative and role == "UNRESOLVED":
            assert result.review_required

def test_unresolved_recipient_abstains():
    for text in ("Manifeste-se a parte contrária.", "Determino a apresentação de documentos em 5 dias."):
        result = specialist.analyze_deadline_text(text)
        assert result.recipient_role == "UNRESOLVED"
        assert result.review_required

def test_eg2_antecedent_query_and_documents_share_signature(monkeypatch):
    from core.documentos import deadline_resolution_pipeline_v1 as pipeline
    assert pipeline.embed_many is eg2.embed_many
    assert pipeline.embed_query is eg2.embed_query
    assert specialist.MODEL_VERSION == "deadline-specialist-evidence-rules-v2"
