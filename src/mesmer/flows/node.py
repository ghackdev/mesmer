from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import Field

from mesmer.artifacts.messages import user_message
from mesmer.attackers.components import CandidateExpander, CandidatePruner
from mesmer.attackers.transforms import Transform
from mesmer.core.config import MesmerModel
from mesmer.execution.state import AttackState, Attempt, Candidate
from mesmer.flows.base import AttackContext, Flow
from mesmer.objectives.models import Objective
from mesmer.targets.base import TargetContext


class NodeExecutionState(MesmerModel):
    attack_state: AttackState
    frontier: list[Candidate] = Field(default_factory=list)
    stopped: bool = False


class AttackNode(MesmerModel, ABC):
    name: str

    @abstractmethod
    async def run(
        self,
        objective: Objective,
        context: AttackContext,
        state: NodeExecutionState,
    ) -> None:
        raise NotImplementedError


class SeedCandidates(AttackNode):
    name: str = "seed_candidates"

    async def run(
        self,
        objective: Objective,
        context: AttackContext,
        state: NodeExecutionState,
    ) -> None:
        messages = list(objective.initial_state.messages) or [user_message(objective.goal)]
        state.frontier = [Candidate(messages=messages, metadata={"node": self.name})]


class ApplyTransforms(AttackNode):
    transforms: list[Transform] = Field(default_factory=list)
    name: str = "apply_transforms"

    async def run(
        self,
        objective: Objective,
        context: AttackContext,
        state: NodeExecutionState,
    ) -> None:
        candidates = state.frontier
        for transform in self.transforms:
            expanded: list[Candidate] = []
            for candidate in candidates:
                expanded.extend(await transform.apply(objective, candidate))
            candidates = expanded
        state.frontier = candidates


class ExpandCandidates(AttackNode):
    expander: CandidateExpander
    branching_factor: int
    name: str = "expand_candidates"

    async def run(
        self,
        objective: Objective,
        context: AttackContext,
        state: NodeExecutionState,
    ) -> None:
        expanded: list[Candidate] = []
        for candidate in state.frontier:
            expanded.extend(await self.expander.expand(objective, candidate, self.branching_factor))
        state.frontier = expanded


class PruneCandidates(AttackNode):
    pruner: CandidatePruner
    width: int
    name: str = "prune_candidates"

    async def run(
        self,
        objective: Objective,
        context: AttackContext,
        state: NodeExecutionState,
    ) -> None:
        state.frontier = self.pruner.prune(objective, state.frontier, self.width)


class CallTarget(AttackNode):
    stop_on_success: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)
    name: str = "call_target"

    async def run(
        self,
        objective: Objective,
        context: AttackContext,
        state: NodeExecutionState,
    ) -> None:
        for candidate in state.frontier:
            context.budget_tracker.record_query()
            response = await context.target.call(
                candidate.messages,
                TargetContext(objective=objective, variables=state.attack_state.variables),
            )
            judgements = [await judge.judge(objective, response) for judge in context.judges]
            attempt = Attempt(
                objective=objective,
                candidate=candidate,
                response=response,
                judgements=judgements,
                turn=len(state.attack_state.attempts) + 1,
                metadata=dict(self.metadata),
            )
            state.attack_state.add_attempt(attempt)
            if context.recorder is not None:
                await context.recorder.record_attempt(attempt)
            if self.stop_on_success and attempt.succeeded:
                state.stopped = True
                state.attack_state.metadata["stop_reason"] = "success"
                return


class Repeat(AttackNode):
    times: int
    steps: list[AttackNode]
    stop_on_success: bool = True
    name: str = "repeat"

    async def run(
        self,
        objective: Objective,
        context: AttackContext,
        state: NodeExecutionState,
    ) -> None:
        for index in range(self.times):
            if state.stopped:
                return
            context.budget_tracker.record_turn()
            state.attack_state.metadata["repeat_index"] = index
            for step in self.steps:
                if state.stopped and self.stop_on_success:
                    return
                await step.run(objective, context, state)


class NodeFlow(Flow):
    steps: list[AttackNode]
    name: str = "node_flow"

    async def execute(self, objective: Objective, context: AttackContext) -> AttackState:
        context.logger.emit("flow.start", flow=self.name, steps=len(self.steps))
        attack_state = AttackState(
            objective=objective,
            variables=dict(objective.initial_state.variables),
        )
        node_state = NodeExecutionState(attack_state=attack_state)
        for step in self.steps:
            if node_state.stopped:
                break
            context.logger.emit("node.start", node=step.name)
            await step.run(objective, context, node_state)
            context.logger.emit("node.finish", node=step.name, stopped=node_state.stopped)
        if "stop_reason" not in attack_state.metadata:
            attack_state.metadata["stop_reason"] = "node_flow_exhausted"
        context.logger.emit("flow.stop", reason=attack_state.metadata["stop_reason"])
        return attack_state


AttackGraph = NodeFlow
