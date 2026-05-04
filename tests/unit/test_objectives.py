from __future__ import annotations

from mesmer import InitialState, Objective, ObjectiveSource
from mesmer.core.enums import MessageRole


def test_objective_string_normalizes() -> None:
    objective = Objective.coerce("Make the target say OK")

    assert objective.goal == "Make the target say OK"
    assert objective.initial_state.messages == []


def test_initial_state_from_prompt() -> None:
    state = InitialState.from_prompt("hello")

    assert state.messages[0].role == MessageRole.USER
    assert state.messages[0].content == "hello"


def test_source_list_normalizes_strings() -> None:
    objectives = list(ObjectiveSource.list(["a", Objective("b")]))

    assert [objective.goal for objective in objectives] == ["a", "b"]
