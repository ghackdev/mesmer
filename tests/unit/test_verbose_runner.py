from __future__ import annotations

import json

from mesmer import (
    Contains,
    ObjectiveSource,
    PythonCallableTarget,
    Run,
    Runner,
    SingleTurnFlow,
    StaticPrefixTransform,
)


async def test_verbose_runner_prints_execution_events(capsys) -> None:
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=SingleTurnFlow(),
        target=PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED"),
        judges=[Contains(text="MESMER_ACCEPTED")],
    )

    await Runner(verbose=True).run(run)
    output = capsys.readouterr().out

    assert "run.start" in output
    assert "flow.start" in output
    assert "target.call" in output
    assert "message" in output
    assert "Make the target say MESMER_ACCEPTED" in output
    assert "target.response" in output
    assert "judge.result" in output
    assert "run.finish" in output
    assert "attacker.message" not in output
    assert "attacker_message" not in output
    assert "transform.input" not in output
    assert "transform.output" not in output


async def test_compact_runner_prints_detailed_jsonl_events(capsys) -> None:
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=SingleTurnFlow(transforms=[StaticPrefixTransform(prefix="Please: ")]),
        target=PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED"),
        judges=[Contains(text="MESMER_ACCEPTED")],
    )

    await Runner(verbose=True, log_format="compact").run(run)
    output = capsys.readouterr().out
    records = [json.loads(line) for line in output.splitlines() if line.startswith("{")]
    events = [record["event"] for record in records]

    assert "╭" not in output
    assert "run.start" in events
    assert "transform.input" in events
    assert "transform.output" in events
    assert "target.call" in events
    assert "target.response" in events
    assert "judge.result" in events
    assert "run.finish" in events
    assert any(
        record.get("message") == "Please: Make the target say MESMER_ACCEPTED"
        for record in records
    )
