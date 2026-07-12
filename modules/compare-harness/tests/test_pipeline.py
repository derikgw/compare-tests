from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from compare_harness.adapters.phases_builtin import HashPhase, RowDiffPhase, SchemaPhase
from compare_harness.adapters.sqlite_loader import SQLiteOutputDatasetReader
from compare_harness.application.configuration import _parse_harness_config
from compare_harness.domain.models import CompareContext


class ConfigurationTests(unittest.TestCase):
    def test_parses_imported_phase_configs_and_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "compare/phases").mkdir(parents=True)
            (root / "compare/phases/schema.yml").write_text(
                "phase:\n  id: schema\n  enabled: true\n  order: 100\n  severity: high\n  config:\n    allow_additive_columns: false\n",
                encoding="utf-8",
            )
            (root / "compare/phases/hash.yml").write_text(
                "phase:\n  id: hash\n  enabled: true\n  order: 300\n  severity: medium\n  config:\n    exclude_columns: true\n",
                encoding="utf-8",
            )

            raw = {
                "etl": {
                    "working_dir": ".",
                    "baseline": {"command": "echo baseline"},
                    "candidate": {"command": "echo candidate"},
                },
                "io": {"sqlite": {"baseline_db": "baseline.db", "candidate_db": "candidate.db"}},
                "output_reader": {"adapter": "sqlite"},
                "report": {"adapters": ["markdown"], "markdown_output": "report.md"},
                "compare": {
                    "fail_fast": False,
                    "phase_imports": ["compare/phases/schema.yml", "compare/phases/hash.yml"],
                    "pipeline": ["schema", "hash"],
                    "datasets": [{"name": "claims", "table": "claims", "key_columns": ["claim_id"]}],
                },
            }

            config = _parse_harness_config(raw, config_dir=root, profile="local")
            self.assertEqual(config.pipeline, ("schema", "hash"))
            self.assertEqual(tuple(config.phases), ("schema", "hash"))
            self.assertEqual(config.datasets[0].name, "claims")
            self.assertEqual(config.output_reader_adapter, "sqlite")
            self.assertEqual(config.report_adapters, ("markdown",))
            self.assertEqual(config.output_root, (root / "../output").resolve())

    def test_rejects_unknown_pipeline_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            raw = {
                "etl": {
                    "working_dir": ".",
                    "baseline": {"command": "echo baseline"},
                    "candidate": {"command": "echo candidate"},
                },
                "io": {"sqlite": {"baseline_db": "baseline.db", "candidate_db": "candidate.db"}},
                "output_reader": {"adapter": "sqlite"},
                "report": {"adapters": ["markdown"], "markdown_output": "report.md"},
                "compare": {
                    "imports": [],
                    "phase_packs": [
                        {
                            "phase": {
                                "id": "schema",
                                "enabled": True,
                                "order": 100,
                                "severity": "high",
                                "config": {},
                            }
                        }
                    ],
                    "pipeline": ["schema", "hash"],
                    "datasets": [{"name": "claims", "table": "claims", "key_columns": ["claim_id"]}],
                },
            }
            with self.assertRaisesRegex(ValueError, "unknown phase ids"):
                _parse_harness_config(raw, config_dir=root, profile=None)

    def test_requires_output_reader_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            raw = {
                "etl": {
                    "working_dir": ".",
                    "baseline": {"command": "echo baseline"},
                    "candidate": {"command": "echo candidate"},
                },
                "io": {"sqlite": {"baseline_db": "baseline.db", "candidate_db": "candidate.db"}},
                "report": {"adapters": ["markdown"], "markdown_output": "report.md"},
                "compare": {
                    "phase_packs": [
                        {"phase": {"id": "schema", "enabled": True, "order": 100, "severity": "high", "config": {}}}
                    ],
                    "pipeline": ["schema"],
                    "datasets": [{"name": "claims", "table": "claims", "key_columns": ["claim_id"]}],
                },
            }
            with self.assertRaisesRegex(ValueError, "output_reader.adapter"):
                _parse_harness_config(raw, config_dir=root, profile=None)

    def test_requires_report_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            raw = {
                "etl": {
                    "working_dir": ".",
                    "baseline": {"command": "echo baseline"},
                    "candidate": {"command": "echo candidate"},
                },
                "io": {"sqlite": {"baseline_db": "baseline.db", "candidate_db": "candidate.db"}},
                "output_reader": {"adapter": "sqlite"},
                "report": {"markdown_output": "report.md"},
                "compare": {
                    "phase_packs": [
                        {"phase": {"id": "schema", "enabled": True, "order": 100, "severity": "high", "config": {}}}
                    ],
                    "pipeline": ["schema"],
                    "datasets": [{"name": "claims", "table": "claims", "key_columns": ["claim_id"]}],
                },
            }
            with self.assertRaisesRegex(ValueError, "report.adapters"):
                _parse_harness_config(raw, config_dir=root, profile=None)

    def test_honors_custom_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            raw = {
                "etl": {
                    "working_dir": ".",
                    "baseline": {"command": "echo baseline"},
                    "candidate": {"command": "echo candidate"},
                },
                "output": {"root_dir": "./custom-output"},
                "io": {"sqlite": {"baseline_db": "baseline.db", "candidate_db": "candidate.db"}},
                "output_reader": {"adapter": "sqlite"},
                "report": {"adapters": ["markdown"], "markdown_output": "report.md"},
                "compare": {
                    "phase_packs": [
                        {"phase": {"id": "schema", "enabled": True, "order": 100, "severity": "high", "config": {}}}
                    ],
                    "pipeline": ["schema"],
                    "datasets": [{"name": "claims", "table": "claims", "key_columns": ["claim_id"]}],
                },
            }
            config = _parse_harness_config(raw, config_dir=root, profile=None)
            self.assertEqual(config.output_root, (root / "custom-output").resolve())
            self.assertEqual(config.baseline_db_path, (root / "custom-output/baseline.db").resolve())


class BuiltinPhaseTests(unittest.TestCase):
    def test_schema_phase_fails_on_removed_column(self) -> None:
        phase = SchemaPhase()
        context = CompareContext(
            dataset_name="claims",
            table_name="claims",
            key_columns=("claim_id",),
            excluded_columns=(),
            baseline_rows=({"claim_id": 1, "legacy": "x"},),
            candidate_rows=({"claim_id": 1},),
            phase_config={"allow_additive_columns": False},
        )
        result = phase.run(context)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.findings[0].column, "legacy")

    def test_hash_phase_respects_excluded_columns(self) -> None:
        phase = HashPhase()
        context = CompareContext(
            dataset_name="claims",
            table_name="claims",
            key_columns=("claim_id",),
            excluded_columns=("updated_at",),
            baseline_rows=({"claim_id": 1, "amount": 100, "updated_at": "2024-01-01"},),
            candidate_rows=({"claim_id": 1, "amount": 100, "updated_at": "2024-02-01"},),
            phase_config={"exclude_columns": True},
        )
        result = phase.run(context)
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.metrics["mismatch_count"], 0)

    def test_rowdiff_phase_reports_value_change(self) -> None:
        phase = RowDiffPhase()
        context = CompareContext(
            dataset_name="claims",
            table_name="claims",
            key_columns=("claim_id",),
            excluded_columns=("updated_at",),
            baseline_rows=({"claim_id": 1, "amount": 100, "updated_at": "2024-01-01"},),
            candidate_rows=({"claim_id": 1, "amount": 125, "updated_at": "2024-02-01"},),
            phase_config={"max_findings": 10},
        )
        result = phase.run(context)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.findings[0].column, "amount")


class SQLiteOutputAdapterTests(unittest.TestCase):
    def test_loads_baseline_and_candidate_rows_for_table(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            baseline_db = root / "baseline.db"
            candidate_db = root / "candidate.db"
            _create_claims_db(baseline_db, [("C-1001", 100.0), ("C-1002", 50.0)])
            _create_claims_db(candidate_db, [("C-1001", 125.0), ("C-1002", 50.0)])

            rows = SQLiteOutputDatasetReader().load_dataset(
                baseline_db_path=baseline_db,
                candidate_db_path=candidate_db,
                table_name="claims",
            )

            self.assertEqual(len(rows.baseline_rows), 2)
            self.assertEqual(len(rows.candidate_rows), 2)
            self.assertEqual(rows.baseline_rows[0]["claim_id"], "C-1001")
            self.assertEqual(rows.candidate_rows[0]["amount"], 125.0)


def _create_claims_db(db_path: Path, rows: list[tuple[str, float]]) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE claims (claim_id TEXT PRIMARY KEY, amount REAL NOT NULL)")
        connection.executemany(
            "INSERT INTO claims (claim_id, amount) VALUES (?, ?)",
            rows,
        )
        connection.commit()


if __name__ == "__main__":
    unittest.main()
