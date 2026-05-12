from __future__ import annotations

from mesmer import (
    ObjectiveSource,
    PythonCallableTarget,
    Run,
    Runner,
    conditions,
    evaluators,
    ops,
    proposers,
    techniques,
)
from mesmer.execution.budgets import Budget


def test_technique_workflow_is_declarative() -> None:
    attack = techniques.FrontierSearch(
        name="unit_graph",
        iterations=1,
        branching=2,
        width=2,
        expand=ops.Propose(proposer=proposers.Template()),
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
    )

    assert attack.name == "unit_graph"
    assert attack.workflow_graph() == [
        "seed_from_objective",
        "propose",
        "query_target",
        "evaluate",
        "stop_when",
        "select",
    ]


async def test_budget_failure_marks_run_failed() -> None:
    target = PythonCallableTarget(fn=lambda messages, context: "not yet")
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=techniques.FrontierSearch(
            name="budget_graph",
            iterations=1,
            branching=2,
            width=2,
            stop_on_success=False,
            expand=ops.Propose(proposer=proposers.Template()),
            evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
            stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
        ),
        target=target,
        budget=Budget(max_queries=1),
    )

    result = await Runner().run(run)

    assert result.status.value == "failed"
    assert "Maximum query budget exceeded" in (result.error or "")
