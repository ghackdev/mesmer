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
    artifacts = result.states[0].metadata["reproduction_artifacts"]
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert "mode" not in artifact
    assert "final_prompt" not in artifact
    assert "target_response" not in artifact
    assert artifact["messages"][0]["role"] == "user"
    assert artifact["messages"][0]["content"] == "Make the target say MESMER_ACCEPTED"
    assert artifact["messages"][1]["role"] == "assistant"
    assert artifact["messages"][1]["content"] == "MESMER_ACCEPTED"
