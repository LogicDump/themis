"""Cross-profile migration coordination: independent processes, one canonical root."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def test_migrate_all_serializes_independent_processes(tmp_path: Path) -> None:
    root = tmp_path / "shared-themis"
    plugin = Path(__file__).resolve().parents[1]
    command = [
        sys.executable, "-B", "-c",
        ("import json; from core.migration_manager import migrate_all; "
         "r=migrate_all(); print(json.dumps({'catalog':r['catalog']['changed'], "
         "'workspace':r['workspace']['changed']}))"),
    ]
    env = dict(os.environ, THEMIS_DATA_ROOT=str(root), PYTHONDONTWRITEBYTECODE="1")
    env["PYTHONPATH"] = os.pathsep.join(
        (str(plugin), env.get("PYTHONPATH", ""))
    )

    def worker(_: int) -> dict[str, bool]:
        result = subprocess.run(command, capture_output=True, text=True, timeout=45, env=env)
        assert result.returncode == 0, result.stderr[-1000:]
        return json.loads(result.stdout.strip().splitlines()[-1])

    with ThreadPoolExecutor(max_workers=6) as executor:
        output = list(executor.map(worker, range(12)))
    assert sum(int(item["catalog"]) for item in output) == 1
    assert sum(int(item["workspace"]) for item in output) == 1

    from core.migration_manager import migrate_all
    again = migrate_all(root=root)
    assert not again["catalog"]["changed"]
    assert not again["workspace"]["changed"]
