from __future__ import annotations

from time import perf_counter

from mesmer.core.config import MesmerModel
from mesmer.core.constants import DEFAULT_MAX_QUERIES, DEFAULT_MAX_TURNS
from mesmer.core.errors import BudgetExceededError


class Budget(MesmerModel):
    max_queries: int = DEFAULT_MAX_QUERIES
    max_turns: int = DEFAULT_MAX_TURNS
    max_seconds: float | None = None


class BudgetTracker:
    def __init__(self, budget: Budget) -> None:
        self.budget = budget
        self.query_count = 0
        self.turn_count = 0
        self.started_at = perf_counter()

    def check(self) -> None:
        if self.query_count > self.budget.max_queries:
            raise BudgetExceededError("Maximum query budget exceeded.")
        if self.turn_count > self.budget.max_turns:
            raise BudgetExceededError("Maximum turn budget exceeded.")
        if (
            self.budget.max_seconds is not None
            and perf_counter() - self.started_at > self.budget.max_seconds
        ):
            raise BudgetExceededError("Maximum time budget exceeded.")

    def record_query(self) -> None:
        self.query_count += 1
        self.check()

    def record_turn(self) -> None:
        self.turn_count += 1
        self.check()
