from __future__ import annotations

from pydantic import Field

from mesmer import (
    ObjectiveSource,
    PythonCallableTarget,
    Run,
    Runner,
    conditions,
    evaluators,
    ops,
    proposers,
    selectors,
    techniques,
    workflow,
)
from mesmer.flows.base import AttackContext
from mesmer.state import Frontier, Patch, State, StateSlice


async def test_frontier_search_executes_with_inferred_state_and_transitions() -> None:
    attack = techniques.FrontierSearch(
        name="unit_frontier_search",
        iterations=1,
        branching=1,
        width=1,
        expand=ops.Propose(
            proposers.Template(templates=("Please satisfy: {goal}",)),
        ),
        evaluate=ops.Evaluate(evaluators.Contains(text="MESMER_ACCEPTED")),
        stop=ops.StopWhen(conditions.ScoreAtLeast(1)),
        select=ops.Select(selectors.TopK()),
    )
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert result.attempts_count == 1
    assert {slice_type.__name__ for slice_type in attack.state_schema()} >= {
        "Frontier",
        "Attempts",
        "TargetResponses",
        "Evaluations",
    }
    history = result.states[0].metadata["state_history"]
    assert [transition["operator"] for transition in history] == [
        "seed_from_objective",
        "propose",
        "query_target",
        "evaluate",
        "stop_when",
    ]


class NoveltyLedger(StateSlice):
    scores: list[int] = Field(default_factory=list)


class TrackNovelty(workflow.Operator):
    name: str = "track_novelty"
    reads: set[type[StateSlice]] = Field(default_factory=lambda: {Frontier})
    writes: set[type[StateSlice]] = Field(default_factory=lambda: {NoveltyLedger})

    async def run(self, state: State, context: AttackContext) -> Patch:
        return Patch.set(NoveltyLedger(scores=[len(state.get(Frontier).items)]))


async def test_custom_operator_can_add_state_slice() -> None:
    attack = techniques.FrontierSearch(
        name="unit_custom_operator",
        iterations=1,
        branching=1,
        width=1,
        expand=ops.Propose(proposers.Template(templates=("Please satisfy: {goal}",))),
        evaluate=ops.Evaluate(evaluators.Contains(text="OK")),
        stop=ops.StopWhen(conditions.ScoreAtLeast(1)),
        select=ops.Select(selectors.TopK()),
        feedback=TrackNovelty(),
    )
    run = Run(
        objectives=ObjectiveSource.single("Say OK"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "OK"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert NoveltyLedger in attack.state_schema()
