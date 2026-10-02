"""One-shot, out-of-process executor for durable process-summary jobs."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from core.api import core_api
from core.ai.long_job_llm import (
    THEMIS_LONG_LLM_TIMEOUT_SECONDS,
    begin_call_diagnostic,
    call_long_job_llm,
    finish_call_diagnostic,
    is_timeout_exception,
)
from dashboard.summary_worker_process import _process_start_time
from dashboard.movement_summary_batch_bakeoff import (
    normalize_structured_result,
    partition_records_by_input_chars,
    structured_input_chars,
)
from core.documentos.movement_analysis_v3 import (
    ANALYSIS_JSON_SCHEMA,
    build_analysis_input,
    build_analysis_instructions,
    validate_analysis_independently,
)

_LOGGER = logging.getLogger("themis.summary_worker")
_CALIBRATION_PROCESS_ID = "1029994-43.2023.8.26.0554"
_RETRY_LIMIT = 3
_RETRY_MAX_SECONDS = 60.0
_STARTUP_CLAIM_SECONDS = 20.0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _persist(job: dict[str, Any]) -> dict[str, Any]:
    job["updated_at"] = _utc_now()
    return core_api.save_movement_analysis_v2_job_record(job)


def _analysis_v3_batch_char_budget() -> tuple[int, int]:
    """Keep the existing calibration and run its full-corpus reads in this process."""
    try:
        movements = core_api.movements(_CALIBRATION_PROCESS_ID)
        if movements is not None:
            records: list[dict[str, Any]] = []
            for movement in movements:
                movement_id = str(movement.get("movement_id") or movement.get("id") or "")
                if not movement_id:
                    continue
                record = core_api.movement_summary_source_record(movement_id)
                if record is None or not str(record.get("source_text") or "").strip():
                    continue
                records.append(record)
            if records:
                total_chars = structured_input_chars(records)
                return min(max(1, total_chars // 2), 40000), total_chars
    except Exception:
        _LOGGER.exception("Calibração do batch de summaries falhou; usando orçamento padrão")
    return 40000, 604474


def _is_current_summary(source_hash: str | None, stored: dict[str, Any] | None) -> bool:
    return bool(
        stored and source_hash
        and stored.get("source_hash") == source_hash
        and str(stored.get("summary_text") or "").strip()
    )


def _is_quota_error(exc: Exception) -> bool:
    normalized = str(exc).casefold()
    return any(token in normalized for token in ("429", "resource_exhausted", "resource exhausted", "rate limit", "too many requests"))


def _retry_after_seconds(exc: Exception, attempt: int) -> float:
    candidates: list[Any] = []
    for name in ("retry_after", "retry_after_seconds"):
        value = getattr(exc, name, None)
        if value is not None:
            candidates.append(value)
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if headers:
        for key in ("retry-after", "Retry-After"):
            if headers.get(key) is not None:
                candidates.append(headers.get(key))
    match = re.search(r"retry[- _]?after\s*[:=]?\s*(\d+(?:\.\d+)?)", str(exc), re.IGNORECASE)
    if match:
        candidates.append(match.group(1))
    match = re.search(r"retry[_-]?delay\s*[\"']?\s*[:=]\s*[\"']?\s*(\d+(?:\.\d+)?)\s*s?", str(exc), re.IGNORECASE)
    if match:
        candidates.append(match.group(1))
    for value in candidates:
        try:
            return max(0.0, min(_RETRY_MAX_SECONDS, float(value)))
        except (TypeError, ValueError):
            pass
    return min(_RETRY_MAX_SECONDS, float(2 ** max(0, attempt)))


def _is_structured_response_error(exc: Exception) -> bool:
    normalized = str(exc).casefold()
    return any(marker in normalized for marker in (
        "resposta deve conter", "resultado deve ser", "resultado inesperado",
        "resultado duplicado", "summary vazio", "resultados incompletos", "objeto json",
        "resposta v3", "movement ausente", "provenance não conferível",
        "papel não factual", "estado epistêmico inválido", "support_status inválido",
    ))


def _error_text(exc: Exception) -> str:
    text = re.sub(r"\s+", " ", str(exc)).strip()
    return text[:1000] or type(exc).__name__


def _is_cancel_requested(job: dict[str, Any]) -> bool:
    fresh = core_api.movement_analysis_v2_job(str(job["process_id"]), str(job["job_id"]))
    if fresh is None:
        raise RuntimeError("Job desapareceu do process.db")
    job.update(fresh)
    return bool(fresh.get("cancel_requested"))


async def _run_summary_unit(
    job: dict[str, Any],
    batch_ids: list[str],
    by_id: dict[str, dict[str, Any]],
    llm: Any,
    counters: dict[str, Any],
    total_count: int,
) -> None:
    pending_ids: list[str] = []
    for movement_id in batch_ids:
        source = by_id.get(movement_id)
        current = core_api.movement_analysis_v3_current(movement_id)
        if source and (job.get("force_all") or not _is_current_summary(source.get("source_hash"), current)):
            pending_ids.append(movement_id)
    if not pending_ids:
        return

    result = None
    last_error: Exception | None = None
    correction_hint = ""
    timed_out = False
    for attempt in range(_RETRY_LIMIT):
        if _is_cancel_requested(job):
            return
        context = core_api.movement_analysis_v3_context(str(job["process_id"]))
        if context is None:
            raise ValueError("Process not found while preparing Movement Analysis V3")
        records = [by_id[movement_id] for movement_id in pending_ids]
        payload = build_analysis_input(context["main"], context["known"], records)
        diagnostic, diagnostic_started = begin_call_diagnostic(
            job, provider=str(job["provider"]), model=str(job["model"]), operation="movement_analysis_v3"
        )
        _persist(job)
        call_kwargs = dict(
            instructions=build_analysis_instructions(pending_ids) + correction_hint,
            input=[{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
            json_schema=ANALYSIS_JSON_SCHEMA,
            schema_name="themis_movement_analysis_v3",
            provider=job["provider"],
            model=job["model"],
            max_tokens=16384,
            purpose="themis.movement_analysis",
        )
        try:
            candidate = await call_long_job_llm(
                llm, "acomplete_structured",
                timeout_seconds=THEMIS_LONG_LLM_TIMEOUT_SECONDS, **call_kwargs,
            )
            parsed, actual_provider, actual_model, usage = normalize_structured_result(candidate)
            if not actual_provider or not actual_model:
                raise RuntimeError("Hermes nao informou provider/model efetivamente usados")
            sources = {
                movement_id: by_id[movement_id].get("_source_pages", {})
                for movement_id in pending_ids
            }
            validated, rejected = validate_analysis_independently(
                parsed, pending_ids, sources=sources,
                known_ids=set(context["known_ids"]),
                main_ids=set(context["main_ids"]),
                actor_ids=set(context["actor_ids"]),
            )
            if not validated and rejected:
                raise ValueError("; ".join(f"{mid}: {reason}" for mid, reason in rejected.items()))
            finish_call_diagnostic(diagnostic, diagnostic_started, result=candidate)
            _persist(job)
            result = {
                "validated": validated, "rejected": rejected,
                "provider": actual_provider, "model": actual_model, "usage": usage,
            }
            break
        except Exception as exc:
            last_error = exc
            correction_hint = (
                "\nA tentativa anterior foi rejeitada pelo validador: "
                + _error_text(exc)
                + ". Corrija exatamente essa violação sem alterar fatos nem inventar conteúdo."
            )
            finish_call_diagnostic(diagnostic, diagnostic_started, error=exc)
            _persist(job)
            if is_timeout_exception(exc):
                timed_out = True
                break
            if attempt + 1 >= _RETRY_LIMIT:
                break
            if _is_quota_error(exc):
                await asyncio.sleep(_retry_after_seconds(exc, attempt))
            elif not _is_structured_response_error(exc):
                await asyncio.sleep(min(_RETRY_MAX_SECONDS, float(2 ** attempt)))

    if result is None:
        if len(pending_ids) > 1 and not timed_out:
            midpoint = max(1, len(pending_ids) // 2)
            await _run_summary_unit(job, pending_ids[:midpoint], by_id, llm, counters, total_count)
            await _run_summary_unit(job, pending_ids[midpoint:], by_id, llm, counters, total_count)
            return
        error = _error_text(last_error or RuntimeError("falha sem diagnostico"))
        if timed_out:
            error = f"TIMEOUT: {error}"
        counters["failed"] += len(pending_ids)
        counters["errors"].extend({"movement_id": movement_id, "error": error} for movement_id in pending_ids)
        job.update(
            failed=counters["failed"],
            pending=max(0, total_count - counters["completed"] - counters["failed"]),
            errors=list(counters["errors"]),
        )
        return

    valid_by_id = {item["movement_id"]: item for item in result["validated"]}
    save_records = [
        {
            "movement_id": movement_id,
            "summary": valid_by_id[movement_id]["summary"],
            "source_hash": by_id[movement_id]["source_hash"],
            "analysis": valid_by_id[movement_id],
        }
        for movement_id in pending_ids if movement_id in valid_by_id
    ]
    if save_records:
        core_api.save_movement_analysis_v3_batch_record(
            save_records, provider=result["provider"], model=result["model"], usage=result.get("usage"),
        )
        counters["completed"] += len(save_records)

    rejected_ids = [movement_id for movement_id in pending_ids if movement_id in result["rejected"]]
    if rejected_ids:
        if len(pending_ids) > 1:
            await _run_summary_unit(job, rejected_ids, by_id, llm, counters, total_count)
        else:
            movement_id = rejected_ids[0]
            counters["failed"] += 1
            counters["errors"].append({
                "movement_id": movement_id, "error": result["rejected"][movement_id],
            })
    job.update(
        completed=counters["completed"], failed=counters["failed"],
        pending=max(0, total_count - counters["completed"] - counters["failed"]),
        errors=list(counters["errors"]),
    )


async def run_process_summary_job(job_id: str, process_id: str, worker_token: str, llm: Any) -> None:
    job = core_api.movement_analysis_v2_job(process_id, job_id)
    if (
        job is None or job.get("worker_token") != worker_token
        or int(job.get("worker_pid") or 0) != os.getpid()
    ):
        raise RuntimeError("Worker não corresponde à identidade persistida no job")
    if job.get("status") not in {"PENDING", "RUNNING"}:
        return

    counters: dict[str, Any] = {
        "completed": int(job.get("completed", 0)),
        "failed": int(job.get("failed", 0)),
        "errors": list(job.get("errors") or []),
    }
    job.setdefault("llm_diagnostics", [])
    total_count = int(job.get("total_eligible", job.get("total", 0)))
    try:
        if not str(job.get("provider") or "").strip() or not str(job.get("model") or "").strip():
            raise ValueError("Job sem provider/model congelados da seleção atual do Hermes")
        job.update(status="RUNNING", worker_started_at=job.get("worker_started_at") or _utc_now())
        _persist(job)
        source_records = []
        for movement_id in list(job.get("movement_ids") or []):
            record = core_api.movement_analysis_v3_source_record(str(movement_id))
            if record is None or not str(record.get("source_text") or "").strip():
                raise ValueError(f"Movement sem conteúdo próprio para resumir: {movement_id}")
            source_records.append(record)

        calibrated_budget, calibration_chars = _analysis_v3_batch_char_budget()
        try:
            char_budget = int(os.environ.get("THEMIS_ANALYSIS_V3_BATCH_INPUT_CHARS", str(calibrated_budget)))
        except ValueError as exc:
            raise ValueError("THEMIS_ANALYSIS_V3_BATCH_INPUT_CHARS deve ser inteiro") from exc
        batches = partition_records_by_input_chars(source_records, char_budget=char_budget)
        by_id = {str(record["movement_id"]): record for record in source_records}
        job.update(
            batch_count=len(batches), input_char_budget=char_budget,
            calibration_process_id=_CALIBRATION_PROCESS_ID,
            calibration_input_chars=calibration_chars,
            batch_sizes=[structured_input_chars(batch) for batch in batches],
            completed=counters["completed"], failed=counters["failed"],
            pending=max(0, total_count - counters["completed"] - counters["failed"]),
        )
        _persist(job)

        for batch_idx, batch in enumerate(batches):
            if _is_cancel_requested(job):
                break
            batch_ids = [str(record["movement_id"]) for record in batch]
            job["current_batch"] = {"number": batch_idx + 1, "size": len(batch_ids), "movement_ids": batch_ids}
            _persist(job)
            await _run_summary_unit(job, batch_ids, by_id, llm, counters, total_count)
            if _is_cancel_requested(job):
                break
            job.update(current_batch=None, completed=counters["completed"], failed=counters["failed"], errors=list(counters["errors"]))
            _persist(job)

        cancelled = _is_cancel_requested(job)
        if cancelled:
            terminal = "FAILED"
            error = "Job cancelado pelo usuário após concluir a unidade em andamento."
        else:
            terminal = "COMPLETED" if counters["failed"] == 0 else ("PARTIAL" if counters["completed"] else "FAILED")
            error = counters["errors"][0]["error"] if counters["errors"] else None
        job.update(
            status=terminal, completed=counters["completed"], failed=counters["failed"],
            pending=max(0, total_count - counters["completed"] - counters["failed"]),
            errors=list(counters["errors"]), error=error,
            completed_at=_utc_now(), current_batch=None,
        )
        _persist(job)
    except Exception as exc:
        error = _error_text(exc)
        failed = max(counters["failed"], total_count - counters["completed"])
        job.update(
            status="PARTIAL" if counters["completed"] else "FAILED",
            completed=counters["completed"], failed=failed, pending=max(0, total_count - counters["completed"] - failed),
            errors=[*counters["errors"], {"error": error}], error=error,
            completed_at=_utc_now(), current_batch=None,
        )
        _persist(job)
        _LOGGER.exception("Worker do job de summaries %s falhou", job_id)


async def _wait_for_claim(process_id: str, job_id: str, worker_token: str) -> dict[str, Any] | None:
    deadline = time.monotonic() + _STARTUP_CLAIM_SECONDS
    while time.monotonic() < deadline:
        job = core_api.movement_analysis_v2_job(process_id, job_id)
        if job and job.get("worker_token") == worker_token and job.get("status") in {"PENDING", "RUNNING"}:
            if int(job.get("worker_pid") or 0) != os.getpid():
                # A Windows venv launcher can expose a shim PID to Popen while
                # the configured interpreter executes the script in a child.
                # The unique worker token identifies this one-shot child.
                job.update(
                    worker_pid=os.getpid(),
                    worker_started_at=_process_start_time(os.getpid()) or _utc_now(),
                )
                job = core_api.save_movement_analysis_v2_job_record(job)
            if int(job.get("worker_pid") or 0) == os.getpid():
                return job
        await asyncio.sleep(0.1)
    return None


async def worker_main(process_id: str, job_id: str, worker_token: str, *, llm: Any | None = None) -> int:
    job = await _wait_for_claim(process_id, job_id, worker_token)
    if job is None:
        return 3
    if llm is None:
        from agent.plugin_llm import PluginLlm
        llm = PluginLlm(plugin_id="themis")
    await run_process_summary_job(job_id, process_id, worker_token, llm)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--process-id", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--worker-token", required=True)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    return asyncio.run(worker_main(args.process_id, args.job_id, args.worker_token))


if __name__ == "__main__":
    raise SystemExit(main())
