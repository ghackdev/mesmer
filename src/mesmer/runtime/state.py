from __future__ import annotations

from typing import Any

from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.core.constants import SUCCESS_TERMINATION_REASON
from mesmer.core.enums import JudgementStatus, StateFact
from mesmer.execution.state import AttackState, Attempt
from mesmer.judging.base import Judgement
from mesmer.objectives.models import Objective


class StatePatch(MesmerModel):
    frontier: list[Any] | None = None
    append_attempts: list[Attempt] = Field(default_factory=list)
    provided: set[StateFact] = Field(default_factory=set)
    stop_reason: str | None = None
    success_trajectory_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "provided": sorted(fact.value for fact in self.provided),
        }
        if self.frontier is not None:
            payload["frontier_count"] = len(self.frontier)
            payload["frontier"] = [_summarize_item(item) for item in self.frontier[:5]]
        if self.append_attempts:
            payload["append_attempts_count"] = len(self.append_attempts)
            payload["append_attempt_ids"] = [attempt.id for attempt in self.append_attempts]
        if self.stop_reason is not None:
            payload["stop_reason"] = self.stop_reason
        if self.success_trajectory_id is not None:
            payload["success_trajectory_id"] = self.success_trajectory_id
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


class RuntimeInternalState(MesmerModel):
    stopped: bool = False
    stop_reason: str | None = None


class StateSnapshot(MesmerModel):
    state_type: str
    iteration: int
    frontier_count: int
    frontier: list[dict[str, Any]] = Field(default_factory=list)
    attempts_count: int
    target_calls: int
    best: dict[str, Any] | None = None
    provided: list[str] = Field(default_factory=list)
    internal: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_state(cls, state: RuntimeState) -> StateSnapshot:
        return cls(
            state_type=state.__class__.__name__,
            iteration=state.iteration,
            frontier_count=len(state.frontier),
            frontier=[_summarize_item(item) for item in state.frontier[:5]],
            attempts_count=len(state.attack_state.attempts),
            target_calls=state.target_calls,
            best=_summarize_item(state.best) if state.best is not None else None,
            provided=sorted(fact.value for fact in state.provided),
            internal={
                "stopped": state.stopped,
                "stop_reason": state.stop_reason,
            },
        )


class StateTransition(MesmerModel):
    component: str
    before: StateSnapshot
    patch: dict[str, Any]
    after: StateSnapshot


class RuntimeState(MesmerModel):
    objective: Objective
    attack_state: AttackState
    frontier: list[Any] = Field(default_factory=list)
    iteration: int = 0
    target_calls: int = 0
    best: Any = None
    internal: RuntimeInternalState = Field(default_factory=RuntimeInternalState)
    provided: set[StateFact] = Field(default_factory=lambda: {StateFact.OBJECTIVE})
    metadata: dict[str, Any] = Field(default_factory=dict)
    history: list[StateTransition] = Field(default_factory=list)

    @classmethod
    def for_objective(cls, objective: Objective) -> RuntimeState:
        return cls(
            objective=objective,
            attack_state=AttackState(
                objective=objective,
                variables=dict(objective.initial_state.variables),
            ),
        )

    def apply_patch(self, patch: StatePatch) -> None:
        if patch.frontier is not None:
            self.frontier = patch.frontier
            self.provided.add(StateFact.FRONTIER)
        for attempt in patch.append_attempts:
            self.attack_state.add_attempt(attempt)
        if patch.append_attempts:
            self.provided.add(StateFact.ATTEMPTS)
        if patch.success_trajectory_id is not None:
            self._mark_attempt_success(patch.success_trajectory_id)
        if patch.stop_reason is not None:
            self.internal.stopped = True
            self.internal.stop_reason = patch.stop_reason
            self.attack_state.metadata["stop_reason"] = patch.stop_reason
            self.provided.add(StateFact.STOP_SIGNAL)
        self.provided.update(patch.provided)
        self.metadata.update(patch.metadata)
        self.attack_state.metadata.update(patch.metadata)

    def record_transition(
        self,
        component: str,
        before: StateSnapshot,
        patch: StatePatch,
        after: StateSnapshot,
    ) -> None:
        self.history.append(
            StateTransition(
                component=component,
                before=before,
                patch=patch.summary(),
                after=after,
            )
        )

    def observe(self, trajectory: Any) -> None:
        score = getattr(trajectory, "best_score", 0.0)
        best_score = getattr(self.best, "best_score", 0.0) if self.best is not None else 0.0
        if self.best is None or score > best_score:
            self.best = trajectory

    @property
    def stopped(self) -> bool:
        return self.internal.stopped

    @property
    def stop_reason(self) -> str | None:
        return self.internal.stop_reason

    def _mark_attempt_success(self, trajectory_id: str) -> None:
        for attempt in reversed(self.attack_state.attempts):
            if attempt.metadata.get("trajectory_id") != trajectory_id:
                continue
            if attempt.judgements:
                attempt.judgements[0].status = JudgementStatus.PASS
                attempt.judgements[0].metadata["stop_reason"] = SUCCESS_TERMINATION_REASON
            else:
                attempt.judgements.append(
                    Judgement(
                        status=JudgementStatus.PASS,
                        score=1.0,
                        reason=SUCCESS_TERMINATION_REASON,
                    )
                )
            return


def _summarize_item(item: Any) -> dict[str, Any]:
    if item is None:
        return {}
    candidate = getattr(item, "candidate", None)
    messages = getattr(candidate, "messages", []) if candidate is not None else []
    latest_text = ""
    if messages:
        latest_text = str(messages[-1].content)
    return {
        "id": str(getattr(item, "id", "")),
        "candidate_id": str(getattr(candidate, "id", "")) if candidate is not None else "",
        "depth": getattr(item, "depth", None),
        "score": getattr(item, "best_score", None),
        "text": _truncate(latest_text),
        "constraints": len(getattr(item, "constraints", []) or []),
        "evaluations": len(getattr(item, "evaluations", []) or []),
        "feedback": len(getattr(item, "feedback", []) or []),
    }


def _truncate(value: str, max_chars: int = 160) -> str:
    collapsed = value.replace("\n", "\\n")
    if len(collapsed) <= max_chars:
        return collapsed
    return collapsed[:max_chars] + "...[truncated]"
