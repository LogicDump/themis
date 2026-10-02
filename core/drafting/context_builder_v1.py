"""Orchestrator for DraftingTask -> Issue Map -> retrieval -> LegalContextPack V1."""
from __future__ import annotations

import asyncio
import json
import sqlite3
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from core.ai.long_job_llm import THEMIS_LONG_LLM_TIMEOUT_SECONDS, call_long_job_llm
from core.drafting.context_pack_v1 import (
    DraftingTask,
    apply_context_selection,
    build_legal_context_pack,
    build_process_frame,
    load_related_documents,
    load_target_document,
    retrieve_related_sources,
)
from core.drafting.context_selector_v1 import (
    SELECTION_JSON_SCHEMA,
    build_selector_input,
    build_selector_instructions,
    validate_selection,
)
from core.drafting.issue_map_v1 import (
    ISSUE_MAP_JSON_SCHEMA,
    build_issue_mapper_input,
    build_issue_mapper_instructions,
    validate_issue_map,
)


def _normalize_usage(value: Any) -> Any:
    return asdict(value) if is_dataclass(value) else value


def _structured_result(value: Any) -> tuple[Any, str | None, str | None, Any]:
    if isinstance(value, dict):
        return (
            value.get("parsed"),
            value.get("provider"),
            value.get("model"),
            _normalize_usage(value.get("usage")),
        )
    return (
        getattr(value, "parsed", None),
        getattr(value, "provider", None),
        getattr(value, "model", None),
        _normalize_usage(getattr(value, "usage", None)),
    )


def _load_base(task: DraftingTask, db_path: Path | str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    db = sqlite3.connect(str(Path(db_path).resolve()))
    db.row_factory = sqlite3.Row
    try:
        target = None
        if task.target_movement_id:
            target = load_target_document(db, task.process_id, task.target_movement_id)
        frame = build_process_frame(db, task.process_id)
        return target, frame
    finally:
        db.close()


def _load_promoted(
    task: DraftingTask,
    db_path: Path | str,
    movement_ids: list[str],
) -> list[dict[str, Any]]:
    if not movement_ids:
        return []
    db = sqlite3.connect(str(Path(db_path).resolve()))
    db.row_factory = sqlite3.Row
    try:
        return load_related_documents(
            db,
            task.process_id,
            movement_ids,
            target_movement_id=task.target_movement_id,
        )
    finally:
        db.close()


async def build_context_pack(
    llm: Any,
    task: DraftingTask,
    *,
    db_path: Path | str,
    vector_db_path: Path | str | None = None,
    provider: str | None = None,
    model: str | None = None,
    top_k_per_issue: int = 6,
    timeout_seconds: float = THEMIS_LONG_LLM_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Build a non-persisted, source-grounded LegalContextPack."""
    target, process_frame = await asyncio.to_thread(_load_base, task, db_path)
    if task.task_kind != "GENERAL_PETITION" and target is None:
        raise ValueError("tarefa dirigida exige ato-alvo integral")

    if target is None:
        issues: list[dict[str, Any]] = []
        issue_trace = {"provider": None, "model": None, "usage": None, "skipped": True}
    else:
        issue_result = await call_long_job_llm(
            llm,
            "acomplete_structured",
            timeout_seconds=timeout_seconds,
            instructions=build_issue_mapper_instructions(task.task_kind, task.goal),
            input=[{
                "type": "text",
                "text": json.dumps(build_issue_mapper_input(target), ensure_ascii=False),
            }],
            json_schema=ISSUE_MAP_JSON_SCHEMA,
            schema_name="themis_drafting_issue_map_v1",
            provider=provider,
            model=model,
            max_tokens=8192,
            purpose="themis.drafting.issue_map",
        )
        parsed, actual_provider, actual_model, usage = _structured_result(issue_result)
        issues = validate_issue_map(parsed, target)
        issue_trace = {
            "provider": actual_provider,
            "model": actual_model,
            "usage": usage,
            "skipped": False,
        }

    candidates = await asyncio.to_thread(
        retrieve_related_sources,
        task,
        issues,
        db_path=db_path,
        vector_db_path=vector_db_path,
        top_k_per_issue=top_k_per_issue,
    ) if issues else []

    if issues and candidates:
        selector_payload = build_selector_input(asdict(task), issues, candidates)
        selector_result = await call_long_job_llm(
            llm,
            "acomplete_structured",
            timeout_seconds=timeout_seconds,
            instructions=build_selector_instructions(task.task_kind, task.goal),
            input=[{
                "type": "text",
                "text": json.dumps(selector_payload, ensure_ascii=False),
            }],
            json_schema=SELECTION_JSON_SCHEMA,
            schema_name="themis_legal_context_selector_v1",
            provider=provider,
            model=model,
            max_tokens=4096,
            purpose="themis.drafting.context_selector",
        )
        parsed, actual_provider, actual_model, usage = _structured_result(selector_result)
        selections = validate_selection(parsed, issues, candidates)
        selector_trace = {
            "provider": actual_provider,
            "model": actual_model,
            "usage": usage,
            "skipped": False,
        }
    else:
        selections = [
            {
                "issue_id": issue["issue_id"],
                "candidate_ids": [],
                "promote_movement_ids": [],
                "unresolved": True,
            }
            for issue in issues
        ]
        selector_trace = {
            "provider": None,
            "model": None,
            "usage": None,
            "skipped": True,
        }

    selected_sources, promote_ids, unresolved = apply_context_selection(
        candidates, selections
    )
    related_documents = await asyncio.to_thread(
        _load_promoted, task, db_path, promote_ids
    )
    pack = build_legal_context_pack(
        task,
        target,
        process_frame=process_frame,
        issues=issues,
        related_sources=selected_sources,
        related_documents=related_documents,
        unresolved_points=unresolved,
    )
    return {
        "pack": pack,
        "trace": {
            "issue_mapper": issue_trace,
            "retrieval_candidate_count": len(candidates),
            "selector": selector_trace,
            "selections": selections,
        },
    }
