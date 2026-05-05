from __future__ import annotations

from mesmer import (
    ObjectiveSource,
    PythonCallableTarget,
    Run,
    Runner,
    evaluation,
    generation,
    initialization,
    runtime,
    targeting,
    topology,
)
from mesmer.execution.budgets import Budget


def test_technique_program_is_declarative() -> None:
    attack = topology.Search(
        name="unit_graph",
        program=runtime.Program(
            initialization.Seed(),
            topology.Iterate(
                policy=topology.Policy(iterations=1, branching=2, width=2),
                children=[
                    generation.Propose(proposer=generation.Template()),
                    targeting.Query(),
                ],
            ),
        ),
    )

    assert attack.name == "unit_graph"
    assert len(attack.program.children) == 2


async def test_budget_failure_marks_run_failed() -> None:
    target = PythonCallableTarget(fn=lambda messages, context: "not yet")
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=topology.Search(
            name="budget_graph",
            program=runtime.Program(
                initialization.Seed(),
                topology.Iterate(
                    policy=topology.Policy(
                        iterations=1,
                        branching=2,
                        width=2,
                        stop_on_success=False,
                    ),
                    children=[
                        generation.Propose(proposer=generation.Template()),
                        targeting.Query(),
                        evaluation.Assess(
                            evaluator=evaluation.Contains(text="MESMER_ACCEPTED"),
                        ),
                    ],
                ),
            ),
        ),
        target=target,
        budget=Budget(max_queries=1),
    )

    result = await Runner().run(run)

    assert result.status.value == "failed"
    assert "Maximum query budget exceeded" in (result.error or "")
