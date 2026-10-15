"""One cross-process, thread-reentrant lock for mutating a Process Package.

Uses the existing Hermes sync-lock namespace so previous and new workers exclude
each other. The OS releases the lock on process exit; no sentinel deletion.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
import threading
from contextlib import contextmanager
from functools import wraps
from inspect import signature
from pathlib import Path

_SLOTS_LOCK = threading.Lock()
_SLOTS: dict[str, "_Slot"] = {}


class ProcessBusyError(RuntimeError):
    """Another operation currently owns the Process Package."""


class _Slot:
    def __init__(self):
        self.guard = threading.RLock()
        self.depth = 0


@contextmanager
def process_operation_lock(cnj: str, data_root: Path | str):
    """Yield True if exclusive ownership was acquired, False if busy.

    A nested operation from the same thread can enter the same process/root.
    Other threads/processes cannot mutate the same package concurrently.
    """
    from core.runtime_paths import validate_process_id
    cnj = validate_process_id(cnj)
    root_key = str(Path(data_root).resolve()).casefold()
    name = hashlib.sha256(f"{root_key}|{cnj}".encode("utf-8")).hexdigest() + ".lock"
    lock_dir = Path(tempfile.gettempdir()) / "themis-process-sync-locks"
    lock_path = lock_dir / name
    key = str(lock_path)
    with _SLOTS_LOCK:
        slot = _SLOTS.setdefault(key, _Slot())
    if not slot.guard.acquire(blocking=False):
        yield False
        return
    handle = None
    try:
        if slot.depth:
            slot.depth += 1
            try:
                yield True
            finally:
                slot.depth -= 1
            return
        lock_dir.mkdir(parents=True, exist_ok=True)
        handle = lock_path.open("a+b")
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b"0")
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
            yield False
            return
        slot.depth = 1
        try:
            yield True
        finally:
            slot.depth = 0
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        if handle is not None:
            handle.close()
        slot.guard.release()


def require_process_operation(cnj: str, root: Path | str):
    """Alias for callers needing a named, documented exception on contention."""
    return process_operation_lock(cnj, root)


def guarded_process_mutation(fn):
    """Apply the canonical lock at a Core mutator's public boundary."""
    params = signature(fn)

    @wraps(fn)
    def guarded(*args, **kwargs):
        bound = params.bind(*args, **kwargs)
        store = bound.arguments["store"]
        cnj = bound.arguments["cnj"]
        with process_operation_lock(cnj, store.root) as acquired:
            if not acquired:
                raise ProcessBusyError(f"Processo {cnj} ocupado por outra operação")
            return fn(*args, **kwargs)

    return guarded
