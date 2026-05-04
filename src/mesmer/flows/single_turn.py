from __future__ import annotations

from pydantic import Field

from mesmer.artifacts.messages import user_message
from mesmer.attackers.transforms import Transform
from mesmer.execution.state import AttackState, Attempt, Candidate
from mesmer.flows.base import AttackContext, Flow
from mesmer.objectives.models import Objective
from mesmer.targets.base import TargetContext


class SingleTurnFlow(Flow):
    transforms: list[Transform] = Field(default_factory=list)
    stop_on_success: bool = True
    name: str = "single_turn"

    async def execute(self, objective: Objective, context: AttackContext) -> AttackState:
        context.logger.emit("flow.start", flow=self.name)
        state = AttackState(objective=objective, variables=dict(objective.initial_state.variables))
        messages = list(objective.initial_state.messages) or [user_message(objective.goal)]
        candidates = [Candidate(messages=messages)]
        context.logger.emit(
            "attacker.seed",
            candidates=len(candidates),
            message=self._candidate_message(candidates[0]),
        )
        for transform in self.transforms:
            context.logger.emit(
                "transform.start",
                transform=transform.name,
                candidates=len(candidates),
            )
            expanded: list[Candidate] = []
            for candidate in candidates:
                context.logger.emit(
                    "transform.input",
                    transform=transform.name,
                    candidate_id=candidate.id,
                    message=self._candidate_message(candidate),
                )
                children = await transform.apply(objective, candidate)
                for child in children:
                    context.logger.emit(
                        "transform.output",
                        transform=transform.name,
                        candidate_id=child.id,
                        message=self._candidate_message(child),
                    )
                expanded.extend(children)
            candidates = expanded
            context.logger.emit(
                "transform.finish",
                transform=transform.name,
                candidates=len(candidates),
            )
        for candidate in candidates:
            prompt = candidate.messages[-1].content if candidate.messages else ""
            context.logger.emit(
                "target.call",
                candidate_id=candidate.id,
                message=prompt,
            )
            context.budget_tracker.record_query()
            response = await context.target.call(
                candidate.messages,
                TargetContext(objective=objective, variables=state.variables),
            )
            context.logger.emit(
                "target.response",
                response_id=response.id,
                text=response.text,
                latency_ms=response.latency_ms,
            )
            judgements = [await judge.judge(objective, response) for judge in context.judges]
            for judgement in judgements:
                context.logger.emit(
                    "judge.result",
                    status=judgement.status.value,
                    score=judgement.score,
                    reason=judgement.reason,
                )
            attempt = Attempt(
                objective=objective,
                candidate=candidate,
                response=response,
                judgements=judgements,
            )
            state.add_attempt(attempt)
            if context.recorder is not None:
                await context.recorder.record_attempt(attempt)
            if self.stop_on_success and attempt.succeeded:
                state.metadata["stop_reason"] = "success"
                context.logger.emit("flow.stop", reason="success")
                return state
        state.metadata["stop_reason"] = "flow_exhausted"
        context.logger.emit("flow.stop", reason="flow_exhausted")
        return state

    def _candidate_message(self, candidate: Candidate) -> str:
        return candidate.messages[-1].content if candidate.messages else ""
