from __future__ import annotations

from mesmer import (
    AttackGraph,
    CallTarget,
    Contains,
    ExpandCandidates,
    InitialState,
    KeywordOverlapPruner,
    Objective,
    ObjectiveSource,
    PruneCandidates,
    PythonCallableTarget,
    Repeat,
    Run,
    Runner,
    SeedCandidates,
    TemplateCandidateExpander,
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
        attacker=AttackGraph(
            name="tap_like_from_paper",
            steps=[
                SeedCandidates(),
                Repeat(
                    times=2,
                    steps=[
                        ExpandCandidates(
                            expander=TemplateCandidateExpander(),
                            branching_factor=3,
                        ),
                        PruneCandidates(pruner=KeywordOverlapPruner(), width=2),
                        CallTarget(metadata={"paper_family": "tap"}),
                    ],
                ),
            ],
        ),
        target=PythonCallableTarget(fn=guarded_marker_target),
        judge=Contains(text=MARKER),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert result.attempts_count >= 1
    first_attempt = result.states[0].attempts[0]
    assert first_attempt.metadata["paper_family"] == "tap"
    assert first_attempt.candidate.metadata["pruner"] == "keyword_overlap"
