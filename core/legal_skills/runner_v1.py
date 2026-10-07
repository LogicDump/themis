"""Executable V1 comprehension slice: Actor/Role -> Facts."""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any

from core.ai.long_job_llm import THEMIS_LONG_LLM_TIMEOUT_SECONDS, call_long_job_llm
from core.legal_skills.actor_role_v1 import (
    ACTOR_ROLE_JSON_SCHEMA,
    build_actor_role_input,
    build_actor_role_instructions,
    validate_actor_role,
)
from core.legal_skills.fact_extractor_v1 import (
    FACT_EXTRACTOR_JSON_SCHEMA,
    build_fact_extractor_input,
    build_fact_extractor_instructions,
    validate_fact_extraction,
)
from core.legal_skills.claim_request_v1 import (
    CLAIM_REQUEST_JSON_SCHEMA,
    build_claim_request_input,
    build_claim_request_instructions,
    validate_claim_request,
)
from core.legal_skills.evidence_mapper_v1 import (
    EVIDENCE_MAPPER_JSON_SCHEMA,
    build_evidence_mapper_input,
    build_evidence_mapper_instructions,
    validate_evidence_mapping,
)
from core.legal_skills.contradiction_detector_v1 import (
    CONTRADICTION_JSON_SCHEMA,
    build_contradiction_input,
    build_contradiction_instructions,
    build_contradiction_llm_input,
    validate_contradictions,
)
from core.legal_skills.evidence_gap_analyzer_v1 import analyze_evidence_gaps
from core.legal_skills.legal_issue_mapper_v1 import (
    LEGAL_ISSUE_JSON_SCHEMA,
    build_legal_issue_input,
    build_legal_issue_instructions,
    build_legal_issue_llm_input,
    validate_legal_issues,
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


async def run_actor_role_skill(
    llm: Any,
    source_document: dict[str, Any],
    process_frame: dict[str, Any],
    *,
    provider: str | None = None,
    model: str | None = None,
    timeout_seconds: float = THEMIS_LONG_LLM_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    skill_input = build_actor_role_input(source_document, process_frame)
    result = await call_long_job_llm(
        llm,
        "acomplete_structured",
        timeout_seconds=timeout_seconds,
        instructions=build_actor_role_instructions(),
        input=[{"type": "text", "text": json.dumps(skill_input, ensure_ascii=False)}],
        json_schema=ACTOR_ROLE_JSON_SCHEMA,
        schema_name="themis_actor_role_resolver_v1",
        provider=provider,
        model=model,
        max_tokens=4096,
        purpose="themis.legal_skills.actor_role",
    )
    parsed, actual_provider, actual_model, usage = _structured_result(result)
    output = validate_actor_role(parsed, skill_input)
    return {
        "input": skill_input,
        "output": output,
        "trace": {
            "provider": actual_provider,
            "model": actual_model,
            "usage": usage,
        },
    }


async def run_fact_extractor_skill(
    llm: Any,
    actor_result: dict[str, Any],
    *,
    provider: str | None = None,
    model: str | None = None,
    timeout_seconds: float = THEMIS_LONG_LLM_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    actor_input = actor_result.get("input")
    actor_output = actor_result.get("output")
    if not isinstance(actor_input, dict) or not isinstance(actor_output, dict):
        raise ValueError("actor_result inválido")
    skill_input = build_fact_extractor_input(actor_input, actor_output)
    result = await call_long_job_llm(
        llm,
        "acomplete_structured",
        timeout_seconds=timeout_seconds,
        instructions=build_fact_extractor_instructions(),
        input=[{"type": "text", "text": json.dumps(skill_input, ensure_ascii=False)}],
        json_schema=FACT_EXTRACTOR_JSON_SCHEMA,
        schema_name="themis_fact_extractor_v1",
        provider=provider,
        model=model,
        max_tokens=4096,
        purpose="themis.legal_skills.fact_extractor",
    )
    parsed, actual_provider, actual_model, usage = _structured_result(result)
    output = validate_fact_extraction(parsed, skill_input)
    return {
        "input": skill_input,
        "output": output,
        "trace": {
            "provider": actual_provider,
            "model": actual_model,
            "usage": usage,
        },
    }


async def run_claim_request_skill(
    llm: Any,
    actor_result: dict[str, Any],
    *,
    provider: str | None = None,
    model: str | None = None,
    timeout_seconds: float = THEMIS_LONG_LLM_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    actor_input = actor_result.get("input")
    actor_output = actor_result.get("output")
    if not isinstance(actor_input, dict) or not isinstance(actor_output, dict):
        raise ValueError("actor_result inválido")
    skill_input = build_claim_request_input(actor_input, actor_output)
    result = await call_long_job_llm(
        llm,
        "acomplete_structured",
        timeout_seconds=timeout_seconds,
        instructions=build_claim_request_instructions(),
        input=[{"type": "text", "text": json.dumps(skill_input, ensure_ascii=False)}],
        json_schema=CLAIM_REQUEST_JSON_SCHEMA,
        schema_name="themis_claim_request_mapper_v1",
        provider=provider,
        model=model,
        max_tokens=4096,
        purpose="themis.legal_skills.claim_request",
    )
    parsed, actual_provider, actual_model, usage = _structured_result(result)
    output = validate_claim_request(parsed, skill_input)
    return {
        "input": skill_input,
        "output": output,
        "trace": {"provider": actual_provider, "model": actual_model, "usage": usage},
    }


async def run_evidence_mapper_skill(
    llm: Any,
    fact_result: dict[str, Any],
    evidence_sources: list[dict[str, Any]],
    *,
    provider: str | None = None,
    model: str | None = None,
    timeout_seconds: float = THEMIS_LONG_LLM_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    fact_input = fact_result.get("input")
    fact_output = fact_result.get("output")
    if not isinstance(fact_input, dict) or not isinstance(fact_output, dict):
        raise ValueError("fact_result inválido")
    skill_input = build_evidence_mapper_input(fact_input, fact_output, evidence_sources)
    result = await call_long_job_llm(
        llm,
        "acomplete_structured",
        timeout_seconds=timeout_seconds,
        instructions=build_evidence_mapper_instructions(),
        input=[{"type": "text", "text": json.dumps(skill_input, ensure_ascii=False)}],
        json_schema=EVIDENCE_MAPPER_JSON_SCHEMA,
        schema_name="themis_evidence_mapper_v1",
        provider=provider,
        model=model,
        max_tokens=6144,
        purpose="themis.legal_skills.evidence_mapper",
    )
    parsed, actual_provider, actual_model, usage = _structured_result(result)
    output = validate_evidence_mapping(parsed, skill_input)
    return {
        "input": skill_input,
        "output": output,
        "trace": {"provider": actual_provider, "model": actual_model, "usage": usage},
    }


async def run_contradiction_detector_skill(
    llm: Any,
    process_id: str,
    fact_outputs: list[dict[str, Any]],
    evidence_outputs: list[dict[str, Any]] | None = None,
    *,
    provider: str | None = None,
    model: str | None = None,
    timeout_seconds: float = THEMIS_LONG_LLM_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    skill_input = build_contradiction_input(process_id, fact_outputs, evidence_outputs)
    llm_input = build_contradiction_llm_input(skill_input)
    result = await call_long_job_llm(
        llm,
        "acomplete_structured",
        timeout_seconds=timeout_seconds,
        instructions=build_contradiction_instructions(),
        input=[{"type": "text", "text": json.dumps(llm_input, ensure_ascii=False)}],
        json_schema=CONTRADICTION_JSON_SCHEMA,
        schema_name="themis_contradiction_detector_v1",
        provider=provider,
        model=model,
        max_tokens=4096,
        purpose="themis.legal_skills.contradiction_detector",
    )
    parsed, actual_provider, actual_model, usage = _structured_result(result)
    output = validate_contradictions(parsed, skill_input)
    return {
        "input": skill_input,
        "output": output,
        "trace": {"provider": actual_provider, "model": actual_model, "usage": usage},
    }


async def run_legal_issue_mapper_skill(
    llm: Any,
    process_id: str,
    fact_outputs: list[dict[str, Any]],
    claim_outputs: list[dict[str, Any]] | None = None,
    contradiction_outputs: list[dict[str, Any]] | None = None,
    gap_outputs: list[dict[str, Any]] | None = None,
    *,
    provider: str | None = None,
    model: str | None = None,
    timeout_seconds: float = THEMIS_LONG_LLM_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    skill_input = build_legal_issue_input(
        process_id,
        fact_outputs,
        claim_outputs,
        contradiction_outputs,
        gap_outputs,
    )
    llm_input = build_legal_issue_llm_input(skill_input)
    result = await call_long_job_llm(
        llm,
        "acomplete_structured",
        timeout_seconds=timeout_seconds,
        instructions=build_legal_issue_instructions(),
        input=[{"type": "text", "text": json.dumps(llm_input, ensure_ascii=False)}],
        json_schema=LEGAL_ISSUE_JSON_SCHEMA,
        schema_name="themis_legal_issue_mapper_v1",
        provider=provider,
        model=model,
        max_tokens=4096,
        purpose="themis.legal_skills.legal_issue_mapper",
    )
    parsed, actual_provider, actual_model, usage = _structured_result(result)
    output = validate_legal_issues(parsed, skill_input)
    return {
        "input": skill_input,
        "output": output,
        "trace": {"provider": actual_provider, "model": actual_model, "usage": usage},
    }


def run_evidence_gap_analyzer_skill(
    process_id: str,
    fact_outputs: list[dict[str, Any]],
    evidence_outputs: list[dict[str, Any]] | None = None,
    contradiction_outputs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    output = analyze_evidence_gaps(
        process_id,
        fact_outputs,
        evidence_outputs,
        contradiction_outputs,
    )
    return {
        "output": output,
        "trace": {
            "executor": "deterministic",
            "provider": None,
            "model": None,
            "usage": None,
        },
    }


async def run_comprehension_slice(
    llm: Any,
    source_document: dict[str, Any],
    process_frame: dict[str, Any],
    *,
    provider: str | None = None,
    model: str | None = None,
    timeout_seconds: float = THEMIS_LONG_LLM_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    actor = await run_actor_role_skill(
        llm,
        source_document,
        process_frame,
        provider=provider,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    facts = await run_fact_extractor_skill(
        llm,
        actor,
        provider=provider,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    claims = await run_claim_request_skill(
        llm,
        actor,
        provider=provider,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    return {
        "schema_version": "legal-comprehension-slice-v1",
        "actor_role": actor,
        "facts": facts,
        "claims_requests": claims,
    }
