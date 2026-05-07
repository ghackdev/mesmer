from __future__ import annotations

import time
from abc import ABC, abstractmethod

from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.core.errors import ConfigError
from mesmer.flows.base import AttackContext
from mesmer.state import Patch, State, StateSlice
from mesmer.transitions import Transition


class Operator(MesmerModel, ABC):
    name: str
    reads: set[type[StateSlice]] = Field(default_factory=set)
    writes: set[type[StateSlice]] = Field(default_factory=set)
    capabilities: set[str] = Field(default_factory=set)

    @abstractmethod
    async def run(self, state: State, context: AttackContext) -> Patch:
        raise NotImplementedError

    def required_slices(self) -> set[type[StateSlice]]:
        return set(self.reads | self.writes)


class Workflow(MesmerModel, ABC):
    name: str

    @abstractmethod
    def operators(self) -> list[Operator]:
        raise NotImplementedError

    @abstractmethod
    async def run(self, state: State, context: AttackContext) -> None:
        raise NotImplementedError

    def required_slices(self) -> set[type[StateSlice]]:
        slices: set[type[StateSlice]] = set()
        for operator in self.operators():
            slices.update(operator.required_slices())
        return slices

    def validate(self, available: set[type[StateSlice]]) -> None:
        for operator in self.operators():
            missing = operator.reads - available
            if missing:
                missing_names = ", ".join(sorted(slice_type.__name__ for slice_type in missing))
                raise ConfigError(
                    f"Operator '{operator.name}' reads missing state slices: {missing_names}."
                )
            available.update(operator.writes)


class Sequence(Workflow):
    steps: list[Operator | Workflow] = Field(default_factory=list)
    name: str = "sequence"

    def __init__(self, *steps: Operator | Workflow, **data: object) -> None:
        if steps and "steps" not in data:
            data["steps"] = list(steps)
        super().__init__(**data)

    def operators(self) -> list[Operator]:
        values: list[Operator] = []
        for step in self.steps:
            if isinstance(step, Operator):
                values.append(step)
            else:
                values.extend(step.operators())
        return values

    async def run(self, state: State, context: AttackContext) -> None:
        for step in self.steps:
            if state.stopped:
                break
            if isinstance(step, Operator):
                await execute_operator(step, state, context)
            else:
                await step.run(state, context)


class Loop(Workflow):
    body: list[Operator | Workflow] = Field(default_factory=list)
    max_iterations: int = Field(default=1, ge=1)
    name: str = "loop"

    def __init__(
        self,
        *body: Operator | Workflow,
        max_iterations: int = 1,
        **data: object,
    ) -> None:
        if body and "body" not in data:
            data["body"] = list(body)
        if "max_iterations" not in data:
            data["max_iterations"] = max_iterations
        super().__init__(**data)

    def operators(self) -> list[Operator]:
        values: list[Operator] = []
        for step in self.body:
            if isinstance(step, Operator):
                values.append(step)
            else:
                values.extend(step.operators())
        return values

    async def run(self, state: State, context: AttackContext) -> None:
        from mesmer.state import Iteration

        for iteration in range(1, self.max_iterations + 1):
            if state.stopped:
                break
            state.apply_patch(Patch.set(Iteration(value=iteration)))
            context.budget_tracker.record_turn()
            context.logger.emit("workflow.loop.start", iteration=iteration)
            for step in self.body:
                if state.stopped:
                    break
                if isinstance(step, Operator):
                    await execute_operator(step, state, context)
                else:
                    await step.run(state, context)


async def execute_operator(operator: Operator, state: State, context: AttackContext) -> None:
    missing = operator.reads - set(state.slices)
    if missing:
        missing_names = ", ".join(sorted(slice_type.__name__ for slice_type in missing))
        raise ConfigError(
            f"Operator '{operator.name}' reads missing state slices: {missing_names}."
        )
    before = state.snapshot()
    start = time.perf_counter()
    try:
        patch = await operator.run(state, context)
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        state.transitions.append(
            Transition(
                operator=operator.name,
                before=before,
                patch={},
                after=state.snapshot(),
                duration_ms=duration_ms,
                error=str(exc),
            )
        )
        raise
    state.apply_patch(patch)
    duration_ms = (time.perf_counter() - start) * 1000
    state.transitions.append(
        Transition(
            operator=operator.name,
            before=before,
            patch=patch.summary(),
            after=state.snapshot(),
            events=patch.events,
            artifacts=patch.artifacts,
            duration_ms=duration_ms,
        )
    )
