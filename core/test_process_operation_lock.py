"""Exclusive per-process mutation gate shared by sync, rebuild and EG2 upgrade."""
import threading

from core.process_operation_lock import process_operation_lock


PID = "1234567-89.2026.8.26.0123"
OTHER = "1234567-89.2026.8.26.0124"


def test_reentrant_and_process_scoped(tmp_path):
    with process_operation_lock(PID, tmp_path) as first:
        assert first
        with process_operation_lock(PID, tmp_path) as nested:
            assert nested
        with process_operation_lock(OTHER, tmp_path) as different:
            assert different


def test_another_thread_is_rejected_but_released_afterward(tmp_path):
    attempted = threading.Event()
    release = threading.Event()
    outcome = []

    def contender():
        with process_operation_lock(PID, tmp_path) as acquired:
            outcome.append(acquired)
        attempted.set()
        release.wait(1)

    with process_operation_lock(PID, tmp_path) as acquired:
        assert acquired
        thread = threading.Thread(target=contender)
        thread.start()
        assert attempted.wait(2)
        assert outcome == [False]
        release.set()
    thread.join(timeout=2)
    assert not thread.is_alive()
    with process_operation_lock(PID, tmp_path) as acquired:
        assert acquired


def test_guarded_bridge_mutation_rejects_busy_process(tmp_path):
    from core.bridge.sync_service import ingest_bulk_zip
    from core.process_operation_lock import ProcessBusyError
    class Store:
        root = tmp_path
    acquired = threading.Event()
    release = threading.Event()
    def owner():
        with process_operation_lock(PID,tmp_path) as ok:
            assert ok
            acquired.set()
            assert release.wait(5)
    thread = threading.Thread(target=owner)
    thread.start()
    try:
        assert acquired.wait(3)
        import pytest
        with pytest.raises(ProcessBusyError):
            ingest_bulk_zip(Store(), PID, b"not-a-zip")
    finally:
        release.set()
        thread.join(timeout=5)
    assert not thread.is_alive()
