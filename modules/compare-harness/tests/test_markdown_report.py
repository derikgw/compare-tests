from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from compare_harness.adapters.markdown_report import MarkdownComparisonReportWriter
from compare_harness.domain.models import (
    CompareRunResult,
    DatasetComparisonResult,
    PhaseResult,
    ValueColumnComparison,
    ValueRowComparison,
)


class MarkdownReportWriterTests(unittest.TestCase):
    def test_writes_color_coded_markdown(self) -> None:
        run_result = CompareRunResult(
            baseline_ref="ETL_APP_V0.1.0",
            candidate_ref="workspace",
            datasets=(
                DatasetComparisonResult(
                    dataset_name="claims",
                    table_name="claims",
                    phase_results=(
                        PhaseResult(phase_id="schema", status="failed", findings=(), metrics={}),
                    ),
                    value_rows=(
                        ValueRowComparison(
                            status="changed",
                            key={"claim_id": "C-1001"},
                            columns=(
                                ValueColumnComparison(
                                    column_name="total_charge",
                                    status="changed",
                                    baseline_value=157.5,
                                    candidate_value=159.07,
                                ),
                                ValueColumnComparison(
                                    column_name="updated_at",
                                    status="excluded",
                                    baseline_value="2026-07-10",
                                    candidate_value="2026-07-11",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            report_artifacts={},
        )

        with tempfile.TemporaryDirectory() as tempdir:
            output_path = Path(tempdir) / "report.md"
            MarkdownComparisonReportWriter().write(run_result=run_result, output_path=output_path)
            report = output_path.read_text(encoding="utf-8")

        self.assertIn("Compare Report", report)
        self.assertIn("color: #c62828", report)
        self.assertIn("different", report)
        self.assertIn("excluded", report)
        self.assertIn("total_charge", report)


if __name__ == "__main__":
    unittest.main()
