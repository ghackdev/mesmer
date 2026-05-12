from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from mesmer.artifacts.messages import Message
from mesmer.core.config import MesmerModel
from mesmer.core.enums import Capability
from mesmer.core.ids import new_id
from mesmer.objectives.models import Objective


class TargetResponse(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("response"))
    text: str
    raw: Any = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float | None = None
    cost: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    finish_reason: str | None = None
    target_error: str | None = None
    error_type: str | None = None
    recoverable: bool = False


class TargetContext(MesmerModel):
    objective: Objective
    variables: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Target(MesmerModel, ABC):
    name: str
    capabilities: set[Capability] = Field(default_factory=set)

    @abstractmethod
    async def call(self, messages: list[Message], context: TargetContext) -> TargetResponse:
        raise NotImplementedError
