from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.core.constants import DEFAULT_TECHNIQUE_STOP_REASON
from mesmer.core.errors import ConfigError
from mesmer.execution.context import AttackContext
from mesmer.execution.state import AttackState
from mesmer.objectives.models import Objective
from mesmer.ops import (
    AssignReward,
    ContinueConversation,
    GenerateFromPopulation,
    Propose,
    QueryTarget,
    SeedFromObjective,
    Select,
)
from mesmer.state import Metadata, Patch, State, StateSlice, StopSignal
from mesmer.trajectory import BranchingPolicy
from mesmer.workflow import Loop, Operator, Sequence, Workflow


class Technique(MesmerModel, ABC):
    name: str
    capabilities: set[Any] = Field(default_factory=set)

    @abstractmethod
    def workflow(self) -> Workflow:
        raise NotImplementedError

    def state_schema(self) -> set[type[StateSlice]]:
        return self.workflow().required_slices()

    def workflow_graph(self) -> list[str]:
        return [operator.name for operator in self.workflow().operators()]

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "technique": self.__class__.__name__,
            "state": sorted(slice_type.__name__ for slice_type in self.state_schema()),
            "workflow": self.workflow_graph(),
            "capabilities": sorted(self.workflow().required_capabilities()),
        }

    async def execute(self, objective: Objective, context: AttackContext) -> AttackState:
        workflow = self.workflow()
        schema = self.state_schema()
        state = State.for_objective(objective, schema)
        workflow.validate(set(state.slices))
        context.logger.emit(
            "technique.start",
            technique=self.name,
            workflow=self.workflow_graph(),
        )
        state.apply_patch(
            Patch.set(
                Metadata(values={"stop_reason": DEFAULT_TECHNIQUE_STOP_REASON}),
            )
        )
        await workflow.run(state, self._context(context))
        if not state.get(StopSignal).reason:
            state.apply_patch(Patch(metadata={"stop_reason": DEFAULT_TECHNIQUE_STOP_REASON}))
        context.logger.emit(
            "technique.stop",
            technique=self.name,
            reason=state.attack_state.metadata.get("stop_reason", DEFAULT_TECHNIQUE_STOP_REASON),
        )
        return state.to_attack_state()

    def _context(self, context: AttackContext) -> AttackContext:
        return context


class FrontierSearch(Technique):
    name: str = "frontier_search"
    iterations: int = Field(default=3, ge=1)
    branching: int = Field(default=3, ge=1)
    width: int = Field(default=2, ge=1)
    max_parallel: int = Field(default=1, ge=1)
    stop_on_success: bool = True
    seed: Operator = Field(default_factory=SeedFromObjective)
    pre_expand: list[Operator] = Field(default_factory=list)
    expand: Operator
    pre_query: list[Operator] = Field(default_factory=list)
    query: Operator = Field(default_factory=QueryTarget)
    post_query: list[Operator] = Field(default_factory=list)
    evaluate: Operator
    post_evaluate: list[Operator] = Field(default_factory=list)
    stop: Operator
    select: Operator = Field(default_factory=Select)
    feedback: Operator | None = None

    def model_post_init(self, __context: Any) -> None:
        self._validate_search_shape()

    def _validate_search_shape(self) -> None:
        if self.iterations == 1 and self.branching == 1 and self.width == 1:
            raise ConfigError(
                "FrontierSearch with iterations=1, branching=1, and width=1 is a "
                "single-turn probe, not a frontier search. Use "
                "techniques.SingleTurnProbe for one-shot checks, or increase branching "
                "or iterations for search."
            )

    def workflow(self) -> Workflow:
        self._validate_search_shape()
        body: list[Operator] = [
            *self.pre_expand,
            self.expand,
            *self.pre_query,
            self.query,
            *self.post_query,
            self.evaluate,
            *self.post_evaluate,
            self.stop,
        ]
        if self.feedback is not None:
            body.append(self.feedback)
        body.append(self.select)
        return Sequence(
            steps=[
                self.seed,
                Loop(
                    body=body,
                    max_iterations=self.iterations,
                ),
            ],
        )

    def _context(self, context: AttackContext) -> AttackContext:
        return context.model_copy(
            update={
                "policy": BranchingPolicy(
                    iterations=self.iterations,
                    branching_factor=self.branching,
                    width=self.width,
                    max_parallel=self.max_parallel,
                    stop_on_success=self.stop_on_success,
                )
            }
        )


class ElicitationSearch(Technique):
    name: str = "elicitation_search"
    iterations: int = Field(default=3, ge=1)
    branching: int = Field(default=2, ge=1)
    width: int = Field(default=2, ge=1)
    max_parallel: int = Field(default=1, ge=1)
    stop_on_success: bool = False
    seed: Operator = Field(default_factory=SeedFromObjective)
    pre_expand: list[Operator] = Field(default_factory=list)
    expand: Operator
    pre_query: list[Operator] = Field(default_factory=list)
    query: Operator = Field(default_factory=QueryTarget)
    post_query: list[Operator] = Field(default_factory=list)
    extract: Operator
    post_extract: list[Operator] = Field(default_factory=list)
    evaluate: Operator | None = None
    post_evaluate: list[Operator] = Field(default_factory=list)
    synthesize: Operator
    feedback: Operator | None = None
    select: Operator | None = None
    stop: Operator | None = None

    def workflow(self) -> Workflow:
        body: list[Operator] = [
            *self.pre_expand,
            self.expand,
            *self.pre_query,
            self.query,
            *self.post_query,
            self.extract,
            *self.post_extract,
        ]
        if self.evaluate is not None:
            body.append(self.evaluate)
            body.extend(self.post_evaluate)
        body.append(self.synthesize)
        if self.stop is not None:
            body.append(self.stop)
        if self.feedback is not None:
            body.append(self.feedback)
        if self.select is not None:
            body.append(self.select)
        return Sequence(
            steps=[
                self.seed,
                Loop(
                    body=body,
                    max_iterations=self.iterations,
                ),
            ],
        )

    def _context(self, context: AttackContext) -> AttackContext:
        return context.model_copy(
            update={
                "policy": BranchingPolicy(
                    iterations=self.iterations,
                    branching_factor=self.branching,
                    width=self.width,
                    max_parallel=self.max_parallel,
                    stop_on_success=self.stop_on_success,
                )
            }
        )


class Probe(Technique):
    name: str = "probe"
    seed: Operator = Field(default_factory=SeedFromObjective)
    prepare: list[Operator] = Field(default_factory=list)
    query: Operator = Field(default_factory=QueryTarget)
    evaluate: Operator
    stop: Operator | None = None
    max_parallel: int = Field(default=1, ge=1)
    stop_on_success: bool = True

    def workflow(self) -> Workflow:
        steps: list[Operator] = [self.seed, *self.prepare, self.query, self.evaluate]
        if self.stop is not None:
            steps.append(self.stop)
        return Sequence(steps=steps)

    def _context(self, context: AttackContext) -> AttackContext:
        return context.model_copy(
            update={
                "policy": BranchingPolicy(
                    iterations=1,
                    branching_factor=1,
                    width=1,
                    max_parallel=self.max_parallel,
                    stop_on_success=self.stop_on_success,
                )
            }
        )


class SingleTurnProbe(Technique):
    name: str = "single_turn_probe"
    query: Operator = Field(default_factory=QueryTarget)
    evaluate: Operator
    stop: Operator | None = None

    def workflow(self) -> Workflow:
        steps: list[Operator] = [SeedFromObjective(), self.query, self.evaluate]
        if self.stop is not None:
            steps.append(self.stop)
        return Sequence(steps=steps)


class ProposedProbe(Technique):
    name: str = "proposed_probe"
    seed: Operator = Field(default_factory=SeedFromObjective)
    expand: Propose
    query: Operator = Field(default_factory=QueryTarget)
    evaluate: Operator
    stop: Operator | None = None
    max_parallel: int = Field(default=1, ge=1)
    stop_on_success: bool = True

    def model_post_init(self, __context: Any) -> None:
        self._validate_probe_shape()

    def _validate_probe_shape(self) -> None:
        if self.expand.branching not in (None, 1):
            raise ConfigError(
                "ProposedProbe generates exactly one candidate. Remove "
                "ops.Propose(branching=...) or use techniques.FrontierSearch for "
                "multi-branch proposal."
            )

    def workflow(self) -> Workflow:
        self._validate_probe_shape()
        steps: list[Operator] = [self.seed, self.expand, self.query, self.evaluate]
        if self.stop is not None:
            steps.append(self.stop)
        return Sequence(steps=steps)

    def _context(self, context: AttackContext) -> AttackContext:
        return context.model_copy(
            update={
                "policy": BranchingPolicy(
                    iterations=1,
                    branching_factor=1,
                    width=1,
                    max_parallel=self.max_parallel,
                    stop_on_success=self.stop_on_success,
                )
            }
        )


class BestOfNProbe(Technique):
    name: str = "best_of_n_probe"
    samples: int = Field(default=8, ge=1)
    width: int = Field(default=1, ge=1)
    max_parallel: int = Field(default=1, ge=1)
    stop_on_success: bool = True
    seed: Operator = Field(default_factory=SeedFromObjective)
    prepare: list[Operator] = Field(default_factory=list)
    query: Operator = Field(default_factory=QueryTarget)
    evaluate: Operator
    stop: Operator | None = None
    select: Operator = Field(default_factory=Select)

    def workflow(self) -> Workflow:
        steps: list[Operator] = [
            self.seed,
            *self.prepare,
            self.query,
            self.evaluate,
        ]
        if self.stop is not None:
            steps.append(self.stop)
        steps.append(self.select)
        return Sequence(steps=steps)

    def _context(self, context: AttackContext) -> AttackContext:
        return context.model_copy(
            update={
                "policy": BranchingPolicy(
                    iterations=1,
                    branching_factor=self.samples,
                    width=self.width,
                    max_parallel=self.max_parallel,
                    stop_on_success=self.stop_on_success,
                )
            }
        )


class ConversationAgentProbe(Technique):
    name: str = "conversation_agent_probe"
    turns: int = Field(default=5, ge=1)
    branching: int = Field(default=1, ge=1)
    width: int = Field(default=1, ge=1)
    max_parallel: int = Field(default=1, ge=1)
    stop_on_success: bool = True
    seed: Operator = Field(default_factory=SeedFromObjective)
    propose: Operator
    query: Operator = Field(default_factory=QueryTarget)
    continue_conversation: Operator = Field(default_factory=ContinueConversation)
    evaluate: Operator
    stop: Operator
    feedback: Operator | None = None
    select: Operator = Field(default_factory=Select)

    def workflow(self) -> Workflow:
        body: list[Operator] = [
            self.propose,
            self.query,
            self.continue_conversation,
            self.evaluate,
            self.stop,
        ]
        if self.feedback is not None:
            body.append(self.feedback)
        body.append(self.select)
        return Sequence(
            steps=[
                self.seed,
                Loop(
                    body=body,
                    max_iterations=self.turns,
                ),
            ],
        )

    def _context(self, context: AttackContext) -> AttackContext:
        return context.model_copy(
            update={
                "policy": BranchingPolicy(
                    iterations=self.turns,
                    branching_factor=self.branching,
                    width=self.width,
                    max_parallel=self.max_parallel,
                    stop_on_success=self.stop_on_success,
                )
            }
        )


class PopulationFuzzing(Technique):
    name: str = "population_fuzzing"
    iterations: int = Field(default=20, ge=1)
    branching: int = Field(default=4, ge=1)
    width: int = Field(default=4, ge=1)
    max_parallel: int = Field(default=1, ge=1)
    stop_on_success: bool = True
    load: Operator
    generate: GenerateFromPopulation
    query: Operator = Field(default_factory=QueryTarget)
    evaluate: Operator
    reward: Operator = Field(default_factory=AssignReward)
    stop: Operator

    def workflow(self) -> Workflow:
        return Sequence(
            steps=[
                self.load,
                Loop(
                    body=[
                        self.generate,
                        self.query,
                        self.evaluate,
                        self.reward,
                        self.stop,
                    ],
                    max_iterations=self.iterations,
                ),
            ],
        )

    def _context(self, context: AttackContext) -> AttackContext:
        return context.model_copy(
            update={
                "policy": BranchingPolicy(
                    iterations=self.iterations,
                    branching_factor=self.branching,
                    width=self.width,
                    max_parallel=self.max_parallel,
                    stop_on_success=self.stop_on_success,
                )
            }
        )


__all__ = [
    "BestOfNProbe",
    "ConversationAgentProbe",
    "ElicitationSearch",
    "FrontierSearch",
    "PopulationFuzzing",
    "Probe",
    "ProposedProbe",
    "SingleTurnProbe",
    "Technique",
]
