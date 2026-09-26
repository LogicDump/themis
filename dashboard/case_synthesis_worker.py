"""One-shot process worker for durable case-synthesis jobs."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
from dataclasses import asdict, is_dataclass
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
)
from dashboard.summary_worker_process import _process_start_time
from dashboard.case_synthesis_contract import (
    CASE_SYNTHESIS_PROMPT_VERSION,
    CASE_SYNTHESIS_SCHEMA,
    case_synthesis_instructions,
    case_synthesis_records,
    validate_case_synthesis,
)


_LOGGER = logging.getLogger("themis.case_synthesis_worker")
_STARTUP_CLAIM_SECONDS = 20.0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _error_text(exc: Exception) -> str:
    text = re.sub(r"\s+", " ", str(exc)).strip()
    return text[:1000] or type(exc).__name__


def _persist(job: dict[str, Any]) -> dict[str, Any]:
    job["updated_at"] = _utc_now()
    return core_api.save_case_synthesis_job_record(job)


def _result_usage(result: Any) -> Any:
    usage = result.get("usage") if isinstance(result, dict) else getattr(result, "usage", None)
    return asdict(usage) if is_dataclass(usage) else usage


def _result_value(result: Any, key: str) -> Any:
    return result.get(key) if isinstance(result, dict) else getattr(result, key, None)


async def _wait_for_claim(process_id: str, job_id: str, worker_token: str) -> dict[str, Any] | None:
    deadline = time.monotonic() + _STARTUP_CLAIM_SECONDS
    while time.monotonic() < deadline:
        job = core_api.case_synthesis_job(process_id, job_id)
        if job and job.get("worker_token") == worker_token and job.get("status") in {"PENDING", "RUNNING"}:
            if int(job.get("worker_pid") or 0) != os.getpid():
                # A Windows venv launcher can expose a shim PID to Popen while
                # the configured interpreter executes the script in a child.
                # The unique worker token identifies this one-shot child.
                job.update(
                    worker_pid=os.getpid(),
                    worker_started_at=_process_start_time(os.getpid()) or _utc_now(),
                )
                job = core_api.save_case_synthesis_job_record(job)
            if int(job.get("worker_pid") or 0) == os.getpid():
                return job
        await asyncio.sleep(0.1)
    return None


async def run_case_synthesis_job(job_id: str, process_id: str, worker_token: str, llm: Any) -> None:
    job = core_api.case_synthesis_job(process_id, job_id)
    if (
        job is None or job.get("worker_token") != worker_token
        or int(job.get("worker_pid") or 0) != os.getpid()
    ):
        raise RuntimeError("Worker não corresponde à identidade persistida no job")
    if job.get("status") not in {"PENDING", "RUNNING"}:
        return

    diagnostic: dict[str, Any] | None = None
    try:
        if not str(job.get("provider") or "").strip() or not str(job.get("model") or "").strip():
            raise ValueError("Job sem provider/model congelados da seleção atual do Hermes")
        job.setdefault("llm_diagnostics", [])
        job.update(status="RUNNING", started_at=job.get("started_at") or _utc_now(), error=None)
        _persist(job)

        prepared = case_synthesis_records(process_id)
        if prepared is None:
            raise ValueError("Process not found")
        records, expected_ids, dependency_hash = prepared
        if len(records) != len(expected_ids):
            raise ValueError("Todos os Movements precisam possuir summary CURRENT válido")
        if not records:
            raise ValueError("O processo não possui Movement summaries CURRENT para sintetizar")

        job.update(dependency_hash=dependency_hash)
        _persist(job)
        diagnostic, diagnostic_started = begin_call_diagnostic(
            job, provider=str(job["provider"]), model=str(job["model"]), operation="case_synthesis"
        )
        _persist(job)
        call_kwargs = dict(
            instructions=case_synthesis_instructions(),
            input=[{"type": "text", "text": json.dumps({"movements": records}, ensure_ascii=False)}],
            json_schema=CASE_SYNTHESIS_SCHEMA,
            schema_name="themis_case_synthesis",
            provider=job["provider"],
            model=job["model"],
            max_tokens=4096,
            purpose="themis.case_synthesis",
        )
        try:
            result = await call_long_job_llm(
                llm,
                "acomplete_structured",
                timeout_seconds=THEMIS_LONG_LLM_TIMEOUT_SECONDS,
                **call_kwargs,
            )
        except Exception as exc:
            finish_call_diagnostic(diagnostic, diagnostic_started, error=exc)
            _persist(job)
            raise
        finish_call_diagnostic(diagnostic, diagnostic_started, result=result)
        _persist(job)
        parsed = validate_case_synthesis(_result_value(result, "parsed"), expected_ids)

        latest = core_api.case_synthesis_dependencies(process_id)
        if latest is None or latest[1] != dependency_hash or len(latest[0]) != len(records):
            raise RuntimeError("As dependências CURRENT do processo mudaram durante a geração")

        actual_provider = _result_value(result, "provider")
        actual_model = _result_value(result, "model")
        if not str(actual_provider or "").strip() or not str(actual_model or "").strip():
            raise RuntimeError("Hermes não informou provider/model efetivamente usados")
        job.update(provider=actual_provider, model=actual_model)
        core_api.complete_case_synthesis_job_record(
            job,
            case_synthesis_text=parsed["case_synthesis"],
            current_status=parsed["current_status"],
            pending_issues=parsed["pending_issues"],
            supporting_movement_ids=parsed["supporting_movement_ids"],
            prompt_version=CASE_SYNTHESIS_PROMPT_VERSION,
            dependency_hash_value=dependency_hash,
            usage=_result_usage(result),
        )
    except Exception as exc:
        now = _utc_now()
        message = _error_text(exc)
        if diagnostic is not None and diagnostic.get("status") == "TIMEOUT":
            message = f"TIMEOUT: {message}"
        job.update(status="FAILED", error=message, updated_at=now, completed_at=now)
        try:
            _persist(job)
        except Exception:
            _LOGGER.exception("Falha ao persistir estado terminal da síntese %s", job_id)
        _LOGGER.exception("Worker da síntese do processo %s falhou", process_id)


async def worker_main(process_id: str, job_id: str, worker_token: str, *, llm: Any | None = None) -> int:
    job = await _wait_for_claim(process_id, job_id, worker_token)
    if job is None:
        return 3
    if llm is None:
        from agent.plugin_llm import PluginLlm
        llm = PluginLlm(plugin_id="themis")
    await run_case_synthesis_job(job_id, process_id, worker_token, llm)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--process-id", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--worker-token", required=True)
    args = parser.parse_args(argv)
    return asyncio.run(worker_main(args.process_id, args.job_id, args.worker_token))


if __name__ == "__main__":
    raise SystemExit(main())
