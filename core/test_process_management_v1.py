"""Independent process archiving and CLI contracts, with synthetic data only."""
import argparse
import sqlite3
from contextlib import closing
import pytest
from core.process_management_v1 import archive_process, restore_process, list_archived_processes, delete_process_permanently
from core.process_commands_v1 import register_management_cli

PID = "1234567-89.2026.8.26.0123"

def _package(root):
    path = root / "processos" / PID / "process.db"
    path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("CREATE TABLE processes(process_id TEXT PRIMARY KEY)")
        db.execute("INSERT INTO processes VALUES(?)",(PID,))
    return path

def test_archive_restore_preserve_contents(tmp_path):
    path=_package(tmp_path)
    original=path.read_bytes()
    assert list_archived_processes(root=tmp_path)==[]
    assert archive_process(PID,root=tmp_path)["changed"] is True
    assert archive_process(PID,root=tmp_path)["changed"] is False
    assert list_archived_processes(root=tmp_path)==[PID]
    assert path.read_bytes()==original
    assert restore_process(PID,root=tmp_path)["changed"] is True
    assert restore_process(PID,root=tmp_path)["changed"] is False
    assert list_archived_processes(root=tmp_path)==[]
    assert path.read_bytes()==original

def test_archive_rejects_missing_package(tmp_path):
    with pytest.raises(FileNotFoundError):
        archive_process(PID,root=tmp_path)

def test_delete_requires_exact_confirmation(tmp_path):
    path=_package(tmp_path)
    with pytest.raises(ValueError):
        delete_process_permanently(PID,"bad",root=tmp_path)
    assert path.exists()

def test_cli_commands_registered():
    p=argparse.ArgumentParser()
    subs=p.add_subparsers()
    register_management_cli(subs)
    for cmd in ("archive","restore","delete","archived"):
        args=[cmd]+([] if cmd=="archived" else [PID])
        if cmd=="delete": args+=["--confirm-cnj",PID]
        assert callable(p.parse_args(args).func)


def test_delete_does_not_affect_other_process_and_cleans_archive(tmp_path):
    from core.process_storage import register_discovery
    path = _package(tmp_path)
    other = tmp_path / "processos" / "1234567-89.2026.8.26.0124" / "untouched.txt"
    other.parent.mkdir(parents=True)
    other.write_text("keep", encoding="utf-8")
    register_discovery(PID, root=tmp_path)
    archive_process(PID, root=tmp_path)
    result = delete_process_permanently(PID, PID, root=tmp_path)
    assert result["status"] == "success"
    assert not path.parent.exists()
    assert other.read_text(encoding="utf-8") == "keep"
    assert list_archived_processes(root=tmp_path) == []
