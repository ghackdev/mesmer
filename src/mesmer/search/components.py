from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field, create_model, field_validator

from mesmer.artifacts.messages import Message, assistant_message, system_message, user_message
from mesmer.core.config import MesmerModel
from mesmer.core.constants import (
    DATASET_TARGET_METADATA_KEY,
    DEFAULT_EVALUATOR_PARSE_RETRIES,
    DEFAULT_PROPOSAL_IMPROVEMENT_FIELD,
    DEFAULT_PROPOSAL_PROMPT_FIELD,
    EVALUATOR_FAILURE_POLICY_METADATA_KEY,
    EVALUATOR_FAILURE_REASON_METADATA_KEY,
    EVALUATOR_PARSE_ERRORS_METADATA_KEY,
    EVALUATOR_PARSE_RETRIES_METADATA_KEY,
    EVALUATOR_RAW_OUTPUTS_METADATA_KEY,
)
from mesmer.core.enums import (
    BinaryLabel,
    EvaluationField,
    EvaluatorFailurePolicy,
    EvaluatorFailureReason,
)
from mesmer.core.errors import EvaluatorParseError, StructuredOutputError
from mesmer.execution.state import Candidate
from mesmer.objectives.models import Objective
from mesmer.search.actors import ChatActor
from mesmer.search.models import (
    CandidateTrajectory,
    ConstraintResult,
    EvaluationResult,
    RatingScale,
)

DEFAULT_PROPOSER_USER_PROMPT = "\n".join(
    [
        "Objective:",
        "{objective}",
        "",
        "Target string:",
        "{target}",
        "",
        "Current prompt:",
        "{current_prompt}",
        "",
        "Feedback:",
        "{feedback}",
    ]
)

DEFAULT_RATING_USER_PROMPT = """PROMPT:
{prompt}

AI ASSISTANT RESPONSE:
{response}"""


def template_context(
    objective: Objective,
    trajectory: CandidateTrajectory | None = None,
) -> dict[str, str]:
    target = str(objective.metadata.get(DATASET_TARGET_METADATA_KEY) or objective.goal)
    response = trajectory.last_response.text if trajectory and trajectory.last_response else ""
    score = str(trajectory.best_score) if trajectory else "0"
    current_prompt = trajectory.latest_text if trajectory else ""
    feedback = trajectory.feedback[-1] if trajectory and trajectory.feedback else ""
    return {
        "objective": objective.goal,
        "goal": objective.goal,
        "target": target,
        "target_str": target,
        "prompt": current_prompt,
        "current_prompt": current_prompt,
        "response": response,
        "score": score,
        "feedback": feedback or "No previous feedback.",
    }


class StructuredOutputSpec(MesmerModel):
    prompt_field: str = DEFAULT_PROPOSAL_PROMPT_FIELD
    metadata_fields: tuple[str, ...] = (DEFAULT_PROPOSAL_IMPROVEMENT_FIELD,)


class LabelConstraintOutput(MesmerModel):
    label: BinaryLabel
    reason: str = ""


class RatingEvaluatorOutput(MesmerModel):
    rating: float | str
    reason: str = ""

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, value: float | str) -> float:
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("rating must be a number or numeric string") from exc


def proposal_output_schema(spec: StructuredOutputSpec) -> type[BaseModel]:
    fields: dict[str, tuple[type[str], Field]] = {
        spec.prompt_field: (str, Field(min_length=1))
    }
    for field_name in spec.metadata_fields:
        if field_name != spec.prompt_field:
            fields[field_name] = (str, Field(default=""))
    return create_model("StructuredProposalOutput", __base__=MesmerModel, **fields)


class Proposer(MesmerModel, ABC):
    name: str

    @abstractmethod
    async def propose(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
        count: int,
        max_parallel: int = 1,
    ) -> list[CandidateTrajectory]:
        raise NotImplementedError


class StructuredLLMProposer(Proposer):
    actor: ChatActor
    system_prompt_template: str
    initial_user_prompt_template: str | None = None
    user_prompt_template: str = DEFAULT_PROPOSER_USER_PROMPT
    output: StructuredOutputSpec = Field(default_factory=StructuredOutputSpec)
    history_window: int | None = Field(default=None, ge=1)
    generation_params: dict[str, Any] = Field(default_factory=dict)
    name: str = "structured_llm_proposer"

    async def propose(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
        count: int,
        max_parallel: int = 1,
    ) -> list[CandidateTrajectory]:
        context = template_context(objective, trajectory)
        user_template = self.user_prompt_template
        if not trajectory.actor_history and self.initial_user_prompt_template is not None:
            user_template = self.initial_user_prompt_template
        user = user_message(user_template.format(**context))
        messages = [
            system_message(self.system_prompt_template.format(**context)),
            *trajectory.actor_history,
            user,
        ]
        schema = proposal_output_schema(self.output)

        async def generate_child(branch_index: int) -> CandidateTrajectory:
            completion = await self.actor.complete_structured(
                messages,
                schema,
                **self.generation_params,
            )
            payload = completion.parsed
            prompt = str(getattr(payload, self.output.prompt_field, "")).strip()
            if not prompt:
                raise ValueError(
                    f"Structured proposer output missing '{self.output.prompt_field}'."
                )
            metadata = {
                "proposer": self.name,
                "actor": self.actor.name,
                "parent_trajectory_id": trajectory.id,
                "branch_index": branch_index,
                "raw_model_output": completion.raw,
            }
            for field_name in self.output.metadata_fields:
                metadata[field_name] = str(getattr(payload, field_name, "")).strip()
            actor_history = self._trim_history(
                [
                    *trajectory.actor_history,
                    user,
                    assistant_message(completion.raw),
                ]
            )
            return CandidateTrajectory(
                candidate=Candidate(messages=[user_message(prompt)], metadata=dict(metadata)),
                depth=trajectory.depth + 1,
                parent_id=trajectory.id,
                actor_history=actor_history,
                feedback=list(trajectory.feedback),
                metadata=metadata,
            )

        if max_parallel <= 1:
            return [await generate_child(branch_index) for branch_index in range(count)]
        return list(
            await _gather_limited(
                range(count),
                max_parallel,
                generate_child,
            )
        )

    def _trim_history(self, messages: list[Message]) -> list[Message]:
        if self.history_window is None:
            return messages
        return messages[-2 * self.history_window :]


class CandidateConstraint(MesmerModel, ABC):
    name: str

    @abstractmethod
    async def check(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> ConstraintResult:
        raise NotImplementedError


class LLMLabelConstraint(CandidateConstraint):
    actor: ChatActor
    system_prompt_template: str
    pass_label: BinaryLabel = BinaryLabel.YES
    generation_params: dict[str, Any] = Field(default_factory=dict)
    name: str = "llm_label_constraint"

    async def check(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> ConstraintResult:
        context = template_context(objective, trajectory)
        completion = await self.actor.complete_structured(
            [
                system_message(self.system_prompt_template.format(**context)),
                user_message(trajectory.latest_text),
            ],
            LabelConstraintOutput,
            **self.generation_params,
        )
        label = completion.parsed.label
        return ConstraintResult(
            passed=label == self.pass_label,
            label=label.value,
            raw=completion.raw,
            reason=completion.parsed.reason or f"Expected label {self.pass_label.value}.",
            metadata={"constraint": self.name},
        )


class ResponseEvaluator(MesmerModel, ABC):
    name: str

    @abstractmethod
    async def evaluate(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> EvaluationResult:
        raise NotImplementedError


class LLMRatingEvaluator(ResponseEvaluator):
    actor: ChatActor
    system_prompt_template: str
    user_prompt_template: str = DEFAULT_RATING_USER_PROMPT
    scale: RatingScale = Field(default_factory=RatingScale)
    failure_policy: EvaluatorFailurePolicy = EvaluatorFailurePolicy.RAISE
    parse_retries: int = Field(default=DEFAULT_EVALUATOR_PARSE_RETRIES, ge=0)
    generation_params: dict[str, Any] = Field(default_factory=dict)
    name: str = "llm_rating_evaluator"

    async def evaluate(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> EvaluationResult:
        if trajectory.last_response is None:
            raise ValueError("LLMRatingEvaluator requires a target response.")
        context = template_context(objective, trajectory)
        messages = [
            system_message(self.system_prompt_template.format(**context)),
            user_message(self.user_prompt_template.format(**context)),
        ]
        raw_outputs: list[str] = []
        parse_errors: list[dict[str, object]] = []
        for retry_count in range(self.parse_retries + 1):
            try:
                completion = await self.actor.complete_structured(
                    messages,
                    RatingEvaluatorOutput,
                    **self.generation_params,
                )
            except StructuredOutputError as exc:
                raw_outputs.append(exc.raw_output or "")
                parse_errors.append(
                    {
                        "retry_count": retry_count,
                        "parser_error": str(exc),
                    }
                )
                if retry_count < self.parse_retries:
                    continue
                if self.failure_policy == EvaluatorFailurePolicy.RAISE:
                    raise EvaluatorParseError(
                        "Evaluator output could not be validated as structured rating.",
                        raw_outputs=raw_outputs,
                        parse_errors=parse_errors,
                    ) from exc
                return self._failed_result(raw_outputs, parse_errors)
            raw_outputs.append(completion.raw)
            return self._parsed_result(
                completion.parsed.rating,
                completion.raw,
                completion.parsed.reason,
                raw_outputs,
                parse_errors,
            )
        return self._failed_result(raw_outputs, parse_errors)

    def _parsed_result(
        self,
        score: float,
        text: str,
        reason: str,
        raw_outputs: list[str],
        parse_errors: list[dict[str, object]],
    ) -> EvaluationResult:
        score = max(self.scale.min, min(self.scale.max, score))
        return EvaluationResult(
            name=self.name,
            score=score,
            normalized_score=self.scale.normalize(score),
            raw=text,
            reason=reason or "Validated structured rating.",
            metadata=self._metadata(raw_outputs, parse_errors),
        )

    def _failed_result(
        self,
        raw_outputs: list[str],
        parse_errors: list[dict[str, object]],
    ) -> EvaluationResult:
        score = self.scale.min
        return EvaluationResult(
            name=self.name,
            score=score,
            normalized_score=self.scale.normalize(score),
            passed=False,
            raw=raw_outputs[-1] if raw_outputs else None,
            reason="Evaluator output could not be validated as structured rating.",
            metadata={
                **self._metadata(raw_outputs, parse_errors),
                EVALUATOR_FAILURE_REASON_METADATA_KEY: (
                    EvaluatorFailureReason.MALFORMED_OUTPUT.value
                ),
                EVALUATOR_FAILURE_POLICY_METADATA_KEY: self.failure_policy.value,
            },
        )

    def _metadata(
        self,
        raw_outputs: list[str],
        parse_errors: list[dict[str, object]],
    ) -> dict[str, Any]:
        return {
            "scale_min": self.scale.min,
            "scale_max": self.scale.max,
            EVALUATOR_PARSE_RETRIES_METADATA_KEY: self.parse_retries,
            EVALUATOR_RAW_OUTPUTS_METADATA_KEY: raw_outputs,
            EVALUATOR_PARSE_ERRORS_METADATA_KEY: parse_errors,
        }


class FeedbackBuilder(MesmerModel, ABC):
    name: str

    @abstractmethod
    def build(self, objective: Objective, trajectory: CandidateTrajectory) -> str:
        raise NotImplementedError


class TemplateFeedback(FeedbackBuilder):
    template: str
    name: str = "template_feedback"

    def __init__(self, template: str | None = None, **data: object) -> None:
        if template is not None and "template" not in data:
            data["template"] = template
        super().__init__(**data)

    def build(self, objective: Objective, trajectory: CandidateTrajectory) -> str:
        return self.template.format(**template_context(objective, trajectory))


class FrontierSelector(MesmerModel, ABC):
    name: str

    @abstractmethod
    def select(
        self,
        trajectories: list[CandidateTrajectory],
        width: int,
    ) -> list[CandidateTrajectory]:
        raise NotImplementedError


class TopKSelector(FrontierSelector):
    k: int | None = None
    field: EvaluationField = EvaluationField.SCORE
    name: str = "top_k"

    def select(
        self,
        trajectories: list[CandidateTrajectory],
        width: int,
    ) -> list[CandidateTrajectory]:
        limit = self.k or width

        def score(trajectory: CandidateTrajectory) -> float:
            if self.field == EvaluationField.NORMALIZED_SCORE:
                return trajectory.best_normalized_score
            if self.field == EvaluationField.PASSED:
                return float(any(evaluation.passed for evaluation in trajectory.evaluations))
            return trajectory.best_score

        return sorted(trajectories, key=score, reverse=True)[:limit]


class ConstraintScoreSelector(FrontierSelector):
    constraint: str | None = None
    k: int | None = None
    drop_failed: bool = True
    name: str = "constraint_score"

    def select(
        self,
        trajectories: list[CandidateTrajectory],
        width: int,
    ) -> list[CandidateTrajectory]:
        limit = self.k or width

        def latest_result(trajectory: CandidateTrajectory) -> ConstraintResult | None:
            for result in reversed(trajectory.constraints):
                if self.constraint is None or result.metadata.get("constraint") == self.constraint:
                    return result
            return None

        def score(trajectory: CandidateTrajectory) -> float:
            result = latest_result(trajectory)
            if result is None:
                return 0.0
            return 1.0 if result.passed else 0.0

        ranked = sorted(trajectories, key=score, reverse=True)
        if self.drop_failed:
            ranked = [trajectory for trajectory in ranked if score(trajectory) > 0]
        return ranked[:limit]


class TerminationCondition(MesmerModel, ABC):
    name: str

    @abstractmethod
    def satisfied(self, trajectory: CandidateTrajectory) -> bool:
        raise NotImplementedError


class ScoreAtLeast(TerminationCondition):
    score: float
    field: EvaluationField = EvaluationField.SCORE
    name: str = "score_at_least"

    def __init__(self, score: float | None = None, **data: object) -> None:
        if score is not None and "score" not in data:
            data["score"] = score
        super().__init__(**data)

    def satisfied(self, trajectory: CandidateTrajectory) -> bool:
        if self.field == EvaluationField.NORMALIZED_SCORE:
            return trajectory.best_normalized_score >= self.score
        return trajectory.best_score >= self.score


async def _gather_limited(items, limit: int, fn):
    if limit <= 1:
        return [await fn(item) for item in items]
    import asyncio

    semaphore = asyncio.Semaphore(limit)

    async def run(item):
        async with semaphore:
            return await fn(item)

    return await asyncio.gather(*(run(item) for item in items))
