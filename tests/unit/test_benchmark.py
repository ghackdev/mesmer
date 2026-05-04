from __future__ import annotations

from mesmer import (
    AttackGraph,
    AttackSuccessRate,
    Benchmark,
    BenchmarkRunner,
    CallTarget,
    Contains,
    MeanQueries,
    ObjectiveSource,
    PythonCallableTarget,
    SeedCandidates,
)


async def test_benchmark_expands_repetitions_and_metrics() -> None:
    benchmark = Benchmark(
        name="marker",
        objectives=ObjectiveSource.list(["Make the target say MESMER_ACCEPTED"]),
        attackers=[AttackGraph(name="single_turn", steps=[SeedCandidates(), CallTarget()])],
        targets=[PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED")],
        judges=[Contains(text="MESMER_ACCEPTED")],
        metrics=[AttackSuccessRate(), MeanQueries()],
        repetitions=2,
    )

    report = await BenchmarkRunner().run(benchmark)

    assert len(report.results) == 2
    assert {metric.name.value: metric.value for metric in report.metrics} == {
        "attack_success_rate": 1.0,
        "mean_queries": 1.0,
    }
