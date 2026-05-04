from __future__ import annotations

from pydantic import Field, field_validator

from mesmer.core.config import MesmerModel
from mesmer.core.ids import new_id
from mesmer.execution.budgets import Budget
from mesmer.flows.base import Flow
from mesmer.judging.base import Judge
from mesmer.objectives.sources import ObjectiveSource
from mesmer.storage.recorder import MemoryRecorder, Recorder
from mesmer.targets.base import Target


class Run(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("run"))
    objectives: ObjectiveSource
    attack: Flow
    target: Target
    judges: list[Judge]
    budget: Budget = Field(default_factory=Budget)
    recorder: Recorder = Field(default_factory=MemoryRecorder)
    metadata: dict[str, str] = Field(default_factory=dict)

    def __init__(self, **data: object) -> None:
        if "attacker" in data and "attack" not in data:
            data["attack"] = data.pop("attacker")
        if "judge" in data and "judges" not in data:
            data["judges"] = data.pop("judge")
        super().__init__(**data)

    @field_validator("judges", mode="before")
    @classmethod
    def _coerce_judges(cls, value: Judge | list[Judge]) -> list[Judge]:
        if isinstance(value, list):
            return value
        return [value]
