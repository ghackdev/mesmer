from __future__ import annotations

import re

from mesmer.population_strategies import (
    EXP3SeedSelector,
    RandomSeedSelector,
    RoundRobinSeedSelector,
    UCBSeedSelector,
    WeightedRandomSeedSelector,
)
from mesmer.strategies import (
    ConstraintScoreSelector,
    FrontierSelector,
    InferenceDiversitySelector,
    TopKSelector,
)
from mesmer.trajectory import CandidateTrajectory

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]{3,}")


class KeywordOverlapSelector(FrontierSelector):
    name: str = "keyword_overlap"

    def select(
        self,
        trajectories: list[CandidateTrajectory],
        width: int,
    ) -> list[CandidateTrajectory]:
        if not trajectories:
            return []
        objective = trajectories[0].metadata.get("objective_goal", "")
        objective_tokens = set(TOKEN_PATTERN.findall(str(objective).lower()))

        def score(trajectory: CandidateTrajectory) -> float:
            prompt_tokens = set(TOKEN_PATTERN.findall(trajectory.latest_text.lower()))
            overlap = len(objective_tokens & prompt_tokens)
            directness_bonus = 1 if {"direct", "directly"} & prompt_tokens else 0
            return overlap + directness_bonus

        ranked = sorted(trajectories, key=score, reverse=True)
        for rank, trajectory in enumerate(ranked, start=1):
            trajectory.candidate.metadata["selector"] = self.name
            trajectory.candidate.metadata["select_rank"] = rank
            trajectory.candidate.metadata["select_score"] = score(trajectory)
        return ranked[:width]


__all__ = [
    "ConstraintScoreSelector",
    "EXP3SeedSelector",
    "FrontierSelector",
    "InferenceDiversitySelector",
    "KeywordOverlapSelector",
    "RandomSeedSelector",
    "RoundRobinSeedSelector",
    "TopKSelector",
    "UCBSeedSelector",
    "WeightedRandomSeedSelector",
]
