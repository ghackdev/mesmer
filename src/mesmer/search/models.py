from __future__ import annotations

from typing import Any

from pydantic import Field

from mesmer.artifacts.messages import Message
from mesmer.core.config import MesmerModel
from mesmer.core.ids import new_id
from mesmer.execution.state import Candidate
from mesmer.targets.base import TargetResponse


class SearchPolicy(MesmerModel):
    iterations: int = Field(default=3, ge=1)
    branching_factor: int = Field(default=3, ge=1)
    width: int = Field(default=2, ge=1)
    max_parallel: int = Field(default=1, ge=1)
    stop_on_success: bool = True


class RatingScale(MesmerModel):
    min: float = 1.0
    max: float = 10.0

    def normalize(self, score: float) -> float:
        if self.max <= self.min:
            return 0.0
        return max(0.0, min(1.0, (score - self.min) / (self.max - self.min)))


class ConstraintResult(MesmerModel):
    passed: bool
    label: str | None = None
    reason: str = ""
    raw: Any = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(MesmerModel):
    name: str
    score: float
    normalized_score: float = Field(ge=0.0, le=1.0)
    passed: bool | None = None
    reason: str = ""
    label: str | None = None
    raw: Any = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CandidateTrajectory(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("trajectory"))
    candidate: Candidate
    depth: int = 0
    parent_id: str | None = None
    actor_history: list[Message] = Field(default_factory=list)
    last_response: TargetResponse | None = None
    constraints: list[ConstraintResult] = Field(default_factory=list)
    evaluations: list[EvaluationResult] = Field(default_factory=list)
    feedback: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def latest_text(self) -> str:
        if not self.candidate.messages:
            return ""
        return self.candidate.messages[-1].content

    @property
    def best_score(self) -> float:
        return max((evaluation.score for evaluation in self.evaluations), default=0.0)

    @property
    def best_normalized_score(self) -> float:
        return max(
            (evaluation.normalized_score for evaluation in self.evaluations),
            default=0.0,
        )
