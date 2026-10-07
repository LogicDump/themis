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
from core.legal_skills.contradiction_detector_v1 import (
    build_contradiction_input,
    score_contradictions,
    validate_contradictions,
)
from core.legal_skills.evidence_gap_analyzer_v1 import (
    analyze_evidence_gaps,
    score_evidence_gaps,
)
from core.legal_skills.burden_of_proof_v1 import (
    build_burden_input,
    score_burden_allocations,
    validate_burden_allocations,
)
from core.legal_skills.legal_issue_mapper_v1 import (
    build_legal_issue_input,
    score_legal_issues,
    validate_legal_issues,
)
from core.legal_skills.legal_research_planner_v1 import (
    build_research_input,
    score_research_plan,
    validate_research_plan,
)
from core.legal_skills.jurisprudence_retriever_v1 import (
    build_jurisprudence_input,
    retrieve_jurisprudence,
    score_jurisprudence_retrieval,
)
from core.legal_skills.runner_v1 import (
    run_comprehension_slice,
    run_evidence_mapper_skill,
    run_contradiction_detector_skill,
    run_evidence_gap_analyzer_skill,
    run_legal_issue_mapper_skill,
    run_burden_of_proof_skill,
    run_legal_research_planner_skill,
    run_jurisprudence_retriever_skill,
)


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


def _contradiction_fact_output(*facts):
    return {
        "schema_version": "fact-extractor-v1",
        "context_sufficiency": "SUFFICIENT",
        "facts": list(facts),
        "unresolved_points": [],
    }


def _cd_fact(fact_id, statement, *, actor_id="p_claimant", temporal_text=None, quote=None, status="ALLEGED"):
    return {
        "fact_id": fact_id,
        "statement": statement,
        "epistemic_status": status,
        "actor_id": actor_id,
        "temporal_text": temporal_text,
        "source_refs": [{
            "document_id": f"doc_{fact_id}",
            "pdf_page": 1,
            "quote": quote or statement,
        }],
    }


def test_contradiction_detector_accepts_direct_fact_incompatibility():
    f1 = _cd_fact("f1", "A autora efetuou o pagamento em 05/04/2026.", temporal_text="05/04/2026")
    f2 = _cd_fact("f2", "A autora não efetuou o pagamento em 05/04/2026.", temporal_text="05/04/2026")
    skill_input = build_contradiction_input("proc", [_contradiction_fact_output(f1, f2)])
    output = validate_contradictions({
        "fact_pairs": [{
            "left_fact_id": "f1",
            "right_fact_id": "f2",
            "strength": "DIRECT",
            "dimensions": ["EXISTENCE"],
        }],
    }, skill_input)
    assert output["context_sufficiency"] == "SUFFICIENT"
    assert output["fact_contradictions"][0]["strength"] == "DIRECT"
    assert output["fact_contradictions"][0]["dimensions"] == ["EXISTENCE"]


def test_contradiction_detector_ignores_identical_fact_pair():
    f1 = _cd_fact("f1", "A autora reside em São Paulo.")
    f2 = _cd_fact("f2", "A autora reside em São Paulo.")
    skill_input = build_contradiction_input("proc", [_contradiction_fact_output(f1, f2)])
    output = validate_contradictions({
        "fact_pairs": [{
            "left_fact_id": "f1",
            "right_fact_id": "f2",
            "strength": "DIRECT",
            "dimensions": ["LOCATION"],
        }],
    }, skill_input)
    assert output["fact_contradictions"] == []


def test_contradiction_detector_potential_creates_unresolved_point():
    f1 = _cd_fact("f1", "Foi realizada uma transferência de R$ 1.000,00.")
    f2 = _cd_fact("f2", "Uma transferência de R$ 1.000,00 não foi realizada.")
    skill_input = build_contradiction_input("proc", [_contradiction_fact_output(f1, f2)])
    output = validate_contradictions({
        "fact_pairs": [{
            "left_fact_id": "f1",
            "right_fact_id": "f2",
            "strength": "POTENTIAL",
            "dimensions": ["ACTION_EVENT"],
        }],
    }, skill_input)
    assert output["context_sufficiency"] == "AMBIGUOUS"
    assert output["unresolved_points"][0]["code"] == "CONTRADICTION_REFERENT_AMBIGUOUS"


def test_contradiction_detector_projects_evidence_contradiction_deterministically():
    fact = _cd_fact("f1", "A autora efetuou o pagamento.")
    evidence = {
        "schema_version": "evidence-mapper-v1",
        "context_sufficiency": "SUFFICIENT",
        "evidence_items": [{
            "evidence_id": "ev1",
            "source_id": "s1",
            "kind": "DOCUMENT",
            "description": "extrato sem o pagamento",
            "source_refs": [{
                "document_id": "evdoc1",
                "pdf_page": 1,
                "quote": "Extrato não registra o pagamento.",
            }],
        }],
        "links": [{
            "fact_id": "f1",
            "evidence_id": "ev1",
            "relation": "CONTRADICTS",
            "directness": "DIRECT",
            "scope": "FULL",
            "limitations": [],
            "source_refs": [{
                "document_id": "evdoc1",
                "pdf_page": 1,
                "quote": "Extrato não registra o pagamento.",
            }],
        }],
        "fact_states": [{"fact_id": "f1", "evidence_state": "CONTRADICTION_PRESENT"}],
        "unresolved_points": [],
    }
    skill_input = build_contradiction_input("proc", [_contradiction_fact_output(fact)], [evidence])
    output = validate_contradictions({"fact_pairs": []}, skill_input)
    assert len(output["evidence_contradictions"]) == 1
    assert output["evidence_contradictions"][0]["fact_id"] == "f1"
    assert output["mixed_evidence_fact_ids"] == []


def test_contradiction_detector_tracks_mixed_evidence_without_asking_llm():
    fact = _cd_fact("f1", "A autora efetuou o pagamento.")
    evidence = {
        "schema_version": "evidence-mapper-v1",
        "context_sufficiency": "SUFFICIENT",
        "evidence_items": [
            {
                "evidence_id": "ev_support",
                "source_id": "s1",
                "kind": "DOCUMENT",
                "description": "recibo",
                "source_refs": [{"document_id": "d1", "pdf_page": 1, "quote": "Recibo de pagamento."}],
            },
            {
                "evidence_id": "ev_against",
                "source_id": "s2",
                "kind": "DOCUMENT",
                "description": "extrato",
                "source_refs": [{"document_id": "d2", "pdf_page": 1, "quote": "Extrato sem pagamento."}],
            },
        ],
        "links": [
            {
                "fact_id": "f1", "evidence_id": "ev_support", "relation": "SUPPORTS",
                "directness": "DIRECT", "scope": "FULL", "limitations": [],
                "source_refs": [{"document_id": "d1", "pdf_page": 1, "quote": "Recibo de pagamento."}],
            },
            {
                "fact_id": "f1", "evidence_id": "ev_against", "relation": "CONTRADICTS",
                "directness": "DIRECT", "scope": "FULL", "limitations": [],
                "source_refs": [{"document_id": "d2", "pdf_page": 1, "quote": "Extrato sem pagamento."}],
            },
        ],
        "fact_states": [{"fact_id": "f1", "evidence_state": "MIXED"}],
        "unresolved_points": [],
    }
    skill_input = build_contradiction_input("proc", [_contradiction_fact_output(fact)], [evidence])
    output = validate_contradictions({"fact_pairs": []}, skill_input)
    assert output["mixed_evidence_fact_ids"] == ["f1"]
    assert len(output["evidence_contradictions"]) == 1


def test_contradiction_score_flags_dangerous_direct_invention():
    expected = {
        "context_sufficiency": "SUFFICIENT",
        "fact_contradictions": [],
        "evidence_contradictions": [],
        "mixed_evidence_fact_ids": [],
    }
    actual = {
        "context_sufficiency": "SUFFICIENT",
        "fact_contradictions": [{
            "left_fact_id": "f1", "right_fact_id": "f2", "strength": "DIRECT",
        }],
        "evidence_contradictions": [],
        "mixed_evidence_fact_ids": [],
    }
    assert score_contradictions(expected, actual)["dangerous_direct_invention"] is True


def test_contradiction_runner_validates_structured_output():
    f1 = _cd_fact("f1", "A autora efetuou o pagamento.")
    f2 = _cd_fact("f2", "A autora não efetuou o pagamento.")
    result = asyncio.run(run_contradiction_detector_skill(
        _FakeLLM([{
            "fact_pairs": [{
                "left_fact_id": "f1",
                "right_fact_id": "f2",
                "strength": "DIRECT",
                "dimensions": ["EXISTENCE"],
            }],
        }]),
        "proc",
        [_contradiction_fact_output(f1, f2)],
        timeout_seconds=5,
    ))
    assert result["output"]["fact_contradictions"][0]["strength"] == "DIRECT"


def test_contradiction_detector_drops_direct_between_distinct_indefinite_events():
    f1 = _cd_fact("f1", "A autora efetuou um pagamento de R$ 500,00 em 05/04/2026.", temporal_text="05/04/2026")
    f2 = _cd_fact("f2", "A autora efetuou um pagamento de R$ 1.000,00 em 05/04/2026.", temporal_text="05/04/2026")
    skill_input = build_contradiction_input("proc", [_contradiction_fact_output(f1, f2)])
    output = validate_contradictions({
        "fact_pairs": [{
            "left_fact_id": "f1",
            "right_fact_id": "f2",
            "strength": "DIRECT",
            "dimensions": ["AMOUNT"],
        }],
    }, skill_input)
    assert output["fact_contradictions"] == []


def test_contradiction_detector_downgrades_indefinite_event_negation_to_potential():
    f1 = _cd_fact("f1", "Uma transferência de R$ 1.000,00 foi realizada.")
    f2 = _cd_fact("f2", "Uma transferência de R$ 1.000,00 não foi realizada.")
    skill_input = build_contradiction_input("proc", [_contradiction_fact_output(f1, f2)])
    output = validate_contradictions({
        "fact_pairs": [{
            "left_fact_id": "f1",
            "right_fact_id": "f2",
            "strength": "DIRECT",
            "dimensions": ["ACTION_EVENT"],
        }],
    }, skill_input)
    assert output["fact_contradictions"][0]["strength"] == "POTENTIAL"
    assert output["context_sufficiency"] == "AMBIGUOUS"


def test_contradiction_detector_drops_changeable_state_at_nonoverlapping_times():
    f1 = _cd_fact("f1", "A autora residia em São Paulo em janeiro de 2026.", temporal_text="janeiro de 2026")
    f2 = _cd_fact("f2", "A autora residia no Rio de Janeiro em junho de 2026.", temporal_text="junho de 2026")
    skill_input = build_contradiction_input("proc", [_contradiction_fact_output(f1, f2)])
    output = validate_contradictions({
        "fact_pairs": [{
            "left_fact_id": "f1",
            "right_fact_id": "f2",
            "strength": "DIRECT",
            "dimensions": ["LOCATION", "DATE_TIME"],
        }],
    }, skill_input)
    assert output["fact_contradictions"] == []


def _gap_evidence_output(fact_id, *, relation=None, scope="FULL", unresolved=None):
    items = []
    links = []
    if relation:
        items = [{
            "evidence_id": "ev1",
            "source_id": "s1",
            "kind": "DOCUMENT",
            "description": "documento",
            "source_refs": [{"document_id": "ed1", "pdf_page": 1, "quote": "Documento."}],
        }]
        links = [{
            "fact_id": fact_id,
            "evidence_id": "ev1",
            "relation": relation,
            "directness": "DIRECT" if relation != "INCONCLUSIVE" else "UNKNOWN",
            "scope": scope,
            "limitations": [],
            "source_refs": [{"document_id": "ed1", "pdf_page": 1, "quote": "Documento."}],
        }]
    return {
        "schema_version": "evidence-mapper-v1",
        "context_sufficiency": "INSUFFICIENT" if unresolved else "SUFFICIENT",
        "evidence_items": items,
        "links": links,
        "fact_states": [],
        "unresolved_points": unresolved or [],
    }


def test_gap_analyzer_no_evidence_in_context():
    fact = _cd_fact("f1", "A autora efetuou o pagamento.")
    output = analyze_evidence_gaps("proc", [_contradiction_fact_output(fact)])
    item = output["gap_items"][0]
    assert item["support_coverage"] == "NONE"
    assert item["gap_codes"] == ["NO_EVIDENCE_IN_CONTEXT"]
    assert output["context_sufficiency"] == "INSUFFICIENT"


def test_gap_analyzer_full_support_closes_gap():
    fact = _cd_fact("f1", "A autora efetuou o pagamento.")
    evidence = _gap_evidence_output("f1", relation="SUPPORTS", scope="FULL")
    output = analyze_evidence_gaps("proc", [_contradiction_fact_output(fact)], [evidence])
    item = output["gap_items"][0]
    assert item["support_coverage"] == "FULL"
    assert item["gap_open"] is False
    assert output["context_sufficiency"] == "SUFFICIENT"


def test_gap_analyzer_partial_support_remains_open():
    fact = _cd_fact("f1", "A autora efetuou o pagamento integral.")
    evidence = _gap_evidence_output("f1", relation="SUPPORTS", scope="PARTIAL")
    output = analyze_evidence_gaps("proc", [_contradiction_fact_output(fact)], [evidence])
    assert output["gap_items"][0]["gap_codes"] == ["PARTIAL_SUPPORT"]


def test_gap_analyzer_inconclusive_evidence():
    fact = _cd_fact("f1", "A autora efetuou o pagamento.")
    evidence = _gap_evidence_output("f1", relation="INCONCLUSIVE", scope="PARTIAL")
    output = analyze_evidence_gaps("proc", [_contradiction_fact_output(fact)], [evidence])
    item = output["gap_items"][0]
    assert "NO_SUPPORT_IN_CONTEXT" in item["gap_codes"]
    assert "INCONCLUSIVE_EVIDENCE" in item["gap_codes"]


def test_gap_analyzer_conflicting_evidence_is_ambiguous():
    fact = _cd_fact("f1", "A autora efetuou o pagamento.")
    evidence = {
        "schema_version": "evidence-mapper-v1",
        "context_sufficiency": "SUFFICIENT",
        "evidence_items": [
            {"evidence_id": "ev1", "source_id": "s1", "kind": "DOCUMENT", "description": "recibo", "source_refs": [{"document_id": "d1", "pdf_page": 1, "quote": "Recibo."}]},
            {"evidence_id": "ev2", "source_id": "s2", "kind": "DOCUMENT", "description": "extrato", "source_refs": [{"document_id": "d2", "pdf_page": 1, "quote": "Extrato."}]},
        ],
        "links": [
            {"fact_id": "f1", "evidence_id": "ev1", "relation": "SUPPORTS", "directness": "DIRECT", "scope": "FULL", "limitations": [], "source_refs": [{"document_id": "d1", "pdf_page": 1, "quote": "Recibo."}]},
            {"fact_id": "f1", "evidence_id": "ev2", "relation": "CONTRADICTS", "directness": "DIRECT", "scope": "FULL", "limitations": [], "source_refs": [{"document_id": "d2", "pdf_page": 1, "quote": "Extrato."}]},
        ],
        "fact_states": [],
        "unresolved_points": [],
    }
    output = analyze_evidence_gaps("proc", [_contradiction_fact_output(fact)], [evidence])
    assert output["context_sufficiency"] == "AMBIGUOUS"
    assert "CONFLICTING_EVIDENCE" in output["gap_items"][0]["gap_codes"]


def test_gap_analyzer_projects_missing_referenced_evidence():
    fact = _cd_fact("f1", "A autora efetuou o pagamento.")
    unresolved = [{
        "fact_id": "f1",
        "code": "REFERENCED_EVIDENCE_NOT_AVAILABLE",
        "reason": "Documento citado ausente.",
        "source_refs": [{"document_id": "d1", "pdf_page": 1, "quote": "Conforme documento de fl. 120."}],
    }]
    evidence = _gap_evidence_output("f1", unresolved=unresolved)
    output = analyze_evidence_gaps("proc", [_contradiction_fact_output(fact)], [evidence])
    assert "REFERENCED_EVIDENCE_NOT_AVAILABLE" in output["gap_items"][0]["gap_codes"]


def test_gap_analyzer_self_documented_event_without_external_evidence():
    fact = _cd_fact("f1", "A audiência ocorreu em 05/04/2026.", status="DOCUMENTED_EVENT")
    output = analyze_evidence_gaps("proc", [_contradiction_fact_output(fact)])
    item = output["gap_items"][0]
    assert item["support_coverage"] == "SELF_DOCUMENTED"
    assert item["gap_open"] is False


def test_gap_analyzer_projects_factual_contradiction():
    f1 = _cd_fact("f1", "A autora efetuou o pagamento.")
    f2 = _cd_fact("f2", "A autora não efetuou o pagamento.")
    contradiction = {
        "schema_version": "contradiction-detector-v1",
        "context_sufficiency": "SUFFICIENT",
        "fact_contradictions": [{
            "contradiction_id": "cd1",
            "kind": "FACT_FACT",
            "left_fact_id": "f1",
            "right_fact_id": "f2",
            "strength": "DIRECT",
            "dimensions": ["EXISTENCE"],
            "left_source_refs": f1["source_refs"],
            "right_source_refs": f2["source_refs"],
        }],
        "evidence_contradictions": [],
        "mixed_evidence_fact_ids": [],
        "unresolved_points": [],
    }
    output = analyze_evidence_gaps("proc", [_contradiction_fact_output(f1, f2)], [], [contradiction])
    assert output["context_sufficiency"] == "AMBIGUOUS"
    assert all("FACTUAL_CONTRADICTION_UNRESOLVED" in x["gap_codes"] for x in output["gap_items"])


def test_gap_analyzer_runner_is_deterministic_no_llm():
    fact = _cd_fact("f1", "A autora efetuou o pagamento.")
    result = run_evidence_gap_analyzer_skill("proc", [_contradiction_fact_output(fact)])
    assert result["trace"]["executor"] == "deterministic"
    assert result["trace"]["model"] is None


def test_gap_score_flags_dangerous_closed_gap():
    expected = {
        "context_sufficiency": "INSUFFICIENT",
        "open_gap_fact_ids": ["f1"],
        "gap_items": [{"fact_id": "f1", "support_coverage": "NONE", "gap_open": True, "gap_codes": ["NO_EVIDENCE_IN_CONTEXT"]}],
    }
    actual = {
        "context_sufficiency": "SUFFICIENT",
        "open_gap_fact_ids": [],
        "gap_items": [{"fact_id": "f1", "support_coverage": "FULL", "gap_open": False, "gap_codes": []}],
    }
    assert score_evidence_gaps(expected, actual)["dangerous_closed_gap"] is True


def _issue_claim_output(*, positions=None, requests=None):
    return {
        "schema_version": "claim-request-mapper-v1",
        "context_sufficiency": "SUFFICIENT",
        "source_actor": {},
        "legal_positions": positions or [],
        "requests": requests or [],
        "unresolved_points": [],
    }


def _issue_position(item_id, text, actor_id="p_claimant"):
    return {
        "item_id": item_id,
        "text": text,
        "actor_id": actor_id,
        "attribution_mode": "EXPLICIT_MENTION",
        "source_refs": [{"document_id": f"d_{item_id}", "pdf_page": 1, "quote": text}],
    }


def _issue_request(item_id, text, actor_id="p_claimant"):
    return {
        "item_id": item_id,
        "text": text,
        "actor_id": actor_id,
        "attribution_mode": "EXPLICIT_MENTION",
        "source_refs": [{"document_id": f"d_{item_id}", "pdf_page": 1, "quote": text}],
    }


def _issue_gap_output(fact_id, *, open_gap=False, codes=None):
    return {
        "schema_version": "evidence-gap-analyzer-v1",
        "context_sufficiency": "INSUFFICIENT" if open_gap else "SUFFICIENT",
        "gap_items": [{
            "gap_id": f"gap_{fact_id}",
            "fact_id": fact_id,
            "epistemic_status": "ALLEGED",
            "support_coverage": "NONE" if open_gap else "FULL",
            "gap_open": open_gap,
            "gap_codes": codes or ([] if not open_gap else ["NO_EVIDENCE_IN_CONTEXT"]),
            "supporting_evidence_ids": [],
            "contradictory_evidence_ids": [],
            "inconclusive_evidence_ids": [],
            "limitations": [],
            "source_refs": [],
        }],
        "open_gap_fact_ids": [fact_id] if open_gap else [],
    }


def test_legal_issue_mapper_accepts_factual_contradiction():
    f1 = _cd_fact("f1", "A autora efetuou o pagamento.")
    f2 = _cd_fact("f2", "A autora não efetuou o pagamento.")
    contradiction = {
        "schema_version": "contradiction-detector-v1",
        "context_sufficiency": "SUFFICIENT",
        "fact_contradictions": [{
            "contradiction_id": "cd1",
            "kind": "FACT_FACT",
            "left_fact_id": "f1",
            "right_fact_id": "f2",
            "strength": "DIRECT",
            "dimensions": ["EXISTENCE"],
            "left_source_refs": f1["source_refs"],
            "right_source_refs": f2["source_refs"],
        }],
        "evidence_contradictions": [],
        "mixed_evidence_fact_ids": [],
        "unresolved_points": [],
    }
    skill_input = build_legal_issue_input(
        "proc", [_contradiction_fact_output(f1, f2)], [], [contradiction], []
    )
    output = validate_legal_issues({
        "issues": [{
            "question": "Houve o pagamento alegado?",
            "kind": "FACTUAL",
            "fact_ids": ["f1", "f2"],
            "legal_position_ids": [],
            "request_ids": [],
        }],
    }, skill_input)
    assert output["issues"][0]["kind"] == "FACTUAL"
    assert output["issues"][0]["contradiction_ids"] == ["cd1"]


def test_legal_issue_mapper_discards_background_fact_without_live_controversy():
    f1 = _cd_fact("f1", "A ação foi ajuizada em 01/02/2026.")
    skill_input = build_legal_issue_input("proc", [_contradiction_fact_output(f1)])
    output = validate_legal_issues({
        "issues": [{
            "question": "Quando a ação foi ajuizada?",
            "kind": "FACTUAL",
            "fact_ids": ["f1"],
            "legal_position_ids": [],
            "request_ids": [],
        }],
    }, skill_input)
    assert output["issues"] == []


def test_legal_issue_mapper_accepts_legal_issue_from_position_and_request():
    position = _issue_position("lp1", "A pretensão está prescrita.", "p_respondent")
    request = _issue_request("rq1", "Requer o reconhecimento da prescrição.", "p_respondent")
    skill_input = build_legal_issue_input(
        "proc", [], [_issue_claim_output(positions=[position], requests=[request])]
    )
    output = validate_legal_issues({
        "issues": [{
            "question": "A pretensão está prescrita?",
            "kind": "LEGAL",
            "fact_ids": [],
            "legal_position_ids": ["lp1"],
            "request_ids": ["rq1"],
        }],
    }, skill_input)
    assert output["issues"][0]["legal_position_ids"] == ["lp1"]
    assert output["issues"][0]["request_ids"] == ["rq1"]


def test_legal_issue_mapper_accepts_mixed_issue():
    fact = _cd_fact("f1", "O requerido foi citado em 10/01/2026.", temporal_text="10/01/2026")
    position = _issue_position("lp1", "A contestação é tempestiva.", "p_respondent")
    request = _issue_request("rq1", "Requer o recebimento da contestação.", "p_respondent")
    skill_input = build_legal_issue_input(
        "proc",
        [_contradiction_fact_output(fact)],
        [_issue_claim_output(positions=[position], requests=[request])],
    )
    output = validate_legal_issues({
        "issues": [{
            "question": "A contestação foi apresentada tempestivamente?",
            "kind": "MIXED",
            "fact_ids": ["f1"],
            "legal_position_ids": ["lp1"],
            "request_ids": ["rq1"],
        }],
    }, skill_input)
    assert output["issues"][0]["kind"] == "MIXED"


def test_legal_issue_mapper_marks_underlying_gap_without_turning_gap_into_issue():
    fact = _cd_fact("f1", "A autora efetuou o pagamento.")
    request = _issue_request("rq1", "Requer a condenação do requerido à restituição.")
    skill_input = build_legal_issue_input(
        "proc",
        [_contradiction_fact_output(fact)],
        [_issue_claim_output(requests=[request])],
        [],
        [_issue_gap_output("f1", open_gap=True)],
    )
    output = validate_legal_issues({
        "issues": [{
            "question": "É devida a restituição do valor alegadamente pago?",
            "kind": "MIXED",
            "fact_ids": ["f1"],
            "legal_position_ids": [],
            "request_ids": ["rq1"],
        }],
    }, skill_input)
    assert output["context_sufficiency"] == "INSUFFICIENT"
    assert output["unresolved_points"][0]["code"] == "UNDERLYING_EVIDENCE_GAP"


def test_legal_issue_mapper_normalizes_mixed_without_fact_to_legal():
    position = _issue_position("lp1", "A pretensão está prescrita.")
    skill_input = build_legal_issue_input(
        "proc", [], [_issue_claim_output(positions=[position])]
    )
    output = validate_legal_issues({
        "issues": [{
            "question": "A pretensão está prescrita?",
            "kind": "MIXED",
            "fact_ids": [],
            "legal_position_ids": ["lp1"],
            "request_ids": [],
        }],
    }, skill_input)
    assert output["issues"][0]["kind"] == "LEGAL"


def test_legal_issue_score_detects_link_mismatch():
    expected = {
        "context_sufficiency": "SUFFICIENT",
        "issues": [{
            "kind": "LEGAL",
            "fact_ids": [],
            "legal_position_ids": ["lp1"],
            "request_ids": ["rq1"],
        }],
    }
    actual = {
        "context_sufficiency": "SUFFICIENT",
        "issues": [{
            "kind": "LEGAL",
            "fact_ids": [],
            "legal_position_ids": ["lp1"],
            "request_ids": [],
        }],
    }
    score = score_legal_issues(expected, actual)
    assert score["issue_precision"] == 0.0
    assert score["issue_recall"] == 0.0
    assert score["link_mismatch_count"] == 1


def test_legal_issue_runner_validates_structured_output():
    position = _issue_position("lp1", "A pretensão está prescrita.", "p_respondent")
    request = _issue_request("rq1", "Requer o reconhecimento da prescrição.", "p_respondent")
    result = asyncio.run(run_legal_issue_mapper_skill(
        _FakeLLM([{
            "issues": [{
                "question": "A pretensão está prescrita?",
                "kind": "LEGAL",
                "fact_ids": [],
                "legal_position_ids": ["lp1"],
                "request_ids": ["rq1"],
            }],
        }]),
        "proc",
        [],
        [_issue_claim_output(positions=[position], requests=[request])],
        timeout_seconds=5,
    ))
    assert result["output"]["issues"][0]["kind"] == "LEGAL"


def _burden_fact_output(*facts):
    return {
        "schema_version": "fact-extractor-v1",
        "context_sufficiency": "SUFFICIENT",
        "facts": list(facts),
        "unresolved_points": [],
    }


def _burden_issue_output(issue_id, question, fact_ids, kind="MIXED"):
    return {
        "schema_version": "legal-issue-mapper-v1",
        "context_sufficiency": "SUFFICIENT",
        "issues": [{
            "issue_id": issue_id,
            "question": question,
            "kind": kind,
            "fact_ids": list(fact_ids),
            "legal_position_ids": [],
            "request_ids": [],
            "actor_ids": [],
            "contradiction_ids": [],
            "evidence_gap_codes": [],
            "source_refs": [],
        }],
        "unresolved_points": [],
    }


def _burden_rule(
    rule_id="r1",
    statement="Incumbe ao autor provar o fato constitutivo de seu direito.",
    authority="CPC art. 373, I",
    regime="CPC",
    applicability="GENERAL",
    allowed_sides=None,
    allowed_types=None,
    conditions=None,
    precondition_status="SATISFIED",
):
    return {
        "rule_id": rule_id,
        "statement": statement,
        "authority": authority,
        "regime": regime,
        "applicability": applicability,
        "burden_side": (allowed_sides or ["CLAIMANT"])[0],
        "allocation_type": (allowed_types or ["DEFAULT"])[0],
        "reason_code": "DYNAMIC_RULE" if allowed_types == ["DYNAMIC"] else "CONSTITUTIVE_FACT",
        "precondition_status": precondition_status,
        "conditions": conditions or [],
    }


def test_burden_analyzer_accepts_supplied_default_rule():
    fact = _cd_fact("f1", "A autora efetuou o pagamento.")
    issue = _burden_issue_output("i1", "Houve pagamento?", ["f1"])
    skill_input = build_burden_input("proc", [issue], [_burden_fact_output(fact)], [_burden_rule()])
    output = validate_burden_allocations({
        "allocations": [{
            "issue_id": "i1",
            "fact_ids": ["f1"],
            "rule_id": "r1",
        }],
    }, skill_input)
    assert output["context_sufficiency"] == "SUFFICIENT"
    assert output["allocations"][0]["authority"] == "CPC art. 373, I"


def test_burden_analyzer_rejects_invented_rule():
    fact = _cd_fact("f1", "A autora efetuou o pagamento.")
    issue = _burden_issue_output("i1", "Houve pagamento?", ["f1"])
    skill_input = build_burden_input("proc", [issue], [_burden_fact_output(fact)], [_burden_rule()])
    with pytest.raises(ValueError, match="rule_id inexistente"):
        validate_burden_allocations({
            "allocations": [{
                "issue_id": "i1",
                "fact_ids": ["f1"],
                "rule_id": "invented",



            }],
        }, skill_input)


def test_burden_analyzer_rejects_unauthorized_shift():
    fact = _cd_fact("f1", "A autora efetuou o pagamento.")
    issue = _burden_issue_output("i1", "Houve pagamento?", ["f1"])
    skill_input = build_burden_input("proc", [issue], [_burden_fact_output(fact)], [_burden_rule()])
    with pytest.raises(ValueError, match="divergente do schema"):
        validate_burden_allocations({
            "allocations": [{
                "issue_id": "i1",
                "fact_ids": ["f1"],
                "rule_id": "r1",
                "allocation_type": "SHIFTED",
            }],
        }, skill_input)


def test_burden_analyzer_allows_explicit_dynamic_rule():
    fact = _cd_fact("f1", "A requerida detém exclusivamente os registros técnicos.")
    issue = _burden_issue_output("i1", "Quem possui acesso aos registros técnicos?", ["f1"])
    rule = _burden_rule(
        rule_id="dyn1",
        statement="Pode haver distribuição dinâmica quando a prova estiver em poder exclusivo da parte contrária.",
        authority="Regra fornecida para teste",
        applicability="CONDITIONAL",
        allowed_sides=["RESPONDENT"],
        allowed_types=["DYNAMIC"],
        conditions=["prova em poder exclusivo da requerida"],
    )
    skill_input = build_burden_input("proc", [issue], [_burden_fact_output(fact)], [rule])
    output = validate_burden_allocations({
        "allocations": [{
            "issue_id": "i1",
            "fact_ids": ["f1"],
            "rule_id": "dyn1",



        }],
    }, skill_input)
    assert output["allocations"][0]["allocation_type"] == "DYNAMIC"


def test_burden_analyzer_requires_unresolved_without_rule():
    fact = _cd_fact("f1", "A autora efetuou o pagamento.")
    issue = _burden_issue_output("i1", "Houve pagamento?", ["f1"])
    skill_input = build_burden_input("proc", [issue], [_burden_fact_output(fact)], [])
    output = validate_burden_allocations({"allocations": []}, skill_input)
    assert output["context_sufficiency"] == "INSUFFICIENT"
    assert output["unresolved_points"][0]["code"] == "RULE_NOT_SUPPLIED"


def test_burden_analyzer_does_not_require_pure_legal_issue_allocation():
    issue = _burden_issue_output("i1", "É aplicável a cláusula contratual?", [], kind="LEGAL")
    skill_input = build_burden_input("proc", [issue], [], [])
    output = validate_burden_allocations({"allocations": []}, skill_input)
    assert output["context_sufficiency"] == "SUFFICIENT"
    assert output["allocations"] == []


def test_burden_analyzer_fact_must_belong_to_issue():
    f1 = _cd_fact("f1", "A autora efetuou o pagamento.")
    f2 = _cd_fact("f2", "A autora entregou as chaves.")
    issue = _burden_issue_output("i1", "Houve pagamento?", ["f1"])
    skill_input = build_burden_input("proc", [issue], [_burden_fact_output(f1, f2)], [_burden_rule()])
    with pytest.raises(ValueError, match="não pertence à issue"):
        validate_burden_allocations({
            "allocations": [{
                "issue_id": "i1",
                "fact_ids": ["f2"],
                "rule_id": "r1",
            }],
        }, skill_input)


def test_burden_runner_validates_structured_output():
    fact = _cd_fact("f1", "A autora efetuou o pagamento.")
    issue = _burden_issue_output("i1", "Houve pagamento?", ["f1"])
    result = asyncio.run(run_burden_of_proof_skill(
        _FakeLLM([{
            "allocations": [{
                "issue_id": "i1",
                "fact_ids": ["f1"],
                "rule_id": "r1",
            }],
        }]),
        "proc",
        [issue],
        [_burden_fact_output(fact)],
        [_burden_rule()],
        timeout_seconds=5,
    ))
    assert result["output"]["allocations"][0]["burden_side"] == "CLAIMANT"

def test_burden_score_flags_dangerous_shift_invention():
    expected = {
        "context_sufficiency": "SUFFICIENT",
        "allocations": [{
            "issue_id": "i1",
            "fact_ids": ["f1"],
            "rule_id": "r1",
            "burden_side": "CLAIMANT",
            "allocation_type": "DEFAULT",
        }],
    }
    actual = {
        "context_sufficiency": "SUFFICIENT",
        "allocations": [{
            "issue_id": "i1",
            "fact_ids": ["f1"],
            "rule_id": "r1",
            "burden_side": "RESPONDENT",
            "allocation_type": "SHIFTED",
        }],
    }
    assert score_burden_allocations(expected, actual, {"burden_rules": [_burden_rule()]})["dangerous_shift_invention"] is True




@pytest.mark.parametrize("status", ["UNKNOWN", "UNSATISFIED", None])
def test_burden_conditional_open_status_is_omitted(status):
    rule = _burden_rule(applicability="CONDITIONAL", allowed_types=["DYNAMIC"])
    if status is None:
        rule.pop("precondition_status")
    else:
        rule["precondition_status"] = status
    inp = build_burden_input("proc", [_burden_issue_output("i1", "Houve pagamento?", ["f1"])],
                             [_burden_fact_output(_cd_fact("f1", "Pagamento alegado."))], [rule])
    actual = validate_burden_allocations({"allocations": [{"issue_id": "i1", "fact_ids": ["f1"], "rule_id": "r1"}]}, inp)
    assert actual == validate_burden_allocations({"allocations": []}, inp)
    assert actual["allocations"] == []
    assert actual["context_sufficiency"] == "INSUFFICIENT"


def test_burden_partial_coverage_and_overlap():
    inp = build_burden_input("proc", [_burden_issue_output("i1", "Houve pagamento e entrega?", ["f1", "f2"])],
        [_burden_fact_output(_cd_fact("f1", "Pagamento alegado."), _cd_fact("f2", "Entrega alegada."))], [_burden_rule()])
    selection = {"issue_id": "i1", "fact_ids": ["f1"], "rule_id": "r1"}
    actual = validate_burden_allocations({"allocations": [selection]}, inp)
    assert actual["unresolved_points"] == [{"issue_id": "i1", "fact_ids": ["f2"], "code": "RULE_NOT_SUPPLIED"}]
    with pytest.raises(ValueError, match="sobreposta"):
        validate_burden_allocations({"allocations": [selection, {**selection, "fact_ids": ["f1", "f2"]}]}, inp)


@pytest.mark.parametrize("field", ["burden_side", "allocation_type", "reason_code", "authority", "regime"])
def test_burden_rejects_model_derived_fields(field):
    inp = build_burden_input("proc", [_burden_issue_output("i1", "Houve pagamento?", ["f1"])],
        [_burden_fact_output(_cd_fact("f1", "Pagamento alegado."))], [_burden_rule()])
    with pytest.raises(ValueError, match="schema"):
        validate_burden_allocations({"allocations": [{"issue_id": "i1", "fact_ids": ["f1"], "rule_id": "r1", field: "FORGED"}]}, inp)


def test_burden_gold_minimal_protocol():
    import json
    from pathlib import Path
    cases = [json.loads(line) for line in (Path(__file__).resolve().parents[1] / "benchmarks/legal_skills_v1/cases.jsonl").read_text(encoding="utf-8").splitlines()]
    cases = [case for case in cases if case["skill"] == "BURDEN_OF_PROOF"]
    assert [case["id"] for case in cases] == [f"BP{i:02d}" for i in range(1, 11)]
    for case in cases:
        inp = build_burden_input("proc", case["issue_outputs"], case["fact_outputs"], case["burden_rules"])
        selections = [{field: item[field] for field in ("issue_id", "fact_ids", "rule_id")} for item in case["expected"]["allocations"]]
        actual = validate_burden_allocations({"allocations": selections}, inp)
        score = score_burden_allocations(case["expected"], actual, inp)
        assert score["allocation_precision"] == score["allocation_recall"] == 1
        assert score["sufficiency_match"]
        for item in actual["allocations"]:
            rule = next(rule for rule in inp["burden_rules"] if rule["rule_id"] == item["rule_id"])
            assert all(item[field] == rule[field] for field in ("burden_side", "allocation_type", "reason_code", "authority", "regime"))


def test_burden_runner_without_eligible_rules_skips_llm():
    result = asyncio.run(run_burden_of_proof_skill(None, "proc",
        [_burden_issue_output("i1", "Houve pagamento?", ["f1"])],
        [_burden_fact_output(_cd_fact("f1", "Pagamento alegado."))], []))
    assert result["trace"]["executor"] == "deterministic"
    assert result["output"]["context_sufficiency"] == "INSUFFICIENT"


@pytest.mark.parametrize("selection,metric", [
    ({"issue_id": "i1", "fact_ids": ["f1"], "rule_id": "invented"}, "rule_inventions"),
    ({"issue_id": "i1", "fact_ids": ["f1"], "rule_id": "r_const", "allocation_type": "SHIFTED"}, "unauthorized_shift_dynamic"),
])
def test_burden_benchmark_counts_rejected_dangerous_output(monkeypatch, selection, metric):
    import json
    from benchmarks.legal_skills_v1 import run_benchmark as bench
    case = next(json.loads(line) for line in bench.Path(bench.__file__).with_name("cases.jsonl").read_text(encoding="utf-8").splitlines() if json.loads(line)["id"] == "BP01")
    monkeypatch.setattr(bench, "call_ollama", lambda *args: (json.dumps({"allocations": [selection]}), {}))
    result = bench.run_case(case, "test")
    assert result["error"] is not None
    assert bench.summarize([result])["BURDEN_OF_PROOF"][metric] == 1


def test_burden_supplied_non_gold_rule_is_not_invented():
    rule = _burden_rule(rule_id="alternative")
    actual = {"allocations": [{"issue_id": "i1", "fact_ids": ["f1"], "rule_id": "alternative", "burden_side": "CLAIMANT", "allocation_type": "DEFAULT"}]}
    assert not score_burden_allocations({"allocations": []}, actual, {"burden_rules": [rule]})["dangerous_invented_rule"]


def _research_issue_output(issue_id, question, kind="LEGAL"):
    return {
        "schema_version": "legal-issue-mapper-v1",
        "context_sufficiency": "SUFFICIENT",
        "issues": [{
            "issue_id": issue_id,
            "question": question,
            "kind": kind,
            "fact_ids": [],
            "legal_position_ids": ["lp1"] if kind != "FACTUAL" else [],
            "request_ids": ["rq1"] if kind != "FACTUAL" else [],
            "actor_ids": [],
            "contradiction_ids": [],
            "evidence_gap_codes": [],
            "source_refs": [],
        }],
        "unresolved_points": [],
    }


def test_research_planner_derives_required_objectives():
    skill_input = build_research_input(
        "proc",
        [
            _research_issue_output("i1", "Qual regra rege a rescisão?", "LEGAL"),
            _research_issue_output("i2", "A audiência ocorreu?", "FACTUAL"),
            _research_issue_output("i3", "A manifestação é tempestiva?", "PROCEDURAL"),
        ],
    )
    required = {(x["issue_id"], x["objective"]) for x in skill_input["required_queries"]}
    assert required == {
        ("i1", "CONTROLLING_RULE"),
        ("i1", "PRECEDENT_LANDSCAPE"),
        ("i3", "PROCEDURAL_RULE"),
        ("i3", "PRECEDENT_LANDSCAPE"),
    }


def test_research_planner_accepts_exact_required_queries():
    skill_input = build_research_input(
        "proc",
        [_research_issue_output("i1", "Qual regra rege a rescisão contratual?", "LEGAL")],
        jurisdiction="BR",
        court_context="TJSP",
    )
    output = validate_research_plan({
        "queries": [
            {
                "issue_id": "i1",
                "objective": "CONTROLLING_RULE",
                "query_text": "rescisão contratual requisitos legais efeitos",
            },
            {
                "issue_id": "i1",
                "objective": "PRECEDENT_LANDSCAPE",
                "query_text": "jurisprudência critérios e limites da rescisão contratual",
            },
        ],
    }, skill_input)
    assert output["context_sufficiency"] == "SUFFICIENT"
    assert all(x["jurisdiction"] == "BR" for x in output["queries"])
    assert all(x["court_context"] == "TJSP" for x in output["queries"])


def test_research_planner_marks_missing_query_unresolved():
    skill_input = build_research_input(
        "proc",
        [_research_issue_output("i1", "Qual regra rege a rescisão contratual?", "LEGAL")],
    )
    output = validate_research_plan({
        "queries": [{
            "issue_id": "i1",
            "objective": "CONTROLLING_RULE",
            "query_text": "rescisão contratual requisitos legais",
        }],
    }, skill_input)
    assert output["context_sufficiency"] == "INSUFFICIENT"
    assert output["unresolved_points"][0]["objective"] == "PRECEDENT_LANDSCAPE"


def test_research_planner_rejects_unsupplied_specific_authority():
    skill_input = build_research_input(
        "proc",
        [_research_issue_output("i1", "Quais requisitos da tutela provisória?", "LEGAL")],
    )
    with pytest.raises(ValueError, match="inventa autoridade específica"):
        validate_research_plan({
            "queries": [
                {"issue_id": "i1", "objective": "CONTROLLING_RULE", "query_text": "art. 300 CPC tutela provisória"},
                {"issue_id": "i1", "objective": "PRECEDENT_LANDSCAPE", "query_text": "jurisprudência tutela provisória requisitos"},
            ],
        }, skill_input)


def test_research_planner_allows_known_authority_from_burden():
    issue = _research_issue_output("i1", "Como se distribui o ônus da prova?", "LEGAL")
    burden = {
        "schema_version": "burden-of-proof-analyzer-v1",
        "context_sufficiency": "SUFFICIENT",
        "allocations": [{
            "allocation_id": "b1",
            "issue_id": "i1",
            "fact_ids": ["f1"],
            "rule_id": "r1",
            "burden_side": "CLAIMANT",
            "allocation_type": "DEFAULT",
            "reason_code": "CONSTITUTIVE_FACT",
            "authority": "CPC art. 373, I",
            "regime": "CPC",
        }],
        "unresolved_points": [],
    }
    skill_input = build_research_input("proc", [issue], [burden])
    output = validate_research_plan({
        "queries": [
            {"issue_id": "i1", "objective": "CONTROLLING_RULE", "query_text": "CPC art. 373, I fato constitutivo ônus da prova"},
            {"issue_id": "i1", "objective": "PRECEDENT_LANDSCAPE", "query_text": "jurisprudência distribuição do ônus da prova fato constitutivo"},
        ],
    }, skill_input)
    assert output["context_sufficiency"] == "SUFFICIENT"


def test_research_planner_rejects_unrequested_objective():
    skill_input = build_research_input(
        "proc",
        [_research_issue_output("i1", "Qual regra rege a rescisão?", "LEGAL")],
    )
    with pytest.raises(ValueError, match="não solicitada"):
        validate_research_plan({
            "queries": [{
                "issue_id": "i1",
                "objective": "PROCEDURAL_RULE",
                "query_text": "rescisão contratual procedimento",
            }],
        }, skill_input)


def test_research_score_flags_authority_invention():
    expected = {
        "context_sufficiency": "SUFFICIENT",
        "known_authorities": [],
        "queries": [
            {"issue_id": "i1", "objective": "CONTROLLING_RULE"},
            {"issue_id": "i1", "objective": "PRECEDENT_LANDSCAPE"},
        ],
    }
    actual = {
        "context_sufficiency": "SUFFICIENT",
        "queries": [
            {"issue_id": "i1", "objective": "CONTROLLING_RULE", "query_text": "art. 300 CPC tutela provisória"},
            {"issue_id": "i1", "objective": "PRECEDENT_LANDSCAPE", "query_text": "jurisprudência tutela provisória"},
        ],
    }
    assert score_research_plan(expected, actual)["dangerous_authority_invention"] is True


def test_research_runner_validates_structured_output():
    issue = _research_issue_output("i1", "Qual regra rege a rescisão contratual?", "LEGAL")
    result = asyncio.run(run_legal_research_planner_skill(
        _FakeLLM([{
            "queries": [
                {"issue_id": "i1", "objective": "CONTROLLING_RULE", "query_text": "rescisão contratual requisitos legais efeitos"},
                {"issue_id": "i1", "objective": "PRECEDENT_LANDSCAPE", "query_text": "jurisprudência critérios e limites da rescisão contratual"},
            ],
        }]),
        "proc",
        [issue],
        timeout_seconds=5,
    ))
    assert result["output"]["context_sufficiency"] == "SUFFICIENT"


def _jurisprudence_research_output(*queries):
    return {
        "schema_version": "legal-research-planner-v1",
        "context_sufficiency": "SUFFICIENT",
        "queries": list(queries),
        "unresolved_points": [],
    }


def _jurisprudence_query(query_id="q1", source_types=None):
    return {
        "query_id": query_id,
        "issue_id": "i1",
        "objective": "PRECEDENT_LANDSCAPE",
        "query_text": "jurisprudência critérios e limites da rescisão contratual",
        "source_types": source_types or ["BINDING_AUTHORITY", "JURISPRUDENCE"],
        "jurisdiction": "BR",
        "court_context": "TJSP",
    }


def _provider_hit(
    *,
    result_id="r1",
    identifier="0001234-56.2025.8.26.0000",
    court="TJSP",
    excerpt="Ementa oficial do julgado.",
    source_type="JURISPRUDENCE",
    rank=1,
):
    return {
        "provider_result_id": result_id,
        "source_type": source_type,
        "court": court,
        "judging_body": "1ª Câmara de Direito Privado",
        "identifier": identifier,
        "date": "2026-04-10",
        "date_kind": "JUDGMENT",
        "excerpt": excerpt,
        "source_url": "https://example.invalid/acordao/" + result_id,
        "document_ref": None,
        "rank": rank,
        "score": None,
    }


def _provider_response(query_id="q1", *, provider="FAKE", results=None, status="OK", error_code=None):
    return {
        "query_id": query_id,
        "provider": provider,
        "status": status,
        "retrieved_at": "2026-10-07T01:00:00Z",
        "results": results or [],
        "error_code": error_code,
    }


def test_jurisprudence_input_keeps_only_judicial_sources():
    output = build_jurisprudence_input([
        _jurisprudence_research_output(
            _jurisprudence_query("q1"),
            _jurisprudence_query("q2", ["LEGISLATION"]),
        )
    ])
    assert [item["query_id"] for item in output["queries"]] == ["q1"]
    assert output["queries"][0]["allowed_source_types"] == ["BINDING_AUTHORITY", "JURISPRUDENCE"]


def test_jurisprudence_retriever_accepts_provenanced_candidate():
    skill_input = build_jurisprudence_input([
        _jurisprudence_research_output(_jurisprudence_query())
    ])
    output = retrieve_jurisprudence(
        skill_input,
        [_provider_response(results=[_provider_hit()])],
    )
    assert output["context_sufficiency"] == "SUFFICIENT"
    assert output["query_results"][0]["status"] == "FOUND"
    assert len(output["candidates"]) == 1
    hit = output["candidates"][0]["retrieval_hits"][0]
    assert hit["provenance"]["provider"] == "FAKE"
    assert len(hit["provenance"]["content_sha256"]) == 64


def test_jurisprudence_retriever_rejects_missing_locator_fail_closed():
    skill_input = build_jurisprudence_input([
        _jurisprudence_research_output(_jurisprudence_query())
    ])
    hit = _provider_hit()
    hit["source_url"] = None
    hit["document_ref"] = None
    output = retrieve_jurisprudence(
        skill_input,
        [_provider_response(results=[hit])],
    )
    assert output["candidates"] == []
    assert output["query_results"][0]["status"] == "INVALID_RESULTS"
    assert output["rejected_results"][0]["code"] == "LOCATOR_MISSING"
    assert output["context_sufficiency"] == "INSUFFICIENT"


def test_jurisprudence_retriever_deduplicates_same_judicial_identity():
    skill_input = build_jurisprudence_input([
        _jurisprudence_research_output(
            _jurisprudence_query("q1"),
            {**_jurisprudence_query("q2"), "issue_id": "i2"},
        )
    ])
    output = retrieve_jurisprudence(
        skill_input,
        [
            _provider_response("q1", provider="P1", results=[_provider_hit(result_id="a")]),
            _provider_response("q2", provider="P2", results=[_provider_hit(result_id="b")]),
        ],
    )
    assert len(output["candidates"]) == 1
    candidate = output["candidates"][0]
    assert candidate["query_ids"] == ["q1", "q2"]
    assert len(candidate["retrieval_hits"]) == 2


def test_jurisprudence_retriever_tracks_provider_failure_without_fabricating_candidate():
    skill_input = build_jurisprudence_input([
        _jurisprudence_research_output(_jurisprudence_query())
    ])
    output = retrieve_jurisprudence(
        skill_input,
        [_provider_response(status="FAILED", error_code="UNAVAILABLE")],
    )
    assert output["candidates"] == []
    assert output["query_results"][0]["status"] == "FAILED"
    assert output["provider_failures"][0]["error_code"] == "UNAVAILABLE"


def test_jurisprudence_score_flags_unprovenanced_acceptance():
    expected = {
        "context_sufficiency": "SUFFICIENT",
        "query_results": [{"query_id": "q1", "status": "FOUND"}],
        "candidates": [{"court": "TJSP", "identifier": "123"}],
        "rejection_count": 0,
        "provider_failure_count": 0,
    }
    actual = {
        "context_sufficiency": "SUFFICIENT",
        "query_results": [{"query_id": "q1", "status": "FOUND"}],
        "candidates": [{
            "court": "TJSP",
            "identifier": "123",
            "retrieval_hits": [{
                "excerpt": "x",
                "source_url": None,
                "document_ref": None,
                "provenance": {},
            }],
        }],
        "rejected_results": [],
        "provider_failures": [],
    }
    score = score_jurisprudence_retrieval(expected, actual)
    assert score["dangerous_unprovenanced_acceptance"] is True


def test_jurisprudence_runner_is_deterministic():
    research = _jurisprudence_research_output(_jurisprudence_query())
    result = run_jurisprudence_retriever_skill(
        [research],
        [_provider_response(results=[_provider_hit()])],
    )
    assert result["trace"]["executor"] == "deterministic"
    assert result["output"]["query_results"][0]["status"] == "FOUND"
