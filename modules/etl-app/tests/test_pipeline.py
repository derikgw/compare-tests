from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from etl_app.pipeline import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_candidate_variant_changes_total_charge(self) -> None:
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
                candidate_amount = candidate_conn.execute(
                    "SELECT total_charge FROM claims WHERE claim_id = 'C-1001'"
                ).fetchone()[0]

            self.assertNotEqual(baseline_amount, candidate_amount)


if __name__ == "__main__":
    unittest.main()
