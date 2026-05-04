from __future__ import annotations

from mesmer.judging.base import Judge, Judgement
from mesmer.objectives.criteria import Regex as RegexCriterion
from mesmer.objectives.models import Objective
from mesmer.targets.base import TargetResponse


class RegexJudge(Judge):
    pattern: str
    flags: int = 0
    name: str = "regex"

    async def judge(self, objective: Objective, response: TargetResponse) -> Judgement:
        result = RegexCriterion(pattern=self.pattern, flags=self.flags).evaluate_text(response.text)
        return Judgement(
            status=result.status,
            score=result.score,
            reason=result.reason,
            criterion_results=[result],
        )
