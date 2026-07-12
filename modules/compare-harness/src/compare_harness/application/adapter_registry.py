from __future__ import annotations

from pathlib import Path

from compare_harness.adapters.markdown_report import MarkdownComparisonReportWriter
from compare_harness.adapters.sqlite_loader import SQLiteOutputDatasetReader
from compare_harness.domain.ports import ComparisonReportWriter, OutputDatasetReader

from .configuration import HarnessConfig


def create_output_reader(config: HarnessConfig) -> OutputDatasetReader:
    adapter = config.output_reader_adapter.lower()
    if adapter == "sqlite":
        return SQLiteOutputDatasetReader()
    raise ValueError(
        f"Unsupported output_reader.adapter '{config.output_reader_adapter}'. "
        "Supported adapters: sqlite"
    )


def create_report_writers(config: HarnessConfig) -> tuple[tuple[str, ComparisonReportWriter, Path], ...]:
    writers: list[tuple[str, ComparisonReportWriter, Path]] = []
    for adapter_name in config.report_adapters:
        normalized = adapter_name.lower()
        if normalized == "markdown":
            writers.append(("markdown", MarkdownComparisonReportWriter(), config.markdown_report_path))
            continue
        raise ValueError(
            f"Unsupported report adapter '{adapter_name}'. "
            "Supported adapters: markdown"
        )
    return tuple(writers)
