from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from compare_harness.domain.models import Record


@dataclass(frozen=True)
class DatasetRows:
    baseline_rows: tuple[Record, ...]
    candidate_rows: tuple[Record, ...]


class OutputDatasetReader(Protocol):
    def load_dataset(self, *, baseline_db_path: Path, candidate_db_path: Path, table_name: str) -> DatasetRows:
        ...
