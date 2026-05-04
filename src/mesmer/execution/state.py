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


class ReproductionTarget(MesmerModel):
    name: str
    model: str | None = None
    system_prompt: str | None = None


class ReproductionArtifact(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("reproduction"))
    objective: Objective
    attempt_id: str
    candidate_id: str
    response_id: str
    turn: int
    target: ReproductionTarget
    messages: list[Message]
    score: float | None = None
    normalized_score: float | None = None
    reason: str = ""
    judgement: Judgement | None = None
    trace: dict[str, Any] = Field(default_factory=dict)


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
