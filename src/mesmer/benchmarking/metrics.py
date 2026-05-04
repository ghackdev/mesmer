from __future__ import annotations

from abc import ABC, abstractmethod
from statistics import mean

from mesmer.core.config import MesmerModel
from mesmer.core.enums import MetricName
from mesmer.execution.runner import RunResult


class MetricValue(MesmerModel):
    name: MetricName
    value: float


class Metric(MesmerModel, ABC):
    name: MetricName

    @abstractmethod
    def compute(self, results: list[RunResult]) -> MetricValue:
        raise NotImplementedError


class AttackSuccessRate(Metric):
    name: MetricName = MetricName.ATTACK_SUCCESS_RATE

    def compute(self, results: list[RunResult]) -> MetricValue:
        if not results:
            return MetricValue(name=self.name, value=0.0)
        success_count = sum(result.succeeded for result in results)
        return MetricValue(name=self.name, value=success_count / len(results))


class MeanQueries(Metric):
    name: MetricName = MetricName.MEAN_QUERIES

    def compute(self, results: list[RunResult]) -> MetricValue:
        if not results:
            return MetricValue(name=self.name, value=0.0)
        return MetricValue(name=self.name, value=mean(result.attempts_count for result in results))


class MeanCost(Metric):
    name: MetricName = MetricName.MEAN_COST

    def compute(self, results: list[RunResult]) -> MetricValue:
        costs = [
            attempt.response.cost or 0.0
            for result in results
            for state in result.states
            for attempt in state.attempts
        ]
        return MetricValue(name=self.name, value=mean(costs) if costs else 0.0)


class MeanTurns(Metric):
    name: MetricName = MetricName.MEAN_TURNS

    def compute(self, results: list[RunResult]) -> MetricValue:
        turns = [
            attempt.turn
            for result in results
            for state in result.states
            for attempt in state.attempts
        ]
        return MetricValue(name=self.name, value=mean(turns) if turns else 0.0)
