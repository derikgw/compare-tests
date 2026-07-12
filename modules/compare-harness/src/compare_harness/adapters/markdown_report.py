from __future__ import annotations

from pathlib import Path

from compare_harness.domain.models import CompareRunResult, ValueColumnComparison, ValueRowComparison
from compare_harness.domain.ports import ComparisonReportWriter

_STATUS_COLORS = {
    "matched": "#2e7d32",
    "different": "#c62828",
    "excluded": "#616161",
    "unknown": "#1565c0",
}

_STATUS_LABELS = {
    "unchanged": "matched",
    "changed": "different",
    "excluded": "excluded",
}


class MarkdownComparisonReportWriter(ComparisonReportWriter):
    def write(self, *, run_result: CompareRunResult, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self._render(run_result), encoding="utf-8")
        return output_path

    def _render(self, run_result: CompareRunResult) -> str:
        lines: list[str] = []
        lines.append("# Compare Report")
        lines.append("")
        lines.append(f"- Baseline ref: `{run_result.baseline_ref}`")
        lines.append(f"- Candidate ref: `{run_result.candidate_ref}`")
        lines.append("")
        lines.append("## Phase Summary")
        lines.append("")
        lines.append("| Dataset | Table | Phase | Status | Findings |")
        lines.append("|---|---|---|---|---:|")
        for dataset in run_result.datasets:
            for phase in dataset.phase_results:
                lines.append(
                    f"| {dataset.dataset_name} | {dataset.table_name} | {phase.phase_id} | "
                    f"{_status_span(_normalize_status(phase.status))} | {len(phase.findings)} |"
                )

        for dataset in run_result.datasets:
            lines.append("")
            lines.append(f"## Value Comparisons — {dataset.dataset_name}.{dataset.table_name}")
            lines.append("")
            lines.append("| Row Key | Column | Status | Baseline Value | Candidate Value |")
            lines.append("|---|---|---|---|---|")
            if not dataset.value_rows:
                lines.append("| (none) |  |  |  |  |")
                continue
            for row in dataset.value_rows:
                row_key = _format_row_key(row)
                for column in row.columns:
                    lines.append(
                        f"| `{_escape(row_key)}` | `{_escape(column.column_name)}` | "
                        f"{_status_span(_normalize_status(column.status))} | "
                        f"`{_escape(_to_text(column.baseline_value))}` | "
                        f"`{_escape(_to_text(column.candidate_value))}` |"
                    )
        lines.append("")
        return "\n".join(lines)


def _normalize_status(status: str) -> str:
    return _STATUS_LABELS.get(status, status)


def _status_span(status: str) -> str:
    color = _STATUS_COLORS.get(status, _STATUS_COLORS["unknown"])
    return f"<span style=\"color: {color}; font-weight: 600;\">{status}</span>"


def _format_row_key(row: ValueRowComparison) -> str:
    return ", ".join(f"{key}={value}" for key, value in row.key.items()) if row.key else "(none)"


def _to_text(value: object) -> str:
    if value is None:
        return "null"
    return str(value)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "\\n")
