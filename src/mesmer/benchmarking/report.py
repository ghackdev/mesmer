from __future__ import annotations

import json
from pathlib import Path

from mesmer.benchmarking.metrics import MetricValue
from mesmer.core.config import MesmerModel
from mesmer.execution.runner import RunResult


class Report(MesmerModel):
    benchmark_name: str
    metrics: list[MetricValue]
    results: list[RunResult]

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def write_json(self, path: str | Path) -> Path:
        target = Path(path)
        target.write_text(self.to_json(), encoding="utf-8")
        return target

    def to_markdown(self) -> str:
        rows = ["| Metric | Value |", "| --- | ---: |"]
        rows.extend(f"| {metric.name.value} | {metric.value:.4f} |" for metric in self.metrics)
        return f"# {self.benchmark_name}\n\n" + "\n".join(rows)

    @classmethod
    def from_json(cls, value: str) -> Report:
        return cls(**json.loads(value))
