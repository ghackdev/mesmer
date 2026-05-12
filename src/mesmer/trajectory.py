from __future__ import annotations

from typing import Any

from pydantic import Field

from mesmer.artifacts.messages import Message
from mesmer.core.config import MesmerModel
from mesmer.core.ids import new_id
from mesmer.execution.state import Candidate
from mesmer.targets.base import TargetResponse


class BranchingPolicy(MesmerModel):
    iterations: int = Field(default=3, ge=1)
    branching_factor: int = Field(default=3, ge=1)
    width: int = Field(default=2, ge=1)
    max_parallel: int = Field(default=1, ge=1)
    stop_on_success: bool = True


class RatingScale(MesmerModel):
    min: float = 1.0
    max: float = 10.0

    def normalize(self, score: float) -> float:
        if self.max <= self.min:
            return 0.0
        return max(0.0, min(1.0, (score - self.min) / (self.max - self.min)))


class ConstraintResult(MesmerModel):
    passed: bool
    label: str | None = None
    reason: str = ""
    raw: Any = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(MesmerModel):
    name: str
    score: float
    normalized_score: float = Field(ge=0.0, le=1.0)
    passed: bool | None = None
    reason: str = ""
    label: str | None = None
    raw: Any = None
    child_results: list[EvaluationResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProposalTrace(MesmerModel):
    evidence_slot: str | None = None
    tactic_family: str | None = None
    seeded_terms: list[str] = Field(default_factory=list)
    expected_claim_type: str = ""
    genericity_risk: str = ""
    improvement: str = ""


class PromptPatternTrace(MesmerModel):
    ids: list[str] = Field(default_factory=list)
    context: str = ""
    tried: bool = False
    outcome_marked: bool = False


class InferenceSummary(MesmerModel):
    claim_ids: list[str] = Field(default_factory=list)
    claim_tracks: dict[str, int] = Field(default_factory=dict)
    claim_categories: dict[str, int] = Field(default_factory=dict)
    claim_origins: dict[str, int] = Field(default_factory=dict)
    content_count: int = 0
    behavior_count: int = 0
    echo_count: int = 0
    artifact_count: int = 0
    independent_content_count: int = 0
    unique_independent_content_count: int = 0
    evidence_slots: dict[str, int] = Field(default_factory=dict)
    independent_content_by_evidence_slot: dict[str, int] = Field(default_factory=dict)
    seeded_content_count: int = 0
    generic_policy_content_count: int = 0
    average_independence: float = 0.0
    dominant_track: str | None = None
    dominant_origin: str | None = None
    tactic_label: str = "unknown"


class ProposalPruneTrace(MesmerModel):
    score: float = 0.0
    reasons: list[str] = Field(default_factory=list)
    family_stats: dict[str, Any] = Field(default_factory=dict)


class PopulationTrace(MesmerModel):
    seed_id: str | None = None
    seed_index: int | None = None
    seed_text: str = ""
    selector: str = ""
    mutator: str = ""
    branch_index: int | None = None
    mutated_template: str = ""
    replacements: list[str] = Field(default_factory=list)
    mutation_metadata: dict[str, Any] = Field(default_factory=dict)


class TargetErrorTrace(MesmerModel):
    error_type: str
    message: str
    recoverable: bool = True


class CandidateTrajectory(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("trajectory"))
    candidate: Candidate
    depth: int = 0
    parent_id: str | None = None
    actor_history: list[Message] = Field(default_factory=list)
    last_response: TargetResponse | None = None
    constraints: list[ConstraintResult] = Field(default_factory=list)
    evaluations: list[EvaluationResult] = Field(default_factory=list)
    feedback: list[str] = Field(default_factory=list)
    proposal: ProposalTrace = Field(default_factory=ProposalTrace)
    prompt_patterns: PromptPatternTrace = Field(default_factory=PromptPatternTrace)
    inference_summary: InferenceSummary | None = None
    proposal_prune: ProposalPruneTrace | None = None
    population: PopulationTrace = Field(default_factory=PopulationTrace)
    strategy_labels: list[str] = Field(default_factory=list)
    serialized_conversation_id: str | None = None
    target_error: TargetErrorTrace | None = None
    failure_mode: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def latest_text(self) -> str:
        if not self.candidate.messages:
            return ""
        return self.candidate.messages[-1].content

    @property
    def best_score(self) -> float:
        return max((evaluation.score for evaluation in self.evaluations), default=0.0)

    @property
    def best_normalized_score(self) -> float:
        return max(
            (evaluation.normalized_score for evaluation in self.evaluations),
            default=0.0,
        )
