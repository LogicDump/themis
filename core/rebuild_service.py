"""Isolated, offline reconstruction of one Themis Process Package."""
from __future__ import annotations

import hashlib
import json
from contextlib import closing
import os
import re
import shutil
import sqlite3
import time
import uuid
from pathlib import Path

from core.runtime_paths import validate_process_id

SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_rebuild(root: Path, cnj: str, *, progress=None) -> dict:
    """Read-only preflight, including every original's digest."""
    cnj = validate_process_id(cnj)
    root = Path(root).resolve()
    package = root / "processos" / cnj
    if package.is_symlink() or not package.is_dir():
        raise ValueError(f"Process Package ausente/inválido: {cnj}")
    source = package / "fontes" / "pecas_manifest.json"
    snapshot = package / "source_snapshot.json"
    if not source.is_file() or not snapshot.is_file():
        raise ValueError("Fonte ou snapshot da captura ausente; rebuild offline impossível")
    manifest = json.loads(source.read_text(encoding="utf-8"))
    pieces = manifest.get("pecas") or []
    if not pieces:
        raise ValueError("Inventário sem peças")
    total = 0
    checked = set()
    total_unique = len({str(piece.get("sha256") or "") for piece in pieces})
    if progress is not None:
        progress.update("VALIDATING", 0, total_unique)
    for piece in pieces:
        digest = str(piece.get("sha256") or "")
        if not SHA256.fullmatch(digest):
            raise ValueError("SHA-256 inválido no inventário")
        original = package / "fontes" / "objetos" / f"{digest}.pdf"
        if original.is_symlink() or not original.is_file():
            raise ValueError(f"PDF original ausente: {digest}")
        if digest not in checked:
            if _sha256(original) != digest:
                raise ValueError(f"PDF original corrompido: {digest}")
            total += original.stat().st_size
            checked.add(digest)
            if progress is not None:
                progress.update("VALIDATING", len(checked), total_unique)
    ai_counts = {"movement_summaries": 0, "case_syntheses": 0}
    movements_before = None
    database = package / "process.db"
    if database.is_file():
        with closing(sqlite3.connect("file:" + database.as_posix() + "?mode=ro", uri=True)) as db:
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master")}
            if "movements" in tables:
                movements_before = db.execute("SELECT count(*) FROM movements WHERE process_id=?", (cnj,)).fetchone()[0]
            for table in ai_counts:
                if table in tables:
                    ai_counts[table] = db.execute("SELECT count(*) FROM " + table).fetchone()[0]
    snapshot_data = json.loads(snapshot.read_text(encoding="utf-8"))
    if not snapshot_data.get("documents"):
        raise ValueError("Snapshot sem inventário documental; rebuild não autorizado")
    return {
        "cnj": cnj, "pdfs": len(checked), "pieces": len(pieces),
        "bytes": total, "snapshot_movements": len(snapshot_data.get("movements") or []),
        "snapshot_participants": len(snapshot_data.get("participants") or []),
        "status": "VALIDATED", "ai_derivatives": ai_counts,
        "movements_before": movements_before,
    }


def _copy_sources(source: Path, target: Path) -> None:
    target.mkdir(parents=True)
    for name in ("fontes", "snapshots"):
        original = source / name
        if original.exists():
            if original.is_symlink():
                raise ValueError("Fonte contém link simbólico")
            shutil.copytree(original, target / name, symlinks=False)
    for name in ("manifest.json", "source_snapshot.json", "cpopg_snapshot.json"):
        original = source / name
        if original.is_file():
            shutil.copy2(original, target / name)


def _stage_manifest(stage: Path) -> None:
    path = stage / "fontes" / "pecas_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    for piece in manifest["pecas"]:
        piece["reused_existing"] = False
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
def _retarget_paths(db_path: Path, staged: Path, target: Path) -> None:
    # The existing pipeline persists absolute file paths: rewrite these
    # BEFORE sealing/checksumming the replacement package.
    with closing(sqlite3.connect(db_path)) as db:
        for rowid, value in db.execute("SELECT rowid,path FROM files"):
            if value.startswith(str(staged) + os.sep):
                db.execute("UPDATE files SET path=? WHERE rowid=?",
                           (str(target) + value[len(str(staged)):], rowid))
        db.commit()


def _validate_result(db_path: Path, expected: int, cnj: str, *, require_vectors: bool = False) -> dict:
    with closing(sqlite3.connect(db_path)) as db:
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        foreign = db.execute("PRAGMA foreign_key_check").fetchall()
        documents = db.execute("SELECT count(*) FROM documents WHERE process_id=?", (cnj,)).fetchone()[0]
        pages = db.execute("SELECT count(*) FROM pages").fetchone()[0]
        vector_tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        vectors = db.execute("SELECT count(*) FROM page_embeddings WHERE process_id=? AND model=?", (cnj, "embeddinggemma:300m")).fetchone()[0] if "page_embeddings" in vector_tables else 0
        if require_vectors and vectors != pages:
            raise RuntimeError(f"Embeddings incompletos: {vectors}/{pages}")
        if integrity != "ok" or foreign or documents != expected or pages < expected:
            raise RuntimeError(f"Rebuild inválido: integrity={integrity}, FK={len(foreign)}, docs={documents}/{expected}, pages={pages}")
        movement_count = db.execute("SELECT count(*) FROM movements WHERE process_id=?", (cnj,)).fetchone()[0] if "movements" in vector_tables else None
        return {"documents": documents, "pages": pages, "embeddings": vectors, "movements": movement_count}
def _swap_packages(source: Path, stage: Path, backup: Path) -> None:
    """Probe staged-directory movability before taking the live package offline."""
    probe = stage.with_name(stage.name + ".rename-probe")
    stage.rename(probe)
    try:
        probe.rename(stage)
    except BaseException as exc:
        raise RuntimeError(f"Pacote reconstruído preservado em {probe}; falha ao restaurar nome de staging") from exc

    source.rename(backup)
    try:
        stage.rename(source)
    except BaseException as exc:
        try:
            backup.rename(source)
        except BaseException as rollback_error:
            raise RuntimeError(
                f"FALHA DE ROLLBACK: original em {backup}, reconstruído em {stage}; "
                "não executar novos rebuilds até recuperar o processo"
            ) from rollback_error
        raise RuntimeError(
            f"Falha ao instalar o pacote; original restaurado em {source}; "
            f"reconstruído preservado em {stage}"
        ) from exc


def rebuild_process(root: Path, cnj: str, *, dry_run: bool = False,
                    allow_ai_loss: bool = False, pipeline=None, progress=None) -> dict:
    """Build in quarantine; atomically exchange package after validation."""
    root = Path(root).resolve()
    started = time.perf_counter()
    durations = {}
    audit = audit_rebuild(root, cnj, progress=progress)
    durations["auditoria"] = round(time.perf_counter() - started, 2)
    if dry_run:
        return {**audit, "status": "DRY_RUN", "changed": False}
    if sum(audit["ai_derivatives"].values()) and not allow_ai_loss:
        raise ValueError("O processo contém derivados de IA; use --discard-ai para confirmar seu descarte")
    cnj = audit["cnj"]
    source = root / "processos" / cnj
    token = uuid.uuid4().hex
    stage_root = root / ".rebuild" / token
    stage = stage_root / "processos" / cnj
    backup = root / ".rebuild-backups" / cnj / token
    stage.parent.mkdir(parents=True)
    swapped = False
    swap_attempted = False
    try:
        if progress is not None:
            progress.update("COPYING")
        copied_at = time.perf_counter()
        _copy_sources(source, stage)
        _stage_manifest(stage)
        durations["cópia"] = round(time.perf_counter() - copied_at, 2)
        from core.documentos.themis_documentos import Store
        from core.bridge.sync_service import plan_process_sync, process_captured_sync, _finalize_process_package
        store = Store(stage_root, process_id=cnj)

        snapshot = json.loads((stage / "source_snapshot.json").read_text(encoding="utf-8"))
        cpopg_file = stage / "cpopg_snapshot.json"
        cpopg = json.loads(cpopg_file.read_text(encoding="utf-8")) if cpopg_file.is_file() else None
        from core.documentos.canonical_store_v1 import migrate as migrate_canonical
        with closing(store.connect()):
            pass
        migrate_canonical(store.db_path)
        plan_started = time.perf_counter()
        plan_process_sync(
            store, cnj, metadata=snapshot.get("metadata") or {},
            participants=snapshot.get("participants") or [],
            movements=snapshot.get("movements") or [],
            documents=snapshot.get("documents") or [],
            page_context=snapshot.get("page_context") or {},
            cpopg=cpopg,
        )
        durations["preparação"] = round(time.perf_counter() - plan_started, 2)
        if progress is not None:
            progress.watch(store.process_manifest_path(cnj))
        pipeline_started = time.perf_counter()
        try:
            pipeline_result = (pipeline or process_captured_sync)(store, cnj)
        finally:
            if progress is not None:
                progress.watch(None)
        durations["pipeline"] = round(time.perf_counter() - pipeline_started, 2)
        if progress is not None:
            progress.update("VERIFYING")
        _retarget_paths(stage / "process.db", stage, source)
        for cached in (stage / "derivados" / "documentos").glob("*/manifest.json"):
            text = cached.read_text(encoding="utf-8")
            cached.write_text(text.replace(str(stage) + os.sep, str(source) + os.sep), encoding="utf-8")
        _finalize_process_package(store, cnj)
        result = _validate_result(stage / "process.db", audit["pdfs"], cnj, require_vectors=pipeline is None)
        durations["validação final"] = round(time.perf_counter() - pipeline_started - durations["pipeline"], 2)
        backup.parent.mkdir(parents=True, exist_ok=True)
        if backup.exists():
            raise RuntimeError("Destino de backup já existe")
        if progress is not None:
            progress.update("SWAPPING")
        swap_attempted = True
        _swap_packages(source, stage, backup)
        swapped = True
        durations["total"] = round(time.perf_counter() - started, 2)
        return {**audit, **result, "status": "READY", "changed": True,
                "backup": str(backup), "durations_seconds": durations}
    finally:
        if stage_root.exists() and (swapped or not swap_attempted):
            try:
                shutil.rmtree(stage_root)
            except OSError:
                import logging
                logging.getLogger(__name__).exception("Staging preservado por bloqueio de arquivos: %s", stage_root)
