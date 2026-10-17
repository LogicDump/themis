"""Provision one Hermes 'themis' agent profile without touching its case data.

No plugin code publication, gateway start, browser registry changes, models or DB work.
The Hermes plugin installer remains the ONLY owner of installed plugin copies.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROFILE = "themis"
PROFILE_SOUL = """# Themis — agente jurídico

Você assiste na investigação de processos judiciais por meio das ferramentas do Themis.
Fundamente fatos em documentos originais e aponte document_id e página/fólio quando disponíveis.
Diferencie alegação, documento, decisão, pedido e fato comprovado.
Não presuma cumprimento de agendamento, deferimento de pedido ou existência de precedente.
Ao faltar evidência, declare a lacuna e solicite verificação.
Não carregue fatos de processos específicos para memória global do perfil.
O processo da sessão deve ser selecionado pelo Themis; não o determine por conjectura.
"""
_SESSION_TOOLSET = "session_search"


class ProfileProvisionError(RuntimeError):
    pass


def _paths() -> tuple[Path, Path]:
    from hermes_constants import get_hermes_home, get_default_hermes_root
    current = get_hermes_home().resolve()
    default = get_default_hermes_root(home=current).resolve()
    if current != default:
        raise ProfileProvisionError(
            "Provisione o perfil pelo ambiente padrão: hermes -p default themis profile setup"
        )
    return default, default / "profiles" / PROFILE


def _plugin_revision(home: Path) -> str | None:
    path = home / "plugins" / ".install-metadata.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ProfileProvisionError(f"Metadados de plugins inválidos: {path}: {exc}") from exc
    entry = data.get("themis") if isinstance(data, dict) else None
    return entry.get("revision") if isinstance(entry, dict) and isinstance(entry.get("revision"), str) else None


def _read_profile_yaml(path: Path):
    from ruamel.yaml import YAML
    parser = YAML(typ="rt")
    parser.preserve_quotes = True
    if not path.is_file():
        return parser, {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            current = parser.load(handle)
    except (OSError, ValueError) as exc:
        raise ProfileProvisionError(f"config.yaml ilegível: {exc}") from exc
    if current is None:
        current = {}
    if not isinstance(current, dict):
        raise ProfileProvisionError("config.yaml não é um objeto YAML")
    return parser, current


def _config_change_needed(path: Path) -> bool:
    _, data = _read_profile_yaml(path)
    agent = data.get("agent", {})
    if not isinstance(agent, dict):
        raise ProfileProvisionError("agent em config.yaml precisa ser um objeto")
    disabled = agent.get("disabled_toolsets", [])
    if not isinstance(disabled, list) or any(not isinstance(item, str) for item in disabled):
        raise ProfileProvisionError("agent.disabled_toolsets precisa ser lista de strings")
    return _SESSION_TOOLSET not in disabled


def _add_session_search_block(config_path: Path) -> None:
    """Modify only the target setting and preserve YAML formatting/comments."""
    import os
    import tempfile

    parser, data = _read_profile_yaml(config_path)
    agent = data.setdefault("agent", {})
    disabled = agent.setdefault("disabled_toolsets", [])
    if _SESSION_TOOLSET in disabled:
        return
    disabled.append(_SESSION_TOOLSET)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=config_path.parent,
            prefix=".themis-config-", suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            parser.dump(data, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, config_path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _soul_action(path: Path) -> str | None:
    if not path.is_file():
        return "write_soul"
    current = path.read_text(encoding="utf-8")
    if current == PROFILE_SOUL:
        return None
    from hermes_cli.default_soul import DEFAULT_SOUL_MD
    if current == DEFAULT_SOUL_MD:
        return "write_soul"
    return "preserve_custom_soul"



def _endpoint_routes(config_path: Path) -> dict[str, str]:
    """Inventory configured named endpoints without exposing or copying credentials.

    Only configuration-backed endpoints need profile-local definitions; built-in
    provider registries and credentials inherited via auth.json are not copied.
    The digest avoids returning endpoint URLs (which can contain secrets).
    """
    from hashlib import sha256

    _, config = _read_profile_yaml(config_path)
    routes: dict[str, str] = {}

    def add(key: object, entry: object) -> None:
        if not isinstance(entry, dict):
            return
        name = str(key or "").strip()
        if not name:
            return
        routing_keys = ("base_url", "baseUrl", "url", "api_base_url", "api")
        if not any(entry.get(field) for field in routing_keys):
            return
        signature = "|".join(str(entry.get(field) or "") for field in routing_keys)
        routes[name] = sha256(signature.encode("utf-8")).hexdigest()

    providers = config.get("providers")
    if isinstance(providers, dict):
        for key, item in providers.items():
            add(key, item)
    customs = config.get("custom_providers")
    if isinstance(customs, list):
        for item in customs:
            if isinstance(item, dict):
                add(item.get("provider_key") or item.get("name"), item)
    return routes


def _provider_coverage(default: Path, profile: Path) -> dict[str, Any]:
    base = _endpoint_routes(default / "config.yaml")
    named = _endpoint_routes(profile / "config.yaml") if profile.exists() else {}
    missing = sorted(set(base) - set(named))
    divergent = sorted(key for key in base.keys() & named.keys()
                       if base[key] != named[key])
    return {
        "configured_endpoints_in_default": sorted(base),
        "missing_in_themis": missing,
        "different_in_themis": divergent,
        "complete": not missing and not divergent,
        "credential_values_copied": False,
        "live_authentication_tested": False,
    }

def inspect_themis_profile() -> dict[str, Any]:
    """Absolutely read-only; no plugin_data_dir(), create_profile() or home mkdir."""
    from hermes_constants import named_profile_has_identity
    default, profile = _paths()
    actions: list[str] = []
    blockers: list[str] = []
    if not (default / "plugins" / "themis" / "plugin.yaml").is_file():
        blockers.append("default_plugin_missing")
    if profile.exists():
        if not named_profile_has_identity(profile):
            blockers.append("profile_without_identity")
        else:
            soul = _soul_action(profile / "SOUL.md")
            if soul:
                actions.append(soul)
            if _config_change_needed(profile / "config.yaml"):
                actions.append("disable_session_search")
    else:
        actions.extend(["create_profile", "write_soul", "disable_session_search"])
    base_revision = _plugin_revision(default)
    prof_revision = _plugin_revision(profile) if profile.exists() else None
    named_installed = (profile / "plugins" / "themis" / "plugin.yaml").is_file()
    if base_revision is not None and prof_revision is not None and base_revision != prof_revision:
        blockers.append("plugin_revisions_differ")
    coverage = _provider_coverage(default, profile)
    return {
        "profile": PROFILE,
        "default_home": str(default),
        "profile_home": str(profile),
        "data_root": str(default / "plugin-data" / "themis"),
        "actions": actions,
        "blockers": blockers,
        "backend": {
            "default_installed": (default / "plugins" / "themis" / "plugin.yaml").is_file(),
            "themis_installed": named_installed,
            "default_revision": base_revision,
            "themis_revision": prof_revision,
            "consistent": base_revision is not None and base_revision == prof_revision,
            "requires_install": not named_installed or prof_revision is None,
        },
        "provider_coverage": coverage,
        "ready_scope": "plugin_revisions_profile_config_and_named_endpoint_definitions_only",
        "ready": (not blockers and not actions and named_installed
                  and base_revision is not None and base_revision == prof_revision
                  and coverage["complete"]),
    }


def setup_themis_profile(*, log_fn=print) -> dict[str, Any]:
    """Idempotently provision the agent profile; NEVER installs/replaces plugin code."""
    from hermes_cli.profiles import create_profile

    status = inspect_themis_profile()
    blockers = status["blockers"]
    if blockers:
        raise ProfileProvisionError(f"Preflight recusado: {', '.join(blockers)}")

    default = Path(status["default_home"])
    profile = Path(status["profile_home"])
    if "create_profile" in status["actions"]:
        created = create_profile(PROFILE, no_skills=True, description="Themis — agente jurídico")
        if created.resolve() != profile.resolve():
            raise ProfileProvisionError(f"Destino inesperado do perfil: {created}")
        log_fn("  [OK] Perfil themis criado pelo Hermes, sem clonagem.")

    action = _soul_action(profile / "SOUL.md")
    if action == "write_soul":
        (profile / "SOUL.md").write_text(PROFILE_SOUL, encoding="utf-8")
        log_fn("  [OK] Orientações jurídicas do perfil configuradas.")
    elif action == "preserve_custom_soul":
        log_fn("  [INFO] SOUL.md personalizado: preservado.")

    config_path = profile / "config.yaml"
    if _config_change_needed(config_path):
        _add_session_search_block(config_path)
        log_fn("  [OK] Busca cruzada de sessões desabilitada no perfil Themis.")
    postflight = inspect_themis_profile()
    if postflight["blockers"] or any(
        item != "preserve_custom_soul" for item in postflight["actions"]
    ):
        raise ProfileProvisionError(f"Postflight incompleto: {postflight}")
    return postflight


def _migration_source(default: Path) -> tuple[str, str]:
    """Use the source and immutable revision already installed in default."""
    path = default / "plugins" / ".install-metadata.json"
    try:
        entry = json.loads(path.read_text(encoding="utf-8-sig"))["themis"]
        source, sha = entry["source"], entry["revision"]
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise ProfileProvisionError("Metadados Git do Themis não disponíveis") from exc
    if not isinstance(sha, str) or len(sha) != 40 or any(
        char not in "0123456789abcdefABCDEF" for char in sha
    ):
        raise ProfileProvisionError("Revisão Git inválida")
    if not isinstance(source, str) or not source.startswith(
        ("https://github.com/", "git@github.com:", "file://")
    ):
        raise ProfileProvisionError("Origem Git inválida")
    return source, sha.lower()


def _save_profile_yaml(path: Path, yaml_parser: Any, config: Any) -> None:
    """Atomically update only the named profile config."""
    import os
    import tempfile
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=".themis-migration-", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            yaml_parser.dump(config, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _copy_missing_providers(default: Path, profile: Path) -> int:
    """Merge endpoint definitions, never overwrite existing named choices."""
    from copy import deepcopy

    _, source = _read_profile_yaml(default / "config.yaml")
    path = profile / "config.yaml"
    parser, target = _read_profile_yaml(path)
    changed = 0
    source_providers = source.get("providers") or {}
    target_providers = target.get("providers") or {}
    if not isinstance(source_providers, dict) or not isinstance(target_providers, dict):
        raise ProfileProvisionError("providers deve ser um mapa YAML")
    for name, entry in source_providers.items():
        if name in target_providers and target_providers[name] != entry:
            raise ProfileProvisionError(f"Provedor '{name}' divergente; não sobrescrever")
        if name not in target_providers:
            target.setdefault("providers", {})[name] = deepcopy(entry)
            changed += 1
    source_custom = source.get("custom_providers") or []
    target_custom = target.get("custom_providers") or []
    if not isinstance(source_custom, list) or not isinstance(target_custom, list):
        raise ProfileProvisionError("custom_providers deve ser lista YAML")
    for entry in source_custom:
        if not isinstance(entry, dict):
            raise ProfileProvisionError("custom_providers contém entrada inválida")
        key = entry.get("provider_key") or entry.get("name")
        if not key:
            raise ProfileProvisionError("custom_providers contém nome vazio")
        existing = [item for item in target_custom
                    if isinstance(item, dict)
                    and (item.get("provider_key") or item.get("name")) == key]
        if any(item != entry for item in existing):
            raise ProfileProvisionError(f"Provedor '{key}' divergente; não sobrescrever")
        if not existing:
            target.setdefault("custom_providers", []).append(deepcopy(entry))
            target_custom = target["custom_providers"]
            changed += 1
    if changed:
        _save_profile_yaml(path, parser, target)
    return changed


def _copy_missing_env(default: Path, profile: Path) -> int:
    """Copy only unset static environment keys; preserve named-profile overrides."""
    import os
    import tempfile

    source, dest = default / ".env", profile / ".env"
    if not source.is_file():
        return 0

    def assignment(line: str) -> str | None:
        text = line.strip()
        if text.startswith("export "):
            text = text[7:].lstrip()
        if not text or text.startswith("#"):
            return None
        name, eq, _ = text.partition("=")
        name = name.strip()
        if not eq or not name or not (name[0].isalpha() or name[0] == "_"):
            return None
        return name if all(ch.isalnum() or ch == "_" for ch in name) else None

    original = dest.read_text(encoding="utf-8-sig") if dest.is_file() else ""
    known = {value for line in original.splitlines() if (value := assignment(line))}
    missing = []
    for line in source.read_text(encoding="utf-8-sig").splitlines():
        name = assignment(line)
        if name in {'HERMES_HOME', 'HERMES_PROFILE', 'API_SERVER_PORT',
                    'THEMIS_DATA_ROOT', 'THEMIS_DB_PATH', 'THEMIS_VECTOR_DB_PATH'}:
            continue
        if name and name not in known:
            missing.append(line)
            known.add(name)
    if not missing:
        return 0
    text = original.rstrip("\r\n") + ("\n" if original.strip() else "") + "\n".join(missing) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=profile,
            prefix=".themis-env-", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, dest)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return len(missing)


def _plugin_enabled(profile: Path) -> bool:
    _, config = _read_profile_yaml(profile / 'config.yaml')
    plugins = config.get('plugins') or {}
    return isinstance(plugins, dict) and 'themis' in (plugins.get('enabled') or []) and 'themis' not in (plugins.get('disabled') or [])


def migrate_themis_profile(*, runner=None, hermes_exe=None, log_fn=print):
    """One explicit, resumable native profile/install workflow."""
    import shutil
    import subprocess

    status = inspect_themis_profile()
    blockers = [b for b in status['blockers'] if b != 'plugin_revisions_differ']
    if blockers:
        raise ProfileProvisionError(f"Preflight recusado: {blockers}")
    default = Path(status['default_home'])
    named = Path(status['profile_home'])
    source, revision = _migration_source(default)
    if 'plugin_revisions_differ' not in status['blockers']:
        setup_themis_profile(log_fn=log_fn)
    _copy_missing_providers(default, named)
    _copy_missing_env(default, named)
    installed = (named / 'plugins' / 'themis' / 'plugin.yaml').is_file()
    actual = _plugin_revision(named)
    command = None
    if not installed or actual != revision:
        command = ['plugins', 'install', source, '--ref', revision, '--yes-deps', '--enable']
        if installed:
            command.append('--force')
    elif not _plugin_enabled(named):
        command = ['plugins', 'enable', 'themis', '--no-allow-tool-override']
    if command:
        executable = hermes_exe or shutil.which('hermes')
        if not executable:
            raise ProfileProvisionError('Hermes CLI não localizado')
        execute = runner or subprocess.run
        # Inherit the console streams. Windows' default cp1252 cannot decode
        # UTF-8 emitted by Hermes, and capture_output also hides install failures.
        result = execute([executable, '-p', PROFILE, *command],
                         check=False, timeout=1800)
        if result.returncode != 0:
            raise ProfileProvisionError(
                f'Instalador Hermes falhou (código {result.returncode}); '
                'consulte a saída acima. Perfil preservado para retomada.'
            )
    post = inspect_themis_profile()
    if not post['ready'] or not _plugin_enabled(named):
        raise ProfileProvisionError('Instalação ainda não está pronta; execute novamente após corrigir pendências')
    log_fn('  [OK] Perfil themis instalado e habilitado com a mesma revisão Git.')
    return post
