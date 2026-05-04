from __future__ import annotations

import random
from abc import ABC, abstractmethod

from mesmer.core.config import MesmerModel
from mesmer.execution.state import Attempt, Candidate


class Selector(MesmerModel, ABC):
    name: str

    @abstractmethod
    def select_candidates(self, candidates: list[Candidate], limit: int) -> list[Candidate]:
        raise NotImplementedError


class FirstSelector(Selector):
    name: str = "first"

    def select_candidates(self, candidates: list[Candidate], limit: int) -> list[Candidate]:
        return candidates[:limit]


class RandomSelector(Selector):
    name: str = "random"
    seed: int | None = None

    def select_candidates(self, candidates: list[Candidate], limit: int) -> list[Candidate]:
        rng = random.Random(self.seed)
        shuffled = list(candidates)
        rng.shuffle(shuffled)
        return shuffled[:limit]


class AttemptScoreSelector(MesmerModel):
    name: str = "attempt_score"

    def select_attempts(self, attempts: list[Attempt], limit: int) -> list[Attempt]:
        return sorted(
            attempts,
            key=lambda attempt: max(
                (judgement.score for judgement in attempt.judgements),
                default=0.0,
            ),
            reverse=True,
        )[:limit]
