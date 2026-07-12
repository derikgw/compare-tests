from __future__ import annotations

from pathlib import Path
import re
import sqlite3

from compare_harness.domain.models import Record
from compare_harness.domain.ports import DatasetRows, OutputDatasetReader

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


class SQLiteOutputDatasetReader(OutputDatasetReader):
    def load_dataset(self, *, baseline_db_path: Path, candidate_db_path: Path, table_name: str) -> DatasetRows:
        baseline_rows = load_rows(baseline_db_path, table_name)
        candidate_rows = load_rows(candidate_db_path, table_name)
        return DatasetRows(
            baseline_rows=baseline_rows,
            candidate_rows=candidate_rows,
        )
