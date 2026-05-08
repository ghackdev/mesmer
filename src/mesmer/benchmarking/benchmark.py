from __future__ import annotations

from pydantic import Field, field_validator

from mesmer.benchmarking.metrics import AttackSuccessRate, Metric
from mesmer.core.config import MesmerModel
from mesmer.core.constants import DEFAULT_REPETITIONS
from mesmer.core.ids import new_id
from mesmer.execution.budgets import Budget
from mesmer.judging.base import Judge
from mesmer.objectives.sources import ObjectiveSource
from mesmer.targets.base import Target
from mesmer.techniques import Technique


class Benchmark(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("benchmark"))
    name: str
    objectives: ObjectiveSource
    attacks: list[Technique]
    targets: list[Target]
    judges: list[Judge] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=lambda: [AttackSuccessRate()])
    budget: Budget = Field(default_factory=Budget)
    repetitions: int = DEFAULT_REPETITIONS

    @field_validator("judges", mode="before")
    @classmethod
    def _coerce_judges(cls, value: Judge | list[Judge]) -> list[Judge]:
        if isinstance(value, list):
            return value
        return [value]
