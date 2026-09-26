"""Experimental multi-Movement summary path used only by the bake-off.

This module deliberately has no database writes.  It receives already resolved
Movement source text and returns validated, independent summaries.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Callable

from core.ai.long_job_llm import call_long_job_llm

PURPOSE = "themis.movement_summary"
DEFAULT_INPUT_TOKEN_BUDGET = 100_000
# Empirical lower bound for the legal Portuguese JSON requests measured with
# Gemini in the whole-process bake-off, with margin for instructions/schema.
CHARS_PER_TOKEN_ESTIMATE = 2.6

BATCH_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"summaries": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "properties": {"movement_id": {"type": "string"}, "summary": {"type": "string"}},
        "required": ["movement_id", "summary"],
    }}},
    "required": ["summaries"],
}

# Keep these instructions byte-for-byte aligned with the current individual
# Movement summary prompt.  The experimental path adds only batch framing and
# the JSON output contract around them.
SUMMARY_INSTRUCTIONS = (
    "1. Identifique primeiro a natureza jurídica real do ato.\n\n"
    "2. Se for ato estrutural — especialmente petição inicial:\n"
    "- produza resumo autossuficiente;\n"
    "- identifique partes e respectivos papéis;\n"
    "- identifique objeto/natureza da ação;\n"
    "- sintetize fatos principais alegados;\n"
    "- sintetize fundamentos jurídicos essenciais;\n"
    "- enumere pedidos relevantes;\n"
    "- preserve valores, tutela provisória e demais requerimentos materialmente relevantes;\n"
    "- mantenha claramente o caráter de alegação quando for narrativa da parte.\n\n"
    "3. Se for ato intermediário:\n"
    "- não reconstitua o processo inteiro;\n"
    "- diga o que o ato acrescenta, modifica, esclarece, contesta ou requer;\n"
    "- preserve documentos, valores e pedidos relevantes.\n\n"
    "4. Se for ato simples:\n"
    "- informe diretamente a providência, decisão ou consequência processual.\n\n"
    "5. Não escreva introduções metalinguísticas.\n"
    "6. Não invente informações.\n"
    "7. Produza somente Markdown simples."
)


def build_summary_prompt(source_text: str) -> str:
    """Build the V1 single-Movement prompt from the same contract used by batches."""
    return f"{SUMMARY_INSTRUCTIONS}\n\nConteúdo da movimentação:\n\n{source_text}"


def validate_movement_ids(movement_ids: list[str]) -> list[str]:
    if not isinstance(movement_ids, list) or not movement_ids:
        raise ValueError("movement_ids deve ser uma lista não vazia")
    normalized = [str(value).strip() for value in movement_ids]
    if any(not value for value in normalized):
        raise ValueError("movement_ids não pode conter id vazio")
    if len(set(normalized)) != len(normalized):
        raise ValueError("movement_ids contém duplicados")
    return normalized


def build_batch_instructions(movement_ids: list[str]) -> str:
    ids = validate_movement_ids(movement_ids)
    return (
        "Você receberá um objeto JSON com movements[]. Cada elemento é um ato processual independente. "
        "Analise cada elemento separadamente e nunca use fatos, pedidos, decisões ou metadata de outro elemento.\n\n"
        f"{SUMMARY_INSTRUCTIONS}\n\n"
        "Responda no schema fornecido, com exatamente um resultado para cada Movement recebido. "
        f"Use exatamente estes ids: {json.dumps(ids, ensure_ascii=False)}. "
        "Não omita, duplique, renomeie nem crie ids. Cada summary deve ser Markdown simples e não vazio."
    )


def build_batch_input(records: list[dict[str, Any]], movement_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    ids = validate_movement_ids(movement_ids)
    if {str(record.get("movement_id")) for record in records} != set(ids):
        raise ValueError("records deve conter exatamente os Movement ids enviados")
    by_id = {record["movement_id"]: record for record in records}
    ordered = []
    for movement_id in ids:
        record = by_id[movement_id]
        if not str(record.get("source_text") or "").strip():
            raise ValueError(f"Movement {movement_id} sem conteúdo próprio para resumir")
        ordered.append({
            "movement_id": movement_id,
            "label": str(record.get("label") or "Movimentação"),
            "source_pages": record.get("source_pages") or [],
            "source_text": record["source_text"],
        })
    return {"movements": ordered}


def estimate_batch_input_tokens(records: list[dict[str, Any]]) -> int:
    """Approximate structured JSON input using a corpus-calibrated conservative ratio."""
    payload = {"movements": [
        {
            "movement_id": str(record.get("movement_id") or ""),
            "label": str(record.get("label") or "Movimentação"),
            "source_pages": record.get("source_pages") or [],
            "source_text": str(record.get("source_text") or ""),
        }
        for record in records
    ]}
    return max(1, int(len(json.dumps(payload, ensure_ascii=False)) / CHARS_PER_TOKEN_ESTIMATE + 0.999999))


def structured_input_chars(records: list[dict[str, Any]]) -> int:
    """Return the exact serialized size of the production batch input."""
    ids = [str(record.get("movement_id") or "") for record in records]
    return len(json.dumps(build_batch_input(records, ids), ensure_ascii=False))


def partition_records_by_input_chars(
    records: list[dict[str, Any]],
    *,
    char_budget: int,
) -> list[list[dict[str, Any]]]:
    """Partition in process order by exact structured-input character size."""
    if not records:
        return []
    if char_budget < 1:
        raise ValueError("char_budget deve ser positivo")
    total_chars = structured_input_chars(records)
    batch_count = max(1, (total_chars + char_budget - 1) // char_budget)
    if batch_count == 1:
        return [records.copy()]

    # The budget is a target derived from half of the reference payload, not a
    # provider limit.  Choose contiguous cuts nearest to equal volume so a
    # final one-Movement tail is not created merely by JSON framing overhead.
    prefix_chars = [structured_input_chars(records[:index]) for index in range(1, len(records) + 1)]
    cuts: list[int] = []
    previous = 0
    for part in range(1, batch_count):
        target = total_chars * part / batch_count
        candidates = range(previous + 1, len(records) - (batch_count - part) + 1)
        cut = min(candidates, key=lambda index: abs(prefix_chars[index - 1] - target))
        cuts.append(cut)
        previous = cut
    boundaries = [0, *cuts, len(records)]
    return [records[start:end] for start, end in zip(boundaries, boundaries[1:])]


def partition_records_by_token_budget(
    records: list[dict[str, Any]],
    *,
    token_budget: int = DEFAULT_INPUT_TOKEN_BUDGET,
) -> list[list[dict[str, Any]]]:
    """Partition in process order without splitting a Movement."""
    if not records:
        return []
    if token_budget < 1:
        raise ValueError("token_budget deve ser positivo")
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for record in records:
        candidate = [*current, record]
        if current and estimate_batch_input_tokens(candidate) > token_budget:
            batches.append(current)
            current = [record]
        else:
            current = candidate
    if current:
        batches.append(current)
    return batches


def validate_batch_output(value: Any, movement_ids: list[str]) -> list[dict[str, str]]:
    expected = validate_movement_ids(movement_ids)
    payload = value
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("resposta estruturada não é um objeto JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("summaries"), list):
        raise ValueError("resposta deve conter a lista summaries")
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in payload["summaries"]:
        if not isinstance(item, dict):
            raise ValueError("cada resultado deve ser um objeto")
        movement_id = str(item.get("movement_id") or "").strip()
        summary = str(item.get("summary") or "").strip()
        if movement_id not in expected:
            raise ValueError(f"resultado inesperado: {movement_id or '<vazio>'}")
        if movement_id in seen:
            raise ValueError(f"resultado duplicado: {movement_id}")
        if not summary:
            raise ValueError(f"summary vazio: {movement_id}")
        seen.add(movement_id)
        results.append({"movement_id": movement_id, "summary": summary})
    if seen != set(expected) or len(results) != len(expected):
        missing = [movement_id for movement_id in expected if movement_id not in seen]
        raise ValueError(f"resultados incompletos; ausentes: {', '.join(missing)}")
    return results


def normalize_usage(usage: Any) -> Any:
    return asdict(usage) if is_dataclass(usage) else usage


def normalize_structured_result(value: Any) -> tuple[Any, str | None, str | None, Any]:
    if isinstance(value, dict):
        return value.get("parsed"), value.get("provider"), value.get("model"), normalize_usage(value.get("usage"))
    return getattr(value, "parsed", None), getattr(value, "provider", None), getattr(value, "model", None), normalize_usage(getattr(value, "usage", None))


async def complete_batch(
    llm: Any,
    movement_ids: list[str],
    source_loader: Callable[[str], dict[str, Any] | None],
    *,
    provider: str | None = None,
    model: str | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    ids = validate_movement_ids(movement_ids)
    records: list[dict[str, Any]] = []
    source_hashes: dict[str, str] = {}
    for movement_id in ids:
        record = source_loader(movement_id)
        if record is None:
            raise ValueError(f"Movement não encontrado: {movement_id}")
        if not str(record.get("source_text") or "").strip():
            raise ValueError(f"Movement {movement_id} sem conteúdo próprio para resumir")
        records.append(record)
        source_hashes[movement_id] = str(record.get("source_hash") or "")

    kwargs: dict[str, Any] = {"purpose": PURPOSE}
    if provider is not None:
        kwargs["provider"] = provider
    if model is not None:
        kwargs["model"] = model
    batch_input = build_batch_input(records, ids)
    call_kwargs = {
        "instructions": build_batch_instructions(ids),
        "input": [{"type": "text", "text": json.dumps(batch_input, ensure_ascii=False)}],
        "json_schema": BATCH_JSON_SCHEMA,
        **kwargs,
    }
    if timeout_seconds is not None:
        result = await call_long_job_llm(
            llm, "acomplete_structured", timeout_seconds=timeout_seconds, **call_kwargs
        )
    else:
        result = await llm.acomplete_structured(**call_kwargs)
    parsed, actual_provider, actual_model, usage = normalize_structured_result(result)
    summaries = validate_batch_output(parsed, ids)
    return {
        "summaries": summaries,
        "provider": actual_provider,
        "model": actual_model,
        "usage": usage,
        "source_hashes": source_hashes,
        "input_chars": len(json.dumps(batch_input, ensure_ascii=False)),
        "output_chars": sum(len(item["summary"]) for item in summaries),
    }
