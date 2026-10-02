"""Deterministic linkage from provider chronology to document-derived Movements.

The provider chronology (process_movements) is the primary timeline.  The
document-derived movements table is used only as a factual bridge to attach
provider artifacts/pages when the association is unambiguous.
"""
from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "process-movement-linker-v1"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS process_movement_links(
  process_movement_id TEXT NOT NULL,
  derived_movement_id TEXT NOT NULL,
  process_id TEXT NOT NULL,
  match_method TEXT NOT NULL,
  confidence TEXT NOT NULL,
  evidence_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY(process_movement_id, derived_movement_id),
  FOREIGN KEY(process_movement_id) REFERENCES process_movements(movement_id),
  FOREIGN KEY(derived_movement_id) REFERENCES movements(movement_id)
);
CREATE INDEX IF NOT EXISTS idx_process_movement_links_process
  ON process_movement_links(process_id);
"""

def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii").upper()
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()

def _date(value: Any) -> str | None:
    text = str(value or "")
    match = re.search(r"(\d{2})/(\d{2})/(\d{4})", text)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    return match.group(1) if match else None

def _protocol(value: Any) -> str | None:
    compact = re.sub(r"[^A-Z0-9]", "", _norm(value))
    match = re.search(r"(W[A-Z]{2,4}\d{10,})", compact)
    return match.group(1) if match else None

def _document_category(value: Any) -> str | None:
    text = _norm(value)
    rules = (
        ("CERTIDAO DE PUBLICACAO", "CERT_PUB"),
        ("ATO ORDINATORIO", "ATO_ORD"),
        ("DESPACHO", "DESPACHO"),
        ("DECISAO", "DECISAO"),
        ("ACORDAO", "ACORDAO"),
        ("RECEBIMENTO DE OFICIO", "OFICIO"),
        ("OFICIO", "OFICIO"),
        ("E MAIL", "EMAIL"),
        ("MANDADO", "MANDADO"),
        ("CARTA", "CARTA"),
        ("AVISO DE RECEBIMENTO", "AR"),
        ("CERTIDAO", "CERTIDAO"),
        ("RELATORIO FINAL", "REL_FINAL"),
        ("DOCUMENTOS DIVERSOS", "DOCUMENTO"),
        ("IMPUGNACAO AO CUMPRIMENTO DE DECISAO", "PETICAO"),
        ("PETICAO", "PETICAO"),
        ("PEDIDO", "PETICAO"),
    )
    return next((category for needle, category in rules if needle in text), None)

def _provider_category(value: Any) -> str | None:
    text = _norm(value)
    if (
        "CONCLUSOS " in text
        or text.startswith("REMETIDO AO DJE")
        or "SUSPENSAO DO PRAZO" in text
        or "PROCESSO ENTRANHADO" in text
        or "INCIDENTE PROCESSUAL INSTAURADO" in text
        or "REMETIDOS OS AUTOS" in text
    ):
        return None
    rules = (
        ("CERTIDAO DE PUBLICACAO EXPEDIDA", "CERT_PUB"),
        ("ATO ORDINATORIO", "ATO_ORD"),
        ("PROFERIDO DESPACHO", "DESPACHO"),
        ("PROFERIDAS OUTRAS DECISOES", "DECISAO"),
        ("EMBARGOS DE DECLARACAO NAO ACOLHIDOS", "DECISAO"),
        ("DECISAO", "DECISAO"),
        ("SENTENCA VOTO ACORDAO", "ACORDAO"),
        ("AGRAVO DE INSTRUMENTO COPIA DO ACORDAO", "ACORDAO"),
        ("OFICIO", "OFICIO"),
        ("MENSAGEM ELETRONICA E MAIL", "EMAIL"),
        ("MANDADO", "MANDADO"),
        ("CARTA", "CARTA"),
        ("AR ", "AR"),
        ("CERTIDAO DE CARTORIO", "CERTIDAO"),
        ("CERTIDAO DE REMESSA", "CERTIDAO"),
        ("RELATORIO FINAL", "REL_FINAL"),
        ("DOCUMENTO JUNTADO", "DOCUMENTO"),
    )
    category = next((category for needle, category in rules if needle in text), None)
    if category:
        return category
    if (
        "JUNTAD" in text
        or text.startswith(("PEDIDO ", "PETICAO ", "IMPUGNACAO ", "MANIFESTACAO ", "REPLICA ",
                            "ALEGACOES FINAIS", "ESPECIFICACAO DE PROVAS"))
    ):
        return "PETICAO"
    return None

def ensure_schema(db: sqlite3.Connection) -> None:
    db.executescript(_SCHEMA)
    db.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    db.execute(
        "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?,?)",
        (SCHEMA_VERSION, _now()),
    )

def audit_links(db: sqlite3.Connection, process_id: str) -> dict[str, Any]:
    db.row_factory = sqlite3.Row
    provider = [dict(row) for row in db.execute(
        "SELECT * FROM process_movements WHERE process_id=?", (process_id,)
    )]
    derived = [dict(row) for row in db.execute(
        "SELECT * FROM movements WHERE process_id=?", (process_id,)
    )]

    links: list[dict[str, Any]] = []
    provider_matched: set[str] = set()
    derived_matched: set[str] = set()

    derived_by_protocol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    provider_by_protocol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in derived:
        protocol = _protocol(item.get("protocol"))
        if protocol:
            derived_by_protocol[protocol].append(item)
    for item in provider:
        protocol = _protocol(item.get("content"))
        if protocol:
            provider_by_protocol[protocol].append(item)

    for protocol, provider_items in provider_by_protocol.items():
        derived_items = derived_by_protocol.get(protocol, [])
        if len(provider_items) != 1 or len(derived_items) != 1:
            continue
        p_item, d_item = provider_items[0], derived_items[0]
        provider_matched.add(p_item["movement_id"])
        derived_matched.add(d_item["movement_id"])
        links.append({
            "process_movement_id": p_item["movement_id"],
            "derived_movement_id": d_item["movement_id"],
            "match_method": "EXACT_PROTOCOL",
            "confidence": "EXACT",
            "evidence": {"protocol_normalized": protocol},
        })

    provider_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    derived_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in provider:
        if item["movement_id"] in provider_matched:
            continue
        key = (_date(item.get("occurred_at")), _provider_category(item.get("movement_type")))
        if all(key):
            provider_groups[key].append(item)
    for item in derived:
        if item["movement_id"] in derived_matched:
            continue
        key = (_date(item.get("occurred_at")), _document_category(item.get("movement_type")))
        if all(key):
            derived_groups[key].append(item)

    for key, provider_items in provider_groups.items():
        derived_items = derived_groups.get(key, [])
        if len(provider_items) != 1 or len(derived_items) != 1:
            continue
        p_item, d_item = provider_items[0], derived_items[0]
        provider_matched.add(p_item["movement_id"])
        derived_matched.add(d_item["movement_id"])
        links.append({
            "process_movement_id": p_item["movement_id"],
            "derived_movement_id": d_item["movement_id"],
            "match_method": "DATE_TYPE_UNIQUE",
            "confidence": "HIGH",
            "evidence": {
                "date": key[0],
                "category": key[1],
                "provider_type": p_item.get("movement_type"),
                "document_type": d_item.get("movement_type"),
            },
        })

    methods: dict[str, int] = defaultdict(int)
    for link in links:
        methods[link["match_method"]] += 1
    return {
        "process_id": process_id,
        "provider_movements": len(provider),
        "derived_movements": len(derived),
        "links": links,
        "link_count": len(links),
        "links_by_method": dict(sorted(methods.items())),
        "provider_unmatched": len(provider) - len(provider_matched),
        "derived_unmatched": len(derived) - len(derived_matched),
    }

def _movement_document_ids(row: sqlite3.Row) -> set[str]:
    try:
        payload = json.loads(row["payload_json"] or "{}")
    except (TypeError, ValueError):
        return set()
    result: set[str] = set()
    for key in ("components", "pieces", "documents"):
        for item in payload.get(key) or []:
            if isinstance(item, dict) and item.get("document_id"):
                result.add(str(item["document_id"]))
    return result

def materialize_links(db: sqlite3.Connection, process_id: str) -> dict[str, Any]:
    ensure_schema(db)
    audit = audit_links(db, process_id)
    stamp = _now()
    linked_artifacts = 0
    artifact_conflicts: list[dict[str, str]] = []

    for link in audit["links"]:
        evidence_json = json.dumps(link["evidence"], ensure_ascii=False, sort_keys=True)
        db.execute(
            """INSERT INTO process_movement_links(
                 process_movement_id,derived_movement_id,process_id,
                 match_method,confidence,evidence_json,created_at,updated_at
               ) VALUES(?,?,?,?,?,?,?,?)
               ON CONFLICT(process_movement_id,derived_movement_id) DO UPDATE SET
                 match_method=excluded.match_method,
                 confidence=excluded.confidence,
                 evidence_json=excluded.evidence_json,
                 updated_at=excluded.updated_at""",
            (
                link["process_movement_id"], link["derived_movement_id"], process_id,
                link["match_method"], link["confidence"], evidence_json, stamp, stamp,
            ),
        )

        movement_row = db.execute(
            "SELECT payload_json FROM movements WHERE movement_id=? AND process_id=?",
            (link["derived_movement_id"], process_id),
        ).fetchone()
        if movement_row is None:
            continue
        document_ids = _movement_document_ids(movement_row)
        if not document_ids:
            continue
        placeholders = ",".join("?" for _ in document_ids)
        artifacts = db.execute(
            f"""SELECT DISTINCT a.provider_artifact_id,a.movement_id
                FROM provider_artifacts a
                JOIN provider_artifact_pages ap
                  ON ap.provider_artifact_id=a.provider_artifact_id
                JOIN canonical_page_observations o
                  ON o.canonical_page_id=ap.canonical_page_id
                WHERE a.process_id=? AND o.document_id IN ({placeholders})""",
            (process_id, *sorted(document_ids)),
        ).fetchall()
        for artifact in artifacts:
            current = artifact["movement_id"]
            target = link["process_movement_id"]
            if current not in (None, "", target):
                artifact_conflicts.append({
                    "provider_artifact_id": artifact["provider_artifact_id"],
                    "existing_process_movement_id": current,
                    "proposed_process_movement_id": target,
                })
                continue
            if current != target:
                db.execute(
                    "UPDATE provider_artifacts SET movement_id=?, updated_at=? WHERE provider_artifact_id=?",
                    (target, stamp, artifact["provider_artifact_id"]),
                )
                linked_artifacts += 1

    db.commit()
    return {
        **{key: value for key, value in audit.items() if key != "links"},
        "links_materialized": audit["link_count"],
        "artifacts_linked": linked_artifacts,
        "artifact_conflicts": artifact_conflicts,
    }
