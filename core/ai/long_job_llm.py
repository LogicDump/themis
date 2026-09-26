"""Shared timeout and diagnostic helpers for durable Themis LLM jobs."""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Awaitable


THEMIS_LONG_LLM_TIMEOUT_SECONDS = 300.0


class ThemisLongJobTimeout(TimeoutError):
    """Themis' wall-clock limit for one durable-job LLM call was reached."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _exception_chain(exc: BaseException):
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def is_timeout_exception(exc: BaseException) -> bool:
    for item in _exception_chain(exc):
        name = type(item).__name__.casefold()
        message = str(item).casefold()
        if isinstance(item, (TimeoutError, asyncio.TimeoutError)) or "timeout" in name or "timed out" in message:
            return True
    return False


def _response_and_status(exc: BaseException) -> tuple[Any | None, int | None, str | None]:
    response = None
    status = None
    request_id = None
    request_id_names = ("request_id", "_request_id", "requestid")
    request_header_names = ("x-request-id", "request-id", "x-goog-request-id", "x-amzn-requestid")
    for item in _exception_chain(exc):
        candidate = getattr(item, "response", None)
        if candidate is not None:
            response = response or candidate
            status = status or getattr(candidate, "status_code", None)
            headers = getattr(candidate, "headers", None)
            if headers:
                for key in request_header_names:
                    value = headers.get(key)
                    if value:
                        request_id = str(value)
                        break
        status = status or getattr(item, "status_code", None)
        for name in request_id_names:
            value = getattr(item, name, None)
            if value:
                request_id = str(value)
                break
    try:
        status = int(status) if status is not None else None
    except (TypeError, ValueError):
        status = None
    return response, status, request_id


def exception_diagnostics(exc: BaseException) -> dict[str, Any]:
    _, status, request_id = _response_and_status(exc)
    message = " ".join(str(exc).split())[:4000] or type(exc).__name__
    causes = [
        {"exception_type": type(item).__name__, "message": " ".join(str(item).split())[:2000]}
        for item in list(_exception_chain(exc))[1:5]
    ]
    return {
        "exception_type": type(exc).__name__,
        "message": message,
        "http_status": status,
        "request_id": request_id,
        "causes": causes,
    }


def begin_call_diagnostic(job: dict[str, Any], *, provider: str, model: str, operation: str) -> tuple[dict[str, Any], float]:
    diagnostic = {
        "operation": operation,
        "provider": provider,
        "model": model,
        "provider_model_source": "job_selection",
        "started_at": utc_now(),
        "ended_at": None,
        "elapsed_seconds": None,
        "status": "RUNNING",
        "exception_type": None,
        "message": None,
        "http_status": None,
        "request_id": None,
    }
    job.setdefault("llm_diagnostics", []).append(diagnostic)
    return diagnostic, time.monotonic()


def finish_call_diagnostic(
    diagnostic: dict[str, Any],
    started_monotonic: float,
    *,
    result: Any = None,
    error: BaseException | None = None,
) -> None:
    diagnostic["ended_at"] = utc_now()
    diagnostic["elapsed_seconds"] = round(max(0.0, time.monotonic() - started_monotonic), 3)
    if error is not None:
        details = exception_diagnostics(error)
        diagnostic.update(details)
        diagnostic["status"] = "TIMEOUT" if is_timeout_exception(error) else "FAILED"
        diagnostic["timeout_source"] = (
            "themis_long_job_deadline" if isinstance(error, ThemisLongJobTimeout)
            else ("hermes_or_provider" if is_timeout_exception(error) else None)
        )
        return
    provider = result.get("provider") if isinstance(result, dict) else getattr(result, "provider", None)
    model = result.get("model") if isinstance(result, dict) else getattr(result, "model", None)
    if provider:
        diagnostic["provider"] = str(provider)
        diagnostic["provider_model_source"] = "hermes_result"
    if model:
        diagnostic["model"] = str(model)
        diagnostic["provider_model_source"] = "hermes_result"
    diagnostic["status"] = "COMPLETED"


async def await_long_job_llm(awaitable: Awaitable[Any], *, timeout_seconds: float = THEMIS_LONG_LLM_TIMEOUT_SECONDS) -> Any:
    """Apply a Themis wall-clock bound in addition to passing it to ctx.llm."""
    started = time.monotonic()
    task = asyncio.ensure_future(awaitable)
    try:
        done, _ = await asyncio.wait({task}, timeout=timeout_seconds)
    except BaseException:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        raise
    if task not in done:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        raise ThemisLongJobTimeout(
            f"Themis long-job LLM timeout after {timeout_seconds:g}s"
        )
    try:
        return task.result()
    except Exception as exc:
        # Hermes' provider client can surface its own request timeout at the same
        # configured boundary, just before asyncio's outer timer fires.
        elapsed = time.monotonic() - started
        if is_timeout_exception(exc) and elapsed >= timeout_seconds * 0.98:
            raise ThemisLongJobTimeout(
                f"Themis long-job LLM timeout after {timeout_seconds:g}s"
            ) from exc
        raise


async def call_long_job_llm(
    llm: Any,
    method_name: str,
    *,
    timeout_seconds: float = THEMIS_LONG_LLM_TIMEOUT_SECONDS,
    **kwargs: Any,
) -> Any:
    """Invoke ctx.llm with Themis' explicit timeout and total wall-clock bound."""
    method = getattr(llm, method_name)
    kwargs["timeout"] = timeout_seconds
    return await await_long_job_llm(
        method(**kwargs), timeout_seconds=timeout_seconds
    )
