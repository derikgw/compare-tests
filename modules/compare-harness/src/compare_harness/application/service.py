from __future__ import annotations

from pathlib import Path

from compare_tests.compare import build_report
from compare_harness.adapters.git_worktree import GitBaselineWorkspace
from compare_harness.adapters.phases_builtin import build_builtin_phase_registry
from compare_harness.adapters.subprocess_runner import run_command
from compare_harness.domain.models import (
    CompareContext,
    CompareRunResult,
    DatasetComparisonResult,
    ValueColumnComparison,
    ValueRowComparison,
)
from compare_harness.domain.ports import ComparisonReportWriter, OutputDatasetReader

from .adapter_registry import create_output_reader, create_report_writers
from .configuration import DatasetConfig, HarnessConfig
from .pipeline import ComparePipeline


class CompareHarnessService:
    def __init__(
        self,
        config: HarnessConfig,
        dataset_reader: OutputDatasetReader | None = None,
        report_writers: tuple[tuple[str, ComparisonReportWriter, Path], ...] | None = None,
    ) -> None:
        self._config = config
        self._pipeline = ComparePipeline(build_builtin_phase_registry())
        self._dataset_reader = dataset_reader or create_output_reader(config)
        self._report_writers = report_writers or create_report_writers(config)

    def run(self) -> CompareRunResult:
        self._materialize_etl_outputs()
        dataset_results = tuple(self._run_dataset(dataset) for dataset in self._config.datasets)
        run_result = CompareRunResult(
            baseline_ref=self._config.baseline_ref,
            candidate_ref=self._config.candidate_ref,
            datasets=dataset_results,
            report_artifacts={},
        )
        report_artifacts: dict[str, str] = {}
        for report_name, writer, output_path in self._report_writers:
            written_path = writer.write(
                run_result=run_result,
                output_path=output_path,
            )
            report_artifacts[report_name] = str(written_path)
        return CompareRunResult(
            baseline_ref=run_result.baseline_ref,
            candidate_ref=run_result.candidate_ref,
            datasets=run_result.datasets,
            report_artifacts=report_artifacts,
        )

    def _materialize_etl_outputs(self) -> None:
        with GitBaselineWorkspace(
            repository=self._config.repository_root,
            baseline_ref=self._config.baseline_ref,
            checkout_path=self._config.baseline_checkout_dir,
        ) as baseline_repo:
            baseline_etl_dir = baseline_repo / self._config.baseline_working_subpath
            if not baseline_etl_dir.is_dir():
                raise ValueError(
                    f"Baseline ETL directory not found in checked out ref '{self._config.baseline_ref}': {baseline_etl_dir}"
                )
            self._run_etl(
                command=self._config.baseline_command,
                working_dir=baseline_etl_dir,
                output_path=self._config.baseline_db_path,
                etl_ref=self._config.baseline_ref,
            )

        self._run_etl(
            command=self._config.candidate_command,
            working_dir=self._config.etl_working_dir,
            output_path=self._config.candidate_db_path,
            etl_ref=self._config.candidate_ref,
        )

    def _run_etl(self, *, command: str, working_dir: Path, output_path: Path, etl_ref: str) -> None:
        run_command(
            command=command,
            cwd=working_dir,
            extra_env={
                "ETL_OUTPUT_DB": str(output_path),
                "ETL_REF": etl_ref,
            },
            pythonpath_entries=(working_dir / "src",),
        )

    def _run_dataset(self, dataset: DatasetConfig) -> DatasetComparisonResult:
        dataset_rows = self._dataset_reader.load_dataset(
            baseline_db_path=self._config.baseline_db_path,
            candidate_db_path=self._config.candidate_db_path,
            table_name=dataset.table,
        )
        context = CompareContext(
            dataset_name=dataset.name,
            table_name=dataset.table,
            key_columns=dataset.key_columns,
            excluded_columns=dataset.excluded_columns,
            baseline_rows=dataset_rows.baseline_rows,
            candidate_rows=dataset_rows.candidate_rows,
            phase_config={},
        )
        value_report = build_report(
            dataset_name=dataset.name,
            baseline_ref=self._config.baseline_ref,
            candidate_ref=self._config.candidate_ref,
            key_columns=dataset.key_columns,
            excluded_columns=dataset.excluded_columns,
            baseline_rows=dataset_rows.baseline_rows,
            candidate_rows=dataset_rows.candidate_rows,
        )
        phase_results = self._pipeline.run(
            context,
            pipeline=self._config.pipeline,
            configs=self._config.phases,
            fail_fast=self._config.fail_fast,
        )
        return DatasetComparisonResult(
            dataset_name=dataset.name,
            table_name=dataset.table,
            phase_results=phase_results,
            value_rows=tuple(
                ValueRowComparison(
                    status=row.status,
                    key=dict(row.key),
                    columns=tuple(
                        ValueColumnComparison(
                            column_name=column.column_name,
                            status=column.status,
                            baseline_value=column.baseline_value,
                            candidate_value=column.candidate_value,
                        )
                        for column in row.columns
                    ),
                )
                for row in value_report.rows
            ),
        )
