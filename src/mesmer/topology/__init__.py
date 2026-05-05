from __future__ import annotations

from typing import Any

from mesmer.flows.base import AttackContext
from mesmer.flows.base import Flow as Technique
from mesmer.search.models import SearchPolicy
from mesmer.search.technique import Iterate, IterativeSearchTechnique


class Policy(SearchPolicy):
    def __init__(self, **data: Any) -> None:
        if "branching" in data and "branching_factor" not in data:
            data["branching_factor"] = data.pop("branching")
        if "parallelism" in data and "max_parallel" not in data:
            data["max_parallel"] = data.pop("parallelism")
        super().__init__(**data)


class Search(IterativeSearchTechnique):
    name: str = "search"


__all__ = [
    "AttackContext",
    "Iterate",
    "Policy",
    "Search",
    "Technique",
]
