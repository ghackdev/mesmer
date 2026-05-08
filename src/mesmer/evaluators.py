from __future__ import annotations

from pydantic import Field

from mesmer.objectives.models import Objective
from mesmer.population_strategies import (
    EmbeddingClassifier,
    EmbeddingClassifierSequenceClassifier,
    EmbeddingProvider,
    HuggingFaceSequenceClassifier,
    SentenceTransformersEmbeddingProvider,
    SequenceClassifier,
    SequenceClassifierEvaluator,
    SklearnMLPEmbeddingClassifier,
)
from mesmer.strategies import LLMRatingEvaluator, ResponseEvaluator
from mesmer.trajectory import CandidateTrajectory, EvaluationResult, RatingScale


class Contains(ResponseEvaluator):
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


class Criteria(ResponseEvaluator):
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
            criterion.evaluate_text(trajectory.last_response.text)
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


__all__ = [
    "Contains",
    "Criteria",
    "EmbeddingClassifier",
    "EmbeddingClassifierSequenceClassifier",
    "EmbeddingProvider",
    "HuggingFaceSequenceClassifier",
    "LLMRatingEvaluator",
    "RatingScale",
    "ResponseEvaluator",
    "SentenceTransformersEmbeddingProvider",
    "SequenceClassifier",
    "SequenceClassifierEvaluator",
    "SklearnMLPEmbeddingClassifier",
]
