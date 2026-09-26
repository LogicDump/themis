"""Launch and observe the short-lived external Movement summary worker."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from core.api import core_api
from core.runtime_paths import process_db_path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WORKER_SCRIPT = PLUGIN_ROOT / "dashboard" / "movement_summary_worker.py"


def _hermes_agent_root() -> Path | None:
    try:
        spec = importlib.util.find_spec("agent")
        if spec and spec.origin:
            return Path(spec.origin).resolve().parent.parent
    except (ImportError, ValueError):
        pass
    return None


def worker_environment() -> dict[str, str]:
    env = os.environ.copy()
    if not env.get("HERMES_HOME"):
        from core.runtime_paths import get_default_hermes_home
        env["HERMES_HOME"] = str(get_default_hermes_home())
    paths = [str(PLUGIN_ROOT)]
    agent_root = _hermes_agent_root()
    if agent_root:
        paths.append(str(agent_root))
    paths.extend(item for item in env.get("PYTHONPATH", "").split(os.pathsep) if item)
    env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(paths))
    return env


def _process_start_time(pid: int) -> str | None:
    """Return the OS process creation time to detect a recycled Windows PID."""
    if os.name != "nt":
        try:
            return datetime.fromtimestamp(Path(f"/proc/{pid}").stat().st_ctime, timezone.utc).isoformat()
        except OSError:
            return datetime.now(timezone.utc).isoformat()
    import ctypes
    from ctypes import wintypes

    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.GetProcessTimes.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME),
        ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME),
    )
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.OpenProcess(0x1000, False, int(pid))
    if not handle:
        return None
    try:
        created, exited, kernel, user = FILETIME(), FILETIME(), FILETIME(), FILETIME()
        if not kernel32.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user)):
            return None
        ticks = (created.dwHighDateTime << 32) | created.dwLowDateTime
        epoch_seconds = (ticks - 116444736000000000) / 10_000_000
        return datetime.fromtimestamp(epoch_seconds, timezone.utc).isoformat()
    finally:
        kernel32.CloseHandle(handle)


def worker_is_alive(pid: int | None, started_at: str | None = None) -> bool:
    if not pid or int(pid) <= 0:
        return False
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(0x1000 | 0x00100000, False, int(pid))
        if not handle:
            return False
        try:
            code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value != 259:
                return False
            if started_at:
                actual = _process_start_time(int(pid))
                try:
                    expected_dt = datetime.fromisoformat(started_at)
                    actual_dt = datetime.fromisoformat(actual) if actual else None
                    if actual_dt and abs((actual_dt - expected_dt).total_seconds()) > 5:
                        return False
                except ValueError:
                    pass
            return True
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(int(pid), 0)
        return True
    except (ProcessLookupError, PermissionError):
        return isinstance(__import__("sys").exc_info()[1], PermissionError)
    except OSError:
        return False


def launch_summary_worker(
    job: dict,
    *,
    command: Sequence[str] | None = None,
) -> dict:
    """Atomically claim a persisted PENDING job and spawn its detached worker."""
    db_path = process_db_path(str(job["process_id"]))
    from core.documentos.movement_summary_store_v1 import analysis_v2_job

    db = sqlite3.connect(str(db_path), timeout=10)
    db.row_factory = sqlite3.Row
    child = None
    try:
        db.execute("BEGIN IMMEDIATE")
        current = analysis_v2_job(db, str(job["process_id"]), str(job["job_id"]))
        if current is None:
            raise RuntimeError("Job não existe no process.db")
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
            "UPDATE movement_analysis_v2_jobs SET worker_pid=?, worker_started_at=?, worker_token=?, updated_at=? WHERE process_id=? AND job_id=? AND status='PENDING'",
            (int(child.pid), started_at, worker_token, updated_at, str(job["process_id"]), str(job["job_id"])),
        )
        db.commit()
        current.update(worker_pid=int(child.pid), worker_started_at=started_at, worker_token=worker_token, updated_at=updated_at)
        return current
    except Exception:
        db.rollback()
        if child is not None and child.poll() is None:
            # The worker claim barrier will also exit if its PID/token was never committed.
            child.terminate()
        raise
    finally:
        db.close()

def mark_worker_start_failed(job: dict, error: Exception) -> dict:
    job.update(
        status="FAILED",
        pending=max(0, int(job.get("total_eligible", 0)) - int(job.get("completed", 0))),
        failed=max(0, int(job.get("total_eligible", 0)) - int(job.get("completed", 0))),
        error=f"Não foi possível iniciar o worker de summaries: {error}",
        completed_at=datetime.now(timezone.utc).isoformat(),
        current_batch=None,
    )
    return core_api.save_movement_analysis_v2_job_record(job)


__all__ = ["launch_summary_worker", "mark_worker_start_failed", "worker_is_alive"]
