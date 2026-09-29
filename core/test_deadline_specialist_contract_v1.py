from core.documentos.deadline_specialist_contract_v1 import (
    ContextRequest, DeadlineSpecialistOutput, score_specialist_output,
)


def test_needs_context_requires_explicit_request():
    try:
        DeadlineSpecialistOutput(operative_instruction=True, context_sufficiency="NEEDS_CONTEXT")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "context_request" in str(exc)


def test_third_party_order_can_extract_term_but_refuse_to_invent_trigger():
    output = DeadlineSpecialistOutput(
        operative_instruction=True,
        context_sufficiency="NEEDS_CONTEXT",
        procedural_act_type="PROVIDE_INFORMATION",
        recipient_text="EMPRESA DESTINATÁRIA",
        recipient_role="THIRD_PARTY",
        explicit_term_value=10,
        explicit_term_unit="DAYS",
        context_requests=(ContextRequest(
            kind="COMMUNICATION_EVENT",
            reason="A data do documento não prova quando o terceiro recebeu a ordem.",
            query_hint="localizar certidão, AR, comunicação eletrônica ou ato equivalente de ciência",
        ),),
    )
    assert output.review_required is True
    assert output.explicit_term_value == 10
    assert output.trigger_text is None


def test_parte_contraria_requests_antecedent_instead_of_guessing_recipient():
    output = DeadlineSpecialistOutput(
        operative_instruction=True,
        context_sufficiency="NEEDS_CONTEXT",
        procedural_act_type="RESPOND_TO_OPPOSING_SUBMISSION",
        action_text="Manifeste-se a parte contrária.",
        recipient_role="UNRESOLVED",
        context_requests=(ContextRequest(
            kind="ANTECEDENT_PLEADING",
            reason="Parte contrária é relacional ao ato antecedente relevante.",
            query_hint="localizar a petição/manifestação imediatamente relacionada que provocou o despacho",
        ),),
    )
    assert output.antecedent_source_event_id is None
    assert output.review_required is True


def test_both_plausible_antecedents_requires_review_and_preserves_candidates():
    output = DeadlineSpecialistOutput(
        operative_instruction=True,
        context_sufficiency="AMBIGUOUS_REVIEW",
        procedural_act_type="RESPOND_TO_OPPOSING_SUBMISSION",
        recipient_role="UNRESOLVED",
        candidate_antecedent_event_ids=("ev_a", "ev_b"),
    )
    assert output.review_required is True
    assert output.candidate_antecedent_event_ids == ("ev_a", "ev_b")


def test_scorer_penalizes_dangerous_false_resolution():
    expected = DeadlineSpecialistOutput(
        operative_instruction=True,
        context_sufficiency="NEEDS_CONTEXT",
        recipient_role="UNRESOLVED",
        context_requests=(ContextRequest(kind="COMMUNICATION_EVENT", reason="falta ciência"),),
    )
    actual = DeadlineSpecialistOutput(
        operative_instruction=True,
        context_sufficiency="SUFFICIENT",
        recipient_role="THIRD_PARTY",
    )
    score = score_specialist_output(expected, actual)
    assert score["dangerous_false_resolution"] is True
    assert score["safe_abstention"] is False


def test_scorer_rewards_correct_context_need():
    request = ContextRequest(kind="LEGAL_CONTEXT", reason="regime aplicável ausente")
    expected = DeadlineSpecialistOutput(False, "NEEDS_CONTEXT", context_requests=(request,))
    actual = DeadlineSpecialistOutput(False, "NEEDS_CONTEXT", context_requests=(request,))
    score = score_specialist_output(expected, actual)
    assert score["field_accuracy"] == 1.0
    assert score["context_need_precision"] == 1.0
    assert score["context_need_recall"] == 1.0
