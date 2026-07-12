#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUTPUT_DIR="${1:-${MODULE_DIR}/output}"

rm -rf "${OUTPUT_DIR}"
echo "Removed compare-harness run artifacts -> ${OUTPUT_DIR}"
