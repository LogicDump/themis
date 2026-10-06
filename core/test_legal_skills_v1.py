import asyncio

import pytest

from core.legal_skills.actor_role_v1 import (
    build_actor_role_input,
    score_actor_role,
    validate_actor_role,
)
from core.legal_skills.fact_extractor_v1 import (
    build_fact_extractor_input,
    score_fact_extraction,
    validate_fact_extraction,
)
from core.legal_skills.claim_request_v1 import (
    build_claim_request_input,
    derive_source_actor,
    validate_claim_request,
)
from core.legal_skills.runner_v1 import run_comprehension_slice


def _source(text: str | None = None):
    return {
        "process_id": "proc",
        "movement_id": "mov1",
        "title": "Petição",
        "actor": "AUTORA",
        "occurred_at": "2026-10-06",
        "movement_type": "Petição",
        "pages": [{
            "document_id": "doc1",
            "pdf_page": 1,
            "content": text or (
                "A autora afirma que deixou o imóvel em março de 2023. "
                "A parte contrária deverá se manifestar. "
                "O juízo reconhece que a intimação ocorreu em 2 de abril de 2026."
            ),
        }],
    }


def _frame():
    return {
        "process_id": "proc",
        "participants": [
            {"participant_id": "p_claimant", "display_name": "Ana", "base_role": "CLAIMANT"},
            {"participant_id": "p_respondent", "display_name": "Bruno", "base_role": "RESPONDENT"},
        ],
        "representations": [],
    }


def _ref(quote: str):
    return {"document_id": "doc1", "pdf_page": 1, "quote": quote}


def _resolved_claimant():
    return {
        "actors": [{
            "mention": "A autora",
            "participant_id": "p_claimant",
            "resolution_status": "RESOLVED",
            "source_refs": [_ref("A autora")],
        }]
    }


def test_actor_input_uses_structured_process_frame():
    skill_input = build_actor_role_input(_source(), _frame())
    assert [item["participant_id"] for item in skill_input["participants"]] == ["p_claimant", "p_respondent"]


def test_actor_role_derives_identity_role_and_sufficiency():
    output = validate_actor_role(_resolved_claimant(), build_actor_role_input(_source(), _frame()))
    actor = output["actors"][0]
    assert actor["actor_id"] == "p_claimant"
    assert actor["actor_kind"] == "PROCESS_PARTICIPANT"
    assert actor["process_role"] == "CLAIMANT"
    assert output["context_sufficiency"] == "SUFFICIENT"


def test_actor_role_rejects_invented_participant():
    skill_input = build_actor_role_input(_source(), _frame())
    payload = _resolved_claimant()
    payload["actors"][0]["participant_id"] = "p_invented"
    with pytest.raises(ValueError, match="participant_id inexistente"):
        validate_actor_role(payload, skill_input)


def test_actor_role_rejects_canonical_name_not_present_as_mention():
    skill_input = build_actor_role_input(_source(), _frame())
    payload = _resolved_claimant()
    payload["actors"][0]["mention"] = "Ana"
    with pytest.raises(ValueError, match="mention deve existir"):
        validate_actor_role(payload, skill_input)


def test_actor_role_derives_ambiguous_diagnostic():
    payload = {
        "actors": [{
            "mention": "A parte contrária",
            "participant_id": None,
            "resolution_status": "AMBIGUOUS",
            "source_refs": [_ref("A parte contrária")],
        }]
    }
    output = validate_actor_role(payload, build_actor_role_input(_source(), _frame()))
    assert output["context_sufficiency"] == "AMBIGUOUS"
    assert output["actors"][0]["actor_kind"] == "UNRESOLVED"
    assert output["unresolved_points"][0]["code"] == "ACTOR_REFERENCE_AMBIGUOUS"


def test_actor_role_derives_court_actor():
    source = _source("O juízo reconhece que houve intimação.")
    output = validate_actor_role({
        "actors": [{
            "mention": "O juízo",
            "participant_id": None,
            "resolution_status": "RESOLVED",
            "source_refs": [_ref("O juízo")],
        }]
    }, build_actor_role_input(source, _frame()))
    assert output["actors"][0]["actor_id"] == "COURT"
    assert output["actors"][0]["process_role"] == "COURT"


def test_actor_score_flags_dangerous_false_resolution():
    expected = {
        "context_sufficiency": "AMBIGUOUS",
        "actors": [{"mention": "parte contrária", "participant_id": None, "resolution_status": "AMBIGUOUS"}],
    }
    actual = {
        "context_sufficiency": "SUFFICIENT",
        "actors": [{"mention": "parte contrária", "participant_id": "p_respondent", "resolution_status": "RESOLVED"}],
    }
    assert score_actor_role(expected, actual)["dangerous_false_resolution"] is True


def test_fact_extractor_accepts_allegation_without_upgrading_it():
    actor_input = build_actor_role_input(_source(), _frame())
    actor_output = validate_actor_role(_resolved_claimant(), actor_input)
    skill_input = build_fact_extractor_input(actor_input, actor_output)
    output = validate_fact_extraction({
        "context_sufficiency": "SUFFICIENT",
        "facts": [{
            "fact_id": "f1",
            "statement": "A autora deixou o imóvel em março de 2023.",
            "epistemic_status": "ALLEGED",
            "actor_id": "p_claimant",
            "temporal_text": "março de 2023",
            "source_refs": [_ref("A autora afirma que deixou o imóvel em março de 2023.")],
        }],
        "unresolved_points": [],
    }, skill_input)
    assert output["facts"][0]["epistemic_status"] == "ALLEGED"


def test_fact_extractor_rejects_proven_as_status():
    actor_input = build_actor_role_input(_source(), _frame())
    actor_output = validate_actor_role(_resolved_claimant(), actor_input)
    skill_input = build_fact_extractor_input(actor_input, actor_output)
    with pytest.raises(ValueError, match="epistemic_status inválido"):
        validate_fact_extraction({
            "context_sufficiency": "SUFFICIENT",
            "facts": [{
                "fact_id": "f1",
                "statement": "A autora deixou o imóvel.",
                "epistemic_status": "PROVEN",
                "actor_id": "p_claimant",
                "temporal_text": None,
                "source_refs": [_ref("A autora afirma que deixou o imóvel")],
            }],
            "unresolved_points": [],
        }, skill_input)


def test_fact_extractor_rejects_unresolved_actor_attribution():
    actor_input = build_actor_role_input(_source(), _frame())
    ambiguous = validate_actor_role({
        "actors": [{
            "mention": "A parte contrária",
            "participant_id": None,
            "resolution_status": "AMBIGUOUS",
            "source_refs": [_ref("A parte contrária")],
        }]
    }, actor_input)
    skill_input = build_fact_extractor_input(actor_input, ambiguous)
    unresolved_id = ambiguous["actors"][0]["actor_id"]
    with pytest.raises(ValueError, match="actor não resolvido"):
        validate_fact_extraction({
            "context_sufficiency": "SUFFICIENT",
            "facts": [{
                "fact_id": "f1",
                "statement": "A parte contrária deverá se manifestar.",
                "epistemic_status": "ALLEGED",
                "actor_id": unresolved_id,
                "temporal_text": None,
                "source_refs": [_ref("A parte contrária deverá se manifestar.")],
            }],
            "unresolved_points": [],
        }, skill_input)


def test_fact_extractor_allows_no_fact_for_pure_request():
    source = _source("Requer a restituição integral do valor.")
    actor_input = build_actor_role_input(source, _frame())
    skill_input = build_fact_extractor_input(
        actor_input,
        {"schema_version": "actor-role-resolver-v1", "context_sufficiency": "SUFFICIENT", "actors": [], "unresolved_points": []},
    )
    output = validate_fact_extraction({
        "context_sufficiency": "SUFFICIENT", "facts": [], "unresolved_points": []
    }, skill_input)
    assert output["facts"] == []


def test_claim_request_resolves_implicit_source_actor():
    source = _source("Requer a condenação do réu ao pagamento.")
    actor_input = build_actor_role_input(source, _frame())
    actor_output = {"schema_version": "actor-role-resolver-v1", "context_sufficiency": "SUFFICIENT", "actors": [], "unresolved_points": []}
    skill_input = build_claim_request_input(actor_input, actor_output)
    assert skill_input["source_actor"]["actor_id"] == "p_claimant"
    output = validate_claim_request({
        "legal_positions": [],
        "requests": [{
            "text": "condenação do réu ao pagamento",
            "actor_id": "p_claimant",
            "source_refs": [_ref("Requer a condenação do réu ao pagamento.")],
        }],
    }, skill_input)
    assert output["context_sufficiency"] == "SUFFICIENT"
    assert output["requests"][0]["actor_id"] == "p_claimant"


def test_claim_request_keeps_legal_position_out_of_fact_space():
    source = _source("Sustenta a incidência do art. 300 do CPC.")
    actor_input = build_actor_role_input(source, _frame())
    actor_output = {"schema_version": "actor-role-resolver-v1", "context_sufficiency": "SUFFICIENT", "actors": [], "unresolved_points": []}
    skill_input = build_claim_request_input(actor_input, actor_output)
    output = validate_claim_request({
        "legal_positions": [{
            "text": "incidência do art. 300 do CPC",
            "actor_id": "p_claimant",
            "source_refs": [_ref("Sustenta a incidência do art. 300 do CPC.")],
        }],
        "requests": [],
    }, skill_input)
    assert output["legal_positions"][0]["actor_id"] == "p_claimant"


def test_claim_request_rejects_unknown_actor():
    source = _source("Requer a procedência do pedido.")
    actor_input = build_actor_role_input(source, _frame())
    actor_output = {"schema_version": "actor-role-resolver-v1", "context_sufficiency": "SUFFICIENT", "actors": [], "unresolved_points": []}
    skill_input = build_claim_request_input(actor_input, actor_output)
    with pytest.raises(ValueError, match="actor_id inexistente"):
        validate_claim_request({
            "legal_positions": [],
            "requests": [{
                "text": "procedência do pedido",
                "actor_id": "p_invented",
                "source_refs": [_ref("Requer a procedência do pedido.")],
            }],
        }, skill_input)


def test_source_actor_is_ambiguous_when_role_has_multiple_participants():
    source = _source("Requer a produção de prova.")
    source["actor"] = "AUTORA"
    participants = [
        {"participant_id": "p1", "display_name": "Ana", "base_role": "CLAIMANT"},
        {"participant_id": "p2", "display_name": "Beatriz", "base_role": "CLAIMANT"},
    ]
    resolved = derive_source_actor(source, participants)
    assert resolved["status"] == "AMBIGUOUS"
    assert resolved["actor_id"] is None


def test_fact_score_flags_allegation_status_upgrade():
    expected = {
        "context_sufficiency": "SUFFICIENT",
        "facts": [{"statement": "Houve pagamento.", "epistemic_status": "ALLEGED", "actor_id": "p_claimant"}],
    }
    actual = {
        "context_sufficiency": "SUFFICIENT",
        "facts": [{"statement": "Houve pagamento.", "epistemic_status": "DOCUMENTED_EVENT", "actor_id": "p_claimant"}],
    }
    assert score_fact_extraction(expected, actual)["dangerous_status_upgrade"] is True


class _FakeLLM:
    def __init__(self, parsed_outputs):
        self._parsed_outputs = list(parsed_outputs)

    async def acomplete_structured(self, **kwargs):
        return {"parsed": self._parsed_outputs.pop(0), "provider": "fake", "model": "fake-model", "usage": {}}


def test_comprehension_slice_wires_actor_fact_and_claims():
    facts = {
        "context_sufficiency": "SUFFICIENT",
        "facts": [{
            "fact_id": "f1",
            "statement": "A autora deixou o imóvel em março de 2023.",
            "epistemic_status": "ALLEGED",
            "actor_id": "p_claimant",
            "temporal_text": "março de 2023",
            "source_refs": [_ref("A autora afirma que deixou o imóvel em março de 2023.")],
        }],
        "unresolved_points": [],
    }
    claims = {"legal_positions": [], "requests": []}
    result = asyncio.run(run_comprehension_slice(
        _FakeLLM([_resolved_claimant(), facts, claims]), _source(), _frame(), timeout_seconds=5
    ))
    assert result["actor_role"]["output"]["actors"][0]["participant_id"] == "p_claimant"
    assert result["facts"]["output"]["facts"][0]["epistemic_status"] == "ALLEGED"
    assert result["claims_requests"]["output"]["requests"] == []
