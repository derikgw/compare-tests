from __future__ import annotations

from dataclasses import dataclass
from typing import Any


Record = dict[str, Any]


@dataclass(frozen=True)
class Finding:
    phase_id: str
    severity: str
    message: str
    table: str
    row_key: dict[str, Any] | None = None
    column: str | None = None
    baseline_value: Any = None
    candidate_value: Any = None


@dataclass(frozen=True)
class PhaseResult:
    phase_id: str
    status: str
    findings: tuple[Finding, ...]
    metrics: dict[str, Any]


@dataclass(frozen=True)
class CompareContext:
    dataset_name: str
    table_name: str
    key_columns: tuple[str, ...]
    excluded_columns: tuple[str, ...]
    baseline_rows: tuple[Record, ...]
    candidate_rows: tuple[Record, ...]
    phase_config: dict[str, Any]


@dataclass(frozen=True)
class DatasetComparisonResult:
    dataset_name: str
    table_name: str
    phase_results: tuple[PhaseResult, ...]


@dataclass(frozen=True)
class CompareRunResult:
    baseline_ref: str
    candidate_ref: str
    datasets: tuple[DatasetComparisonResult, ...]
