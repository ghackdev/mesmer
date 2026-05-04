from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.core.enums import JudgementStatus
from mesmer.core.ids import new_id
from mesmer.objectives.criteria import CriterionResult
from mesmer.objectives.models import Objective
from mesmer.targets.base import TargetResponse


class Judgement(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("judgement"))
    status: JudgementStatus
    score: float = Field(ge=0.0, le=1.0)
    reason: str = ""
    criterion_results: list[CriterionResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Judge(MesmerModel, ABC):
    name: str

    @abstractmethod
    async def judge(self, objective: Objective, response: TargetResponse) -> Judgement:
        raise NotImplementedError
