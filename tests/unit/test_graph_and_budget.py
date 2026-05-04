from __future__ import annotations

from mesmer import (
    AttackGraph,
    CallTarget,
    Contains,
    ExpandCandidates,
    ObjectiveSource,
    PythonCallableTarget,
    Run,
    Runner,
    SeedCandidates,
    TemplateCandidateExpander,
)
from mesmer.execution.budgets import Budget


def test_attack_graph_is_declarative() -> None:
    attacker = AttackGraph(
        name="unit_graph",
        steps=[
            SeedCandidates(),
            ExpandCandidates(expander=TemplateCandidateExpander(), branching_factor=2),
            CallTarget(),
        ],
    )

    assert attacker.name == "unit_graph"
    assert len(attacker.steps) == 3


async def test_budget_failure_marks_run_failed() -> None:
    target = PythonCallableTarget(fn=lambda messages, context: "not yet")
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attacker=AttackGraph(
            name="budget_graph",
            steps=[
                SeedCandidates(),
                ExpandCandidates(expander=TemplateCandidateExpander(), branching_factor=2),
                CallTarget(stop_on_success=False),
            ],
        ),
        target=target,
        judge=Contains(text="MESMER_ACCEPTED"),
        budget=Budget(max_queries=1),
    )

    result = await Runner().run(run)

    assert result.status.value == "failed"
    assert "Maximum query budget exceeded" in (result.error or "")
