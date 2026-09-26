"""Provider-neutral persistence for factual document-marker projections."""
from __future__ import annotations

import json
import re
import sqlite3
from typing import Any, Iterable

from core.documentos.lateral_protocol_v1 import (
    extract_lateral_protocols,
    _normalized,
)
from core.documentos.provider_artifacts_v1 import (
    link_provider_artifact_pages,
    register_provider_artifact,
)


def _normalise_heading(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().upper()


def confirmed_document_type(
    structure: dict[str, Any],
    *,
    document_id: str,
    canonical_page_id: str,
    pdf_page: int,
) -> dict[str, Any] | None:
    """Return a type only when the first page names the piece unambiguously.

    This intentionally examines structural blocks, never the body Markdown.  The
    result carries the exact persisted evidence needed to reproduce the decision.
    """
    for block in structure.get("blocks", []):
        if not isinstance(block, dict):
            continue
        heading = _normalise_heading(block.get("text"))
        artifact_type = None
        if heading == "ACÓRDÃO":
            artifact_type = "ACÓRDÃO"
        elif heading == "DECISÃO" or heading.startswith("DECISÃO PROCESSO"):
            artifact_type = "DECISÃO"
        elif heading == "SENTENÇA" or heading.startswith("SENTENÇA PROCESSO"):
            artifact_type = "SENTENÇA"
        elif heading == "DESPACHO" or heading.startswith("DESPACHO PROCESSO"):
            artifact_type = "DESPACHO"
        elif heading == "ATO ORDINATÓRIO" or heading.startswith("ATO ORDINATÓRIO PROCESSO"):
            artifact_type = "ATO ORDINATÓRIO"
        elif heading.startswith("CERTIDÃO"):
            artifact_type = "CERTIDÃO"
        elif heading == "CIÊNCIA DA INTIMAÇÃO":
            artifact_type = "CIÊNCIA DA INTIMAÇÃO"
        elif heading == "CARTA DE CITAÇÃO":
            artifact_type = "CARTA DE CITAÇÃO"
        elif heading.startswith("SOLICITAÇÃO DE PERÍCIA MÉDICA"):
            artifact_type = "SOLICITAÇÃO DE PERÍCIA MÉDICA"
        if artifact_type:
            return {
                "artifact_type": artifact_type,
                "verification_status": "CONFIRMED",
                "classification_source": "STRUCTURAL_HEADING_V1",
                "evidence": {
                    "document_id": document_id,
                    "canonical_page": canonical_page_id,
                    "pdf_page": pdf_page,
                    "block_id": block.get("block_id"),
                    "bbox": block.get("bbox"),
                    "heading_literal": block.get("text"),
                },
            }
    return None


def _apply_confirmed_document_type(
    db: sqlite3.Connection,
    *,
    provider_artifact_id: str,
    provenance: dict[str, Any],
    classification: dict[str, Any] | None,
) -> bool:
    """Persist structural heading evidence without mutating provider artifact status."""
    if classification is None:
        return False
    updated_provenance = dict(provenance)
    updated_provenance.setdefault("provider_verification_status", "PROVIDER_ATTESTED")
    updated_provenance["structural_heading"] = classification
    updated_provenance["document_type"] = classification
    db.execute(
        "UPDATE provider_artifacts SET provenance_json=?, updated_at=datetime('now') WHERE provider_artifact_id=?",
        (json.dumps(updated_provenance, ensure_ascii=False), provider_artifact_id),
    )
    return True


def lateral_regions_from_structures(page_structures: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Adapt persisted PDFium marginal furniture to the existing region contract.

    This is a lossless shape adaptation: no text is parsed or changed here.  A
    furniture item already classified by PDFium as marginal supplies the exact
    text and bounding box; matching line ids are retained as source provenance.
    """
    result: list[dict[str, Any]] = []
    for structure in page_structures:
        if not isinstance(structure, dict) or not isinstance(structure.get("page"), int):
            continue
        lines = [line for line in structure.get("lines", []) if isinstance(line, dict)]
        regions = []
        seen_texts = set()
        for index, furniture in enumerate(structure.get("furniture", []), start=1):
            if not isinstance(furniture, dict) or furniture.get("classification") != "furniture":
                continue
            text = furniture.get("raw_text") or furniture.get("text")
            bbox = furniture.get("bbox")
            if not isinstance(text, str) or len(bbox or []) != 4:
                continue
            source_line_ids = [item for item in furniture.get("source_line_ids", []) if isinstance(item, int)]
            if not source_line_ids:
                source_line_ids = [
                    line["line_id"] for line in lines
                    if isinstance(line.get("line_id"), int) and line.get("bbox") == bbox and line.get("text") == text
                ]
            seen_texts.add(text)
            regions.append({
                "region_id": f"p{structure['page']}-furniture-{index:04d}",
                "kind": "unknown",
                "raw_text": text,
                "bbox": list(bbox),
                "source_line_ids": source_line_ids,
            })
        for index, reg in enumerate(structure.get("regions", []), start=len(regions) + 1):
            text = reg.get("raw_text") or reg.get("text")
            if isinstance(text, str) and text not in seen_texts:
                norm = _normalized(text)
                if any(k in norm for k in ("assinado digitalmente por", "para conferir o original", "pastadigital", "liberado nos autos")):
                    seen_texts.add(text)
                    regions.append({
                        "region_id": reg.get("region_id") or f"p{structure['page']}-region-{index:04d}",
                        "kind": "unknown",
                        "raw_text": text,
                        "bbox": list(reg.get("bbox") or [0.0, 0.0, 595.0, 842.0]),
                        "source_line_ids": list(reg.get("source_line_ids") or []),
                    })
        for index, line in enumerate(lines, start=len(regions) + 1):
            text = line.get("text")
            if isinstance(text, str) and text not in seen_texts:
                norm = _normalized(text)
                if any(k in norm for k in ("assinado digitalmente por", "para conferir o original", "pastadigital", "liberado nos autos")):
                    seen_texts.add(text)
                    regions.append({
                        "region_id": f"p{structure['page']}-line-{index:04d}",
                        "kind": "unknown",
                        "raw_text": text,
                        "bbox": list(line.get("bbox") or [0.0, 0.0, 595.0, 842.0]),
                        "source_line_ids": [line["line_id"]] if isinstance(line.get("line_id"), int) else [],
                    })
        result.append({"page": structure["page"], "regions": regions})
    return result


def provider_attested_markers_by_page(
    *, document_id: str, process_id: str, page_structures: Iterable[dict[str, Any]],
    recovered_pdfium_page_text: dict[int, str] | None = None,
) -> dict[int, dict[str, Any]]:
    """Return provider-attested e-SAJ markers by physical page without persistence.

    This is the single eligibility rule used both by persistence and read
    projections.  A marker must carry the provider verification code and name
    the target process; no neighbouring-page or document metadata is used.
    """
    structures = list(page_structures)
    extraction = extract_lateral_protocols(
        document_id, lateral_regions_from_structures(structures), target_process_id=process_id,
        recovered_pdfium_page_text=recovered_pdfium_page_text,
    )
    result = {}
    for marker in extraction["provider_document_markers"]["markers"]:
        source = marker.get("source_map") or {}
        page = source.get("pdf_page")
        code = (marker.get("verification") or {}).get("code")
        if isinstance(page, int) and code and marker.get("target_process_match") is True:
            result[page] = marker
    return result


def persist_esaj_provider_artifacts(
    db: sqlite3.Connection,
    *,
    document_id: str,
    process_id: str,
    page_structures: Iterable[dict[str, Any]],
    recovered_pdfium_page_text: dict[int, str] | None = None,
) -> dict[str, Any]:
    """Persist only e-SAJ marker facts that identify an original artifact."""
    page_structures = list(page_structures)
    adapted = lateral_regions_from_structures(page_structures)
    extraction = extract_lateral_protocols(
        document_id, adapted, target_process_id=process_id,
        recovered_pdfium_page_text=recovered_pdfium_page_text,
    )
    projection = extraction["provider_document_markers"]
    canonical_by_page = {
        int(row["pdf_page"] if isinstance(row, sqlite3.Row) or hasattr(row, "keys") else row[0]): (
            row["canonical_page_id"] if isinstance(row, sqlite3.Row) or hasattr(row, "keys") else row[1]
        )
        for row in db.execute(
            "SELECT pdf_page, canonical_page_id FROM canonical_page_observations WHERE document_id=?",
            (document_id,),
        )
    }
    structure_by_page = {
        int(item["page"]): item
        for item in page_structures
        if isinstance(item, dict) and isinstance(item.get("page"), int)
    }
    group_ids_by_marker = {
        marker_id: group["provider_marker_group_id"]
        for group in projection["groups"]
        for marker_id in group.get("marker_ids", [])
    }
    markers_by_code: dict[str, list[dict[str, Any]]] = {}
    for page, marker in provider_attested_markers_by_page(
        document_id=document_id, process_id=process_id, page_structures=page_structures,
        recovered_pdfium_page_text=recovered_pdfium_page_text,
    ).items():
        code = (marker.get("verification") or {}).get("code")
        canonical_page_id = canonical_by_page.get(page)
        if not canonical_page_id:
            continue
        markers_by_code.setdefault(code, []).append(marker)
    artifacts = []
    for code, markers in markers_by_code.items():
        markers = sorted(markers, key=lambda marker: marker["source_map"]["pdf_page"])
        primary = markers[0]
        primary_page = primary["source_map"]["pdf_page"]
        classification = confirmed_document_type(
            structure_by_page.get(primary_page, {}),
            document_id=document_id,
            canonical_page_id=canonical_by_page[primary_page],
            pdf_page=primary_page,
        )
        canonical_page_ids = [
            canonical_by_page[marker["source_map"]["pdf_page"]]
            for marker in markers
            if marker["source_map"]["pdf_page"] in canonical_by_page
        ]
        provenance = {
            "provider_document_marker_version": projection["provider_document_marker_version"],
            "verification_status": "PROVIDER_ATTESTED",
            "provider_verification_status": "PROVIDER_ATTESTED",
            "marker": primary,
            "markers": markers,
            "provider_marker_group_ids": sorted({
                group_ids_by_marker.get(marker["marker_id"])
                for marker in markers if group_ids_by_marker.get(marker["marker_id"])
            }),
        }
        if classification:
            provenance["structural_heading"] = classification
            provenance["document_type"] = classification
        artifact_id = register_provider_artifact(
            db,
            process_id=process_id,
            source_origin="ESAJ",
            source_artifact_id=f"ESAJ:VERIFICATION_CODE:{code}",
            artifact_fingerprint=primary.get("artifact_fingerprint"),
            artifact_type=None,
            signer=primary.get("signatory_literal"),
            provenance=provenance,
        )
        link_provider_artifact_pages(db, artifact_id, canonical_page_ids)
        artifacts.append({"artifact_id": artifact_id, "marker_ids": [marker["marker_id"] for marker in markers], "pdf_pages": [marker["source_map"]["pdf_page"] for marker in markers]})
    return {
        "provider": "ESAJ",
        "document_id": document_id,
        "markers": len(projection["markers"]),
        "marker_groups": len(projection["groups"]),
        "artifacts": artifacts,
        "extraction": extraction,
    }


def backfill_confirmed_document_types(db: sqlite3.Connection, *, document_id: str) -> dict[str, int]:
    """Classify existing artifacts from persisted structures, without re-extracting markers.

    Artifacts without an unambiguous heading are deliberately left byte-for-byte
    untouched, including their provider-derived event metadata.
    """
    rows = db.execute(
        """SELECT ap.provider_artifact_id, a.provenance_json, o.canonical_page_id,
                  o.pdf_page, ps.structure_json
           FROM provider_artifact_pages ap
           JOIN provider_artifacts a ON a.provider_artifact_id=ap.provider_artifact_id
           JOIN canonical_page_observations o ON o.canonical_page_id=ap.canonical_page_id
           JOIN pages p ON p.document_id=o.document_id AND p.page_number=o.pdf_page
           JOIN page_structures ps ON ps.page_id=p.page_id
           WHERE o.document_id=?
           ORDER BY ap.provider_artifact_id, o.pdf_page""",
        (document_id,),
    ).fetchall()
    first_by_artifact: dict[str, sqlite3.Row] = {}
    for row in rows:
        first_by_artifact.setdefault(row["provider_artifact_id"], row)
    confirmed = 0
    unknown = 0
    for artifact_id, row in first_by_artifact.items():
        try:
            provenance = json.loads(row["provenance_json"] or "{}")
        except (TypeError, ValueError):
            provenance = {}
        heading_classification = confirmed_document_type(
            json.loads(row["structure_json"] or "{}"),
            document_id=document_id,
            canonical_page_id=row["canonical_page_id"],
            pdf_page=row["pdf_page"],
        )
        if _apply_confirmed_document_type(
            db,
            provider_artifact_id=artifact_id,
            provenance=provenance,
            classification=heading_classification,
        ):
            confirmed += 1
        else:
            unknown += 1
    return {"artifacts": len(first_by_artifact), "confirmed": confirmed, "unknown": unknown}


def confirm_core_referenced_artifact(
    db: sqlite3.Connection,
    *,
    provider_artifact_id: str,
    movement_id: str,
    folio_reference_literal: str,
    process_source_type: str,
    process_source_id: str,
    artifact_type: str,
) -> None:
    """Confirm a document type through an explicit Core movement reference.

    The caller supplies an already audited reference.  This function verifies
    that artifact, movement and process source belong to the same process, then
    persists the literal evidence without parsing or changing marker raw text.
    """
    artifact = db.execute(
        "SELECT process_id, provenance_json FROM provider_artifacts WHERE provider_artifact_id=?",
        (provider_artifact_id,),
    ).fetchone()
    if artifact is None:
        raise ValueError("provider artifact inexistente")
    movement = db.execute(
        "SELECT process_id, content FROM process_movements WHERE movement_id=?",
        (movement_id,),
    ).fetchone()
    if movement is None or movement["process_id"] != artifact["process_id"]:
        raise ValueError("movement não pertence ao processo do artifact")
    if folio_reference_literal not in (movement["content"] or ""):
        raise ValueError("referência literal não encontrada na movement")
    source = db.execute(
        "SELECT 1 FROM process_sources WHERE process_id=? AND source_type=? AND source_id=?",
        (artifact["process_id"], process_source_type, process_source_id),
    ).fetchone()
    if source is None:
        raise ValueError("process source não confirmado")
    try:
        provenance = json.loads(artifact["provenance_json"] or "{}")
    except (TypeError, ValueError):
        provenance = {}
    provenance.setdefault("provider_verification_status", provenance.get("verification_status", "PROVIDER_ATTESTED"))
    provenance["verification_status"] = "CONFIRMED"
    provenance["document_type"] = {
        "artifact_type": artifact_type,
        "verification_status": "CONFIRMED",
        "classification_source": "CORE_REFERENCED",
        "evidence": {
            "movement_id": movement_id,
            "folio_reference_literal": folio_reference_literal,
            "process_source": {
                "source_type": process_source_type,
                "source_id": process_source_id,
            },
            "method": "CORE_REFERENCED",
        },
    }
    db.execute(
        "UPDATE provider_artifacts SET movement_id=?, artifact_type=?, provenance_json=?, updated_at=datetime('now') WHERE provider_artifact_id=?",
        (movement_id, artifact_type, json.dumps(provenance, ensure_ascii=False), provider_artifact_id),
    )


def document_page_structures(db: sqlite3.Connection, document_id: str) -> list[dict[str, Any]]:
    rows = db.execute(
        "SELECT p.page_number, ps.structure_json FROM pages p JOIN page_structures ps USING(page_id) "
        "WHERE p.document_id=? ORDER BY p.page_number",
        (document_id,),
    ).fetchall()
    return [
        {
            "page": row["page_number"] if isinstance(row, sqlite3.Row) or hasattr(row, "keys") else row[0],
            **json.loads((row["structure_json"] if isinstance(row, sqlite3.Row) or hasattr(row, "keys") else row[1]) or "{}"),
        }
        for row in rows
    ]


def ensure_document_canonical_pages(db: sqlite3.Connection, document_id: str) -> None:
    """Backfill the existing Canonical Store only when this document lacks it."""
    exists = db.execute(
        "SELECT 1 FROM canonical_page_observations WHERE document_id=? LIMIT 1", (document_id,)
    ).fetchone()
    if not exists:
        from core.documentos.canonical_store_v1 import _backfill
        _backfill(db)
