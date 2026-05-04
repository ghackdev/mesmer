from __future__ import annotations

from pydantic import Field

from mesmer.artifacts.messages import user_message
from mesmer.attackers.components import (
    CandidateExpander,
    CandidatePruner,
    KeywordOverlapPruner,
    TemplateCandidateExpander,
)
from mesmer.execution.state import AttackState, Attempt, Candidate
from mesmer.flows.base import AttackContext, Flow
from mesmer.flows.policies import TreeSearchPolicy
from mesmer.objectives.models import Objective
from mesmer.targets.base import TargetContext


class TreeSearchFlow(Flow):
    expander: CandidateExpander = Field(default_factory=TemplateCandidateExpander)
    pruner: CandidatePruner = Field(default_factory=KeywordOverlapPruner)
    policy: TreeSearchPolicy = Field(default_factory=TreeSearchPolicy)
    name: str = "tree_search"

    async def execute(self, objective: Objective, context: AttackContext) -> AttackState:
        context.logger.emit(
            "flow.start",
            flow=self.name,
            depth=self.policy.depth,
            branching_factor=self.policy.branching_factor,
            width=self.policy.width,
        )
        state = AttackState(objective=objective, variables=dict(objective.initial_state.variables))
        root_messages = list(objective.initial_state.messages) or [user_message(objective.goal)]
        frontier = [Candidate(messages=root_messages, metadata={"tree_depth": 0})]

        for depth_index in range(1, self.policy.depth + 1):
            context.logger.emit("tree.depth.start", depth=depth_index, frontier=len(frontier))
            context.budget_tracker.record_turn()
            expanded: list[Candidate] = []
            for candidate in frontier:
                children = await self.expander.expand(
                    objective,
                    candidate,
                    self.policy.branching_factor,
                )
                for child in children:
                    child.metadata["tree_depth"] = depth_index
                expanded.extend(children)
            context.logger.emit(
                "tree.expand.finish",
                depth=depth_index,
                expander=self.expander.name,
                candidates=len(expanded),
            )
            frontier = self.pruner.prune(objective, expanded, self.policy.width)
            context.logger.emit(
                "tree.prune.finish",
                depth=depth_index,
                pruner=self.pruner.name,
                candidates=len(frontier),
            )

            for candidate in frontier:
                prompt = candidate.messages[-1].content if candidate.messages else ""
                context.logger.emit(
                    "target.call",
                    depth=depth_index,
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
                    turn=depth_index,
                    metadata={"flow": self.name},
                )
                state.add_attempt(attempt)
                if context.recorder is not None:
                    await context.recorder.record_attempt(attempt)
                if self.policy.stop_on_success and attempt.succeeded:
                    state.metadata["stop_reason"] = "success"
                    context.logger.emit("flow.stop", reason="success")
                    return state
        state.metadata["stop_reason"] = "depth_exhausted"
        context.logger.emit("flow.stop", reason="depth_exhausted")
        return state
