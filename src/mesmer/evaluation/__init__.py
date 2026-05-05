from __future__ import annotations

from pydantic import Field

from mesmer.objectives.models import Objective
from mesmer.search.components import LLMRatingEvaluator, ResponseEvaluator
from mesmer.search.fuzzing import (
    EmbeddingClassifier,
    EmbeddingClassifierSequenceClassifier,
    EmbeddingProvider,
    HuggingFaceSequenceClassifier,
    SentenceTransformersEmbeddingProvider,
    SequenceClassifier,
    SequenceClassifierEvaluator,
    SklearnMLPEmbeddingClassifier,
)
from mesmer.search.models import CandidateTrajectory, EvaluationResult, RatingScale
from mesmer.search.technique import Assess as _Assess

Evaluator = ResponseEvaluator
LLMRating = LLMRatingEvaluator
SequenceClassification = SequenceClassifierEvaluator
EmbeddingSequenceClassifier = EmbeddingClassifierSequenceClassifier
SentenceTransformersEmbeddings = SentenceTransformersEmbeddingProvider
SklearnMLP = SklearnMLPEmbeddingClassifier


class Contains(Evaluator):
    text: str
    case_sensitive: bool = True
    scale: RatingScale = Field(default_factory=lambda: RatingScale(min=0, max=1))
    name: str = "contains"

    async def evaluate(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> EvaluationResult:
        response = trajectory.last_response.text if trajectory.last_response else ""
        haystack = response if self.case_sensitive else response.lower()
        needle = self.text if self.case_sensitive else self.text.lower()
        passed = needle in haystack
        score = 1.0 if passed else 0.0
        return EvaluationResult(
            name=self.name,
            score=score,
            normalized_score=self.scale.normalize(score),
            passed=passed,
            reason="Expected text found." if passed else "Expected text not found.",
        )


class Criteria(Evaluator):
    scale: RatingScale = Field(default_factory=lambda: RatingScale(min=0, max=1))
    name: str = "criteria"

    async def evaluate(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> EvaluationResult:
        if trajectory.last_response is None:
            raise ValueError("Criteria evaluator requires a target response.")
        if not objective.success:
            return EvaluationResult(
                name=self.name,
                score=0.0,
                normalized_score=0.0,
                passed=None,
                reason="Objective has no success criteria.",
            )
        results = [
            criterion.evaluate(trajectory.last_response.text)
            for criterion in objective.success
        ]
        passed = all(result.status.value == "pass" for result in results)
        score = 1.0 if passed else 0.0
        return EvaluationResult(
            name=self.name,
            score=score,
            normalized_score=self.scale.normalize(score),
            passed=passed,
            reason="All criteria passed." if passed else "At least one criterion failed.",
            metadata={
                "criterion_results": [
                    result.model_dump(mode="json") for result in results
                ]
            },
        )


class Assess(_Assess):
    def __init__(
        self,
        evaluator: Evaluator | None = None,
        *,
        evaluators: list[Evaluator] | None = None,
        **data: object,
    ) -> None:
        if evaluator is not None and "evaluators" not in data:
            data["evaluators"] = [evaluator]
        if evaluators is not None and "evaluators" not in data:
            data["evaluators"] = evaluators
        super().__init__(**data)


__all__ = [
    "Assess",
    "Contains",
    "Criteria",
    "EmbeddingClassifier",
    "EmbeddingProvider",
    "EmbeddingSequenceClassifier",
    "Evaluator",
    "HuggingFaceSequenceClassifier",
    "LLMRating",
    "RatingScale",
    "SentenceTransformersEmbeddings",
    "SequenceClassification",
    "SequenceClassifier",
    "SklearnMLP",
]
