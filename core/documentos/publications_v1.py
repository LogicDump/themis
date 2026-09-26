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
from datetime import date
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
 full_text TEXT, source_url TEXT, payload_hash TEXT NOT NULL, provenance_json TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 FOREIGN KEY(process_id) REFERENCES processes(process_id),
 UNIQUE(provider, communication_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS publications_provider_certificate
 ON publications(provider, certificate_code) WHERE communication_id IS NULL AND certificate_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS publications_process ON publications(process_id, published_on);
"""

def migrate_connection(db: sqlite3.Connection) -> None:
    db.executescript("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);")
    db.executescript(SCHEMA)
    db.execute("INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES(?,datetime('now'))", (MIGRATION,))

def normalize_cnj(value: object) -> str | None:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits if len(digits) == 20 else None

def cnj_masked(digits: str) -> str:
    return f"{digits[:7]}-{digits[7:9]}.{digits[9:13]}.{digits[13]}.{digits[14:16]}.{digits[16:]}"

def _date(value: object) -> str | None:
    raw = str(value or "")[:10]
    try: date.fromisoformat(raw)
    except ValueError: return None
    return raw

class DjenClient:
    def __init__(self, *, base_url: str = BASE_URL, opener: Callable[..., Any] | None = None, sleep: Callable[[float], None] = time.sleep):
        self.base_url, self.opener, self.sleep = base_url.rstrip("/"), opener or urllib.request.urlopen, sleep

    def communications(self, *, process_id: str, available_from: str, available_to: str, page: int = 1, page_size: int = 100) -> dict[str, Any]:
        if page_size not in {5, 100}: raise ValueError("itensPorPagina deve ser 5 ou 100")
        cnj = normalize_cnj(process_id)
        if not cnj or not _date(available_from) or not _date(available_to): raise ValueError("CNJ e datas ISO são obrigatórios")
        query = urllib.parse.urlencode({"numeroProcesso": cnj, "dataDisponibilizacaoInicio": available_from, "dataDisponibilizacaoFim": available_to, "pagina": page, "itensPorPagina": page_size})
        request = urllib.request.Request(f"{self.base_url}/comunicacao?{query}", headers={"Accept": "application/json", "User-Agent": "Themis/1.0"})
        try:
            with self.opener(request, timeout=20) as response:
                raw = response.read(); payload = json.loads(raw.decode("utf-8")); headers = dict(response.headers.items())
        except urllib.error.HTTPError as exc:
            if exc.code == 429: raise RuntimeError("DJEN rate limited; retry after 60 seconds") from exc
            raise RuntimeError(f"DJEN HTTP {exc.code}") from exc
        if not isinstance(payload, dict): raise RuntimeError("DJEN payload inválido")
        return {"payload": payload, "headers": {key.lower(): value for key, value in headers.items()}, "request_url": request.full_url}

def publication_from_item(item: dict[str, Any], *, process_id: str, request_url: str) -> dict[str, Any] | None:
    target = normalize_cnj(process_id)
    source_cnj = normalize_cnj(item.get("numero_processo") or item.get("numeroprocessocommascara"))
    medium = str(item.get("meio") or "").upper()
    if not target or source_cnj != target or medium != "D": return None
    communication_id = item.get("id") or item.get("numeroComunicacao") or item.get("numero_comunicacao")
    code = item.get("hash")
    if communication_id is None and not code: return None
    available = _date(item.get("data_disponibilizacao") or item.get("datadisponibilizacao"))
    payload = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"process_id": process_id, "provider": PROVIDER, "communication_id": str(communication_id) if communication_id is not None else None,
            "certificate_code": str(code) if code else None, "tribunal": item.get("siglaTribunal") or item.get("sigla_tribunal"),
            "organ": item.get("nomeOrgao") or item.get("orgao"), "publication_type": item.get("tipoComunicacao") or item.get("tipo_comunicacao"),
            "medium": medium, "available_on": available, "published_on": None, "full_text": item.get("texto"), "source_url": item.get("link") or request_url,
            "payload_hash": hashlib.sha256(payload.encode()).hexdigest(), "provenance": {"source": "CNJ_PJE_COMUNICA", "raw_item": item, "query_url": request_url, "medium_raw": item.get("meio")}}

def upsert_publication(db: sqlite3.Connection, publication: dict[str, Any]) -> str:
    identity = publication["communication_id"] or publication["certificate_code"]
    publication_id = "pub_" + uuid.uuid5(NAMESPACE, f"{publication['provider']}|{identity}").hex
    if publication["communication_id"] and publication["certificate_code"]:
        prior = db.execute("SELECT publication_id FROM publications WHERE provider=? AND certificate_code=?", (publication["provider"], publication["certificate_code"])).fetchone()
        if prior:
            publication_id = prior[0]
    now = "datetime('now')"
    db.execute(f"""INSERT INTO publications VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,{now},{now})
    ON CONFLICT(publication_id) DO UPDATE SET communication_id=coalesce(excluded.communication_id,publications.communication_id), certificate_code=coalesce(excluded.certificate_code,publications.certificate_code), tribunal=excluded.tribunal, organ=excluded.organ, publication_type=excluded.publication_type, medium=excluded.medium, available_on=excluded.available_on, published_on=coalesce(publications.published_on,excluded.published_on), full_text=excluded.full_text, source_url=excluded.source_url, payload_hash=excluded.payload_hash, provenance_json=excluded.provenance_json, updated_at=datetime('now')""", (publication_id, publication['process_id'], publication['provider'], publication['communication_id'], publication['certificate_code'], publication['tribunal'], publication['organ'], publication['publication_type'], publication['medium'], publication['available_on'], publication['published_on'], publication['full_text'], publication['source_url'], publication['payload_hash'], json.dumps(publication['provenance'],ensure_ascii=False)))
    return publication_id

def sync_djen(db: sqlite3.Connection, *, process_id: str, available_from: str, available_to: str, client: DjenClient | None = None) -> dict[str, Any]:
    migrate_connection(db); client = client or DjenClient(); page = 1; persisted = []
    while True:
        response = client.communications(process_id=process_id, available_from=available_from, available_to=available_to, page=page)
        items = response['payload'].get('items') or []
        for item in items:
            publication = publication_from_item(item, process_id=process_id, request_url=response['request_url']) if isinstance(item, dict) else None
            if publication: persisted.append(upsert_publication(db, publication))
        if len(items) < 100: break
        page += 1
        if response['headers'].get('x-ratelimit-remaining') == '0': raise RuntimeError('DJEN rate limit exhausted')
    return {"process_id": process_id, "publication_ids": persisted, "count": len(persisted)}

def list_publications(db: sqlite3.Connection, process_id: str) -> list[dict[str, Any]]:
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='publications'").fetchone(): return []
    db.row_factory = sqlite3.Row
    return [dict(row) | {"provenance": json.loads(row['provenance_json'] or '{}')} for row in db.execute("SELECT * FROM publications WHERE process_id=? ORDER BY coalesce(published_on,available_on) DESC,publication_id",(process_id,))]
