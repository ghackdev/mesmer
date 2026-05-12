from __future__ import annotations

from typing import Any

from pydantic import Field

from mesmer.core.errors import ConfigError
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
    allow_prompt_echo: bool = True
    scale: RatingScale = Field(default_factory=lambda: RatingScale(min=0, max=1))
    name: str = "contains"

    async def evaluate(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> EvaluationResult:
        response = trajectory.last_response.text if trajectory.last_response else ""
        prompt = "\n".join(message.content for message in trajectory.candidate.messages)
        if self.case_sensitive:
            needle = self.text
            response_haystack = response
            prompt_haystack = prompt
        else:
            needle = self.text.lower()
            response_haystack = response.lower()
            prompt_haystack = prompt.lower()

        response_contains_text = needle in response_haystack
        prompt_contains_text = needle in prompt_haystack
        passed = response_contains_text and (
            self.allow_prompt_echo or not prompt_contains_text
        )
        score = 1.0 if passed else 0.0
        if self.allow_prompt_echo:
            reason = "Expected text found." if passed else "Expected text not found."
        else:
            reason = (
                "Expected text found in response without prompt echo."
                if passed
                else (
                    "Expected text not found in response, or candidate prompt already "
                    "contained it."
                )
            )
        return EvaluationResult(
            name=self.name,
            score=score,
            normalized_score=self.scale.normalize(score),
            passed=passed,
            reason=reason,
            metadata={
                "allow_prompt_echo": self.allow_prompt_echo,
                "prompt_contains_text": prompt_contains_text,
                "response_contains_text": response_contains_text,
            },
        )


class StartsWith(ResponseEvaluator):
    prefixes: tuple[str, ...]
    case_sensitive: bool = True
    strip: bool = True
    scale: RatingScale = Field(default_factory=lambda: RatingScale(min=0, max=1))
    name: str = "starts_with"

    def model_post_init(self, __context: Any) -> None:
        self._validate_prefixes()

    def _validate_prefixes(self) -> None:
        if not self.prefixes:
            raise ConfigError("evaluators.StartsWith requires at least one prefix.")

    async def evaluate(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> EvaluationResult:
        self._validate_prefixes()
        response = trajectory.last_response.text if trajectory.last_response else ""
        haystack = response.strip() if self.strip else response
        prefixes = self.prefixes
        if not self.case_sensitive:
            haystack = haystack.lower()
            prefixes = tuple(prefix.lower() for prefix in prefixes)
        matched = next((prefix for prefix in prefixes if haystack.startswith(prefix)), None)
        passed = matched is not None
        score = 1.0 if passed else 0.0
        return EvaluationResult(
            name=self.name,
            score=score,
            normalized_score=self.scale.normalize(score),
            passed=passed,
            reason="Expected prefix found." if passed else "Expected prefix not found.",
            metadata={"matched_prefix": matched, "prefixes": list(self.prefixes)},
        )


class NotContainsAny(ResponseEvaluator):
    phrases: tuple[str, ...]
    case_sensitive: bool = True
    scale: RatingScale = Field(default_factory=lambda: RatingScale(min=0, max=1))
    name: str = "not_contains_any"

    async def evaluate(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> EvaluationResult:
        response = trajectory.last_response.text if trajectory.last_response else ""
        haystack = response if self.case_sensitive else response.lower()
        phrases = self.phrases if self.case_sensitive else tuple(
            phrase.lower() for phrase in self.phrases
        )
        found = [
            original
            for original, phrase in zip(self.phrases, phrases, strict=True)
            if phrase in haystack
        ]
        passed = not found
        score = 1.0 if passed else 0.0
        return EvaluationResult(
            name=self.name,
            score=score,
            normalized_score=self.scale.normalize(score),
            passed=passed,
            reason="No blocked phrases found." if passed else "Blocked phrase found.",
            metadata={"found_phrases": found, "phrases": list(self.phrases)},
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
            raise ConfigError(
                "evaluators.Criteria requires objective.success criteria. Add success "
                "criteria to the Objective or use an explicit evaluator such as "
                "evaluators.Contains."
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


class JudgePanel(ResponseEvaluator):
    evaluators: list[ResponseEvaluator] = Field(default_factory=list)
    name: str = "judge_panel"

    def model_post_init(self, __context: Any) -> None:
        self._validate_evaluators()

    def _validate_evaluators(self) -> None:
        if not self.evaluators:
            raise ConfigError("evaluators.JudgePanel requires at least one evaluator.")

    async def evaluate(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> EvaluationResult:
        self._validate_evaluators()
        results = [
            await evaluator.evaluate(objective, trajectory)
            for evaluator in self.evaluators
        ]
        normalized_score = sum(result.normalized_score for result in results) / len(results)
        passed = any(result.passed is True for result in results)
        return EvaluationResult(
            name=self.name,
            score=normalized_score,
            normalized_score=normalized_score,
            passed=passed,
            reason=(
                "At least one panel evaluator passed."
                if passed
                else "No panel evaluator passed."
            ),
            metadata={
                "aggregation": "mean_normalized_score_any_pass",
                "evaluators": [evaluator.name for evaluator in self.evaluators],
                "results": [result.model_dump(mode="json") for result in results],
            },
        )


__all__ = [
    "Contains",
    "Criteria",
    "EmbeddingClassifier",
    "EmbeddingClassifierSequenceClassifier",
    "EmbeddingProvider",
    "HuggingFaceSequenceClassifier",
    "JudgePanel",
    "LLMRatingEvaluator",
    "NotContainsAny",
    "RatingScale",
    "ResponseEvaluator",
    "SentenceTransformersEmbeddingProvider",
    "SequenceClassifier",
    "SequenceClassifierEvaluator",
    "SklearnMLPEmbeddingClassifier",
    "StartsWith",
]
