"""Regional OCR for pages routed to TEXTUAL_VISUAL by Page Triage."""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


class TextualVisualOcrUnavailable(RuntimeError):
    pass


def _windows_media_ocr(regions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    if os.name != "nt":
        raise TextualVisualOcrUnavailable("Windows.Media.Ocr is available only on Windows")
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        raise TextualVisualOcrUnavailable("Windows PowerShell was not found")
    worker = Path(__file__).with_name("windows_media_ocr_worker.ps1")
    payload = {
        "regions": [
            {
                "region_id": region["region_id"],
                "image_base64": base64.b64encode(region["image_bytes"]).decode("ascii"),
            }
            for region in regions
        ]
    }
    try:
        completed = subprocess.run(
            [powershell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(worker)],
            input=json.dumps(payload, separators=(",", ":")),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            timeout=180,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        result = json.loads(completed.stdout)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        raise TextualVisualOcrUnavailable(f"Windows.Media.Ocr failed: {detail}") from exc
    except Exception as exc:
        raise TextualVisualOcrUnavailable(f"Windows.Media.Ocr failed: {exc}") from exc
    if not result.get("ok"):
        raise TextualVisualOcrUnavailable("Windows.Media.Ocr worker returned an invalid response")
    return {str(row["region_id"]): row.get("lines", []) for row in result.get("regions", [])}


def _faster_paddle_ocr(regions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    try:
        from core.ocr.faster_paddle_adapter import get_ocr_engine
        engine = get_ocr_engine(model_size="small", rec_batch=32)
    except Exception as exc:
        raise TextualVisualOcrUnavailable(f"faster-paddle fallback is unavailable: {exc}") from exc
    output: dict[str, list[dict[str, Any]]] = {}
    for region in regions:
        result = engine.ocr(region["image_bytes"])
        lines = []
        for item in result.get("bounds", {}).values():
            text = str(item.get("text", "")).strip()
            if not text:
                continue
            lines.append({
                "text": text,
                "bbox_px": [
                    *item.get("topLeftCoord", [0, 0]),
                    *item.get("bottomRightCoord", [0, 0]),
                ],
                "confidence": float(item.get("confidence", 0.0)),
            })
        output[str(region["region_id"])] = lines
    return output


def recognize_textual_visual_regions(regions: list[dict[str, Any]]) -> dict[str, Any]:
    """OCR only supplied candidate crops; use faster-paddle for missing/failed Windows results."""
    if not regions:
        return {"engine": None, "regions": {}}
    try:
        windows_result = _windows_media_ocr(regions)
    except TextualVisualOcrUnavailable:
        windows_result = {}
    missing = [region for region in regions if not windows_result.get(str(region["region_id"]))]
    faster_result = _faster_paddle_ocr(missing) if missing else {}
    merged = {**windows_result, **faster_result}
    engine_by_region = {
        str(region["region_id"]): (
            "windows_media_ocr_pt-BR"
            if windows_result.get(str(region["region_id"]))
            else "faster_paddle_small"
        )
        for region in regions
        if merged.get(str(region["region_id"]))
    }
    return {"engine_by_region": engine_by_region, "regions": merged}
