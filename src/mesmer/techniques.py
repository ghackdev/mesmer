from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.core.constants import DEFAULT_SEARCH_STOP_REASON
from mesmer.execution.state import AttackState
from mesmer.flows.base import AttackContext
from mesmer.objectives.models import Objective
from mesmer.ops import (
    AssignReward,
    GenerateFromPopulation,
    LoadPopulation,
    QueryTarget,
    SeedFromObjective,
    Select,
)
from mesmer.search.models import SearchPolicy
from mesmer.state import Metadata, Patch, State, StateSlice, StopSignal
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
                Metadata(values={"stop_reason": DEFAULT_SEARCH_STOP_REASON}),
            )
        )
        await workflow.run(state, self._context(context))
        if not state.get(StopSignal).reason:
            state.apply_patch(Patch(metadata={"stop_reason": DEFAULT_SEARCH_STOP_REASON}))
        context.logger.emit(
            "technique.stop",
            technique=self.name,
            reason=state.attack_state.metadata.get("stop_reason", DEFAULT_SEARCH_STOP_REASON),
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
    expand: Operator
    query: Operator = Field(default_factory=QueryTarget)
    evaluate: Operator
    stop: Operator
    select: Operator = Field(default_factory=Select)
    feedback: Operator | None = None

    def workflow(self) -> Workflow:
        body: list[Operator] = [self.expand, self.query, self.evaluate, self.stop]
        if self.feedback is not None:
            body.append(self.feedback)
        body.append(self.select)
        return Sequence(
            self.seed,
            Loop(
                *body,
                max_iterations=self.iterations,
            ),
        )

    def _context(self, context: AttackContext) -> AttackContext:
        return context.model_copy(
            update={
                "policy": SearchPolicy(
                    iterations=self.iterations,
                    branching_factor=self.branching,
                    width=self.width,
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
        return Sequence(*steps)


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

    def __init__(self, *, seeds=None, load: Operator | None = None, **data: object) -> None:
        if seeds is not None and load is None and "load" not in data:
            data["load"] = LoadPopulation(source=seeds)
        elif load is not None and "load" not in data:
            data["load"] = load
        super().__init__(**data)

    def workflow(self) -> Workflow:
        return Sequence(
            self.load,
            Loop(
                self.generate,
                self.query,
                self.evaluate,
                self.reward,
                self.stop,
                max_iterations=self.iterations,
            ),
        )

    def _context(self, context: AttackContext) -> AttackContext:
        return context.model_copy(
            update={
                "policy": SearchPolicy(
                    iterations=self.iterations,
                    branching_factor=self.branching,
                    width=self.width,
                    max_parallel=self.max_parallel,
                    stop_on_success=self.stop_on_success,
                )
            }
        )


__all__ = [
    "FrontierSearch",
    "PopulationFuzzing",
    "SingleTurnProbe",
    "Technique",
]
