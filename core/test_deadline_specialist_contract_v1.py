from core.documentos.deadline_specialist_contract_v1 import (
    ContextRequest, DeadlineSpecialistOutput, score_specialist_output,
)


def test_needs_context_requires_semantic_request():
    try:
        DeadlineSpecialistOutput(
            operative_instruction=True,
            context_sufficiency="NEEDS_CONTEXT",
            context_requests=(ContextRequest(
                kind="COMMUNICATION_EVENT",
                purpose="TRIGGER_RESOLUTION",
                reason="falta ciência",
            ),),
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "SEMANTIC_RESOLUTION" in str(exc)


def test_sufficient_may_request_trigger_context_without_semantic_review():
    output = DeadlineSpecialistOutput(
        operative_instruction=True,
        context_sufficiency="SUFFICIENT",
        procedural_act_type="PROVIDE_INFORMATION",
        recipient_text="EMPRESA DESTINATÁRIA",
        recipient_role="THIRD_PARTY",
        explicit_term_value=10,
        explicit_term_unit="DAYS",
        context_requests=(ContextRequest(
            kind="COMMUNICATION_EVENT",
            purpose="TRIGGER_RESOLUTION",
            reason="A data do documento não prova quando o terceiro recebeu a ordem.",
            query_hint="localizar certidão, AR, comunicação eletrônica ou ato equivalente de ciência",
        ),),
    )
    assert output.review_required is False
    assert output.downstream_context_required is True
    assert output.explicit_term_value == 10
    assert output.trigger_text is None


def test_sufficient_rejects_semantic_context_request():
    try:
        DeadlineSpecialistOutput(
            operative_instruction=True,
            context_sufficiency="SUFFICIENT",
            context_requests=(ContextRequest(
                kind="ANTECEDENT_PLEADING",
                purpose="SEMANTIC_RESOLUTION",
                reason="falta antecedente",
            ),),
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "resolução semântica" in str(exc)


def test_parte_contraria_requests_antecedent_instead_of_guessing_recipient():
    output = DeadlineSpecialistOutput(
        operative_instruction=True,
        context_sufficiency="NEEDS_CONTEXT",
        procedural_act_type="RESPOND_TO_OPPOSING_SUBMISSION",
        action_text="Manifeste-se a parte contrária.",
        recipient_role="UNRESOLVED",
        context_requests=(ContextRequest(
            kind="ANTECEDENT_PLEADING",
            purpose="SEMANTIC_RESOLUTION",
            reason="Parte contrária é relacional ao ato antecedente relevante.",
            query_hint="localizar a petição/manifestação imediatamente relacionada que provocou o despacho",
        ),),
    )
    assert output.antecedent_source_event_id is None
    assert output.review_required is True
    assert output.downstream_context_required is False


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


def test_rule_resolution_context_does_not_make_semantics_insufficient():
    output = DeadlineSpecialistOutput(
        operative_instruction=True,
        context_sufficiency="SUFFICIENT",
        procedural_act_type="FILE_DEFENSE",
        recipient_role="DEFENDANT",
        context_requests=(ContextRequest(
            kind="LEGAL_CONTEXT",
            purpose="RULE_RESOLUTION",
            reason="regime aplicável ausente",
        ),),
    )
    assert output.review_required is False
    assert output.downstream_context_required is True


def test_scorer_penalizes_dangerous_false_semantic_resolution():
    expected = DeadlineSpecialistOutput(
        operative_instruction=True,
        context_sufficiency="NEEDS_CONTEXT",
        recipient_role="UNRESOLVED",
        context_requests=(ContextRequest(
            kind="ANTECEDENT_PLEADING",
            purpose="SEMANTIC_RESOLUTION",
            reason="falta antecedente",
        ),),
    )
    actual = DeadlineSpecialistOutput(
        operative_instruction=True,
        context_sufficiency="SUFFICIENT",
        recipient_role="THIRD_PARTY",
    )
    score = score_specialist_output(expected, actual)
    assert score["dangerous_false_resolution"] is True
    assert score["safe_abstention"] is False


def test_scorer_distinguishes_same_kind_different_purpose():
    expected = DeadlineSpecialistOutput(
        True,
        "SUFFICIENT",
        context_requests=(ContextRequest(
            kind="LEGAL_CONTEXT",
            purpose="RULE_RESOLUTION",
            reason="regime aplicável ausente",
        ),),
    )
    actual = DeadlineSpecialistOutput(
        True,
        "NEEDS_CONTEXT",
        context_requests=(ContextRequest(
            kind="LEGAL_CONTEXT",
            purpose="SEMANTIC_RESOLUTION",
            reason="modelo pediu contexto no estágio errado",
        ),),
    )
    score = score_specialist_output(expected, actual)
    assert score["context_need_precision"] == 0.0
    assert score["context_need_recall"] == 0.0


def test_explicit_date_and_participant_ids_are_scored():
    expected = DeadlineSpecialistOutput(
        True,
        "SUFFICIENT",
        recipient_role="BOTH_PARTIES",
        recipient_participant_ids=("p1", "p2"),
        explicit_term_unit="DATE_CERTAIN",
        explicit_term_date="2026-10-30",
    )
    actual = DeadlineSpecialistOutput(
        True,
        "SUFFICIENT",
        recipient_role="BOTH_PARTIES",
        recipient_participant_ids=("p1", "p2"),
        explicit_term_unit="DATE_CERTAIN",
        explicit_term_date="2026-10-30",
    )
    score = score_specialist_output(expected, actual)
    assert score["field_accuracy"] == 1.0
