#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

VARIANT="${ETL_VARIANT:-default}"
INPUT_ROOT="${1:-${MODULE_DIR}/data/raw}"
OUTPUT_DB="${2:-${MODULE_DIR}/runs/output.db}"

PYTHONPATH="${MODULE_DIR}/src:${PYTHONPATH:-}" \
  python -m etl_app run \
    --variant "${VARIANT}" \
    --input-root "${INPUT_ROOT}" \
    --output-db "${OUTPUT_DB}"

echo "ETL run complete -> ${OUTPUT_DB}"
