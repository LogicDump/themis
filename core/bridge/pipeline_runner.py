"""Host-independent entry point for the captured-process pipeline."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from core.bridge.sync_service import process_captured_sync
from core.documentos.themis_documentos import Store
from core.runtime_paths import pdfium_helper_path, themis_data_root


def run_captured_pipeline(cnj: str, *, data_root: Path | None = None) -> dict[str, Any]:
    """Run the canonical pipeline using the Themis Core runtime contract.

    This is deliberately host-independent: Hermes' HTTP route and the local
    CLI are adapters over this same capability.  It does not start a server or
    mutate any path other than the selected Themis data root through the
    canonical ``process_captured_sync`` service.
    """
    if not isinstance(cnj, str) or not cnj.strip():
        raise ValueError("cnj é obrigatório")

    root = Path(data_root).resolve() if data_root is not None else themis_data_root()
    helper = pdfium_helper_path()
    if not helper.is_file():
        raise RuntimeError(f"Helper PDFium não encontrado: {helper}")
    os.environ["PDFIUM_HELPER_PATH"] = str(helper)

    return process_captured_sync(store=Store(root), cnj=cnj.strip())
