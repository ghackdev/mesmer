from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.core.enums import Capability
from mesmer.execution.state import AttackState
from mesmer.objectives.models import Objective
from mesmer.telemetry.logger import NULL_LOGGER, RunLogger


class AttackContext(MesmerModel):
    target: object
    judges: list[object]
    budget_tracker: object
    policy: Any = None
    recorder: object | None = None
    logger: RunLogger = NULL_LOGGER


class Flow(MesmerModel, ABC):
    name: str
    capabilities: set[Capability] = Field(default_factory=set)

    @abstractmethod
    async def execute(self, objective: Objective, context: AttackContext) -> AttackState:
        raise NotImplementedError
