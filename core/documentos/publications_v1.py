"""Canonical, idempotent DJEN publications and minimal public CNJ client."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import date, datetime, timezone
from typing import Any, Callable

PROVIDER = "DJEN_COMUNICA"
BASE_URL = "https://comunicaapi.pje.jus.br/api/v1"
MIGRATION = "publications-v1"
NAMESPACE = uuid.UUID("4ef8d6ea-a6cc-5264-bd55-52822a77d91e")

SCHEMA = """
CREATE TABLE IF NOT EXISTS publications(
 publication_id TEXT PRIMARY KEY, process_id TEXT NOT NULL, provider TEXT NOT NULL,
 communication_id TEXT, certificate_code TEXT, tribunal TEXT, organ TEXT,
 publication_type TEXT, medium TEXT NOT NULL, available_on TEXT, published_on TEXT,
 publication_status TEXT, active INTEGER, canceled_on TEXT, cancellation_reason TEXT,
 full_text TEXT, source_url TEXT, recipients_json TEXT NOT NULL DEFAULT '[]',
 recipient_lawyers_json TEXT NOT NULL DEFAULT '[]',
 payload_hash TEXT NOT NULL, provenance_json TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 FOREIGN KEY(process_id) REFERENCES processes(process_id),
 UNIQUE(provider, communication_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS publications_provider_certificate
 ON publications(provider, certificate_code) WHERE communication_id IS NULL AND certificate_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS publications_process ON publications(process_id, published_on, available_on);
"""

def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def migrate_connection(db: sqlite3.Connection) -> dict[str, Any]:
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    db.executescript(SCHEMA)
    columns = {str(row[1]) for row in db.execute("PRAGMA table_info(publications)")}
    if "recipients_json" not in columns:
        db.execute("ALTER TABLE publications ADD COLUMN recipients_json TEXT NOT NULL DEFAULT '[]'")
    if "recipient_lawyers_json" not in columns:
        db.execute("ALTER TABLE publications ADD COLUMN recipient_lawyers_json TEXT NOT NULL DEFAULT '[]'")
    for name, declaration in (
        ("publication_status", "TEXT"),
        ("active", "INTEGER"),
        ("canceled_on", "TEXT"),
        ("cancellation_reason", "TEXT"),
    ):
        if name not in columns:
            db.execute(f"ALTER TABLE publications ADD COLUMN {name} {declaration}")
    applied = db.execute("SELECT 1 FROM schema_migrations WHERE version=?", (MIGRATION,)).fetchone()
    db.execute("INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES(?,?)", (MIGRATION, _now()))
    db.commit()
    return {"migration_version": MIGRATION, "already_applied": bool(applied)}

def normalize_cnj(value: object) -> str | None:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits if len(digits) == 20 else None

def _date(value: object) -> str | None:
    raw = str(value or "")[:10]
    try:
        date.fromisoformat(raw)
    except ValueError:
        return None
    return raw

def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []

class DjenClient:
    def __init__(
        self,
        *,
        base_url: str = BASE_URL,
        opener: Callable[..., Any] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.base_url = base_url.rstrip("/")
        self.opener = opener or urllib.request.urlopen
        self.sleep = sleep

    def communications(
        self,
        *,
        process_id: str,
        available_from: str,
        available_to: str,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        if page_size not in {5, 100}:
            raise ValueError("itensPorPagina deve ser 5 ou 100")
        cnj = normalize_cnj(process_id)
        if not cnj or not _date(available_from) or not _date(available_to):
            raise ValueError("CNJ e datas ISO são obrigatórios")
        if available_from > available_to:
            raise ValueError("intervalo DJEN inválido")
        query = urllib.parse.urlencode({
            "numeroProcesso": cnj,
            "dataDisponibilizacaoInicio": available_from,
            "dataDisponibilizacaoFim": available_to,
            "pagina": page,
            "itensPorPagina": page_size,
        })
        request = urllib.request.Request(
            f"{self.base_url}/comunicacao?{query}",
            headers={"Accept": "application/json", "User-Agent": "Themis/1.0"},
        )
        try:
            with self.opener(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
                headers = dict(response.headers.items())
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                suffix = f"; retry-after={retry_after}" if retry_after else ""
                raise RuntimeError(f"DJEN rate limited{suffix}") from exc
            raise RuntimeError(f"DJEN HTTP {exc.code}") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("DJEN payload inválido")
        return {
            "payload": payload,
            "headers": {key.lower(): value for key, value in headers.items()},
            "request_url": request.full_url,
        }

def publication_from_item(
    item: dict[str, Any], *, process_id: str, request_url: str
) -> dict[str, Any] | None:
    target = normalize_cnj(process_id)
    source_cnj = normalize_cnj(item.get("numero_processo") or item.get("numeroprocessocommascara"))
    medium = str(item.get("meio") or "").upper()
    if not target or source_cnj != target or medium != "D":
        return None
    communication_id = item.get("id") or item.get("numeroComunicacao") or item.get("numero_comunicacao")
    certificate_code = item.get("hash")
    if communication_id is None and not certificate_code:
        return None
    payload = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "process_id": process_id,
        "provider": PROVIDER,
        "communication_id": str(communication_id) if communication_id is not None else None,
        "certificate_code": str(certificate_code) if certificate_code else None,
        "tribunal": item.get("siglaTribunal") or item.get("sigla_tribunal"),
        "organ": item.get("nomeOrgao") or item.get("orgao"),
        "publication_type": item.get("tipoComunicacao") or item.get("tipo_comunicacao"),
        "medium": medium,
        "available_on": _date(item.get("data_disponibilizacao") or item.get("datadisponibilizacao")),
        "published_on": None,
        "publication_status": item.get("status"),
        "active": item.get("ativo") if isinstance(item.get("ativo"), bool) else None,
        "canceled_on": _date(item.get("data_cancelamento")),
        "cancellation_reason": item.get("motivo_cancelamento"),
        "full_text": item.get("texto"),
        "source_url": item.get("link") or request_url,
        "recipients": _as_list(item.get("destinatarios")),
        "recipient_lawyers": _as_list(item.get("destinatarioadvogados")),
        "payload_hash": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "provenance": {
            "source": "CNJ_PJE_COMUNICA",
            "raw_item": item,
            "query_url": request_url,
            "medium_raw": item.get("meio"),
        },
    }

def upsert_publication(db: sqlite3.Connection, publication: dict[str, Any]) -> str:
    identity = publication["communication_id"] or publication["certificate_code"]
    publication_id = "pub_" + uuid.uuid5(
        NAMESPACE, f"{publication['provider']}|{identity}"
    ).hex
    if publication["communication_id"] and publication["certificate_code"]:
        prior = db.execute(
            "SELECT publication_id FROM publications WHERE provider=? AND certificate_code=?",
            (publication["provider"], publication["certificate_code"]),
        ).fetchone()
        if prior:
            publication_id = str(prior[0])
    now = _now()
    db.execute(
        """INSERT INTO publications(
          publication_id,process_id,provider,communication_id,certificate_code,tribunal,organ,
          publication_type,medium,available_on,published_on,publication_status,active,canceled_on,cancellation_reason,
          full_text,source_url,recipients_json,recipient_lawyers_json,payload_hash,provenance_json,created_at,updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(publication_id) DO UPDATE SET
          communication_id=coalesce(excluded.communication_id,publications.communication_id),
          certificate_code=coalesce(excluded.certificate_code,publications.certificate_code),
          tribunal=excluded.tribunal, organ=excluded.organ, publication_type=excluded.publication_type,
          medium=excluded.medium, available_on=excluded.available_on,
          published_on=coalesce(publications.published_on,excluded.published_on),
          publication_status=excluded.publication_status, active=excluded.active,
          canceled_on=excluded.canceled_on, cancellation_reason=excluded.cancellation_reason,
          full_text=excluded.full_text, source_url=excluded.source_url,
          recipients_json=excluded.recipients_json,
          recipient_lawyers_json=excluded.recipient_lawyers_json,
          payload_hash=excluded.payload_hash, provenance_json=excluded.provenance_json,
          updated_at=excluded.updated_at""",
        (
            publication_id, publication["process_id"], publication["provider"],
            publication["communication_id"], publication["certificate_code"],
            publication["tribunal"], publication["organ"], publication["publication_type"],
            publication["medium"], publication["available_on"], publication["published_on"],
            publication["publication_status"],
            None if publication["active"] is None else int(publication["active"]),
            publication["canceled_on"], publication["cancellation_reason"],
            publication["full_text"], publication["source_url"],
            json.dumps(publication["recipients"], ensure_ascii=False),
            json.dumps(publication["recipient_lawyers"], ensure_ascii=False),
            publication["payload_hash"],
            json.dumps(publication["provenance"], ensure_ascii=False),
            now, now,
        ),
    )
    return publication_id

def sync_djen(
    db: sqlite3.Connection, *, process_id: str, available_from: str, available_to: str,
    client: DjenClient | None = None,
) -> dict[str, Any]:
    migrate_connection(db)
    if not db.execute("SELECT 1 FROM processes WHERE process_id=?", (process_id,)).fetchone():
        raise ValueError("processo não existe no Process Package")
    client = client or DjenClient()
    page = 1
    persisted: list[str] = []
    while True:
        response = client.communications(
            process_id=process_id,
            available_from=available_from,
            available_to=available_to,
            page=page,
        )
        items = response["payload"].get("items") or []
        if not isinstance(items, list):
            raise RuntimeError("DJEN payload.items inválido")
        for item in items:
            publication = publication_from_item(
                item, process_id=process_id, request_url=response["request_url"]
            ) if isinstance(item, dict) else None
            if publication:
                persisted.append(upsert_publication(db, publication))
        if len(items) < 100:
            break
        page += 1
        if response["headers"].get("x-ratelimit-remaining") == "0":
            raise RuntimeError("DJEN rate limit exhausted")
    db.commit()
    return {
        "process_id": process_id,
        "available_from": available_from,
        "available_to": available_to,
        "publication_ids": persisted,
        "count": len(persisted),
    }

def list_publications(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    if not db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='publications'"
    ).fetchone():
        return []
    db.row_factory = sqlite3.Row
    result = []
    rows = db.execute(
        """SELECT * FROM publications WHERE process_id=?
           ORDER BY coalesce(published_on,available_on) DESC, publication_id""",
        (process_id,),
    )
    for row in rows:
        value = dict(row)
        value["recipients"] = json.loads(value.pop("recipients_json") or "[]")
        value["recipient_lawyers"] = json.loads(value.pop("recipient_lawyers_json") or "[]")
        value["provenance"] = json.loads(value.pop("provenance_json") or "{}")
        result.append(value)
    return result
