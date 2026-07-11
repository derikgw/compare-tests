from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

DEFAULT_BASELINE_REF = "main"


@dataclass(frozen=True)
class CompareConfig:
    dataset_name: str
    key_columns: tuple[str, ...]
    excluded_columns: tuple[str, ...] = ()
    baseline_ref: str = DEFAULT_BASELINE_REF

    @classmethod
    def from_mapping(cls, source: Mapping[str, Any]) -> "CompareConfig":
        dataset_name = str(source["dataset_name"])
        key_columns = tuple(str(value) for value in source["key_columns"])
        excluded_columns = tuple(str(value) for value in source.get("excluded_columns", ()))
        baseline_ref = str(source.get("baseline_ref") or DEFAULT_BASELINE_REF)
        return cls(
            dataset_name=dataset_name,
            key_columns=key_columns,
            excluded_columns=excluded_columns,
            baseline_ref=baseline_ref,
        )


def load_compare_config(source: Mapping[str, Any]) -> CompareConfig:
    return CompareConfig.from_mapping(source)
