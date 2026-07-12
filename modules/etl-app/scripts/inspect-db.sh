#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DB_PATH="${1:-${MODULE_DIR}/runs/output.db}"
TABLE_NAME="${2:-claims}"
LIMIT_ROWS="${3:-10}"

python - "${DB_PATH}" "${TABLE_NAME}" "${LIMIT_ROWS}" <<'PY'
import sqlite3
import re
import sys
from pathlib import Path

db_path = Path(sys.argv[1]).resolve()
table_name = sys.argv[2]
limit_rows = int(sys.argv[3])
if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", table_name):
    raise SystemExit(f"Invalid table name: {table_name}")

if not db_path.is_file():
    raise SystemExit(f"Database file not found: {db_path}")

connection = sqlite3.connect(str(db_path))
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

tables = cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()
print(f"Database: {db_path}")
print("Tables:", ", ".join(row["name"] for row in tables) if tables else "(none)")

exists = cursor.execute(
    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
    (table_name,),
).fetchone()

if exists:
    count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"\nTable: {table_name} (rows={count})")
    rows = cursor.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit_rows,)).fetchall()
    for row in rows:
        print(dict(row))
else:
    print(f"\nTable not found: {table_name}")

connection.close()
PY
