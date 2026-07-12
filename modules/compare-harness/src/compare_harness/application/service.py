from __future__ import annotations

from pathlib import Path

from compare_harness.adapters.git_worktree import GitBaselineWorkspace
from compare_harness.adapters.phases_builtin import build_builtin_phase_registry
from compare_harness.adapters.sqlite_loader import load_rows
from compare_harness.adapters.subprocess_runner import run_command
from compare_harness.domain.models import CompareContext, CompareRunResult, DatasetComparisonResult

from .configuration import DatasetConfig, HarnessConfig
from .pipeline import ComparePipeline


class CompareHarnessService:
    def __init__(self, config: HarnessConfig) -> None:
        self._config = config
        self._pipeline = ComparePipeline(build_builtin_phase_registry())

    def run(self) -> CompareRunResult:
        self._materialize_etl_outputs()
        dataset_results = tuple(self._run_dataset(dataset) for dataset in self._config.datasets)
        return CompareRunResult(
            baseline_ref=self._config.baseline_ref,
            candidate_ref=self._config.candidate_ref,
            datasets=dataset_results,
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
        baseline_rows = load_rows(self._config.baseline_db_path, dataset.table)
        candidate_rows = load_rows(self._config.candidate_db_path, dataset.table)
        context = CompareContext(
            dataset_name=dataset.name,
            table_name=dataset.table,
            key_columns=dataset.key_columns,
            excluded_columns=dataset.excluded_columns,
            baseline_rows=baseline_rows,
            candidate_rows=candidate_rows,
            phase_config={},
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
        )
