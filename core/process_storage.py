"""Process Package database routing and the deliberately small global catalog."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from core.runtime_paths import (
    catalog_db_path,
    process_db_path,
    process_package_dir,
    themis_data_root,
    validate_process_id,
    workspace_db_path,
)

CATALOG_SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS process_discovery (
  process_id TEXT PRIMARY KEY,
  tribunal TEXT,
  provider TEXT,
  external_id TEXT,
  discovery_status TEXT NOT NULL DEFAULT 'KNOWN',
  access_status TEXT,
  package_rel_path TEXT NOT NULL,
  first_seen_at TEXT,
  last_seen_at TEXT,
  last_sync_at TEXT
);
CREATE TABLE IF NOT EXISTS provider_artifact_identity (
  provider TEXT NOT NULL,
  external_artifact_id TEXT NOT NULL,
  process_id TEXT NOT NULL,
  PRIMARY KEY(provider, external_artifact_id)
);
"""

WORKSPACE_SCHEMA = """
CREATE TABLE IF NOT EXISTS professional_profiles(
  profile_id TEXT PRIMARY KEY, display_name TEXT NOT NULL,
  profile_type TEXT NOT NULL CHECK(profile_type IN ('LAWYER','PARTY','OTHER')),
  oab_number TEXT, oab_uf TEXT, future_identity_ref TEXT,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_context_bindings(
  chat_id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
  owner_type TEXT NOT NULL CHECK(owner_type='PROCESS'),
  owner_id TEXT NOT NULL, created_at TEXT NOT NULL
);
"""


def connect_process(process_id: str, *, root: Path | None = None, create: bool = False) -> sqlite3.Connection:
    target = process_db_path(validate_process_id(process_id), root)
    if not target.is_file() and not create:
        raise FileNotFoundError(f"Process Package ausente: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(target)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def connect_catalog(*, root: Path | None = None, create: bool = False) -> sqlite3.Connection:
    target = catalog_db_path(root)
    if not target.is_file() and not create:
        raise FileNotFoundError(f"Catalog ausente: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(target)
    db.row_factory = sqlite3.Row
    db.executescript(CATALOG_SCHEMA)
    return db


def known_process_ids(*, root: Path | None = None) -> list[str]:
    target = catalog_db_path(root)
    if not target.is_file():
        return sorted(p.name for p in (root or themis_data_root()).joinpath("processos").iterdir() if p.is_dir()) if (root or themis_data_root()).joinpath("processos").is_dir() else []
    db = connect_catalog(root=root)
    try:
        return [str(row[0]) for row in db.execute("SELECT process_id FROM process_discovery ORDER BY process_id")]
    finally:
        db.close()


def connect_workspace(*, root: Path | None = None, create: bool = False) -> sqlite3.Connection:
    target = workspace_db_path(root)
    if not target.is_file() and not create:
        raise FileNotFoundError(f"Workspace DB ausente: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(target)
    db.row_factory = sqlite3.Row
    db.executescript(WORKSPACE_SCHEMA)
    return db


def sync_workspace_profiles(process_db: sqlite3.Connection, *, root: Path | None = None) -> int:
    target = workspace_db_path(root)
    if not target.is_file():
        return 0
    global_db = connect_workspace(root=root)
    try:
        rows = global_db.execute("SELECT * FROM professional_profiles").fetchall()
    finally:
        global_db.close()
    if not rows:
        return 0
    process_db.executemany(
        """INSERT INTO professional_profiles(profile_id,display_name,profile_type,oab_number,oab_uf,future_identity_ref,created_at,updated_at)
           VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(profile_id) DO NOTHING""",
        [tuple(row) for row in rows],
    )
    process_db.commit()
    return len(rows)


def locate_process_for_record(table: str, key_column: str, key_value: Any, *, root: Path | None = None) -> str | None:
    """Resolve an opaque process-owned record ID without putting it in catalog.db."""
    if not table.replace("_", "").isalnum() or not key_column.replace("_", "").isalnum():
        raise ValueError("identificadores SQL inválidos")
    for process_id in known_process_ids(root=root):
        path = process_db_path(process_id, root)
        if not path.is_file():
            continue
        db = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        try:
            exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
            if exists and db.execute(f'SELECT 1 FROM "{table}" WHERE "{key_column}"=? LIMIT 1', (key_value,)).fetchone():
                return process_id
        except sqlite3.Error:
            continue
        finally:
            db.close()
    return None


def register_discovery(process_id: str, *, root: Path | None = None, provider: str | None = None, tribunal: str | None = None, external_id: str | None = None, discovery_status: str = "KNOWN", access_status: str | None = None, observed_at: str | None = None) -> None:
    cnj = validate_process_id(process_id)
    db = connect_catalog(root=root, create=True)
    try:
        db.execute(
            """INSERT INTO process_discovery(process_id,tribunal,provider,external_id,discovery_status,access_status,package_rel_path,first_seen_at,last_seen_at,last_sync_at)
               VALUES(?,?,?,?,?,?,?,COALESCE(?,CURRENT_TIMESTAMP),COALESCE(?,CURRENT_TIMESTAMP),?)
               ON CONFLICT(process_id) DO UPDATE SET tribunal=COALESCE(excluded.tribunal,tribunal),provider=COALESCE(excluded.provider,provider),external_id=COALESCE(excluded.external_id,external_id),discovery_status=excluded.discovery_status,access_status=COALESCE(excluded.access_status,access_status),last_seen_at=COALESCE(excluded.last_seen_at,CURRENT_TIMESTAMP),last_sync_at=COALESCE(excluded.last_sync_at,last_sync_at)""",
            (cnj, tribunal, provider, external_id, discovery_status, access_status, f"processos/{cnj}", observed_at, observed_at, observed_at),
        )
        db.commit()
    finally:
        db.close()


def remove_discovery(process_id: str, *, root: Path | None = None) -> int:
    """Remove somente o ponteiro global do pacote; conteúdo do processo é local."""
    target = catalog_db_path(root)
    if not target.is_file():
        return 0
    db = sqlite3.connect(target)
    try:
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='process_discovery'"
        ).fetchone()
        if not exists:
            return 0
        cnj = validate_process_id(process_id)
        db.execute("BEGIN")
        cur = db.execute("DELETE FROM process_discovery WHERE process_id=?", (cnj,))
        has_identity = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='provider_artifact_identity'"
        ).fetchone()
        if has_identity:
            db.execute("DELETE FROM provider_artifact_identity WHERE process_id=?", (cnj,))
        db.commit()
        return max(0, cur.rowcount)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def provider_artifact_owner(provider: str, external_artifact_id: str, *, root: Path | None = None) -> str | None:
    """Resolve an opaque provider ID to its owning process without storing content globally."""
    artifact_id = str(external_artifact_id or "").strip()
    if not provider or not artifact_id:
        return None
    target = catalog_db_path(root)
    if not target.is_file():
        rebuild_provider_artifact_identity_index(root=root)
    db: sqlite3.Connection | None = connect_catalog(root=root)
    try:
        has_rows = db.execute("SELECT 1 FROM provider_artifact_identity LIMIT 1").fetchone()
        if not has_rows:
            # First use after upgrading an existing installation: rebuild the
            # small identity index from package-local provider_artifacts.
            db.close()
            db = None
            rebuild_provider_artifact_identity_index(root=root)
            db = connect_catalog(root=root)
        row = db.execute(
            "SELECT process_id FROM provider_artifact_identity WHERE provider=? AND external_artifact_id=?",
            (provider, artifact_id),
        ).fetchone()
        return str(row[0]) if row else None
    finally:
        if db is not None:
            db.close()


def claim_provider_artifact_identity(
    provider: str, external_artifact_id: str, process_id: str, *, root: Path | None = None,
) -> None:
    """Index provider identity only; source bytes and artifact metadata stay in process.db."""
    cnj = validate_process_id(process_id)
    artifact_id = str(external_artifact_id or "").strip()
    if not provider or not artifact_id:
        return
    db = connect_catalog(root=root, create=True)
    try:
        db.execute("BEGIN")
        row = db.execute(
            "SELECT process_id FROM provider_artifact_identity WHERE provider=? AND external_artifact_id=?",
            (provider, artifact_id),
        ).fetchone()
        if row and str(row[0]) != cnj:
            raise ValueError(
                f"INVARIANT_VIOLATION: {provider} artifact '{artifact_id}' já pertence ao processo '{row[0]}', não a '{cnj}'."
            )
        if row:
            db.commit()
            return
        db.execute(
            """INSERT INTO provider_artifact_identity(provider,external_artifact_id,process_id)
               VALUES(?,?,?) ON CONFLICT(provider,external_artifact_id) DO UPDATE SET process_id=excluded.process_id""",
            (provider, artifact_id, cnj),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def claim_provider_artifact_identities(
    provider: str, external_artifact_ids: list[str], process_id: str, *, root: Path | None = None,
) -> int:
    """Claim a captured inventory in one catalog transaction."""
    cnj = validate_process_id(process_id)
    ids = sorted({str(value or "").strip() for value in external_artifact_ids if str(value or "").strip()})
    if not provider or not ids:
        return 0
    db = connect_catalog(root=root, create=True)
    try:
        db.execute("BEGIN")
        for artifact_id in ids:
            row = db.execute(
                "SELECT process_id FROM provider_artifact_identity WHERE provider=? AND external_artifact_id=?",
                (provider, artifact_id),
            ).fetchone()
            if row and str(row[0]) != cnj:
                raise ValueError(
                    f"INVARIANT_VIOLATION: {provider} artifact '{artifact_id}' já pertence ao processo '{row[0]}', não a '{cnj}'."
                )
            if row:
                continue
            db.execute(
                """INSERT INTO provider_artifact_identity(provider,external_artifact_id,process_id)
                   VALUES(?,?,?) ON CONFLICT(provider,external_artifact_id) DO UPDATE SET process_id=excluded.process_id""",
                (provider, artifact_id, cnj),
            )
        db.commit()
        return len(ids)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def rebuild_provider_artifact_identity_index(*, root: Path | None = None) -> int:
    """Backfill opaque provider-ID ownership from existing packages; never copies artifact content."""
    identities: dict[tuple[str, str], str] = {}
    for process_id in known_process_ids(root=root):
        path = process_db_path(process_id, root)
        if not path.is_file():
            continue
        source = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        try:
            table = source.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='provider_artifacts'"
            ).fetchone()
            if not table:
                continue
            rows = source.execute(
                "SELECT source_origin,source_artifact_id FROM provider_artifacts "
                "WHERE source_origin IS NOT NULL AND source_artifact_id IS NOT NULL"
            ).fetchall()
        finally:
            source.close()
        for provider, artifact_id in rows:
            key = (str(provider), str(artifact_id))
            prior = identities.get(key)
            if prior and prior != process_id:
                raise ValueError(
                    f"INVARIANT_VIOLATION: {key[0]} artifact '{key[1]}' aparece em '{prior}' e '{process_id}'."
                )
            identities[key] = process_id

        # The provider snapshot may know a document identity before its PDF
        # has been downloaded and materialized in provider_artifacts.
        snapshot_path = process_package_dir(process_id, root) / "source_snapshot.json"
        if snapshot_path.is_file():
            try:
                snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(f"snapshot do pacote ilegível ao reconstruir identidade: {snapshot_path}") from exc
            for document in snapshot.get("documents", []):
                artifact_id = str(document.get("cdDocumento") or "").strip()
                if not artifact_id:
                    continue
                key = ("pastadigital_esaj", artifact_id)
                prior = identities.get(key)
                if prior and prior != process_id:
                    raise ValueError(
                        f"INVARIANT_VIOLATION: {key[0]} artifact '{key[1]}' aparece em '{prior}' e '{process_id}'."
                    )
                identities[key] = process_id

    db = connect_catalog(root=root, create=True)
    try:
        db.execute("BEGIN")
        db.execute("DELETE FROM provider_artifact_identity")
        for (provider, artifact_id), process_id in identities.items():
            db.execute(
                """INSERT INTO provider_artifact_identity(provider,external_artifact_id,process_id)
                   VALUES(?,?,?) ON CONFLICT(provider,external_artifact_id) DO UPDATE SET process_id=excluded.process_id""",
                (provider, artifact_id, process_id),
            )
        db.commit()
        return len(identities)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def provider_artifact_owners(*, root: Path | None = None) -> dict[tuple[str, str], str]:
    """Return the current opaque identity index, backfilling it from packages first."""
    db = connect_catalog(root=root, create=True)
    try:
        has_rows = db.execute("SELECT 1 FROM provider_artifact_identity LIMIT 1").fetchone()
        if not has_rows:
            db.close()
            db = None
            rebuild_provider_artifact_identity_index(root=root)
            db = connect_catalog(root=root, create=True)
        return {
            (str(row[0]), str(row[1])): str(row[2])
            for row in db.execute(
                "SELECT provider,external_artifact_id,process_id FROM provider_artifact_identity"
            )
        }
    finally:
        if db is not None:
            db.close()


def catalog_discovery(process_id: str, *, root: Path | None = None) -> dict[str, Any] | None:
    db = connect_catalog(root=root)
    try:
        row = db.execute("SELECT * FROM process_discovery WHERE process_id=?", (validate_process_id(process_id),)).fetchone()
        return dict(row) if row else None
    finally:
        db.close()
