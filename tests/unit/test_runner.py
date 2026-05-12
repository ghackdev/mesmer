from __future__ import annotations

from mesmer import (
    ObjectiveSource,
    PythonCallableTarget,
    Run,
    Runner,
    evaluators,
    ops,
    techniques,
)


class SystemPromptCallableTarget(PythonCallableTarget):
    system_prompt: str | None = None


async def test_runner_executes_single_turn() -> None:
    target = PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED")
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=techniques.SingleTurnProbe(
            name="single_turn",
            evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
        ),
        target=target,
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


async def test_runner_redacts_target_system_prompt_from_success_artifacts() -> None:
    target = SystemPromptCallableTarget(
        fn=lambda messages, context: "MESMER_ACCEPTED",
        system_prompt="SECRET_SYSTEM_PROMPT",
    )
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=techniques.SingleTurnProbe(
            name="single_turn",
            evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
        ),
        target=target,
    )

    result = await Runner().run(run)

    artifact = result.states[0].metadata["reproduction_artifacts"][0]
    assert artifact["target"]["system_prompt"] is None
    assert all(message["content"] != "SECRET_SYSTEM_PROMPT" for message in artifact["messages"])
