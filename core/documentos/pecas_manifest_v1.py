"""Manipulação e extração de metadados factuais de pecas_manifest.json."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PieceMetadata:
    document_id: str
    piece_type: str
    source_identity: str
    source_filename_literal: str
    folha_inicial: int | None
    folha_final: int | None
    page_count: int | None
    order: int | None
    provider_item_identity: str | None = None
    provider_document_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "piece_type": self.piece_type,
            "source_filename_literal": self.source_filename_literal,
            "source_identity": self.source_identity,
            "folha_inicial": self.folha_inicial,
            "folha_final": self.folha_final,
            "page_count": self.page_count,
            "document_id": self.document_id,
            "sha256": self.document_id,
            "order": self.order,
            "provider_item_identity": self.provider_item_identity,
            "provider_document_id": self.provider_document_id,
            "source": "PECAS_MANIFEST_V1",
        }


def extract_piece_type_from_filename(filename: str) -> str:
    """Extrai deterministicamente o nome/tipo da peça a partir do nome de arquivo literal capturado.
    
    Remove a extensão .pdf e o intervalo de páginas no final (ex: '(pag 1 - 18)', '(pag 43)'),
    preservando qualificadores semânticos internos como '(Outras)', '(Outros)', '(Informação)'.
    """
    fn = str(filename or "").strip()
    if not fn:
        return ""
    if fn.lower().endswith(".pdf"):
        fn = fn[:-4].strip()
    # Remove sufixos como (pag 1 - 18), (pag. 1-18), (fls 1 - 18), (folha 10), etc.
    fn = re.sub(
        r"\s*\((?:pag|pags|pág|págs|fl|fls|folha|folhas)\.?\s*\d+(?:\s*[-–—/a]\s*\d+)?\)\s*$",
        "",
        fn,
        flags=re.IGNORECASE,
    ).strip()
    return fn


def _find_manifest_path(
    manifest_or_proc_dir: Path | str,
    process_id: str | None = None,
) -> Path | None:
    target = Path(manifest_or_proc_dir)
    if target.is_file() and target.name.endswith(".json"):
        return target
    if target.is_dir():
        candidates = [
            target / "fontes" / "pecas_manifest.json",
            target / "pecas_manifest.json",
        ]
        if process_id:
            candidates.extend([
                target / "processos" / process_id / "fontes" / "pecas_manifest.json",
                target / "processos" / process_id / "pecas_manifest.json",
            ])
        for c in candidates:
            if c.is_file():
                return c
    return None


def _parse_manifest_data(manifest_path: Path | None) -> list[dict[str, Any]]:
    if not manifest_path or not manifest_path.is_file():
        return []
    raw_bytes = manifest_path.read_bytes()
    data: dict[str, Any] = {}
    for enc in ("utf-8", "cp1252", "latin-1", "iso-8859-1"):
        try:
            decoded = raw_bytes.decode(enc)
            data = json.loads(decoded)
            break
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    if not isinstance(data, dict):
        return []
    pecas_list = data.get("pecas")
    return pecas_list if isinstance(pecas_list, list) else []


def load_ordered_pecas_manifest(
    manifest_or_proc_dir: Path | str,
    process_id: str | None = None,
) -> list[PieceMetadata]:
    """Carrega o manifesto de peças preservando rigorosamente a ordem da árvore Pasta Digital."""
    manifest_path = _find_manifest_path(manifest_or_proc_dir, process_id)
    pecas_list = _parse_manifest_data(manifest_path)
    result: list[PieceMetadata] = []
    for item in pecas_list:
        if not isinstance(item, dict):
            continue
        sha = str(item.get("sha256") or "").strip()
        if not sha:
            continue
        raw_fn = str(item.get("source_filename_literal") or "").strip()
        piece_type = extract_piece_type_from_filename(raw_fn)
        order = item.get("order") if isinstance(item.get("order"), int) else None
        f_ini = item.get("folha_inicial") if isinstance(item.get("folha_inicial"), int) else None
        f_fim = item.get("folha_final") if isinstance(item.get("folha_final"), int) else None
        p_cnt = item.get("page_count") if isinstance(item.get("page_count"), int) else None
        s_id = str(item.get("source_identity") or "")
        p_item_id = str(item.get("provider_item_identity") or "").strip() or None
        p_doc_id = str(item.get("provider_document_id") or "").strip() or None

        result.append(PieceMetadata(
            document_id=sha,
            piece_type=piece_type,
            source_identity=s_id,
            source_filename_literal=raw_fn,
            folha_inicial=f_ini,
            folha_final=f_fim,
            page_count=p_cnt,
            order=order,
            provider_item_identity=p_item_id,
            provider_document_id=p_doc_id,
        ))
    return result


def load_pecas_manifest(
    manifest_or_proc_dir: Path | str,
    process_id: str | None = None,
) -> dict[str, PieceMetadata]:
    """Carrega o manifesto de peças estruturadas e retorna mapeamento {document_id_sha256: PieceMetadata}."""
    ordered = load_ordered_pecas_manifest(manifest_or_proc_dir, process_id)
    return {p.document_id: p for p in ordered}
