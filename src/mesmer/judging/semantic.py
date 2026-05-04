from __future__ import annotations

from mesmer.judging.base import Judge, Judgement
from mesmer.judging.exact import CriteriaJudge
from mesmer.objectives.models import Objective
from mesmer.targets.base import TargetResponse


class SemanticJudge(Judge):
    """Placeholder semantic judge.

    V1 keeps this safe and deterministic unless users wire their own LLM judge.
    """

    name: str = "semantic"
    fallback: CriteriaJudge = CriteriaJudge()

    async def judge(self, objective: Objective, response: TargetResponse) -> Judgement:
        return await self.fallback.judge(objective, response)
