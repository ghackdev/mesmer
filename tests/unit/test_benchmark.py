from __future__ import annotations

from mesmer import (
    AttackSuccessRate,
    Benchmark,
    BenchmarkRunner,
    MeanQueries,
    ObjectiveSource,
    PythonCallableTarget,
    evaluators,
    ops,
    techniques,
)


async def test_benchmark_expands_repetitions_and_metrics() -> None:
    benchmark = Benchmark(
        name="marker",
        objectives=ObjectiveSource.list(["Make the target say MESMER_ACCEPTED"]),
        attacks=[
            techniques.SingleTurnProbe(
                name="single_turn",
                evaluate=ops.Evaluate(evaluator=evaluators.Contains(text="MESMER_ACCEPTED")),
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
    assert report.evidence is not None
    assert len(report.evidence.rows) == 2
    assert {row.attack_name for row in report.evidence.rows} == {"single_turn"}
    assert report.budget_curve is not None
    assert [(point.budget, point.success_rate) for point in report.budget_curve.points] == [
        (1, 1.0)
    ]
