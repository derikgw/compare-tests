#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_DIR="${APP_CONFIG_DIR:-${MODULE_DIR}/config}"
PROFILE="${1:-local}"

CONFIG_DIR_VALUE="${CONFIG_DIR}" PROFILE_VALUE="${PROFILE}" PYTHONPATH="${MODULE_DIR}/src:${PYTHONPATH:-}" python - <<'PY'
import os
from compare_harness.adapters.git_worktree import GitBaselineWorkspace
from compare_harness.adapters.subprocess_runner import run_command
from compare_harness.application.configuration import load_harness_config

profile = os.environ.get("PROFILE_VALUE", "local")
config_dir = os.environ["CONFIG_DIR_VALUE"]
cfg = load_harness_config(config_dir=config_dir, profile=profile)
with GitBaselineWorkspace(cfg.repository_root, cfg.baseline_ref, cfg.baseline_checkout_dir) as baseline_repo:
    etl_dir = baseline_repo / cfg.baseline_working_subpath
    if not etl_dir.is_dir():
        raise ValueError(f"Baseline ETL directory not found for ref '{cfg.baseline_ref}': {etl_dir}")
    run_command(
        command=cfg.baseline_command,
        cwd=etl_dir,
        extra_env={"ETL_OUTPUT_DB": str(cfg.baseline_db_path), "ETL_REF": cfg.baseline_ref},
        pythonpath_entries=(etl_dir / "src",),
    )
print(f"Baseline ETL output -> {cfg.baseline_db_path}")
print(f"Baseline checkout path -> {cfg.baseline_checkout_dir}")
PY
