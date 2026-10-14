import io
import json
from core.pipeline_progress_console import PipelineProgressConsole, rebuild_report


def test_pipeline_progress_reads_canonical_manifest(tmp_path):
    output = io.StringIO()
    monitor = PipelineProgressConsole(output, tty=False, quiet_seconds=999)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"pipeline_progress": {
        "phase": "INDEXING", "completed_pages": 240, "total_pages": 354
    }}), encoding="utf-8")
    monitor._path = manifest
    monitor.poll_once()
    assert "240/354" in output.getvalue()
    assert "67%" in output.getvalue()
    monitor.finish()
    assert "Concluído" in output.getvalue()


def test_progress_keeps_indeterminate_phases_and_report():
    output = io.StringIO()
    monitor = PipelineProgressConsole(output, tty=False)
    monitor.update("STRUCTURING", 0, 354)
    assert "Estruturação" in output.getvalue()
    assert "0%" not in output.getvalue()
    report = rebuild_report({"status": "READY", "documents": 147, "pages": 354,
                             "embeddings": 354, "movements_before": 96,
                             "movements": 81, "backup": "backup"})
    assert "96 → 81" in report
    assert "354" in report


def test_incomplete_rebuild_report_does_not_claim_swap_or_backup():
    report = rebuild_report({"status": "INCOMPLETE", "changed": False, "staging": "isolated-stage"})
    assert "INCOMPLETE" in report and "sem swap" in report and "isolated-stage" in report
