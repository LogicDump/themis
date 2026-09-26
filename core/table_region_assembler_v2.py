"""Offline V2 table-region diagnostics with transient PDFium glyph geometry.

The canonical database is opened immutable/read-only.  ``GlyphRun`` objects
are re-derived from source PDFs and live only while this command runs; neither
``pages.content`` nor ``structure_json`` is modified.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

try:
    from core.runtime_paths import index_db_path
except ModuleNotFoundError:
    from runtime_paths import index_db_path
from typing import Any

import onnxruntime as ort
import pypdfium2 as pdfium

THEMIS_ROOT = Path(__file__).resolve().parents[1]
if str(THEMIS_ROOT) not in sys.path:
    sys.path.insert(0, str(THEMIS_ROOT))

from core.pdfium_structuralizer import extract_page_glyph_runs
from core import table_region_assembler_v0 as v0
from core import table_region_assembler_v1 as v1



def _source_path(db: sqlite3.Connection, data_root: Path, document_id: str) -> Path:
    canonical = data_root / "documentos" / document_id / "source.pdf"
    if canonical.is_file():
        return canonical
    # External holdouts may predate materialization under documentos/.  The
    # registered file path is still immutable source input and is read only.
    row = db.execute("SELECT path FROM files WHERE sha256=?", (document_id,)).fetchone()
    return Path(row["path"]) if row and row["path"] else canonical


def _glyph_runs_for_page(
    documents: dict[str, Any], db: sqlite3.Connection, data_root: Path, document_id: str, pdf_page: int,
) -> tuple[dict[int, list[Any]], str | None]:
    path = _source_path(db, data_root, document_id)
    if not path.is_file():
        return {}, f"source_not_found:{path}"
    try:
        document = documents.setdefault(document_id, pdfium.PdfDocument(str(path)))
        page = document.get_page(pdf_page - 1)
        try:
            textpage = page.get_textpage()
            return extract_page_glyph_runs(page.raw, textpage.raw, pdf_page), None
        finally:
            page.close()
    except Exception as exc:
        return {}, f"pdfium:{type(exc).__name__}:{exc}"


def _glyph_summary(page: dict[str, Any]) -> dict[str, Any]:
    evidence = [item for region in page["candidate_regions"] for item in region.get("line_evidence", [])]
    return {
        "candidate_line_count": len(evidence),
        "candidate_lines_with_glyph_runs": sum(bool(item.get("glyph_run_count")) for item in evidence),
        "candidate_lines_with_recurring_x": sum(bool(item.get("has_recurring_x_alignment")) for item in evidence),
    }


def _promote_spatial_glyph_seeds(page: dict[str, Any]) -> int:
    """Expose isolated, high-confidence glyph rows to the existing V1 merger.

    PDFium reading order can put intervening labels between two physical table
    rows.  V0 correctly rejects those rows as sequential singletons; V2 makes
    them spatial fragments, which V1 may join only through its established 2D
    compatibility checks.  No text value is used here.
    """
    represented = {line_id for region in page["candidate_regions"] for line_id in region["line_ids"]}
    isolated_ids = {
        line_id
        for rejected in page["rejected_activations"]
        if rejected.get("reason") == "isolated_activation"
        for line_id in rejected["line_ids"]
    }
    potential: list[dict[str, Any]] = []
    for line in page.get("line_diagnostics", []):
        if (
            line["line_id"] in represented
            or line["line_id"] not in isolated_ids
            or line["p_table"] < v0.TABLE_SEED_THRESHOLD
            or not line.get("has_glyph_columnar_gap")
            # A compact binary field may corroborate an already detected
            # region, but is not enough to create one by itself.
            or line.get("glyph_run_count", 0) < 5
            # One coincidental X start is common in prose; two independent
            # recurring starts establish a column pattern without text rules.
            or line.get("recurring_x_alignment_count", 0) < 2
        ):
            continue
        potential.append({
            "bbox": line["bbox"],
            "line_ids": [line["line_id"]],
            "line_indexes": [line["line_index"]],
            "confidence": "strong" if line["p_table"] >= v0.STRONG_THRESHOLD else "ambiguous",
            "boundary_probabilities": [],
            "geometry_evidence": {
                "mean_p_table": line["p_table"],
                "max_p_table": line["p_table"],
                "columnar_line_count": 1,
                "row_band_count": 1,
                "seed_basis": "glyph_runs+recurring_x_alignment+aux_is_table",
            },
            "line_evidence": [line],
        })
    page_width = float(page["page_geometry"]["width"])
    page_height = float(page["page_geometry"]["height"])
    admitted: list[dict[str, Any]] = []
    for fragment in potential:
        peers = [other for other in [*page["candidate_regions"], *potential] if other is not fragment]
        if any(v1._connection(fragment, peer, page_width, page_height)[0] for peer in peers):
            admitted.append(fragment)
    page["candidate_regions"].extend(admitted)
    return len(admitted)


def _analyze_v2_process(
    db: sqlite3.Connection, process_id: str, session: ort.InferenceSession, data_root: Path,
) -> dict[str, Any]:
    documents: dict[str, Any] = {}
    pages: list[dict[str, Any]] = []
    unavailable: list[dict[str, Any]] = []
    try:
        for row in v0._iter_pages(db, process_id):
            glyph_runs, error = _glyph_runs_for_page(documents, db, data_root, row["document_id"], int(row["page_number"]))
            if error:
                unavailable.append({"document_id": row["document_id"], "pdf_page": row["page_number"], "reason": error})
            # With glyph evidence, decisions use runs and recurring X bands;
            # text whitespace is explicitly disabled in v0.assemble_page.
            diagnostic = v0.assemble_page(
                json.loads(row["structure_json"]),
                session,
                glyph_runs,
                require_glyph_alignment=True,
            )
            diagnostic["document_id"] = row["document_id"]
            diagnostic["pdf_page"] = row["page_number"]
            diagnostic["glyph_seed_fragment_count"] = _promote_spatial_glyph_seeds(diagnostic)
            diagnostic["glyph_geometry"] = _glyph_summary(diagnostic)
            pages.append(v1.merge_page(diagnostic))
    finally:
        for document in documents.values():
            document.close()

    regions = [region for page in pages for region in page["candidate_regions"]]
    rejected = [item for page in pages for item in page["rejected_activations"]]
    return {
        "process_id": process_id,
        "page_count": len(pages),
        "candidate_region_count": len(regions),
        "pages_affected": sum(bool(page["candidate_regions"]) for page in pages),
        "region_confidence_counts": dict(Counter(region["confidence"] for region in regions)),
        "rejected_activation_count": len(rejected),
        "source_pages_unavailable": unavailable,
        "pages": pages,
    }


def _comparison(v1_process: dict[str, Any], v2_process: dict[str, Any]) -> dict[str, Any]:
    v1_pages = {(page["document_id"], page["pdf_page"]): page for page in v1_process["pages"]}
    recovered: list[dict[str, Any]] = []
    lost: list[dict[str, Any]] = []
    for page in v2_process["pages"]:
        key = (page["document_id"], page["pdf_page"])
        before = len(v1_pages[key]["candidate_regions"])
        after = len(page["candidate_regions"])
        item = {
            "document_id": key[0], "pdf_page": key[1],
            "v1_regions": before, "v2_regions": after,
            "glyph_geometry": page.get("glyph_geometry", {}),
        }
        if after > before:
            recovered.append(item)
        elif after < before:
            lost.append(item)
    return {
        "v1_regions": v1_process["candidate_region_count"],
        "v2_regions": v2_process["candidate_region_count"],
        "v1_pages_affected": v1_process["pages_affected"],
        "v2_pages_affected": v2_process["pages_affected"],
        "recovered_pages": recovered,
        "lost_pages": lost,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=index_db_path())
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--process", action="append", dest="processes")
    parser.add_argument("--output", type=Path, default=Path("scratch/table_region_assembler_v2.json"))
    args = parser.parse_args()
    data_root = args.data_root or args.db.resolve().parent.parent
    processes = args.processes or ["1029994-43.2023.8.26.0554", "1000045-87.2026.8.26.0450"]
    db = sqlite3.connect(args.db.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    db.row_factory = sqlite3.Row
    session = ort.InferenceSession(str(v0.MODEL_PATH_DEFAULT), providers=["CPUExecutionProvider"])
    try:
        v1_processes = [v1.analyze_process(db, process_id, session) for process_id in processes]
        v2_processes = [_analyze_v2_process(db, process_id, session, data_root) for process_id in processes]
    finally:
        db.close()
    v1_by_process = {item["process_id"]: item for item in v1_processes}
    comparisons = [_comparison(v1_by_process[item["process_id"]], item) for item in v2_processes]
    output = {
        "prototype": "THEMIS-TABLE-REGION-ASSEMBLER-V2",
        "mode": "offline-read-only",
        "glyph_contract": "transient PDFium GlyphRun only; never persisted",
        "model": v0.MODEL_PATH_DEFAULT.name,
        "comparison_base": "THEMIS-TABLE-REGION-ASSEMBLER-V1",
        "processes": v2_processes,
        "v1_to_v2": comparisons,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    for comparison, process in zip(comparisons, v2_processes):
        print(f"{process['process_id']}: V1 {comparison['v1_regions']} -> V2 {comparison['v2_regions']} regiões; +{len(comparison['recovered_pages'])}/-{len(comparison['lost_pages'])} páginas")
    print(f"JSON: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
