from __future__ import annotations

import sqlite3

from mesmer import (
    ObjectiveSource,
    PythonCallableTarget,
    Run,
    Runner,
    SQLiteRecorder,
    evaluation,
    initialization,
    runtime,
    targeting,
    topology,
)


async def test_sqlite_recorder_persists_attempt(tmp_path) -> None:
    db_path = tmp_path / "runs.sqlite3"
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=topology.Search(
            name="single_turn",
            program=runtime.Program(
                initialization.Seed(),
                targeting.Query(),
                evaluation.Assess(evaluator=evaluation.Contains(text="MESMER_ACCEPTED")),
            ),
        ),
        target=PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED"),
        recorder=SQLiteRecorder(path=db_path),
    )

    result = await Runner().run(run)

    with sqlite3.connect(db_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
    assert result.succeeded
    assert count == 1
