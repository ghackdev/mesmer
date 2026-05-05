from __future__ import annotations

from mesmer.search.components import CandidateConstraint, LLMLabelConstraint
from mesmer.search.technique import Constrain

Constraint = CandidateConstraint
LLMLabel = LLMLabelConstraint


class Filter(Constrain):
    name: str = "filter"

    def __init__(
        self,
        constraint: Constraint | None = None,
        *,
        constraints: list[Constraint] | None = None,
        **data: object,
    ) -> None:
        if constraint is not None and "constraints" not in data:
            data["constraints"] = [constraint]
        if constraints is not None and "constraints" not in data:
            data["constraints"] = constraints
        super().__init__(**data)


__all__ = [
    "Constraint",
    "Filter",
    "LLMLabel",
]
