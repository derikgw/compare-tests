from __future__ import annotations

from typing import Protocol

from .models import CompareContext, PhaseResult


class ComparePhase(Protocol):
    id: str

    def validate_config(self, config: dict[str, object]) -> None:
        ...

    def run(self, context: CompareContext) -> PhaseResult:
        ...
