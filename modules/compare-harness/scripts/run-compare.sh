#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_DIR="${APP_CONFIG_DIR:-${MODULE_DIR}/config}"
PROFILE="${1:-local}"

PYTHONPATH="${MODULE_DIR}/src:${PYTHONPATH:-}" \
  python -m compare_harness.cli run \
    --config-dir "${CONFIG_DIR}" \
    --profile "${PROFILE}"
