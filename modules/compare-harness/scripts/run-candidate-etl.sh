#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_DIR="${APP_CONFIG_DIR:-${MODULE_DIR}/config}"
PROFILE="${1:-local}"

CONFIG_DIR_VALUE="${CONFIG_DIR}" PROFILE_VALUE="${PROFILE}" PYTHONPATH="${MODULE_DIR}/src:${PYTHONPATH:-}" python - <<'PY'
import os
from compare_harness.adapters.subprocess_runner import run_command
from compare_harness.application.configuration import load_harness_config

profile = os.environ.get("PROFILE_VALUE", "local")
config_dir = os.environ["CONFIG_DIR_VALUE"]
cfg = load_harness_config(config_dir=config_dir, profile=profile)
etl_dir = cfg.etl_working_dir
run_command(
    command=cfg.candidate_command,
    cwd=etl_dir,
    extra_env={"ETL_OUTPUT_DB": str(cfg.candidate_db_path), "ETL_REF": cfg.candidate_ref},
    pythonpath_entries=(etl_dir / "src",),
)
print(f"Candidate ETL output -> {cfg.candidate_db_path}")
print(f"Candidate source path -> {etl_dir}")
PY
