"""Regression: validated source PDFs remain available during fresh-install processing."""
import hashlib
import io
import json

from pypdf import PdfReader, PdfWriter

from core.api import core_api
from core.bridge.sync_service import _persisted_provider_document_ids, plan_process_sync
from core.documentos.themis_documentos import Store

CNJ = "1234567-89.2026.8.26.0001"


def _pdf(pages):
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


def _capture(root, pdfs, state):
    source = root / "processos" / CNJ / "fontes"
    objects = source / "objetos"
    objects.mkdir(parents=True, exist_ok=True)
    pieces = []
    for ordinal, blob in enumerate(pdfs, 1):
        digest = hashlib.sha256(blob).hexdigest()
        (objects / f"{digest}.pdf").write_bytes(blob)
        pieces.append({
            "order": ordinal, "sha256": digest, "document_id": digest,
            "provider_item_identity": f"esaj:cdDocumento:{ordinal}:part:1",
        })
    (source / "pecas_manifest.json").write_text(json.dumps({
        "pecas": pieces,
        "validation": {"all_valid": True},
        "source_state_sha256": state,
        "total_entries": len(pieces),
    }), encoding="utf-8")
    return source


def test_one_original_is_available_before_process_db(tmp_path, monkeypatch):
    monkeypatch.setenv("THEMIS_DATA_ROOT", str(tmp_path))
    original = _pdf(1)
    _capture(tmp_path, [original], "a" * 64)
    assert core_api.process_pdf_bytes(CNJ) == original


def test_multi_original_rebuilds_when_capture_changes(tmp_path, monkeypatch):
    monkeypatch.setenv("THEMIS_DATA_ROOT", str(tmp_path))
    _capture(tmp_path, [_pdf(1), _pdf(2)], "a" * 64)
    output = core_api.process_pdf_bytes(CNJ)
    assert len(PdfReader(io.BytesIO(output)).pages) == 3
    _capture(tmp_path, [_pdf(1), _pdf(3)], "b" * 64)
    updated = core_api.process_pdf_bytes(CNJ)
    assert len(PdfReader(io.BytesIO(updated)).pages) == 4
    assert updated != output


def test_missing_original_not_marked_as_downloaded(tmp_path):
    source = _capture(tmp_path, [_pdf(1)], "a" * 64)
    for original in (source / "objetos").glob("*.pdf"):
        original.unlink()
    store = Store(tmp_path, process_id=CNJ)
    assert _persisted_provider_document_ids(store, CNJ) == {}
    assert core_api._source_process_pdf_path(CNJ, store.db_path) is None


def test_zero_new_sync_does_not_reset_ready_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr("core.bridge.sync_service._materialize_movements_with_projection_policy", lambda *a, **k: {"projection_repair_applied": False})
    store = Store(tmp_path, process_id=CNJ)
    package = store.process_path(CNJ)
    package.mkdir(parents=True, exist_ok=True)
    (package / "manifest.json").write_text(json.dumps({
        "cnj": CNJ, "status": "READY", "pipeline_status": "READY",
        "pipeline_progress": {"phase": "READY"},
        "counts": {"documents": 1},
    }), encoding="utf-8")
    plan = plan_process_sync(store, CNJ, documents=[], metadata={})
    state = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    assert plan["needed_count"] == 0
    assert state["pipeline_status"] == "READY"
    assert state["pipeline_progress"]["phase"] == "READY"
    assert state["counts"]["documents"] == 1

def test_bounded_range_matches_one_integral_pdf(tmp_path, monkeypatch):
    monkeypatch.setenv("THEMIS_DATA_ROOT", str(tmp_path))
    from dashboard import plugin_api
    import base64

    _capture(tmp_path, [_pdf(2), _pdf(3)], "a" * 64)
    full = core_api.process_pdf_bytes(CNJ)
    meta = plugin_api.get_process_pdf_meta(CNJ)
    assert meta["size"] == len(full)
    slices = []
    for start in range(0, len(full), 65536):
        end = min(len(full), start + 65536)
        part = plugin_api.get_process_pdf_range(CNJ, start=start, end=end, version=meta["version"])
        assert part["start"] == start
        slices.append(base64.b64decode(part["content_base64"]))
    assert b"".join(slices) == full
    assert len(PdfReader(io.BytesIO(full)).pages) == 5

def test_range_rejects_invalid_limits_or_old_version(tmp_path, monkeypatch):
    monkeypatch.setenv("THEMIS_DATA_ROOT", str(tmp_path))
    from dashboard import plugin_api
    from fastapi import HTTPException

    _capture(tmp_path, [_pdf(2), _pdf(3)], "b" * 64)
    meta = plugin_api.get_process_pdf_meta(CNJ)
    for args in (
        {"start": 0, "end": 262145, "version": meta["version"]},
        {"start": 12, "end": 12, "version": meta["version"]},
        {"start": 0, "end": 1, "version": "0" * 64},
    ):
        try:
            plugin_api.get_process_pdf_range(CNJ, **args)
        except HTTPException as exc:
            assert exc.status_code in (409, 422)
        else:
            raise AssertionError("Faixa inválida aceita")


def test_integral_page_order(tmp_path, monkeypatch):
    monkeypatch.setenv("THEMIS_DATA_ROOT", str(tmp_path))
    originals = []
    for width in (511, 612, 713):
        writer = PdfWriter()
        writer.add_blank_page(width=width, height=792)
        output = io.BytesIO()
        writer.write(output)
        originals.append(output.getvalue())
    _capture(tmp_path, originals, "c" * 64)
    pages = PdfReader(io.BytesIO(core_api.process_pdf_bytes(CNJ))).pages
    assert [int(page.mediabox.width) for page in pages] == [511, 612, 713]
