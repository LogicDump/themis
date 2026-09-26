"""Read-only, page-sequential projection of provider-attested procedural acts.

An act is a maximal contiguous run of canonical process pages carrying the
same factual lateral identity (actor, datetime, and submission protocol when present).
Provider artifacts evidence pages and individual piece verification codes;
they never enumerate or delimit acts.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any



ID_NAMESPACE = uuid.UUID("eeffea46-c6c1-5c2a-89d1-bc116a0145e1")


def _json(value: object) -> dict[str, Any]:
    try:
        parsed = json.loads(value or "{}")
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _marker(provenance: dict[str, Any]) -> dict[str, Any]:
    marker = provenance.get("marker")
    return marker if isinstance(marker, dict) else {}


def _canonical_datetime(value: object) -> str | None:
    """Normalize only equivalent provider timestamp encodings for identity comparison."""
    if not isinstance(value, str) or not value:
        return None
    for pattern in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, pattern).strftime("%d/%m/%Y %H:%M")
        except ValueError:
            pass
    return value


def _extract_protocol(marker: dict[str, Any], prov: dict[str, Any]) -> tuple[str | None, str | None]:
    """Returns (protocol, wprc_protocol)."""
    proto = marker.get("protocol_number") or prov.get("protocol_number")
    if not proto:
        p_id = marker.get("provider_identity")
        if isinstance(p_id, dict):
            val = p_id.get("document_or_movement_or_protocol")
            if isinstance(val, dict) and val.get("kind") == "PROTOCOL":
                proto = val.get("value")
    proto_str = str(proto).strip() if proto else None
    wprc = proto_str if (proto_str and proto_str.upper().startswith("WPRC")) else None
    return proto_str, wprc


def _page_rows(db: sqlite3.Connection, process_id: str) -> list[sqlite3.Row]:
    """Return one physical primary observation per canonical page, in process order."""
    return db.execute(
        """SELECT cp.canonical_page_id, cp.process_id, cp.canonical_order, cp.process_page_number,
                  cp.process_folio_label, o.document_id, o.pdf_page, p.quality,
                  a.provider_artifact_id, a.artifact_type, a.title, a.signer,
                  a.source_origin, a.provenance_json
           FROM canonical_pages cp
           JOIN canonical_page_observations o ON o.canonical_page_id=cp.canonical_page_id
                                            AND o.observation_role='PRIMARY'
           JOIN pages p ON p.document_id=o.document_id AND p.page_number=o.pdf_page
           LEFT JOIN provider_artifact_pages ap ON ap.canonical_page_id=cp.canonical_page_id
           LEFT JOIN provider_artifacts a ON a.provider_artifact_id=ap.provider_artifact_id
                                         AND a.process_id=?
           WHERE cp.process_id=? AND cp.lifecycle_status='ACTIVE'
           ORDER BY CASE WHEN cp.canonical_order IS NULL THEN 1 ELSE 0 END,
                    cp.canonical_order, cp.process_page_number, o.document_id, o.pdf_page""",
        (process_id, process_id),
    ).fetchall()


def _page_evidence(rows: list[sqlite3.Row]) -> tuple[dict[str, Any] | None, str | None]:
    """Resolve a page's factual identity, never deriving it from piece verification codes or document text."""
    evidence = []
    for row in rows:
        if not row["provider_artifact_id"]:
            continue
        prov = _json(row["provenance_json"])
        marker = _marker(prov)
        actor = marker.get("signatory_literal") or row["signer"]
        occurred_at = _canonical_datetime(marker.get("event_at"))
        
        protocol, wprc_protocol = _extract_protocol(marker, prov)
        
        # Piece verification code (e.g. aqgMCLbP) belongs strictly to the piece, not act boundary
        verification_code = marker.get("verification_code") or (marker.get("verification") or {}).get("code")
        
        act_identity = (actor or None, occurred_at or None, wprc_protocol or protocol or None)
        if any(act_identity):
            evidence.append({
                "act_identity": act_identity,
                "actor": actor or None,
                "occurred_at": occurred_at or None,
                "protocol": wprc_protocol or protocol or None,
                "verification_code": verification_code or None,
                "artifact_id": row["provider_artifact_id"],
                "artifact_type": row["artifact_type"],
                "title": row["title"],
                "signer": row["signer"],
                "source_origin": row["source_origin"],
                "evidence_origin": "PERSISTED_PROVIDER_ARTIFACT",
                "marker": marker,
            })
    if not evidence:
        return None, "NO_ARTIFACT_CONTEXT"
    identities = {item["act_identity"] for item in evidence}
    if len(identities) != 1:
        return None, "CONFLICTING_ARTIFACT_CONTEXT"
    return evidence[0], None


def _act_id(process_id: str, start_page_id: str, identity: tuple[Any, ...]) -> str:
    return "act_" + uuid.uuid5(
        ID_NAMESPACE, f"{process_id}|{start_page_id}|{'|'.join(str(item or '') for item in identity)}"
    ).hex


def _page_payload(row: sqlite3.Row, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "document_id": row["document_id"],
        "pdf_page": row["pdf_page"],
        "process_page_number": row["process_page_number"],
        "process_folio_label": row["process_folio_label"],
        "quality": row["quality"],
        "provider_artifact_id": evidence.get("artifact_id"),
        "verification_code": evidence.get("verification_code"),
    }


def _component_payload(
    pages: list[dict[str, Any]],
    evidence: dict[str, Any],
    piece_meta: Any = None,
) -> dict[str, Any]:
    first = pages[0]
    last = pages[-1]
    piece_type = getattr(piece_meta, "piece_type", None) or evidence.get("artifact_type") or "Documento"
    filename = getattr(piece_meta, "source_filename_literal", None) or evidence.get("title") or piece_type
    verification_code = first.get("verification_code") or evidence.get("verification_code")
    return {
        "component_id": f"piece:{first['document_id']}:{first['pdf_page']}",
        "document_id": first["document_id"],
        "provider_artifact_id": evidence.get("artifact_id"),
        "artifact_type": piece_type,
        "piece_type": piece_type,
        "title": filename,
        "verification_code": verification_code,
        "page_count": len(pages),
        "pages": pages,
        "folha_inicial": first.get("process_folio_label"),
        "folha_final": last.get("process_folio_label"),
        "provenance": {
            "source_kind": "canonical_page_member",
            "provider_artifact_id": evidence.get("artifact_id"),
            "verification_code": verification_code,
        },
    }


def _act_from_run(
    process_id: str,
    run: list[tuple[sqlite3.Row, dict[str, Any]]],
    pecas_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    first_row, evidence = run[0]
    pages = [_page_payload(row, page_ev) for row, page_ev in run]
    
    # Group into piece components preserving sequence of occurrence
    components = []
    current_doc_id = None
    current_doc_pages: list[dict[str, Any]] = []
    current_doc_ev = None

    for row, page_ev in run:
        doc_id = row["document_id"]
        if current_doc_id is not None and doc_id != current_doc_id:
            piece_meta = pecas_map.get(current_doc_id) if pecas_map else None
            components.append(_component_payload(current_doc_pages, current_doc_ev, piece_meta))
            current_doc_pages = []
        current_doc_id = doc_id
        current_doc_ev = page_ev
        current_doc_pages.append(_page_payload(row, page_ev))
    
    if current_doc_pages:
        piece_meta = pecas_map.get(current_doc_id) if pecas_map else None
        components.append(_component_payload(current_doc_pages, current_doc_ev, piece_meta))

    first = pages[0]
    last = pages[-1]
    
    # Act title and type derived from principal component
    principal_piece = components[0] if components else {}
    act_type = principal_piece.get("piece_type") or evidence.get("artifact_type") or "PROVIDER_ATTESTED_ACT"
    title = principal_piece.get("title") or evidence.get("title") or act_type
    
    if len(components) > 1:
        description = f"{act_type} (com {len(components) - 1} anexo(s))"
    else:
        description = title

    return {
        "act_id": _act_id(process_id, first_row["canonical_page_id"], evidence["act_identity"]),
        "process_id": process_id,
        "act_type": act_type,
        "title": title,
        "description": description,
        "actor": evidence["actor"],
        "occurred_at": evidence["occurred_at"],
        "protocol": evidence["protocol"],
        "official_identity": {
            "actor": evidence["actor"],
            "datetime": evidence["occurred_at"],
            "protocol": evidence["protocol"],
        },
        "page_count": len(pages),
        "component_count": len(components),
        "components": components,
        "source_ref": {
            "document_id": first["document_id"],
            "pdf_page": first["pdf_page"],
            "process_folio": first["process_folio_label"],
            "process_folio_start": first["process_folio_label"],
            "process_folio_end": last["process_folio_label"],
            "process_page_start": first["process_page_number"],
            "process_page_end": last["process_page_number"],
        },
        "provenance": {
            "source_kind": "canonical_page_identity_run_v2",
            "identity": {
                "actor": evidence["actor"],
                "datetime": evidence["occurred_at"],
                "protocol": evidence["protocol"],
            },
            "canonical_page_start": first_row["canonical_page_id"],
            "canonical_page_end": run[-1][0]["canonical_page_id"],
            "provider_artifact_ids": sorted({page["provider_artifact_id"] for page in pages if page["provider_artifact_id"]}),
            "verification_codes": sorted({page["verification_code"] for page in pages if page["verification_code"]}),
        },
    }


def project_procedural_acts(
    db: sqlite3.Connection,
    process_id: str,
    pecas_map: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Project maximal contiguous factual-identity runs in canonical page order."""
    grouped: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in _page_rows(db, process_id):
        grouped[row["canonical_page_id"]].append(row)

    acts: list[dict[str, Any]] = []
    run: list[tuple[sqlite3.Row, dict[str, Any]]] = []
    current_identity: tuple[Any, ...] | None = None
    for page_rows in grouped.values():
        row = page_rows[0]
        evidence, _reason = _page_evidence(page_rows)
        identity = evidence["act_identity"] if evidence else None
        if identity is None:
            if run:
                acts.append(_act_from_run(process_id, run, pecas_map))
                run, current_identity = [], None
            continue
        if run and identity != current_identity:
            acts.append(_act_from_run(process_id, run, pecas_map))
            run = []
        run.append((row, evidence))
        current_identity = identity
    if run:
        acts.append(_act_from_run(process_id, run, pecas_map))
    return acts


def movement_projection(
    db: sqlite3.Connection,
    process_id: str,
    manifest_or_root: Any = None,
) -> list[dict[str, Any]]:
    """Project factual occurrences as the operational Movimentos read model.
    
    Uses pecas_manifest / e-SAJ tree as the oracle of pieces and groups contiguous
    pieces sharing the same factual provider occurrence (actor, occurred_at, protocol).
    """
    ordered_pecas = []
    try:
        from core.documentos.pecas_manifest_v1 import load_ordered_pecas_manifest
        from core.runtime_paths import themis_data_root
        root = manifest_or_root or themis_data_root()
        ordered_pecas = load_ordered_pecas_manifest(root, process_id)
    except Exception:
        ordered_pecas = []

    # If ordered pecas exist from Pasta Digital manifest, project using manifest as oracle of pieces
    if ordered_pecas:
        page_rows_list = _page_rows(db, process_id)
        grouped: dict[str, list[sqlite3.Row]] = defaultdict(list)
        for row in page_rows_list:
            grouped[row["canonical_page_id"]].append(row)

        page_ev_map = {}
        for cp_id, rows in grouped.items():
            evidence, _ = _page_evidence(rows)
            row = rows[0]
            page_ev_map[row["process_page_number"]] = (row, evidence)

        # Build document physical offsets in concatenated PDF
        doc_counts = {
            r["document_id"]: r["page_count"]
            for r in db.execute("SELECT document_id, page_count FROM documents WHERE process_id=?", (process_id,)).fetchall()
        } if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='documents'").fetchone() else {}
        doc_offsets = {}
        cur_offset = 0
        for p in ordered_pecas:
            sha = p.document_id
            if sha and sha not in doc_offsets:
                doc_offsets[sha] = cur_offset
                cur_offset += doc_counts.get(sha, p.page_count or 1)

        piece_records = []
        for p in ordered_pecas:
            fi = p.folha_inicial
            ff = p.folha_final
            ptype = p.piece_type or "Documento"
            fn = p.source_filename_literal or ptype
            sha = p.document_id

            piece_pages = []
            if fi is not None and ff is not None:
                for ppn in range(fi, ff + 1):
                    if ppn in page_ev_map:
                        r, ev = page_ev_map[ppn]
                        pdf_p = r["pdf_page"]
                        piece_pages.append({
                            "process_page_number": ppn,
                            "pdf_page": pdf_p,
                            "integral_pdf_page": doc_offsets.get(r["document_id"], 0) + pdf_p,
                            "document_id": r["document_id"],
                            "process_folio_label": r["process_folio_label"],
                            "verification_code": (ev.get("verification_code") if ev else None),
                            "evidence": ev,
                        })

            evs = [pg["evidence"] for pg in piece_pages if pg.get("evidence")]
            actor = evs[0]["actor"] if evs else None
            occurred_at = evs[0]["occurred_at"] if evs else None
            protocol = evs[0]["protocol"] if evs else None
            verification_code = evs[0]["verification_code"] if evs else None

            first_pg = piece_pages[0] if piece_pages else {
                "process_page_number": fi, "pdf_page": 1, "document_id": sha, "process_folio_label": str(fi or 1),
                "integral_pdf_page": doc_offsets.get(sha, 0) + 1
            }
            last_pg = piece_pages[-1] if piece_pages else first_pg

            p_start = fi if fi is not None else first_pg["process_page_number"]
            p_end = ff if ff is not None else last_pg["process_page_number"]
            int_start = first_pg.get("integral_pdf_page", doc_offsets.get(first_pg["document_id"], 0) + first_pg.get("pdf_page", 1))
            int_end = last_pg.get("integral_pdf_page", doc_offsets.get(last_pg["document_id"], 0) + last_pg.get("pdf_page", 1))

            piece_records.append({
                "component_id": f"piece:{sha}:{first_pg.get('pdf_page', 1)}",
                "order": p.order,
                "piece_type": ptype,
                "artifact_type": ptype,
                "title": fn,
                "source_filename_literal": fn,
                "folha_inicial": p_start,
                "folha_final": p_end,
                "page_start": p_start,
                "page_end": p_end,
                "integral_page_start": int_start,
                "integral_page_end": int_end,
                "page_count": p.page_count or ((p_end - p_start + 1) if (p_start is not None and p_end is not None) else len(piece_pages)),
                "document_id": sha,
                "sha256": sha,
                "provider_item_identity": p.provider_item_identity,
                "provider_document_id": p.provider_document_id,
                "verification_code": verification_code,
                "actor": actor,
                "occurred_at": occurred_at,
                "protocol": protocol,
                "identity": (actor, occurred_at, protocol) if (actor or occurred_at or protocol) else None,
                "source_ref": {
                    "document_id": first_pg["document_id"],
                    "pdf_page": first_pg["pdf_page"],
                    "process_folio": first_pg["process_folio_label"],
                    "process_folio_start": first_pg["process_folio_label"],
                    "process_folio_end": last_pg["process_folio_label"],
                    "process_page_start": p_start,
                    "process_page_end": p_end,
                    "integral_pdf_page": int_start,
                    "integral_page_start": int_start,
                    "integral_page_end": int_end,
                },
                "pages": [
                    {
                        "process_page_number": pg["process_page_number"],
                        "pdf_page": pg["pdf_page"],
                        "integral_pdf_page": pg.get("integral_pdf_page", doc_offsets.get(pg["document_id"], 0) + pg["pdf_page"]),
                        "document_id": pg["document_id"],
                        "process_folio_label": pg["process_folio_label"],
                        "verification_code": pg.get("verification_code"),
                    } for pg in piece_pages
                ],
                "provenance": {
                    "source_kind": "esaj_pastadigital_piece",
                    "provider_item_identity": p.provider_item_identity,
                    "provider_document_id": p.provider_document_id,
                    "verification_code": verification_code,
                },
            })

        grouped_movements = []
        current_pieces = []
        current_identity = None

        for piece in piece_records:
            ident = piece["identity"]
            if ident is None:
                if current_pieces:
                    grouped_movements.append(current_pieces)
                    current_pieces = []
                    current_identity = None
                grouped_movements.append([piece])
                continue
            if current_pieces and ident != current_identity:
                grouped_movements.append(current_pieces)
                current_pieces = []
            current_pieces.append(piece)
            current_identity = ident

        if current_pieces:
            grouped_movements.append(current_pieces)

        results = []
        for seq, pieces in enumerate(grouped_movements, 1):
            first_p = pieces[0]
            last_p = pieces[-1]
            p_start = first_p["page_start"]
            p_end = last_p["page_end"]
            actor = first_p["actor"]
            occurred_at = first_p["occurred_at"]
            proto = first_p["protocol"]
            mov_type = first_p["piece_type"] or "Movimento"
            title = first_p["title"] or mov_type
            description = f"{mov_type} (com {len(pieces) - 1} anexo(s))" if len(pieces) > 1 else title

            mid = f"mov_{process_id}_{p_start}_{p_end}_{seq}"
            results.append({
                "movement_id": mid,
                "act_id": mid,
                "process_id": process_id,
                "sequence": seq,
                "movement_type": mov_type,
                "title": title,
                "description": description,
                "actor": actor,
                "occurred_at": occurred_at,
                "source_datetime": occurred_at,
                "protocol": proto,
                "page_start": p_start,
                "page_end": p_end,
                "page_count": sum(p["page_count"] for p in pieces if p.get("page_count")),
                "piece_count": len(pieces),
                "component_count": len(pieces),
                "source_ref": {
                    "document_id": first_p["source_ref"]["document_id"],
                    "pdf_page": first_p["source_ref"]["pdf_page"],
                    "process_folio": first_p["source_ref"]["process_folio"],
                    "process_folio_start": first_p["source_ref"]["process_folio_start"],
                    "process_folio_end": last_p["source_ref"]["process_folio_end"],
                    "process_page_start": p_start,
                    "process_page_end": p_end,
                    "integral_page_start": first_p["source_ref"].get("integral_page_start"),
                    "integral_page_end": last_p["source_ref"].get("integral_page_end"),
                    "integral_pdf_page": first_p["source_ref"].get("integral_page_start"),
                },
                "pieces": pieces,
                "documents": pieces,
                "components": pieces,
                "provenance": {
                    "source_kind": "esaj_pastadigital_movement_grouping_v1",
                    "identity": {
                        "actor": actor,
                        "datetime": occurred_at,
                        "protocol": proto,
                    },
                    "page_start": p_start,
                    "page_end": p_end,
                    "provider_item_identities": [p["provider_item_identity"] for p in pieces if p.get("provider_item_identity")],
                    "verification_codes": [p["verification_code"] for p in pieces if p.get("verification_code")],
                },
            })
        return results

    # Fallback when no pecas manifest is available
    pecas_map = {p.document_id: p for p in ordered_pecas} if ordered_pecas else None
    acts = project_procedural_acts(db, process_id, pecas_map=pecas_map)
    return [{
        "movement_id": act["act_id"],
        "act_id": act["act_id"],
        "process_id": process_id,
        "sequence": index,
        "movement_type": act["act_type"],
        "title": act["title"],
        "description": act["description"],
        "actor": act["actor"],
        "occurred_at": act["occurred_at"],
        "source_datetime": act["occurred_at"],
        "source_ref": act["source_ref"],
        "protocol": act["protocol"],
        "page_start": act["source_ref"].get("process_page_start"),
        "page_end": act["source_ref"].get("process_page_end"),
        "page_count": act["page_count"],
        "piece_count": act["component_count"],
        "component_count": act["component_count"],
        "pieces": act["components"],
        "documents": act["components"],
        "components": act["components"],
        "provenance": act["provenance"],
    } for index, act in enumerate(acts, 1)]


def audit_procedural_act_coverage(db: sqlite3.Connection, process_id: str) -> dict[str, Any]:
    """Account for every canonical page without mutating persisted data."""
    grouped: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in _page_rows(db, process_id):
        grouped[row["canonical_page_id"]].append(row)
    artifact_documents = {
        row[0] for row in db.execute(
            """SELECT DISTINCT o.document_id
               FROM provider_artifact_pages ap
               JOIN canonical_page_observations o ON o.canonical_page_id=ap.canonical_page_id
               JOIN provider_artifacts a ON a.provider_artifact_id=ap.provider_artifact_id
               WHERE a.process_id=?""",
            (process_id,),
        )
    }
    gaps = []
    recovered = []
    for page_rows in grouped.values():
        evidence, reason = _page_evidence(page_rows)
        if evidence is not None and evidence.get("evidence_origin") == "RECOVERED_PAGE_MARKER":
            row = page_rows[0]
            recovered.append({
                "canonical_page_id": row["canonical_page_id"],
                "process_page_number": row["process_page_number"],
                "document_id": row["document_id"],
                "pdf_page": row["pdf_page"],
                "actor": evidence["actor"],
                "datetime": evidence["occurred_at"],
                "protocol": evidence["protocol"],
                "provider_identity": {
                    "actor": evidence["actor"],
                    "datetime": evidence["occurred_at"],
                    "protocol": evidence["protocol"],
                },
            })
        elif evidence is None:
            row = page_rows[0]
            gaps.append({
                "reason": reason,
                "classification": "NO_PERSISTED_LATERAL_EVIDENCE",
                "canonical_page_id": row["canonical_page_id"],
                "process_page_number": row["process_page_number"],
                "document_id": row["document_id"],
                "pdf_page": row["pdf_page"],
                "document_has_other_artifact_context": row["document_id"] in artifact_documents,
            })
    acts = project_procedural_acts(db, process_id)
    return {
        "canonical_pages": len(grouped),
        "persisted_artifact_context_pages": len(grouped) - len(gaps) - len(recovered),
        "recovered_page_marker_context_pages": len(recovered),
        "attested_pages": len(grouped) - len(gaps),
        "recovered_page_markers": recovered,
        "unattested_pages": gaps,
        "unattested_by_classification": {
            classification: sum(item["classification"] == classification for item in gaps)
            for classification in sorted({item["classification"] for item in gaps})
        },
        "acts": len(acts),
        "act_pages": sum(act["page_count"] for act in acts),
        "pieces": sum(act["component_count"] for act in acts),
    }
