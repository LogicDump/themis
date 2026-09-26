#!/usr/bin/env python3
"""Themis Browser Bridge - Native Messaging Host for dynamic Hermes endpoint discovery."""
import os
import sys
import json
import struct
import ctypes
from pathlib import Path


def is_pid_alive(pid: int) -> bool:
    """Verifica se o processo com o PID fornecido está ativo no Windows."""
    if not pid or pid <= 0:
        return False
    if os.name == "nt":
        process_query_limited_information = 0x1000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _installed_hermes_paths() -> tuple[list[Path], list[Path]]:
    homes: list[Path] = []
    try:
        from hermes_constants import get_hermes_home
    except ModuleNotFoundError as exc:
        if exc.name != "hermes_constants":
            raise
        env_home = os.environ.get("HERMES_HOME")
        if env_home:
            homes.append(Path(env_home))
    else:
        homes.append(Path(get_hermes_home()))

    if not homes:
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "spawn-ledger.json").is_file() or (parent / "hermes-agent").is_dir() or (parent / "config.yaml").is_file():
                homes.append(parent)
                break

    unique_homes = list(dict.fromkeys(path.expanduser().resolve() for path in homes))
    return unique_homes, []


def discover_hermes_endpoint() -> dict:
    """Descobre o endpoint dinâmico do Hermes e o token de emparelhamento do Themis."""
    homes, data_roots = _installed_hermes_paths()
    if len(homes) != 1:
        return {
            "success": False,
            "error": "HermesHome ativo não pôde ser resolvido; configure HERMES_HOME pelo Hermes.",
            "token": "",
        }
    candidates = [home / "spawn-ledger.json" for home in homes]

    discovered = None
    for ledger_path in candidates:
        if not ledger_path.exists():
            continue
        try:
            entries = json.loads(ledger_path.read_text(encoding="utf-8"))
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                purpose = entry.get("purpose")
                port = entry.get("port")
                pid = entry.get("pid")
                if purpose in ("serve", "dashboard") and port and pid:
                    if is_pid_alive(pid):
                        host = entry.get("host") or "127.0.0.1"
                        if host in ("0.0.0.0", "::"):
                            host = "127.0.0.1"
                        discovered = {
                            "host": host,
                            "port": int(port),
                            "pid": pid,
                            "purpose": purpose,
                        }
                        break
        except Exception:
            pass_e = None
        if discovered:
            break

    token = ""
    themis_data = os.environ.get("THEMIS_DATA_ROOT")
    token_candidates = []
    if themis_data:
        token_candidates.append(Path(themis_data) / "config" / "bridge_token.json")
    token_candidates.extend(root / "config" / "bridge_token.json" for root in data_roots)
    token_candidates.extend(home / "plugin-data" / "themis" / "config" / "bridge_token.json" for home in homes)
    for tp in token_candidates:
        if tp.exists():
            try:
                tdata = json.loads(tp.read_text(encoding="utf-8"))
                if isinstance(tdata, dict) and tdata.get("token"):
                    token = tdata["token"]
                    break
            except Exception:
                pass_t = None

    if not discovered:
        return {
            "success": False,
            "error": "Hermes Desktop não está em execução ou ledger não encontrado.",
            "token": token,
        }

    host = discovered["host"]
    port = discovered["port"]
    api_base = f"http://{host}:{port}/api/plugins/themis/bridge"

    return {
        "success": True,
        "host": host,
        "port": port,
        "pid": discovered["pid"],
        "api_base": api_base,
        "token": token,
    }


def main():
    if sys.platform == "win32":
        import msvcrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

    while True:
        raw_length = sys.stdin.buffer.read(4)
        if len(raw_length) < 4:
            break
        msg_len = struct.unpack("@I", raw_length)[0]
        if msg_len == 0:
            break
        raw_data = sys.stdin.buffer.read(msg_len).decode("utf-8")
        try:
            req = json.loads(raw_data)
        except Exception:
            req = {}

        action = req.get("action", "GET_ENDPOINT")
        if action == "GET_ENDPOINT":
            resp = discover_hermes_endpoint()
        else:
            resp = {"success": False, "error": f"Ação desconhecida: {action}"}

        resp_bytes = json.dumps(resp).encode("utf-8")
        sys.stdout.buffer.write(struct.pack("@I", len(resp_bytes)))
        sys.stdout.buffer.write(resp_bytes)
        sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
