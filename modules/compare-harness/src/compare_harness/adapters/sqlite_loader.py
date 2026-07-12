from __future__ import annotations

from pathlib import Path
import re
import sqlite3

from compare_harness.domain.models import Record

_VALID_TABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_rows(database_path: Path, table_name: str) -> tuple[Record, ...]:
    if not database_path.is_file():
        raise ValueError(f"Expected sqlite file not found: {database_path}")
    if not _VALID_TABLE_NAME.match(table_name):
        raise ValueError(f"Invalid sqlite table name: {table_name!r}")

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(f"SELECT * FROM {table_name}")
        rows = tuple(dict(row) for row in cursor.fetchall())
    return rows
