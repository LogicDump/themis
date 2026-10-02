"""Task-conditioned legal context selection contract.

The selector does not summarize or create facts. It chooses among retrieved,
source-grounded candidates and may request full canonical promotion of a
selected candidate's Movement when an excerpt is insufficient.
"""
from __future__ import annotations

import json
from typing import Any

SCHEMA_VERSION = "legal-context-selector-v1"

SELECTION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "selections": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "issue_id": {"type": "string", "minLength": 1},
                    "candidate_ids": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                        "uniqueItems": True,
                    },
                    "promote_movement_ids": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                        "uniqueItems": True,
                    },
                    "unresolved": {"type": "boolean"},
                },
                "required": [
                    "issue_id",
                    "candidate_ids",
                    "promote_movement_ids",
                    "unresolved",
                ],
            },
        },
    },
    "required": ["selections"],
}


def build_selector_instructions(task_kind: str, goal: str) -> str:
    return (
        "Você é o seletor jurídico de contexto, não o redator. Receberá issues extraídas do ato-alvo "
        "e candidatos recuperados do restante do processo, todos com fonte. Para cada issue, selecione "
        "somente candidate_ids materialmente úteis à tarefa. Não resuma, não reescreva fatos, não crie "
        "teses e não resolva contradições. candidate_ids só podem vir dos candidatos da própria issue. "
        "Use promote_movement_ids apenas quando o EXCERTO selecionado for insuficiente e o Movement inteiro "
        "precisar ser lido para preservar contexto jurídico; só promova Movements presentes nos candidate_ids "
        "selecionados. Se nenhum candidato for suficiente, marque unresolved=true. "
        f"task_kind={task_kind}; objetivo={goal}. Responda somente no schema."
    )


def build_selector_input(
    task: dict[str, Any],
    issues: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    issue_ids = [str(item.get("issue_id") or "").strip() for item in issues]
    if any(not item for item in issue_ids) or len(issue_ids) != len(set(issue_ids)):
        raise ValueError("issues inválidas/duplicadas")
    issue_set = set(issue_ids)
    compact_candidates = []
    seen_candidates: set[str] = set()
    for item in candidates:
        candidate_id = str(item.get("candidate_id") or "").strip()
        issue_id = str(item.get("issue_id") or "").strip()
        if not candidate_id or candidate_id in seen_candidates:
            raise ValueError("candidate_id ausente/duplicado")
        if issue_id not in issue_set:
            raise ValueError("candidate sem issue correspondente")
        movement_id = str(item.get("movement_id") or "").strip()
        if not movement_id:
            raise ValueError("candidate sem movement_id")
        seen_candidates.add(candidate_id)
        compact_candidates.append({
            "candidate_id": candidate_id,
            "issue_id": issue_id,
            "movement_id": movement_id,
            "movement_title": item.get("movement_title"),
            "excerpt": item.get("excerpt"),
            "score": item.get("score"),
            "source_ref": item.get("source_ref"),
            "retrieval_route": item.get("retrieval_route"),
        })
    return {
        "task": task,
        "issues": issues,
        "candidates": compact_candidates,
    }


def validate_selection(
    value: Any,
    issues: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("seleção não é JSON válido") from exc
    if not isinstance(value, dict) or set(value) != {"selections"}:
        raise ValueError("seleção deve conter somente selections[]")
    selections = value["selections"]
    if not isinstance(selections, list):
        raise ValueError("selections deve ser lista")

    issue_ids = [str(item.get("issue_id") or "").strip() for item in issues]
    if (
        any(not item for item in issue_ids)
        or len(issue_ids) != len(set(issue_ids))
        or len(selections) != len(issue_ids)
    ):
        raise ValueError("seleção deve conter exatamente uma entrada por issue")

    candidates_by_issue: dict[str, dict[str, dict[str, Any]]] = {
        issue_id: {} for issue_id in issue_ids
    }
    for candidate in candidates:
        issue_id = str(candidate.get("issue_id") or "")
        candidate_id = str(candidate.get("candidate_id") or "")
        if issue_id not in candidates_by_issue or not candidate_id:
            raise ValueError("candidate inválido para seleção")
        if candidate_id in candidates_by_issue[issue_id]:
            raise ValueError("candidate_id duplicado")
        candidates_by_issue[issue_id][candidate_id] = candidate

    seen_issues: set[str] = set()
    validated: list[dict[str, Any]] = []
    for selection in selections:
        required = {"issue_id", "candidate_ids", "promote_movement_ids", "unresolved"}
        if not isinstance(selection, dict) or set(selection) != required:
            raise ValueError("selection divergente do schema")
        issue_id = str(selection["issue_id"])
        if issue_id not in candidates_by_issue or issue_id in seen_issues:
            raise ValueError("issue_id inválida/duplicada na seleção")
        candidate_ids = selection["candidate_ids"]
        promote_ids = selection["promote_movement_ids"]
        if (
            not isinstance(candidate_ids, list)
            or len(candidate_ids) != len(set(candidate_ids))
            or not isinstance(promote_ids, list)
            or len(promote_ids) != len(set(promote_ids))
            or not isinstance(selection["unresolved"], bool)
        ):
            raise ValueError(f"listas/status inválidos em {issue_id}")
        allowed = candidates_by_issue[issue_id]
        if any(candidate_id not in allowed for candidate_id in candidate_ids):
            raise ValueError(f"candidate_id externo à issue {issue_id}")
        selected_movements = {
            str(allowed[candidate_id].get("movement_id") or "")
            for candidate_id in candidate_ids
        }
        if any(movement_id not in selected_movements for movement_id in promote_ids):
            raise ValueError(f"promoção sem candidate selecionado em {issue_id}")
        if not candidate_ids and not selection["unresolved"]:
            raise ValueError(f"issue sem contexto deve permanecer unresolved: {issue_id}")
        seen_issues.add(issue_id)
        validated.append(selection)

    if [item["issue_id"] for item in validated] != issue_ids:
        raise ValueError("ordem de selections deve seguir a ordem das issues")
    return validated
