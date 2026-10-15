"""EG2-only provisioning and idle lifecycle contracts (isolated, no downloads)."""
import json
import threading
from pathlib import Path

from core.retrieval import embeddinggemma2_litert as eg2


def test_pinned_manifest_has_only_eg2():
    manifest=json.loads((Path(__file__).resolve().parents[1]/"models_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["models"])==1
    item=manifest["models"][0]
    assert item["destination"].endswith(eg2.FILENAME)
    assert item["sha256"]==eg2.SHA256
    assert item["size_bytes"]>0
    assert manifest["source"]["revision"]==eg2.HF_REVISION


def test_cancel_idle_preserves_active_engine(monkeypatch):
    class FakeTimer:
        def __init__(self, interval, callback, args=()):
            self.callback=callback
            self.args=args
            self.cancelled=False
        def start(self): pass
        def cancel(self): self.cancelled=True
    with eg2._LOCK:
        original=(eg2._ENGINE,eg2._ENGINE_BACKEND,eg2._ENGINE_PATH,eg2._IDLE_TIMER,eg2._IDLE_GENERATION)
        try:
            monkeypatch.setattr(threading,"Timer",FakeTimer)
            eg2._ENGINE=None
            eg2._IDLE_TIMER=None
            eg2.schedule_embedding_unload()
            stale=eg2._IDLE_TIMER
            assert eg2.cancel_embedding_unload() is True
            assert stale.cancelled
            stale.callback(*stale.args)
            assert eg2._ENGINE is None
            assert eg2.cancel_embedding_unload() is False
        finally:
            eg2._ENGINE,eg2._ENGINE_BACKEND,eg2._ENGINE_PATH,eg2._IDLE_TIMER,eg2._IDLE_GENERATION=original
