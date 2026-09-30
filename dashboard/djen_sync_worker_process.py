"""Launch a detached DJEN sync worker, persisted in workspace.db."""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from core.process_storage import connect_workspace
from core.documentos import djen_sync_job_store_v1 as jobs
from dashboard.summary_worker_process import _process_start_time, worker_environment, worker_is_alive

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WORKER_SCRIPT = PLUGIN_ROOT / "dashboard" / "djen_sync_worker.py"


def launch_djen_sync_worker(job: dict) -> dict:
    db = connect_workspace(create=True)
    child = None
    try:
        db.execute("BEGIN IMMEDIATE")
        current = jobs.get(db, str(job["job_id"]))
        if current is None:
            raise RuntimeError("Job DJEN não existe no workspace.db")
        if current["status"] != "PENDING" or worker_is_alive(current.get("worker_pid"), current.get("worker_started_at")):
            db.commit()
            return current
        token = uuid.uuid4().hex
        argv = [sys.executable, str(WORKER_SCRIPT), "--job-id", str(job["job_id"]), "--worker-token", token]
        kwargs = {"cwd": str(PLUGIN_ROOT), "env": worker_environment(), "stdin": subprocess.DEVNULL,
                  "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "close_fds": True}
        if os.name == "nt":
            kwargs["creationflags"] = (getattr(subprocess, "DETACHED_PROCESS", 0x8) |
                                       getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200) |
                                       getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000))
        else:
            kwargs["start_new_session"] = True
        child = subprocess.Popen(argv, **kwargs)
        started_at = _process_start_time(int(child.pid))
        db.execute("UPDATE djen_sync_jobs SET worker_pid=?,worker_started_at=?,worker_token=? WHERE job_id=? AND status='PENDING'",
                   (int(child.pid), started_at, token, str(job["job_id"])))
        db.commit()
        current.update(worker_pid=int(child.pid), worker_started_at=started_at, worker_token=token)
        return current
    except Exception:
        db.rollback()
        if child is not None and child.poll() is None:
            child.terminate()
        raise
    finally:
        db.close()


def mark_start_failed(job: dict, error: Exception) -> dict:
    db = connect_workspace(create=True)
    try:
        job.update(status="FAILED", error=f"Não foi possível iniciar o worker DJEN: {error}"[:2000], completed_at=datetime.now(timezone.utc).isoformat())
        return jobs.save(db, job)
    finally:
        db.close()
