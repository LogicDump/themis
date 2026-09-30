"""Execute one persisted DJEN synchronization job outside the API process."""
from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone

from core.process_storage import connect_workspace
from core.documentos import djen_sync_job_store_v1 as jobs
from dashboard.summary_worker_process import _process_start_time


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(job_id: str, worker_token: str) -> int:
    job = None
    for _ in range(100):
        db = connect_workspace(create=True)
        try:
            job = jobs.get(db, job_id)
            if job and job.get("worker_token") == worker_token:
                if job.get("status") != "PENDING":
                    return 0
                pid = os.getpid()
                started_at = _process_start_time(pid)
                job.update(status="RUNNING", started_at=job.get("started_at") or _utc_now())
                db.execute("UPDATE djen_sync_jobs SET status='RUNNING',started_at=?,worker_pid=?,worker_started_at=? WHERE job_id=? AND status='PENDING' AND worker_token=?",
                           (job["started_at"], pid, started_at, job_id, worker_token))
                db.commit()
                break
        finally:
            db.close()
        time.sleep(0.05)
    else:
        return 2

    try:
        from core.documentos.djen_sync_v1 import sync_now
        result = sync_now(process_id=job.get("process_id"), available_to=job.get("available_to"))
        if not result.get("ok", False):
            errors = [str(item.get("error") or "Falha na sincronização") for item in result.get("results", []) if not item.get("ok")]
            job.update(status="FAILED", error="; ".join(errors)[:2000] or "A sincronização DJEN falhou.", result=result)
        else:
            job.update(status="COMPLETED", error=None, result=result)
    except Exception as exc:
        job.update(status="FAILED", error=str(exc)[:2000], result=None)
    job["completed_at"] = _utc_now()
    db = connect_workspace(create=True)
    try:
        jobs.save(db, job)
    finally:
        db.close()
    return 0 if job["status"] == "COMPLETED" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--worker-token", required=True)
    args = parser.parse_args()
    return run(args.job_id, args.worker_token)


if __name__ == "__main__":
    raise SystemExit(main())
