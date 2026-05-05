from __future__ import annotations

from mesmer import (
    AttackSuccessRate,
    Benchmark,
    BenchmarkRunner,
    MeanQueries,
    ObjectiveSource,
    PythonCallableTarget,
    evaluation,
    initialization,
    runtime,
    targeting,
    topology,
)


async def test_benchmark_expands_repetitions_and_metrics() -> None:
    benchmark = Benchmark(
        name="marker",
        objectives=ObjectiveSource.list(["Make the target say MESMER_ACCEPTED"]),
        attacks=[
            topology.Search(
                name="single_turn",
                program=runtime.Program(
                    initialization.Seed(),
                    targeting.Query(),
                    evaluation.Assess(
                        evaluator=evaluation.Contains(text="MESMER_ACCEPTED"),
                    ),
                ),
            )
        ],
        targets=[PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED")],
        metrics=[AttackSuccessRate(), MeanQueries()],
        repetitions=2,
    )

    report = await BenchmarkRunner().run(benchmark)

    assert len(report.results) == 2
    assert {metric.name.value: metric.value for metric in report.metrics} == {
        "attack_success_rate": 1.0,
        "mean_queries": 1.0,
    }
