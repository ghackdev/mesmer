from __future__ import annotations

from typing import Any

from pydantic import Field

from mesmer.artifacts.messages import Message
from mesmer.core.config import MesmerModel
from mesmer.core.ids import new_id
from mesmer.judging.base import Judgement
from mesmer.objectives.models import Objective
from mesmer.targets.base import TargetResponse


class Candidate(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("candidate"))
    messages: list[Message]
    metadata: dict[str, Any] = Field(default_factory=dict)


class Attempt(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("attempt"))
    objective: Objective
    candidate: Candidate
    response: TargetResponse
    judgements: list[Judgement]
    turn: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        return any(judgement.status.value == "pass" for judgement in self.judgements)


class ConversationState(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("conversation"))
    messages: list[Message] = Field(default_factory=list)
    attempts: list[Attempt] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AttackState(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("attack"))
    objective: Objective
    conversations: list[ConversationState] = Field(default_factory=list)
    attempts: list[Attempt] = Field(default_factory=list)
    variables: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_attempt(self, attempt: Attempt) -> None:
        self.attempts.append(attempt)
