"""Rebuildable readable projection using PDFium structural extraction only."""
from __future__ import annotations

import json
import os
import subprocess
import hashlib
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium

from core.pdfium_structuralizer import (
    deduplicate_recurring_furniture,
    extract_document_pages,
    extract_page_structure,
    mark_cross_page_continuity,
    mark_cross_page_table_continuity,
    normalize_tabular_markdown,
    VisualAssetSourceResolver,
)

# This value is persisted in each derived document manifest and is the sole
# cache-compatibility contract for a full structural extraction.  Bump it for
# any change that can alter the derived pages/structures.
EXTRACTION_PIPELINE_VERSION = "themis-pdfium-boundary-v2.0.4-textual-visual-regional-ocr-v1"
PIPELINE_VERSION = EXTRACTION_PIPELINE_VERSION

PDFIUM_HELPER = "PDFIUM_HELPER_PATH"
MAP_ERROR_RATIO = 0.05
MAP_ERROR_MIN = 8


def _configured_file(name: str) -> Path:
    value = os.environ.get(name)
    if not value or not Path(value).is_file():
        raise RuntimeError(f"{name} não configurado ou não encontrado")
    return Path(value)


def _run(args: list[str]) -> str:
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout


def pdfium_source_quality(pdf: Path, output: Path) -> dict[int, dict[str, Any]]:
    """Use the native FPDFText_HasUnicodeMapError signal, not text heuristics."""
    helper = _configured_file(PDFIUM_HELPER)
    rows = [json.loads(line) for line in _run([str(helper), "dump_pages", str(pdf)]).splitlines() if line.strip()]
    output.mkdir(parents=True, exist_ok=True)
    (output / "pdfium-pages.ndjson").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8"
    )
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        total, errors = row.get("total_chars", 0), row.get("unicode_map_errors", 0)
        ratio = errors / total if isinstance(total, int) and total else 0.0
        status = "BAD" if errors >= MAP_ERROR_MIN and ratio >= MAP_ERROR_RATIO else ("SCANNED" if not row.get("text", "").strip() else "GOOD")
        result[row["page"]] = {
            "source_quality": status,
            "source_reason": "TEXT_MAPPING_BAD" if status == "BAD" else None,
            "pdfium": {
                "total_chars": total,
                "unicode_map_errors": errors,
                "unicode_map_error_ratio": ratio,
                "unicode_zero_count": row.get("unicode_zero_count", 0),
            },
        }
    return result


_HERON_DETECTOR: Any = None
_HERON_INIT_ATTEMPTED: bool = False


def _get_heron_detector() -> Any:
    global _HERON_DETECTOR, _HERON_INIT_ATTEMPTED
    if _HERON_INIT_ATTEMPTED:
        return _HERON_DETECTOR
    _HERON_INIT_ATTEMPTED = True
    try:
        from core.heron_layout_adapter import HeronLayoutDetector
        _HERON_DETECTOR = HeronLayoutDetector()
    except Exception:
        _HERON_DETECTOR = None
    return _HERON_DETECTOR


def is_heron_fallback_enabled(explicit_flag: bool | None = None) -> bool:
    """Check feature flag for Heron fallback."""
    if explicit_flag is not None:
        return explicit_flag
    flag = os.environ.get("THEMIS_ENABLE_HERON_FALLBACK", "").strip().lower()
    if flag in {"0", "false", "no", "off", "disable", "disabled"}:
        return False
    return True


def pdfium_structural_pages(
    pdf: Path,
    page_numbers: set[int],
    include_visual_asset_sources: bool = False,
    enable_heron_fallback: bool | None = None,
) -> dict[int, dict[str, Any]]:
    """Deterministic structural extraction with calibrated selective Heron fallback."""
    digest = hashlib.sha256()
    with pdf.open("rb") as source_stream:
        for chunk in iter(lambda: source_stream.read(1024 * 1024), b""):
            digest.update(chunk)
    doc = pdfium.PdfDocument(str(pdf))
    try:
        source_resolver = VisualAssetSourceResolver(pdf, page_numbers) if include_visual_asset_sources else None
        return extract_document_pages(
            doc,
            page_numbers,
            source_resolver=source_resolver,
            enable_heron_fallback=enable_heron_fallback,
            document_id=digest.hexdigest(),
        )
    finally:
        doc.close()



def compose(pdf: Path, output: Path, enable_heron_fallback: bool | None = None) -> dict[str, Any]:
    """Compose an ordered derived projection using PDFium structuralizer with selective Heron fallback."""
    source = pdfium_source_quality(pdf, output)
    non_text_pages = [page for page, state in sorted(source.items()) if state["source_quality"] in {"BAD", "SCANNED"}]
    structural_pages = pdfium_structural_pages(pdf, set(source), enable_heron_fallback=enable_heron_fallback)


    pages, markdown = [], []
    for page, state in sorted(source.items()):
        table_models: list[dict[str, Any]] = []
        st = structural_pages.get(page, {"text": "", "furniture": [], "source_refs": []})
        text = st["text"]
        ocr_engines = st.get("ocr_engine") or []
        if isinstance(ocr_engines, str):
            ocr_engines = [ocr_engines]
        engine = "pdfium_structuralizer"
        if ocr_engines:
            engine += "+" + "+".join(sorted(set(ocr_engines)))
        refs = st.get("source_refs", [])
        removed_furniture = st.get("furniture", [])
        table_models = st.get("tables", [])

        readable_quality = st.get("quality", "GOOD" if text.strip() else "SUSPECT")
        start_offset = len("\n\n".join(markdown)) + (2 if markdown else 0)
        end_offset = start_offset + len(text)

        record = {
            "page": page,
            "source_quality": state["source_quality"],
            "source_reason": state["source_reason"],
            "readable_quality": readable_quality,
            "quality": readable_quality,
            "engine_used": engine,
            "text": text,
            "markdown_start_offset": start_offset,
            "markdown_end_offset": end_offset,
            "source_refs": refs,
            "removed_furniture": removed_furniture,
            "tables": table_models,
            "fallback_status": st.get("fallback_status"),
            "provenance": state["pdfium"],
            "page_category": st.get("page_category", "NATIVE_VALID"),
            "ocr_engine": ocr_engines,
            "ocr_provenance": st.get("ocr_provenance", []),
            "triage_metrics": st.get("triage_metrics", {}),
        }
        for continuity_key in ("continues_from_page", "continues_to_page", "logical_paragraph_id", "continuity_confidence"):
            if continuity_key in structural_pages.get(page, {}):
                record[continuity_key] = structural_pages[page][continuity_key]
        pages.append(record)
        markdown.append(text)

    mark_cross_page_table_continuity(pages)

    projection = {
        "pipeline_version": PIPELINE_VERSION,
        "pages": pages,
        "markdown": "\n\n".join(markdown).strip() + "\n",
        "source_refs": [ref for page in pages for ref in page["source_refs"]],
        "non_text_pages": non_text_pages,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "readable.json").write_text(json.dumps(projection, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "readable.md").write_text(projection["markdown"], encoding="utf-8")
    report = [
        f"# Readable Markdown {PIPELINE_VERSION}",
        "",
        "Engine Principal: PDFium Structuralizer",
        f"Páginas sem texto PDFium: {non_text_pages}",
        "",
        "| Página | Fonte | Leitura | Engine |",
        "|---|---|---|---|",
    ]
    report.extend(f"| {page['page']} | {page['source_quality']} | {page['readable_quality']} | {page['engine_used']} |" for page in pages)
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return projection
