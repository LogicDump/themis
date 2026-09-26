"""Shared case-synthesis input, validation, and prompt contract."""
from __future__ import annotations

from typing import Any

from core.api import core_api


CASE_SYNTHESIS_PROMPT_VERSION = "case-synthesis-v4"

CASE_SYNTHESIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "case_synthesis": {"type": "string"},
        "current_status": {"type": "string"},
        "pending_issues": {"type": "array", "items": {"$ref": "#/$defs/pending_item"}},
        "supporting_movement_ids": {"type": "array", "items": {"type": "string"}},
    },
    "$defs": {
        "pending_item": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "text": {"type": "string"},
                "source_movement_ids": {"type": "array", "items": {"type": "string"}},
                "basis": {"type": "string", "enum": ["AWAITING_RESPONSE", "AWAITING_ACTION", "AWAITING_DECISION", "PENDING_EVIDENCE", "PENDING_INSTRUCTION", "OTHER_EXPLICIT_PENDING"]},
            },
            "required": ["text", "source_movement_ids", "basis"],
        },
    },
    "required": ["case_synthesis", "current_status", "pending_issues", "supporting_movement_ids"],
}


def validate_case_synthesis(value: Any, expected_ids: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("resultado estruturado deve ser objeto")
    if not str(value.get("case_synthesis") or "").strip():
        raise ValueError("case_synthesis não pode ser vazio")
    if not str(value.get("current_status") or "").strip():
        raise ValueError("current_status não pode ser vazio")
    supporting_ids = value.get("supporting_movement_ids")
    if not isinstance(supporting_ids, list) or any(str(item_id) not in expected_ids for item_id in supporting_ids):
        raise ValueError("supporting_movement_ids inválido")
    pending = value.get("pending_issues")
    if not isinstance(pending, list) or len(pending) > 5:
        raise ValueError("pending_issues deve ser uma lista com no máximo 5 itens")
    for item in pending:
        if not isinstance(item, dict) or not str(item.get("text") or "").strip():
            raise ValueError("item inválido em pending_issues")
        if item.get("basis") not in {"AWAITING_RESPONSE", "AWAITING_ACTION", "AWAITING_DECISION", "PENDING_EVIDENCE", "PENDING_INSTRUCTION", "OTHER_EXPLICIT_PENDING"}:
            raise ValueError("pending_issue sem basis válido")
        ids = item.get("source_movement_ids")
        if not isinstance(ids, list) or not ids or any(str(item_id) not in expected_ids for item_id in ids):
            raise ValueError("source_movement_ids inválido em pending_issues")
    return value


def case_synthesis_instructions() -> str:
    return (
        "Produza uma síntese do caso a partir da sequência processual fornecida em movements[]. "
        "Cada elemento é um Movement independente e contém somente seu summary_text CURRENT. "
        "Preserve rigorosamente a ordem processual e a independência dos atos.\n\n"
        "Retorne case_synthesis em Markdown estruturado, preferencialmente com 250–400 palavras, usando exatamente estas três seções e nesta ordem:\n"
        "## Contexto e objeto\n"
        "## Posições e elementos relevantes\n"
        "## Desenvolvimento e decisões\n"
        "Cada título deve ficar sozinho numa linha. Em cada seção escreva parágrafos curtos, com no máximo 3 frases, separados por uma linha em branco. "
        "Explique de forma compacta o objeto do processo, as alegações e posições centrais das partes, os fatos e provas materialmente relevantes "
        "e as principais decisões que alteraram o estado do processo. Não produza um bloco corrido, não junte seções no mesmo parágrafo, "
        "não reproduza cronologia ato a ato nem repita informação apenas para aumentar cobertura; o objetivo é situar rapidamente o advogado sobre o caso. "
        "Pendências devem ser retornadas somente em pending_issues, que a interface apresenta como lista; não duplique a lista no texto case_synthesis.\n\n"
        "Retorne current_status em texto curto, preferencialmente 1–3 parágrafos ou frases, priorizando onde o processo está agora. "
        "Retorne pending_issues somente com situações explicitamente indicadas pelos summaries como ainda pendentes, no máximo 5 itens. "
        "Uma pending_issue só pode existir quando os summaries disserem expressamente que há ato aguardado, resposta aguardada, manifestação aguardada, decisão ainda não proferida, diligência em curso, instrução ainda por realizar ou obrigação cujo cumprimento esteja expressamente pendente. "
        "Cada item deve conter text, source_movement_ids e basis, usando exatamente AWAITING_RESPONSE, AWAITING_ACTION, AWAITING_DECISION, PENDING_EVIDENCE, PENDING_INSTRUCTION ou OTHER_EXPLICIT_PENDING. "
        "Se a fonte não disser explicitamente que a providência continua pendente, omita o item. "
        "Nunca infira cobrança, depósito, pagamento, inadimplemento, cumprimento, comprovação, execução ou vencimento. "
        "Condenação, multa, obrigação, tutela deferida, decisão, pedido acolhido ou direito reconhecido não são pendência por si sós. "
        "Retorne supporting_movement_ids com os Movements materialmente usados para compor a síntese principal.\n\n"
        "Atribua alegações às partes. Não apresente conclusão de laudo ou prova técnica como fato judicialmente reconhecido sem decisão correspondente. "
        "Decisões judiciais podem modificar ou superar estados anteriores. Não invente fatos ou IDs, não calcule datas ou prazos e não transforme detalhes cartorários sem relevância em destaque principal. "
        "Todos os IDs em pending_issues e supporting_movement_ids devem pertencer aos IDs recebidos. "
        "Produza somente o objeto JSON conforme o schema fornecido."
    )


def case_synthesis_records(process_id: str) -> tuple[list[dict[str, Any]], set[str], str] | None:
    movements = core_api.movements(process_id)
    dependencies = core_api.case_synthesis_dependencies(process_id)
    if movements is None or dependencies is None:
        return None
    dependency_rows, dependency_hash = dependencies
    summaries = {row["movement_id"]: row for row in dependency_rows}
    records = []
    for movement in movements:
        movement_id = str(movement["movement_id"])
        summary = summaries.get(movement_id)
        if summary is None or not str(summary.get("summary_text") or "").strip():
            continue
        records.append({
            "movement_id": movement_id,
            "occurred_at": movement.get("occurred_at") or movement.get("source_datetime"),
            "label": movement.get("movement_type") or movement.get("label") or "Movimentação",
            "summary_text": summary["summary_text"],
            "summary_version": summary["summary_version"],
        })
    return records, {str(movement["movement_id"]) for movement in movements}, dependency_hash
