"""Themis dashboard plugin — backend API routes, mounted at /api/plugins/themis/."""
from __future__ import annotations

import base64
import asyncio
import contextlib
import json
import logging
import mimetypes
import os
import re
import sys
import threading
import uuid
import time
import hashlib
import tempfile
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import FileResponse

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from core.api import core_api
from core.bridge.pairing import setup_hermes_bridge_auth
from dashboard.movement_summary_batch_bakeoff import (
    complete_batch,
    normalize_structured_result,
    partition_records_by_input_chars,
)
from dashboard.case_synthesis_contract import (
    CASE_SYNTHESIS_SCHEMA,
    case_synthesis_instructions as _case_synthesis_instructions,
    validate_case_synthesis as _validate_case_synthesis,
)
from dashboard.case_synthesis_worker_process import (
    launch_case_synthesis_worker,
    mark_case_synthesis_worker_start_failed,
    worker_is_alive,
)
from dashboard.summary_worker_process import (
    launch_summary_worker,
    mark_worker_start_failed,
    worker_is_alive,
)
from dashboard.djen_sync_worker_process import launch_djen_sync_worker, mark_start_failed as mark_djen_worker_start_failed

# Backend bootstrap: migrations finish on the canonical writable database
# before any route can open its read-only query connection.
core_api.bootstrap_database()

# Registra automaticamente rotas de autenticação de token do bridge no Hermes
setup_hermes_bridge_auth()
register_token_route = None
try:
    # The experimental route is token-authable for the local bake-off runner;
    # keep this registration adjacent to the route because dashboard imports
    # can be isolated from the plugin Core package during host startup.
    from hermes_cli.dashboard_auth.token_auth import register_token_route
    register_token_route("/api/plugins/themis/experimental/movement-summary-batch")
except ImportError:
    pass
if register_token_route is not None:
    register_token_route("/api/plugins/themis/experimental/case-synthesis")


@contextlib.asynccontextmanager
async def _plugin_lifespan(app):
    await _resume_interrupted_process_syncs()
    yield


router = APIRouter(lifespan=_plugin_lifespan)
_LOGGER = logging.getLogger(__name__)

_FONT_ASSETS = {
    "fonts.css": "text/css; charset=utf-8",
    "InterVariable.woff2": "font/woff2",
    "InterVariable-Italic.woff2": "font/woff2",
    "RobotoMonoVariable.woff2": "font/woff2",
    "RobotoMonoVariable-Italic.woff2": "font/woff2",
}


@router.get("/assets/fonts/{filename}")
def get_font_asset(filename: str):
    """Serve bundled Themis fonts over the plugin HTTP origin.

    Desktop Chromium blocks direct file:// stylesheet loads. Restrict the route
    to the shipped font bundle so theme assets remain local without exposing an
    arbitrary filesystem path.
    """
    media_type = _FONT_ASSETS.get(filename)
    if media_type is None:
        raise HTTPException(status_code=404, detail="Font asset not found")
    path = PLUGIN_ROOT / "assets" / "fonts" / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Font asset not found")
    return FileResponse(path, media_type=media_type, filename=None)


_SUMMARY_JOBS_LOCK = threading.RLock()
_PROCESS_SYNC_TASKS: set[asyncio.Task[Any]] = set()
def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_is_active(status: Any) -> bool:
    return str(status or "").upper() in {"PENDING", "RUNNING"}


def _plugin_asset_root() -> Path:
    """Return the deployed plugin asset root, with a source-tree fallback."""
    deployed_root = Path(__file__).resolve().parents[1] / "assets"
    if deployed_root.is_dir():
        return deployed_root
    return Path(__file__).resolve().parents[1] / "plugins" / "themis" / "assets"


def _safe_plugin_asset_path(relative_path: str) -> Path:
    asset_root = _plugin_asset_root().resolve()
    candidate = (asset_root / relative_path).resolve()
    if not candidate.is_relative_to(asset_root) or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Plugin asset not found")
    return candidate


@router.get("/assets/{asset_path:path}")
def get_plugin_asset(asset_path: str):
    """Read-only access to packaged plugin assets, without directory traversal."""
    if not asset_path or asset_path.startswith(("/", "\\")):
        raise HTTPException(status_code=404, detail="Plugin asset not found")
    asset = _safe_plugin_asset_path(asset_path)
    media_type = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
    return {
        "content_base64": base64.b64encode(asset.read_bytes()).decode("ascii"),
        "content_type": media_type,
        "path": asset_path,
    }


@router.get("/health")
def health():
    return core_api.health()


@router.post("/embedding/warmup")
def warmup_embedding_model():
    """Start local EmbeddingGemma loading without waiting for ONNX startup."""
    try:
        from core.retrieval.onnx_embed import request_embedding_warmup
        return {"state": request_embedding_warmup()}
    except Exception as exc:
        _LOGGER.warning("EmbeddingGemma warm-up request failed: %s", exc)
        return {"state": "UNAVAILABLE"}


@router.post("/embedding/cancel_idle")
def cancel_idle_embedding_model():
    """Cancel pending idle unload timer when re-entering Pesquisa."""
    try:
        from core.retrieval.onnx_embed import cancel_embedding_unload
        return {"cancelled": cancel_embedding_unload()}
    except Exception as exc:
        _LOGGER.warning("EmbeddingGemma cancel idle request failed: %s", exc)
        return {"cancelled": False}


@router.post("/embedding/idle")
def idle_embedding_model():
    """Start the fixed 90-second idle window after leaving Pesquisa."""
    try:
        from core.retrieval.onnx_embed import schedule_embedding_unload, EMBEDDING_IDLE_TTL_SECONDS
        schedule_embedding_unload()
        return {"state": "IDLE", "ttl_seconds": EMBEDDING_IDLE_TTL_SECONDS}
    except Exception as exc:
        _LOGGER.warning("EmbeddingGemma idle request failed: %s", exc)
        return {"state": "UNAVAILABLE"}


@router.get("/tree")
def tree():
    return core_api.tree()


@router.get("/events")
def list_events(
    process_id: Optional[str] = None,
    kind: Optional[str] = None,
    query: Optional[str] = None,
):
    return core_api.list_events(process_id=process_id, kind=kind, query=query)


@router.get("/events/{event_id}")
def get_event(event_id: str):
    val = core_api.get_event(event_id)
    if val is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return val


@router.get("/processes/{process_id}/process-events")
def list_process_events(
    process_id: str,
    event_type: Optional[str] = None,
    date_precision: Optional[str] = None,
):
    """Diagnostic read model for observed temporal facts (ProcessEvent V1)."""
    return core_api.process_events(
        process_id,
        event_type=event_type,
        date_precision=date_precision,
    )


@router.get("/processes/{process_id}/deadline-instructions")
def list_deadline_instructions(
    process_id: str,
    status: Optional[str] = None,
    trigger_status: Optional[str] = None,
):
    """Diagnostic read model for explicit temporal instructions."""
    return core_api.deadline_instructions(
        process_id,
        status=status,
        trigger_status=trigger_status,
    )


@router.get("/processes/{process_id}/deadline-obligations")
def list_deadline_obligations(
    process_id: str,
    status: Optional[str] = None,
    recipient: Optional[str] = None,
):
    """Diagnostic read model for consolidated temporal obligations."""
    return core_api.deadline_obligations(
        process_id,
        status=status,
        recipient=recipient,
    )


@router.get("/processes/{process_id}/relations")
def list_process_relations(process_id: str):
    try:
        return core_api.process_relations(process_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/processes/{process_id}/participants")
def list_process_participants(process_id: str):
    """Structured participants only; textual mentions are not promoted here."""
    value = core_api.process_participants(process_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Process participants not found")
    return value


@router.get("/processes/{process_id}/representations")
def list_process_representations(process_id: str):
    value = core_api.process_representations(process_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Process representations not found")
    return value


@router.get("/professional-profile")
@router.get("/profile")
def get_professional_profile(profile_id: str = Query("profile_local_default")):
    return core_api.professional_profile(profile_id)


@router.put("/professional-profile")
@router.put("/profile")
def put_professional_profile(payload: dict[str, Any]):
    try:
        return core_api.save_professional_profile_record(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/processes/{process_id}/user-context")
def get_process_user_context(process_id: str, profile_id: str = Query("profile_local_default")):
    value = core_api.user_process_context(process_id, profile_id)
    if value is None:
        return None
    return value


@router.put("/processes/{process_id}/user-context")
def put_process_user_context(process_id: str, payload: dict[str, Any]):
    try:
        return core_api.save_user_process_context_record(process_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/processes/{process_id}")
def get_process(process_id: str):
    val = core_api.process(process_id)
    if val is None:
        raise HTTPException(status_code=404, detail="Process not found")
    return val


@router.delete("/processes/{process_id}")
@router.post("/processes/{process_id}/delete")
def delete_process(
    process_id: str,
    payload: dict[str, Any] | None = None,
    confirm_cnj: Optional[str] = Query(None),
):
    """Exclui atomicamente um processo, seus registros SQL, índices, vetores e diretórios."""
    confirm = confirm_cnj or (payload.get("confirm_cnj") if payload else None) or (payload.get("confirm_process_id") if payload else None)
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmação de CNJ obrigatória. Envie 'confirm_cnj' no corpo JSON ou query string correspondente ao processo.",
        )
    try:
        receipt = core_api.delete_process(process_id=process_id, confirm_process_id=str(confirm))
        return receipt
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir processo: {exc}")



@router.get("/processes/{process_id}/overview")
def get_process_overview(process_id: str):
    val = core_api.overview(process_id)
    if val is None:
        raise HTTPException(status_code=404, detail="Process overview not found")
    return val


@router.get("/processes/{process_id}/movements")
def get_process_movements(process_id: str):
    val = core_api.movements(process_id)
    if val is None:
        raise HTTPException(status_code=404, detail="Process movements not found")
    return val


def _llm_result(value: Any) -> tuple[str, str | None, str | None, Any]:
    """Normalize the Hermes ctx.llm.acomplete result without choosing a model."""
    def usage_json_value(usage: Any) -> Any:
        return asdict(usage) if is_dataclass(usage) else usage

    if isinstance(value, str):
        return value, None, None, None
    if isinstance(value, dict):
        text = value.get("text") or value.get("content") or value.get("output")
        if text is None and isinstance(value.get("message"), dict):
            text = value["message"].get("content")
        return str(text or ""), value.get("provider"), value.get("model"), usage_json_value(value.get("usage"))
    text = getattr(value, "text", None) or getattr(value, "content", None) or getattr(value, "output", None)
    return str(text or value), getattr(value, "provider", None), getattr(value, "model", None), usage_json_value(getattr(value, "usage", None))


def _movement_summary_error(exc: Exception) -> str:
    raw = str(exc)
    normalized = raw.casefold()
    capability_markers = (
        "capabilit",
        "trust gate",
        "consent",
        "provider_override",
        "model_override",
    )
    if any(marker in normalized for marker in capability_markers):
        return (
            "O Hermes não concedeu as capabilities de modelo do Themis (capability not granted). "
            "Execute `hermes plugins capabilities themis` e conceda "
            "llm.provider_override e llm.model_override quando solicitado."
        )
    return raw


def _load_process_summary_job(process_id: str, job_id: str | None = None) -> dict[str, Any] | None:
    """Read only the durable job row; never scan Movement or page content here."""
    return core_api.movement_analysis_v2_job(process_id, job_id)


def _request_llm(request: Request) -> Any:
    try:
        from themis_llm_bridge import resolve_runtime
        llm = resolve_runtime(request)
    except ImportError:
        llm = None
    if llm is None:
        raise HTTPException(status_code=503, detail="Runtime LLM do profile Hermes indisponível")
    return llm


def _llm_selection(payload: dict[str, Any], *, required: bool) -> tuple[str | None, str | None]:
    provider = str(payload.get("provider") or "").strip() or None
    model = str(payload.get("model") or "").strip() or None
    if (provider is None) != (model is None):
        raise HTTPException(status_code=422, detail="provider e model devem ser informados juntos")
    if required and provider is None:
        raise HTTPException(
            status_code=422,
            detail="Seleção provider/model atual do Hermes ausente; atualize a seleção do modelo e tente novamente",
        )
    return provider, model


@router.get("/movements/{movement_id}/summary")
def get_movement_summary(movement_id: str):
    val = core_api.movement_summary(movement_id)
    record = core_api.movement_analysis_v2_source_record(movement_id)
    job = None
    if record:
        latest = _load_process_summary_job(str(record["process_id"]))
        if latest and movement_id in set(latest.get("movement_ids") or []):
            job = latest
    if val is None:
        return {"movement_id": movement_id, "summary": None, "versions": [], "job": job}
    return {
        "movement_id": movement_id,
        "summary": val,
        "versions": core_api.movement_summary_versions_list(movement_id),
        "job": job,
    }


@router.get("/movements/{movement_id}/summary/jobs/{job_id}")
def get_movement_summary_job(movement_id: str, job_id: str):
    record = core_api.movement_summary_source_record(movement_id)
    job = _load_process_summary_job(str(record["process_id"]), job_id) if record else None
    if job is None or movement_id not in set(job.get("movement_ids") or []):
        raise HTTPException(status_code=404, detail="Job de resumo não encontrado")
    return job


@router.get("/processes/{process_id}/summaries/jobs/{job_id}")
async def get_process_summary_job(process_id: str, job_id: str):
    job = await asyncio.to_thread(core_api.movement_analysis_v2_job, process_id, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job processual de resumo não encontrado")
    if job.get("status") == "PENDING" and not worker_is_alive(job.get("worker_pid"), job.get("worker_started_at")):
        job = await _start_process_summary_worker(job)
    elif job.get("status") == "RUNNING" and not worker_is_alive(job.get("worker_pid"), job.get("worker_started_at")):
        completed = int(job.get("completed", 0))
        total = int(job.get("total_eligible", job.get("total", 0)))
        remaining = max(0, total - completed)
        job.update(
            status="PARTIAL" if completed else "FAILED",
            pending=remaining,
            failed=max(int(job.get("failed", 0)), remaining),
            error="Worker terminou antes de registrar estado terminal; resultados incrementais foram preservados.",
            completed_at=_utc_now(),
            current_batch=None,
        )
        job = await asyncio.to_thread(core_api.save_movement_analysis_v2_job_record, job)
    return job

@router.get("/processes/{process_id}/summaries")
def get_process_summaries(process_id: str):
    summaries = core_api.process_movement_summaries(process_id)
    if summaries is None:
        raise HTTPException(status_code=404, detail="Process not found")
    return {"summaries": summaries}


@router.get("/processes/{process_id}/summaries/status")
def get_process_summary_status(process_id: str):
    status = core_api.process_summary_status(process_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Process not found")
    return status


def _new_process_summary_job(process_id: str, movement_ids: list[str], total_eligible: int, payload: dict[str, Any]) -> dict[str, Any]:
    now = _utc_now()
    return {
        "job_id": uuid.uuid4().hex,
        "process_id": process_id,
        "status": "PENDING",
        "schema_version": "movement-summary-batch-v1",
        "total": len(movement_ids),
        "total_eligible": int(total_eligible),
        "completed": 0,
        "pending": len(movement_ids),
        "failed": 0,
        "movement_ids": list(movement_ids),
        "errors": [],
        "current_batch": None,
        "batch_count": 0,
        "provider": payload.get("provider"),
        "model": payload.get("model"),
        "force_all": bool(payload.get("force_all", False)),
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "worker_token": uuid.uuid4().hex,
        "cancel_requested": False,
    }


async def _start_process_summary_worker(job: dict[str, Any]) -> dict[str, Any]:
    """Persist and spawn from a helper thread so Gateway's event loop stays free."""
    def persist_and_spawn() -> dict[str, Any]:
        saved = core_api.create_movement_analysis_v2_job_if_absent(job)
        if saved.get("status") == "RUNNING" and worker_is_alive(saved.get("worker_pid"), saved.get("worker_started_at")):
            return saved
        if saved.get("status") == "RUNNING":
            completed = int(saved.get("completed", 0))
            remaining = max(0, int(saved.get("total_eligible", saved.get("total", 0))) - completed)
            saved.update(
                status="PARTIAL" if completed else "FAILED",
                pending=remaining,
                failed=max(int(saved.get("failed", 0)), remaining),
                error="Worker terminou antes de registrar estado terminal; resultados incrementais foram preservados.",
                completed_at=_utc_now(),
                current_batch=None,
            )
            return core_api.save_movement_analysis_v2_job_record(saved)
        if saved.get("status") not in {"PENDING", "RUNNING"}:
            return saved
        try:
            return launch_summary_worker(saved)
        except Exception as exc:
            return mark_worker_start_failed(saved, exc)
    return await asyncio.to_thread(persist_and_spawn)


@router.post("/processes/{process_id}/summaries", status_code=202)
async def generate_process_summaries(
    process_id: str,
    request: Request,
    payload: dict[str, Any] | None = None,
):
    del request  # Worker resolves the official Hermes PluginLlm facade itself.
    payload = payload or {}
    provider, model = _llm_selection(payload, required=True)
    force_all = payload.get("force_all", False)
    if not isinstance(force_all, bool):
        raise HTTPException(status_code=422, detail="force_all deve ser booleano explícito")
    existing = await asyncio.to_thread(_load_process_summary_job, process_id)
    if existing and _job_is_active(existing.get("status")):
        if worker_is_alive(existing.get("worker_pid"), existing.get("worker_started_at")):
            return existing
        if existing.get("status") == "PENDING":
            return await _start_process_summary_worker(existing)
        completed = int(existing.get("completed", 0))
        remaining = max(0, int(existing.get("total_eligible", existing.get("total", 0))) - completed)
        existing.update(status="PARTIAL" if completed else "FAILED", pending=remaining, failed=max(existing.get("failed", 0), remaining), current_batch=None, completed_at=_utc_now(), error="Worker terminou antes de registrar estado terminal.")
        await asyncio.to_thread(core_api.save_movement_analysis_v2_job_record, existing)

    query = await asyncio.to_thread(core_api.process_movement_summary_targets, process_id, force_all=force_all)
    movement_ids = query.get("movement_ids")
    if movement_ids is None:
        raise HTTPException(status_code=404, detail="Process not found")
    # Job totals describe only this run's eligible targets; process-wide totals
    # remain available from the compact summary-status endpoint.
    job = _new_process_summary_job(process_id, movement_ids, len(movement_ids), {**payload, "provider": provider, "model": model, "force_all": force_all})
    if not movement_ids:
        job.update(status="COMPLETED", completed=0, pending=0, completed_at=_utc_now())
        return await asyncio.to_thread(core_api.save_movement_analysis_v2_job_record, job)
    return await _start_process_summary_worker(job)


@router.post("/processes/{process_id}/summaries/jobs/{job_id}/cancel")
async def cancel_process_summary_job(process_id: str, job_id: str):
    job = await asyncio.to_thread(core_api.request_movement_analysis_v2_job_cancel, process_id, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job processual de resumo não encontrado")
    return job

@router.post("/movements/{movement_id}/summary", status_code=202)
async def generate_movement_summary(
    movement_id: str,
    request: Request,
    payload: dict[str, Any] | None = None,
):
    payload = payload or {}
    provider, model = _llm_selection(payload, required=True)

    record = await asyncio.to_thread(core_api.movement_summary_source_record, movement_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Movement not found")
    if not str(record.get("source_text") or "").strip():
        raise HTTPException(status_code=422, detail="Movement sem conteúdo próprio para resumir")
    process_id = str(record["process_id"])
    del request
    active = await asyncio.to_thread(_load_process_summary_job, process_id)
    if active and _job_is_active(active.get("status")):
        if movement_id in set(active.get("movement_ids") or []):
            if worker_is_alive(active.get("worker_pid"), active.get("worker_started_at")):
                return active
            if active.get("status") == "PENDING":
                return await _start_process_summary_worker(active)
        raise HTTPException(status_code=409, detail="Já existe um processamento de summaries em andamento para este processo")
    job = _new_process_summary_job(
        process_id,
        [movement_id],
        1,
        {"provider": provider, "model": model, "force_all": True},
    )
    return await _start_process_summary_worker(job)


@router.post("/experimental/movement-summary-batch")
async def generate_movement_summary_batch_bakeoff(
    request: Request,
    payload: dict[str, Any] | None = None,
):
    """Experimental, non-persisting multi-Movement bake-off endpoint."""
    payload = payload or {}
    movement_ids = payload.get("movement_ids")
    provider, model = _llm_selection(payload, required=False)
    try:
        llm = _request_llm(request)
        return await complete_batch(
            llm,
            movement_ids,
            core_api.movement_summary_source_record,
            provider=provider,
            model=model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha no batch experimental: {_movement_summary_error(exc)}") from exc


@router.get("/processes/{process_id}/case-synthesis")
def get_case_synthesis(process_id: str):
    dependencies = core_api.case_synthesis_dependencies(process_id)
    movements = core_api.movements(process_id)
    if dependencies is None or movements is None:
        raise HTTPException(status_code=404, detail="Process not found")
    current = core_api.case_synthesis(process_id)
    status = "MISSING" if current is None else ("CURRENT" if len(dependencies[0]) == len(movements) and current["dependency_hash"] == dependencies[1] else "STALE")
    return {
        "process_id": process_id,
        "status": status,
        "dependency_hash": dependencies[1],
        "movement_count": len(movements),
        "current_summary_count": len(dependencies[0]),
        "synthesis": current,
        "job": core_api.latest_case_synthesis_job_record(process_id),
        "versions": core_api.case_synthesis_versions_list(process_id),
    }


def _reconcile_case_synthesis_job(process_id: str, job_id: str) -> dict[str, Any] | None:
    job = core_api.case_synthesis_job(process_id, job_id)
    if job is None or job["status"] not in {"PENDING", "RUNNING"}:
        return job
    alive = worker_is_alive(job.get("worker_pid"), job.get("worker_started_at"))
    if alive:
        return job
    if job["status"] == "RUNNING":
        now = _utc_now()
        job.update(status="FAILED", error="Worker da síntese encerrou antes de concluir", updated_at=now, completed_at=now)
        return core_api.save_case_synthesis_job_record(job)
    try:
        return launch_case_synthesis_worker(job)
    except Exception as exc:
        return mark_case_synthesis_worker_start_failed(job, exc)


@router.get("/processes/{process_id}/case-synthesis/jobs/{job_id}")
async def get_case_synthesis_job(process_id: str, job_id: str):
    job = await asyncio.to_thread(_reconcile_case_synthesis_job, process_id, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job de síntese do caso não encontrado")
    result = dict(job)
    if job["status"] == "COMPLETED":
        result["synthesis"] = await asyncio.to_thread(core_api.case_synthesis, process_id)
    return result


@router.post("/processes/{process_id}/case-synthesis", status_code=202)
async def generate_case_synthesis(process_id: str, payload: dict[str, Any] | None = None):
    payload = payload or {}
    provider, model = _llm_selection(payload, required=True)
    now = _utc_now()
    record = {
        "job_id": uuid.uuid4().hex, "process_id": process_id, "status": "PENDING",
        "provider": provider, "model": model, "dependency_hash": None,
        "synthesis_id": None, "error": None, "created_at": now, "updated_at": now,
    }
    job, created = await asyncio.to_thread(core_api.create_case_synthesis_job_record, record)
    if job is None:
        raise HTTPException(status_code=404, detail="Process not found")
    if job["status"] == "PENDING":
        job = await asyncio.to_thread(_reconcile_case_synthesis_job, process_id, job["job_id"])
    return dict(job)


@router.post("/experimental/case-synthesis")
async def generate_case_synthesis_experiment(
    request: Request,
    payload: dict[str, Any] | None = None,
):
    payload = payload or {}
    process_id = str(payload.get("process_id") or "1029994-43.2023.8.26.0554").strip()
    movements = core_api.movements(process_id)
    if movements is None:
        raise HTTPException(status_code=404, detail="Process not found")
    records: list[dict[str, Any]] = []
    for movement in movements:
        movement_id = str(movement["movement_id"])
        summary = core_api.movement_summary(movement_id)
        if summary is None or not str(summary.get("summary_text") or "").strip():
            raise HTTPException(status_code=422, detail=f"Movement sem summary CURRENT válido: {movement_id}")
        records.append({
            "movement_id": movement_id,
            "occurred_at": movement.get("occurred_at") or movement.get("source_datetime"),
            "label": movement.get("movement_type") or movement.get("label") or "Movimentação",
            "summary_text": summary["summary_text"],
            "summary_version": summary["summary_version"],
        })
    expected_ids = {record["movement_id"] for record in records}
    if len(records) != 179 or len(expected_ids) != 179:
        raise HTTPException(status_code=422, detail=f"Esperados 179 Movements CURRENT únicos; recebidos {len(records)}")
    instructions = _case_synthesis_instructions()
    llm = _request_llm(request)
    started = time.perf_counter()
    try:
        provider, model = _llm_selection(payload, required=False)
        model_kwargs: dict[str, Any] = {}
        if provider is not None:
            model_kwargs["provider"] = provider
            model_kwargs["model"] = model
        result = await llm.acomplete_structured(
            instructions=instructions,
            input=[{"type": "text", "text": json.dumps({"movements": records}, ensure_ascii=False)}],
            json_schema=CASE_SYNTHESIS_SCHEMA,
            schema_name="themis_case_synthesis",
            max_tokens=4096,
            purpose="themis.case_synthesis",
            **model_kwargs,
        )
        parsed = result.get("parsed") if isinstance(result, dict) else getattr(result, "parsed", None)
        parsed = _validate_case_synthesis(parsed, expected_ids)
        usage = _llm_result(result)[3]
        actual_provider = result.get("provider") if isinstance(result, dict) else getattr(result, "provider", None)
        actual_model = result.get("model") if isinstance(result, dict) else getattr(result, "model", None)
        return {
            "process_id": process_id,
            "movement_count": len(records),
            "input_chars": len(json.dumps({"movements": records}, ensure_ascii=False)),
            "result": parsed,
            "provider": actual_provider,
            "model": actual_model,
            "usage": usage,
            "duration_ms": round((time.perf_counter() - started) * 1000),
            "source_movement_ids": [record["movement_id"] for record in records],
        }
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"Resultado estruturado inválido: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha na síntese experimental: {_movement_summary_error(exc)}") from exc


@router.get("/processes/{process_id}/procedural-acts")
@router.get("/processes/{process_id}/acts")
def get_process_procedural_acts(process_id: str):
    val = core_api.procedural_acts(process_id)
    if val is None:
        raise HTTPException(status_code=404, detail="Process procedural acts not found")
    return val


@router.get("/djen/status")
def get_djen_status():
    value = core_api.djen_status()
    job = value.get("active_job")
    if job:
        alive = worker_is_alive(job.get("worker_pid"), job.get("worker_started_at"))
        if job.get("status") == "PENDING" and not alive:
            try:
                launch_djen_sync_worker(job)
            except Exception as exc:
                mark_djen_worker_start_failed(job, exc)
        elif job.get("status") == "RUNNING" and not alive:
            from core.process_storage import connect_workspace
            from core.documentos import djen_sync_job_store_v1 as jobs
            db = connect_workspace()
            try:
                job.update(status="FAILED", error="Worker DJEN encerrou antes de concluir.", completed_at=_utc_now())
                jobs.save(db, job)
            finally:
                db.close()
        value = core_api.djen_status()
    return value


@router.get("/djen/jobs/{job_id}")
def get_djen_sync_job(job_id: str):
    job = core_api.djen_sync_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job DJEN não encontrado")
    if job.get("status") in {"PENDING", "RUNNING"}:
        alive = worker_is_alive(job.get("worker_pid"), job.get("worker_started_at"))
        if job.get("status") == "PENDING" and not alive:
            try:
                job = launch_djen_sync_worker(job)
            except Exception as exc:
                job = mark_djen_worker_start_failed(job, exc)
        elif job.get("status") == "RUNNING" and not alive:
            from core.process_storage import connect_workspace
            from core.documentos import djen_sync_job_store_v1 as jobs
            db = connect_workspace()
            try:
                job.update(status="FAILED", error="Worker DJEN encerrou antes de concluir.", completed_at=_utc_now())
                job = jobs.save(db, job)
            finally:
                db.close()
    return job


@router.post("/djen/sync-now")
async def sync_djen_now(payload: dict[str, Any] | None = None):
    process_id = str((payload or {}).get("process_id") or "").strip() or None
    available_to = str((payload or {}).get("available_to") or "").strip() or None
    try:
        def create_and_launch():
            job, created = core_api.create_djen_sync_job(process_id, available_to)
            if created or job.get("status") == "PENDING":
                try:
                    job = launch_djen_sync_worker(job)
                except Exception as exc:
                    job = mark_djen_worker_start_failed(job, exc)
            return {"job": job, "job_id": job["job_id"], "status": job["status"], "reused": not created}
        return await asyncio.to_thread(create_and_launch)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/processes/{process_id}/publications")
def get_process_publications(process_id: str):
    val = core_api.publications(process_id)
    if val is None:
        raise HTTPException(status_code=404, detail="Process not found")
    return val


@router.post("/processes/{process_id}/publications/sync")
def sync_process_publications(process_id: str, payload: dict[str, Any]):
    available_from = str(payload.get("available_from") or "").strip()
    available_to = str(payload.get("available_to") or "").strip()
    if not available_from or not available_to:
        raise HTTPException(status_code=400, detail="available_from e available_to são obrigatórios")
    try:
        return core_api.sync_publications(
            process_id,
            available_from=available_from,
            available_to=available_to,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/processes/{process_id}/autos")
def get_autos(
    process_id: str,
    offset: int = 0,
    limit: int | None = None,
    anchor_document_id: str | None = None,
    anchor_pdf_page: int | None = None,
    window_before: int = 10,
    window_after: int = 10,
):
    val = core_api.autos(
        process_id,
        offset=offset,
        limit=limit,
        anchor_document_id=anchor_document_id,
        anchor_pdf_page=anchor_pdf_page,
        window_before=window_before,
        window_after=window_after,
    )
    if val is None:
        raise HTTPException(status_code=404, detail="Autos not found")
    return val


@router.get("/processes/{process_id}/pdf")
def get_process_pdf(process_id: str):
    """Return the Core-resolved integral PDF for the whole process."""
    from core.runtime_paths import process_package_dir

    manifest_path = process_package_dir(process_id) / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=503, detail="O estado do pacote ainda não pode ser confirmado.") from exc
        pipeline_status = str(manifest.get("pipeline_status") or "").upper()
        if pipeline_status and pipeline_status != "READY":
            progress = manifest.get("pipeline_progress") or {}
            message = progress.get("message") or f"O processo está na etapa {progress.get('phase') or pipeline_status}."
            raise HTTPException(status_code=409, detail=f"O PDF integral estará disponível após o processamento. {message}")

    pdf_bytes = core_api.process_pdf_bytes(process_id)
    if pdf_bytes is None:
        raise HTTPException(status_code=404, detail="Process integral PDF not found")
    return {
        "process_id": process_id,
        "content_base64": base64.b64encode(pdf_bytes).decode("ascii"),
    }


@router.get("/documents/{document_id}/original")
def get_document_original(document_id: str):
    """Expose only the Core-resolved original path for the desktop OS door."""
    path = core_api.document_path(document_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Original document not found")
    return {"document_id": document_id, "path": str(path)}


@router.get("/documents/{document_id}/pdf")
def get_document_pdf(document_id: str):
    """Return the Core-resolved original for the plugin's internal PDF view."""
    path = core_api.document_path(document_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Original document not found")
    return {
        "document_id": document_id,
        "path": str(path),
        "content_base64": base64.b64encode(path.read_bytes()).decode("ascii"),
    }


@router.post("/retrieval/search")
def retrieval_search(payload: dict[str, Any]):
    """Busca híbrida de evidências nos Autos com citações e navegação."""
    process_id = payload.get("process_id")
    query = payload.get("query")
    top_k = payload.get("top_k", 5)
    if not process_id or not query:
        raise HTTPException(status_code=400, detail="process_id e query são obrigatórios")
    return core_api.retrieval_search(process_id=process_id, query=query, top_k=top_k)


@router.post("/retrieval/answer")
def retrieval_answer(payload: dict[str, Any]):
    """Gera resposta fundamentada com citações verificáveis vinculadas aos Autos."""
    process_id = payload.get("process_id")
    query = payload.get("query")
    top_k = payload.get("top_k", 5)
    if not process_id or not query:
        raise HTTPException(status_code=400, detail="process_id e query são obrigatórios")
    return core_api.retrieval_answer(process_id=process_id, query=query, top_k=top_k)


# ---------------------------------------------------------------------------
# Bridge Routes (Browser Bridge Themis <-> e-SAJ / Sincronização e Ingestão)
# ---------------------------------------------------------------------------


@router.get("/bridge/status")
def bridge_status():
    """Status do endpoint de bridge no backend Themis hospedado pelo Hermes."""
    return {
        "status": "ok",
        "app": "Themis Hermes Plugin Backend",
        "version": "1.2.0",
        "ingest_ready": True,
        "sync_ready": True,
    }


@router.post("/bridge/sync/plan")
def bridge_sync_plan(payload: dict[str, Any]):
    """Planeja sincronização de processo e-SAJ, identifica novas peças e persiste partes/movs."""
    cnj = payload.get("cnj")
    if not cnj:
        raise HTTPException(status_code=400, detail="cnj é obrigatório")

    from core.bridge.sync_service import plan_process_sync
    from core.documentos.themis_documentos import Store
    from core.runtime_paths import themis_data_root

    store = Store(themis_data_root())
    metadata = payload.get("metadata", {})
    page_context = payload.get("page_context") or payload.get("pageContext") or {}
    participants = payload.get("participants", [])
    movements = payload.get("movements", [])
    documents = payload.get("documents", [])
    cpopg = payload.get("cpopg")

    try:
        plan = plan_process_sync(
            store=store,
            cnj=cnj,
            metadata=metadata,
            participants=participants,
            movements=movements,
            documents=documents,
            page_context=page_context,
            cpopg=cpopg,
        )
        return plan
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao planejar sincronização: {exc}")


@router.post("/bridge/ingest")
def bridge_ingest(payload: dict[str, Any]):
    """Ingestão canônica de documentos PDF recebidos via Browser Bridge com proveniência e-SAJ."""
    cnj = payload.get("cnj")
    filename = payload.get("filename", "documento.pdf")
    content_b64 = payload.get("content_base64")
    metadata = payload.get("metadata", {})
    page_context = payload.get("page_context") or payload.get("pageContext") or {}

    if not cnj or not content_b64:
        raise HTTPException(status_code=400, detail="cnj e content_base64 são obrigatórios")

    try:
        pdf_bytes = base64.b64decode(content_b64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Base64 inválido: {exc}")

    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Arquivo inválido: assinatura %PDF não encontrada")

    parts_b64 = payload.get("parts_base64")
    parts_bytes = None
    if parts_b64 and isinstance(parts_b64, list):
        parts_bytes = []
        for pb in parts_b64:
            try:
                parts_bytes.append(base64.b64decode(pb))
            except Exception:
                pass

    from core.bridge.sync_service import ingest_bridge_document
    from core.documentos.themis_documentos import Store
    from core.runtime_paths import themis_data_root

    store = Store(themis_data_root())

    try:
        res = ingest_bridge_document(
            store=store,
            cnj=cnj,
            filename=filename,
            pdf_bytes=pdf_bytes,
            parts_bytes=parts_bytes,
            metadata=metadata,
            page_context=page_context,
        )
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao ingerir documento via bridge: {exc}")


@router.post("/bridge/sync/finish")
def bridge_sync_finish(payload: dict[str, Any]):
    """Finaliza a sincronização, reconcilia os Autos canônicos e retorna o resumo consolidado."""
    cnj = payload.get("cnj")
    if not cnj:
        raise HTTPException(status_code=400, detail="cnj é obrigatório")

    metadata = payload.get("metadata", {})
    page_context = payload.get("page_context") or payload.get("pageContext") or {}

    from core.bridge.sync_service import finish_process_sync
    from core.documentos.themis_documentos import Store
    from core.runtime_paths import themis_data_root

    store = Store(themis_data_root())

    try:
        result = finish_process_sync(
            store=store,
            cnj=cnj,
            metadata=metadata,
            page_context=page_context,
        )
        return result
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao finalizar sincronização: {exc}")


@router.post("/bridge/sync/zip")
async def bridge_sync_zip(
    request: Request,
    background_tasks: BackgroundTasks,
    cnj: str = Query(..., description="CNJ do processo no formato canônico"),
):
    """Recebe e valida o ZIP; extração/indexação seguem em tarefa de fundo."""
    if not cnj:
        raise HTTPException(status_code=400, detail="cnj é obrigatório")

    zip_bytes = await request.body()
    if not zip_bytes or len(zip_bytes) < 4 or not zip_bytes.startswith(b"PK"):
        raise HTTPException(status_code=400, detail="Arquivo inválido: assinatura ZIP (PK) não encontrada")

    from core.bridge.sync_service import _update_pipeline_progress, ingest_bulk_zip
    from core.documentos.themis_documentos import Store
    from core.runtime_paths import themis_data_root

    data_root = themis_data_root()
    store = Store(data_root).for_process(cnj)
    total_pages = 0
    try:
        total_pages = int(json.loads(store.process_manifest_path(cnj).read_text(encoding="utf-8")).get("total_physical_pages") or 0)
    except Exception:
        pass

    try:
        _update_pipeline_progress(store, cnj, "INGESTING", 0, total_pages)
        res = ingest_bulk_zip(
            store=store,
            cnj=cnj,
            zip_bytes=zip_bytes,
            run_pipeline=False,
        )
        background_tasks.add_task(_run_process_sync_background, cnj, str(data_root))
        return res
    except ValueError as val_err:
        _update_pipeline_progress(store, cnj, "ERROR", 0, total_pages, error_message=str(val_err))
        raise HTTPException(status_code=422, detail=str(val_err))
    except Exception as exc:
        _update_pipeline_progress(store, cnj, "ERROR", 0, total_pages, error_message=str(exc))
        raise HTTPException(status_code=500, detail=f"Erro ao processar pacote ZIP de bulk download: {exc}")


@contextlib.contextmanager
def _process_sync_file_lock(cnj: str, data_root: str):
    """Avoid two API workers processing the same captured package concurrently.

    The OS releases this lock if the Gateway/API process exits. Its stable path
    lets a newly started worker safely claim the interrupted job.
    """
    root_key = str(Path(data_root).resolve()).casefold()
    lock_name = hashlib.sha256(f"{root_key}|{cnj}".encode("utf-8")).hexdigest() + ".lock"
    lock_dir = Path(tempfile.gettempdir()) / "themis-process-sync-locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    handle = (lock_dir / lock_name).open("a+b")
    if handle.seek(0, os.SEEK_END) == 0:
        handle.write(b"\0")
        handle.flush()
    handle.seek(0)
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        yield False
        return
    try:
        yield True
    finally:
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def _run_process_sync_background(cnj: str, data_root: str) -> None:
    from core.bridge.sync_service import _update_pipeline_progress, process_captured_sync
    from core.documentos.themis_documentos import Store

    with _process_sync_file_lock(cnj, data_root) as acquired:
        if not acquired:
            _LOGGER.info("Pipeline do processo %s já está ativo em outro worker; execução duplicada ignorada", cnj)
            return
        store = Store(Path(data_root)).for_process(cnj)
        try:
            process_captured_sync(store=store, cnj=cnj)
        except Exception as exc:
            total_pages = 0
            manifest_path = store.process_manifest_path(cnj)
            try:
                total_pages = int(json.loads(manifest_path.read_text(encoding="utf-8")).get("total_physical_pages") or 0)
            except Exception:
                pass
            _update_pipeline_progress(store, cnj, "ERROR", 0, total_pages, error_message=str(exc))
            _LOGGER.exception("Pipeline de sync falhou para o processo %s", cnj)


def _interrupted_process_syncs(data_root: Path) -> list[str]:
    """Find captured packages whose API-owned worker vanished before READY."""
    from core.runtime_paths import validate_process_id

    process_root = Path(data_root) / "processos"
    candidates: list[str] = []
    if not process_root.is_dir():
        return candidates
    for package_dir in process_root.iterdir():
        if not package_dir.is_dir():
            continue
        try:
            cnj = validate_process_id(package_dir.name)
            manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
            progress = manifest.get("pipeline_progress") or {}
            status = str(manifest.get("pipeline_status") or progress.get("pipeline_status") or "").upper()
            if status not in {"PROCESSING", "QUEUED"} or progress.get("error"):
                continue
            if manifest.get("cnj") != cnj or not (package_dir / "fontes" / "pecas_manifest.json").is_file():
                continue
            candidates.append(cnj)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            _LOGGER.warning("Manifesto inválido ao procurar sync interrompido: %s", package_dir)
    return sorted(candidates)


async def _resume_interrupted_process_syncs() -> None:
    """Requeue durable package jobs after an API/Gateway restart."""
    from core.runtime_paths import themis_data_root

    root = themis_data_root()
    for cnj in _interrupted_process_syncs(root):
        task = asyncio.create_task(asyncio.to_thread(_run_process_sync_background, cnj, str(root)))
        _PROCESS_SYNC_TASKS.add(task)
        task.add_done_callback(_PROCESS_SYNC_TASKS.discard)
        _LOGGER.info("Retomando pipeline interrompido do pacote %s a partir dos fontes/checkpoints", cnj)


@router.get("/bridge/sync/status")
def bridge_sync_status(cnj: str = Query(..., description="CNJ canônico do processo")):
    from core.runtime_paths import process_package_dir

    manifest_path = process_package_dir(cnj) / "manifest.json"
    if not manifest_path.is_file():
        raise HTTPException(status_code=404, detail="Process Package ainda não possui manifesto")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Manifest do Process Package inválido: {exc}")
    progress = manifest.get("pipeline_progress") or {}
    status = manifest.get("pipeline_status") or progress.get("pipeline_status") or "CAPTURED"
    return {
        "status": "ok",
        "cnj": cnj,
        "pipeline_status": status,
        "progress": progress,
        "counts": manifest.get("counts") or {},
    }


@router.post("/bridge/sync/pipeline")
def bridge_sync_pipeline(payload: dict[str, Any]):
    """Executa o pipeline nativo de processamento, extração, autos, cronologia e embeddings de um processo capturado."""
    cnj = payload.get("cnj")
    if not cnj:
        raise HTTPException(status_code=400, detail="cnj é obrigatório")

    from core.bridge import pipeline_runner

    try:
        res = pipeline_runner.run_captured_pipeline(cnj)
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao executar pipeline do processo: {exc}")
