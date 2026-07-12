#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUNS_DIR="${1:-${MODULE_DIR}/runs}"

rm -rf "${RUNS_DIR}"
echo "Removed ETL run artifacts -> ${RUNS_DIR}"
