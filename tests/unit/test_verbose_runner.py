from __future__ import annotations

import json

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


def single_turn_attack(*, proposer=None):
    if proposer is None:
        return techniques.SingleTurnProbe(
            name="single_turn",
            evaluate=ops.Evaluate(evaluator=evaluators.Contains(text="MESMER_ACCEPTED")),
        )
    return techniques.FrontierSearch(
        name="single_turn",
        iterations=1,
        branching=1,
        width=1,
        expand=ops.Propose(proposer),
        evaluate=ops.Evaluate(evaluator=evaluators.Contains(text="MESMER_ACCEPTED")),
        stop=ops.StopWhen(conditions.ScoreAtLeast(1)),
    )


async def test_verbose_runner_prints_execution_events(capsys) -> None:
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=single_turn_attack(),
        target=PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED"),
    )

    await Runner(verbose=True).run(run)
    output = capsys.readouterr().out

    assert "run.start" in output
    assert "technique.start" in output
    assert "target.call" in output
    assert "message" in output
    assert "Make the target say MESMER_ACCEPTED" in output
    assert "target.response" in output
    assert "operator.evaluate.result" in output
    assert "run.finish" in output
    assert "REPRODUCTION ARTIFACT" in output
    assert "target replay messages" in output
    assert output.rfind("REPRODUCTION ARTIFACT") > output.rfind("RUN COMPLETE")
    assert "attacker.message" not in output
    assert "attacker_message" not in output
    assert "transform.input" not in output
    assert "transform.output" not in output


async def test_compact_runner_prints_detailed_jsonl_events(capsys) -> None:
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=single_turn_attack(
        proposer=proposers.Template(templates=("Please: {prompt}",))
        ),
        target=PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED"),
    )

    await Runner(verbose=True, log_format="compact").run(run)
    output = capsys.readouterr().out
    records = [json.loads(line) for line in output.splitlines() if line.startswith("{")]
    events = [record["event"] for record in records]

    assert "╭" not in output
    assert "run.start" in events
    assert "operator.propose.finish" in events
    assert "target.call" in events
    assert "target.response" in events
    assert "operator.evaluate.result" in events
    assert "objective.success" in events
    assert "run.finish" in events
    assert events.index("objective.success") > events.index("run.finish")
    assert any(
        record.get("message") == "Please: Make the target say MESMER_ACCEPTED"
        for record in records
    )
    success = next(record for record in records if record["event"] == "objective.success")
    assert "mode" not in success
    assert "final_prompt" not in success
    assert "target_response" not in success
    assert "reproduction" not in success
    assert success["messages"][0]["role"] == "user"
    assert success["messages"][0]["content"] == "Please: Make the target say MESMER_ACCEPTED"
    assert success["messages"][1]["role"] == "assistant"
    assert success["messages"][1]["content"] == "MESMER_ACCEPTED"
    assert success["score"] == 1.0
