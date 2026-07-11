from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from tempfile import mkdtemp
from typing import Any, Protocol
import shutil
import subprocess

from .config import CompareConfig, DEFAULT_BASELINE_REF

Record = Mapping[str, Any]


class DatasetAdapter(Protocol):
    def materialize(self, workspace: Path, config: CompareConfig) -> Sequence[Record]:
        ...


@dataclass(frozen=True)
class SchemaChange:
    change_type: str
    column_name: str


@dataclass(frozen=True)
class ColumnComparison:
    column_name: str
    baseline_value: Any
    candidate_value: Any
    status: str


@dataclass(frozen=True)
class RowComparison:
    status: str
    key: dict[str, Any]
    columns: tuple[ColumnComparison, ...]


@dataclass(frozen=True)
class CompareReport:
    dataset_name: str
    baseline_ref: str
    candidate_ref: str
    schema_changes: tuple[SchemaChange, ...]
    rows: tuple[RowComparison, ...]


class GitBaselineWorkspace:
    def __init__(self, repository: Path, baseline_ref: str | None = None) -> None:
        self._repository = Path(repository)
        self._baseline_ref = baseline_ref or DEFAULT_BASELINE_REF
        self._root: Path | None = None
        self._workspace: Path | None = None

    @property
    def baseline_ref(self) -> str:
        return self._baseline_ref

    def __enter__(self) -> Path:
        ref = self._resolve_ref(self._baseline_ref)
        self._root = Path(mkdtemp(prefix="compare-tests-baseline-"))
        self._workspace = self._root / "workspace"
        self._run_git("worktree", "add", "--detach", str(self._workspace), ref)
        return self._workspace

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._workspace is not None:
            self._run_git("worktree", "remove", "--force", str(self._workspace))
        if self._root is not None:
            shutil.rmtree(self._root, ignore_errors=True)

    def _resolve_ref(self, requested_ref: str) -> str:
        for ref in (requested_ref, f"origin/{requested_ref}"):
            result = subprocess.run(
                ["git", "-C", str(self._repository), "rev-parse", "--verify", ref],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return ref
        raise ValueError(f"Unable to resolve baseline ref '{requested_ref}' from {self._repository}")

    def _run_git(self, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(self._repository), *args],
            capture_output=True,
            text=True,
            check=True,
        )


class CompareService:
    def __init__(self, repository: Path, adapter: DatasetAdapter) -> None:
        self._repository = Path(repository)
        self._adapter = adapter

    def run(self, config: CompareConfig) -> CompareReport:
        with GitBaselineWorkspace(self._repository, config.baseline_ref) as baseline_workspace:
            baseline_rows = tuple(self._adapter.materialize(baseline_workspace, config))

        candidate_rows = tuple(self._adapter.materialize(self._repository, config))
        return build_report(
            dataset_name=config.dataset_name,
            baseline_ref=config.baseline_ref or DEFAULT_BASELINE_REF,
            candidate_ref="workspace",
            key_columns=config.key_columns,
            excluded_columns=config.excluded_columns,
            baseline_rows=baseline_rows,
            candidate_rows=candidate_rows,
        )


def build_report(
    *,
    dataset_name: str,
    baseline_ref: str,
    candidate_ref: str,
    key_columns: Sequence[str],
    excluded_columns: Sequence[str],
    baseline_rows: Sequence[Record],
    candidate_rows: Sequence[Record],
) -> CompareReport:
    baseline_columns = _collect_columns(baseline_rows)
    candidate_columns = _collect_columns(candidate_rows)
    schema_changes = tuple(
        [SchemaChange(change_type="removed", column_name=column) for column in baseline_columns if column not in candidate_columns]
        + [SchemaChange(change_type="added", column_name=column) for column in candidate_columns if column not in baseline_columns]
    )

    all_columns = tuple(dict.fromkeys((*baseline_columns, *candidate_columns)))
    baseline_by_key = _index_rows(baseline_rows, key_columns)
    candidate_by_key = _index_rows(candidate_rows, key_columns)
    all_keys = sorted(set(baseline_by_key) | set(candidate_by_key))

    rows = tuple(
        _compare_row(
            key_columns=key_columns,
            excluded_columns=set(excluded_columns),
            all_columns=all_columns,
            baseline_row=baseline_by_key.get(key, {}),
            candidate_row=candidate_by_key.get(key, {}),
        )
        for key in all_keys
    )

    return CompareReport(
        dataset_name=dataset_name,
        baseline_ref=baseline_ref,
        candidate_ref=candidate_ref,
        schema_changes=schema_changes,
        rows=rows,
    )


def _collect_columns(rows: Sequence[Record]) -> tuple[str, ...]:
    ordered: dict[str, None] = {}
    for row in rows:
        for column_name in row:
            ordered.setdefault(column_name, None)
    return tuple(ordered)


def _index_rows(rows: Sequence[Record], key_columns: Sequence[str]) -> dict[tuple[Any, ...], Record]:
    indexed: dict[tuple[Any, ...], Record] = {}
    for row in rows:
        key = tuple(row.get(column_name) for column_name in key_columns)
        if key in indexed:
            raise ValueError(f"Duplicate row detected for key {key!r}")
        indexed[key] = row
    return indexed


def _compare_row(
    *,
    key_columns: Sequence[str],
    excluded_columns: set[str],
    all_columns: Sequence[str],
    baseline_row: Record,
    candidate_row: Record,
) -> RowComparison:
    changed = False
    excluded_difference = False
    comparisons: list[ColumnComparison] = []

    for column_name in all_columns:
        baseline_value = baseline_row.get(column_name)
        candidate_value = candidate_row.get(column_name)

        if column_name in excluded_columns:
            status = "excluded"
            excluded_difference = excluded_difference or baseline_value != candidate_value
        else:
            status = "unchanged" if baseline_value == candidate_value else "changed"
            changed = changed or status == "changed"

        comparisons.append(
            ColumnComparison(
                column_name=column_name,
                baseline_value=baseline_value,
                candidate_value=candidate_value,
                status=status,
            )
        )

    row_status = "changed" if changed else "excluded" if excluded_difference else "unchanged"
    key = {column_name: baseline_row.get(column_name, candidate_row.get(column_name)) for column_name in key_columns}
    return RowComparison(status=row_status, key=key, columns=tuple(comparisons))
