from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


class GitBaselineWorkspace:
    def __init__(self, repository: Path, baseline_ref: str, checkout_path: Path) -> None:
        self._repository = repository
        self._baseline_ref = baseline_ref
        self._checkout_path = checkout_path

    def __enter__(self) -> Path:
        if self._checkout_path.exists():
            self._run_git("worktree", "remove", "--force", str(self._checkout_path), check=False)
            shutil.rmtree(self._checkout_path, ignore_errors=True)
        self._checkout_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_ref = self._resolve_ref(self._baseline_ref)
        self._run_git("worktree", "add", "--detach", str(self._checkout_path), resolved_ref, check=True)
        return self._checkout_path

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self._run_git("worktree", "remove", "--force", str(self._checkout_path), check=False)
        shutil.rmtree(self._checkout_path, ignore_errors=True)

    def _resolve_ref(self, requested_ref: str) -> str:
        for ref in (requested_ref, f"origin/{requested_ref}"):
            result = subprocess.run(
                ["git", "-C", str(self._repository), "rev-parse", "--verify", ref],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return ref
        raise ValueError(f"Unable to resolve baseline ref '{requested_ref}' from {self._repository}")

    def _run_git(self, *args: str, check: bool) -> None:
        subprocess.run(
            ["git", "-C", str(self._repository), *args],
            capture_output=True,
            text=True,
            check=check,
        )
