"""Themis Setup CLI and storage initialization for Hermes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.request import urlopen

# Hermes loads directory plugins under a package namespace (for example
# hermes_plugins.themis) and does not add the plugin root to sys.path.
# Prefer package-relative imports; keep a standalone fallback for local tools.
try:
    from .core.process_storage import connect_catalog
    from .core.runtime_paths import themis_data_root
    from .core.migration_manager import migrate_all
except (ImportError, ValueError):
    _PLUGIN_ROOT = Path(__file__).resolve().parent
    _plugin_root_str = str(_PLUGIN_ROOT)
    if _plugin_root_str not in sys.path:
        sys.path.insert(0, _plugin_root_str)
    from core.process_storage import connect_catalog
    from core.runtime_paths import themis_data_root
    from core.migration_manager import migrate_all


class ThemisSetupError(RuntimeError):
    """Raised when setup or model provisioning fails."""


def _resolve_plugin_data_dir() -> Path:
    """Resolve data root using official Hermes plugin_storage or fallback."""
    try:
        from plugins.plugin_storage import plugin_data_dir
        return Path(plugin_data_dir("themis")).expanduser().resolve()
    except Exception:
        return themis_data_root().resolve()


def _is_valid_asset(path: Path, expected_size: int, expected_sha256: str) -> bool:
    """Check if file exists with matching size and SHA-256."""
    try:
        if path.stat().st_size != expected_size:
            return False
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest().lower() == expected_sha256.lower()
    except OSError:
        return False


def _download_verified_asset(
    url: str,
    target: Path,
    expected_size: int,
    expected_sha256: str,
    log_fn: Callable[[str], None] = print,
) -> None:
    """Download an asset atomically with SHA-256 validation."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    digest = hashlib.sha256()
    byte_count = 0

    log_fn(f"  -> Baixando {target.name} ({expected_size / (1024*1024):.1f} MB)...")
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f"{target.name}.",
            suffix=".part",
            dir=target.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            with urlopen(url, timeout=120) as response:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    byte_count += len(chunk)
                    if byte_count > expected_size:
                        raise ThemisSetupError(
                            f"Tamanho do download excedeu o manifesto para {target.name}: "
                            f"esperado {expected_size}, recebido > {byte_count}"
                        )
                    digest.update(chunk)
                    temp_file.write(chunk)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        actual_sha256 = digest.hexdigest().lower()
        if byte_count != expected_size:
            raise ThemisSetupError(
                f"Tamanho divergente para {target.name}: esperado {expected_size}, obtido {byte_count}"
            )
        if actual_sha256 != expected_sha256.lower():
            raise ThemisSetupError(
                f"Hash SHA-256 divergente para {target.name}: esperado {expected_sha256.lower()}, obtido {actual_sha256}"
            )

        os.replace(temp_path, target)
        temp_path = None
        log_fn(f"  [OK] {target.name} baixado e validado com sucesso.")
    except ThemisSetupError:
        raise
    except Exception as exc:
        raise ThemisSetupError(f"Falha no download de {target.name} a partir de {url}: {exc}") from exc
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def provision_models(
    data_root: Path,
    manifest_file: Path | None = None,
    log_fn: Callable[[str], None] = print,
) -> list[dict[str, Any]]:
    """Download and verify pinned models listed in models_manifest.json."""
    m_path = manifest_file or (Path(__file__).resolve().parent / "models_manifest.json")
    if not m_path.is_file():
        raise ThemisSetupError(f"Manifesto de modelos não encontrado em {m_path}")

    try:
        manifest = json.loads(m_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ThemisSetupError(f"Erro ao ler manifesto de modelos {m_path}: {exc}") from exc

    source = manifest.get("source", {})
    repository = source.get("repository")
    revision = source.get("revision")
    if not repository or not revision:
        raise ThemisSetupError("Manifesto de modelos deve fixar repositório e revisão imutável.")
    immutable_prefix = f"https://huggingface.co/{repository}/resolve/{revision}/"

    results: list[dict[str, Any]] = []
    root = data_root.resolve()

    for item in manifest.get("models", []):
        if item.get("bundled", False):
            continue
        name = item.get("name", "unnamed model")
        url = item.get("url")
        destination = item.get("destination")
        expected_size = item.get("size_bytes")
        expected_sha256 = item.get("sha256")

        if not all((url, destination, expected_sha256)) or not isinstance(expected_size, int):
            raise ThemisSetupError(f"Metadados de download incompletos para {name}.")
        if not str(url).startswith(immutable_prefix):
            raise ThemisSetupError(f"URL do modelo não está fixada em {repository}@{revision}: {url}")

        target = (root / Path(destination)).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise ThemisSetupError(f"Destino do modelo escapa do data root: {destination}") from exc

        if _is_valid_asset(target, expected_size, expected_sha256):
            log_fn(f"  [OK] {target.name} já presente e válido (SHA-256 verificado).")
            status = "already-valid"
        else:
            _download_verified_asset(url, target, expected_size, expected_sha256, log_fn=log_fn)
            status = "downloaded-and-verified"

        results.append({
            "name": name,
            "path": str(target),
            "size_bytes": expected_size,
            "sha256": expected_sha256.lower(),
            "status": status,
        })
    return results


def _setup_native_messaging_host(plugin_root: Path, log_fn: Callable[[str], None] = print) -> bool:
    """Prepare and register Native Messaging Host in Windows Registry for Chrome and Edge."""
    native_dir = plugin_root / "browser-bridge" / "native-host"
    if not native_dir.is_dir():
        log_fn("  [INFO] Pasta native-host não encontrada no pacote; pulando registro.")
        return False

    host_bat = (native_dir / "themis_bridge_host.bat").resolve()
    manifest_file = (native_dir / "themis_browser_bridge.json").resolve()

    manifest_data = {
        "name": "themis_browser_bridge",
        "description": "Themis Browser Bridge Native Messaging Host",
        "path": str(host_bat),
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://ihlmgonioeefmhbgchhalccbimcfngcd/"
        ]
    }
    manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    if sys.platform != "win32":
        log_fn("  [INFO] Native Messaging Host preparado (registro automático suportado no Windows).")
        return True

    try:
        import winreg
        registered_count = 0
        for reg_subpath in [
            r"Software\Google\Chrome\NativeMessagingHosts\themis_browser_bridge",
            r"Software\Microsoft\Edge\NativeMessagingHosts\themis_browser_bridge",
        ]:
            try:
                with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, reg_subpath, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest_file))
                registered_count += 1
            except OSError as reg_err:
                log_fn(f"  [AVISO] Falha ao registrar {reg_subpath}: {reg_err}")

        if registered_count > 0:
            log_fn("  [OK] Native Messaging Host registrado em HKCU (Chrome e Edge).")
            return True
        return False
    except Exception as exc:
        log_fn(f"  [AVISO] Erro ao registrar Native Messaging Host: {exc}")
        return False


def _ensure_windows_plugin_permissions(
    plugin_root: Path,
    log_fn: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Repair/validate the installed plugin ACL on Windows.

    Hermes discovers the backend from <HERMES_HOME>/plugins/themis. A Windows
    clone/publication can occasionally leave that tree unreadable (WinError 5),
    which makes Hermes skip the plugin backend and ctx.rest() return 404.
    Setup normalizes inheritance, grants the current user Modify on the plugin
    tree, then verifies the backend files can actually be read.
    """
    if sys.platform != "win32":
        return {"checked": False, "repaired": False}

    plugin_root = plugin_root.resolve()
    if not plugin_root.is_dir():
        raise ThemisSetupError(f"Diretório do plugin não encontrado: {plugin_root}")

    username = os.environ.get("USERNAME", "").strip()
    domain = os.environ.get("USERDOMAIN", "").strip()
    principal = f"{domain}\\{username}" if domain and username else username
    if not principal:
        raise ThemisSetupError("Não foi possível identificar o usuário atual do Windows para validar as permissões.")

    commands = [
        ["icacls", str(plugin_root), "/inheritance:e", "/T", "/C", "/Q"],
        ["icacls", str(plugin_root), "/grant:r", f"{principal}:(OI)(CI)M", "/T", "/C", "/Q"],
    ]

    changed = False
    for command in commands:
        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise ThemisSetupError(
                f"Falha ao validar/reparar permissões de {plugin_root}: {exc}"
            ) from exc
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise ThemisSetupError(
                "O Windows recusou o ajuste automático das permissões do plugin "
                f"({detail or f'icacls retornou {proc.returncode}'}). "
                "Execute o terminal como Administrador uma única vez e rode novamente "
                "'hermes themis setup'."
            )
        changed = True

    critical_paths = [
        plugin_root / "plugin.yaml",
        plugin_root / "dashboard" / "manifest.json",
        plugin_root / "dashboard" / "plugin_api.py",
        plugin_root / "desktop" / "plugin.js",
    ]
    for path in critical_paths:
        try:
            if not path.is_file():
                raise OSError(f"arquivo ausente: {path}")
            with path.open("rb") as stream:
                stream.read(1)
        except OSError as exc:
            raise ThemisSetupError(
                f"Plugin instalado, mas ainda não está legível após o reparo de ACL: {path} ({exc})"
            ) from exc

    log_fn("  [OK] Permissões do plugin verificadas/reparadas para o usuário atual.")
    return {"checked": True, "repaired": changed, "principal": principal}


def run_themis_setup(
    args: argparse.Namespace | None = None,
    *,
    data_root_override: Path | str | None = None,
    log_fn: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Execute complete, idempotent Themis setup."""
    if data_root_override:
        data_root = Path(data_root_override).expanduser().resolve()
    else:
        data_root = _resolve_plugin_data_dir()

    plugin_root = Path(__file__).resolve().parent

    log_fn(f"[Themis] Inicializando ambiente em: {data_root}")

    # 0. Windows: garantir que o Hermes consiga reler o próprio plugin após a instalação.
    permissions_result = _ensure_windows_plugin_permissions(plugin_root, log_fn=log_fn)

    # 1. Diretórios operacionais essenciais
    for subdir in (
        "config",
        "models",
        "models/embeddinggemma-300m-onnx",
        "processos",
    ):
        (data_root / subdir).mkdir(parents=True, exist_ok=True)

    # 2. Configurações padrão (idempotente - nunca sobrescreve)
    fontes_cfg = data_root / "config" / "fontes.json"
    if not fontes_cfg.is_file():
        default_fontes = {
            "format_version": 1,
            "datajud": {
                "api_key": "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==",
                "timeout_seconds": 35,
            },
        }
        fontes_cfg.write_text(json.dumps(default_fontes, indent=2), encoding="utf-8")
        log_fn("  [OK] config/fontes.json criado com defaults.")
    else:
        log_fn("  [OK] config/fontes.json preservado.")

    bridge_token_cfg = data_root / "config" / "bridge_token.json"
    if not bridge_token_cfg.is_file():
        token_payload = {
            "token": secrets.token_hex(24),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        bridge_token_cfg.write_text(json.dumps(token_payload, indent=2), encoding="utf-8")
        log_fn("  [OK] config/bridge_token.json gerado localmente.")
    else:
        log_fn("  [OK] config/bridge_token.json preservado.")

    # 3. Bancos de dados e esquemas vigentes.
    # O mesmo Migration Manager é usado no bootstrap automático do plugin,
    # portanto setup é bootstrap/recuperação manual, não um caminho paralelo.
    migration_result = migrate_all(root=data_root)
    log_fn(
        "  [OK] schemas verificados/migrados: "
        f"catalog.db, workspace.db e {len(migration_result.get('processes', {}))} Process Package(s)."
    )

    # 4. Native Messaging Host para Browser Bridge
    skip_native = getattr(args, "skip_native_host", False) if args else False
    if not skip_native:
        _setup_native_messaging_host(plugin_root, log_fn=log_fn)
    else:
        log_fn("  [INFO] Registro de Native Messaging ignorado (--skip-native-host).")

    # 5. Provisionamento do EmbeddingGemma ONNX
    skip_models = getattr(args, "skip_models", False) if args else False
    models_result = []
    if not skip_models:
        log_fn("[Themis] Verificando modelos neurais locais...")
        models_result = provision_models(data_root, log_fn=log_fn)
    else:
        log_fn("[Themis] Provisionamento de modelos ignorado (--skip-models).")

    log_fn("[Themis] Setup concluído com sucesso!")
    return {
        "status": "ready",
        "data_root": str(data_root),
        "permissions": permissions_result,
        "migrations": migration_result,
        "models": models_result,
    }




def run_themis_migrate(
    args: argparse.Namespace | None = None,
    *,
    data_root_override: Path | str | None = None,
    log_fn: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Run only schema migrations; no model/native-host provisioning."""
    data_root = (
        Path(data_root_override).expanduser().resolve()
        if data_root_override
        else _resolve_plugin_data_dir()
    )
    log_fn(f"[Themis] Verificando migrations em: {data_root}")
    result = migrate_all(root=data_root)
    changed_processes = sum(
        1 for item in result.get("processes", {}).values() if item.get("changed")
    )
    log_fn(
        "  [OK] migrations concluídas: "
        f"catalog={'alterado' if result['catalog'].get('changed') else 'ok'}, "
        f"workspace={'alterado' if result['workspace'].get('changed') else 'ok'}, "
        f"processos alterados={changed_processes}/{len(result.get('processes', {}))}."
    )
    return {"status": "ready", "data_root": str(data_root), "migrations": result}


def register_cli(subparser: argparse.ArgumentParser) -> None:
    """Build the argparse tree for `hermes themis`."""
    subs = subparser.add_subparsers(dest="themis_subcommand")
    setup_parser = subs.add_parser(
        "setup",
        help="Inicializa persistência, esquemas e modelos do Themis",
        description="Inicializa o plugin-data/themis, catálogo SQLite, Native Messaging Host e modelos ONNX locais.",
    )
    setup_parser.add_argument(
        "--skip-models",
        action="store_true",
        help="Inicializa apenas estrutura de dados e diretórios, pulando o download dos modelos",
    )
    setup_parser.add_argument(
        "--skip-native-host",
        action="store_true",
        help="Pula o registro do Native Messaging Host no registro do Windows",
    )
    setup_parser.set_defaults(func=run_themis_setup)

    migrate_parser = subs.add_parser(
        "migrate",
        help="Aplica migrations pendentes dos bancos do Themis",
        description=(
            "Atualiza schemas de catalog.db, workspace.db e Process Packages "
            "sem provisionar modelos nem alterar o Native Messaging Host."
        ),
    )
    migrate_parser.set_defaults(func=run_themis_migrate)
