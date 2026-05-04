from __future__ import annotations

from mesmer.core.enums import JudgementStatus
from mesmer.judging.base import Judge, Judgement
from mesmer.objectives.models import Objective
from mesmer.targets.base import TargetResponse


class ToolActionJudge(Judge):
    tool_name: str
    name: str = "tool_action"

    async def judge(self, objective: Objective, response: TargetResponse) -> Judgement:
        tool_calls = response.metadata.get("tool_calls", [])
        matched = any(
            call.get("name") == self.tool_name
            for call in tool_calls
            if isinstance(call, dict)
        )
        return Judgement(
            status=JudgementStatus.PASS if matched else JudgementStatus.FAIL,
            score=1.0 if matched else 0.0,
            reason=f"Tool {self.tool_name} {'called' if matched else 'not called'}.",
        )
