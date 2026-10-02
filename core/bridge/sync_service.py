"""Serviço de sincronização processual Themis Browser Bridge <-> e-SAJ/TJSP.

Gerencia o planejamento de sincronização, detecção de peças ausentes, persistência
de metadados/partes/movimentações e reconciliação dos Autos.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.documentos.autos_reconciler_v1 import reconcile_process_autos
from core.documentos.provider_artifacts_v1 import (
    register_movement,
    register_provider_artifact,
)
from core.documentos.themis_documentos import Store, now, _page_class, _page_folios, _compact_page_record
from core.pdf import themis_pdf
from core.readable_markdown import EXTRACTION_PIPELINE_VERSION
from core.runtime_paths import index_db_path, themis_data_root


import re
from urllib.parse import parse_qs, urlparse

CNJ_REGEX = re.compile(r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$")
_LOGGER = logging.getLogger(__name__)


def is_current_extraction_cache(manifest: dict[str, Any], document_id: str) -> bool:
    """Return whether a manifest can be reused by the active extractor.

    Manifests without a version and manifests emitted by any earlier pipeline
    are deliberately stale.  Only the exact active version is reusable.
    """
    return (
        manifest.get("sha256") == document_id
        and manifest.get("extraction_pipeline_version") == EXTRACTION_PIPELINE_VERSION
    )


def _cached_extraction_page_count(store: Store, pecas: list[dict[str, Any]]) -> int:
    """Count durable per-document extraction checkpoints before a resumed run."""
    cached_pages = 0
    for piece in pecas:
        document_id = piece.get("document_id") or piece.get("sha256")
        if not document_id:
            continue
        pages_path = store.pages_path(str(document_id))
        manifest_path = store.manifest_path(str(document_id))
        if not pages_path.is_file() or not manifest_path.is_file():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if is_current_extraction_cache(manifest, str(document_id)):
                cached_pages += max(0, int(manifest.get("pages") or 0))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return cached_pages


def esaj_provider_item_identity(item: dict[str, Any], part_index: int = 0, part: dict[str, Any] | None = None) -> str:
    """Return the stable provider identity for one Pasta Digital piece.

    e-SAJ's ``cdDocumento`` identifies the provider inventory item across bulk
    exports.  A ZIP member's bytes and filename are transport artefacts and
    must never decide whether an already persisted piece is new.
    """
    cd_documento = str(item.get("cdDocumento") or "").strip()
    if not cd_documento:
        raise ValueError("INVARIANT_VIOLATION: item da Pasta Digital sem cdDocumento estável.")
    params = str((part or {}).get("parametros") or item.get("parametros") or "")
    provider_piece_id = parse_qs(params).get("idDocumento", [""])[0].strip()
    if provider_piece_id:
        return f"esaj:idDocumento:{provider_piece_id}"
    return f"esaj:cdDocumento:{cd_documento}:part:{part_index + 1}"


def _snapshot_documents_by_order(store: Store, cnj: str) -> dict[int, dict[str, Any]]:
    snapshot_path = store.process_snapshot_path(cnj)
    if not snapshot_path.is_file():
        raise FileNotFoundError(f"source_snapshot.json não encontrado para {cnj}")
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    pieces: dict[int, dict[str, Any]] = {}
    ordinal = 0
    for item in sorted(payload.get("documents", []), key=lambda row: int(row.get("order") or 0)):
        parts = item.get("parts") or [{}]
        for part_index, part in enumerate(parts):
            ordinal += 1
            pieces[ordinal] = {"document": item, "part": part, "part_index": part_index}
    return pieces


def _persisted_provider_document_ids(store: Store, cnj: str) -> dict[str, str]:
    """Resolve stable provider item identity to an existing Themis document.

    New manifests persist ``provider_item_identity``.  The fallback maps a
    pre-incremental manifest by its provider snapshot order solely to upgrade
    already homologated data; it never uses PDF bytes as identity.
    """
    manifest_path = store.process_fontes_path(cnj) / "pecas_manifest.json"
    if not manifest_path.is_file():
        return {}
    previous = json.loads(manifest_path.read_text(encoding="utf-8"))
    pieces = previous.get("pecas", [])
    if not pieces:
        return {}

    prior_by_order: dict[int, dict[str, Any]] = {}
    snapshot_dirs = sorted(store.process_snapshots_dir(cnj).glob("*/source_snapshot.json"), reverse=True)
    for candidate in snapshot_dirs:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
        documents = payload.get("documents", [])
        expanded: list[dict[str, Any]] = []
        for item in sorted(documents, key=lambda row: int(row.get("order") or 0)):
            for part_index, part in enumerate(item.get("parts") or [{}]):
                expanded.append({"document": item, "part": part, "part_index": part_index})
        if len(expanded) == len(pieces):
            prior_by_order = {index: item for index, item in enumerate(expanded, 1)}
            break

    known: dict[str, str] = {}
    for ordinal, piece in enumerate(pieces, 1):
        identity = piece.get("provider_item_identity")
        if not identity and ordinal in prior_by_order:
            source = prior_by_order[ordinal]
            identity = esaj_provider_item_identity(source["document"], source["part_index"], source["part"])
        document_id = str(piece.get("document_id") or piece.get("sha256") or "").strip()
        if identity and document_id:
            known[str(identity)] = document_id
    return known


_MANIFEST_PAGE_RANGE_RE = re.compile(r"\(\s*pag\.?\s+(\d+)\s*(?:-\s*(\d+))?\s*\)", re.IGNORECASE)


def _provider_part_page_range(document: dict[str, Any], part: dict[str, Any]) -> tuple[int, int]:
    """Return a provider-attested page range for one inventory part."""
    params = str(part.get("parametros") or document.get("parametros") or "")
    query = parse_qs(params)
    first = (query.get("numInicial") or [""])[0]
    last = (query.get("numFinal") or [""])[0]
    if not str(first).isdigit() or not str(last).isdigit():
        raise ValueError("INVARIANT_VIOLATION: parte e-SAJ sem faixa numInicial/numFinal factual.")
    return int(first), int(last)


def backfill_legacy_esaj_provider_identities(store: Store, cnj: str) -> dict[str, int]:
    """Persist stable e-SAJ identities in a verified pre-incremental manifest.

    The migration is intentionally metadata-only: it pairs existing manifest
    entries with the current provider snapshot by the ordered provider part,
    after proving equal cardinality, unique identities and equal factual page
    ranges.  It never reads PDF bytes, creates documents, or opens the index.
    """
    manifest_path = store.process_fontes_path(cnj) / "pecas_manifest.json"
    snapshot_path = store.process_snapshot_path(cnj)
    if not manifest_path.is_file() or not snapshot_path.is_file():
        raise FileNotFoundError(f"Manifesto ou source_snapshot ausente para {cnj}.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    pieces = manifest.get("pecas") or []
    provider_parts: list[tuple[dict[str, Any], int, dict[str, Any]]] = []
    for document in sorted(snapshot.get("documents", []), key=lambda row: int(row.get("order") or 0)):
        for part_index, part in enumerate(document.get("parts") or [{}]):
            provider_parts.append((document, part_index, part))
    if len(pieces) != len(provider_parts):
        raise ValueError(
            "INVARIANT_VIOLATION: cardinalidade manifesto/provider diverge "
            f"({len(pieces)} != {len(provider_parts)})."
        )

    planned: list[tuple[dict[str, Any], str, str]] = []
    seen: set[str] = set()
    for ordinal, (piece, source) in enumerate(zip(pieces, provider_parts), 1):
        document, part_index, part = source
        identity = esaj_provider_item_identity(document, part_index, part)
        if identity in seen:
            raise ValueError(f"INVARIANT_VIOLATION: identidade provider duplicada no ordinal {ordinal}: {identity}")
        seen.add(identity)
        cd_documento = str(document.get("cdDocumento") or "").strip()
        if not cd_documento:
            raise ValueError(f"INVARIANT_VIOLATION: cdDocumento ausente no ordinal {ordinal}.")

        filename = str(piece.get("source_filename_literal") or "")
        page_match = _MANIFEST_PAGE_RANGE_RE.search(filename)
        if not page_match:
            raise ValueError(f"INVARIANT_VIOLATION: peça legada sem faixa verificável no ordinal {ordinal}.")
        manifest_range = (int(page_match.group(1)), int(page_match.group(2) or page_match.group(1)))
        provider_range = _provider_part_page_range(document, part)
        if manifest_range != provider_range:
            raise ValueError(
                f"INVARIANT_VIOLATION: faixa diverge no ordinal {ordinal}: "
                f"manifesto={manifest_range}, provider={provider_range}."
            )

        persisted_identity = str(piece.get("provider_item_identity") or "").strip()
        persisted_cd = str(piece.get("provider_document_id") or "").strip()
        if persisted_identity and persisted_identity != identity:
            raise ValueError(f"INVARIANT_VIOLATION: identidade provider conflitante no ordinal {ordinal}.")
        if persisted_cd and persisted_cd != cd_documento:
            raise ValueError(f"INVARIANT_VIOLATION: cdDocumento conflitante no ordinal {ordinal}.")
        planned.append((piece, identity, cd_documento))

    changed = 0
    for piece, identity, cd_documento in planned:
        if not piece.get("provider_item_identity"):
            piece["provider_item_identity"] = identity
            changed += 1
        if not piece.get("provider_document_id"):
            piece["provider_document_id"] = cd_documento
    manifest["manifest_version"] = "2.1"
    manifest["incremental_identity"] = "esaj:idDocumento:<valor>"
    manifest["total_entries"] = len(pieces)

    temporary_path = manifest_path.with_suffix(".json.backfill.tmp")
    temporary_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary_path.replace(manifest_path)
    return {"entries": len(pieces), "identities_backfilled": changed, "provider_identities": len(seen)}


def partition_incremental_pieces(pecas: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split a received provider inventory into reusable and genuinely new pieces.

    This is intentionally performed before PDF extraction.  Duplicate factual
    identities are rejected rather than silently collapsing provider data.
    """
    seen: set[str] = set()
    reused: list[dict[str, Any]] = []
    new: list[dict[str, Any]] = []
    for piece in pecas:
        identity = str(piece.get("provider_item_identity") or "").strip()
        if not identity:
            # Direct processing of a pre-v2.1 manifest remains supported, but
            # it is deliberately never eligible for factual reuse.  This path
            # cannot turn a legacy ZIP/container identifier into a sync key.
            if piece.get("reused_existing"):
                raise ValueError("INVARIANT_VIOLATION: peça reutilizada sem provider_item_identity.")
            identity = f"legacy:{piece.get('source_identity') or piece.get('sha256') or ''}"
            if identity == "legacy:":
                raise ValueError("INVARIANT_VIOLATION: peça sem identidade de origem.")
        if identity in seen:
            raise ValueError(f"INVARIANT_VIOLATION: provider_item_identity duplicada: {identity}")
        seen.add(identity)
        (reused if piece.get("reused_existing") else new).append(piece)
    return reused, new


def merge_incremental_manifest_entries(
    previous: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge a received ZIP delta into the complete persisted piece inventory."""
    by_identity: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for entry in previous:
        identity = str(entry.get("provider_item_identity") or "").strip()
        if not identity or identity in by_identity:
            continue
        by_identity[identity] = dict(entry)
        order.append(identity)
    next_order = max((int(e.get("order") or 0) for e in by_identity.values()), default=0)
    for entry in incoming:
        identity = str(entry.get("provider_item_identity") or "").strip()
        if not identity:
            raise ValueError("INVARIANT_VIOLATION: peça incremental sem provider_item_identity")
        if identity in by_identity:
            merged = dict(by_identity[identity])
            merged.update({k: v for k, v in entry.items() if v is not None})
            merged["order"] = by_identity[identity].get("order") or entry.get("order")
            merged["document_id"] = by_identity[identity].get("document_id") or entry.get("document_id")
            merged["reused_existing"] = True
            by_identity[identity] = merged
            continue
        next_order += 1
        merged = dict(entry)
        merged["order"] = next_order
        merged["reused_existing"] = False
        by_identity[identity] = merged
        order.append(identity)
    return [by_identity[identity] for identity in order]


def esaj_document_piece_identities(document: dict[str, Any]) -> list[str]:
    """Return all provider-attested piece identities belonging to one tree item."""
    parts = document.get("parts") or [{}]
    return [
        esaj_provider_item_identity(document, part_index, part)
        for part_index, part in enumerate(parts)
    ]


def classify_esaj_inventory(
    documents: list[dict[str, Any]], known_piece_identities: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Classify provider tree items before any PDF download.

    A multipart document is reusable only when every factual provider piece is
    known.  Any new part keeps its containing tree item in NEW so the Bridge
    can request the exact authenticated ``getPDF.do`` URLs supplied by e-SAJ.
    """
    existing: list[dict[str, Any]] = []
    new: list[dict[str, Any]] = []
    for document in documents:
        identities = esaj_document_piece_identities(document)
        (existing if all(identity in known_piece_identities for identity in identities) else new).append(document)
    return existing, new


def record_incremental_bridge_document(
    store: Store, cnj: str, metadata: dict[str, Any], document_id: str,
) -> None:
    """Append provider identities received through authenticated getPDF.do.

    The individual-download path has no bulk ZIP to rewrite the manifest.  It
    therefore records only the new factual identities, so a subsequent plan
    can reuse the newly ingested document without consulting its binary hash.
    """
    manifest_path = store.process_fontes_path(cnj) / "pecas_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"cnj": cnj, "manifest_version": "2.1", "pecas": []}
    if manifest_path.is_file():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    pieces = payload.setdefault("pecas", [])
    known = {str(piece.get("provider_item_identity") or "") for piece in pieces}
    parts = metadata.get("parts") or [{}]
    order = metadata.get("order")
    for part_index, part in enumerate(parts):
        identity = esaj_provider_item_identity(metadata, part_index, part)
        if identity in known:
            continue
        pieces.append({
            "order": order,
            "provider_item_identity": identity,
            "provider_document_id": str(metadata.get("cdDocumento") or ""),
            "source_identity": identity,
            "document_id": document_id,
            "sha256": document_id,
            "source_filename_literal": metadata.get("docName") or metadata.get("title") or "",
            "folha_inicial": metadata.get("folhaInicial"),
            "folha_final": metadata.get("folhaFinal"),
            "page_count": part.get("nuPaginas") or None,
            "incremental_acquisition": "esaj_getPDF.do",
        })
        known.add(identity)
    payload["manifest_version"] = "2.1"
    payload["incremental_identity"] = "esaj:idDocumento:<valor>"
    payload["total_entries"] = len(pieces)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def clean_cnj_digits(val: Any) -> str:
    """Extrai somente os dígitos de um CNJ ou número de processo."""
    return re.sub(r"\D", "", str(val or ""))


def format_cnj(digits: str) -> str:
    """Formata 20 dígitos no padrão canônico NNNNNNN-DD.YYYY.J.TR.OOOO."""
    d = clean_cnj_digits(digits)
    if len(d) == 20:
        return f"{d[:7]}-{d[7:9]}.{d[9:13]}.{d[13]}.{d[14:16]}.{d[16:20]}"
    return str(digits)


def validate_esaj_invariants(
    cnj: str,
    metadata: dict[str, Any] | None = None,
    page_context: dict[str, Any] | None = None,
    documents: list[dict[str, Any]] | None = None,
    store: Store | None = None,
) -> str:
    """Valida rigorosamente todas as invariantes e-SAJ antes de qualquer processamento/escrita.
    
    Invariantes:
    1. process_id vem da Pasta Digital aberta (formato CNJ válido de 20 dígitos).
    2. nuProcesso da URL deve coincidir com o CNJ extraído da página.
    3. cdProcesso usado em getPDF.do / metadata deve coincidir com o processo da aba.
    4. Todo cdDocumento fica vinculado a esse process_id na origem.
    5. Backend rejeita ingestão se CNJ/URL/pageContext divergirem.
    6. Uma sincronização nunca pode criar outro processo além daquele aberto na aba.
    """
    metadata = metadata or {}
    page_context = page_context or {}
    documents = documents or []

    # 1. Validação de formato do CNJ
    cnj_digits = clean_cnj_digits(cnj)
    if len(cnj_digits) != 20:
        raise ValueError(
            f"INVARIANT_VIOLATION: CNJ '{cnj}' é inválido. Esperados 20 dígitos numéricos."
        )
    formatted_cnj = format_cnj(cnj_digits)

    # 2. Invariante: nuProcesso da URL deve coincidir com o CNJ
    url_str = metadata.get("url") or page_context.get("url")
    if url_str:
        parsed = urlparse(url_str)
        qs = parse_qs(parsed.query)
        url_nu = qs.get("nuProcesso", [None])[0] or qs.get("processo.numero", [None])[0]
        if url_nu:
            url_digits = clean_cnj_digits(url_nu)
            if url_digits and url_digits != cnj_digits:
                raise ValueError(
                    f"INVARIANT_VIOLATION: nuProcesso da URL ('{url_nu}') diverge do CNJ do processo ('{cnj}')."
                )

    # 3. Invariante: pageContext.nuProcesso deve coincidir com o CNJ
    ctx_nu = page_context.get("nuProcesso")
    if ctx_nu:
        ctx_digits = clean_cnj_digits(ctx_nu)
        if ctx_digits and ctx_digits != cnj_digits:
            raise ValueError(
                f"INVARIANT_VIOLATION: pageContext.nuProcesso ('{ctx_nu}') diverge do CNJ do processo ('{cnj}')."
            )

    # 4. Invariante: cdProcesso da URL / contexto / documentos deve coincidir
    tab_cd_proc = (
        str(metadata.get("cdProcesso") or "").strip()
        or str(page_context.get("cdProcesso") or "").strip()
    )
    if url_str:
        parsed = urlparse(url_str)
        qs = parse_qs(parsed.query)
        url_cd = qs.get("processo.codigo", [None])[0]
        if url_cd:
            url_cd_str = str(url_cd).strip()
            if tab_cd_proc and url_cd_str != tab_cd_proc:
                raise ValueError(
                    f"INVARIANT_VIOLATION: cdProcesso da URL ('{url_cd_str}') diverge do cdProcesso informado ('{tab_cd_proc}')."
                )
            if not tab_cd_proc:
                tab_cd_proc = url_cd_str

    if tab_cd_proc and documents:
        for doc in documents:
            params_str = doc.get("parametros")
            if params_str:
                doc_qs = parse_qs(params_str)
                doc_cd = doc_qs.get("cdProcesso", [None])[0]
                if doc_cd and str(doc_cd).strip() != tab_cd_proc:
                    raise ValueError(
                        f"INVARIANT_VIOLATION: cdProcesso do documento '{doc.get('title')}' ('{doc_cd}') diverge do processo da aba ('{tab_cd_proc}')."
                    )

    # 5. Invariante: todo cdDocumento fica vinculado a esse process_id na origem
    if store is not None and metadata.get("cdDocumento"):
        cd_doc = str(metadata["cdDocumento"]).strip()
        db = store.connect()
        try:
            row = db.execute(
                "SELECT process_id FROM provider_artifacts WHERE source_artifact_id=? AND source_origin='pastadigital_esaj'",
                (cd_doc,),
            ).fetchone()
            if row and clean_cnj_digits(row[0]) != cnj_digits:
                raise ValueError(
                    f"INVARIANT_VIOLATION: cdDocumento '{cd_doc}' já pertence ao processo '{row[0]}', não a '{formatted_cnj}'."
                )
        finally:
            db.close()
        from core.process_storage import provider_artifact_owner
        registered_owner = provider_artifact_owner("pastadigital_esaj", cd_doc, root=store.root)
        if registered_owner and clean_cnj_digits(registered_owner) != cnj_digits:
            raise ValueError(
                f"INVARIANT_VIOLATION: cdDocumento '{cd_doc}' já pertence ao processo '{registered_owner}', não a '{formatted_cnj}'."
            )

    return formatted_cnj


def validate_folio_set(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Valida a foliação por teoria dos conjuntos (union_count, overlap_count, gap_count, gap_ranges)."""
    folio_occurrences: dict[int, list[str]] = {}
    valid_pieces = 0

    for doc in documents:
        f_ini = doc.get("folhaInicial")
        f_fim = doc.get("folhaFinal")
        cd_doc = str(doc.get("cdDocumento") or doc.get("title") or "").strip()
        if f_ini is not None and f_fim is not None:
            valid_pieces += 1
            for fol in range(int(f_ini), int(f_fim) + 1):
                folio_occurrences.setdefault(fol, []).append(cd_doc)

    if not folio_occurrences:
        return {
            "union_count": 0,
            "overlap_count": 0,
            "gap_count": 0,
            "min_folio": 0,
            "max_folio": 0,
            "gap_ranges": [],
            "expected_physical_pages": 0
        }

    all_folios = sorted(folio_occurrences.keys())
    min_fol = all_folios[0]
    max_fol = all_folios[-1]
    union_set = set(all_folios)
    union_count = len(union_set)

    # Overlaps: folios appearing in more than 1 piece
    overlap_count = sum(1 for fol, docs in folio_occurrences.items() if len(docs) > 1)

    # Gaps: folios missing between min_fol and max_fol
    gap_ranges = []
    missing_folios = [f for f in range(min_fol, max_fol + 1) if f not in union_set]
    gap_count = len(missing_folios)

    if missing_folios:
        start_gap = missing_folios[0]
        prev_gap = missing_folios[0]
        for f in missing_folios[1:]:
            if f == prev_gap + 1:
                prev_gap = f
            else:
                gap_ranges.append({
                    "start": start_gap,
                    "end": prev_gap,
                    "count": prev_gap - start_gap + 1
                })
                start_gap = f
                prev_gap = f
        gap_ranges.append({
            "start": start_gap,
            "end": prev_gap,
            "count": prev_gap - start_gap + 1
        })

    return {
        "union_count": union_count,
        "overlap_count": overlap_count,
        "gap_count": gap_count,
        "min_folio": min_fol,
        "max_folio": max_fol,
        "gap_ranges": gap_ranges,
        "expected_physical_pages": union_count
    }


def sanitize_cpopg_payload(data: Any) -> Any:
    """Recursivamente remove campos sensíveis de tokens, cookies, tickets e credenciais."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in ("token", "ticket", "cookie", "session", "auth", "secret", "csrf", "nonce", "password", "senha")):
                continue
            cleaned[k] = sanitize_cpopg_payload(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_cpopg_payload(item) for item in data]
    elif isinstance(data, str):
        if "ticket=" in data.lower() or "token=" in data.lower() or "jsessionid" in data.lower():
            return re.sub(r"(?i)(ticket|token|jsessionid)=[^&]+", r"\1=[REDACTED]", data)
        return data
    return data


def parse_cpopg_datetime(dt_str: str | None) -> tuple[str | None, str]:
    """Interpreta data/hora brasileira da capa CPOPG (ex: '15/10/2024 14:30' ou '15/10/2024')."""
    if not dt_str:
        return None, "UNKNOWN"
    s = str(dt_str).strip()
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})(?:\s*(?:às|as)?\s*(\d{2}):(\d{2})(?::(\d{2}))?)?", s)
    if m:
        day, month, year, hour, minute, second = m.groups()
        if hour and minute:
            sec = second or "00"
            return f"{year}-{month}-{day}T{hour}:{minute}:{sec}", "EXACT"
        return f"{year}-{month}-{day}", "DAY"
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s, "EXACT" if ("T" in s or " " in s) else "DAY"
    return None, "UNKNOWN"


def _ensure_process(db: sqlite3.Connection, process_id: str) -> None:
    db.execute(
        "INSERT OR IGNORE INTO processes VALUES(?,?,?)",
        (process_id, "ACTIVE", now()),
    )


def _materialize_movements_with_projection_policy(
    db: sqlite3.Connection,
    process_id: str,
    *,
    manifest_or_root: Any,
) -> dict[str, Any]:
    """Materialize Movements and safely repair the provider-boundary projection once.

    The historical manifest projection promoted unidentified pieces to Movements.
    A one-time stale prune is safe only before AI-derived movement summaries/case
    synthesis exist.  Otherwise preserve rows and expose a pending repair flag.
    """
    from core.documentos.movement_store_v1 import materialize_movements

    repair_version = "movement-projection-provider-boundaries-v2"
    repair_applied = bool(
        db.execute(
            "SELECT 1 FROM schema_migrations WHERE version=?",
            (repair_version,),
        ).fetchone()
    )
    existing_count = db.execute(
        "SELECT count(*) FROM movements WHERE process_id=?",
        (process_id,),
    ).fetchone()[0]
    summary_count = (
        db.execute(
            """SELECT count(*) FROM movement_summaries s
               JOIN movements m ON m.movement_id=s.movement_id
               WHERE m.process_id=?""",
            (process_id,),
        ).fetchone()[0]
        if db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='movement_summaries'"
        ).fetchone()
        else 0
    )
    synthesis_count = (
        db.execute(
            "SELECT count(*) FROM case_syntheses WHERE process_id=?",
            (process_id,),
        ).fetchone()[0]
        if db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='case_syntheses'"
        ).fetchone()
        else 0
    )
    safe_repair = (
        not repair_applied
        and existing_count > 0
        and summary_count == 0
        and synthesis_count == 0
    )
    repair_pending = bool(
        not repair_applied and existing_count > 0 and not safe_repair
    )

    if repair_pending:
        # Never mix old and new movement identities after AI-derived content
        # already exists. Reconciliation must preserve/re-map those derivatives
        # explicitly before the projection can advance.
        return {
            "process_id": process_id,
            "projected": existing_count,
            "inserted": 0,
            "updated": 0,
            "unchanged": existing_count,
            "deleted": 0,
            "projection_repair_applied": False,
            "projection_repair_pending": True,
            "projection_repair_blocked_by": {
                "movement_summaries": summary_count,
                "case_syntheses": synthesis_count,
            },
        }

    result = materialize_movements(
        db,
        process_id,
        manifest_or_root=manifest_or_root,
        prune_stale=safe_repair,
    )
    result["projection_repair_applied"] = safe_repair
    result["projection_repair_pending"] = False

    if not repair_applied and (safe_repair or existing_count == 0):
        db.execute(
            "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?, ?)",
            (
                repair_version,
                datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            ),
        )
        db.commit()
    return result


def plan_process_sync(
    store: Store,
    cnj: str,
    metadata: dict[str, Any] | None = None,
    participants: list[dict[str, Any]] | None = None,
    movements: list[dict[str, Any]] | None = None,
    documents: list[dict[str, Any]] | None = None,
    page_context: dict[str, Any] | None = None,
    cpopg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    store = store.for_process(cnj)
    """Compara a árvore do e-SAJ com o índice local do Themis e calcula o plano de sincronização."""
    metadata = metadata or {}
    participants = participants or []
    movements = movements or []
    documents = documents or []
    page_context = page_context or {}
    cpopg = sanitize_cpopg_payload(cpopg) if cpopg else None

    # Validação estrita de invariantes
    cnj = validate_esaj_invariants(
        cnj=cnj,
        metadata=metadata,
        page_context=page_context,
        documents=documents,
        store=store,
    )

    from core.process_storage import claim_provider_artifact_identities, provider_artifact_owners
    artifact_owners = provider_artifact_owners(root=store.root)
    for document in documents:
        cd_doc = str(document.get("cdDocumento") or "").strip()
        owner = artifact_owners.get(("pastadigital_esaj", cd_doc)) if cd_doc else None
        if owner and clean_cnj_digits(owner) != clean_cnj_digits(cnj):
            raise ValueError(
                f"INVARIANT_VIOLATION: cdDocumento '{cd_doc}' já pertence ao processo '{owner}', não a '{cnj}'."
            )

    from core.documentos.knowledge_objects_v1 import (
        ID_NAMESPACE,
        _fingerprint,
        _json,
        migrate as migrate_knowledge,
    )
    from core.documentos.domain_objects_v1 import (
        migrate as migrate_domain,
        upsert_process_metadata,
    )
    from core.themis_fontes import normalize_name

    def upsert_cpopg_party_relation(db, *, entity_id, role, role_raw, stamp):
        """Upsert capa relations across current and legacy fingerprints."""
        rel_fp = _fingerprint("process", cnj, entity_id, role, role_raw)
        rel_id = "party_" + uuid.uuid5(ID_NAMESPACE, rel_fp).hex
        existing = db.execute(
            "SELECT party_relation_id FROM party_relations WHERE relation_fingerprint=?",
            (rel_fp,),
        ).fetchone()
        if not existing:
            existing = db.execute(
                """SELECT party_relation_id FROM party_relations
                   WHERE owner_type='PROCESS' AND owner_id=? AND entity_id=?
                     AND role=? AND role_raw=?
                   ORDER BY party_relation_id LIMIT 1""",
                (cnj, entity_id, role, role_raw),
            ).fetchone()
        if existing:
            db.execute(
                """UPDATE party_relations
                   SET entity_id=?, role=?, role_raw=?, status='CONFIRMED',
                       confidence='HIGH', updated_at=?
                   WHERE party_relation_id=?""",
                (entity_id, role, role_raw, stamp, existing["party_relation_id"]),
            )
            return existing["party_relation_id"]
        db.execute(
            """INSERT INTO party_relations(party_relation_id, entity_id, owner_type, owner_id, role, role_raw, status, confidence, relation_fingerprint, extraction_run_id, created_at, updated_at)
            VALUES(?, ?, 'PROCESS', ?, ?, ?, 'CONFIRMED', 'HIGH', ?, NULL, ?, ?)""",
            (rel_id, entity_id, cnj, role, role_raw, rel_fp, stamp, stamp),
        )
        return rel_id

    store.db_path.parent.mkdir(parents=True, exist_ok=True)
    migrate_knowledge(store.db_path)
    migrate_domain(store.db_path)

    # 0. Criar raiz física do processo e salvar snapshot JSON fiel da fonte (versionado e latest)
    process_dir = store.process_path(cnj)
    process_docs_dir = store.process_documents_path(cnj)
    process_fontes_dir = store.process_parts_path(cnj)
    process_dir.mkdir(parents=True, exist_ok=True)
    process_docs_dir.mkdir(parents=True, exist_ok=True)
    process_fontes_dir.mkdir(parents=True, exist_ok=True)

    # This must precede writing the received snapshot: comparison is against
    # the prior persisted provider inventory, never ZIP bytes or filenames.
    known_piece_identities = set(_persisted_provider_document_ids(store, cnj))
    already_ingested, needed = classify_esaj_inventory(documents, known_piece_identities)

    previous_snapshot = None
    previous_snapshot_path = store.process_snapshot_path(cnj)
    if previous_snapshot_path.is_file():
        try:
            previous_snapshot = json.loads(previous_snapshot_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous_snapshot = None
    unchanged_captured_state = (
        not needed
        and previous_snapshot is not None
        and previous_snapshot.get("metadata", {}) == metadata
        and previous_snapshot.get("page_context", {}) == page_context
        and previous_snapshot.get("participants", []) == participants
        and previous_snapshot.get("movements", []) == movements
        and previous_snapshot.get("documents", []) == documents
    )

    capture_time = now()
    stamp_safe = capture_time.replace(":", "-").replace(".", "-")
    
    # Validação de foliação por teoria dos conjuntos
    folio_stats = validate_folio_set(documents)

    snapshot_payload = {
        "cnj": cnj,
        "captured_at": capture_time,
        "metadata": metadata,
        "page_context": page_context,
        "participants": participants,
        "movements": movements,
        "documents": documents,
        "folio_set_validation": folio_stats
    }
    
    # Persiste snapshot latest da Pasta Digital
    store.process_snapshot_path(cnj).write_text(
        json.dumps(snapshot_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    
    # Persiste snapshot versionado imutável da Pasta Digital
    versioned_snap_path = store.process_snapshot_versioned_path(cnj, stamp_safe)
    versioned_snap_path.parent.mkdir(parents=True, exist_ok=True)
    versioned_snap_path.write_text(
        json.dumps(snapshot_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Persiste snapshot CPOPG se disponível
    cpopg_snap_path = None
    if cpopg:
        cpopg_snap_path = store.process_cpopg_snapshot_path(cnj)
        cpopg_snap_path.parent.mkdir(parents=True, exist_ok=True)
        cpopg_snap_path.write_text(
            json.dumps(cpopg, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        versioned_cpopg_path = store.process_cpopg_snapshot_versioned_path(cnj, stamp_safe)
        versioned_cpopg_path.parent.mkdir(parents=True, exist_ok=True)
        versioned_cpopg_path.write_text(
            json.dumps(cpopg, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    store.process_manifest_path(cnj).write_text(
        json.dumps(
            {
                "cnj": cnj,
                "status": "CAPTURED",
                "pipeline_status": "CAPTURED",
                "total_documents": len(documents),
                "total_movements": len(movements),
                "total_participants": len(participants),
                "source": "pastadigital_esaj",
                "synced_at": capture_time,
                "folio_stats": folio_stats,
                "latest_snapshot_version": stamp_safe,
                "has_cpopg_snapshot": bool(cpopg)
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    db = store.connect()
    try:
        db.execute("BEGIN")
        _ensure_process(db, cnj)

        # 1. Registra proveniência do processo
        cd_processo = metadata.get("cdProcesso") or metadata.get("nuProcesso") or cnj
        db.execute(
            """INSERT INTO process_sources(process_id, source_type, source_id, created_at)
            VALUES(?, ?, ?, ?) ON CONFLICT DO NOTHING""",
            (cnj, "ESAJ_PASTADIGITAL", str(cd_processo), now()),
        )

        hearings_synced = 0
        cpopg_parties_synced = 0
        cpopg_lawyers_synced = 0

        # Se CPOPG foi fornecido, materializa metadados cadastrais, fontes, partes, advogados e audiências
        if cpopg:
            basic_data = cpopg.get("basic_data") or {}
            
            # 1.1 Registra proveniência CPOPG
            db.execute(
                """INSERT INTO process_sources(process_id, source_type, source_id, created_at)
                VALUES(?, ?, ?, ?) ON CONFLICT DO NOTHING""",
                (cnj, "ESAJ_CPOPG", str(cd_processo), capture_time),
            )

            # 1.2 Materializa process_metadata
            summary_parts = []
            if basic_data.get("juiz"):
                summary_parts.append(f"Juiz: {basic_data['juiz']}")
            if basic_data.get("distribuicao"):
                summary_parts.append(f"Distribuição: {basic_data['distribuicao']}")
            if basic_data.get("controle"):
                summary_parts.append(f"Controle: {basic_data['controle']}")
            if basic_data.get("area"):
                summary_parts.append(f"Área: {basic_data['area']}")
            if basic_data.get("valor_acao"):
                summary_parts.append(f"Valor da Ação: {basic_data['valor_acao']}")
            if basic_data.get("outros_assuntos"):
                summary_parts.append(f"Outros Assuntos: {basic_data['outros_assuntos']}")
            if basic_data.get("outros_numeros"):
                summary_parts.append(f"Outros Números: {basic_data['outros_numeros']}")
            if basic_data.get("segredo_justica"):
                summary_parts.append("Segredo de Justiça: Sim")

            summary_str = " | ".join(summary_parts)
            meta_prov = {
                "source": "cpopg_esaj",
                "captured_at": capture_time,
                "canonical_url": cpopg.get("canonical_url"),
                "basic_data": basic_data,
            }

            upsert_process_metadata(
                db,
                cnj,
                commit=False,
                classe=basic_data.get("classe") or None,
                assunto=basic_data.get("assunto") or None,
                tribunal="TJSP",
                comarca=basic_data.get("foro") or None,
                unidade=basic_data.get("vara") or None,
                grau="1º Grau",
                status="ACTIVE",
                fase="Em tramitação",
                summary=summary_str or None,
                provenance=meta_prov,
            )

            # 1.3 Materializa Partes CPOPG
            for p in cpopg.get("parties", []):
                p_name = " ".join(str(p.get("name", "")).split())
                if not p_name:
                    continue
                p_role = str(p.get("role") or "PARTE").strip()
                norm = normalize_name(p_name)
                identifiers = {}
                identity_fp = _fingerprint("UNKNOWN", norm)

                row = db.execute(
                    "SELECT entity_id FROM legal_entities WHERE identity_fingerprint=?",
                    (identity_fp,),
                ).fetchone()
                if not row:
                    # Capa pode fornecer OAB para uma pessoa já criada pela
                    # relação RepreLeg. Reconciliar somente nome normalizado
                    # quando a identidade anterior ainda não tem identificadores.
                    row = db.execute(
                        "SELECT entity_id FROM legal_entities WHERE normalized_name=? AND (identifiers_json IS NULL OR identifiers_json='{}' OR identifiers_json=?) ORDER BY entity_id LIMIT 1",
                        (norm, _json(identifiers)),
                    ).fetchone()
                if row:
                    e_id = row[0]
                    db.execute(
                        "UPDATE legal_entities SET display_name=?, normalized_name=?, updated_at=? WHERE entity_id=?",
                        (p_name, norm, capture_time, e_id),
                    )
                else:
                    e_id = "entity_" + uuid.uuid5(ID_NAMESPACE, identity_fp).hex
                    db.execute(
                        """INSERT INTO legal_entities(entity_id, entity_type, display_name, normalized_name, identifiers_json, identity_fingerprint, created_at, updated_at)
                        VALUES(?, ?, ?, ?, '{}', ?, ?, ?)""",
                        (e_id, "UNKNOWN", p_name, norm, identity_fp, capture_time, capture_time),
                    )

                upsert_cpopg_party_relation(
                    db, entity_id=e_id, role=p_role, role_raw=p_role, stamp=capture_time
                )
                cpopg_parties_synced += 1

            # 1.4 Materializa Advogados com OAB CPOPG
            for law in cpopg.get("lawyers", []):
                l_name = " ".join(str(law.get("lawyer_name", "")).split())
                if not l_name:
                    continue
                oab = law.get("oab")
                identifiers = {"oab": oab} if oab else {}
                norm = normalize_name(l_name)
                identity_fp = _fingerprint("PERSON", _json(identifiers) if identifiers else norm)

                # When the cover has no OAB, prefer the same-name identity
                # already attached to this process (for example a RepreLeg)
                # over a duplicate global PERSON identity from an older run.
                row = None
                if not oab:
                    row = db.execute(
                        """SELECT le.entity_id FROM legal_entities le
                           JOIN party_relations pr ON pr.entity_id=le.entity_id
                           WHERE pr.owner_type='PROCESS' AND pr.owner_id=?
                             AND le.normalized_name=?
                           ORDER BY le.entity_id LIMIT 1""",
                        (cnj, norm),
                    ).fetchone()
                if not row:
                    row = db.execute(
                        "SELECT entity_id FROM legal_entities WHERE identity_fingerprint=?",
                        (identity_fp,),
                    ).fetchone()
                if row:
                    e_id = row[0]
                    db.execute(
                        "UPDATE legal_entities SET display_name=?, normalized_name=?, identifiers_json=?, updated_at=? WHERE entity_id=?",
                        (l_name, norm, _json(identifiers), capture_time, e_id),
                    )
                else:
                    # Reconcile a lawyer previously materialized from a
                    # structured RepreLeg/party relation when the refreshed
                    # cover carries the same name but no OAB.
                    row = db.execute(
                        """SELECT entity_id FROM legal_entities
                           WHERE normalized_name=?
                             AND (identifiers_json IS NULL OR identifiers_json='{}'
                                  OR identifiers_json=?)
                           ORDER BY entity_id LIMIT 1""",
                        (norm, _json(identifiers)),
                    ).fetchone()
                    if row:
                        e_id = row[0]
                        db.execute(
                            """UPDATE legal_entities
                               SET display_name=?, normalized_name=?, identifiers_json=?, updated_at=?
                               WHERE entity_id=?""",
                            (l_name, norm, _json(identifiers), capture_time, e_id),
                        )
                    else:
                        e_id = "entity_" + uuid.uuid5(ID_NAMESPACE, identity_fp).hex
                        db.execute(
                            """INSERT INTO legal_entities(entity_id, entity_type, display_name, normalized_name, identifiers_json, identity_fingerprint, created_at, updated_at)
                            VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                            (e_id, "PERSON", l_name, norm, _json(identifiers), identity_fp, capture_time, capture_time),
                        )

                party_rep = law.get("party_represented") or ""
                role_raw = f"Advogado ({party_rep})" if party_rep else "Advogado"
                upsert_cpopg_party_relation(
                    db,
                    entity_id=e_id,
                    role="ADVOGADO",
                    role_raw=role_raw,
                    stamp=capture_time,
                )
                cpopg_lawyers_synced += 1

            # 1.5 Materializa Audiências CPOPG
            for h in cpopg.get("hearings", []):
                dt_raw = h.get("data_hora")
                sched, prec = parse_cpopg_datetime(dt_raw)
                h_type = (h.get("tipo") or "Audiência").strip()
                h_sit = (h.get("situacao") or "DESIGNADA").strip()
                h_loc = h.get("location")
                
                fp = hashlib.sha256(f"{cnj}_{h_type}_{sched}_{h_loc}".encode("utf-8")).hexdigest()
                h_id = "hearing_" + uuid.uuid5(ID_NAMESPACE, fp).hex
                h_prov = json.dumps({"source": "cpopg_esaj", "raw": h}, ensure_ascii=False)
                h_refs = json.dumps([{"source": "cpopg", "type": "cpopg_cover"}], ensure_ascii=False)

                row = db.execute("SELECT hearing_id FROM hearings WHERE fingerprint=?", (fp,)).fetchone()
                if row:
                    h_id = row[0]
                    db.execute(
                        """UPDATE hearings SET scheduled_at=?, date_precision=?, location=?, status=?, outcome_notes=?,
                           provenance_json=?, updated_at=? WHERE hearing_id=?""",
                        (sched, prec, h_loc, h_sit, f"Situação: {h_sit}", h_prov, capture_time, h_id),
                    )
                else:
                    db.execute(
                        """INSERT INTO hearings(hearing_id, process_id, hearing_type, scheduled_at, date_precision,
                           location, meeting_info, status, outcome_notes, source_refs_json, provenance_json,
                           fingerprint, created_at, updated_at, extraction_run_id)
                        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
                        (h_id, cnj, h_type, sched, prec, h_loc, None, h_sit, f"Situação: {h_sit}", h_refs, h_prov, fp, capture_time, capture_time),
                    )
                hearings_synced += 1

        # 2. Persiste partes e participantes se disponíveis
        parties_synced = 0
        if participants:
            try:
                stamp = now()

                for part in participants:
                    d_name = " ".join(str(part.get("display_name", "")).split())
                    if not d_name:
                        continue
                    e_type = str(part.get("entity_type", "UNKNOWN")).upper()
                    if e_type not in {"PERSON", "ORGANIZATION", "UNKNOWN"}:
                        e_type = "UNKNOWN"
                    norm = normalize_name(d_name)
                    identifiers = part.get("identifiers") or {}
                    identity_fp = _fingerprint(e_type, _json(identifiers) if identifiers else norm)

                    row = db.execute(
                        "SELECT entity_id FROM legal_entities WHERE identity_fingerprint=?",
                        (identity_fp,),
                    ).fetchone()
                    if row:
                        e_id = row[0]
                        db.execute(
                            "UPDATE legal_entities SET display_name=?, normalized_name=?, identifiers_json=?, updated_at=? WHERE entity_id=?",
                            (d_name, norm, _json(identifiers), stamp, e_id),
                        )
                    else:
                        e_id = "entity_" + uuid.uuid5(ID_NAMESPACE, identity_fp).hex
                        db.execute(
                            """INSERT INTO legal_entities(entity_id, entity_type, display_name, normalized_name, identifiers_json, identity_fingerprint, created_at, updated_at)
                            VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                            (e_id, e_type, d_name, norm, _json(identifiers), identity_fp, stamp, stamp),
                        )

                    role_raw = part.get("role") or "PARTE"
                    role = str(role_raw).strip() or "PARTE"
                    rel_fp = _fingerprint("process", cnj, e_id, role, role_raw)
                    rel_id = "party_" + uuid.uuid5(ID_NAMESPACE, rel_fp).hex

                    db.execute(
                        """INSERT INTO party_relations(party_relation_id, entity_id, owner_type, owner_id, role, role_raw, status, confidence, relation_fingerprint, extraction_run_id, created_at, updated_at)
                        VALUES(?, ?, 'PROCESS', ?, ?, ?, 'CONFIRMED', 'HIGH', ?, NULL, ?, ?)
                        ON CONFLICT(relation_fingerprint) DO UPDATE SET status=excluded.status, confidence=excluded.confidence, updated_at=excluded.updated_at""",
                        (rel_id, e_id, cnj, role, role_raw, rel_fp, stamp, stamp),
                    )
                    parties_synced += 1
            except Exception as p_err:
                print(f"[Themis Bridge Sync] Aviso ao persistir partes: {p_err}")

        # 3. Persiste movimentações com deduplicação
        movements_synced = 0
        for source_order, mov in enumerate(movements):
            m_date = mov.get("date") or mov.get("occurred_at")
            m_name = mov.get("name") or mov.get("movement_type") or "Movimentação registrada"
            m_text = mov.get("content") or m_name
            m_code = mov.get("code") or mov.get("movement_code")
            src_m_id = mov.get("source_movement_id") or mov.get("cdMovimento")

            fp = hashlib.sha256(
                f"{cnj}_{m_date}_{m_name}_{m_text[:80]}".encode("utf-8")
            ).hexdigest()[:16]

            register_movement(
                db,
                process_id=cnj,
                movement_type=m_name,
                occurred_at=m_date,
                content=m_text,
                source_movement_id=str(src_m_id) if src_m_id else None,
                movement_code=str(m_code) if m_code else None,
                movement_fingerprint=fp,
                provenance={"source": "esaj_bridge", "metadata": metadata, "source_order": source_order},
            )
            movements_synced += 1

        db.commit()

        from core.documentos.process_movement_linker_v1 import materialize_links as materialize_process_movement_links
        try:
            process_movement_links = materialize_process_movement_links(db, cnj)
        except Exception as link_err:
            process_movement_links = {"error": str(link_err)}
            print(f"[Themis Bridge Sync] Aviso ao associar cronologia provider aos documentos: {link_err}")

        # The plan route also owns the metadata-only/0-NEW path.  The Browser
        # Bridge may have received a fresh CPOPG cover while no PDF needs to
        # be downloaded; project the structured participant context here so
        # that the early-return path does not leave only party_relations.
        if unchanged_captured_state and not cpopg:
            # A byte-for-byte repeat of the captured provider state is a true
            # no-op. In particular, do not rewrite canonical participant or
            # representation projections just because the browser re-sent an
            # unchanged 0-NEW inventory.
            participant_context_materialization = {"participants": 0, "representations": 0}
        else:
            from core.documentos.participant_context_store_v1 import materialize_all as materialize_participant_context
            participant_context_materialization = materialize_participant_context(db)

        # A listagem operacional usa catalog.db quando ele existe. Registrar
        # discovery depois de persistir a captura garante que um pacote novo
        # apareça na Themis sem copiar conteúdo processual para o catálogo.
        from core.process_storage import catalog_discovery, register_discovery
        if catalog_discovery(cnj, root=store.root) is None or needed:
            register_discovery(
                cnj,
                root=store.root,
                provider="pastadigital_esaj",
                tribunal="TJSP",
                external_id=str(metadata.get("cdProcesso") or metadata.get("nuProcesso") or cnj),
                discovery_status="KNOWN",
                observed_at=capture_time,
            )
        claim_provider_artifact_identities(
            "pastadigital_esaj",
            [str(document.get("cdDocumento") or "") for document in documents],
            cnj,
            root=store.root,
        )

        process_relations_synced = 0
        process_relations_error = None
        if cpopg:
            try:
                from core.process_relations import relations_from_cpopg
                process_relations_synced = len(
                    relations_from_cpopg(
                        cnj,
                        cpopg,
                        root=store.root,
                        observed_at=capture_time,
                    )
                )
            except Exception as rel_err:
                # Relation discovery is metadata enrichment. Keep the Process
                # Package sync valid and retry on the next cover refresh.
                process_relations_error = str(rel_err)
                print(f"[Themis Bridge Sync] Aviso ao persistir relações processuais: {rel_err}")

        movement_projection_repair = None
        if not needed:
            # 0-NEW is still a synchronization point. It must be able to repair
            # a stale derived Movement projection without re-downloading PDFs.
            movement_projection_repair = _materialize_movements_with_projection_policy(
                db,
                cnj,
                manifest_or_root=store.root,
            )
            if movement_projection_repair.get("projection_repair_applied"):
                from core.documentos.participant_context_store_v1 import materialize_all as materialize_participant_context
                participant_context_materialization = materialize_participant_context(db)
                db.close()
                db = None
                _finalize_process_package(store, cnj)

        return {
            "status": "ok",
            "cnj": cnj,
            "total_documents_online": len(documents),
            "already_ingested_count": len(already_ingested),
            "already_ingested_ids": [
                str(d.get("cdDocumento")) for d in already_ingested if d.get("cdDocumento")
            ],
            "needed_count": len(needed),
            "needed_documents": needed,
            "parties_synced": parties_synced + cpopg_parties_synced + cpopg_lawyers_synced,
            "movements_synced": movements_synced,
            "process_movement_links": process_movement_links,
            "cpopg_synced": bool(cpopg),
            "hearings_synced": hearings_synced,
            "cpopg_parties_synced": cpopg_parties_synced,
            "cpopg_lawyers_synced": cpopg_lawyers_synced,
            "process_relations_synced": process_relations_synced,
            "process_relations_error": process_relations_error,
            "cpopg_snapshot_path": str(cpopg_snap_path) if cpopg_snap_path else None,
            "participant_context": participant_context_materialization,
            "movement_projection_repair": movement_projection_repair,
            "needs_download": len(needed) > 0,
        }
    except Exception:
        if db is not None:
            db.rollback()
        raise
    finally:
        if db is not None:
            db.close()


def ingest_bridge_document(
    store: Store,
    cnj: str,
    filename: str,
    pdf_bytes: bytes,
    parts_bytes: list[bytes] | None = None,
    metadata: dict[str, Any] | None = None,
    page_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    store = store.for_process(cnj)
    """Ingere binário PDF recebido via bridge na raiz física do processo, atualiza páginas e proveniência."""
    metadata = metadata or {}
    page_context = page_context or {}

    # Validação estrita de invariantes
    cnj = validate_esaj_invariants(
        cnj=cnj,
        metadata=metadata,
        page_context=page_context,
        store=store,
    )

    # 1. Ordem Transacional 1: process / snapshot / source metadata
    db = store.connect()
    try:
        db.execute("BEGIN")
        _ensure_process(db, cnj)
        cd_processo = metadata.get("cdProcesso") or metadata.get("nuProcesso") or cnj
        db.execute(
            """INSERT INTO process_sources(process_id, source_type, source_id, created_at)
            VALUES(?, ?, ?, ?) ON CONFLICT DO NOTHING""",
            (cnj, "ESAJ_PASTADIGITAL", str(cd_processo), now()),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    # Garante existência do manifesto do processo se ainda não existir
    manifest_p = store.process_manifest_path(cnj)
    if not manifest_p.exists():
        manifest_p.parent.mkdir(parents=True, exist_ok=True)
        manifest_data = {
            "cnj": cnj,
            "created_at": now(),
            "updated_at": now(),
            "source": "pastadigital_esaj",
            "metadata": metadata,
        }
        manifest_p.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. Ordem Transacional 2: source parts / document / derived relations (Atômico por peça)
    created_files: list[Path] = []
    try:
        # Salva partes originais brutas na raiz canônica do processo se existirem
        if parts_bytes and len(parts_bytes) > 0:
            parts_dir = store.process_parts_path(cnj)
            parts_dir.mkdir(parents=True, exist_ok=True)
            cd_doc_prefix = str(metadata.get("cdDocumento") or "doc").strip()
            for p_idx, p_bytes in enumerate(parts_bytes, 1):
                if p_bytes.startswith(b"%PDF"):
                    p_file = parts_dir / f"{cd_doc_prefix}_parte_{p_idx}.pdf"
                    p_file.write_bytes(p_bytes)
                    created_files.append(p_file)

        # Se há múltiplas partes, faz o merge sequencial fiel
        if parts_bytes and len(parts_bytes) > 1:
            try:
                import pypdfium2 as pdfium
                import io
                out_pdf = pdfium.PdfDocument.new()
                for b in parts_bytes:
                    if b.startswith(b"%PDF"):
                        src = pdfium.PdfDocument(b)
                        out_pdf.import_pages(src)
                        src.close()
                buf = io.BytesIO()
                out_pdf.save(buf)
                out_pdf.close()
                pdf_bytes = buf.getvalue()
            except Exception as merge_err:
                print(f"[Themis Bridge] Aviso no merge de partes com pypdfium2: {merge_err}")

        if not pdf_bytes.startswith(b"%PDF"):
            raise ValueError("Arquivo inválido: assinatura %PDF não encontrada")

        # Salva na raiz canônica física do processo (derivados/pecas)
        process_docs_dir = store.process_documents_path(cnj)
        process_docs_dir.mkdir(parents=True, exist_ok=True)

        safe_name = f"{filename}"
        target_path = process_docs_dir / safe_name
        target_path.write_bytes(pdf_bytes)
        created_files.append(target_path)

        # Ingestão canônica do documento e páginas diretamente na raiz física do processo
        did = hashlib.sha256(pdf_bytes).hexdigest()
        pages = themis_pdf.hybrid_pages(target_path, themis_pdf.open_pdf(target_path), include_visual_asset_sources=False)
        stamp = now()
        manifest = {
            "format_version": 4,
            "document_id": did,
            "sha256": did,
            "size_bytes": len(pdf_bytes),
            "pages": len(pages),
            "format": "PDF",
            "known_paths": [str(target_path)],
            "canonical_source_path": str(target_path),
            "status": "process_confirmed_explicitly",
            "ingested_at": stamp,
            "normalization_version": 2,
            "extractors": {"tool_version": "0.1.0", "pdfium": "1.3.0", "pypdf": "6.14.2"},
            "process_id": cnj,
            "process_resolution": {"process_id": cnj, "confidence": 1.0, "source": "explicit_bridge_sync"},
        }

        # Registro de proveniência factual do e-SAJ
        cd_doc = str(metadata.get("cdDocumento") or "").strip()
        doc_name = metadata.get("docName") or metadata.get("title") or filename
        doc_type = metadata.get("deTipoDocDigital") or metadata.get("docType") or doc_name

        db = store.connect()
        try:
            db.execute("BEGIN")
            _ensure_process(db, cnj)
            from core.documentos.themis_documentos import index_document
            index_document(db, manifest, pages)

            register_provider_artifact(
                db,
                process_id=cnj,
                source_origin="pastadigital_esaj",
                source_artifact_id=cd_doc if cd_doc else None,
                artifact_type=doc_type,
                title=doc_name,
                provenance={
                    **metadata,
                    "document_id": did,
                    "filename": filename,
                    "ingested_at": stamp,
                },
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        if cd_doc:
            from core.process_storage import claim_provider_artifact_identity
            claim_provider_artifact_identity(
                "pastadigital_esaj", cd_doc, cnj, root=store.root
            )

        record_incremental_bridge_document(store, cnj, metadata, did)

        # Atualiza canonical store e autos
        try:
            from core.documentos.canonical_store_v1 import migrate as migrate_canonical
            migrate_canonical(store.db_path)
        except Exception:
            pass

        return {
            "status": "success",
            "ingested": True,
            "cnj": cnj,
            "filename": filename,
            "document_id": did,
            "path": str(target_path),
            "pages": len(pages),
            "metadata": metadata,
        }
    except Exception:
        # Atomicidade: limpa arquivos gerados se a ingestão da peça falhar
        for f in created_files:
            try:
                if f.exists():
                    f.unlink()
            except Exception:
                pass
        raise


def consolidate_process_docket(store: Store, cnj: str) -> None:
    store = store.for_process(cnj)
    """Consolida documentos, ordem canônica e snapshot global dos Autos do processo."""
    db = store.connect()
    try:
        db.execute("BEGIN")
        docs = db.execute("SELECT * FROM documents WHERE process_id=?", (cnj,)).fetchall()
        arts = db.execute("SELECT * FROM provider_artifacts WHERE process_id=?", (cnj,)).fetchall()

        art_by_doc = {}
        for a in arts:
            try:
                prov = json.loads(a["provenance_json"] or "{}")
            except Exception:
                prov = {}
            did = prov.get("document_id")
            if did:
                cd_val = prov.get("cdDocumento")
                art_by_doc[did] = {
                    "cdDocumento": int(cd_val) if str(cd_val or "").strip().isdigit() else 0,
                    "dtInclusao": prov.get("dtInclusao") or "",
                }

        doc_list = []
        for d in docs:
            did = d["document_id"]
            meta = art_by_doc.get(did, {"cdDocumento": 0, "dtInclusao": d["created_at"]})
            doc_list.append({
                "document_id": did,
                "cdDocumento": meta["cdDocumento"],
                "dtInclusao": meta["dtInclusao"],
                "created_at": d["created_at"],
            })

        doc_list.sort(key=lambda x: (x["cdDocumento"], x["dtInclusao"], x["created_at"], x["document_id"]))

        page_counter = 0
        for doc_ord, d in enumerate(doc_list, 1):
            pages = db.execute(
                """SELECT cp.canonical_page_id, o.pdf_page 
                   FROM canonical_pages cp 
                   JOIN canonical_page_observations o USING(canonical_page_id) 
                   WHERE o.document_id=? 
                   ORDER BY o.pdf_page""",
                (d["document_id"],),
            ).fetchall()
            for p in pages:
                page_counter += 1
                db.execute(
                    "UPDATE canonical_pages SET canonical_order=? WHERE canonical_page_id=?",
                    (page_counter, p["canonical_page_id"]),
                )

        if doc_list:
            snap_id = f"snapshot_consolidated_{hashlib.sha256(cnj.encode()).hexdigest()[:16]}"
            stamp = now()
            db.execute(
                "INSERT OR REPLACE INTO docket_snapshots VALUES(?,?,?,?)",
                (snap_id, cnj, stamp, "CURRENT"),
            )
            db.execute("DELETE FROM docket_documents WHERE snapshot_id=?", (snap_id,))
            for doc_ord, d in enumerate(doc_list, 1):
                dd_id = f"docket_{snap_id}_{doc_ord}"
                db.execute(
                    "INSERT INTO docket_documents VALUES(?,?,?,?)",
                    (dd_id, snap_id, d["document_id"], doc_ord),
                )

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def finish_process_sync(
    store: Store,
    cnj: str,
    metadata: dict[str, Any] | None = None,
    page_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    store = store.for_process(cnj)
    """Finaliza a sincronização disparando a consolidação e a reconciliação canônica dos Autos."""
    from core.api import core_api
    from core.documentos.canonical_store_v1 import migrate as migrate_canonical
    from core.documentos.autos_reconciler_v1 import migrate as migrate_autos

    cnj = validate_esaj_invariants(
        cnj=cnj,
        metadata=metadata,
        page_context=page_context,
        store=store,
    )

    migrate_canonical(store.db_path)
    migrate_autos(store.db_path)

    consolidate_process_docket(store, cnj)
    composition = reconcile_process_autos(cnj, db_path=store.db_path)
    overview_data = core_api.overview(cnj, path=store.db_path)

    # Gera artefato derivado autos-integrado.pdf e page-map.json lossless
    integrated_info = {}
    try:
        integrated_info = generate_integrated_autos(store, cnj)
    except Exception as auto_err:
        print(f"[Themis Bridge] Aviso ao gerar autos-integrado: {auto_err}")

    return {
        "status": "ok",
        "cnj": cnj,
        "autos_reconciled": True,
        "composition_status": composition.get("composition", {}).get("status") if composition else "ready",
        "integrated_autos": integrated_info,
        "overview": overview_data or {},
    }


def generate_integrated_autos(store: Store, cnj: str) -> dict[str, Any]:
    store = store.for_process(cnj)
    """Gera autos-integrado.pdf lossless e page-map.json estruturado sob derivados/autos/."""
    import pypdfium2 as pdfium

    autos_dir = store.process_derivados_path(cnj) / "autos"
    autos_dir.mkdir(parents=True, exist_ok=True)
    integrated_pdf_path = autos_dir / "autos-integrado.pdf"
    page_map_path = autos_dir / "page-map.json"

    snap_file = store.process_snapshot_path(cnj)
    if not snap_file.is_file():
        raise FileNotFoundError(f"Snapshot fiel do processo não encontrado em {snap_file}")

    snap_data = json.loads(snap_file.read_text(encoding="utf-8"))
    documents = snap_data.get("documents", [])

    # Ordena documentos na ordem canônica da árvore e-SAJ
    def get_sort_key(d: dict[str, Any]) -> tuple:
        ord_val = d.get("order") or d.get("nuSequencia") or 0
        f_ini = d.get("folhaInicial") or 0
        return (int(ord_val), int(f_ini))

    sorted_docs = sorted(documents, key=get_sort_key)
    process_docs_dir = store.process_documents_path(cnj)

    out_pdf = pdfium.PdfDocument.new()
    page_map_entries = []
    integrated_page_counter = 0

    for doc in sorted_docs:
        cd_doc = str(doc.get("cdDocumento") or "").strip()
        doc_title = doc.get("title") or "Peça Processual"
        doc_type = doc.get("deTipoDocDigital") or doc_title
        f_ini = doc.get("folhaInicial")
        parts = doc.get("parts") or []

        # Localiza arquivo PDF canônico da peça
        pdf_candidate = process_docs_dir / f"{cd_doc}.pdf"
        if not pdf_candidate.is_file():
            matches = list(process_docs_dir.glob(f"*{cd_doc}*.pdf"))
            if matches:
                pdf_candidate = matches[0]

        if not pdf_candidate.is_file():
            # Tenta localizar por provider_artifacts no SQLite (via source_artifact_id)
            try:
                with store.connect() as db:
                    row = db.execute(
                        """
                        SELECT provenance_json FROM provider_artifacts
                        WHERE process_id = ? AND (source_artifact_id = ? OR source_artifact_id LIKE ?)
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        (cnj, cd_doc, f"%{cd_doc}%")
                    ).fetchone()
                    if row and row[0]:
                        p_meta = json.loads(row[0])
                        fn = p_meta.get("filename")
                        if fn and (process_docs_dir / fn).is_file():
                            pdf_candidate = process_docs_dir / fn
                        elif p_meta.get("document_id"):
                            doc_id = p_meta.get("document_id")
                            f_row = db.execute(
                                """
                                SELECT f.path FROM documents d
                                JOIN files f ON d.file_id = f.file_id
                                WHERE d.document_id = ?
                                """,
                                (doc_id,)
                            ).fetchone()
                            if f_row and f_row[0] and Path(f_row[0]).is_file():
                                pdf_candidate = Path(f_row[0])
            except Exception:
                pass

        if not pdf_candidate.is_file():
            continue

        src_pdf = pdfium.PdfDocument(pdf_candidate)
        num_pages_in_doc = len(src_pdf)
        out_pdf.import_pages(src_pdf)
        src_pdf.close()

        # Mapeia cada página do documento para o fólio oficial
        for p_idx in range(1, num_pages_in_doc + 1):
            integrated_page_counter += 1
            calculated_folio = (int(f_ini) + p_idx - 1) if f_ini is not None else None

            # Identifica a qual part pertence (se multipartes)
            part_num = 1
            if len(parts) > 1:
                cur_accum = 0
                for pt_idx, pt in enumerate(parts, 1):
                    p_len = pt.get("nuPaginas") or 1
                    if cur_accum < p_idx <= (cur_accum + p_len):
                        part_num = pt_idx
                        break
                    cur_accum += p_len

            page_map_entries.append({
                "integrated_page": integrated_page_counter,
                "source_folio": calculated_folio,
                "cdDocumento": cd_doc,
                "part": part_num,
                "source_page": p_idx,
                "doc_title": doc_title,
                "deTipoDocDigital": doc_type
            })

    # Grava o PDF integrado de forma lossless
    with open(integrated_pdf_path, "wb") as f:
        out_pdf.save(f)
    out_pdf.close()

    map_payload = {
        "cnj": cnj,
        "total_integrated_pages": integrated_page_counter,
        "generated_at": now(),
        "pdf_sha256": hashlib.sha256(integrated_pdf_path.read_bytes()).hexdigest(),
        "entries": page_map_entries
    }
    page_map_path.write_text(
        json.dumps(map_payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return {
        "status": "success",
        "integrated_pdf": str(integrated_pdf_path),
        "page_map": str(page_map_path),
        "total_pages": integrated_page_counter
    }


def reconstruct_process_from_package(store: Store, cnj: str) -> dict[str, Any]:
    store = store.for_process(cnj)
    """Reconstrói todo o processo no SQLite, Autos, Timeline e FTS5 a partir de processos/<CNJ>/."""
    from core.api import core_api
    from core.documentos.canonical_store_v1 import migrate as migrate_canonical
    from core.documentos.autos_reconciler_v1 import migrate as migrate_autos
    from core.documentos.knowledge_objects_v1 import (
        ID_NAMESPACE,
        _fingerprint,
        _json,
        migrate as migrate_knowledge,
    )
    from core.themis_fontes import normalize_name

    snap_file = store.process_snapshot_path(cnj)
    if not snap_file.is_file():
        raise FileNotFoundError(f"Snapshot fiel do processo não encontrado em {snap_file}")

    snap_data = json.loads(snap_file.read_text(encoding="utf-8"))
    metadata = snap_data.get("metadata", {})
    page_context = snap_data.get("page_context", {})
    participants = snap_data.get("participants", [])
    movements = snap_data.get("movements", [])
    documents = snap_data.get("documents", [])

    # 1. Executa migrações
    migrate_knowledge(store.db_path)
    migrate_canonical(store.db_path)
    migrate_autos(store.db_path)

    # 2. Registra processo, participantes e movimentações
    db = store.connect()
    try:
        db.execute("BEGIN")
        _ensure_process(db, cnj)

        cd_processo = metadata.get("cdProcesso") or metadata.get("nuProcesso") or cnj
        db.execute(
            """INSERT INTO process_sources(process_id, source_type, source_id, created_at)
            VALUES(?, ?, ?, ?) ON CONFLICT DO NOTHING""",
            (cnj, "ESAJ_PASTADIGITAL", str(cd_processo), now()),
        )

        for part in participants:
            d_name = " ".join(str(part.get("display_name", "")).split())
            if not d_name:
                continue
            e_type = str(part.get("entity_type", "UNKNOWN")).upper()
            if e_type not in {"PERSON", "ORGANIZATION", "UNKNOWN"}:
                e_type = "UNKNOWN"
            norm = normalize_name(d_name)
            identifiers = part.get("identifiers") or {}
            identity_fp = _fingerprint(e_type, _json(identifiers) if identifiers else norm)

            row = db.execute(
                "SELECT entity_id FROM legal_entities WHERE identity_fingerprint=?",
                (identity_fp,),
            ).fetchone()
            if row:
                e_id = row[0]
            else:
                e_id = "entity_" + uuid.uuid5(ID_NAMESPACE, identity_fp).hex
                db.execute(
                    """INSERT INTO legal_entities(entity_id, entity_type, display_name, normalized_name, identifiers_json, identity_fingerprint, created_at, updated_at)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                    (e_id, e_type, d_name, norm, _json(identifiers), identity_fp, now(), now()),
                )

            role_raw = part.get("role") or "PARTE"
            role = str(role_raw).strip() or "PARTE"
            rel_fp = _fingerprint("process", cnj, e_id, role, role_raw)
            rel_id = "party_" + uuid.uuid5(ID_NAMESPACE, rel_fp).hex
            db.execute(
                """INSERT INTO party_relations(party_relation_id, entity_id, owner_type, owner_id, role, role_raw, status, confidence, relation_fingerprint, extraction_run_id, created_at, updated_at)
                VALUES(?, ?, 'PROCESS', ?, ?, ?, 'CONFIRMED', 'HIGH', ?, NULL, ?, ?)
                ON CONFLICT(relation_fingerprint) DO UPDATE SET status=excluded.status, confidence=excluded.confidence, updated_at=excluded.updated_at""",
                (rel_id, e_id, cnj, role, role_raw, rel_fp, now(), now()),
            )

        for mov in movements:
            m_date = mov.get("date") or mov.get("occurred_at")
            m_name = mov.get("name") or mov.get("movement_type") or "Movimentação registrada"
            m_text = mov.get("content") or m_name
            m_code = mov.get("code") or mov.get("movement_code")
            src_m_id = mov.get("source_movement_id") or mov.get("cdMovimento")

            fp = hashlib.sha256(f"{cnj}_{m_date}_{m_name}_{m_text[:80]}".encode("utf-8")).hexdigest()[:16]
            register_movement(
                db,
                process_id=cnj,
                movement_type=m_name,
                occurred_at=m_date,
                content=m_text,
                source_movement_id=str(src_m_id) if src_m_id else None,
                movement_code=str(m_code) if m_code else None,
                movement_fingerprint=fp,
                provenance={"source": "esaj_bridge", "metadata": metadata},
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    # 3. Ingestão de todos os documentos físicos do pacote
    proc_docs_dir = store.process_documents_path(cnj)
    doc_meta_by_name = {f"{d.get('title', '').replace('/', '_')}.pdf": d for d in documents}
    doc_meta_by_cd = {str(d.get("cdDocumento") or ""): d for d in documents if d.get("cdDocumento")}

    if proc_docs_dir.is_dir():
        for pdf_file in sorted(proc_docs_dir.glob("*.pdf")):
            ingest_res = themis_pdf.command_ingest(pdf_file, confirmed_case_id=cnj)
            did = ingest_res.get("document_id")

            matched_doc = doc_meta_by_name.get(pdf_file.name)
            if not matched_doc:
                for cd, md in doc_meta_by_cd.items():
                    if cd in pdf_file.name:
                        matched_doc = md
                        break
            if not matched_doc:
                matched_doc = {"title": pdf_file.stem, "deTipoDocDigital": pdf_file.stem}

            cd_doc = str(matched_doc.get("cdDocumento") or "").strip()
            doc_name = matched_doc.get("docName") or matched_doc.get("title") or pdf_file.name
            doc_type = matched_doc.get("deTipoDocDigital") or matched_doc.get("docType") or doc_name

            db = store.connect()
            try:
                db.execute("BEGIN")
                _ensure_process(db, cnj)
                register_provider_artifact(
                    db,
                    process_id=cnj,
                    source_origin="pastadigital_esaj",
                    source_artifact_id=cd_doc if cd_doc else None,
                    artifact_type=doc_type,
                    title=doc_name,
                    provenance={
                        **matched_doc,
                        "document_id": did,
                        "filename": pdf_file.name,
                        "ingested_at": now(),
                    },
                )
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

    # 4. Consolidação e reconciliação dos Autos
    consolidate_process_docket(store, cnj)
    composition = reconcile_process_autos(cnj, db_path=store.db_path)
    overview_data = core_api.overview(cnj, path=store.db_path)

    return {
        "status": "ok",
        "cnj": cnj,
        "reconstructed": True,
        "composition_status": composition.get("composition", {}).get("status") if composition else "ready",
        "overview": overview_data or {},
    }


def sanitize_pdf_filename(orig_name: str, index: int) -> str:
    """Gera um nome de arquivo seguro para o filesystem preservando legibilidade e extensão .pdf."""
    name = Path(orig_name).name
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    safe = re.sub(r"\s+", " ", safe).strip()
    if not safe.lower().endswith(".pdf"):
        safe = f"{safe}.pdf"
    if not safe or safe == ".pdf":
        safe = f"peca_{index:04d}.pdf"
    return safe


def ingest_bulk_zip(
    store: Store,
    cnj: str,
    zip_bytes: bytes,
    metadata: dict[str, Any] | None = None,
    page_context: dict[str, Any] | None = None,
    run_pipeline: bool = True,
) -> dict[str, Any]:
    store = store.for_process(cnj)
    """Ingere e valida o pacote ZIP oficial do e-SAJ de bulk download sob fontes/.
    
    Invariantes:
    1. Preserva ZIP original e calcula SHA-256 sob processos/<CNJ>/fontes/bulk_download.zip.
    2. Extrai PDFs sob processos/<CNJ>/fontes/pecas/ (NUNCA sob derivados/ e NUNCA em themis/documentos).
    3. Preserva nomes originais como metadata e materializa paths filesystem-safe.
    4. Valida ZIP e todos os PDFs com PDFium (verifica contagem de páginas e integridade).
    5. NÃO gera Markdown, embeddings ou autos-integrado.
    """
    import io
    import zipfile
    import pypdfium2 as pdfium

    cnj = validate_esaj_invariants(
        cnj=cnj,
        metadata=metadata,
        page_context=page_context,
        store=store,
    )

    if not zip_bytes or len(zip_bytes) < 4 or not (zip_bytes.startswith(b"PK\x03\x04") or zip_bytes.startswith(b"PK")):
        raise ValueError("Assinatura de arquivo ZIP (PK) inválida ou ausente.")

    # 1. Diretórios estritamente sob processos/<CNJ>/fontes/
    process_dir = store.process_path(cnj)
    process_dir.mkdir(parents=True, exist_ok=True)
    process_fontes_dir = store.process_fontes_path(cnj)
    process_fontes_dir.mkdir(parents=True, exist_ok=True)
    objetos_dir = process_fontes_dir / "objetos"
    objetos_dir.mkdir(parents=True, exist_ok=True)
    inventory_by_order = _snapshot_documents_by_order(store, cnj)
    persisted_document_ids = _persisted_provider_document_ids(store, cnj)

    # 2. Salva ZIP original em artefato imutável versionado sob fontes/bulk/<stamp-ou-hash>/pacote.zip
    zip_sha256 = hashlib.sha256(zip_bytes).hexdigest()
    capture_time = now()
    stamp_safe = capture_time.replace(":", "-").replace(".", "-")
    bulk_version_dir = process_fontes_dir / "bulk" / f"{stamp_safe}_{zip_sha256[:12]}"
    bulk_version_dir.mkdir(parents=True, exist_ok=True)
    raw_zip_path = bulk_version_dir / "pacote.zip"
    raw_zip_path.write_bytes(zip_bytes)

    # 3. Validação de integridade do arquivo ZIP antes de promover / extrair
    if not zipfile.is_zipfile(io.BytesIO(zip_bytes)):
        raise ValueError("O arquivo recebido não é uma estrutura ZIP válida.")

    # 4. Descompacta entradas do ZIP sob storage canônico content-addressed (fontes/objetos/<sha256>.pdf)
    pdf_entries = []
    unique_objects = set()
    folha_regex = re.compile(r"\(pag\s+(\d+)(?:\s*-\s*(\d+))?\)", re.IGNORECASE)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        # Testa integridade interna do arquivo ZIP
        corrupt_file = zf.testzip()
        if corrupt_file is not None:
            raise ValueError(f"Arquivo corrompido detectado dentro do ZIP: {corrupt_file}")

        infolist = zf.infolist()
        # Filtra apenas arquivos PDF (exclui diretórios)
        pdf_infos = [
            info for info in infolist
            if not info.is_dir() and (info.filename.lower().endswith(".pdf") or not Path(info.filename).suffix)
        ]
        
        for idx, info in enumerate(pdf_infos, 1):
            raw_pdf = zf.read(info)
            if not raw_pdf.startswith(b"%PDF"):
                continue
            
            orig_filename = info.filename
            inventory_piece = inventory_by_order.get(idx)
            # A delta ZIP is not ordinally aligned with the complete provider
            # snapshot.  Prefer its provider-attested page range when the
            # filename exposes one; otherwise the legacy ordinal path remains
            # valid for complete ZIPs.
            range_match = folha_regex.search(orig_filename)
            if range_match:
                wanted_range = (int(range_match.group(1)), int(range_match.group(2) or range_match.group(1)))
                for candidate in inventory_by_order.values():
                    try:
                        if _provider_part_page_range(candidate["document"], candidate["part"]) == wanted_range:
                            inventory_piece = candidate
                            break
                    except ValueError:
                        continue
            if inventory_piece is None:
                raise ValueError(
                    f"INVARIANT_VIOLATION: PDF de ordem {idx} sem item correspondente no inventário e-SAJ."
                )
            inventory_item = inventory_piece["document"]
            provider_item_identity = esaj_provider_item_identity(
                inventory_item, inventory_piece["part_index"], inventory_piece["part"]
            )
            pdf_sha256 = hashlib.sha256(raw_pdf).hexdigest()
            unique_objects.add(pdf_sha256)

            # Valida o conteúdo recebido antes da persistência. Abrir primeiro o
            # caminho recém-escrito pode observar um objeto ainda indisponível
            # para PDFium em alguns hosts Windows, embora os bytes do ZIP sejam válidos.
            obj_filename = f"{pdf_sha256}.pdf"
            obj_path = objetos_dir / obj_filename

            # Extração de foliação
            folha_ini = None
            folha_fim = None
            match = folha_regex.search(orig_filename)
            if match:
                folha_ini = int(match.group(1))
                folha_fim = int(match.group(2)) if match.group(2) else folha_ini

            # Validação estrita com PDFium no objeto canônico
            try:
                pdf_doc = pdfium.PdfDocument(raw_pdf)
                doc_page_count = len(pdf_doc)
                for p_i in range(doc_page_count):
                    page = pdf_doc.get_page(p_i)
                    width, height = page.get_size()
                    if width <= 0 or height <= 0:
                        raise ValueError(f"Página sem dimensões físicas no PDF '{obj_filename}'")
                    page.close()
                pdf_doc.close()
            except Exception as pdf_err:
                raise ValueError(f"Falha na validação PDFium do objeto '{obj_filename}': {pdf_err}")

            # O original só entra no storage após validar o mesmo payload que
            # veio no ZIP. Objetos existentes são imutáveis e precisam conferir
            # com o endereço content-addressed antes de serem reutilizados.
            if obj_path.exists():
                existing_sha256 = hashlib.sha256(obj_path.read_bytes()).hexdigest()
                if existing_sha256 != pdf_sha256:
                    raise ValueError(
                        f"Objeto existente diverge do SHA-256 content-addressed '{obj_filename}'."
                    )
            else:
                obj_path.write_bytes(raw_pdf)

            existing_document_id = persisted_document_ids.get(provider_item_identity)
            pdf_entries.append({
                "order": idx,
                "source_identity": provider_item_identity,
                "provider_item_identity": provider_item_identity,
                "provider_document_id": str(inventory_item["cdDocumento"]),
                "source_filename_literal": orig_filename,
                "folha_inicial": folha_ini,
                "folha_final": folha_fim,
                "page_count": doc_page_count,
                "size_bytes": len(raw_pdf),
                "sha256": pdf_sha256,
                "object_path": f"fontes/objetos/{obj_filename}",
                "relative_object_path": f"fontes/objetos/{obj_filename}",
                # document_id is stable for an already known provider item;
                # sha256 remains provenance of this particular ZIP export.
                "document_id": existing_document_id or pdf_sha256,
                "reused_existing": bool(existing_document_id),
            })

    # Um ZIP incremental contém somente o delta recebido. O manifesto
    # persistido continua sendo o inventário completo do processo.
    fontes_manifest_path = process_fontes_dir / "pecas_manifest.json"
    previous_manifest: list[dict[str, Any]] = []
    if fontes_manifest_path.is_file():
        try:
            previous_manifest = json.loads(fontes_manifest_path.read_text(encoding="utf-8")).get("pecas", [])
        except Exception:
            previous_manifest = []
    pdf_entries = merge_incremental_manifest_entries(previous_manifest, pdf_entries)
    complete_physical_pages = sum(int(entry.get("page_count") or 0) for entry in pdf_entries)
    complete_unique_objects = {str(entry.get("sha256") or entry.get("document_id")) for entry in pdf_entries}

    # 5. Calcula source_state_sha256 canônico e reproduzível
    hasher_state = hashlib.sha256()
    for e in sorted(pdf_entries, key=lambda x: x["order"]):
        line = (
            f"{e['order']:04d}|"
            f"{e['provider_item_identity']}|"
            f"{e['source_filename_literal']}|"
            f"{e['folha_inicial']}|"
            f"{e['folha_final']}|"
            f"{e['page_count']}|"
            f"{e['size_bytes']}|"
            f"{e['document_id']}\n"
        )
        hasher_state.update(line.encode("utf-8"))
    source_state_sha256 = hasher_state.hexdigest()

    # 6. Salva manifesto estruturado sob fontes/ e atualiza manifest.json do processo
    manifest_payload = {
        "cnj": cnj,
        "manifest_version": "2.1",
        "storage_architecture": "content_addressed_objects",
        "captured_at": capture_time,
        "source_type": "esaj_pastadigital_bulk_zip",
        "source_state_sha256": source_state_sha256,
        "zip_source": {
            "path": str(raw_zip_path.relative_to(process_dir)),
            "sha256": zip_sha256,
            "size_bytes": len(zip_bytes),
        },
        "total_entries": len(pdf_entries),
        "total_unique_objects": len({str(e.get("sha256") or e.get("document_id")) for e in pdf_entries}),
        "total_physical_pages": complete_physical_pages,
        "incremental_identity": "esaj:cdDocumento:<cdDocumento>",
        "reused_existing_entries": sum(1 for entry in pdf_entries if entry["reused_existing"]),
        "new_entries": sum(1 for entry in pdf_entries if not entry["reused_existing"]),
        "validation": {
            "pdfium_validated": True,
            "all_valid": True,
            "all_objects_exist": True,
            "non_empty_pages": complete_physical_pages,
            "total_pages_verified": complete_physical_pages,
        },
        "pecas": pdf_entries,
    }
    fontes_manifest_path.write_text(
        json.dumps(manifest_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Atualiza manifest.json principal na raiz de processos/<CNJ>/
    proc_manifest_path = store.process_manifest_path(cnj)
    existing_manifest = {}
    if proc_manifest_path.is_file():
        try:
            existing_manifest = json.loads(proc_manifest_path.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    existing_manifest.update({
        "cnj": cnj,
        "updated_at": capture_time,
        "source": "pastadigital_esaj_bulk",
        "source_state_sha256": source_state_sha256,
        "storage_architecture": "content_addressed_objects",
        "total_source_pdfs": len(pdf_entries),
        "total_unique_objects": len(complete_unique_objects),
        "total_physical_pages": complete_physical_pages,
        "zip_sha256": zip_sha256,
        "fontes_manifest": "fontes/pecas_manifest.json",
    })
    proc_manifest_path.write_text(
        json.dumps(existing_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # API callers can return the durable capture immediately and run the costly
    # extraction/indexing phase as a tracked background task.
    pipeline_result = None
    if run_pipeline:
        pipeline_result = process_captured_sync(store=store, cnj=cnj)
    else:
        _update_pipeline_progress(store, cnj, "QUEUED", 0, complete_physical_pages)

    return {
        "status": "success",
        "cnj": cnj,
        "zip_sha256": zip_sha256,
        "zip_size_bytes": len(zip_bytes),
        "source_state_sha256": source_state_sha256,
        "total_entries": len(pdf_entries),
        "total_unique_objects": len(unique_objects),
        "total_physical_pages": complete_physical_pages,
        "fontes_dir": str(process_fontes_dir),
        "objetos_dir": str(objetos_dir),
        "validation": manifest_payload["validation"],
        "pipeline": pipeline_result or {"status": "QUEUED"},
    }


def _update_pipeline_progress(
    store: Store,
    cnj: str,
    phase: str,
    completed_pages: int,
    total_pages: int,
    status_label: str = "PROCESSING",
    error_message: str | None = None,
) -> None:
    pct = round((completed_pages / max(1, total_pages)) * 100.0, 1)
    progress_info = {
        "phase": phase,
        "pipeline_status": phase if phase in {"READY", "ERROR", "QUEUED"} else status_label,
        "status": "ACTIVE" if phase == "READY" else ("ERROR" if phase == "ERROR" else ("QUEUED" if phase == "QUEUED" else "PROCESSING")),
        "completed_pages": completed_pages,
        "total_pages": total_pages,
        "percentage": pct,
        "message": f"Processando documentos: {phase} páginas {completed_pages} / {total_pages} ({pct}%)",
        "updated_at": now(),
        "error": error_message,
    }

    # The package manifest is also the durable progress record polled by the
    # browser extension. Write atomically so readers never observe partial JSON.
    proc_manifest = store.process_manifest_path(cnj)
    if proc_manifest.is_file():
        try:
            mdata = json.loads(proc_manifest.read_text(encoding="utf-8"))
            mdata["pipeline_progress"] = progress_info
            mdata["pipeline_status"] = progress_info["pipeline_status"]
            if phase == "READY":
                mdata["status"] = "READY"
            temporary = proc_manifest.with_name(f".{proc_manifest.name}.{uuid.uuid4().hex}.tmp")
            try:
                temporary.write_text(json.dumps(mdata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                os.replace(temporary, proc_manifest)
            finally:
                if temporary.exists():
                    temporary.unlink()
        except Exception:
            _LOGGER.exception("Não foi possível persistir progresso do sync no manifest do pacote %s", cnj)

    # Pipeline progress is operational state, not process_metadata domain data.
    try:
        db = sqlite3.connect(store.db_path, timeout=15)
        try:
            db_status = "ACTIVE" if phase == "READY" else ("ERROR" if phase == "ERROR" else phase)
            db.execute("UPDATE processes SET status=? WHERE process_id=?", (db_status, cnj))
            db.commit()
        finally:
            db.close()
    except Exception:
        _LOGGER.exception("Não foi possível atualizar status do processo %s durante o sync", cnj)


def _finalize_process_package(store: Store, cnj: str) -> dict[str, Any]:
    """Rebuild the portable projection and seal a current package inventory."""
    from core.process_markdown import generate_process_markdown

    db = store.connect()
    try:
        markdown_files = generate_process_markdown(db, store.process_path(cnj), cnj)
        db.execute("UPDATE processes SET status='ACTIVE' WHERE process_id=?", (cnj,))
        db.commit()
        existing_tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        counts = {
            "documents": db.execute("SELECT count(*) FROM documents WHERE process_id=?", (cnj,)).fetchone()[0],
            "pages": db.execute("SELECT count(*) FROM pages p JOIN documents d USING(document_id) WHERE d.process_id=?", (cnj,)).fetchone()[0],
            "movements": db.execute("SELECT count(*) FROM movements WHERE process_id=?", (cnj,)).fetchone()[0],
            "summaries": db.execute("SELECT count(*) FROM movement_summaries ms JOIN movements m USING(movement_id) WHERE m.process_id=?", (cnj,)).fetchone()[0],
            "syntheses": db.execute("SELECT count(*) FROM case_syntheses WHERE process_id=?", (cnj,)).fetchone()[0],
            "participants": db.execute("SELECT count(*) FROM process_participants WHERE process_id=?", (cnj,)).fetchone()[0],
            "embeddings": db.execute("SELECT count(*) FROM page_embeddings WHERE process_id=?", (cnj,)).fetchone()[0] if "page_embeddings" in existing_tables else 0,
            "fts": db.execute("SELECT count(*) FROM pages_fts").fetchone()[0] if "pages_fts" in existing_tables else 0,
        }
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        fk_errors = db.execute("PRAGMA foreign_key_check").fetchall()
        if integrity != "ok" or fk_errors:
            raise RuntimeError(f"Process Package inválido ao finalizar {cnj}: integrity={integrity}; foreign_keys={len(fk_errors)}")
    finally:
        db.close()

    package = store.process_path(cnj)
    process_db = store.db_path
    artifacts: list[dict[str, Any]] = []
    for path in sorted(package.rglob("*")):
        if not path.is_file() or path.name == "manifest.json" or path.name.endswith(("-wal", "-shm", ".tmp")):
            continue
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        artifacts.append({
            "path": path.relative_to(package).as_posix(),
            "sha256": digest.hexdigest(),
            "size_bytes": path.stat().st_size,
        })

    manifest_path = store.process_manifest_path(cnj)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    manifest.update({
        "schema": "themis.process-package/v1",
        "process_id": cnj,
        "authority": "process.db",
        "updated_at": now(),
        "total_documents": counts["documents"],
        "total_movements": counts["movements"],
        "total_participants": counts["participants"],
        "total_pages": counts["pages"],
        "total_summaries": counts["summaries"],
        "total_syntheses": counts["syntheses"],
        "counts": counts,
        "process_db_sha256": next((item["sha256"] for item in artifacts if item["path"] == "process.db"), None),
        "markdown": {"schema": "themis.process-markdown/v1", "files": markdown_files},
        "artifacts": artifacts,
        "integrity_check": integrity,
        "foreign_key_errors": 0,
        "pipeline_status": "READY",
        "status": "READY",
        "pipeline_progress": {
            "phase": "READY",
            "pipeline_status": "READY",
            "status": "ACTIVE",
            "completed_pages": counts["pages"],
            "total_pages": counts["pages"],
            "percentage": 100.0,
            "message": f"Processamento concluído: {counts['pages']} páginas",
            "updated_at": now(),
            "error": None,
        },
    })
    temporary = manifest_path.with_name(f".{manifest_path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, manifest_path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {"counts": counts, "markdown_files": len(markdown_files), "artifacts": len(artifacts)}


def process_captured_sync(
    store: Store,
    cnj: str,
) -> dict[str, Any]:
    store = store.for_process(cnj)
    """Executa o pipeline nativo pós-captura do Themis para gerar Markdown, Autos, Cronologia, FTS e Embeddings.
    
    Estágios do Pipeline:
    1. VALIDATED: Confirma integridade dos PDFs e manifesto.
    2. EXTRACTING: Extração estrutural Heron + PDFium Spans (idempotente/retomável).
    3. STRUCTURING: Materialização no Themis, Canonical Store, Autos Reconciler e Cronologia Documental.
    4. INDEXING: Geração de embeddings ONNX (embeddinggemma:300m) e indexação FTS.
    5. READY: Atualização de estado final do processo.
    """
    import time
    from core.documentos.themis_documentos import write_json, write_pages
    from core.pdf.themis_pdf import hybrid_pages
    from core.documentos import canonical_store_v1, autos_reconciler_v1
    from core.retrieval.vector_store import VectorStore, pack_vector, _now as vector_now
    from core.retrieval.onnx_embed import generate_embeddings_batch_onnx

    t_total_start = time.perf_counter()
    proc_dir = store.process_path(cnj)
    fontes_dir = store.process_fontes_path(cnj)
    pecas_manifest_path = fontes_dir / "pecas_manifest.json"

    if not pecas_manifest_path.is_file():
        raise FileNotFoundError(f"pecas_manifest.json não encontrado em {pecas_manifest_path}")

    pecas_data = json.loads(pecas_manifest_path.read_text(encoding="utf-8"))
    pecas = pecas_data.get("pecas", [])
    if not pecas:
        raise ValueError("Nenhuma peça encontrada no manifesto de peças do processo.")

    reused_pecas, new_pecas = partition_incremental_pieces(pecas)
    total_expected_pages = sum(p.get("page_count", 0) for p in new_pecas) or len(new_pecas)
    cached_extraction_pages = _cached_extraction_page_count(store, new_pecas)

    # Início do processamento: registrar VALIDATED
    _update_pipeline_progress(store, cnj, "VALIDATED", 0, total_expected_pages)

    # --- ESTÁGIO 1 & 2: EXTRACTING (Heron + PDFium Spans Fusion) ---
    t_extract_start = time.perf_counter()
    extracted_count = 0
    newly_extracted_pages = 0
    total_physical_pages = 0
    doc_pages_map = {}
    _update_pipeline_progress(store, cnj, "EXTRACTING", cached_extraction_pages, total_expected_pages)

    for idx, p in enumerate(new_pecas, 1):
        doc_id = p.get("document_id") or p["sha256"]
        obj_path = proc_dir / p["object_path"]
        if not obj_path.is_file():
            raise FileNotFoundError(f"Objeto PDF não encontrado: {obj_path}")

        pages_ndjson = store.pages_path(doc_id)
        manifest_doc = store.manifest_path(doc_id)

        is_cache_valid = False
        if pages_ndjson.is_file() and manifest_doc.is_file():
            try:
                m_data = json.loads(manifest_doc.read_text(encoding="utf-8"))
                if is_current_extraction_cache(m_data, doc_id):
                    is_cache_valid = True
            except Exception:
                is_cache_valid = False

        if is_cache_valid:
            pages = [json.loads(line) for line in pages_ndjson.read_text(encoding="utf-8").splitlines() if line]
        else:
            pages = hybrid_pages(obj_path)
            extracted_count += 1
            newly_extracted_pages += len(pages)

        doc_pages_map[doc_id] = pages
        total_physical_pages += len(pages)

        # Atualiza progresso da extração periodicamente
        if idx % 10 == 0 or idx == len(new_pecas):
            _update_pipeline_progress(store, cnj, "EXTRACTING", cached_extraction_pages + newly_extracted_pages, total_expected_pages)

    t_extract_dur = time.perf_counter() - t_extract_start

    # --- ESTÁGIO 3: STRUCTURING (Documentos, Páginas, FTS, Canonical Store, Autos e Cronologia) ---
    t_struct_start = time.perf_counter()
    _update_pipeline_progress(store, cnj, "STRUCTURING", 0, total_physical_pages)

    db = store.connect()
    try:
        db.execute("BEGIN")
        _ensure_process(db, cnj)

        snapshot_id = f"snapshot_{cnj}"
        stamp = pecas_data.get("captured_at") or now()
        db.execute("INSERT OR IGNORE INTO docket_snapshots VALUES(?,?,?,?)", (snapshot_id, cnj, stamp, "CURRENT"))
        structured_pages_count = 0
        for idx, p in enumerate(new_pecas, 1):
            doc_id = p.get("document_id") or p["sha256"]
            pages = doc_pages_map[doc_id]
            obj_path = str(proc_dir / p["object_path"])
            file_id = f"file_{doc_id}"

            db.execute("INSERT OR REPLACE INTO files VALUES(?,?,?,?,?)", (file_id, obj_path, doc_id, p["size_bytes"], stamp))
            db.execute("INSERT OR REPLACE INTO documents VALUES(?,?,?,?,?,?,?)", (doc_id, cnj, file_id, "PDF", "complete", len(pages), stamp))
            document_ordinal = int(p.get("order") or idx)
            db.execute("INSERT OR IGNORE INTO docket_documents VALUES(?,?,?,?)", (f"docket_{cnj}_{doc_id[:12]}_{document_ordinal}", snapshot_id, doc_id, document_ordinal))

            db.execute("DELETE FROM pages_fts WHERE document_id=?", (doc_id,))

            f_ini = p.get("folha_inicial")
            page_folios = _page_folios(pages, cnj)
            for item in pages:
                num = item["page"]
                content = item.get("content_markdown", item.get("text", ""))
                pid = f"{doc_id}:{num}"
                cid = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()
                quality = item.get("quality", "OK")
                page_class = _page_class(item)
                process_folio = page_folios.get(num)
                if process_folio is None and f_ini is not None:
                    process_folio = f_ini + (num - 1)
                db.execute("INSERT OR REPLACE INTO pages(page_id,document_id,page_number,content,quality,engine,fallback_used,content_id,process_folio,page_class) VALUES(?,?,?,?,?,?,?,?,?,?)", (pid, doc_id, num, content, quality, "heron_pdfium_fusion", 0, cid, process_folio, page_class))
                db.execute("INSERT INTO pages_fts VALUES(?,?,?)", (pid, doc_id, content))

                if f_ini is not None:
                    calc_folio = f_ini + (num - 1)
                    ev_id = f"ev_{hashlib.sha256(f'{pid}:folha:{calc_folio}'.encode()).hexdigest()[:16]}"
                    db.execute("INSERT OR REPLACE INTO evidence VALUES(?,?,?,?,?,?,?)", (ev_id, pid, "folha", str(calc_folio), f"Foliação da peça {p.get('source_identity')}", str(calc_folio), None))

                structured_pages_count += 1

        db.commit()
    finally:
        db.close()

    # Migrações e Backfill do Canonical Store
    from core.documentos.knowledge_objects_v1 import migrate as migrate_knowledge
    migrate_knowledge(store.db_path)
    canonical_store_v1.migrate(store.db_path)
    from core.documentos.provider_artifacts_v1 import migrate as migrate_provider_artifacts
    migrate_provider_artifacts(store.db_path)
    autos_reconciler_v1.migrate(store.db_path)

    db = store.connect()
    try:
        db.execute("BEGIN")
        canonical_store_v1._backfill(db)
        db.commit()
    finally:
        db.close()

    # Extração e persistência de Provider Artifacts e vínculo a Canonical Pages
    from core.documentos.provider_marker_pipeline_v1 import persist_esaj_provider_artifacts
    db = store.connect()
    try:
        db.execute("BEGIN")
        for p in new_pecas:
            doc_id = p.get("document_id") or p["sha256"]
            persist_esaj_provider_artifacts(
                db,
                document_id=doc_id,
                process_id=cnj,
                page_structures=[{"page": int(item["page"]), **(item.get("structure") or {})} for item in doc_pages_map[doc_id] if isinstance(item.get("structure"), dict)],
            )
        db.commit()
    finally:
        db.close()

    # Persist only compact final extraction caches after page text and provider
    # facts have committed successfully. A crash before this point re-extracts
    # from the immutable PDF rather than reopening serialized geometry.
    for p in new_pecas:
        doc_id = p.get("document_id") or p["sha256"]
        obj_path = proc_dir / p["object_path"]
        pages = doc_pages_map[doc_id]
        folios = _page_folios(pages, cnj)
        write_pages(store.pages_path(doc_id), [
            _compact_page_record(page, process_folio=folios.get(int(page["page"])))
            for page in pages
        ])
        write_json(store.manifest_path(doc_id), {
            "format_version": "2.0.0",
            "document_id": doc_id,
            "sha256": doc_id,
            "extraction_pipeline_version": EXTRACTION_PIPELINE_VERSION,
            "size_bytes": p["size_bytes"],
            "pages": len(pages),
            "format": "PDF",
            "known_paths": [str(obj_path)],
            "canonical_source_path": str(obj_path),
            "status": "complete",
            "ingested_at": pecas_data.get("captured_at") or now(),
            "process_id": cnj,
            "source_identity": p.get("source_identity"),
            "source_filename_literal": p.get("source_filename_literal"),
            "folha_inicial": p.get("folha_inicial"),
            "folha_final": p.get("folha_final"),
        })

    # Reconciliação dos Autos
    autos_result = autos_reconciler_v1.reconcile_process_autos(cnj, db_path=store.db_path)

    # Materializa uma vez o read-model leve consumido pelo GET /autos. A
    # projeção pesada continua disponível para auditoria/reprocessamento, mas
    # não volta a ser executada na abertura normal do processo.
    from core.documentos.autos_context_v1 import materialize_process as materialize_autos_context
    autos_context_result = materialize_autos_context(store.db_path, cnj)

    # Document Chronology (sem alterar process_movements)
    db = store.connect()
    try:
        db.execute("BEGIN")
        snap_docs_by_cd = {}
        snapshot_path = store.process_snapshot_path(cnj)
        if snapshot_path.is_file():
            sdata = json.loads(snapshot_path.read_text(encoding="utf-8"))
            snap_docs_by_cd = {str(sd.get("cdDocumento")): sd for sd in sdata.get("documents", []) if sd.get("cdDocumento")}

        chronology_count = 0
        for idx, p in enumerate(new_pecas, 1):
            doc_id = p.get("document_id") or p["sha256"]
            snap_doc = snap_docs_by_cd.get(str(p.get("provider_document_id") or ""), {})
            title = snap_doc.get("title") or p.get("source_filename_literal") or f"Documento {idx}"
            f_ini = p.get("folha_inicial")
            f_fim = p.get("folha_final")
            folio_str = f"fls. {f_ini}-{f_fim}" if f_ini and f_fim and f_ini != f_fim else (f"fls. {f_ini}" if f_ini else "s/ folha")

            dt_inc = snap_doc.get("dtInclusao")
            occ_at = None
            date_prec = "UNKNOWN"
            if dt_inc:
                m = re.match(r"(\d{2})/(\d{2})/(\d{4})", str(dt_inc))
                if m:
                    d, mo, y = m.groups()
                    occ_at = f"{y}-{mo}-{d}"
                    date_prec = "DAY"

            event_fp = f"{cnj}|{p.get('provider_item_identity')}"
            event_id = f"event_doc_{hashlib.sha256(event_fp.encode('utf-8')).hexdigest()[:16]}"

            db.execute("""
                INSERT OR REPLACE INTO chronology_events(
                    chronology_event_id, owner_type, owner_id, occurred_at, date_precision, event_type,
                    title, description, status, confidence, source_fingerprint, extraction_run_id, created_at, updated_at
                ) VALUES(?, 'PROCESS', ?, ?, ?, 'DOCUMENT_JUNCTION', ?, ?, 'CONFIRMED', 'HIGH', ?, NULL, ?, ?)
            """, (
                event_id, cnj, occ_at, date_prec, f"Juntada: {title} ({folio_str})",
                f"Documento de ordem {p.get('order')} ({p.get('source_filename_literal')}) juntado aos autos sob {folio_str} ({p.get('page_count')} páginas).",
                event_fp, stamp, stamp
            ))

            cp_row = db.execute("SELECT canonical_page_id FROM canonical_page_observations WHERE document_id=? AND pdf_page=1", (doc_id,)).fetchone()
            cp_id = cp_row[0] if cp_row else f"cp_{doc_id[:16]}"
            ev_id = f"ce_{event_id}_{doc_id[:8]}"
            src_ref = {"canonical_page_id": cp_id, "document_id": doc_id, "pdf_page": 1, "process_folio": f_ini}

            db.execute("""
                INSERT OR IGNORE INTO chronology_evidence(
                    chronology_evidence_id, chronology_event_id, document_id, canonical_page_id,
                    pdf_page, process_folio, source_ref_json, excerpt, extraction_method, confidence, evidence_fingerprint, created_at
                ) VALUES(?, ?, ?, ?, 1, ?, ?, ?, 'document_manifest', 'HIGH', ?, ?)
            """, (
                ev_id, event_id, doc_id, cp_id, f_ini, json.dumps(src_ref, ensure_ascii=False),
                f"Juntada de {title} ({folio_str})", hashlib.sha256(f"{doc_id}:1".encode()).hexdigest(), stamp
            ))
            chronology_count += 1

        db.commit()
    finally:
        db.close()

    # Materializa o read model atual de Movements depois que páginas,
    # manifesto e contexto documental já estão disponíveis. Isso mantém a
    # fronteira de atos consistente para summaries e síntese posteriores.
    from core.documentos.participant_context_store_v1 import materialize_all as materialize_participant_context
    db = store.connect()
    try:
        movement_materialization = _materialize_movements_with_projection_policy(
            db,
            cnj,
            manifest_or_root=store.root,
        )

        from core.documentos.process_movement_linker_v1 import materialize_links as materialize_process_movement_links
        try:
            process_movement_links = materialize_process_movement_links(db, cnj)
        except Exception as link_err:
            process_movement_links = {"error": str(link_err)}
            print(f"[Themis Bridge Sync] Aviso ao associar cronologia provider aos documentos: {link_err}")

        # Movements/movement_pieces are the semantic boundary for documentary
        # representation discovery.  Run the existing idempotent projector
        # after that boundary is available, including 0-NEW syncs.
        participant_context_materialization = materialize_participant_context(db)
    finally:
        db.close()

    t_struct_dur = time.perf_counter() - t_struct_start

    # --- ESTÁGIO 4: INDEXING (Embeddings ONNX) ---
    t_embed_start = time.perf_counter()
    _update_pipeline_progress(store, cnj, "INDEXING", 0, total_physical_pages)

    vstore = VectorStore(store.db_path)
    vconn = sqlite3.connect(str(vstore.db_path))

    all_pages_to_embed = []
    for doc_id, pages in doc_pages_map.items():
        for page in pages:
            p_num = page["page"]
            p_id = f"{doc_id}:{p_num}"
            content = page.get("content_markdown", page.get("text", "")).strip()
            all_pages_to_embed.append((p_id, doc_id, p_num, content))

    existing_rows = vconn.execute(
        "SELECT page_id, content_hash FROM page_embeddings WHERE process_id=? AND model=?",
        (cnj, "embeddinggemma:300m")
    ).fetchall()
    existing_hashes = {r[0]: r[1] for r in existing_rows}

    pending = []
    for item in all_pages_to_embed:
        p_id = item[0]
        content = item[3]
        c_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if p_id not in existing_hashes or existing_hashes[p_id] != c_hash:
            pending.append((*item, c_hash))

    BATCH_SIZE = 16
    embedded_count = 0

    for b_idx in range(0, len(pending), BATCH_SIZE):
        batch = pending[b_idx:b_idx + BATCH_SIZE]
        texts = [item[3] if item[3] else "Página sem texto reconhecido." for item in batch]
        embs = generate_embeddings_batch_onnx(texts)
        now_v = vector_now()

        vconn.execute("BEGIN")
        for (p_id, doc_id, p_num, _, c_hash), emb in zip(batch, embs):
            if emb is not None:
                blob = pack_vector(emb)
                vconn.execute("""
                    INSERT OR REPLACE INTO page_embeddings(
                        page_id, document_id, process_id, page_number, model, backend, model_version, quantization, dim, vector_blob, content_hash, updated_at
                    ) VALUES(?, ?, ?, ?, 'embeddinggemma:300m', 'onnx', 'v1', 'int8', 768, ?, ?, ?)
                """, (p_id, doc_id, cnj, p_num, blob, c_hash, now_v))
                embedded_count += 1
        vconn.commit()

        if b_idx % (BATCH_SIZE * 5) == 0 or b_idx + BATCH_SIZE >= len(pending):
            _update_pipeline_progress(store, cnj, "INDEXING", embedded_count, len(pending) if pending else total_physical_pages)

    now_meta = vector_now()
    vconn.execute("""
        INSERT OR REPLACE INTO vector_index_metadata(
            process_id, model, backend, model_version, quantization, dim, created_at, updated_at
        ) VALUES(?, 'embeddinggemma:300m', 'onnx', 'v1', 'int8', 768, ?, ?)
    """, (cnj, now_meta, now_meta))
    vconn.commit()
    vconn.close()

    t_embed_dur = time.perf_counter() - t_embed_start

    # --- ESTÁGIO 5: READY (Atualização Final do Processo) ---
    _update_pipeline_progress(store, cnj, "FINALIZING", total_physical_pages, total_physical_pages)
    package_result = _finalize_process_package(store, cnj)

    t_total_dur = time.perf_counter() - t_total_start

    return {
        "status": "READY",
        "cnj": cnj,
        "reused_entries": len(reused_pecas),
        "new_entries": len(new_pecas),
        "stages": {
            "VALIDATED": {"status": "OK", "documents_validated": len(pecas)},
            "EXTRACTING": {"status": "OK", "new_extracted": extracted_count, "reused": len(reused_pecas), "total_pages": total_physical_pages, "duration_sec": round(t_extract_dur, 2)},
            "STRUCTURING": {"status": "OK", "documents_indexed": len(new_pecas), "canonical_pages": structured_pages_count, "autos_pages": len(autos_result.get("pages", [])), "autos_context": autos_context_result, "chronology_events": chronology_count, "movements": movement_materialization, "process_movement_links": process_movement_links, "participant_context": participant_context_materialization, "duration_sec": round(t_struct_dur, 2)},
            "INDEXING": {"status": "OK", "new_embeddings": embedded_count, "total_embeddings": len(all_pages_to_embed), "duration_sec": round(t_embed_dur, 2)},
            "PACKAGE": {"status": "OK", **package_result},
            "READY": {"status": "OK", "total_duration_sec": round(t_total_dur, 2)},
        },
    }
