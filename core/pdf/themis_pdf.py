"""Inspeção local, seletiva e somente leitura de PDFs jurídicos."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
except ImportError:
    PdfReader = None
    PdfReadError = Exception

# Compatível com importação como pacote e com execução direta do CLI.
try:
    from ..documentos.themis_documentos import Store, ingest as ingest_document, resolve_process as resolve_document_process, search_index, migrate_existing, forget_document, rebuild as rebuild_state, refresh_canonical_paths
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "documentos"))
    from themis_documentos import Store, ingest as ingest_document, resolve_process as resolve_document_process, search_index, migrate_existing, forget_document, rebuild as rebuild_state, refresh_canonical_paths

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

from core.runtime_paths import themis_data_root

TOOL_VERSION = "2.0.0"
PDFIUM_RENDER_VERSION = "0.9.3"
PDFIUM_VERSION = "151.0.7881.0 (build 7881)"
TOOL_DIR = Path(__file__).resolve().parent
PDFIUM_HELPER = TOOL_DIR / "pdfium" / "themis-pdf-pdfium.exe"


def get_state_root() -> Path:
    return themis_data_root()
MAX_PAGE_CHARS = 12_000
MAX_SEARCH_RESULTS = 100
MAX_CNJ_RESULTS = 200
UNICODE_MAP_ERROR_RATIO_BAD = 0.05
UNICODE_MAP_ERROR_MIN_CHARS = 8
CNJ_PATTERN = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")
WORDS = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]{2,}", re.UNICODE)
UNUSUAL_PUNCTUATION = set('!"#$%&*+<=>?@[\\]^_`{|}~')
HEADER_PATTERNS = {
    "Processo Digital": re.compile(r"\bProcesso\s+Digital\b", re.IGNORECASE),
    "Classe - Assunto": re.compile(r"\bClasse\s*-?\s*Assunto\b", re.IGNORECASE),
    "Requerente": re.compile(r"\bRequerente\b", re.IGNORECASE),
    "Requerido": re.compile(r"\bRequerido\b", re.IGNORECASE),
    "Vara": re.compile(r"\bVara\b", re.IGNORECASE),
    "Foro": re.compile(r"\bForo\b", re.IGNORECASE),
}
logging.getLogger("pypdf").setLevel(logging.ERROR)


class ToolError(Exception):
    def __init__(self, code: str, message: str, exit_code: int = 1) -> None:
        self.code, self.message, self.exit_code = code, message, exit_code
        super().__init__(message)


def emit(value: Any, stream: Any = sys.stdout) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str), file=stream)


def pdf_path(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ToolError("file_not_found", f"PDF não encontrado: {path}", 3)
    if path.suffix.lower() != ".pdf":
        raise ToolError("invalid_input", f"O arquivo não possui extensão .pdf: {path}", 2)
    return path


def open_pdf(path: Path, require_decryption: bool = True) -> Any:
    if PdfReader is None:
        try:
            import pypdfium2 as pdfium
            doc = pdfium.PdfDocument(str(path))
            class _PdfiumReaderWrapper:
                def __init__(self, doc_len: int):
                    self.is_encrypted = False
                    self.pages = [None] * doc_len
            wrapper = _PdfiumReaderWrapper(len(doc))
            doc.close()
            return wrapper
        except Exception as exc:
            raise ToolError("pdf_open_failed", f"Não foi possível ler o PDF via pdfium: {exc}", 4) from exc
    try:
        reader = PdfReader(path, strict=False)
    except (PdfReadError, OSError, ValueError) as exc:
        raise ToolError("pdf_open_failed", f"Não foi possível ler o PDF: {exc}", 4) from exc
    if reader.is_encrypted and require_decryption:
        raise ToolError("encrypted_pdf", "O PDF está criptografado; esta versão não tenta senha nem altera o arquivo.", 5)
    return reader


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def clipped(value: str, limit: int) -> tuple[str, bool]:
    return (value, False) if len(value) <= limit else (value[:limit].rstrip() + "…", True)


def context(text: str, start: int, end: int, radius: int = 110) -> str:
    return normalized(text[max(0, start - radius): min(len(text), end + radius)])


def quality_metrics(text: str, pdfium_signal: dict[str, Any] | None = None) -> dict[str, Any]:
    total = len(text)
    nonspace = [char for char in text if not char.isspace()]
    tokens = WORDS.findall(text)
    lines = text.splitlines()
    c0 = sum(ord(char) < 32 and char not in "\r\n\t" for char in text)
    printable = sum(char.isprintable() or char.isspace() for char in text)
    letters = sum(char.isalpha() for char in nonspace)
    digits = sum(char.isdigit() for char in nonspace)
    unusual = sum(char in UNUSUAL_PUNCTUATION for char in nonspace)
    long_runs = sum(len(run) >= 40 for run in re.split(r"\s+", text))
    base = len(nonspace)
    metrics = {
        "characters": total, "printable_ratio": printable / total if total else 0.0,
        "c0_controls": c0, "c0_ratio": c0 / total if total else 0.0,
        "replacement_chars": text.count("\ufffd"), "letter_ratio": letters / base if base else 0.0,
        "digit_ratio": digits / base if base else 0.0,
        "unusual_punctuation_ratio": unusual / base if base else 0.0,
        "recognized_words": len(tokens),
        "mean_token_length": sum(map(len, tokens)) / len(tokens) if tokens else 0.0,
        "long_unseparated_runs": long_runs, "lines": len(lines),
        "mean_line_length": statistics.mean(map(len, lines)) if lines else 0.0,
    }
    signal = pdfium_signal or {}
    total_chars = signal.get("total_chars")
    unicode_errors = signal.get("unicode_map_errors")
    unicode_zeros = signal.get("unicode_zero_count")
    if isinstance(total_chars, int) and isinstance(unicode_errors, int) and total_chars >= 0 and unicode_errors >= 0:
        metrics["total_chars"] = total_chars
        metrics["unicode_map_errors"] = unicode_errors
        metrics["unicode_map_error_ratio"] = unicode_errors / total_chars if total_chars else 0.0
    else:
        metrics["total_chars"] = None
        metrics["unicode_map_errors"] = None
        metrics["unicode_map_error_ratio"] = None
    metrics["unicode_zero_count"] = unicode_zeros if isinstance(unicode_zeros, int) and unicode_zeros >= 0 else None
    return metrics


def classify_quality(metrics: dict[str, Any], extraction_error: str | None) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if (
        metrics["unicode_map_errors"] is not None
        and metrics["unicode_map_errors"] >= UNICODE_MAP_ERROR_MIN_CHARS
        and metrics["unicode_map_error_ratio"] >= UNICODE_MAP_ERROR_RATIO_BAD
    ):
        return "BAD", ["TEXT_MAPPING_BAD"]
    if extraction_error:
        reasons.append("pdfium_extraction_error")
    if metrics["characters"] <= 24:
        reasons.append("empty_or_near_empty_text")
    if metrics["c0_controls"] >= 20 or metrics["c0_ratio"] >= 0.02:
        reasons.append("high_c0_control_ratio")
    if metrics["replacement_chars"]:
        reasons.append("unicode_replacement_characters")
    if metrics["characters"] >= 300 and metrics["letter_ratio"] < 0.20 and metrics["unusual_punctuation_ratio"] >= 0.08:
        reasons.append("low_letter_high_unusual_punctuation")
    if metrics["characters"] >= 500 and metrics["recognized_words"] < 12:
        reasons.append("low_recognized_word_density")
    if reasons:
        return "BAD", reasons
    suspect: list[str] = []
    if metrics["c0_controls"] > 1:
        suspect.append("c0_controls_present")
    if metrics["characters"] >= 250 and metrics["letter_ratio"] < 0.32 and metrics["unusual_punctuation_ratio"] >= 0.04:
        suspect.append("degraded_character_distribution")
    if metrics["characters"] >= 300 and metrics["recognized_words"] < 25:
        suspect.append("low_word_density")
    return ("SUSPECT", suspect) if suspect else ("OK", [])


def pdfium_pages(path: Path) -> list[dict[str, Any]]:
    if PDFIUM_HELPER.is_file():
        try:
            completed = subprocess.run(
                [str(PDFIUM_HELPER), "dump_pages", str(path)], capture_output=True,
                text=True, encoding="utf-8", errors="replace", check=False,
            )
            if completed.returncode == 0:
                result: list[dict[str, Any]] = []
                for line in completed.stdout.splitlines():
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if isinstance(row.get("page"), int) and isinstance(row.get("text"), str):
                        result.append(row)
                if result and [row["page"] for row in result] == list(range(1, len(result) + 1)):
                    return result
        except Exception:
            pass

    try:
        import pypdfium2 as pdfium
        if hasattr(pdfium, "PdfDocument"):
            doc = pdfium.PdfDocument(str(path))
            result = []
            for i in range(len(doc)):
                p = doc.get_page(i)
                tp = p.get_textpage()
                text = tp.get_text_range()
                result.append({
                    "page": i + 1,
                    "text": text,
                    "total_chars": len(text),
                    "unicode_map_errors": text.count("\ufffd"),
                    "unicode_zero_count": 0,
                })
            doc.close()
            return result
    except Exception:
        pass

    reader = open_pdf(path)
    result = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        result.append({
            "page": i + 1,
            "text": text,
            "total_chars": len(text),
            "unicode_map_errors": text.count("\ufffd"),
            "unicode_zero_count": 0,
        })
    return result


def hybrid_pages(path: Path, reader: PdfReader | None = None, include_visual_asset_sources: bool = False) -> list[dict[str, Any]]:
    from core.readable_markdown import pdfium_structural_pages

    raw_pages = pdfium_pages(path)
    structural_pages = pdfium_structural_pages(path, {row["page"] for row in raw_pages}, include_visual_asset_sources=include_visual_asset_sources)
    pages: list[dict[str, Any]] = []
    for row in raw_pages:
        metrics = quality_metrics(row["text"], row)
        quality, reasons = classify_quality(metrics, row.get("error"))
        structure = structural_pages.get(row["page"], {})
        final_quality = structure.get("quality") if structure.get("quality") in {"SCANNED", "NEED_OCR"} else quality
        pages.append({"page": row["page"], "content_markdown": structure.get("text", row["text"].strip()),
                      "structure": structure, "engine": "pdfium", "primary_engine": "pdfium",
                      "quality": final_quality, "fallback_used": False, "fallback_reason": reasons, "fallback_status": structure.get("fallback_status"), "quality_metrics": metrics})
    return pages


def extraction_summary(pages: list[dict[str, Any]]) -> dict[str, Any]:
    fallback = [page["page"] for page in pages if page["fallback_used"]]
    return {"primary_engine": "pdfium", "fallback_engine": None, "pdfium_page_count": len(pages) - len(fallback),
            "fallback_page_count": len(fallback), "fallback_pages": fallback}


def provenance(page: dict[str, Any], include_metrics: bool = True) -> dict[str, Any]:
    value = {key: page[key] for key in ("page", "engine", "primary_engine", "quality", "fallback_used", "fallback_reason")}
    if page["fallback_used"]:
        value["fallback_status"] = page["fallback_status"]
    if include_metrics:
        value["quality_metrics"] = page["quality_metrics"]
    return value


def metadata(reader: PdfReader) -> dict[str, str]:
    try:
        raw = reader.metadata or {}
    except Exception:
        return {}
    return {str(key): str(value) for key, value in raw.items() if value is not None}


def base_info(path: Path, reader: PdfReader, pages: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    encrypted = bool(reader.is_encrypted)
    result: dict[str, Any] = {"path": str(path), "size_bytes": path.stat().st_size, "pages": None if encrypted else len(reader.pages),
                              "encrypted": encrypted, "metadata": metadata(reader), "read_only": True}
    if encrypted:
        result["native_text_preliminary"] = "not_assessed_encrypted"
    elif pages is not None:
        sample_numbers = list(dict.fromkeys(n for n in [1, 2, 3, len(pages)] if 1 <= n <= len(pages)))
        result["native_text_preliminary"] = [{"page": n, "status": "available" if pages[n - 1]["content_markdown"] else "native_text_unavailable",
                                               "characters": len(pages[n - 1]["content_markdown"]), "engine": pages[n - 1]["engine"]} for n in sample_numbers]
        result["extraction"] = extraction_summary(pages)
    return result


def parse_interval(value: str, page_count: int) -> list[int]:
    result: list[int] = []
    for part in value.split(","):
        match = re.fullmatch(r"(\d+)(?:-(\d+))?", part.strip())
        if not match:
            raise ToolError("invalid_interval", f"Intervalo inválido: {value!r}", 2)
        start, end = int(match.group(1)), int(match.group(2) or match.group(1))
        if start < 1 or end < start or end > page_count:
            raise ToolError("invalid_interval", f"Intervalo fora de 1-{page_count}: {part}", 2)
        result.extend(range(start, end + 1))
    return list(dict.fromkeys(result))


def command_info(path: Path) -> dict[str, Any]:
    reader = open_pdf(path, require_decryption=False)
    if reader.is_encrypted:
        return {"command": "info", **base_info(path, reader)}
    pages = hybrid_pages(path, reader)
    return {"command": "info", **base_info(path, reader, pages), "tool_version": TOOL_VERSION,
            "pdfium": {"pdfium_render": PDFIUM_RENDER_VERSION, "pdfium": PDFIUM_VERSION}}


def command_pages(path: Path, interval: str) -> dict[str, Any]:
    reader = open_pdf(path)
    all_pages = hybrid_pages(path, reader)
    selected = parse_interval(interval, len(all_pages))
    pages = []
    for number in selected:
        record = all_pages[number - 1]
        excerpt, truncated = clipped(record["content_markdown"], MAX_PAGE_CHARS)
        pages.append({**provenance(record), "status": "available" if record["content_markdown"] else "native_text_unavailable", "text": excerpt, "truncated": truncated})
    return {"command": "pages", "path": str(path), "requested": interval, "pages": pages,
            "extraction": extraction_summary(all_pages), "read_only": True}


def command_search(path: Path, expression: str) -> dict[str, Any]:
    try:
        pattern = re.compile(expression, re.IGNORECASE)
    except re.error as exc:
        raise ToolError("invalid_regex", f"Regex inválida: {exc}", 2) from exc
    all_pages = hybrid_pages(path, open_pdf(path))
    found, unavailable, stopped = [], [], False
    for record in all_pages:
        text = record["content_markdown"]
        if not text:
            unavailable.append(record["page"]); continue
        for match in pattern.finditer(text):
            term, _ = clipped(match.group(0), 240)
            found.append({**provenance(record, False), "term": term, "context": context(text, match.start(), match.end())})
            if len(found) >= MAX_SEARCH_RESULTS:
                stopped = True; break
        if stopped: break
    return {"command": "search", "path": str(path), "expression": expression, "occurrences": found, "count": len(found),
            "truncated": stopped, "native_text_unavailable_pages": unavailable, "extraction": extraction_summary(all_pages), "read_only": True}


def command_cnj(path: Path) -> dict[str, Any]:
    all_pages = hybrid_pages(path, open_pdf(path))
    hits, unavailable, total = [], [], 0
    for record in all_pages:
        if not record["content_markdown"]:
            unavailable.append(record["page"]); continue
        for match in CNJ_PATTERN.finditer(record["content_markdown"]):
            total += 1
            if len(hits) < MAX_CNJ_RESULTS:
                hits.append({**provenance(record, False), "number": match.group(0), "context": context(record["content_markdown"], match.start(), match.end())})
    return {"command": "cnj", "path": str(path), "occurrences": hits, "count": total, "truncated": total > len(hits),
            "native_text_unavailable_pages": unavailable, "semantic_interpretation": "not_inferred", "extraction": extraction_summary(all_pages), "read_only": True}


def command_probe(path: Path) -> dict[str, Any]:
    reader = open_pdf(path); all_pages = hybrid_pages(path, reader)
    highlights: dict[str, list[dict[str, Any]]] = {name: [] for name in HEADER_PATTERNS}
    hits, unavailable, recommended, cnj_total = [], [], set(range(1, min(len(all_pages), 2) + 1)), 0
    recommended.update(range(max(1, len(all_pages) - 1), len(all_pages) + 1))
    for record in all_pages:
        text, number = record["content_markdown"], record["page"]
        if not text:
            unavailable.append(number); continue
        for match in CNJ_PATTERN.finditer(text):
            cnj_total += 1
            if len(hits) < MAX_CNJ_RESULTS: hits.append({**provenance(record, False), "number": match.group(0), "context": context(text, match.start(), match.end())})
            recommended.add(number)
        for name, pattern in HEADER_PATTERNS.items():
            match = pattern.search(text)
            if match and len(highlights[name]) < 8:
                highlights[name].append({**provenance(record, False), "context": context(text, match.start(), match.end(), 75)})
                recommended.add(number)
    samples = []
    for number in sorted(set(range(1, min(len(all_pages), 2) + 1)) | set(range(max(1, len(all_pages) - 1), len(all_pages) + 1))):
        record = all_pages[number - 1]; excerpt, truncated = clipped(normalized(record["content_markdown"]), 800)
        samples.append({**provenance(record, False), "status": "available" if record["content_markdown"] else "native_text_unavailable", "excerpt": excerpt, "truncated": truncated})
    return {"command": "probe", "info": base_info(path, reader, all_pages), "sample_pages": samples,
            "cnj": {"occurrences": hits, "count": cnj_total, "truncated": cnj_total > len(hits)},
            "headers": {name: values for name, values in highlights.items() if values},
            "pages_recommended_for_later_reading": sorted(recommended), "native_text_unavailable_pages": unavailable,
            "extraction": extraction_summary(all_pages), "read_only": True}


def command_ingest(path: Path | str, confirmed_case_id: str | None = None) -> dict[str, Any]:
    path = Path(path)
    try:
        store = Store(get_state_root()); migrate_existing(store)
        return ingest_document(path, lambda value: hybrid_pages(value, open_pdf(value), include_visual_asset_sources=True), store, confirmed_case_id,
                               {"tool_version": TOOL_VERSION, "pdfium_render": PDFIUM_RENDER_VERSION, "pdfium": PDFIUM_VERSION, "pypdf": "6.14.2"})
    except ValueError as exc:
        raise ToolError("document_registry_error", str(exc), 7) from exc


def command_resolve_process(document_id: str, process_id: str) -> dict[str, Any]:
    try:
        store = Store(get_state_root()); migrate_existing(store)
        return resolve_document_process(document_id.lower(), process_id, store)
    except ValueError as exc:
        raise ToolError("case_resolution_error", str(exc), 7) from exc


def command_rebuild() -> dict[str, Any]:
    try:
        return rebuild_state(Store(get_state_root()), TOOL_DIR.parents[2] / "01_Casos", lambda value: hybrid_pages(value, open_pdf(value)),
                             {"tool_version": TOOL_VERSION, "pdfium_render": PDFIUM_RENDER_VERSION, "pdfium": PDFIUM_VERSION, "pypdf": "6.14.2"})
    except ValueError as exc:
        raise ToolError("rebuild_error", str(exc), 7) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="themis-pdf", description="Inspeção local e somente leitura de PDFs.")
    parser.add_argument("command", choices=("info", "pages", "search", "cnj", "probe", "ingest", "resolve-process", "resolve-case", "search-index", "forget-document", "rebuild", "refresh-paths")); parser.add_argument("target", nargs="?")
    parser.add_argument("argument", nargs="?"); return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command in {"pages", "search"} and not args.argument:
        raise ToolError("missing_argument", f"O comando {args.command} exige um argumento adicional.", 2)
    if args.command in {"resolve-process", "resolve-case"} and not args.argument:
        raise ToolError("missing_argument", "O comando exige DOCUMENT_ID e PROCESS_ID.", 2)
    if args.command in {"info", "cnj", "probe", "forget-document", "rebuild", "refresh-paths"} and args.argument:
        raise ToolError("unexpected_argument", f"O comando {args.command} não aceita argumento adicional.", 2)
    if args.command not in {"rebuild", "refresh-paths"} and not args.target:
        raise ToolError("missing_argument", f"O comando {args.command} exige um argumento.", 2)
    if args.command == "rebuild":
        emit(command_rebuild()); return 0
    if args.command == "refresh-paths":
        emit(refresh_canonical_paths(Store(STATE_ROOT), TOOL_DIR.parents[2] / "01_Casos")); return 0
    if args.command == "forget-document":
        emit(forget_document(args.target.lower(), Store(STATE_ROOT))); return 0
    if args.command in {"resolve-process", "resolve-case"}:
        result=command_resolve_process(args.target, args.argument)
        if args.command == "resolve-case": result["deprecated_alias"]="resolve-case; use resolve-process"
        emit(result); return 0
    if args.command == "search-index":
        process_id = matter_id = None
        if args.argument:
            if args.argument.startswith("process:"): process_id=args.argument.removeprefix("process:")
            elif args.argument.startswith("matter:"): matter_id=args.argument.removeprefix("matter:")
            else: raise ToolError("invalid_scope", "Escopo de search-index deve ser process:<CNJ> ou matter:<MATTER_ID>.", 2)
        store=Store(STATE_ROOT); migrate_existing(store); emit(search_index(args.target, store, process_id, matter_id)); return 0
    path = pdf_path(args.target)
    commands = {"info": lambda: command_info(path), "pages": lambda: command_pages(path, args.argument),
                "search": lambda: command_search(path, args.argument), "cnj": lambda: command_cnj(path), "probe": lambda: command_probe(path),
                "ingest": lambda: command_ingest(path, args.argument)}
    emit(commands[args.command]()); return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ToolError as exc:
        emit({"error": exc.code, "message": exc.message}, sys.stderr); raise SystemExit(exc.exit_code)
    except Exception as exc:
        emit({"error": "unexpected_error", "message": str(exc)}, sys.stderr); raise SystemExit(1)
