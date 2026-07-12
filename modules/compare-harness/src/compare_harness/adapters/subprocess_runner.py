from __future__ import annotations

from pathlib import Path
import os
import subprocess


def run_command(*, command: str, cwd: Path, extra_env: dict[str, str], pythonpath_entries: tuple[Path, ...] = ()) -> None:
    env = os.environ.copy()
    env.update(extra_env)
    if pythonpath_entries:
        pythonpath_prefix = os.pathsep.join(str(path) for path in pythonpath_entries)
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = pythonpath_prefix if not existing else f"{pythonpath_prefix}{os.pathsep}{existing}"
    subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        shell=True,
        check=True,
        text=True,
    )
