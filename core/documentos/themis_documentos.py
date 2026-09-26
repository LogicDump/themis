"""Persistência process-centric v2 do Jurídico; sem migração de schema v1."""
from __future__ import annotations
import base64, hashlib, json, os, re, shutil, sqlite3, time, unicodedata, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
try:
    from .process_resolvers.esaj_tjsp import resolve_page_one
except ImportError:
    from process_resolvers.esaj_tjsp import resolve_page_one

FORMAT_VERSION = 4
NORMALIZATION_VERSION = "conservative-whitespace-v1"
MAX_RESULTS = 50
CNJ = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")
DATE = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")
FOLIO = re.compile(r"\b(?:fls?\.?|folhas?)\s*(\d{1,6})\b", re.I)
FIELD_PATTERNS = {"tribunal": re.compile(r"\b(TJ[A-Z]{2}|TRF\s*\d|STJ|STF|TST|TRT\s*\d+)\b", re.I), "comarca": re.compile(r"\bComarca\s+de\s+([^\n]{2,100})", re.I), "foro": re.compile(r"\bForo\s+(?:de\s+)?([^\n]{2,100})", re.I), "requerente": re.compile(r"\bRequerente\s*:?\s*([^\n]{2,180})", re.I), "requerido": re.compile(r"\bRequerido\s*:?\s*([^\n]{2,180})", re.I), "tipo_ato": re.compile(r"\b(Sentença|Decisão|Despacho|Certidão|Petição|Acórdão|Intimação)\b", re.I)}

def normalized_text(text: str) -> str: return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""): digest.update(block)
    return digest.hexdigest()
def content_id(text: str) -> tuple[str, str]:
    value = normalized_text(text); return hashlib.sha256(value.encode("utf-8")).hexdigest(), value
def now() -> str: return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def compact(text: str, start: int, end: int, radius: int = 100) -> str: return normalized_text(text[max(0, start-radius):end+radius])

def page_evidence(page: dict[str, Any]) -> list[dict[str, Any]]:
    text, number = page["content_markdown"], page["page"]
    folio = next((m.group(1) for m in FOLIO.finditer(text)), None); dates = [m.group(0) for m in DATE.finditer(text)][:3]; found = []
    for pattern in [CNJ, *FIELD_PATTERNS.values()]:
        field = "cnj" if pattern is CNJ else next(k for k, v in FIELD_PATTERNS.items() if v is pattern)
        for match in list(pattern.finditer(text))[:8]: found.append({"field": field, "value": (match.group(1) if match.lastindex else match.group(0)).strip(), "page": number, "context": compact(text, match.start(), match.end()), "folio": folio, "act_date": dates[0] if dates else None})
    return found

SCHEMA = """
CREATE TABLE IF NOT EXISTS processes(process_id TEXT PRIMARY KEY,status TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS process_relations(relation_id TEXT PRIMARY KEY,from_process_id TEXT NOT NULL,to_process_id TEXT NOT NULL,relation_kind TEXT NOT NULL,evidence TEXT,created_at TEXT NOT NULL,FOREIGN KEY(from_process_id) REFERENCES processes(process_id),FOREIGN KEY(to_process_id) REFERENCES processes(process_id));
CREATE TABLE IF NOT EXISTS process_sources(process_id TEXT NOT NULL,source_type TEXT NOT NULL,source_id TEXT NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(process_id,source_type,source_id),FOREIGN KEY(process_id) REFERENCES processes(process_id));
CREATE TABLE IF NOT EXISTS process_movements(movement_id TEXT PRIMARY KEY,process_id TEXT NOT NULL,movement_type TEXT NOT NULL,occurred_at TEXT,content TEXT,FOREIGN KEY(process_id) REFERENCES processes(process_id));
CREATE TABLE IF NOT EXISTS files(file_id TEXT PRIMARY KEY,path TEXT NOT NULL UNIQUE,sha256 TEXT NOT NULL UNIQUE,size_bytes INTEGER NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS documents(document_id TEXT PRIMARY KEY,process_id TEXT NOT NULL,file_id TEXT NOT NULL,document_type TEXT NOT NULL,status TEXT NOT NULL,page_count INTEGER NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(process_id) REFERENCES processes(process_id),FOREIGN KEY(file_id) REFERENCES files(file_id));
CREATE TABLE IF NOT EXISTS docket_snapshots(snapshot_id TEXT PRIMARY KEY,process_id TEXT NOT NULL,created_at TEXT NOT NULL,status TEXT NOT NULL,FOREIGN KEY(process_id) REFERENCES processes(process_id));
CREATE TABLE IF NOT EXISTS docket_documents(docket_document_id TEXT PRIMARY KEY,snapshot_id TEXT NOT NULL,document_id TEXT NOT NULL,ordinal INTEGER NOT NULL,FOREIGN KEY(snapshot_id) REFERENCES docket_snapshots(snapshot_id),FOREIGN KEY(document_id) REFERENCES documents(document_id));
CREATE TABLE IF NOT EXISTS pages(page_id TEXT PRIMARY KEY,document_id TEXT NOT NULL,page_number INTEGER NOT NULL,content TEXT NOT NULL,quality TEXT NOT NULL,engine TEXT NOT NULL DEFAULT 'pdfium',fallback_used INTEGER NOT NULL DEFAULT 0,content_id TEXT NOT NULL,process_folio INTEGER,page_class TEXT NOT NULL DEFAULT 'NATIVE_VALID',UNIQUE(document_id,page_number),FOREIGN KEY(document_id) REFERENCES documents(document_id));
CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(page_id UNINDEXED,document_id UNINDEXED,content);
CREATE TABLE IF NOT EXISTS evidence(evidence_id TEXT PRIMARY KEY,page_id TEXT NOT NULL,field TEXT NOT NULL,value TEXT NOT NULL,context TEXT NOT NULL,folio TEXT,act_date TEXT,FOREIGN KEY(page_id) REFERENCES pages(page_id));
CREATE TABLE IF NOT EXISTS chat_context_bindings(chat_id TEXT PRIMARY KEY,user_id TEXT NOT NULL,owner_type TEXT NOT NULL CHECK(owner_type='PROCESS'),owner_id TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(owner_id) REFERENCES processes(process_id));
CREATE INDEX IF NOT EXISTS pages_document_number ON pages(document_id,page_number);
CREATE INDEX IF NOT EXISTS evidence_lookup ON evidence(field,value);
"""

class Store:
    def __init__(self, root: Path, process_id: str | None = None) -> None:
        self.root = root
        self.process_id = process_id
        self.documents = root / "documentos"
        self.processes = root / "processos"
        themis_db = root / "index" / "themis.db"
        juridico_db = root / "index" / "juridico.db"
        self._legacy_db_path = themis_db if themis_db.exists() else (juridico_db if juridico_db.exists() else themis_db)
        from core.runtime_paths import process_db_path
        self.db_path = process_db_path(process_id, root) if process_id else self._legacy_db_path
    def for_process(self, process_id: str) -> "Store":
        return Store(self.root, process_id=process_id)
    def process_path(self, process_id: str) -> Path: return self.processes / process_id
    def process_snapshots_dir(self, process_id: str) -> Path: return self.process_path(process_id) / "snapshots"
    def process_snapshot_path(self, process_id: str) -> Path: return self.process_path(process_id) / "source_snapshot.json"
    def process_snapshot_versioned_path(self, process_id: str, stamp: str) -> Path: return self.process_snapshots_dir(process_id) / stamp / "source_snapshot.json"
    def process_cpopg_snapshot_path(self, process_id: str) -> Path: return self.process_path(process_id) / "cpopg_snapshot.json"
    def process_cpopg_snapshot_versioned_path(self, process_id: str, stamp: str) -> Path: return self.process_snapshots_dir(process_id) / stamp / "cpopg_snapshot.json"
    def process_manifest_path(self, process_id: str) -> Path: return self.process_path(process_id) / "manifest.json"
    def process_fontes_path(self, process_id: str) -> Path: return self.process_path(process_id) / "fontes"
    def process_objetos_path(self, process_id: str) -> Path: return self.process_fontes_path(process_id) / "objetos"
    def process_parts_path(self, process_id: str) -> Path: return self.process_fontes_path(process_id) / "parts"
    def process_documents_path(self, process_id: str) -> Path: return self.process_path(process_id) / "derivados" / "pecas"
    def process_derivados_path(self, process_id: str) -> Path: return self.process_path(process_id) / "derivados"
    def process_temp_path(self, process_id: str) -> Path: return self.process_path(process_id) / ".temp"
    def delete_process(self, process_id: str, confirm_process_id: str) -> dict[str, Any]:
        return delete_process(store=self, process_id=process_id, confirm_process_id=confirm_process_id)
    def connect(self, process_id: str | None = None) -> sqlite3.Connection:
        from core.runtime_paths import process_db_path
        process_id = process_id or self.process_id
        target = process_db_path(process_id, self.root) if process_id else self._legacy_db_path
        target.parent.mkdir(parents=True, exist_ok=True); db = sqlite3.connect(target); db.row_factory = sqlite3.Row; db.execute("PRAGMA foreign_keys=ON"); db.executescript(SCHEMA)
        page_columns = {row[1] for row in db.execute("PRAGMA table_info(pages)")}
        if "process_folio" not in page_columns:
            db.execute("ALTER TABLE pages ADD COLUMN process_folio INTEGER")
        if "page_class" not in page_columns:
            db.execute("ALTER TABLE pages ADD COLUMN page_class TEXT NOT NULL DEFAULT 'NATIVE_VALID'")
        # Provider artifacts are an additive, provider-neutral part of the
        # document store and must be available to every ingestion.
        from core.documentos.provider_artifacts_v1 import migrate_connection
        migrate_connection(db)
        from core.documentos.movement_store_v1 import migrate_connection as migrate_movements
        migrate_movements(db)
        from core.documentos.movement_summary_store_v1 import migrate_connection as migrate_movement_summaries
        migrate_movement_summaries(db)
        from core.documentos.case_synthesis_store_v1 import migrate_connection as migrate_case_synthesis
        migrate_case_synthesis(db)
        from core.documentos.process_event_store_v1 import migrate_connection as migrate_process_events
        migrate_process_events(db)
        from core.documentos.deadline_instruction_store_v1 import migrate_connection as migrate_deadline_instructions
        migrate_deadline_instructions(db)
        from core.documentos.deadline_obligation_store_v1 import migrate_connection as migrate_deadline_obligations
        migrate_deadline_obligations(db)
        from core.documentos.participant_context_store_v1 import migrate_connection as migrate_participant_context
        migrate_participant_context(db)
        if process_id:
            from core.process_storage import sync_workspace_profiles
            sync_workspace_profiles(db, root=self.root)
        return db
    def _derived_document_dir(self, document_id: str) -> Path:
        if self.process_id:
            return self.process_derivados_path(self.process_id) / "documentos" / document_id
        return self.documents / document_id
    def manifest_path(self, document_id: str) -> Path: return self._derived_document_dir(document_id) / "manifest.json"
    def pages_path(self, document_id: str) -> Path: return self._derived_document_dir(document_id) / "pages.ndjson"
    def source_path(self, document_id: str) -> Path:
        if self.process_id:
            return self.process_objetos_path(self.process_id) / f"{document_id}.pdf"
        return self.documents / document_id / "source.pdf"
    def visual_blob_path(self, blob_sha256: str) -> Path: return self.documents / "blobs" / "sha256" / blob_sha256[:2] / blob_sha256
    def visual_manifest_path(self, source_identity_sha256: str) -> Path: return self.documents / "source-manifests" / "v1" / source_identity_sha256[:2] / f"{source_identity_sha256}.json"

    def materialize_source(self, source: Path, document_id: str) -> Path:
        """Create the immutable, content-addressed source held by this store."""
        target = self.source_path(document_id)
        if target.is_file():
            if sha256_file(target) != document_id:
                raise ValueError(f"fonte canônica divergente para {document_id}")
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
        try:
            shutil.copyfile(source, temporary)
            if sha256_file(temporary) != document_id:
                raise ValueError("fonte copiada não corresponde ao document_id")
            # Do not replace an already materialized source: a concurrent or
            # prior ingestion wins only after its content hash is verified.
            if target.exists():
                if sha256_file(target) != document_id:
                    raise ValueError(f"fonte canônica divergente para {document_id}")
                return target
            os.replace(temporary, target)
            return target
        finally:
            if temporary.exists():
                temporary.unlink()

    def write_visual_blob(self, blob_sha256: str, raw_bytes: bytes) -> Path:
        if hashlib.sha256(raw_bytes).hexdigest() != blob_sha256:
            raise ValueError(f"blob visual divergente para {blob_sha256}")
        target = self.visual_blob_path(blob_sha256)
        if target.is_file():
            if sha256_file(target) != blob_sha256:
                raise ValueError(f"blob visual canônico divergente para {blob_sha256}")
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
        try:
            temporary.write_bytes(raw_bytes)
            if sha256_file(temporary) != blob_sha256:
                raise ValueError(f"blob visual temporário divergente para {blob_sha256}")
            if target.exists():
                if sha256_file(target) != blob_sha256:
                    raise ValueError(f"blob visual canônico divergente para {blob_sha256}")
                return target
            os.replace(temporary, target)
            return target
        finally:
            if temporary.exists():
                temporary.unlink()

    def write_visual_manifest(self, source_identity_sha256: str, manifest: dict[str, Any]) -> Path:
        target = self.visual_manifest_path(source_identity_sha256)
        payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        if target.is_file():
            if target.read_bytes() != payload:
                raise ValueError(f"manifest visual canônico divergente para {source_identity_sha256}")
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
        try:
            temporary.write_bytes(payload)
            if target.exists():
                if target.read_bytes() != payload:
                    raise ValueError(f"manifest visual canônico divergente para {source_identity_sha256}")
                return target
            os.replace(temporary, target)
            return target
        finally:
            if temporary.exists():
                temporary.unlink()

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
def write_pages(path: Path, pages: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text("".join(json.dumps(p, ensure_ascii=False, separators=(",", ":"))+"\n" for p in pages), encoding="utf-8")
def read_pages(path: Path) -> list[dict[str, Any]]: return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
def _ensure_process(db: sqlite3.Connection, process_id: str) -> None: db.execute("INSERT OR IGNORE INTO processes VALUES(?,?,?)", (process_id,"ACTIVE",now()))

def _visual_items_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Small persisted index; full visual instances are re-extracted on demand."""
    kinds: dict[str, int] = {}
    path_segments = paths_with_curves = paths_with_stroke = 0
    for item in items:
        kind = str(item.get("kind", "unknown"))
        kinds[kind] = kinds.get(kind, 0) + 1
        if kind == "path":
            summary = item.get("summary") or {}
            path_segments += int(summary.get("segment_count") or 0)
            paths_with_curves += int(bool(summary.get("has_curves")))
            paths_with_stroke += int(bool((summary.get("draw_mode") or {}).get("has_stroke")))
    return {
        "total": len(items),
        "by_kind": dict(sorted(kinds.items())),
        "path_segment_count": path_segments,
        "paths_with_curves": paths_with_curves,
        "paths_with_stroke": paths_with_stroke,
    }

def _decoded_blob(record: dict[str, Any], *, role: str) -> bytes:
    encoded = record.get("raw_bytes_base64")
    if not isinstance(encoded, str) or not isinstance(record.get("blob_sha256"), str):
        raise ValueError(f"{role} visual sem bytes ou hash")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise ValueError(f"{role} visual Base64 inválido") from exc
    if hashlib.sha256(raw).hexdigest() != record["blob_sha256"]:
        raise ValueError(f"{role} visual não corresponde ao blob_sha256")
    return raw

def _component_manifest(store: Store, component: dict[str, Any]) -> dict[str, Any]:
    raw = _decoded_blob(component, role=str(component.get("role", "componente")))
    store.write_visual_blob(component["blob_sha256"], raw)
    return {key: value for key, value in component.items() if key != "raw_bytes_base64"}

def _source_identity_sha256(blob_sha256: str, dictionary: Any, components: list[dict[str, Any]]) -> str:
    identity = {
        "blob_sha256": blob_sha256,
        "dictionary": dictionary,
        "components": [
            {key: component.get(key) for key in ("role", "blob_sha256", "indirect_ref", "dictionary")}
            for component in components
        ],
    }
    return hashlib.sha256(json.dumps(identity, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

def persist_visual_asset_sources(store: Store, pages: list[dict[str, Any]]) -> None:
    """Materialize lossless visual sources, replacing transient Base64 with refs."""
    for page in pages:
        structure = page.get("structure") or {}
        for asset in structure.get("visual_assets", []):
            source = asset.get("visual_asset_source")
            if not isinstance(source, dict):
                continue
            status = source.get("match_status")
            if status != "MATCHED_BY_BLOB_GEOMETRY":
                asset["visual_asset_source"] = {
                    key: value for key, value in source.items()
                    if key in {"match_status", "blob_sha256", "byte_length", "candidate_count"}
                }
                continue
            if source.get("source_manifest_ref") and "raw_bytes_base64" not in source:
                continue
            source_identity = source.get("source_identity_sha256")
            if not isinstance(source_identity, str):
                raise ValueError("fonte visual matched sem source_identity_sha256")
            raw = _decoded_blob(source, role="fonte")
            store.write_visual_blob(source["blob_sha256"], raw)
            components = [_component_manifest(store, component) for component in source.get("components", [])]
            if _source_identity_sha256(source["blob_sha256"], source.get("dictionary", {}), components) != source_identity:
                raise ValueError("fonte visual não corresponde ao source_identity_sha256")
            manifest = {
                "visual_asset_source_version": "v1",
                "source_identity_sha256": source_identity,
                "blob_sha256": source["blob_sha256"],
                "byte_length": source["byte_length"],
                "dictionary": source.get("dictionary", {}),
                "components": components,
            }
            store.write_visual_manifest(source_identity, manifest)
            asset["visual_asset_source_version"] = "v1"
            asset["visual_asset_source"] = {
                "match_status": status,
                "source_identity_sha256": source_identity,
                "blob_sha256": source["blob_sha256"],
                "byte_length": source["byte_length"],
                "source_manifest_ref": source_identity,
                "source_object_ref": source.get("source_object_ref"),
                "paint_instance_ref": source.get("paint_instance_ref"),
                "paint_matrix": source.get("paint_matrix"),
            }

def _compact_visual_assets_for_storage(assets: Any) -> Any:
    if not isinstance(assets, list):
        return assets
    compacted = []
    for asset in assets:
        if not isinstance(asset, dict):
            compacted.append(asset); continue
        item = dict(asset)
        source = item.get("visual_asset_source")
        if isinstance(source, dict):
            source = {key: value for key, value in source.items() if key != "raw_bytes_base64"}
            if isinstance(source.get("components"), list):
                source["components"] = [{key: value for key, value in component.items() if key != "raw_bytes_base64"} if isinstance(component, dict) else component for component in source["components"]]
            item["visual_asset_source"] = source
        compacted.append(item)
    return compacted

def _page_class(item: dict[str, Any]) -> str:
    """Return final coarse page classification while extraction state is in memory."""
    existing = item.get("page_class")
    valid_classes = {"NATIVE_VALID", "CORRUPTED_TEXT_LAYER", "TEXTUAL_VISUAL", "VISUAL_ASSET", "BLANK_PAGE", "BLANK_BODY", "MISSING_FOLIO"}
    if existing in valid_classes:
        return existing
    quality = str(item.get("quality") or "OK").upper()
    if quality in {"OCR", "NEED_OCR", "CORRUPTED_TEXT_LAYER"}:
        return "CORRUPTED_TEXT_LAYER"
    structure = item.get("structure") if isinstance(item.get("structure"), dict) else {}
    page_category = structure.get("page_category")
    if page_category in valid_classes:
        return page_category
    content = str(item.get("content_markdown") or item.get("text") or "")
    visual_comment = content.startswith("<!-- visual-asset:") or content.startswith("*[Página digitalizada") or content == "[Página digitalizada / Anexo visual]"
    has_visual = bool(structure.get("has_images") or structure.get("visual_assets") or structure.get("visual_items"))
    has_structural_text = bool(structure.get("lines") or structure.get("blocks") or any(
        isinstance(region, dict) and str(region.get("text") or "").strip()
        for region in structure.get("regions", [])
    ))
    if quality == "VISUAL_ASSET" or visual_comment or (has_visual and (not has_structural_text or quality in {"SCANNED", "EMPTY"})):
        return "VISUAL_ASSET"
    return "NATIVE_VALID"


def _page_folios(pages: list[dict[str, Any]], process_id: str) -> dict[int, int | None]:
    """Resolve folios during ingestion, before intermediate structures are discarded."""
    from core.documentos.folio_resolver import FolioResolver, PageFolioInput

    inputs = []
    existing_folios: dict[int, int | None] = {}
    for item in pages:
        if item.get("process_folio") is not None:
            try:
                existing_folios[int(item["page"])] = int(item["process_folio"])
            except (TypeError, ValueError):
                pass
        structure = item.get("structure") if isinstance(item.get("structure"), dict) else {}
        parts = [
            entry.get("text", "")
            for section in ("lines", "furniture")
            for entry in structure.get(section, [])
            if isinstance(entry, dict) and entry.get("text")
        ]
        inputs.append(PageFolioInput(
            pdf_page=int(item["page"]),
            text="\n".join(parts) if parts else str(item.get("content_markdown") or item.get("text") or ""),
            process_id=process_id,
        ))
    result = FolioResolver(target_process_id=process_id).resolve(inputs)
    return {page.pdf_page: existing_folios.get(page.pdf_page, page.process_folio) for page in result.pages}


def _compact_page_record(item: dict[str, Any], *, process_folio: int | None = None) -> dict[str, Any]:
    """Serialize only product-facing page text and compact final metadata."""
    return {
        "page": int(item["page"]),
        "content_id": item.get("content_id"),
        "engine": item.get("engine", "pdfium"),
        "quality": item.get("quality", "OK"),
        "fallback_used": bool(item.get("fallback_used", False)),
        "content_markdown": item.get("content_markdown", item.get("text", item.get("content", ""))),
        "process_folio": process_folio if process_folio is not None else item.get("process_folio"),
        "page_class": _page_class(item),
    }

def index_document(db: sqlite3.Connection, manifest: dict[str, Any], pages: list[dict[str, Any]]) -> None:
    did=manifest["document_id"]; process_id=manifest.get("process_id") or "unresolved"; _ensure_process(db,process_id); path=manifest.get("canonical_source_path") or (manifest.get("known_paths") or [""])[0]; stamp=manifest.get("ingested_at",now())
    db.execute("INSERT OR REPLACE INTO files VALUES(?,?,?,?,?)", ("file_"+did,path,manifest.get("sha256",did),manifest.get("size_bytes",0),stamp))
    db.execute("INSERT OR REPLACE INTO documents VALUES(?,?,?,?,?,?,?)", (did,process_id,"file_"+did,"PDF",manifest.get("status","complete"),len(pages),stamp))
    sid="snapshot_"+did; db.execute("INSERT OR IGNORE INTO docket_snapshots VALUES(?,?,?,?)",(sid,process_id,stamp,"CURRENT")); db.execute("INSERT OR REPLACE INTO docket_documents VALUES(?,?,?,?)",("docket_"+did,sid,did,1))
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='canonical_page_observations'").fetchone():
        db.execute("DELETE FROM canonical_page_equivalences WHERE left_observation_id IN (SELECT canonical_page_observation_id FROM canonical_page_observations WHERE document_id=?) OR right_observation_id IN (SELECT canonical_page_observation_id FROM canonical_page_observations WHERE document_id=?)", (did, did))
        db.execute("DELETE FROM canonical_page_observations WHERE document_id=?", (did,))
    db.execute("DELETE FROM pages_fts WHERE document_id=?",(did,)); db.execute("DELETE FROM evidence WHERE page_id IN (SELECT page_id FROM pages WHERE document_id=?)",(did,)); db.execute("DELETE FROM pages WHERE document_id=?",(did,))
    folios = _page_folios(pages, process_id)
    for item in pages:
        number=item["page"]; content=item.get("content_markdown",item.get("text","")); pid=f"{did}:{number}"; cid=item.get("content_id") or content_id((item.get("structure") or {}).get("logical_text") or content)[0]
        page_class = _page_class(item)
        db.execute("INSERT INTO pages(page_id,document_id,page_number,content,quality,engine,fallback_used,content_id,process_folio,page_class) VALUES(?,?,?,?,?,?,?,?,?,?)",(pid,did,number,content,item.get("quality","OK"),item.get("engine","pdfium"),int(bool(item.get("fallback_used"))),cid,folios.get(number),page_class))
        db.execute("INSERT INTO pages_fts VALUES(?,?,?)",(pid,did,content))
        for ev in page_evidence({"page":number,"content_markdown":content}): db.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?)",("ev_"+uuid.uuid4().hex,pid,ev["field"],ev["value"],ev["context"],ev.get("folio"),ev.get("act_date")))

def ingest(path: Path, extract: Callable[[Path],list[dict[str,Any]]], store: Store, confirmed_process_id: str|None=None, versions: dict[str,str]|None=None, matter_dir: Path|None=None) -> dict[str,Any]:
    del matter_dir; source_path=path; did=sha256_file(source_path); canonical_source=store.materialize_source(source_path,did); pages=[]
    for item in extract(canonical_source):
        content=item.get("content_markdown",item.get("text","")); pages.append({**item,"content_markdown":content,"engine":"pdfium","fallback_used":False,"content_id":content_id((item.get("structure") or {}).get("logical_text") or content)[0]})
    persist_visual_asset_sources(store, pages)
    resolution=resolve_page_one(pages[0]["content_markdown"]) if pages else None; process_id=confirmed_process_id or (resolution["process_id"] if resolution else "unresolved"); status="process_confirmed_explicitly" if confirmed_process_id else ("process_resolved_by_recognizer" if resolution else "process_unresolved"); stamp=now()
    manifest={"format_version":FORMAT_VERSION,"document_id":did,"sha256":did,"size_bytes":canonical_source.stat().st_size,"pages":len(pages),"format":"PDF","known_paths":[str(source_path)],"canonical_source_path":str(canonical_source),"status":status,"ingested_at":stamp,"normalization_version":NORMALIZATION_VERSION,"extractors":versions or {},"process_id":process_id,"process_resolution":resolution,"manifest_path":str(store.manifest_path(did))}
    folios = _page_folios(pages, process_id)
    db=store.connect()
    try:
        db.execute("BEGIN"); index_document(db,manifest,pages); db.commit()
        persisted_pages=[_compact_page_record(item, process_folio=folios.get(int(item["page"]))) for item in pages]
        write_pages(store.pages_path(did),persisted_pages); write_json(store.manifest_path(did),manifest)
    finally: db.close()
    # The Canonical Store owns Page -> canonical_page identity.  Its existing
    # migration/backfill is used before provider artifacts are linked.
    from core.documentos.canonical_store_v1 import migrate as migrate_canonical
    migrate_canonical(store.db_path)
    db=store.connect()
    try:
        from core.documentos.provider_marker_pipeline_v1 import ensure_document_canonical_pages, persist_esaj_provider_artifacts
        db.execute("BEGIN")
        ensure_document_canonical_pages(db, did)
        marker_result = persist_esaj_provider_artifacts(
            db, document_id=did, process_id=process_id,
            page_structures=[{"page": int(item["page"]), **(item.get("structure") or {})} for item in pages if isinstance(item.get("structure"), dict)],
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally: db.close()
    return {"command":"ingest","document_id":did,"process_id":process_id,"pages_indexed":len(pages),"provider_markers":marker_result["markers"],"provider_artifacts":len(marker_result["artifacts"]),"status":"complete","snapshot_id":"snapshot_"+did,"canonical_source_path":str(canonical_source),"read_only_source":True}

def migrate_existing(store: Store) -> dict[str,int]: store.connect().close(); return {"migrated":0,"resolved":0}
def resolve_process(document_id: str, process_id: str, store: Store) -> dict[str,Any]:
    if not CNJ.fullmatch(process_id): raise ValueError("PROCESS_ID deve ser um número CNJ formatado")
    db=store.connect()
    try: _ensure_process(db,process_id); db.execute("UPDATE documents SET process_id=? WHERE document_id=?",(process_id,document_id)); db.commit()
    finally: db.close()
    return {"command":"resolve-process","document_id":document_id,"process_id":process_id}
def forget_document(document_id: str, store: Store) -> dict[str,Any]:
    db=store.connect()
    try: db.execute("DELETE FROM documents WHERE document_id=?",(document_id,)); db.commit()
    finally: db.close()
    target=store.documents/document_id
    if target.exists(): shutil.rmtree(target)
    return {"command":"forget-document","document_id":document_id,"derived_data_removed":True,"original_removed":False}
def add_process_relation(store: Store, from_process: str, to_process: str, relation_kind: str, evidence: str, document_id: str|None=None, page: int|None=None, status: str="CONFIRMED") -> None:
    del document_id,page,status; db=store.connect()
    try: _ensure_process(db,from_process); _ensure_process(db,to_process); db.execute("INSERT INTO process_relations VALUES(?,?,?,?,?,?)",("rel_"+uuid.uuid4().hex,from_process,to_process,relation_kind,evidence,now())); db.commit()
    finally: db.close()
def rebuild(store: Store, cases_root: Path, extract: Callable[[Path],list[dict[str,Any]]], versions: dict[str,str]) -> dict[str,Any]:
    ids=[]
    for process_dir in sorted(p for p in cases_root.rglob("*") if p.is_dir() and CNJ.fullmatch(p.name)):
        for pdf in sorted(process_dir.rglob("*.pdf")): ids.append(ingest(pdf,extract,store,process_dir.name,versions)["document_id"])
    return {"command":"rebuild","documents_ingested":ids}
def refresh_canonical_paths(store: Store, cases_root: Path) -> dict[str,Any]: del store,cases_root; return {"command":"refresh-paths","updated_document_ids":[],"extractors_executed":False}
def search_index(query: str, store: Store, process_id: str|None=None, matter_id: str|None=None) -> dict[str,Any]:
    del matter_id; db=store.connect()
    try:
        rows=db.execute("SELECT p.document_id,d.process_id,p.page_number,p.content,f.path FROM pages p JOIN documents d USING(document_id) JOIN files f USING(file_id) WHERE instr(lower(p.content),lower(?))>0 AND (? IS NULL OR d.process_id=?) ORDER BY d.process_id,p.page_number LIMIT ?",(query,process_id,process_id,MAX_RESULTS+1)).fetchall()
        results=[{"document_id":r[0],"process_id":r[1],"page":r[2],"context":compact(r[3],0,min(len(r[3]),len(query))),"path":str(store.source_path(r[0]))} for r in rows[:MAX_RESULTS]]
        return {"command":"search-index","query":query,"process_id":process_id,"results":results,"count":len(results),"truncated":len(rows)>MAX_RESULTS,"source":"persistent_local_index"}
    finally: db.close()

def reprocess_page(
    document_id_or_process_id: str,
    page_number: int,
    *,
    store: Store | None = None,
    pdf_path: Path | str | None = None,
    enable_heron_fallback: bool | None = None,
    update_embedding: bool = True,
    backend: str | None = None,
    vector_db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Reprocessa de forma incremental uma única página de um documento/processo.

    Atualiza atomicamente apenas a página alvo em pages, pages_fts, evidence,
    pages.ndjson e atualiza seu embedding no vector_store sem tocar no restante do documento.
    """
    if store is None:
        try:
            from core.runtime_paths import themis_data_root
            store = Store(themis_data_root())
        except Exception:
            store = Store(Path("."))

    db = store.connect()
    try:
        # 1. Localiza documento e processo
        row = db.execute(
            """SELECT d.document_id, d.process_id, d.page_count, f.path 
               FROM documents d 
               JOIN files f USING(file_id) 
               WHERE d.document_id = ? OR d.process_id = ? 
               ORDER BY (d.document_id = ?) DESC, d.created_at DESC LIMIT 1""",
            (document_id_or_process_id, document_id_or_process_id, document_id_or_process_id),
        ).fetchone()

        if not row and pdf_path:
            p_obj = Path(pdf_path)
            if p_obj.is_file():
                file_sha = sha256_file(p_obj)
                row = db.execute(
                    """SELECT d.document_id, d.process_id, d.page_count, f.path 
                       FROM documents d 
                       JOIN files f USING(file_id) 
                       WHERE d.document_id = ? OR f.sha256 = ? 
                       ORDER BY d.created_at DESC LIMIT 1""",
                    (file_sha, file_sha),
                ).fetchone()

        if not row:
            raise ValueError(f"Documento ou processo '{document_id_or_process_id}' não encontrado no índice.")

        document_id = row["document_id"]
        process_id = row["process_id"]
        recorded_path = row["path"]

        # 2. Localiza arquivo PDF
        canonical_source = store.source_path(document_id)
        source_file = canonical_source if canonical_source.is_file() else (Path(pdf_path) if pdf_path and Path(pdf_path).is_file() else Path(recorded_path))
        if not source_file.is_file():
            raise FileNotFoundError(f"Arquivo PDF não encontrado: {source_file}")

        # 3. Extrai dados brutos e estruturais somente para a página solicitada
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(source_file))
        total_pdf_pages = len(doc)
        if page_number < 1 or page_number > total_pdf_pages:
            doc.close()
            raise ValueError(f"Página {page_number} fora dos limites do documento (1..{total_pdf_pages})")

        page_obj = doc.get_page(page_number - 1)
        tp = page_obj.get_textpage()
        raw_text = tp.get_text_range()
        doc.close()

        raw_page = {
            "page": page_number,
            "text": raw_text,
            "total_chars": len(raw_text),
            "unicode_map_errors": raw_text.count("\ufffd"),
            "unicode_zero_count": 0,
        }

        try:
            from core.readable_markdown import pdfium_structural_pages
        except ImportError:
            from readable_markdown import pdfium_structural_pages

        structural_pages = pdfium_structural_pages(
            source_file,
            {page_number},
            include_visual_asset_sources=True,
            enable_heron_fallback=enable_heron_fallback,
        )
        structure = structural_pages.get(page_number, {})

        try:
            from core.pdf.themis_pdf import quality_metrics, classify_quality
        except ImportError:
            try:
                from themis_pdf import quality_metrics, classify_quality
            except ImportError:
                def quality_metrics(t, sig=None):
                    return {"characters": len(t), "unicode_map_errors": t.count("\ufffd")}
                def classify_quality(m, err=None):
                    return ("OK" if m.get("characters", 0) > 0 else "BAD", [])

        metrics = quality_metrics(raw_page["text"], raw_page)
        quality, reasons = classify_quality(metrics, raw_page.get("error"))
        final_quality = structure.get("quality") if structure.get("quality") in {"SCANNED", "NEED_OCR"} else quality
        content_markdown = structure.get("text", raw_page["text"].strip())
        fallback_status = structure.get("fallback_status")
        fallback_used = bool(fallback_status or ("heron" in str(structure.get("engine_used", "")).lower()))
        engine = structure.get("engine_used", "pdfium")
        cid = content_id((structure or {}).get("logical_text") or content_markdown)[0]

        page_record = {
            "page": page_number,
            "content_markdown": content_markdown,
            "structure": structure,
            "engine": engine,
            "quality": final_quality,
            "fallback_used": fallback_used,
            "fallback_reason": reasons,
            "fallback_status": fallback_status,
            "quality_metrics": metrics,
            "content_id": cid,
        }

        # 4. Materializa assets visuais se houver
        persist_visual_asset_sources(store, [page_record])

        # 5. Atualização atômica no SQLite
        page_id = f"{document_id}:{page_number}"
        page_item = {"page": page_number, "content_markdown": content_markdown, "quality": final_quality, "structure": structure}
        page_class = _page_class(page_item)
        page_folio = _page_folios([page_item], process_id).get(page_number)
        now_stamp = now()

        db.execute("BEGIN")
        try:
            db.execute(
                """INSERT INTO pages(page_id, document_id, page_number, content, quality, engine, fallback_used, content_id, process_folio, page_class)
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(page_id) DO UPDATE SET
                     content=excluded.content,
                     quality=excluded.quality,
                     engine=excluded.engine,
                     fallback_used=excluded.fallback_used,
                     content_id=excluded.content_id,
                     process_folio=coalesce(excluded.process_folio,pages.process_folio),
                     page_class=excluded.page_class""",
                (page_id, document_id, page_number, content_markdown, final_quality, engine, int(fallback_used), cid, page_folio, page_class),
            )
            db.execute("DELETE FROM pages_fts WHERE page_id=?", (page_id,))
            db.execute("INSERT INTO pages_fts(page_id, document_id, content) VALUES(?, ?, ?)", (page_id, document_id, content_markdown))
            db.execute("DELETE FROM evidence WHERE page_id=?", (page_id,))
            for ev in page_evidence({"page": page_number, "content_markdown": content_markdown}):
                db.execute(
                    "INSERT INTO evidence VALUES(?, ?, ?, ?, ?, ?, ?)",
                    ("ev_" + uuid.uuid4().hex, page_id, ev["field"], ev["value"], ev["context"], ev.get("folio"), ev.get("act_date")),
                )
            db.commit()
        except Exception:
            db.rollback()
            raise

        # 6. Atualiza pages.ndjson em disco se existir
        pages_file = store.pages_path(document_id)
        if pages_file.exists():
            try:
                current_pages = read_pages(pages_file)
                stored_item = _compact_page_record({**page_record, "page_class": page_class}, process_folio=page_folio)
                replaced = False
                new_pages = []
                for p in current_pages:
                    if p.get("page") == page_number:
                        new_pages.append(stored_item)
                        replaced = True
                    else:
                        new_pages.append(p)
                if not replaced:
                    new_pages.append(stored_item)
                    new_pages.sort(key=lambda x: x.get("page", 0))
                write_pages(pages_file, new_pages)
            except Exception:
                pass

        # 7. Atualiza embedding vetorial se solicitado
        embedding_updated = False
        if update_embedding and content_markdown.strip():
            try:
                from core.retrieval.ollama_embed import generate_embedding_with_meta
                from core.retrieval.vector_store import VectorStore, EMBEDDING_MODEL_NAME
                from core.runtime_paths import process_db_path

                v_db = Path(vector_db_path) if vector_db_path else process_db_path(process_id, store.root)
                if v_db.parent.exists():
                    v_store = VectorStore(v_db)
                    vec, meta = generate_embedding_with_meta(
                        content_markdown,
                        is_query=False,
                        model=EMBEDDING_MODEL_NAME,
                        backend=backend,
                    )
                    if vec:
                        v_store.save_embedding(
                            page_id=page_id,
                            document_id=document_id,
                            process_id=process_id,
                            page_number=page_number,
                            vector=vec,
                            model=meta.get("model", EMBEDDING_MODEL_NAME),
                            backend=meta.get("backend", "onnx"),
                            model_version=meta.get("model_version", "v1"),
                            quantization=meta.get("quantization", "int8"),
                        )
                        embedding_updated = True
            except Exception:
                embedding_updated = False

        # 8. Atualiza canonical pages / provider artifacts
        try:
            from core.documentos.provider_marker_pipeline_v1 import ensure_document_canonical_pages, persist_esaj_provider_artifacts
            ensure_document_canonical_pages(db, document_id)
            persist_esaj_provider_artifacts(
                db, document_id=document_id, process_id=process_id,
                page_structures=[{"page": page_number, **structure}],
            )
        except Exception:
            pass


        return {
            "command": "reprocess_page",
            "status": "success",
            "document_id": document_id,
            "process_id": process_id,
            "page_number": page_number,
            "page_id": page_id,
            "quality": final_quality,
            "engine": engine,
            "fallback_used": fallback_used,
            "fallback_status": fallback_status,
            "content_id": cid,
            "content_length": len(content_markdown),
            "embedding_updated": embedding_updated,
        }
    finally:
        db.close()


def delete_process(
    store: Store,
    process_id: str,
    confirm_process_id: str,
) -> dict[str, Any]:
    """Exclui nativa e atomicamente um processo, seus registros SQL, índices e arquivos do filesystem.

    Invariantes:
    1. Confirmação explícita obrigatória: confirm_process_id == process_id.
    2. A exclusão exige confirmação explícita do identificador completo.
    3. Nunca apaga dados ou objetos de outros processos.
    4. Exclui transacionalmente todos os registros SQL relacionados no SQLite e tabelas FTS.
    5. Exclui embeddings vetoriais associados ao processo.
    6. Exclui a raiz processos/<CNJ>/ e seus derivados.
    7. Retorna receipt detalhado com contagens e integridade.
    """
    if not process_id or not isinstance(process_id, str):
        raise ValueError("process_id é obrigatório.")
    process_id = process_id.strip()

    if not confirm_process_id or confirm_process_id.strip() != process_id:
        raise ValueError(
            f"Confirmação de CNJ inválida. Para confirmar a exclusão permanente, digite exatamente o CNJ '{process_id}'."
        )

    # A Process Package é uma unidade autocontida. Não executar a antiga
    # varredura de tabelas do store monolítico (canonical_pages etc.) contra
    # process.db: apagar o pacote remove seus fatos, índices e originais locais.
    if store.process_id == process_id:
        from core.runtime_paths import process_package_dir, validate_process_id
        from core.process_storage import workspace_db_path

        cnj = validate_process_id(process_id)
        requested_dir = (store.processes / cnj)
        process_dir = process_package_dir(cnj, store.root)
        processes_root = (store.root / "processos").resolve()
        if requested_dir.is_symlink() or not process_dir.is_relative_to(processes_root):
            raise ValueError("Process Package fora da raiz permitida")

        pre_counts: dict[str, int] = {}
        process_db = process_dir / "process.db"
        integrity = "absent"
        fk_errors: list[dict[str, Any]] = []
        if process_db.is_file():
            audit_db = sqlite3.connect(process_db)
            audit_db.row_factory = sqlite3.Row
            try:
                integrity = str(audit_db.execute("PRAGMA integrity_check").fetchone()[0])
                fk_errors = [dict(row) for row in audit_db.execute("PRAGMA foreign_key_check")]
                tables = [str(row[0]) for row in audit_db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )]
                for table in tables:
                    safe_table = table.replace('"', '""')
                    try:
                        pre_counts[table] = int(audit_db.execute(f'SELECT COUNT(*) FROM "{safe_table}"').fetchone()[0])
                    except sqlite3.Error:
                        pre_counts[table] = -1
            finally:
                audit_db.close()

        workspace_path = workspace_db_path(store.root)
        tombstones = list(processes_root.glob(f".themis-delete-{cnj}-*"))
        for tombstone in tombstones:
            if tombstone.is_symlink() or not tombstone.is_dir() or not tombstone.resolve().is_relative_to(processes_root):
                raise ValueError("Diretório de remoção fora da raiz permitida")
        moved = False
        if process_dir.exists():
            tombstone = processes_root / f".themis-delete-{cnj}-{uuid.uuid4().hex}"
            rename_attempts = 20
            for attempt in range(rename_attempts):
                try:
                    process_dir.rename(tombstone)
                    break
                except OSError as exc:
                    transient_windows_lock = getattr(exc, "winerror", None) in {5, 32}
                    if not isinstance(exc, PermissionError) and not transient_windows_lock:
                        raise
                    if attempt + 1 >= rename_attempts:
                        raise
                    time.sleep(0.1)
            tombstones.append(tombstone)
            moved = True

        files_removed = 0
        bytes_freed = 0
        for tombstone in tombstones:
            for item in tombstone.rglob("*"):
                if item.is_file():
                    files_removed += 1
                    try:
                        bytes_freed += item.stat().st_size
                    except OSError:
                        pass
            # Keep a failed purge quarantined and retryable; never restore a
            # partially removed package under its canonical CNJ directory.
            shutil.rmtree(tombstone)

        from core.process_storage import remove_discovery
        discovery_deleted = remove_discovery(cnj, root=store.root)

        workspace_deleted = 0
        if workspace_path.is_file():
            workspace = sqlite3.connect(workspace_path)
            try:
                has_table = workspace.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='chat_context_bindings'"
                ).fetchone()
                if has_table:
                    cursor = workspace.execute(
                        "DELETE FROM chat_context_bindings WHERE owner_type='PROCESS' AND owner_id=?", (cnj,)
                    )
                    workspace_deleted = max(0, cursor.rowcount)
                workspace.commit()
            except Exception:
                workspace.rollback()
                raise
            finally:
                workspace.close()

        return {
            "status": "success",
            "operation": "delete_process",
            "process_id": cnj,
            "deleted_at": now(),
            "storage": "process_package",
            "sql_records_deleted": {"package_rows": sum(max(0, count) for count in pre_counts.values()),
                                    "catalog_process_discovery": discovery_deleted,
                                    "workspace_chat_context_bindings": workspace_deleted},
            "package_table_rows_before_delete": pre_counts,
            "filesystem_deleted": {"process_directory": str(process_dir),
                                   "directory_existed": moved or bool(tombstones),
                                   "files_removed_count": files_removed,
                                   "bytes_freed": bytes_freed},
            "integrity_before_delete": {"foreign_key_errors": fk_errors, "integrity_check": integrity},
            "shared_legal_entities_preserved": True,
        }

    db = store.connect()
    sql_deleted: dict[str, int] = {}

    # Coleta IDs de documentos e arquivos antes da exclusão
    doc_rows = db.execute("SELECT document_id, file_id FROM documents WHERE process_id=?", (process_id,)).fetchall()
    doc_ids = [r["document_id"] for r in doc_rows]
    file_ids = [r["file_id"] for r in doc_rows]

    def _delete_where(table: str, condition: str, params: tuple) -> int:
        exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
        if not exists:
            return 0
        cur = db.execute(f"DELETE FROM {table} WHERE {condition}", params)
        count = cur.rowcount if cur.rowcount >= 0 else 0
        if count > 0:
            sql_deleted[table] = sql_deleted.get(table, 0) + count
        return count

    try:
        db.execute("BEGIN TRANSACTION")

        # 1. Limpeza de páginas, FTS e metadados de páginas para cada documento
        for doc_id in doc_ids:
            _delete_where("pages_fts", "document_id=?", (doc_id,))
            _delete_where(
                "canonical_page_equivalences",
                "left_observation_id IN (SELECT canonical_page_observation_id FROM canonical_page_observations WHERE document_id=?) OR right_observation_id IN (SELECT canonical_page_observation_id FROM canonical_page_observations WHERE document_id=?)",
                (doc_id, doc_id),
            )
            _delete_where("canonical_page_observations", "document_id=?", (doc_id,))
            _delete_where("party_evidence", "document_id=?", (doc_id,))
            _delete_where("chronology_evidence", "document_id=?", (doc_id,))
            _delete_where("autos_page_sources", "document_id=?", (doc_id,))
            _delete_where("autos_page_memberships", "document_id=?", (doc_id,))
            _delete_where("evidence", "page_id IN (SELECT page_id FROM pages WHERE document_id=?)", (doc_id,))
            _delete_where("docket_documents", "document_id=?", (doc_id,))
            _delete_where("pages", "document_id=?", (doc_id,))

        # 2. Documentos e arquivos não compartilhados
        _delete_where("docket_snapshots", "process_id=?", (process_id,))

        # 3. Composições de autos e fontes de páginas
        _delete_where(
            "autos_page_sources",
            "membership_id IN (SELECT membership_id FROM autos_page_memberships WHERE composition_id IN (SELECT composition_id FROM autos_compositions WHERE process_id=?)) OR canonical_page_id IN (SELECT canonical_page_id FROM canonical_pages WHERE process_id=?)",
            (process_id, process_id),
        )
        _delete_where(
            "autos_page_memberships",
            "composition_id IN (SELECT composition_id FROM autos_compositions WHERE process_id=?) OR canonical_page_id IN (SELECT canonical_page_id FROM canonical_pages WHERE process_id=?)",
            (process_id, process_id),
        )
        _delete_where("autos_compositions", "process_id=?", (process_id,))

        # 4. Canonical page equivalences e observations
        _delete_where(
            "canonical_page_equivalences",
            "left_observation_id IN (SELECT canonical_page_observation_id FROM canonical_page_observations WHERE canonical_page_id IN (SELECT canonical_page_id FROM canonical_pages WHERE process_id=?)) OR right_observation_id IN (SELECT canonical_page_observation_id FROM canonical_page_observations WHERE canonical_page_id IN (SELECT canonical_page_id FROM canonical_pages WHERE process_id=?))",
            (process_id, process_id),
        )
        _delete_where(
            "canonical_page_observations",
            "canonical_page_id IN (SELECT canonical_page_id FROM canonical_pages WHERE process_id=?)",
            (process_id,),
        )

        # 5. Provider artifacts e páginas
        _delete_where(
            "provider_artifact_pages",
            "provider_artifact_id IN (SELECT provider_artifact_id FROM provider_artifacts WHERE process_id=?) OR canonical_page_id IN (SELECT canonical_page_id FROM canonical_pages WHERE process_id=?)",
            (process_id, process_id),
        )
        _delete_where("provider_artifacts", "process_id=?", (process_id,))

        # 6. Logical documents e referências
        _delete_where(
            "logical_document_pages",
            "logical_document_id IN (SELECT logical_document_id FROM logical_documents WHERE process_id=?) OR canonical_page_id IN (SELECT canonical_page_id FROM canonical_pages WHERE process_id=?)",
            (process_id, process_id),
        )
        _delete_where(
            "internal_references",
            "target_process_id=? OR source_logical_document_id IN (SELECT logical_document_id FROM logical_documents WHERE process_id=?)",
            (process_id, process_id),
        )
        _delete_where(
            "source_refs",
            "start_canonical_page_id IN (SELECT canonical_page_id FROM canonical_pages WHERE process_id=?) OR end_canonical_page_id IN (SELECT canonical_page_id FROM canonical_pages WHERE process_id=?)",
            (process_id, process_id),
        )
        _delete_where(
            "derived_content",
            "process_id=? OR (owner_type='PROCESS' AND owner_id=?)",
            (process_id, process_id),
        )
        _delete_where("logical_documents", "process_id=?", (process_id,))

        # 7. Canonical pages
        _delete_where("canonical_pages", "process_id=?", (process_id,))

        # 8. Documentos e arquivos
        _delete_where("documents", "process_id=?", (process_id,))
        for fid in file_ids:
            other_ref = db.execute("SELECT 1 FROM documents WHERE file_id=?", (fid,)).fetchone()
            if not other_ref:
                _delete_where("files", "file_id=?", (fid,))

        # 9. Audiências e participantes
        _delete_where(
            "hearing_participants",
            "hearing_id IN (SELECT hearing_id FROM hearings WHERE process_id=?)",
            (process_id,),
        )
        _delete_where("hearings", "process_id=?", (process_id,))

        # 10. Partes e evidências de partes
        _delete_where(
            "party_evidence",
            "party_relation_id IN (SELECT party_relation_id FROM party_relations WHERE (owner_type='PROCESS' AND owner_id=?) OR owner_id=?)",
            (process_id, process_id),
        )

        # 10.1. Contexto local, representações e participantes do processo
        # ProfessionalProfile é local ao produto e permanece após a exclusão
        # de um processo; somente os vínculos processuais são removidos.
        _delete_where("user_process_contexts", "process_id=?", (process_id,))
        _delete_where("representations", "process_id=?", (process_id,))
        _delete_where("process_participants", "process_id=?", (process_id,))
        _delete_where(
            "party_relations",
            "(owner_type='PROCESS' AND owner_id=?) OR owner_id=?",
            (process_id, process_id),
        )

        # 11. Cronologia e eventos
        _delete_where(
            "chronology_evidence",
            "chronology_event_id IN (SELECT chronology_event_id FROM chronology_events WHERE (owner_type='PROCESS' AND owner_id=?) OR owner_id=?)",
            (process_id, process_id),
        )
        _delete_where(
            "chronology_events",
            "(owner_type='PROCESS' AND owner_id=?) OR owner_id=?",
            (process_id, process_id),
        )

        # 12. Prazos, estratégias, pendências
        _delete_where("deadlines", "(owner_type='PROCESS' AND owner_id=?) OR owner_id=?", (process_id, process_id))
        _delete_where("strategy_entries", "(owner_type='PROCESS' AND owner_id=?) OR owner_id=?", (process_id, process_id))
        _delete_where("pending_items", "(owner_type='PROCESS' AND owner_id=?) OR owner_id=?", (process_id, process_id))

        # 13. Extrações e publicações
        _delete_where("domain_extraction_runs", "(owner_type='PROCESS' AND owner_id=?) OR owner_id=?", (process_id, process_id))
        _delete_where("extraction_runs", "(owner_type='PROCESS' AND owner_id=?) OR owner_id=?", (process_id, process_id))
        _delete_where("publications", "process_id=?", (process_id,))
        _delete_where("process_metadata", "process_id=?", (process_id,))

        # 13.1. Read models derivados do ciclo temporal/IA e Movements.
        _delete_where("case_syntheses", "process_id=?", (process_id,))
        _delete_where("process_events", "process_id=?", (process_id,))
        _delete_where("deadline_obligations", "process_id=?", (process_id,))
        _delete_where("deadline_instructions", "process_id=?", (process_id,))
        _delete_where("procedural_act_movement_backfill_v1", "process_id=?", (process_id,))
        _delete_where(
            "movement_summaries",
            "movement_id IN (SELECT movement_id FROM movements WHERE process_id=?)",
            (process_id,),
        )
        _delete_where(
            "movement_pieces",
            "movement_id IN (SELECT movement_id FROM movements WHERE process_id=?)",
            (process_id,),
        )
        _delete_where("movements", "process_id=?", (process_id,))

        # 14. Snapshots, movimentações, fontes e vínculos
        _delete_where("process_movements", "process_id=?", (process_id,))
        _delete_where("process_sources", "process_id=?", (process_id,))
        _delete_where("process_relations", "from_process_id=? OR to_process_id=?", (process_id, process_id))
        _delete_where("chat_context_bindings", "owner_type='PROCESS' AND owner_id=?", (process_id,))

        # 15. Registro principal do processo
        _delete_where("processes", "process_id=?", (process_id,))

        # 16. Limpeza de entidades jurídicas órfãs
        has_pr = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='party_relations'").fetchone()
        has_le = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='legal_entities'").fetchone()
        if has_pr and has_le:
            orphaned = db.execute(
                "DELETE FROM legal_entities WHERE entity_id NOT IN (SELECT DISTINCT entity_id FROM party_relations) AND entity_id NOT IN (SELECT DISTINCT entity_id FROM process_participants)"
            ).rowcount
            if orphaned and orphaned > 0:
                sql_deleted["legal_entities_orphaned"] = orphaned

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        fk_errors = db.execute("PRAGMA foreign_key_check").fetchall()
        fk_list = [dict(row) for row in fk_errors] if fk_errors else []
        integ_check = db.execute("PRAGMA integrity_check").fetchone()[0]
        db.close()

    # 10. Limpeza no banco vetorial se existir
    vector_records_deleted = 0
    try:
        from core.retrieval.vector_store import VectorStore
        from core.runtime_paths import process_db_path
        vec_path = process_db_path(process_id, store.root)
        if vec_path.exists():
            v_store = VectorStore(vec_path)
            conn_vec = v_store.connect()
            try:
                c1 = conn_vec.execute("DELETE FROM page_embeddings WHERE process_id=?", (process_id,)).rowcount
                c2 = conn_vec.execute("DELETE FROM vector_index_metadata WHERE process_id=?", (process_id,)).rowcount
                conn_vec.commit()
                vector_records_deleted = (c1 or 0) + (c2 or 0)
                if vector_records_deleted > 0:
                    sql_deleted["vector_embeddings"] = vector_records_deleted
            finally:
                conn_vec.close()
    except Exception:
        pass

    # 11. Exclusão no Filesystem da raiz processos/<CNJ>/
    process_dir = store.process_path(process_id)
    files_removed = 0
    bytes_freed = 0
    dir_existed = process_dir.exists()

    if dir_existed:
        for f in process_dir.rglob("*"):
            if f.is_file():
                files_removed += 1
                try:
                    bytes_freed += f.stat().st_size
                except Exception:
                    pass
        shutil.rmtree(process_dir, ignore_errors=True)

    # Old shared document directories are cleaned only by the legacy store;
    # a package operation must never remove content that another package may use.
    if not store.process_id:
        for doc_id in doc_ids:
            doc_dir = store.documents / doc_id
            if doc_dir.exists():
                for f in doc_dir.rglob("*"):
                    if f.is_file():
                        files_removed += 1
                        try:
                            bytes_freed += f.stat().st_size
                        except Exception:
                            pass
                shutil.rmtree(doc_dir, ignore_errors=True)

    receipt = {
        "status": "success",
        "operation": "delete_process",
        "process_id": process_id,
        "deleted_at": now(),
        "sql_records_deleted": sql_deleted,
        "total_sql_records_deleted": sum(sql_deleted.values()),
        "filesystem_deleted": {
            "process_directory": str(process_dir),
            "directory_existed": dir_existed,
            "files_removed_count": files_removed,
            "bytes_freed": bytes_freed,
        },
        "integrity": {
            "foreign_key_errors": fk_list,
            "integrity_check": integ_check,
        },
    }
    return receipt
