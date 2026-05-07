from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import Any

from pydantic import Field

from mesmer.artifacts.messages import assistant_message, user_message
from mesmer.core.constants import SUCCESS_TERMINATION_REASON
from mesmer.core.enums import JudgementStatus, TargetBinding
from mesmer.core.errors import EvaluatorParseError
from mesmer.execution.state import Attempt, Candidate
from mesmer.flows.base import AttackContext
from mesmer.judging.base import Judgement
from mesmer.search.components import (
    FeedbackBuilder,
    FrontierSelector,
    Proposer,
    ResponseEvaluator,
    TerminationCondition,
    TopKSelector,
)
from mesmer.search.fuzzing import (
    PromptMutator,
    PromptSeedRecord,
    SeedPoolSource,
    SeedSelectionPolicy,
    WeightedRandomSeedSelector,
)
from mesmer.search.models import CandidateTrajectory, EvaluationResult, SearchPolicy
from mesmer.state import (
    Attempts,
    Evaluations,
    Feedback,
    Frontier,
    Iteration,
    Objective,
    Patch,
    PopulationPool,
    RewardLedger,
    State,
    StopSignal,
    TargetResponses,
)
from mesmer.targets.base import Target, TargetContext
from mesmer.workflow import Operator


class SeedFromObjective(Operator):
    name: str = "seed_from_objective"
    reads: set[type] = Field(default_factory=lambda: {Objective})
    writes: set[type] = Field(default_factory=lambda: {Frontier})

    async def run(self, state: State, context: AttackContext) -> Patch:
        objective = state.objective
        messages = list(objective.initial_state.messages) or [user_message(objective.goal)]
        trajectory = CandidateTrajectory(
            candidate=Candidate(messages=messages, metadata={"seed": self.name})
        )
        return Patch.set(Frontier(items=[trajectory]))


class Propose(Operator):
    proposer: Proposer
    branching: int | None = Field(default=None, ge=1)
    max_parallel: int | None = Field(default=None, ge=1)
    name: str = "propose"
    reads: set[type] = Field(default_factory=lambda: {Objective, Frontier})
    writes: set[type] = Field(default_factory=lambda: {Frontier})

    def __init__(self, proposer: Proposer | None = None, **data: object) -> None:
        if proposer is not None and "proposer" not in data:
            data["proposer"] = proposer
        super().__init__(**data)

    async def run(self, state: State, context: AttackContext) -> Patch:
        policy = _policy(context)
        count = self.branching or policy.branching_factor
        max_parallel = self.max_parallel or policy.max_parallel
        proposed: list[CandidateTrajectory] = []
        for trajectory in state.get(Frontier).items:
            proposed.extend(
                await self.proposer.propose(
                    state.objective,
                    trajectory,
                    count,
                    max_parallel=max_parallel,
                )
            )
        context.logger.emit(
            "operator.propose.finish",
            proposer=self.proposer.name,
            candidates=len(proposed),
        )
        return Patch.set(Frontier(items=proposed))


class QueryTarget(Operator):
    target: Target | TargetBinding = TargetBinding.DEFAULT
    max_parallel: int | None = Field(default=None, ge=1)
    name: str = "query_target"
    reads: set[type] = Field(default_factory=lambda: {Objective, Frontier, Attempts})
    writes: set[type] = Field(default_factory=lambda: {Attempts, TargetResponses})

    async def run(self, state: State, context: AttackContext) -> Patch:
        target = self._resolve_target(context)
        policy = _policy(context)
        max_parallel = self.max_parallel or policy.max_parallel
        iteration = state.get(Iteration).value

        async def query_trajectory(trajectory: CandidateTrajectory) -> Attempt:
            context.budget_tracker.record_query()
            context.logger.emit(
                "target.call",
                iteration=iteration,
                trajectory_id=trajectory.id,
                message=trajectory.latest_text,
            )
            response = await target.call(
                trajectory.candidate.messages,
                TargetContext(objective=state.objective, variables=state.attack_state.variables),
            )
            trajectory.last_response = response
            context.logger.emit(
                "target.response",
                iteration=iteration,
                response_id=response.id,
                text=response.text,
                latency_ms=response.latency_ms,
                finish_reason=response.metadata.get("finish_reason"),
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
            )
            return Attempt(
                objective=state.objective,
                candidate=trajectory.candidate,
                response=response,
                judgements=[],
                turn=max(1, iteration),
                metadata={"trajectory_id": trajectory.id, "depth": trajectory.depth},
            )

        attempts = await _gather_limited(state.get(Frontier).items, max_parallel, query_trajectory)
        state.target_calls += len(attempts)
        existing_attempts = list(state.get(Attempts).items)
        existing_responses = list(state.get(TargetResponses).items)
        responses = [*existing_responses, *(attempt.response for attempt in attempts)]
        return Patch.set(
            Attempts(items=[*existing_attempts, *attempts]),
            TargetResponses(items=responses),
        )

    def _resolve_target(self, context: AttackContext) -> Target:
        if self.target == TargetBinding.DEFAULT:
            return context.target
        return self.target


class ContinueConversation(Operator):
    name: str = "continue_conversation"
    reads: set[type] = Field(default_factory=lambda: {Frontier, TargetResponses})
    writes: set[type] = Field(default_factory=lambda: {Frontier})

    async def run(self, state: State, context: AttackContext) -> Patch:
        continued = 0
        for trajectory in state.get(Frontier).items:
            if trajectory.last_response is None:
                continue
            trajectory.candidate.messages.append(assistant_message(trajectory.last_response.text))
            continued += 1
        context.logger.emit("conversation.continue", candidates=continued)
        return Patch.set(Frontier(items=state.get(Frontier).items))


class Evaluate(Operator):
    evaluators: list[ResponseEvaluator] = Field(default_factory=list)
    max_parallel: int | None = Field(default=None, ge=1)
    name: str = "evaluate"
    reads: set[type] = Field(
        default_factory=lambda: {Objective, Frontier, Attempts, TargetResponses}
    )
    writes: set[type] = Field(default_factory=lambda: {Evaluations, Attempts})

    def __init__(
        self,
        evaluator: ResponseEvaluator | None = None,
        *,
        evaluators: list[ResponseEvaluator] | None = None,
        **data: object,
    ) -> None:
        if evaluator is not None and "evaluators" not in data:
            data["evaluators"] = [evaluator]
        if evaluators is not None and "evaluators" not in data:
            data["evaluators"] = evaluators
        super().__init__(**data)

    async def run(self, state: State, context: AttackContext) -> Patch:
        policy = _policy(context)
        max_parallel = self.max_parallel or policy.max_parallel

        async def evaluate_trajectory(
            trajectory: CandidateTrajectory,
        ) -> tuple[CandidateTrajectory, list[EvaluationResult]]:
            evaluations: list[EvaluationResult] = []
            for evaluator in self.evaluators:
                context.logger.emit(
                    "operator.evaluate.call",
                    evaluator=evaluator.name,
                    trajectory_id=trajectory.id,
                )
                try:
                    evaluation = await evaluator.evaluate(state.objective, trajectory)
                except EvaluatorParseError:
                    raise
                evaluations.append(evaluation)
                context.logger.emit(
                    "operator.evaluate.result",
                    evaluator=evaluator.name,
                    trajectory_id=trajectory.id,
                    score=evaluation.score,
                    normalized_score=evaluation.normalized_score,
                    passed=evaluation.passed,
                    reason=evaluation.reason,
                )
            return trajectory, evaluations

        evaluated = await _gather_limited(
            state.get(Frontier).items,
            max_parallel,
            evaluate_trajectory,
        )
        all_evaluations = list(state.get(Evaluations).items)
        attempts = list(state.get(Attempts).items)
        for trajectory, evaluations in evaluated:
            trajectory.evaluations.extend(evaluations)
            all_evaluations.extend(evaluations)
            state.observe(trajectory)
            attempt = _attach_judgements(attempts, trajectory, evaluations)
            if attempt is not None and context.recorder is not None:
                await context.recorder.record_attempt(attempt)
        return Patch.set(Evaluations(items=all_evaluations), Attempts(items=attempts))


class StopWhen(Operator):
    condition: TerminationCondition
    stop_on_success: bool | None = None
    name: str = "stop_when"
    reads: set[type] = Field(default_factory=lambda: {Frontier, Evaluations})
    writes: set[type] = Field(default_factory=lambda: {StopSignal})

    def __init__(self, condition: TerminationCondition | None = None, **data: object) -> None:
        if condition is not None and "condition" not in data:
            data["condition"] = condition
        super().__init__(**data)

    async def run(self, state: State, context: AttackContext) -> Patch:
        policy = _policy(context)
        stop_on_success = (
            policy.stop_on_success
            if self.stop_on_success is None
            else self.stop_on_success
        )
        for trajectory in state.get(Frontier).items:
            if not self.condition.satisfied(trajectory):
                continue
            context.logger.emit(
                "operator.stop",
                reason=SUCCESS_TERMINATION_REASON,
                condition=self.condition.name,
                score=trajectory.best_score,
            )
            if stop_on_success:
                return Patch.stop(
                    SUCCESS_TERMINATION_REASON,
                    success_trajectory_id=trajectory.id,
                )
        return Patch()


class Select(Operator):
    selector: FrontierSelector = Field(default_factory=TopKSelector)
    width: int | None = Field(default=None, ge=1)
    name: str = "select"
    reads: set[type] = Field(default_factory=lambda: {Frontier})
    writes: set[type] = Field(default_factory=lambda: {Frontier})

    def __init__(self, selector: FrontierSelector | None = None, **data: object) -> None:
        if selector is not None and "selector" not in data:
            data["selector"] = selector
        super().__init__(**data)

    async def run(self, state: State, context: AttackContext) -> Patch:
        policy = _policy(context)
        width = self.width or policy.width
        selected = self.selector.select(state.get(Frontier).items, width)
        context.logger.emit(
            "operator.select.finish",
            selector=self.selector.name,
            candidates=len(selected),
        )
        return Patch.set(Frontier(items=selected))


class AddFeedback(Operator):
    feedback: FeedbackBuilder | None = None
    name: str = "add_feedback"
    reads: set[type] = Field(default_factory=lambda: {Objective, Frontier})
    writes: set[type] = Field(default_factory=lambda: {Frontier, Feedback})

    async def run(self, state: State, context: AttackContext) -> Patch:
        feedback_items = list(state.get(Feedback).items)
        if self.feedback is not None:
            for trajectory in state.get(Frontier).items:
                value = self.feedback.build(state.objective, trajectory)
                trajectory.feedback.append(value)
                feedback_items.append(value)
        return Patch.set(Frontier(items=state.get(Frontier).items), Feedback(items=feedback_items))


class LoadPopulation(Operator):
    source: SeedPoolSource
    count: int | None = Field(default=None, ge=1)
    name: str = "load_population"
    reads: set[type] = Field(default_factory=lambda: {Objective})
    writes: set[type] = Field(default_factory=lambda: {PopulationPool})

    async def run(self, state: State, context: AttackContext) -> Patch:
        records = await self.source.load(state.objective, _source_context(context), self.count)
        return Patch.set(
            PopulationPool(pool=type(state.get(PopulationPool).pool)(records=records)),
            population_size=len(records),
            population_source=self.source.name,
        )


class GenerateFromPopulation(Operator):
    selector: SeedSelectionPolicy = Field(default_factory=WeightedRandomSeedSelector)
    mutator: PromptMutator
    branching: int | None = Field(default=None, ge=1)
    name: str = "generate_from_population"
    reads: set[type] = Field(default_factory=lambda: {Objective, PopulationPool})
    writes: set[type] = Field(default_factory=lambda: {Frontier, PopulationPool})

    async def run(self, state: State, context: AttackContext) -> Patch:
        import random

        policy = _policy(context)
        count = self.branching or policy.branching_factor
        pool = state.get(PopulationPool).pool
        rng = random.Random(pool.selection_step)
        generated: list[CandidateTrajectory] = []
        for branch_index in range(count):
            seed_index = self.selector.select(pool, rng)
            seed = pool.selected(seed_index)
            mutated = await self.mutator.mutate(seed.text, rng)
            prompt = _materialize_prompt(mutated.text, state.objective)
            metadata = {
                "seed_id": seed.id,
                "seed_index": seed_index,
                "seed_text": seed.text,
                "selector": self.selector.name,
                "mutator": self.mutator.name,
                "branch_index": branch_index,
                "mutated_template": mutated.text,
                "replacements": mutated.replacements,
                "mutation_metadata": mutated.metadata,
            }
            generated.append(
                CandidateTrajectory(
                    candidate=Candidate(messages=[user_message(prompt)], metadata=metadata),
                    metadata=metadata,
                )
            )
        context.logger.emit(
            "operator.population.generate",
            selector=self.selector.name,
            mutator=self.mutator.name,
            candidates=len(generated),
        )
        return Patch.set(Frontier(items=generated), PopulationPool(pool=pool))


class AssignReward(Operator):
    success_score: float = 1.0
    reward_scale: float = 1.0
    add_successful_seeds: bool = True
    name: str = "assign_reward"
    reads: set[type] = Field(
        default_factory=lambda: {Frontier, Evaluations, PopulationPool, RewardLedger}
    )
    writes: set[type] = Field(default_factory=lambda: {PopulationPool, RewardLedger})

    async def run(self, state: State, context: AttackContext) -> Patch:
        pool = state.get(PopulationPool).pool
        ledger = dict(state.get(RewardLedger).rewards)
        successes = 0
        for trajectory in state.get(Frontier).items:
            seed_index = trajectory.metadata.get("seed_index")
            if not isinstance(seed_index, int) or seed_index >= len(pool.records):
                continue
            seed = pool.records[seed_index]
            seed.attempts += 1
            score = trajectory.best_score
            reward = score * self.reward_scale
            seed.reward += reward
            seed.weight = max(0.001, seed.weight + reward)
            ledger[seed.id] = seed.reward
            if score >= self.success_score:
                seed.successes += 1
                successes += 1
                if self.add_successful_seeds:
                    pool.append(
                        PromptSeedRecord(
                            text=str(trajectory.metadata.get("mutated_template") or seed.text),
                            parent_id=seed.id,
                            weight=max(1.0, reward),
                            metadata={
                                "source": self.name,
                                "trajectory_id": trajectory.id,
                                "parent_seed_id": seed.id,
                            },
                        )
                    )
        context.logger.emit(
            "operator.population.reward",
            population_size=len(pool.records),
            successes=successes,
        )
        return Patch.set(
            PopulationPool(pool=pool),
            RewardLedger(rewards=ledger),
            population_size=len(pool.records),
            successful_candidates=successes,
        )


def _policy(context: AttackContext) -> SearchPolicy:
    policy = getattr(context, "policy", None)
    if isinstance(policy, SearchPolicy):
        return policy
    return SearchPolicy()


async def _gather_limited(items: Iterable[Any], limit: int, fn):
    item_list = list(items)
    if limit <= 1:
        return [await fn(item) for item in item_list]
    semaphore = asyncio.Semaphore(limit)

    async def run(item):
        async with semaphore:
            return await fn(item)

    return await asyncio.gather(*(run(item) for item in item_list))


def _attach_judgements(
    attempts: list[Attempt],
    trajectory: CandidateTrajectory,
    evaluations: list[EvaluationResult],
) -> Attempt | None:
    for attempt in reversed(attempts):
        if attempt.metadata.get("trajectory_id") != trajectory.id:
            continue
        attempt.judgements = [
            Judgement(
                status=_status_from_evaluation(evaluation),
                score=evaluation.normalized_score,
                reason=evaluation.reason,
                metadata={
                    "evaluator": evaluation.name,
                    "raw_score": evaluation.score,
                    **evaluation.metadata,
                },
            )
            for evaluation in evaluations
        ]
        attempt.metadata["trace"] = {
            **attempt.metadata.get("trace", {}),
            "trajectory": _trajectory_provenance(trajectory),
        }
        return attempt
    return None


def _status_from_evaluation(evaluation: EvaluationResult) -> JudgementStatus:
    if evaluation.passed is True:
        return JudgementStatus.PASS
    if evaluation.passed is False:
        return JudgementStatus.FAIL
    return JudgementStatus.UNKNOWN


def _trajectory_provenance(trajectory: CandidateTrajectory) -> dict[str, Any]:
    return {
        "id": trajectory.id,
        "parent_id": trajectory.parent_id,
        "depth": trajectory.depth,
        "metadata": trajectory.metadata,
        "candidate_metadata": trajectory.candidate.metadata,
        "actor_history": [
            message.model_dump(mode="json") for message in trajectory.actor_history
        ],
        "feedback": list(trajectory.feedback),
        "constraints": [
            constraint.model_dump(mode="json") for constraint in trajectory.constraints
        ],
        "evaluations": [
            evaluation.model_dump(mode="json") for evaluation in trajectory.evaluations
        ],
    }


def _materialize_prompt(template: str, objective) -> str:
    return (
        template.replace("[INSERT PROMPT HERE]", objective.goal)
        .replace("{question}", objective.goal)
        .replace("{goal}", objective.goal)
        .replace("{objective}", objective.goal)
    )


def _source_context(context: AttackContext):
    from mesmer.runtime.component import RuntimeContext

    return RuntimeContext(attack=context)
