from __future__ import annotations

from mesmer.core.enums import JudgementStatus
from mesmer.judging.base import Judge, Judgement
from mesmer.objectives.criteria import Contains as ContainsCriterion
from mesmer.objectives.models import Objective
from mesmer.targets.base import TargetResponse


class CriteriaJudge(Judge):
    name: str = "criteria"

    async def judge(self, objective: Objective, response: TargetResponse) -> Judgement:
        results = [criterion.evaluate_text(response.text) for criterion in objective.success]
        if not results:
            return Judgement(
                status=JudgementStatus.UNKNOWN,
                score=0.0,
                reason="Objective has no success criteria.",
            )
        passed = all(result.status == JudgementStatus.PASS for result in results)
        score = sum(result.score for result in results) / len(results)
        return Judgement(
            status=JudgementStatus.PASS if passed else JudgementStatus.FAIL,
            score=score,
            reason="All criteria passed." if passed else "One or more criteria failed.",
            criterion_results=results,
        )


class Contains(Judge):
    text: str
    case_sensitive: bool = False
    name: str = "contains"

    async def judge(self, objective: Objective, response: TargetResponse) -> Judgement:
        criterion = ContainsCriterion(
            text=self.text,
            case_sensitive=self.case_sensitive,
        )
        result = criterion.evaluate_text(response.text)
        return Judgement(
            status=result.status,
            score=result.score,
            reason=result.reason,
            criterion_results=[result],
        )
