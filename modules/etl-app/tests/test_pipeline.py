from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from etl_app.pipeline import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_transforms_claim_output_without_variant_math_drift(self) -> None:
        fixture_root = Path(__file__).resolve().parents[1] / "data" / "raw"
        with tempfile.TemporaryDirectory() as tempdir:
            baseline_db = Path(tempdir) / "baseline.db"
            candidate_db = Path(tempdir) / "candidate.db"
            run_pipeline(variant="baseline", input_root=fixture_root, output_db=baseline_db)
            run_pipeline(variant="candidate", input_root=fixture_root, output_db=candidate_db)

            with sqlite3.connect(baseline_db) as baseline_conn, sqlite3.connect(candidate_db) as candidate_conn:
                baseline_amount = baseline_conn.execute(
                    "SELECT total_charge FROM claims WHERE claim_id = 'C-1001'"
                ).fetchone()[0]
                lines_text = baseline_conn.execute(
                    "SELECT lines FROM claims WHERE claim_id = 'C-1001'"
                ).fetchone()[0]
                diagnosis_codes_text = baseline_conn.execute(
                    "SELECT diagnosis_codes FROM claims WHERE claim_id = 'C-1001'"
                ).fetchone()[0]
                candidate_amount = candidate_conn.execute(
                    "SELECT total_charge FROM claims WHERE claim_id = 'C-1001'"
                ).fetchone()[0]

            self.assertEqual(baseline_amount, candidate_amount)
            lines = json.loads(lines_text)
            self.assertIsInstance(lines, list)
            self.assertEqual(len(lines), 2)
            diagnosis_codes = json.loads(diagnosis_codes_text)
            self.assertIsInstance(diagnosis_codes, list)
            self.assertEqual(diagnosis_codes, ["J10.1", "R05.9"])


if __name__ == "__main__":
    unittest.main()
