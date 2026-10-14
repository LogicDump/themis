from types import SimpleNamespace
from unittest.mock import Mock
import subprocess

from dashboard import summary_worker_process as workers


def test_windows_worker_owns_hidden_console(monkeypatch):
    popen = Mock(return_value=object())
    monkeypatch.setattr(workers, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(workers, "worker_environment", lambda: {})
    monkeypatch.setattr(workers.subprocess, "Popen", popen)
    workers.spawn_background_worker(["python", "script.py"])
    opts = popen.call_args.kwargs
    flags = opts["creationflags"]
    assert flags & 0x08000000
    assert flags & 0x00000200
    assert flags & 0x01000000
    assert not flags & 0x00000008
    assert opts["stdin"] == subprocess.DEVNULL
    assert opts["stdout"] == subprocess.DEVNULL


def test_windows_worker_falls_back_on_breakaway_denied(monkeypatch):
    error = OSError("access denied")
    error.winerror = 5
    popen = Mock(side_effect=[error, object()])
    monkeypatch.setattr(workers, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(workers, "worker_environment", lambda: {})
    monkeypatch.setattr(workers.subprocess, "Popen", popen)
    workers.spawn_background_worker(["python", "script.py"])
    assert popen.call_count == 2
    flags = popen.call_args.kwargs["creationflags"]
    assert flags & 0x08000000
    assert not flags & 0x01000000
    assert not flags & 0x00000008


def test_posix_worker_starts_separate_session(monkeypatch):
    popen = Mock(return_value=object())
    monkeypatch.setattr(workers, "os", SimpleNamespace(name="posix"))
    monkeypatch.setattr(workers, "worker_environment", lambda: {})
    monkeypatch.setattr(workers.subprocess, "Popen", popen)
    workers.spawn_background_worker(["python", "script.py"])
    assert popen.call_args.kwargs["start_new_session"] is True
    assert "creationflags" not in popen.call_args.kwargs
