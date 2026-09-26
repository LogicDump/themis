"""Themis unified plugin for Hermes."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path


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
        # CLI registration failure should not prevent runtime tools/bridge from loading
        import logging
        logging.getLogger(__name__).warning("Falha ao registrar comandos CLI do Themis: %s", exc)
