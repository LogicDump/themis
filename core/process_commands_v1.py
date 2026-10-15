"""Independent Themis CLI entries for process management."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from core.process_management_v1 import (
    archive_process, restore_process, delete_process_permanently, list_archived_processes,
)
from core.runtime_paths import themis_data_root


def run_archive(args, *, root: Path | str | None = None, log_fn: Callable = print) -> dict[str, Any]:
    result = archive_process(args.cnj, root=root or themis_data_root())
    log_fn(json.dumps(result, ensure_ascii=False))
    return result


def run_restore(args, *, root: Path | str | None = None, log_fn: Callable = print) -> dict[str, Any]:
    result = restore_process(args.cnj, root=root or themis_data_root())
    log_fn(json.dumps(result, ensure_ascii=False))
    return result


def run_delete(args, *, root: Path | str | None = None, log_fn: Callable = print) -> dict[str, Any]:
    result = delete_process_permanently(args.cnj, args.confirm_cnj, root=root or themis_data_root())
    log_fn(json.dumps(result, ensure_ascii=False))
    return result


def run_archived(args, *, root: Path | str | None = None, log_fn: Callable = print) -> dict[str, Any]:
    result = {"archived_processes": list_archived_processes(root=root or themis_data_root())}
    log_fn(json.dumps(result, ensure_ascii=False))
    return result


def register_management_cli(subs) -> None:
    for name, help_text, runner in (
        ("archive", "Arquivar processo sem excluir dados", run_archive),
        ("restore", "Restaurar processo arquivado", run_restore),
        ("delete", "Excluir processo definitivamente mediante confirmação", run_delete),
    ):
        parser = subs.add_parser(name, help=help_text)
        parser.add_argument("cnj", help="Número CNJ completo do processo")
        if name == "delete":
            parser.add_argument("--confirm-cnj", required=True, help="Repita o CNJ para confirmar exclusão")
        parser.set_defaults(func=runner)
    subs.add_parser("archived", help="Listar processos arquivados").set_defaults(func=run_archived)
