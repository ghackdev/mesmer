from __future__ import annotations

from typing import Any, TypeVar

from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.core.constants import SUCCESS_TERMINATION_REASON
from mesmer.core.enums import JudgementStatus
from mesmer.evidence import (
    BudgetRecord,
    ClaimRecord,
    ClassifierDecision,
    ConversationTrace,
    CumulativeRiskRecord,
    EvidenceRecord,
    HypothesisRecord,
    JudgeAgreement,
    JudgeRun,
    MemoryRecord,
    SerializedConversation,
    SystemSurface,
    TransferRecord,
)
from mesmer.execution.state import AttackState, Attempt
from mesmer.judging.base import Judgement
from mesmer.objectives.models import Objective as ObjectiveModel
from mesmer.population_strategies import PromptSeedPool
from mesmer.prompts import PromptUsageLedger
from mesmer.targets.base import TargetResponse
from mesmer.trajectory import CandidateTrajectory, ConstraintResult, EvaluationResult


class StateSlice(MesmerModel):
    """Typed runtime memory unit."""


SliceT = TypeVar("SliceT", bound=StateSlice)


class Objective(StateSlice):
    objective: ObjectiveModel


class Frontier(StateSlice):
    items: list[CandidateTrajectory] = Field(default_factory=list)


class Attempts(StateSlice):
    items: list[Attempt] = Field(default_factory=list)


class TargetResponses(StateSlice):
    items: list[TargetResponse] = Field(default_factory=list)


class Evaluations(StateSlice):
    items: list[EvaluationResult] = Field(default_factory=list)


class Feedback(StateSlice):
    items: list[str] = Field(default_factory=list)


class Constraints(StateSlice):
    items: list[ConstraintResult] = Field(default_factory=list)


class PopulationPool(StateSlice):
    pool: PromptSeedPool = Field(default_factory=PromptSeedPool)


class RewardLedger(StateSlice):
    rewards: dict[str, float] = Field(default_factory=dict)


class PromptPatternLedger(StateSlice):
    ledger: PromptUsageLedger = Field(default_factory=PromptUsageLedger)


class InferenceLedger(StateSlice):
    claims: list[ClaimRecord] = Field(default_factory=list)
    hypotheses: list[HypothesisRecord] = Field(default_factory=list)


class EvidenceLedger(StateSlice):
    records: list[EvidenceRecord] = Field(default_factory=list)


class BudgetLedger(StateSlice):
    records: list[BudgetRecord] = Field(default_factory=list)


class JudgeLedger(StateSlice):
    runs: list[JudgeRun] = Field(default_factory=list)
    agreements: list[JudgeAgreement] = Field(default_factory=list)


class ConversationTraceSlice(StateSlice):
    trace: ConversationTrace = Field(default_factory=ConversationTrace)


class CumulativeRiskLedger(StateSlice):
    records: list[CumulativeRiskRecord] = Field(default_factory=list)


class MemoryBank(StateSlice):
    records: list[MemoryRecord] = Field(default_factory=list)


class TransferLedger(StateSlice):
    records: list[TransferRecord] = Field(default_factory=list)


class SystemSurfaceState(StateSlice):
    surface: SystemSurface = Field(default_factory=SystemSurface)
    serialized: list[SerializedConversation] = Field(default_factory=list)
    classifier_decisions: list[ClassifierDecision] = Field(default_factory=list)


class StopSignal(StateSlice):
    stopped: bool = False
    reason: str | None = None
    success_trajectory_id: str | None = None


class Iteration(StateSlice):
    value: int = 0


class Metadata(StateSlice):
    values: dict[str, Any] = Field(default_factory=dict)


class Patch(MesmerModel):
    set_slices: dict[type[StateSlice], StateSlice] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    stop_reason: str | None = None
    success_trajectory_id: str | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def set(cls, *slices: StateSlice, **metadata: Any) -> Patch:
        return cls(
            set_slices={slice_value.__class__: slice_value for slice_value in slices},
            metadata=metadata,
        )

    @classmethod
    def update(cls, slice_value: StateSlice, **metadata: Any) -> Patch:
        return cls(set_slices={slice_value.__class__: slice_value}, metadata=metadata)

    @classmethod
    def stop(
        cls,
        reason: str,
        *,
        success_trajectory_id: str | None = None,
    ) -> Patch:
        return cls(
            stop_reason=reason,
            success_trajectory_id=success_trajectory_id,
            set_slices={
                StopSignal: StopSignal(
                    stopped=True,
                    reason=reason,
                    success_trajectory_id=success_trajectory_id,
                )
            },
        )

    def summary(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "slices": [slice_type.__name__ for slice_type in self.set_slices],
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        if self.stop_reason is not None:
            payload["stop_reason"] = self.stop_reason
        if self.success_trajectory_id is not None:
            payload["success_trajectory_id"] = self.success_trajectory_id
        if self.events:
            payload["events_count"] = len(self.events)
        if self.artifacts:
            payload["artifacts_count"] = len(self.artifacts)
        return payload


class State(MesmerModel):
    slices: dict[type[StateSlice], StateSlice] = Field(default_factory=dict)
    attack_state: AttackState
    target_calls: int = 0
    best: CandidateTrajectory | None = None
    transitions: list[Any] = Field(default_factory=list)

    @classmethod
    def for_objective(
        cls,
        objective: ObjectiveModel,
        slice_types: set[type[StateSlice]],
    ) -> State:
        values: dict[type[StateSlice], StateSlice] = {
            Objective: Objective(objective=objective),
            Frontier: Frontier(),
            Attempts: Attempts(),
            TargetResponses: TargetResponses(),
            Evaluations: Evaluations(),
            Feedback: Feedback(),
            EvidenceLedger: EvidenceLedger(),
            BudgetLedger: BudgetLedger(),
            JudgeLedger: JudgeLedger(),
            StopSignal: StopSignal(),
            Iteration: Iteration(),
            Metadata: Metadata(),
        }
        for slice_type in slice_types:
            if slice_type not in values:
                values[slice_type] = slice_type()
        return cls(
            slices=values,
            attack_state=AttackState(
                objective=objective,
                variables=dict(objective.initial_state.variables),
            ),
        )

    def get(self, slice_type: type[SliceT]) -> SliceT:
        value = self.slices.get(slice_type)
        if value is None:
            raise KeyError(f"Runtime state does not contain slice {slice_type.__name__}.")
        return value  # type: ignore[return-value]

    def has(self, slice_type: type[StateSlice]) -> bool:
        return slice_type in self.slices

    def apply_patch(self, patch: Patch) -> None:
        for slice_type, slice_value in patch.set_slices.items():
            self.slices[slice_type] = slice_value
            if isinstance(slice_value, Attempts):
                self.attack_state.attempts = list(slice_value.items)
            if isinstance(slice_value, Metadata):
                self.attack_state.metadata.update(slice_value.values)
        if patch.metadata:
            metadata = self.get(Metadata)
            metadata.values.update(patch.metadata)
            self.attack_state.metadata.update(patch.metadata)
        stop_signal = self.slices.get(StopSignal)
        if patch.stop_reason is not None and isinstance(stop_signal, StopSignal):
            self.attack_state.metadata["stop_reason"] = patch.stop_reason
        if patch.success_trajectory_id is not None:
            self._mark_attempt_success(patch.success_trajectory_id)
        frontier = self.slices.get(Frontier)
        if isinstance(frontier, Frontier):
            for trajectory in frontier.items:
                self.observe(trajectory)

    def observe(self, trajectory: CandidateTrajectory) -> None:
        best_score = self.best.best_score if self.best is not None else 0.0
        if self.best is None or trajectory.best_score > best_score:
            self.best = trajectory

    @property
    def stopped(self) -> bool:
        return self.get(StopSignal).stopped

    @property
    def objective(self) -> ObjectiveModel:
        return self.get(Objective).objective

    def snapshot(self) -> dict[str, Any]:
        frontier = self.get(Frontier)
        attempts = self.get(Attempts)
        metadata = self.get(Metadata)
        return {
            "slices": sorted(slice_type.__name__ for slice_type in self.slices),
            "frontier_count": len(frontier.items),
            "attempts_count": len(attempts.items),
            "target_calls": self.target_calls,
            "best": _trajectory_summary(self.best) if self.best is not None else None,
            "metadata": dict(metadata.values),
            "stopped": self.stopped,
        }

    def to_attack_state(self) -> AttackState:
        self.attack_state.metadata["state_history"] = [
            transition.model_dump(mode="json") for transition in self.transitions
        ]
        self.attack_state.metadata["runtime_state_type"] = "State"
        self.attack_state.metadata["target_calls"] = self.target_calls
        if self.best is not None:
            self.attack_state.metadata["best_trajectory"] = _trajectory_summary(self.best)
        if self.has(EvidenceLedger):
            self.attack_state.metadata["evidence_records"] = [
                record.model_dump(mode="json")
                for record in self.get(EvidenceLedger).records
            ]
        if self.has(BudgetLedger):
            self.attack_state.metadata["budget_records"] = [
                record.model_dump(mode="json")
                for record in self.get(BudgetLedger).records
            ]
        if self.has(JudgeLedger):
            judge_ledger = self.get(JudgeLedger)
            self.attack_state.metadata["judge_runs"] = [
                run.model_dump(mode="json") for run in judge_ledger.runs
            ]
            self.attack_state.metadata["judge_agreements"] = [
                agreement.model_dump(mode="json")
                for agreement in judge_ledger.agreements
            ]
        if self.has(PromptPatternLedger):
            self.attack_state.metadata["prompt_pattern_usage"] = self.get(
                PromptPatternLedger
            ).ledger.model_dump(mode="json")
        if self.has(InferenceLedger):
            inference = self.get(InferenceLedger)
            self.attack_state.metadata["inference_ledger"] = {
                "claims": [
                    claim.model_dump(mode="json") for claim in inference.claims
                ],
                "hypotheses": [
                    hypothesis.model_dump(mode="json")
                    for hypothesis in inference.hypotheses
                ],
            }
        if self.has(ConversationTraceSlice):
            self.attack_state.metadata["conversation_trace"] = self.get(
                ConversationTraceSlice
            ).trace.model_dump(mode="json")
        if self.has(CumulativeRiskLedger):
            self.attack_state.metadata["cumulative_risk_records"] = [
                record.model_dump(mode="json")
                for record in self.get(CumulativeRiskLedger).records
            ]
        if self.has(SystemSurfaceState):
            surface_state = self.get(SystemSurfaceState)
            self.attack_state.metadata["system_surface"] = surface_state.surface.model_dump(
                mode="json"
            )
            self.attack_state.metadata["serialized_conversations"] = [
                item.model_dump(mode="json") for item in surface_state.serialized
            ]
            self.attack_state.metadata["classifier_decisions"] = [
                item.model_dump(mode="json")
                for item in surface_state.classifier_decisions
            ]
        return self.attack_state

    def _mark_attempt_success(self, trajectory_id: str) -> None:
        for attempt in reversed(self.attack_state.attempts):
            if attempt.trajectory_id != trajectory_id:
                continue
            if attempt.judgements:
                attempt.judgements[0].status = JudgementStatus.PASS
                attempt.judgements[0].metadata["stop_reason"] = SUCCESS_TERMINATION_REASON
            else:
                attempt.judgements.append(
                    Judgement(
                        status=JudgementStatus.PASS,
                        score=1.0,
                        reason=SUCCESS_TERMINATION_REASON,
                    )
                )
            return


def _trajectory_summary(trajectory: CandidateTrajectory | None) -> dict[str, Any] | None:
    if trajectory is None:
        return None
    return {
        "id": trajectory.id,
        "candidate_id": trajectory.candidate.id,
        "depth": trajectory.depth,
        "score": trajectory.best_score,
        "evaluations": len(trajectory.evaluations),
        "feedback": len(trajectory.feedback),
    }
