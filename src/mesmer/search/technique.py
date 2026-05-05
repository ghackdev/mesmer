from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from pydantic import Field

from mesmer.artifacts.messages import assistant_message, user_message
from mesmer.core.config import MesmerModel
from mesmer.core.constants import (
    DEFAULT_SEARCH_STOP_REASON,
    EVALUATOR_PARSE_ERRORS_METADATA_KEY,
    EVALUATOR_RAW_OUTPUTS_METADATA_KEY,
    SUCCESS_TERMINATION_REASON,
)
from mesmer.core.enums import JudgementStatus, StateFact, TargetBinding
from mesmer.core.errors import EvaluatorParseError
from mesmer.execution.state import Attempt, Candidate
from mesmer.flows.base import AttackContext, Flow
from mesmer.judging.base import Judgement
from mesmer.objectives.models import Objective
from mesmer.runtime.component import Component, ContainerComponent, Program, RuntimeContext
from mesmer.runtime.executor import ProgramExecutor
from mesmer.runtime.state import RuntimeState, StatePatch, StateSnapshot
from mesmer.search.components import (
    CandidateConstraint,
    FeedbackBuilder,
    FrontierSelector,
    Proposer,
    ResponseEvaluator,
    TerminationCondition,
    TopKSelector,
)
from mesmer.search.models import CandidateTrajectory, EvaluationResult, SearchPolicy
from mesmer.targets.base import Target, TargetContext


class SearchSeed(MesmerModel, ABC):
    name: str

    @abstractmethod
    def build(self, objective: Objective) -> list[CandidateTrajectory]:
        raise NotImplementedError


class ObjectiveSeed(Component, SearchSeed):
    name: str = "objective_seed"
    requires: set[StateFact] = Field(default_factory=lambda: {StateFact.OBJECTIVE})
    provides: set[StateFact] = Field(default_factory=lambda: {StateFact.FRONTIER})

    def build(self, objective: Objective) -> list[CandidateTrajectory]:
        messages = list(objective.initial_state.messages) or [user_message(objective.goal)]
        return [
            CandidateTrajectory(
                candidate=Candidate(messages=messages, metadata={"seed": self.name})
            )
        ]

    async def apply(self, state: RuntimeState, context: RuntimeContext) -> StatePatch:
        return StatePatch(frontier=self.build(state.objective), provided=self.provides)


class Iterate(ContainerComponent):
    policy: SearchPolicy = Field(default_factory=SearchPolicy)
    name: str = "iterate"
    requires: set[StateFact] = Field(default_factory=lambda: {StateFact.FRONTIER})
    provides: set[StateFact] = Field(default_factory=lambda: {StateFact.FRONTIER})

    async def apply(self, state: RuntimeState, context: RuntimeContext) -> StatePatch:
        state.attack_state.metadata["stop_reason"] = DEFAULT_SEARCH_STOP_REASON
        for iteration in range(1, self.policy.iterations + 1):
            if state.stopped:
                break
            state.iteration = iteration
            context.attack.budget_tracker.record_turn()
            context.attack.logger.emit(
                "search.iteration.start",
                iteration=iteration,
                frontier=len(state.frontier),
            )
            for child in self.children:
                if state.stopped:
                    break
                before = StateSnapshot.from_state(state)
                patch = await child.apply(state, context.with_policy(self.policy))
                state.apply_patch(patch)
                after = StateSnapshot.from_state(state)
                state.record_transition(child.name, before, patch, after)
            if not state.stopped and not state.frontier:
                state.apply_patch(StatePatch(stop_reason="frontier_empty"))
        if not state.stopped:
            state.apply_patch(StatePatch(stop_reason=DEFAULT_SEARCH_STOP_REASON))
        return StatePatch(provided=self.provides)


class Propose(Component):
    proposer: Proposer
    name: str = "propose"
    requires: set[StateFact] = Field(default_factory=lambda: {StateFact.FRONTIER})
    provides: set[StateFact] = Field(default_factory=lambda: {StateFact.FRONTIER})

    def __init__(self, proposer: Proposer | None = None, **data: object) -> None:
        if proposer is not None and "proposer" not in data:
            data["proposer"] = proposer
        super().__init__(**data)

    async def apply(self, state: RuntimeState, context: RuntimeContext) -> StatePatch:
        policy = _policy(context)
        proposed: list[CandidateTrajectory] = []
        for trajectory in state.frontier:
            proposed.extend(
                await self.proposer.propose(
                    state.objective,
                    trajectory,
                    policy.branching_factor,
                    max_parallel=policy.max_parallel,
                )
            )
        context.attack.logger.emit(
            "search.propose.finish",
            proposer=self.proposer.name,
            candidates=len(proposed),
        )
        return StatePatch(frontier=proposed, provided=self.provides)


class Constrain(Component):
    constraints: list[CandidateConstraint] = Field(default_factory=list)
    name: str = "constrain"
    requires: set[StateFact] = Field(default_factory=lambda: {StateFact.FRONTIER})
    provides: set[StateFact] = Field(default_factory=lambda: {StateFact.FRONTIER})

    def __init__(
        self,
        *constraints: CandidateConstraint,
        constraints_: list[CandidateConstraint] | None = None,
        **data: object,
    ) -> None:
        if constraints and "constraints" not in data:
            data["constraints"] = list(constraints)
        if constraints_ is not None and "constraints" not in data:
            data["constraints"] = constraints_
        super().__init__(**data)

    async def apply(self, state: RuntimeState, context: RuntimeContext) -> StatePatch:
        policy = _policy(context)

        async def check_trajectory(trajectory: CandidateTrajectory) -> CandidateTrajectory | None:
            passed = True
            for constraint in self.constraints:
                result = await constraint.check(state.objective, trajectory)
                result.metadata.setdefault("constraint", constraint.name)
                trajectory.constraints.append(result)
                context.attack.logger.emit(
                    "search.constraint.result",
                    constraint=constraint.name,
                    passed=result.passed,
                    label=result.label,
                    prompt=trajectory.latest_text,
                )
                if not result.passed:
                    passed = False
                    break
            if passed:
                return trajectory
            return None

        checked = await _gather_limited(
            state.frontier,
            policy.max_parallel,
            check_trajectory,
        )
        kept = [trajectory for trajectory in checked if trajectory is not None]
        context.attack.logger.emit("search.constrain.finish", candidates=len(kept))
        return StatePatch(frontier=kept, provided=self.provides)


class SelectFrontier(Component):
    selector: FrontierSelector = Field(default_factory=TopKSelector)
    name: str = "select_frontier"
    requires: set[StateFact] = Field(default_factory=lambda: {StateFact.FRONTIER})
    provides: set[StateFact] = Field(default_factory=lambda: {StateFact.FRONTIER})

    def __init__(
        self,
        selector: FrontierSelector | None = None,
        **data: object,
    ) -> None:
        if selector is not None and "selector" not in data:
            data["selector"] = selector
        super().__init__(**data)

    async def apply(self, state: RuntimeState, context: RuntimeContext) -> StatePatch:
        policy = _policy(context)
        selected = self.selector.select(state.frontier, policy.width)
        context.attack.logger.emit(
            "search.select.finish",
            selector=self.selector.name,
            candidates=len(selected),
        )
        return StatePatch(frontier=selected, provided=self.provides)


class Query(Component):
    target: Target | TargetBinding = TargetBinding.DEFAULT
    name: str = "query"
    requires: set[StateFact] = Field(default_factory=lambda: {StateFact.FRONTIER})
    provides: set[StateFact] = Field(
        default_factory=lambda: {StateFact.TARGET_RESPONSES, StateFact.ATTEMPTS}
    )

    def __init__(
        self,
        target: Target | TargetBinding | None = None,
        **data: object,
    ) -> None:
        if target is not None and "target" not in data:
            data["target"] = target
        super().__init__(**data)

    async def apply(self, state: RuntimeState, context: RuntimeContext) -> StatePatch:
        target = self._resolve_target(context)
        policy = _policy(context)

        async def query_trajectory(trajectory: CandidateTrajectory) -> Attempt:
            context.attack.budget_tracker.record_query()
            context.attack.logger.emit(
                "target.call",
                iteration=state.iteration,
                trajectory_id=trajectory.id,
                message=trajectory.latest_text,
            )
            response = await target.call(
                trajectory.candidate.messages,
                TargetContext(objective=state.objective, variables=state.attack_state.variables),
            )
            trajectory.last_response = response
            context.attack.logger.emit(
                "target.response",
                iteration=state.iteration,
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
                turn=state.iteration,
                metadata={
                    "trajectory_id": trajectory.id,
                    "depth": trajectory.depth,
                },
            )
        attempts = await _gather_limited(
            state.frontier,
            policy.max_parallel,
            query_trajectory,
        )
        state.target_calls += len(attempts)
        return StatePatch(append_attempts=attempts, provided=self.provides)

    def _resolve_target(self, context: RuntimeContext) -> Target:
        if self.target == TargetBinding.DEFAULT:
            return context.attack.target
        return self.target


class ContinueConversation(Component):
    name: str = "continue_conversation"
    requires: set[StateFact] = Field(
        default_factory=lambda: {StateFact.FRONTIER, StateFact.TARGET_RESPONSES}
    )
    provides: set[StateFact] = Field(
        default_factory=lambda: {StateFact.FRONTIER, StateFact.CONVERSATIONS}
    )

    async def apply(self, state: RuntimeState, context: RuntimeContext) -> StatePatch:
        continued = 0
        for trajectory in state.frontier:
            if trajectory.last_response is None:
                continue
            trajectory.candidate.messages.append(assistant_message(trajectory.last_response.text))
            continued += 1
        context.attack.logger.emit(
            "conversation.continue",
            candidates=continued,
        )
        return StatePatch(frontier=state.frontier, provided=self.provides)


class Assess(Component):
    evaluators: list[ResponseEvaluator] = Field(default_factory=list)
    name: str = "assess"
    requires: set[StateFact] = Field(default_factory=lambda: {StateFact.TARGET_RESPONSES})
    provides: set[StateFact] = Field(default_factory=lambda: {StateFact.EVALUATIONS})

    def __init__(
        self,
        *evaluators: ResponseEvaluator,
        evaluators_: list[ResponseEvaluator] | None = None,
        **data: object,
    ) -> None:
        if evaluators and "evaluators" not in data:
            data["evaluators"] = list(evaluators)
        if evaluators_ is not None and "evaluators" not in data:
            data["evaluators"] = evaluators_
        super().__init__(**data)

    async def apply(self, state: RuntimeState, context: RuntimeContext) -> StatePatch:
        policy = _policy(context)

        async def evaluate_trajectory(
            trajectory: CandidateTrajectory,
        ) -> tuple[CandidateTrajectory, list[EvaluationResult]]:
            evaluations = await self._evaluate(state, context, trajectory)
            return trajectory, evaluations

        evaluated = await _gather_limited(
            state.frontier,
            policy.max_parallel,
            evaluate_trajectory,
        )
        for trajectory, evaluations in evaluated:
            trajectory.evaluations.extend(evaluations)
            state.observe(trajectory)
            attempt = self._attach_judgements(state, trajectory, evaluations)
            if attempt is not None and context.attack.recorder is not None:
                await context.attack.recorder.record_attempt(attempt)
        return StatePatch(provided=self.provides)

    async def _evaluate(
        self,
        state: RuntimeState,
        context: RuntimeContext,
        trajectory: CandidateTrajectory,
    ) -> list[EvaluationResult]:
        evaluations: list[EvaluationResult] = []
        for evaluator in self.evaluators:
            context.attack.logger.emit(
                "search.evaluator.call",
                evaluator=evaluator.name,
                trajectory_id=trajectory.id,
            )
            try:
                evaluation = await evaluator.evaluate(state.objective, trajectory)
            except EvaluatorParseError as exc:
                self._log_evaluator_raw_outputs(
                    context,
                    evaluator.name,
                    trajectory,
                    exc.raw_outputs,
                )
                self._log_evaluator_parse_errors(
                    context,
                    evaluator.name,
                    trajectory,
                    exc.parse_errors,
                )
                raise
            evaluations.append(evaluation)
            self._log_evaluator_diagnostics(context, evaluator.name, trajectory, evaluation)
            context.attack.logger.emit(
                "search.evaluator.result",
                evaluator=evaluator.name,
                trajectory_id=trajectory.id,
                score=evaluation.score,
                normalized_score=evaluation.normalized_score,
                passed=evaluation.passed,
                reason=evaluation.reason,
            )
        return evaluations

    def _log_evaluator_diagnostics(
        self,
        context: RuntimeContext,
        evaluator_name: str,
        trajectory: CandidateTrajectory,
        evaluation: EvaluationResult,
    ) -> None:
        raw_outputs = evaluation.metadata.get(EVALUATOR_RAW_OUTPUTS_METADATA_KEY)
        if isinstance(raw_outputs, list):
            self._log_evaluator_raw_outputs(context, evaluator_name, trajectory, raw_outputs)
        elif evaluation.raw is not None:
            self._log_evaluator_raw_outputs(context, evaluator_name, trajectory, [evaluation.raw])
        parse_errors = evaluation.metadata.get(EVALUATOR_PARSE_ERRORS_METADATA_KEY)
        if isinstance(parse_errors, list):
            self._log_evaluator_parse_errors(context, evaluator_name, trajectory, parse_errors)

    def _log_evaluator_raw_outputs(
        self,
        context: RuntimeContext,
        evaluator_name: str,
        trajectory: CandidateTrajectory,
        raw_outputs: list[Any],
    ) -> None:
        for call_index, raw in enumerate(raw_outputs):
            context.attack.logger.emit(
                "search.evaluator.raw",
                evaluator=evaluator_name,
                trajectory_id=trajectory.id,
                call_index=call_index,
                raw=str(raw),
            )

    def _log_evaluator_parse_errors(
        self,
        context: RuntimeContext,
        evaluator_name: str,
        trajectory: CandidateTrajectory,
        parse_errors: list[Any],
    ) -> None:
        for error in parse_errors:
            payload = error if isinstance(error, dict) else {"parser_error": str(error)}
            context.attack.logger.emit(
                "search.evaluator.parse_error",
                evaluator=evaluator_name,
                trajectory_id=trajectory.id,
                retry_count=payload.get("retry_count"),
                parser_error=payload.get("parser_error"),
            )

    def _attach_judgements(
        self,
        state: RuntimeState,
        trajectory: CandidateTrajectory,
        evaluations: list[EvaluationResult],
    ) -> Attempt | None:
        for attempt in reversed(state.attack_state.attempts):
            if attempt.metadata.get("trajectory_id") != trajectory.id:
                continue
            attempt.judgements = [
                Judgement(
                    status=self._status_from_evaluation(evaluation),
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

    def _status_from_evaluation(self, evaluation: EvaluationResult) -> JudgementStatus:
        if evaluation.passed is True:
            return JudgementStatus.PASS
        if evaluation.passed is False:
            return JudgementStatus.FAIL
        return JudgementStatus.UNKNOWN


class StopWhen(Component):
    condition: TerminationCondition
    name: str = "stop_when"
    requires: set[StateFact] = Field(default_factory=lambda: {StateFact.EVALUATIONS})
    provides: set[StateFact] = Field(default_factory=lambda: {StateFact.STOP_SIGNAL})

    def __init__(self, condition: TerminationCondition | None = None, **data: object) -> None:
        if condition is not None and "condition" not in data:
            data["condition"] = condition
        super().__init__(**data)

    async def apply(self, state: RuntimeState, context: RuntimeContext) -> StatePatch:
        policy = _policy(context)
        for trajectory in state.frontier:
            if not self.condition.satisfied(trajectory):
                continue
            context.attack.logger.emit(
                "search.stop",
                reason=SUCCESS_TERMINATION_REASON,
                condition=self.condition.name,
                score=trajectory.best_score,
            )
            if policy.stop_on_success:
                return StatePatch(
                    stop_reason=SUCCESS_TERMINATION_REASON,
                    success_trajectory_id=trajectory.id,
                    provided=self.provides,
                )
        return StatePatch()


class Refine(Component):
    feedback: FeedbackBuilder | None = None
    selector: FrontierSelector = Field(default_factory=TopKSelector)
    name: str = "refine"
    requires: set[StateFact] = Field(default_factory=lambda: {StateFact.FRONTIER})
    provides: set[StateFact] = Field(
        default_factory=lambda: {StateFact.FRONTIER, StateFact.FEEDBACK}
    )

    async def apply(self, state: RuntimeState, context: RuntimeContext) -> StatePatch:
        if self.feedback is not None:
            for trajectory in state.frontier:
                trajectory.feedback.append(self.feedback.build(state.objective, trajectory))
        policy = _policy(context)
        selected = self.selector.select(state.frontier, policy.width)
        context.attack.logger.emit(
            "search.refine.finish",
            selector=self.selector.name,
            candidates=len(selected),
        )
        return StatePatch(frontier=selected, provided=self.provides)


class IterativeSearchTechnique(Flow):
    program: Program
    name: str = "iterative_search"

    async def execute(self, objective: Objective, context: AttackContext) -> Any:
        context.logger.emit("flow.start", flow=self.name, program=self.program.name)
        context.logger.emit(
            "program.start",
            program=self.program.name,
            components=_component_labels(self.program),
            evaluators=_program_evaluator_names(self.program),
        )
        runtime_state = await ProgramExecutor(self.program).execute(objective, context)
        if "stop_reason" not in runtime_state.attack_state.metadata:
            runtime_state.attack_state.metadata["stop_reason"] = DEFAULT_SEARCH_STOP_REASON
        context.logger.emit(
            "flow.stop",
            reason=runtime_state.attack_state.metadata["stop_reason"],
        )
        return runtime_state.attack_state


def _policy(context: RuntimeContext) -> SearchPolicy:
    if isinstance(context.policy, SearchPolicy):
        return context.policy
    return SearchPolicy()


def _component_labels(component: Component) -> list[str]:
    labels = [_component_label(component)]
    for child in getattr(component, "children", []) or []:
        labels.extend(_component_labels(child))
    return labels


def _component_label(component: Component) -> str:
    evaluators = getattr(component, "evaluators", None)
    if evaluators:
        return f"{component.name}({','.join(evaluator.name for evaluator in evaluators)})"
    proposer = getattr(component, "proposer", None)
    if proposer is not None:
        return f"{component.name}({proposer.name})"
    constraints = getattr(component, "constraints", None)
    if constraints:
        return f"{component.name}({','.join(constraint.name for constraint in constraints)})"
    return component.name


def _program_evaluator_names(component: Component) -> list[str]:
    names = [evaluator.name for evaluator in getattr(component, "evaluators", []) or []]
    for child in getattr(component, "children", []) or []:
        names.extend(_program_evaluator_names(child))
    return names


async def _gather_limited(items: Iterable[Any], limit: int, fn):
    item_list = list(items)
    if limit <= 1:
        return [await fn(item) for item in item_list]
    semaphore = asyncio.Semaphore(limit)

    async def run(item):
        async with semaphore:
            return await fn(item)

    return await asyncio.gather(*(run(item) for item in item_list))


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
