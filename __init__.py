"""Themis unified plugin for Hermes."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

# Hermes loads directory plugins under a package namespace and does not add
# the plugin root to sys.path. Keep the plugin root importable for legacy
# absolute imports while package-relative imports are preferred.
_PLUGIN_ROOT = Path(__file__).resolve().parent
_plugin_root_str = str(_PLUGIN_ROOT)
if _plugin_root_str not in sys.path:
    sys.path.insert(0, _plugin_root_str)


def _bridge_module():
    """Load the bridge once under a process-wide name shared with the dashboard."""
    try:
        return importlib.import_module("themis_llm_bridge")
    except ModuleNotFoundError as exc:
        if exc.name != "themis_llm_bridge":
            raise
    path = Path(__file__).with_name("themis_llm_bridge.py")
    spec = importlib.util.spec_from_file_location("themis_llm_bridge", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["themis_llm_bridge"] = module
    spec.loader.exec_module(module)
    return module


def _load_setup_cli():
    """Load the setup CLI helpers across package and standalone import roots."""
    _plugin_root_str = str(_PLUGIN_ROOT)
    if _plugin_root_str not in sys.path:
        sys.path.insert(0, _plugin_root_str)
    try:
        from plugins.themis.setup_cli import register_cli, run_themis_setup
        return register_cli, run_themis_setup
    except ImportError:
        pass

    try:
        from .setup_cli import register_cli, run_themis_setup
        return register_cli, run_themis_setup
    except (ImportError, ValueError):
        pass

    try:
        from setup_cli import register_cli, run_themis_setup
        return register_cli, run_themis_setup
    except ImportError:
        pass

    path = Path(__file__).with_name("setup_cli.py")
    spec = importlib.util.spec_from_file_location("themis_setup_cli", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load setup_cli from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.register_cli, module.run_themis_setup


def register(ctx):
    """Publish the host-selected LLM facade for the dashboard API and register CLI commands."""
    _bridge_module().register_runtime(ctx)

    try:
        register_cli, run_themis_setup = _load_setup_cli()
        ctx.register_cli_command(
            name="themis",
            help="Comandos da plataforma jurídica Themis (setup, etc.)",
            setup_fn=register_cli,
            handler_fn=run_themis_setup,
            description="Themis — Plataforma jurídica unificada para Hermes. Execute: hermes themis setup",
        )
    except Exception as exc:
        # Keep the plugin runtime available, but never make the CLI failure silent.
        import logging
        logging.getLogger(__name__).warning(
            "Falha ao registrar comandos CLI do Themis: %s", exc, exc_info=True
        )

        def _broken_cli_parser(subparser):
            subparser.set_defaults(_themis_cli_load_error=str(exc))

        def _broken_cli_handler(args):
            message = (
                "Themis foi carregado, mas o comando CLI não pôde ser inicializado: "
                f"{getattr(args, '_themis_cli_load_error', exc)}"
            )
            print(message, file=sys.stderr)
            raise SystemExit(2)

        ctx.register_cli_command(
            name="themis",
            help="Comandos da plataforma jurídica Themis (falha de inicialização)",
            setup_fn=_broken_cli_parser,
            handler_fn=_broken_cli_handler,
            description="Themis — falha ao inicializar a interface CLI. Consulte o log do Hermes.",
        )
