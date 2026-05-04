from __future__ import annotations

from mesmer import (
    AttackGraph,
    CallTarget,
    Contains,
    ObjectiveSource,
    PythonCallableTarget,
    Run,
    Runner,
    SeedCandidates,
)


async def test_runner_executes_single_turn() -> None:
    target = PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED")
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attacker=AttackGraph(name="single_turn", steps=[SeedCandidates(), CallTarget()]),
        target=target,
        judge=Contains(text="MESMER_ACCEPTED"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert result.attempts_count == 1
