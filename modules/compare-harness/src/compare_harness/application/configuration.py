from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os
import subprocess

import yaml
from sprigconfig import load_config


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    table: str
    key_columns: tuple[str, ...]
    excluded_columns: tuple[str, ...]


@dataclass(frozen=True)
class PipelinePhaseConfig:
    id: str
    enabled: bool
    order: int
    severity: str
    config: dict[str, Any]


@dataclass(frozen=True)
class HarnessConfig:
    repository_root: Path
    config_dir: Path
    profile: str | None
    baseline_ref: str
    candidate_ref: str
    baseline_working_subpath: Path
    baseline_checkout_dir: Path
    baseline_db_path: Path
    candidate_db_path: Path
    etl_working_dir: Path
    baseline_command: str
    candidate_command: str
    fail_fast: bool
    datasets: tuple[DatasetConfig, ...]
    pipeline: tuple[str, ...]
    phases: dict[str, PipelinePhaseConfig]


def resolve_config_dir(config_dir: str | Path | None) -> Path:
    if config_dir is not None:
        return Path(config_dir).resolve()
    if "APP_CONFIG_DIR" in os.environ:
        return Path(os.environ["APP_CONFIG_DIR"]).resolve()
    return Path.cwd() / "config"


def load_harness_config(*, config_dir: str | Path | None = None, profile: str | None = None) -> HarnessConfig:
    resolved_dir = resolve_config_dir(config_dir)
    loaded_raw = load_config(config_dir=str(resolved_dir), profile=profile)
    if hasattr(loaded_raw, "to_dict"):
        loaded = loaded_raw.to_dict()
    elif isinstance(loaded_raw, dict):
        loaded = loaded_raw
    else:
        raise ValueError("sprig-config load_config() returned an unsupported config type.")
    return _parse_harness_config(loaded, config_dir=resolved_dir, profile=profile)


def _parse_harness_config(raw: dict[str, Any], *, config_dir: Path, profile: str | None) -> HarnessConfig:
    etl = _as_dict(raw.get("etl"), "etl")
    compare = _as_dict(raw.get("compare"), "compare")
    io = _as_dict(raw.get("io"), "io")
    sqlite = _as_dict(io.get("sqlite"), "io.sqlite")

    dataset_specs = tuple(_parse_dataset_config(item) for item in _as_list(compare.get("datasets"), "compare.datasets"))
    imports = _resolve_phase_import_paths(raw, compare, config_dir)
    imported_phases = _load_imported_phase_configs(imports)
    inline_phases = _parse_inline_phases(_as_list(compare.get("phase_packs", []), "compare.phase_packs"))
    phases = _merge_phase_configs(imported_phases, inline_phases)

    pipeline = tuple(str(item) for item in _as_list(compare.get("pipeline"), "compare.pipeline"))
    _validate_pipeline(pipeline, phases)

    repository_root = _resolve_repository_root(config_dir)
    return HarnessConfig(
        repository_root=repository_root,
        config_dir=config_dir,
        profile=profile,
        baseline_ref=str(etl.get("baseline_ref", "main")),
        candidate_ref=str(etl.get("candidate_ref", "workspace")),
        baseline_working_subpath=Path(str(etl.get("baseline_working_subpath", "modules/etl-app"))),
        baseline_checkout_dir=(config_dir / str(etl.get("baseline_checkout_dir", "./runs/worktrees/baseline-repo"))).resolve(),
        baseline_db_path=(config_dir / str(sqlite["baseline_db"])).resolve(),
        candidate_db_path=(config_dir / str(sqlite["candidate_db"])).resolve(),
        etl_working_dir=(config_dir / str(etl["working_dir"])).resolve(),
        baseline_command=str(_as_dict(etl.get("baseline"), "etl.baseline")["command"]),
        candidate_command=str(_as_dict(etl.get("candidate"), "etl.candidate")["command"]),
        fail_fast=bool(compare.get("fail_fast", False)),
        datasets=dataset_specs,
        pipeline=pipeline,
        phases=phases,
    )


def _parse_dataset_config(raw: Any) -> DatasetConfig:
    values = _as_dict(raw, "compare.datasets[]")
    return DatasetConfig(
        name=str(values["name"]),
        table=str(values["table"]),
        key_columns=tuple(str(value) for value in _as_list(values["key_columns"], "compare.datasets[].key_columns")),
        excluded_columns=tuple(
            str(value) for value in _as_list(values.get("excluded_columns", []), "compare.datasets[].excluded_columns")
        ),
    )


def _parse_phase_pack(raw: dict[str, Any]) -> PipelinePhaseConfig:
    phase = _as_dict(raw.get("phase"), "phase")
    return PipelinePhaseConfig(
        id=str(phase["id"]),
        enabled=bool(phase.get("enabled", True)),
        order=int(phase.get("order", 0)),
        severity=str(phase.get("severity", "medium")),
        config=dict(_as_dict(phase.get("config", {}), "phase.config")),
    )


def _parse_inline_phases(raw: list[Any]) -> dict[str, PipelinePhaseConfig]:
    parsed = [_parse_phase_pack(_as_dict(item, "compare.phase_packs[]")) for item in raw]
    return _ensure_unique_phase_ids(parsed)


def _resolve_phase_import_paths(raw: dict[str, Any], compare: dict[str, Any], config_dir: Path) -> tuple[Path, ...]:
    phase_imports = compare.get("phase_imports")
    if isinstance(phase_imports, list):
        return tuple((config_dir / str(relative_path)).resolve() for relative_path in phase_imports)
    if isinstance(compare.get("imports"), list):
        return tuple((config_dir / str(relative_path)).resolve() for relative_path in compare["imports"])

    metadata = _as_dict(raw.get("sprigconfig", {}), "sprigconfig")
    meta = _as_dict(metadata.get("_meta", {}), "sprigconfig._meta")
    trace = _as_list(meta.get("import_trace", []), "sprigconfig._meta.import_trace")
    discovered: list[Path] = []
    for item in trace:
        value = _as_dict(item, "sprigconfig._meta.import_trace[]")
        imported_file = value.get("file")
        if not isinstance(imported_file, str):
            continue
        if "/compare/phases/" not in imported_file.replace("\\", "/"):
            continue
        discovered.append(Path(imported_file).resolve())
    return tuple(discovered)


def _load_imported_phase_configs(imports: tuple[Path, ...]) -> dict[str, PipelinePhaseConfig]:
    parsed: list[PipelinePhaseConfig] = []
    for resolved_path in imports:
        if not resolved_path.is_file():
            raise ValueError(f"compare.imports includes missing file: {resolved_path}")
        with resolved_path.open("r", encoding="utf-8") as stream:
            loaded = yaml.safe_load(stream)
        parsed.append(_parse_phase_pack(_as_dict(loaded, f"phase import: {resolved_path}")))
    return _ensure_unique_phase_ids(parsed)


def _merge_phase_configs(
    imported: dict[str, PipelinePhaseConfig], inline: dict[str, PipelinePhaseConfig]
) -> dict[str, PipelinePhaseConfig]:
    merged = dict(imported)
    for phase_id, value in inline.items():
        merged[phase_id] = value
    return merged


def _validate_pipeline(pipeline: tuple[str, ...], phases: dict[str, PipelinePhaseConfig]) -> None:
    if not pipeline:
        raise ValueError("compare.pipeline must include at least one phase.")
    unknown = [phase_id for phase_id in pipeline if phase_id not in phases]
    if unknown:
        joined = ", ".join(unknown)
        raise ValueError(f"compare.pipeline references unknown phase ids: {joined}")


def _ensure_unique_phase_ids(phases: list[PipelinePhaseConfig]) -> dict[str, PipelinePhaseConfig]:
    by_id: dict[str, PipelinePhaseConfig] = {}
    for phase in phases:
        if phase.id in by_id:
            raise ValueError(f"Duplicate phase id detected: {phase.id}")
        by_id[phase.id] = phase
    return by_id


def _as_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping.")
    return value


def _as_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list.")
    return value


def _resolve_repository_root(config_dir: Path) -> Path:
    for probe_dir in (config_dir, Path.cwd()):
        result = subprocess.run(
            ["git", "-C", str(probe_dir), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).resolve()
    return config_dir.resolve()
