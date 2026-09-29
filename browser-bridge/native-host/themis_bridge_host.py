#!/usr/bin/env python3
"""Themis Browser Bridge native host.

Its only responsibility is local discovery:
- derive the Hermes home from the installed Themis plugin path;
- read Hermes' own spawn-ledger.json;
- select the active local serve/dashboard endpoint;
- read the Themis bridge token;
- return that information through Chrome/Edge Native Messaging.

No provider, scraping, PDF, process or legal-domain logic belongs here.
"""

from __future__ import annotations

import ctypes
import json
import os
import socket
import struct
import sys
from pathlib import Path
from typing import Any


HOST_NAME = "themis_browser_bridge"
BRIDGE_API_PATH = "/api/plugins/themis/bridge"


def _installed_plugin_home() -> Path | None:
    """Return <HERMES_HOME> from <home>/plugins/themis/browser-bridge/native-host."""
    try:
        current = Path(__file__).resolve()
        plugin_root = current.parents[2]   # .../plugins/themis
        plugins_root = current.parents[3]  # .../plugins
        home = current.parents[4]          # .../<HERMES_HOME>
    except (OSError, IndexError):
        return None

    if plugin_root.name.lower() != "themis":
        return None
    if plugins_root.name.lower() != "plugins":
        return None
    return home


def _default_root_for_home(home: Path) -> Path:
    """Mirror Hermes get_default_hermes_root(home=...) for a known installed home."""
    if home.parent.name.lower() == "profiles":
        return home.parent.parent
    return home


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _process_alive(pid: int) -> bool:
    if pid <= 0:
        return False

    if os.name == "nt":
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        kernel32.CloseHandle(handle)
        return True

    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _loopback_host(value: Any) -> str | None:
    host = str(value or "127.0.0.1").strip().lower()
    if host in {"127.0.0.1", "localhost", "0.0.0.0", "::", "::1"}:
        return "127.0.0.1"
    return None


def _port_open(host: str, port: int, timeout: float = 0.35) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _same_home(left: Any, right: Path) -> bool:
    if not isinstance(left, str) or not left.strip():
        return False
    try:
        return os.path.normcase(str(Path(left).expanduser().resolve())) == os.path.normcase(
            str(right.expanduser().resolve())
        )
    except OSError:
        return False


def _candidate_entries(entries: list[dict[str, Any]], home: Path) -> list[dict[str, Any]]:
    candidates = [
        entry
        for entry in entries
        if entry.get("purpose") in {"serve", "dashboard"}
        and not bool(entry.get("isolated"))
    ]

    # Prefer the backend registered for this exact Hermes home/profile.
    matching = [entry for entry in candidates if _same_home(entry.get("hermes_home"), home)]
    if matching:
        candidates = matching

    def registered_at(entry: dict[str, Any]) -> float:
        try:
            return float(entry.get("registered_at") or 0.0)
        except (TypeError, ValueError):
            return 0.0

    return sorted(candidates, key=registered_at, reverse=True)


def _discover_endpoint(home: Path) -> dict[str, Any] | None:
    ledger = _default_root_for_home(home) / "spawn-ledger.json"
    payload = _read_json(ledger)
    if not isinstance(payload, list):
        return None

    entries = [entry for entry in payload if isinstance(entry, dict)]
    for entry in _candidate_entries(entries, home):
        try:
            pid = int(entry.get("pid") or 0)
            port = int(entry.get("port") or 0)
        except (TypeError, ValueError):
            continue

        host = _loopback_host(entry.get("host"))
        if host is None or not (1 <= port <= 65535):
            continue
        if not _process_alive(pid):
            continue
        if not _port_open(host, port):
            continue

        return {
            "host": host,
            "port": port,
            "pid": pid,
            "purpose": str(entry.get("purpose")),
        }

    return None


def _read_bridge_token(home: Path) -> str:
    token_path = home / "plugin-data" / "themis" / "config" / "bridge_token.json"
    payload = _read_json(token_path)
    if not isinstance(payload, dict):
        return ""
    token = payload.get("token")
    return token if isinstance(token, str) else ""


def discover_hermes_endpoint() -> dict[str, Any]:
    home = _installed_plugin_home()
    if home is None:
        return {
            "success": False,
            "error": "Não foi possível derivar HERMES_HOME a partir da instalação do plugin.",
            "token": "",
        }

    endpoint = _discover_endpoint(home)
    token = _read_bridge_token(home)

    if endpoint is None:
        return {
            "success": False,
            "error": "Nenhum backend Hermes serve/dashboard ativo foi encontrado no spawn-ledger.",
            "token": token,
        }

    host = endpoint["host"]
    port = endpoint["port"]
    return {
        "success": True,
        "host": host,
        "port": port,
        "pid": endpoint["pid"],
        "purpose": endpoint["purpose"],
        "api_base": f"http://{host}:{port}{BRIDGE_API_PATH}",
        "token": token,
    }


def _read_native_message() -> dict[str, Any] | None:
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) < 4:
        return None

    length = struct.unpack("<I", raw_length)[0]
    if length <= 0:
        return None

    raw = sys.stdin.buffer.read(length)
    if len(raw) != length:
        return None

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_native_message(payload: dict[str, Any]) -> None:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(raw)))
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()


def main() -> None:
    if sys.platform == "win32":
        import msvcrt

        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

    while True:
        request = _read_native_message()
        if request is None:
            break

        action = request.get("action", "GET_ENDPOINT")
        if action == "GET_ENDPOINT":
            response = discover_hermes_endpoint()
        else:
            response = {
                "success": False,
                "error": f"Ação desconhecida: {action}",
            }

        _write_native_message(response)


if __name__ == "__main__":
    main()
