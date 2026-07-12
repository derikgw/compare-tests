from __future__ import annotations

from pathlib import Path
from typing import Protocol

from compare_harness.domain.models import CompareRunResult


class ComparisonReportWriter(Protocol):
    def write(self, *, run_result: CompareRunResult, output_path: Path) -> Path:
        ...
