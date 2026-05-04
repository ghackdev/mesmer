from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Self

from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.core.enums import StateFact
from mesmer.core.errors import ConfigError
from mesmer.flows.base import AttackContext
from mesmer.runtime.state import RuntimeState, StatePatch, StateSnapshot


class RuntimeContext(MesmerModel):
    attack: AttackContext
    policy: Any = None

    def with_policy(self, policy: Any) -> Self:
        return self.model_copy(update={"policy": policy})


class Component(MesmerModel, ABC):
    name: str
    requires: set[StateFact] = Field(default_factory=set)
    provides: set[StateFact] = Field(default_factory=set)

    @abstractmethod
    async def apply(self, state: RuntimeState, context: RuntimeContext) -> StatePatch:
        raise NotImplementedError

    def validate(self, provided: set[StateFact]) -> set[StateFact]:
        missing = self.requires - provided
        if missing:
            missing_list = ", ".join(sorted(fact.value for fact in missing))
            available_list = ", ".join(sorted(fact.value for fact in provided))
            raise ConfigError(
                f"Component '{self.name}' requires missing state facts: {missing_list}. "
                f"Available facts: {available_list or '(none)'}."
            )
        return provided | self.provides


class ContainerComponent(Component):
    children: list[Component] = Field(default_factory=list)

    def __init__(self, *children: Component, **data: object) -> None:
        if children and "children" not in data:
            data["children"] = list(children)
        super().__init__(**data)

    def validate(self, provided: set[StateFact]) -> set[StateFact]:
        facts = super().validate(provided)
        for child in self.children:
            facts = child.validate(facts)
        return facts | self.provides

    async def apply(self, state: RuntimeState, context: RuntimeContext) -> StatePatch:
        for child in self.children:
            if state.stopped:
                break
            before = StateSnapshot.from_state(state)
            patch = await child.apply(state, context)
            state.apply_patch(patch)
            after = StateSnapshot.from_state(state)
            state.record_transition(child.name, before, patch, after)
        return StatePatch(provided=self.provides)


class Program(ContainerComponent):
    state: type[RuntimeState] = RuntimeState
    name: str = "program"
    requires: set[StateFact] = Field(default_factory=lambda: {StateFact.OBJECTIVE})
