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
from core.legal_skills.evidence_mapper_v1 import (
    build_evidence_mapper_input,
    score_evidence_mapping,
    validate_evidence_mapping,
)
from core.legal_skills.runner_v1 import run_comprehension_slice, run_evidence_mapper_skill


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
            "source_refs": [_ref("Requer a condenação do réu ao pagamento.")],
        }],
    }, skill_input)
    assert output["context_sufficiency"] == "SUFFICIENT"
    assert output["requests"][0]["actor_id"] == "p_claimant"
    assert output["requests"][0]["attribution_mode"] == "MOVEMENT_ACTOR"


def test_claim_request_keeps_legal_position_out_of_fact_space():
    source = _source("Sustenta a incidência do art. 300 do CPC.")
    actor_input = build_actor_role_input(source, _frame())
    actor_output = {"schema_version": "actor-role-resolver-v1", "context_sufficiency": "SUFFICIENT", "actors": [], "unresolved_points": []}
    skill_input = build_claim_request_input(actor_input, actor_output)
    output = validate_claim_request({
        "legal_positions": [{
            "text": "incidência do art. 300 do CPC",
            "source_refs": [_ref("Sustenta a incidência do art. 300 do CPC.")],
        }],
        "requests": [],
    }, skill_input)
    assert output["legal_positions"][0]["actor_id"] == "p_claimant"


def test_claim_request_model_cannot_supply_actor_id():
    source = _source("Requer a procedência do pedido.")
    actor_input = build_actor_role_input(source, _frame())
    actor_output = {"schema_version": "actor-role-resolver-v1", "context_sufficiency": "SUFFICIENT", "actors": [], "unresolved_points": []}
    skill_input = build_claim_request_input(actor_input, actor_output)
    with pytest.raises(ValueError, match="divergente do schema"):
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


def _fact_result_for_evidence(statement: str = "A autora efetuou o pagamento.", fact_id: str = "f1"):
    actor_input = build_actor_role_input(_source("A autora afirma que efetuou o pagamento."), _frame())
    actor_output = validate_actor_role(_resolved_claimant(), actor_input)
    fact_input = build_fact_extractor_input(actor_input, actor_output)
    fact_output = validate_fact_extraction({
        "context_sufficiency": "SUFFICIENT",
        "facts": [{
            "fact_id": fact_id,
            "statement": statement,
            "epistemic_status": "ALLEGED",
            "actor_id": "p_claimant",
            "temporal_text": None,
            "source_refs": [_ref("A autora afirma que efetuou o pagamento.")],
        }],
        "unresolved_points": [],
    }, fact_input)
    return fact_input, fact_output


def _evidence_source(content: str, *, source_id: str = "evsrc1", document_id: str = "evdoc1", kind: str = "DOCUMENT"):
    return [{
        "source_id": source_id,
        "movement_id": "evmov1",
        "document_id": document_id,
        "title": "Documento probatório",
        "source_kind": kind,
        "actor_id": None,
        "pages": [{"pdf_page": 1, "content": content}],
    }]


def _evidence_ref(quote: str, document_id: str = "evdoc1"):
    return {"document_id": document_id, "pdf_page": 1, "quote": quote}


def test_evidence_mapper_accepts_direct_support_without_calling_fact_proven():
    fact_input, fact_output = _fact_result_for_evidence()
    skill_input = build_evidence_mapper_input(
        fact_input,
        fact_output,
        _evidence_source("Comprovante bancário: transferência de R$ 1.000,00 realizada em 05/04/2026."),
    )
    output = validate_evidence_mapping({
        "evidence_items": [{
            "key": "e1",
            "source_id": "evsrc1",
            "kind": "DOCUMENT",
            "description": "comprovante bancário de transferência",
            "source_refs": [_evidence_ref("Comprovante bancário: transferência de R$ 1.000,00 realizada em 05/04/2026.")],
        }],
        "links": [{
            "fact_id": "f1",
            "evidence_key": "e1",
            "relation": "SUPPORTS",
            "directness": "DIRECT",
            "scope": "FULL",
            "limitations": [],
            "source_refs": [_evidence_ref("Comprovante bancário: transferência de R$ 1.000,00 realizada em 05/04/2026.")],
        }],
        "unresolved_points": [],
    }, skill_input)
    assert output["fact_states"][0]["evidence_state"] == "SUPPORT_PRESENT"
    assert "PROVEN" not in str(output)


def test_evidence_mapper_accepts_contradiction():
    fact_input, fact_output = _fact_result_for_evidence()
    skill_input = build_evidence_mapper_input(
        fact_input,
        fact_output,
        _evidence_source("Extrato da conta não registra qualquer transferência em 05/04/2026."),
    )
    output = validate_evidence_mapping({
        "evidence_items": [{
            "key": "e1",
            "source_id": "evsrc1",
            "kind": "DOCUMENT",
            "description": "extrato bancário sem registro da transferência alegada",
            "source_refs": [_evidence_ref("Extrato da conta não registra qualquer transferência em 05/04/2026.")],
        }],
        "links": [{
            "fact_id": "f1",
            "evidence_key": "e1",
            "relation": "CONTRADICTS",
            "directness": "DIRECT",
            "scope": "FULL",
            "limitations": [],
            "source_refs": [_evidence_ref("Extrato da conta não registra qualquer transferência em 05/04/2026.")],
        }],
        "unresolved_points": [],
    }, skill_input)
    assert output["fact_states"][0]["evidence_state"] == "CONTRADICTION_PRESENT"


def test_evidence_mapper_no_link_means_no_evidence_in_context_not_not_proven():
    fact_input, fact_output = _fact_result_for_evidence()
    skill_input = build_evidence_mapper_input(
        fact_input,
        fact_output,
        _evidence_source("Petição reiterando que houve pagamento."),
    )
    output = validate_evidence_mapping({
        "evidence_items": [],
        "links": [],
        "unresolved_points": [],
    }, skill_input)
    assert output["fact_states"] == [{"fact_id": "f1", "evidence_state": "NO_EVIDENCE_IN_CONTEXT"}]


def test_evidence_mapper_represents_unavailable_referenced_document():
    fact_input, fact_output = _fact_result_for_evidence()
    source_text = "A autora afirma que o documento de fl. 120 comprova o pagamento."
    skill_input = build_evidence_mapper_input(
        fact_input,
        fact_output,
        _evidence_source(source_text),
    )
    output = validate_evidence_mapping({
        "evidence_items": [],
        "links": [],
        "unresolved_points": [{
            "fact_id": "f1",
            "code": "REFERENCED_EVIDENCE_NOT_AVAILABLE",
            "reason": "O documento citado não está disponível no contexto fornecido.",
            "source_refs": [_evidence_ref(source_text)],
        }],
    }, skill_input)
    assert output["context_sufficiency"] == "INSUFFICIENT"
    assert output["fact_states"][0]["evidence_state"] == "NO_EVIDENCE_IN_CONTEXT"


def test_evidence_mapper_represents_unavailable_visual_asset():
    fact_input, fact_output = _fact_result_for_evidence()
    placeholder = "[VISUAL_ASSET: fotografia; conteúdo visual não extraído]"
    skill_input = build_evidence_mapper_input(
        fact_input,
        fact_output,
        _evidence_source(placeholder, kind="VISUAL_ASSET"),
    )
    output = validate_evidence_mapping({
        "evidence_items": [],
        "links": [],
        "unresolved_points": [{
            "fact_id": "f1",
            "code": "VISUAL_CONTENT_NOT_AVAILABLE",
            "reason": "O conteúdo visual não está disponível para análise nesta entrada.",
            "source_refs": [_evidence_ref(placeholder)],
        }],
    }, skill_input)
    assert output["context_sufficiency"] == "INSUFFICIENT"


def test_evidence_mapper_rejects_source_ref_from_wrong_source_id():
    fact_input, fact_output = _fact_result_for_evidence()
    sources = _evidence_source("Recibo assinado.", source_id="s1", document_id="d1")
    sources += _evidence_source("Extrato bancário.", source_id="s2", document_id="d2")
    skill_input = build_evidence_mapper_input(fact_input, fact_output, sources)
    with pytest.raises(ValueError, match="não pertencem ao source_id"):
        validate_evidence_mapping({
            "evidence_items": [{
                "key": "e1",
                "source_id": "s1",
                "kind": "DOCUMENT",
                "description": "recibo",
                "source_refs": [{"document_id": "d2", "pdf_page": 1, "quote": "Extrato bancário."}],
            }],
            "links": [],
            "unresolved_points": [],
        }, skill_input)


def test_evidence_mapper_rejects_unknown_fact_link():
    fact_input, fact_output = _fact_result_for_evidence()
    skill_input = build_evidence_mapper_input(
        fact_input,
        fact_output,
        _evidence_source("Recibo assinado."),
    )
    with pytest.raises(ValueError, match="fact_id inexistente"):
        validate_evidence_mapping({
            "evidence_items": [{
                "key": "e1",
                "source_id": "evsrc1",
                "kind": "DOCUMENT",
                "description": "recibo",
                "source_refs": [_evidence_ref("Recibo assinado.")],
            }],
            "links": [{
                "fact_id": "f99",
                "evidence_key": "e1",
                "relation": "SUPPORTS",
                "directness": "DIRECT",
                "scope": "FULL",
                "limitations": [],
                "source_refs": [_evidence_ref("Recibo assinado.")],
            }],
            "unresolved_points": [],
        }, skill_input)


def test_evidence_score_flags_dangerous_support_invention():
    expected = {
        "context_sufficiency": "SUFFICIENT",
        "evidence_items": [],
        "links": [],
        "fact_states": [{"fact_id": "f1", "evidence_state": "NO_EVIDENCE_IN_CONTEXT"}],
    }
    actual = {
        "context_sufficiency": "SUFFICIENT",
        "evidence_items": [{"evidence_id": "ev1", "source_id": "s1", "kind": "DOCUMENT", "description": "x"}],
        "links": [{
            "fact_id": "f1", "evidence_id": "ev1", "relation": "SUPPORTS",
            "directness": "DIRECT", "scope": "FULL",
        }],
        "fact_states": [{"fact_id": "f1", "evidence_state": "SUPPORT_PRESENT"}],
    }
    assert score_evidence_mapping(expected, actual)["dangerous_support_invention"] is True


def test_evidence_runner_validates_structured_output():
    fact_input, fact_output = _fact_result_for_evidence()
    evidence_sources = _evidence_source("Recibo de R$ 1.000,00 emitido em 05/04/2026.")
    fact_result = {"input": fact_input, "output": fact_output}
    payload = {
        "evidence_items": [{
            "key": "e1",
            "source_id": "evsrc1",
            "kind": "DOCUMENT",
            "description": "recibo de pagamento",
            "source_refs": [_evidence_ref("Recibo de R$ 1.000,00 emitido em 05/04/2026.")],
        }],
        "links": [{
            "fact_id": "f1",
            "evidence_key": "e1",
            "relation": "SUPPORTS",
            "directness": "DIRECT",
            "scope": "FULL",
            "limitations": [],
            "source_refs": [_evidence_ref("Recibo de R$ 1.000,00 emitido em 05/04/2026.")],
        }],
        "unresolved_points": [],
    }
    result = asyncio.run(run_evidence_mapper_skill(
        _FakeLLM([payload]), fact_result, evidence_sources, timeout_seconds=5
    ))
    assert result["output"]["fact_states"][0]["evidence_state"] == "SUPPORT_PRESENT"


def test_evidence_mapper_rejects_party_submission_as_underlying_evidence():
    fact_input, fact_output = _fact_result_for_evidence()
    skill_input = build_evidence_mapper_input(
        fact_input,
        fact_output,
        _evidence_source("A autora reitera que efetuou o pagamento.", kind="PARTY_SUBMISSION"),
    )
    with pytest.raises(ValueError, match="PARTY_SUBMISSION"):
        validate_evidence_mapping({
            "evidence_items": [{
                "key": "e1",
                "source_id": "evsrc1",
                "kind": "DOCUMENT",
                "description": "reiteração da autora",
                "source_refs": [_evidence_ref("A autora reitera que efetuou o pagamento.")],
            }],
            "links": [],
            "unresolved_points": [],
        }, skill_input)


def test_evidence_mapper_rejects_visual_placeholder_as_evidence_item():
    fact_input, fact_output = _fact_result_for_evidence()
    placeholder = "[VISUAL_ASSET: fotografia; conteúdo visual não extraído]"
    skill_input = build_evidence_mapper_input(
        fact_input,
        fact_output,
        _evidence_source(placeholder, kind="VISUAL_ASSET"),
    )
    with pytest.raises(ValueError, match="VISUAL_ASSET sem conteúdo analisável"):
        validate_evidence_mapping({
            "evidence_items": [{
                "key": "e1",
                "source_id": "evsrc1",
                "kind": "VISUAL_ASSET",
                "description": "fotografia",
                "source_refs": [_evidence_ref(placeholder)],
            }],
            "links": [],
            "unresolved_points": [],
        }, skill_input)


def test_evidence_mapper_rejects_self_serving_party_submission_as_admission():
    fact_input, fact_output = _fact_result_for_evidence()
    sources = _evidence_source(
        "A autora reitera que efetuou o pagamento.",
        kind="PARTY_SUBMISSION",
    )
    sources[0]["actor_id"] = "p_claimant"
    skill_input = build_evidence_mapper_input(fact_input, fact_output, sources)
    with pytest.raises(ValueError, match="self-serving PARTY_SUBMISSION"):
        validate_evidence_mapping({
            "evidence_items": [{
                "key": "e1",
                "source_id": "evsrc1",
                "kind": "ADMISSION",
                "description": "reiteração da autora",
                "source_refs": [_evidence_ref("A autora reitera que efetuou o pagamento.")],
            }],
            "links": [{
                "fact_id": "f1",
                "evidence_key": "e1",
                "relation": "SUPPORTS",
                "directness": "DIRECT",
                "scope": "FULL",
                "limitations": [],
                "source_refs": [_evidence_ref("A autora reitera que efetuou o pagamento.")],
            }],
            "unresolved_points": [],
        }, skill_input)


def test_evidence_mapper_forces_identity_unknown_support_to_inconclusive():
    fact_input, fact_output = _fact_result_for_evidence()
    text = "Registro bancário contém transferência de R$ 1.000,00, sem identificação do beneficiário."
    skill_input = build_evidence_mapper_input(
        fact_input,
        fact_output,
        _evidence_source(text),
    )
    output = validate_evidence_mapping({
        "evidence_items": [{
            "key": "e1",
            "source_id": "evsrc1",
            "kind": "DOCUMENT",
            "description": "registro bancário sem beneficiário identificado",
            "source_refs": [_evidence_ref(text)],
        }],
        "links": [{
            "fact_id": "f1",
            "evidence_key": "e1",
            "relation": "SUPPORTS",
            "directness": "INDIRECT",
            "scope": "PARTIAL",
            "limitations": ["AUTHENTICITY_DISPUTED"],
            "source_refs": [_evidence_ref(text)],
        }],
        "unresolved_points": [],
    }, skill_input)
    link = output["links"][0]
    assert link["relation"] == "INCONCLUSIVE"
    assert link["directness"] == "UNKNOWN"
    assert "IDENTITY_UNCLEAR" in link["limitations"]
    assert "AUTHENTICITY_DISPUTED" not in link["limitations"]
