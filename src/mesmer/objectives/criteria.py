from __future__ import annotations

import re
from abc import ABC, abstractmethod

from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.core.enums import JudgementStatus


class CriterionResult(MesmerModel):
    name: str
    status: JudgementStatus
    score: float = Field(ge=0.0, le=1.0)
    reason: str = ""


class Criterion(MesmerModel, ABC):
    name: str

    @abstractmethod
    def evaluate_text(self, text: str) -> CriterionResult:
        raise NotImplementedError


class Contains(Criterion):
    text: str
    case_sensitive: bool = False
    name: str = "contains"

    def evaluate_text(self, text: str) -> CriterionResult:
        haystack = text if self.case_sensitive else text.lower()
        needle = self.text if self.case_sensitive else self.text.lower()
        passed = needle in haystack
        return CriterionResult(
            name=self.name,
            status=JudgementStatus.PASS if passed else JudgementStatus.FAIL,
            score=1.0 if passed else 0.0,
            reason=f"Expected substring {'found' if passed else 'not found'}.",
        )


class Regex(Criterion):
    pattern: str
    flags: int = 0
    name: str = "regex"

    def evaluate_text(self, text: str) -> CriterionResult:
        passed = re.search(self.pattern, text, self.flags) is not None
        return CriterionResult(
            name=self.name,
            status=JudgementStatus.PASS if passed else JudgementStatus.FAIL,
            score=1.0 if passed else 0.0,
            reason=f"Pattern {'matched' if passed else 'did not match'}.",
        )


class AlwaysPass(Criterion):
    name: str = "always_pass"

    def evaluate_text(self, text: str) -> CriterionResult:
        return CriterionResult(
            name=self.name,
            status=JudgementStatus.PASS,
            score=1.0,
            reason="Always-pass criterion.",
        )
