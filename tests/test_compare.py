from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from compare_tests.compare import CompareService, GitBaselineWorkspace, SchemaChange, build_report
from compare_tests.config import DEFAULT_BASELINE_REF, CompareConfig, load_compare_config


class GitBaselineWorkspaceTests(unittest.TestCase):
    def test_defaults_to_main_and_checks_out_baseline_content(self) -> None:
        with TemporaryGitRepository() as repository:
            baseline_file = repository / "dataset.txt"
            baseline_file.write_text("baseline\n", encoding="utf-8")
            git(repository, "add", "dataset.txt")
            git(repository, "commit", "-m", "baseline")
            git(repository, "checkout", "-b", "feature")
            baseline_file.write_text("candidate\n", encoding="utf-8")
            git(repository, "commit", "-am", "candidate")

            with GitBaselineWorkspace(repository) as baseline_workspace:
                self.assertEqual((baseline_workspace / "dataset.txt").read_text(encoding="utf-8"), "baseline\n")

    def test_accepts_commit_hash_override(self) -> None:
        with TemporaryGitRepository() as repository:
            tracked_file = repository / "dataset.txt"
            tracked_file.write_text("first\n", encoding="utf-8")
            git(repository, "add", "dataset.txt")
            git(repository, "commit", "-m", "first")
            baseline_commit = git_output(repository, "rev-parse", "HEAD")
            tracked_file.write_text("second\n", encoding="utf-8")
            git(repository, "commit", "-am", "second")

            with GitBaselineWorkspace(repository, baseline_commit) as baseline_workspace:
                self.assertEqual((baseline_workspace / "dataset.txt").read_text(encoding="utf-8"), "first\n")


class CompareServiceTests(unittest.TestCase):
    def test_runs_baseline_before_candidate_and_reports_differences(self) -> None:
        with TemporaryGitRepository() as repository:
            version_file = repository / "version.txt"
            version_file.write_text("baseline\n", encoding="utf-8")
            git(repository, "add", "version.txt")
            git(repository, "commit", "-m", "baseline")
            git(repository, "checkout", "-b", "feature")
            version_file.write_text("candidate\n", encoding="utf-8")
            git(repository, "commit", "-am", "candidate")

            config = load_compare_config(
                {
                    "dataset_name": "claims",
                    "key_columns": ["claim_id"],
                    "excluded_columns": ["updated_at"],
                }
            )
            adapter = RecordingAdapter()

            report = CompareService(repository, adapter).run(config)

            self.assertEqual(adapter.calls, ["baseline\n", "candidate\n"])
            self.assertEqual(report.schema_changes, ())
            self.assertEqual(report.rows[0].status, "changed")
            self.assertEqual(report.rows[0].columns[1].status, "changed")
            self.assertEqual(report.rows[0].columns[2].status, "excluded")


class BuildReportTests(unittest.TestCase):
    def test_reports_schema_changes_and_excluded_only_rows(self) -> None:
        report = build_report(
            dataset_name="claims",
            baseline_ref=DEFAULT_BASELINE_REF,
            candidate_ref="workspace",
            key_columns=("claim_id",),
            excluded_columns=("updated_at",),
            baseline_rows=(
                {"claim_id": 1, "amount": 100, "updated_at": "2024-01-01", "legacy_only": "x"},
            ),
            candidate_rows=(
                {"claim_id": 1, "amount": 100, "updated_at": "2024-02-01", "new_only": "y"},
            ),
        )

        self.assertEqual(
            report.schema_changes,
            (
                SchemaChange("removed", "legacy_only"),
                SchemaChange("added", "new_only"),
            ),
        )
        self.assertEqual(report.rows[0].status, "changed")
        self.assertEqual(
            [(column.column_name, column.status) for column in report.rows[0].columns],
            [
                ("claim_id", "unchanged"),
                ("amount", "unchanged"),
                ("updated_at", "excluded"),
                ("legacy_only", "changed"),
                ("new_only", "changed"),
            ],
        )

    def test_marks_row_excluded_when_only_excluded_columns_change(self) -> None:
        report = build_report(
            dataset_name="claims",
            baseline_ref=DEFAULT_BASELINE_REF,
            candidate_ref="workspace",
            key_columns=("claim_id",),
            excluded_columns=("updated_at",),
            baseline_rows=({"claim_id": 1, "updated_at": "2024-01-01", "amount": 100},),
            candidate_rows=({"claim_id": 1, "updated_at": "2024-02-01", "amount": 100},),
        )

        self.assertEqual(report.rows[0].status, "excluded")

    def test_rejects_duplicate_keys(self) -> None:
        with self.assertRaisesRegex(ValueError, "Duplicate row detected"):
            build_report(
                dataset_name="claims",
                baseline_ref=DEFAULT_BASELINE_REF,
                candidate_ref="workspace",
                key_columns=("claim_id",),
                excluded_columns=(),
                baseline_rows=(
                    {"claim_id": 1, "amount": 100},
                    {"claim_id": 1, "amount": 125},
                ),
                candidate_rows=(),
            )


class RecordingAdapter:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def materialize(self, workspace: Path, config: CompareConfig) -> tuple[dict[str, object], ...]:
        version = (workspace / "version.txt").read_text(encoding="utf-8")
        self.calls.append(version)
        return (
            {
                "claim_id": 1,
                "amount": 100 if version == "baseline\n" else 125,
                "updated_at": "2024-01-01" if version == "baseline\n" else "2024-02-01",
            },
        )


class TemporaryGitRepository:
    def __enter__(self) -> Path:
        self._tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self._tempdir.name)
        git(self.path, "init", "-b", "main")
        git(self.path, "config", "user.name", "Copilot")
        git(self.path, "config", "user.email", "copilot@example.com")
        return self.path

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self._tempdir.cleanup()


def git(repository: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repository), *args], check=True, capture_output=True, text=True)


def git_output(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
