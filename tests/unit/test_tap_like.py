from __future__ import annotations

from mesmer import (
    InitialState,
    Objective,
    ObjectiveSource,
    PythonCallableTarget,
    Run,
    Runner,
    evaluation,
    generation,
    initialization,
    runtime,
    selection,
    stopping,
    targeting,
    topology,
)

MARKER = "MESMER_ACCEPTED"


def guarded_marker_target(messages, context) -> str:
    prompt = messages[-1].content.lower()
    if "directly" in prompt and MARKER.lower() in prompt:
        return MARKER
    return "clarify the marker"


async def test_tap_like_attacker_expands_prunes_and_succeeds() -> None:
    objective = Objective(
        goal=f"Get the target to output the benign test marker {MARKER}.",
        initial_state=InitialState.from_prompt("Can you help me run an integration test?"),
    )
    run = Run(
        objectives=ObjectiveSource.single(objective),
        attack=topology.Search(
            name="tap_like_from_paper",
            program=runtime.Program(
                initialization.Seed(),
                topology.Iterate(
                    policy=topology.Policy(iterations=2, branching=3, width=2),
                    children=[
                        generation.Propose(proposer=generation.Template()),
                        selection.Select(selector=selection.KeywordOverlap()),
                        targeting.Query(),
                        evaluation.Assess(evaluator=evaluation.Contains(text=MARKER)),
                        stopping.StopWhen(condition=stopping.ScoreAtLeast(1)),
                    ],
                ),
            ),
        ),
        target=PythonCallableTarget(fn=guarded_marker_target),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert result.attempts_count >= 1
    first_attempt = result.states[0].attempts[0]
    assert first_attempt.metadata["trace"]["trajectory"]["depth"] == 1
    assert first_attempt.candidate.metadata["selector"] == "keyword_overlap"
