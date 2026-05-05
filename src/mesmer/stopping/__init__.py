from __future__ import annotations

from mesmer.search.components import ScoreAtLeast, TerminationCondition
from mesmer.search.technique import StopWhen

Condition = TerminationCondition

__all__ = [
    "Condition",
    "ScoreAtLeast",
    "StopWhen",
]
