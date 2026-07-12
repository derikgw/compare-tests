from __future__ import annotations

from dataclasses import replace

from compare_harness.domain.models import CompareContext, PhaseResult
from compare_harness.domain.phases import ComparePhase

from .configuration import PipelinePhaseConfig


class ComparePipeline:
    def __init__(self, phases: dict[str, ComparePhase]) -> None:
        self._phases = phases

    def run(self, context: CompareContext, *, pipeline: tuple[str, ...], configs: dict[str, PipelinePhaseConfig], fail_fast: bool) -> tuple[PhaseResult, ...]:
        results: list[PhaseResult] = []
        for phase_id in pipeline:
            config = configs[phase_id]
            if not config.enabled:
                results.append(
                    PhaseResult(
                        phase_id=phase_id,
                        status="skipped",
                        findings=(),
                        metrics={"reason": "disabled"},
                    )
                )
                continue

            phase = self._phases[phase_id]
            phase.validate_config(config.config)
            result = phase.run(replace(context, phase_config=config.config))
            results.append(result)

            if fail_fast and result.status == "failed":
                break
        return tuple(results)
