from __future__ import annotations

import json
from pathlib import Path

from pydantic import Field

from mesmer.benchmarking.metrics import MetricValue
from mesmer.core.config import MesmerModel
from mesmer.execution.runner import RunResult


class EvidenceRow(MesmerModel):
    run_id: str
    objective_id: str
    attack_name: str | None = None
    technique: str | None = None
    target_name: str | None = None
    target_model: str | None = None
    target_capabilities: list[str] = Field(default_factory=list)
    turn: int
    candidate_id: str
    attempt_id: str
    response_id: str
    evaluator: str | None = None
    score: float | None = None
    normalized_score: float | None = None
    passed: bool | None = None
    query_count: int | None = None
    cost: float | None = None


class EvidenceMatrix(MesmerModel):
    rows: list[EvidenceRow] = Field(default_factory=list)

    @classmethod
    def from_results(cls, results: list[RunResult]) -> EvidenceMatrix:
        rows: list[EvidenceRow] = []
        for result in results:
            for state in result.states:
                base = {
                    "run_id": result.run_id,
                    "attack_name": state.metadata.get("attack_name"),
                    "technique": state.metadata.get("technique"),
                    "target_name": state.metadata.get("target_name"),
                    "target_model": state.metadata.get("target_model"),
                    "target_capabilities": list(state.metadata.get("target_capabilities", [])),
                    "query_count": state.metadata.get("target_calls"),
                }
                for attempt in state.attempts:
                    if not attempt.judgements:
                        rows.append(
                            EvidenceRow(
                                **base,
                                objective_id=attempt.objective.id,
                                turn=attempt.turn,
                                candidate_id=attempt.candidate.id,
                                attempt_id=attempt.id,
                                response_id=attempt.response.id,
                                cost=attempt.response.cost,
                            )
                        )
                        continue
                    for judgement in attempt.judgements:
                        rows.append(
                            EvidenceRow(
                                **base,
                                objective_id=attempt.objective.id,
                                turn=attempt.turn,
                                candidate_id=attempt.candidate.id,
                                attempt_id=attempt.id,
                                response_id=attempt.response.id,
                                evaluator=judgement.metadata.get("evaluator"),
                                score=judgement.metadata.get("raw_score"),
                                normalized_score=judgement.score,
                                passed=judgement.status.value == "pass",
                                cost=attempt.response.cost,
                            )
                        )
        return cls(rows=rows)


class BudgetCurvePoint(MesmerModel):
    budget: int
    successes: int
    total: int
    success_rate: float


class BudgetCurve(MesmerModel):
    points: list[BudgetCurvePoint] = Field(default_factory=list)

    @classmethod
    def from_results(cls, results: list[RunResult]) -> BudgetCurve:
        attempts_by_result = [
            [attempt for state in result.states for attempt in state.attempts]
            for result in results
        ]
        max_budget = max((len(attempts) for attempts in attempts_by_result), default=0)
        points: list[BudgetCurvePoint] = []
        for budget in range(1, max_budget + 1):
            successes = sum(
                any(attempt.succeeded for attempt in attempts[:budget])
                for attempts in attempts_by_result
            )
            total = len(attempts_by_result)
            points.append(
                BudgetCurvePoint(
                    budget=budget,
                    successes=successes,
                    total=total,
                    success_rate=successes / total if total else 0.0,
                )
            )
        return cls(points=points)


class Report(MesmerModel):
    benchmark_name: str
    metrics: list[MetricValue]
    results: list[RunResult]
    evidence: EvidenceMatrix | None = None
    budget_curve: BudgetCurve | None = None

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
