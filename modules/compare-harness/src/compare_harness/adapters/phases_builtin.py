from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from json import dumps
from typing import Any

from compare_tests.compare import build_report
from compare_harness.domain.models import CompareContext, Finding, PhaseResult, Record
from compare_harness.domain.phases import ComparePhase


def build_builtin_phase_registry() -> dict[str, ComparePhase]:
    phases: list[ComparePhase] = [
        SchemaPhase(),
        DatatypePhase(),
        HashPhase(),
        RowDiffPhase(),
    ]
    return {phase.id: phase for phase in phases}


class SchemaPhase:
    id = "schema"

    def validate_config(self, config: dict[str, object]) -> None:
        _expect_bool(config, "allow_additive_columns", default=False)

    def run(self, context: CompareContext) -> PhaseResult:
        report = build_report(
            dataset_name=context.dataset_name,
            baseline_ref="baseline",
            candidate_ref="candidate",
            key_columns=context.key_columns,
            excluded_columns=context.excluded_columns,
            baseline_rows=context.baseline_rows,
            candidate_rows=context.candidate_rows,
        )

        removed = sorted(change.column_name for change in report.schema_changes if change.change_type == "removed")
        added = sorted(change.column_name for change in report.schema_changes if change.change_type == "added")
        allow_additive = bool(context.phase_config.get("allow_additive_columns", False))

        findings = tuple(
            [
                Finding(
                    phase_id=self.id,
                    severity="high",
                    message=f"Column removed: {column}",
                    table=context.table_name,
                    column=column,
                )
                for column in removed
            ]
            + [
                Finding(
                    phase_id=self.id,
                    severity="medium" if allow_additive else "high",
                    message=f"Column added: {column}",
                    table=context.table_name,
                    column=column,
                )
                for column in added
            ]
        )
        failed = bool(removed) or (bool(added) and not allow_additive)
        return PhaseResult(
            phase_id=self.id,
            status="failed" if failed else "passed",
            findings=findings,
            metrics={"removed_count": len(removed), "added_count": len(added)},
        )


class DatatypePhase:
    id = "datatype"

    def validate_config(self, config: dict[str, object]) -> None:
        _expect_bool(config, "ignore_nulls", default=True)

    def run(self, context: CompareContext) -> PhaseResult:
        ignore_nulls = bool(context.phase_config.get("ignore_nulls", True))
        baseline_types = _collect_column_types(context.baseline_rows, ignore_nulls)
        candidate_types = _collect_column_types(context.candidate_rows, ignore_nulls)
        findings: list[Finding] = []

        for column in sorted(set(baseline_types) | set(candidate_types)):
            if baseline_types.get(column, set()) == candidate_types.get(column, set()):
                continue
            findings.append(
                Finding(
                    phase_id=self.id,
                    severity="medium",
                    message=f"Datatype mismatch for column '{column}'",
                    table=context.table_name,
                    column=column,
                    baseline_value=sorted(baseline_types.get(column, set())),
                    candidate_value=sorted(candidate_types.get(column, set())),
                )
            )

        return PhaseResult(
            phase_id=self.id,
            status="failed" if findings else "passed",
            findings=tuple(findings),
            metrics={"mismatch_count": len(findings)},
        )


class HashPhase:
    id = "hash"

    def validate_config(self, config: dict[str, object]) -> None:
        _expect_bool(config, "exclude_columns", default=True)

    def run(self, context: CompareContext) -> PhaseResult:
        exclude_columns = bool(context.phase_config.get("exclude_columns", True))
        baseline_index = _index_rows(context.baseline_rows, context.key_columns)
        candidate_index = _index_rows(context.candidate_rows, context.key_columns)
        all_keys = sorted(set(baseline_index) | set(candidate_index))
        excluded = set(context.excluded_columns) if exclude_columns else set()

        findings: list[Finding] = []
        for key in all_keys:
            baseline = baseline_index.get(key)
            candidate = candidate_index.get(key)
            if baseline is None:
                findings.append(
                    Finding(
                        phase_id=self.id,
                        severity="high",
                        message="Row only in candidate.",
                        table=context.table_name,
                        row_key=_format_key(context.key_columns, key),
                    )
                )
                continue
            if candidate is None:
                findings.append(
                    Finding(
                        phase_id=self.id,
                        severity="high",
                        message="Row only in baseline.",
                        table=context.table_name,
                        row_key=_format_key(context.key_columns, key),
                    )
                )
                continue

            baseline_hash = _row_hash(baseline, excluded)
            candidate_hash = _row_hash(candidate, excluded)
            if baseline_hash == candidate_hash:
                continue

            findings.append(
                Finding(
                    phase_id=self.id,
                    severity="medium",
                    message="Row hash mismatch.",
                    table=context.table_name,
                    row_key=_format_key(context.key_columns, key),
                    baseline_value=baseline_hash,
                    candidate_value=candidate_hash,
                )
            )

        return PhaseResult(
            phase_id=self.id,
            status="failed" if findings else "passed",
            findings=tuple(findings),
            metrics={"mismatch_count": len(findings), "row_count": len(all_keys)},
        )


class RowDiffPhase:
    id = "rowdiff"

    def validate_config(self, config: dict[str, object]) -> None:
        _expect_int(config, "max_findings", default=200)

    def run(self, context: CompareContext) -> PhaseResult:
        max_findings = int(context.phase_config.get("max_findings", 200))
        report = build_report(
            dataset_name=context.dataset_name,
            baseline_ref="baseline",
            candidate_ref="candidate",
            key_columns=context.key_columns,
            excluded_columns=context.excluded_columns,
            baseline_rows=context.baseline_rows,
            candidate_rows=context.candidate_rows,
        )

        findings: list[Finding] = []
        for row in report.rows:
            for column in row.columns:
                if column.status != "changed":
                    continue
                findings.append(
                    Finding(
                        phase_id=self.id,
                        severity="medium",
                        message=f"Value mismatch in '{column.column_name}'.",
                        table=context.table_name,
                        row_key=row.key,
                        column=column.column_name,
                        baseline_value=column.baseline_value,
                        candidate_value=column.candidate_value,
                    )
                )
                if len(findings) >= max_findings:
                    return PhaseResult(
                        phase_id=self.id,
                        status="failed",
                        findings=tuple(findings),
                        metrics={"truncated": True, "max_findings": max_findings},
                    )

        return PhaseResult(
            phase_id=self.id,
            status="failed" if findings else "passed",
            findings=tuple(findings),
            metrics={"truncated": False, "finding_count": len(findings)},
        )


def _collect_column_types(rows: tuple[Record, ...], ignore_nulls: bool) -> dict[str, set[str]]:
    column_types: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        for column_name, value in row.items():
            if value is None and ignore_nulls:
                continue
            column_types[column_name].add(type(value).__name__)
    return column_types


def _index_rows(rows: tuple[Record, ...], key_columns: tuple[str, ...]) -> dict[tuple[Any, ...], Record]:
    indexed: dict[tuple[Any, ...], Record] = {}
    for row in rows:
        key = tuple(row.get(column_name) for column_name in key_columns)
        if key in indexed:
            raise ValueError(f"Duplicate row detected for key {key!r}")
        indexed[key] = row
    return indexed


def _row_hash(row: Record, excluded_columns: set[str]) -> str:
    included = {key: value for key, value in row.items() if key not in excluded_columns}
    payload = dumps(included, sort_keys=True, default=str, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def _format_key(columns: tuple[str, ...], values: tuple[Any, ...]) -> dict[str, Any]:
    return {column_name: values[index] for index, column_name in enumerate(columns)}


def _expect_bool(config: dict[str, object], key: str, *, default: bool) -> None:
    value = config.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"Phase config '{key}' must be a boolean.")


def _expect_int(config: dict[str, object], key: str, *, default: int) -> None:
    value = config.get(key, default)
    if not isinstance(value, int):
        raise ValueError(f"Phase config '{key}' must be an integer.")
