from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from compare_harness.adapters.phases_builtin import HashPhase, RowDiffPhase, SchemaPhase
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


if __name__ == "__main__":
    unittest.main()
