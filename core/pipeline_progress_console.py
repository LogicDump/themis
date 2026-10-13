"""Lightweight CLI view of the canonical, persisted Themis pipeline progress.

The ingestion pipeline is the sole source of truth. This monitor never writes
to a Process Package and does not fabricate whole-pipeline percentages.
"""
from __future__ import annotations

import json
import shutil
import sys
import threading
import time
from pathlib import Path
from typing import TextIO

LABELS = {
    "VALIDATING": "Verificando PDFs",
    "COPYING": "Preparando pacote",
    "VALIDATED": "Fontes validadas",
    "QUEUED": "Na fila",
    "EXTRACTING": "Extração",
    "STRUCTURING": "Estruturação",
    "INDEXING": "Embeddings LiteRT",
    "FINALIZING": "Finalização",
    "VERIFYING": "Verificando resultado",
    "SWAPPING": "Substituindo pacote",
}
COUNTED = {"VALIDATING", "EXTRACTING", "INDEXING"}


def _duration(seconds: float) -> str:
    value = max(0, int(seconds))
    return f"{value // 3600:02d}:{(value // 60) % 60:02d}:{value % 60:02d}"


class PipelineProgressConsole:
    """Thread-safe, non-blocking observer for a pipeline manifest."""

    def __init__(self, stream: TextIO | None = None, *,
                 refresh_seconds: float = 0.5,
                 quiet_seconds: float = 15.0,
                 tty: bool | None = None) -> None:
        self.stream = stream if stream is not None else sys.stdout
        self.tty = bool(self.stream.isatty()) if tty is None else tty
        self.refresh_seconds = refresh_seconds
        self.quiet_seconds = quiet_seconds
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._path: Path | None = None
        self._start = time.monotonic()
        self._stage_start = self._start
        self._phase: str | None = None
        self._last_line = ""
        self._last_emit = self._start
        self._last_bucket = -1
        self._last_count: tuple[int, int] | None = None
        self._line_width = 0

    def _line(self, text: str, *, in_place: bool) -> None:
        if in_place and self.tty:
            columns = max(40, shutil.get_terminal_size(fallback=(100, 25)).columns)
            shown = text[:columns - 1]
            self.stream.write("\r" + shown + " " * max(0, self._line_width - len(shown)))
            self._line_width = len(shown)
        else:
            if self._line_width:
                self.stream.write("\n")
                self._line_width = 0
            self.stream.write(text + "\n")
        self.stream.flush()

    def update(self, phase: str, completed: int | None = None,
               total: int | None = None) -> None:
        """Render stage-local counts, never a misleading overall percentage."""
        now = time.monotonic()
        with self._lock:
            change = phase != self._phase
            if change:
                if self._phase is not None:
                    self._line(f"[Themis] {LABELS.get(self._phase, self._phase)} — "
                               f"{_duration(now - self._stage_start)}", in_place=False)
                self._phase = phase
                self._stage_start = now
                self._last_bucket = -1
                self._last_count = None
            label = LABELS.get(phase, phase)
            count = None
            bucket = -1
            if phase in COUNTED and completed is not None and total is not None and total > 0:
                done = max(0, int(completed))
                size = int(total)
                pct = min(100, int(100 * done / size))
                count = (done, size)
                bucket = pct // 10
                label = f"{label}: {done}/{size} páginas ({pct}%)" if phase != "VALIDATING" else (
                    f"{label}: {done}/{size} PDFs ({pct}%)")
            message = f"[Themis] {label} | {_duration(now - self._stage_start)}"
            render = change or (count is not None and count == (count[1], count[1]) and count != self._last_count) or now - self._last_emit >= (0.2 if self.tty else self.quiet_seconds) or (not self.tty and bucket > self._last_bucket)
            if render:
                self._line(message, in_place=self.tty)
                self._last_emit = now
                self._last_bucket = bucket
            self._last_count = count

    def watch(self, manifest: Path | None) -> None:
        """Observe only the canonical progress payload; no DB or source writes."""
        self.stop()
        self._path = Path(manifest) if manifest is not None else None
        self._stop.clear()
        self._thread = threading.Thread(target=self._poll, name="themis-progress", daemon=True)
        self._thread.start()
    def _poll(self) -> None:
        while not self._stop.is_set():
            self.poll_once()
            self._stop.wait(self.refresh_seconds)

    def poll_once(self) -> None:
        path = self._path
        if path is None:
            if self._phase is not None:
                count = self._last_count
                self.update(self._phase, *(count if count is not None else (None, None)))
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            progress = data.get("pipeline_progress") or {}
            phase = str(progress.get("phase") or "")
            if phase in LABELS:
                self.update(phase, progress.get("completed_pages"), progress.get("total_pages"))
        except (FileNotFoundError, PermissionError, ValueError, TypeError, OSError):
            # Transient file replacement or phase not yet persisted.
            return

    def stop(self) -> None:
        self._stop.set()
        worker = self._thread
        if worker is not None:
            worker.join(timeout=max(1.0, self.refresh_seconds * 3))
            self._thread = None
        self._path = None

    def finish(self, *, error: str | None = None) -> None:
        self.stop()
        now = time.monotonic()
        with self._lock:
            if self._phase is not None:
                self._line(f"[Themis] {LABELS.get(self._phase, self._phase)} — "
                           f"{_duration(now - self._stage_start)}", in_place=False)
                self._phase = None
            label = f"ERRO: {error}" if error else "Concluído"
            self._line(f"[Themis] {label} | Tempo total: {_duration(now - self._start)}", in_place=False)


def rebuild_report(result: dict) -> str:
    """Human-readable, factual final report; JSON remains the machine contract."""
    if result.get("status") == "DRY_RUN":
        return (f"[Themis] Auditoria: {result.get('pieces', 0)} peças, "
                f"{result.get('pdfs', 0)} PDFs íntegros. Nenhum dado alterado.")
    before = result.get("movements_before")
    after = result.get("movements")
    movement = f"{before} → {after}" if before is not None and after is not None else "não aferido"
    durations = result.get("durations_seconds") or {}
    timing = " · ".join(f"{name}: {seconds:.1f}s" for name, seconds in durations.items())
    return (
        f"[Themis] Documentos: {result.get('documents', '—')} | "
        f"Páginas: {result.get('pages', '—')} | "
        f"Embeddings: {result.get('embeddings', '—')} | "
        f"Movimentos: {movement}\n"
        f"[Themis] Etapas: {timing or 'sem medidas'}\n"
        f"[Themis] Backup: {result.get('backup', 'nenhum')}"
    )
