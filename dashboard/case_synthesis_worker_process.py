"""Start and observe the one-shot case-synthesis worker."""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from core.api import core_api
from core.documentos.case_synthesis_store_v1 import job as read_case_synthesis_job
from core.documentos.case_synthesis_store_v1 import migrate_connection as migrate_case_synthesis
from core.runtime_paths import process_db_path
from dashboard.summary_worker_process import (
    _process_start_time,
    worker_environment,
    worker_is_alive,
)


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WORKER_SCRIPT = PLUGIN_ROOT / "dashboard" / "case_synthesis_worker.py"


def launch_case_synthesis_worker(job: dict, *, command: Sequence[str] | None = None) -> dict:
    db_path = process_db_path(str(job["process_id"]))
    db = sqlite3.connect(str(db_path), timeout=10)
    db.row_factory = sqlite3.Row
    child = None
    try:
        migrate_case_synthesis(db)
        db.execute("BEGIN IMMEDIATE")
        current = read_case_synthesis_job(db, str(job["process_id"]), str(job["job_id"]))
        if current is None:
            raise RuntimeError("Job de síntese não existe no process.db")
        if current.get("status") != "PENDING":
            db.commit()
            return current
        if worker_is_alive(current.get("worker_pid"), current.get("worker_started_at")):
            db.commit()
            return current

        worker_token = uuid.uuid4().hex
        if command is not None:
            substitutions = {
                "{process_id}": str(job["process_id"]),
                "{job_id}": str(job["job_id"]),
                "{worker_token}": worker_token,
            }
            argv = [substitutions.get(str(item), str(item)) for item in command]
        else:
            argv = [
                sys.executable,
                str(WORKER_SCRIPT),
                "--process-id", str(job["process_id"]),
                "--job-id", str(job["job_id"]),
                "--worker-token", worker_token,
            ]
        kwargs = {
            "cwd": str(PLUGIN_ROOT),
            "env": worker_environment(),
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "close_fds": True,
        }
        if os.name == "nt":
            kwargs["creationflags"] = (
                getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
                | getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000)
            )
        else:
            kwargs["start_new_session"] = True
        child = subprocess.Popen(argv, **kwargs)
        started_at = _process_start_time(int(child.pid))
        updated_at = datetime.now(timezone.utc).isoformat()
        db.execute(
            """UPDATE case_synthesis_jobs
               SET worker_pid=?, worker_started_at=?, worker_token=?, updated_at=?
               WHERE process_id=? AND job_id=? AND status='PENDING'""",
            (int(child.pid), started_at, worker_token, updated_at, str(job["process_id"]), str(job["job_id"])),
        )
        db.commit()
        current.update(worker_pid=int(child.pid), worker_started_at=started_at, worker_token=worker_token, updated_at=updated_at)
        return current
    except Exception:
        db.rollback()
        if child is not None and child.poll() is None:
            child.terminate()
        raise
    finally:
        db.close()


def mark_case_synthesis_worker_start_failed(job: dict, error: Exception) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    job.update(
        status="FAILED",
        error=f"Não foi possível iniciar o worker da síntese: {error}",
        updated_at=now,
        completed_at=now,
    )
    return core_api.save_case_synthesis_job_record(job)


__all__ = ["launch_case_synthesis_worker", "mark_case_synthesis_worker_start_failed", "worker_is_alive"]
