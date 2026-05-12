from __future__ import annotations

from typing import Any, Self

from pydantic import Field, field_validator

from mesmer.artifacts.messages import Message, user_message
from mesmer.artifacts.models import AnyArtifact
from mesmer.core.config import MesmerModel
from mesmer.core.ids import new_id
from mesmer.objectives.criteria import Criterion


class InitialState(MesmerModel):
    messages: list[Message] = Field(default_factory=list)
    variables: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[AnyArtifact] = Field(default_factory=list)
    conversation_id: str | None = None
    observations: list[str] = Field(default_factory=list)

    @classmethod
    def from_prompt(cls, prompt: str) -> Self:
        return cls(messages=[user_message(prompt)])

    @classmethod
    def coerce(cls, value: str | Message | list[Message] | Self | None) -> Self:
        if value is None:
            return cls()
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls.from_prompt(value)
        if isinstance(value, Message):
            return cls(messages=[value])
        return cls(messages=value)


class Objective(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("objective"))
    goal: str
    initial_state: InitialState = Field(default_factory=InitialState)
    success: list[Criterion] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("initial_state", mode="before")
    @classmethod
    def _coerce_initial_state(cls, value: Any) -> InitialState:
        return InitialState.coerce(value)

    @classmethod
    def coerce(cls, value: str | Objective) -> Objective:
        if isinstance(value, Objective):
            return value
        return Objective(goal=value)
