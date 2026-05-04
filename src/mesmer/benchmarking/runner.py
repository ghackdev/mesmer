from __future__ import annotations

from mesmer.benchmarking.benchmark import Benchmark
from mesmer.benchmarking.report import Report
from mesmer.core.config import MesmerModel
from mesmer.core.enums import SpanName
from mesmer.execution.run import Run
from mesmer.execution.runner import Runner, RunResult
from mesmer.objectives.sources import ObjectiveSource
from mesmer.telemetry.tracing import start_span


class BenchmarkRunner(MesmerModel):
    runner: Runner = Runner()

    async def run(self, benchmark: Benchmark) -> Report:
        results: list[RunResult] = []
        with start_span(SpanName.BENCHMARK.value, {"benchmark.name": benchmark.name}):
            objectives = list(benchmark.objectives)
            for repetition in range(benchmark.repetitions):
                for attack in benchmark.attacks:
                    for target in benchmark.targets:
                        run = Run(
                            objectives=ObjectiveSource.list(objectives),
                            attack=attack,
                            target=target,
                            judges=benchmark.judges,
                            budget=benchmark.budget,
                            metadata={"benchmark": benchmark.name, "repetition": str(repetition)},
                        )
                        results.append(await self.runner.run(run))
            metrics = [metric.compute(results) for metric in benchmark.metrics]
        return Report(benchmark_name=benchmark.name, metrics=metrics, results=results)
