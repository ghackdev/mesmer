from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from mesmer.artifacts.messages import Message
from mesmer.core.config import MesmerModel
from mesmer.core.enums import MessageRole
from mesmer.core.ids import new_id


class TransformKind(StrEnum):
    GENERIC = "generic"
    ENCODING = "encoding"
    STYLE = "style"
    SUFFIX = "suffix"
    PAYLOAD_SPLIT = "payload_split"
    CHARACTER_REWRITE = "character_rewrite"
    TEMPLATE = "template"
    CHAT_TEMPLATE = "chat_template"
    DEMONSTRATION_PACK = "demonstration_pack"
    AUGMENTATION = "augmentation"
    LEXICAL_ANCHOR = "lexical_anchor"


class ClaimTrack(StrEnum):
    CONTENT = "content"
    BEHAVIOR = "behavior"
    ECHO = "echo"
    ARTIFACT = "artifact"


class ClaimOrigin(StrEnum):
    TARGET_OBSERVED = "target_observed"
    CONVERSATION_SEEDED = "conversation_seeded"
    HYPOTHESIS_SEEDED = "hypothesis_seeded"
    PROMPT_SEEDED = "prompt_seeded"
    UNKNOWN = "unknown"
    ARTIFACT = "artifact"


class CapabilityProfile(MesmerModel):
    """Executable threat-model and target-capability declaration."""

    values: set[str] = Field(default_factory=set)

    @classmethod
    def from_values(cls, values: set[str] | list[str] | tuple[str, ...]) -> CapabilityProfile:
        return cls(values={str(value) for value in values})

    @classmethod
    def from_target(cls, target: object) -> CapabilityProfile:
        raw = getattr(target, "capabilities", set())
        values = {str(getattr(value, "value", value)) for value in raw}
        return cls(values=values)

    def supports(self, capability: str) -> bool:
        return capability in self.values

    def missing(self, required: set[str]) -> set[str]:
        return {capability for capability in required if capability not in self.values}

    def merged(self, *profiles: CapabilityProfile) -> CapabilityProfile:
        values = set(self.values)
        for profile in profiles:
            values.update(profile.values)
        return CapabilityProfile(values=values)


class EvidenceRecord(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("evidence"))
    kind: str
    objective_id: str | None = None
    target_name: str | None = None
    target_model: str | None = None
    trajectory_id: str | None = None
    candidate_id: str | None = None
    attempt_id: str | None = None
    response_id: str | None = None
    evaluator: str | None = None
    turn: int | None = None
    query_index: int | None = None
    score: float | None = None
    normalized_score: float | None = None
    passed: bool | None = None
    label: str | None = None
    cost: float | None = None
    latency_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedClaim(MesmerModel):
    category: str
    text: str
    track: ClaimTrack = ClaimTrack.CONTENT
    origin: ClaimOrigin = ClaimOrigin.UNKNOWN
    independence: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: str = ""
    uncertainty: str = ""
    contradicts: list[str] = Field(default_factory=list)
    first_seen_claim_id: str | None = None
    first_seen_response_id: str | None = None
    seeded_by: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClaimExtraction(MesmerModel):
    claims: list[ExtractedClaim] = Field(default_factory=list)
    notes: str = ""
    raw: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClaimSourceContext(MesmerModel):
    tactic_family: str | None = None
    evidence_slot: str | None = None
    trajectory_id: str | None = None
    candidate_id: str | None = None
    response_id: str | None = None


class ClaimAgreement(MesmerModel):
    supported: bool = False
    cluster_id: str | None = None
    claim_ids: list[str] = Field(default_factory=list)
    tactic_families: list[str] = Field(default_factory=list)
    trajectory_ids: list[str] = Field(default_factory=list)
    candidate_only: bool = False


class ClaimAnnotations(MesmerModel):
    source: ClaimSourceContext = Field(default_factory=ClaimSourceContext)
    agreement: ClaimAgreement | None = None
    provenance_reasons: list[str] = Field(default_factory=list)
    provenance_anchors: list[str] = Field(default_factory=list)
    seeded_terms: list[str] = Field(default_factory=list)


class ClaimRecord(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("claim"))
    category: str
    text: str
    track: ClaimTrack = ClaimTrack.CONTENT
    origin: ClaimOrigin = ClaimOrigin.UNKNOWN
    independence: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: str = ""
    uncertainty: str = ""
    contradicts: list[str] = Field(default_factory=list)
    first_seen_claim_id: str | None = None
    first_seen_response_id: str | None = None
    seeded_by: list[str] = Field(default_factory=list)
    objective_id: str | None = None
    trajectory_id: str | None = None
    candidate_id: str | None = None
    response_id: str | None = None
    iteration: int | None = None
    extractor: str | None = None
    source_claim_ids: list[str] = Field(default_factory=list)
    duplicate_claim_ids: list[str] = Field(default_factory=list)
    annotations: ClaimAnnotations = Field(default_factory=ClaimAnnotations)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HypothesisSynthesis(MesmerModel):
    text: str
    value: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    supporting_claim_ids: list[str] = Field(default_factory=list)
    uncertainty: str = ""
    raw: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class HypothesisRecord(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("hypothesis"))
    text: str
    value: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    supporting_claim_ids: list[str] = Field(default_factory=list)
    uncertainty: str = ""
    iteration: int | None = None
    synthesizer: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BudgetRecord(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("budget"))
    turn: int
    query_count: int
    turn_count: int
    max_queries: int | None = None
    max_turns: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class JudgeRun(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("judge_run"))
    evaluator: str
    trajectory_id: str | None = None
    response_id: str | None = None
    score: float
    normalized_score: float
    passed: bool | None = None
    label: str | None = None
    reason: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class JudgeAgreement(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("judge_agreement"))
    panel: str
    evaluator_count: int
    pass_count: int
    fail_count: int
    unknown_count: int
    agreement_rate: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class AdjudicationRecord(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("adjudication"))
    judge_run_ids: list[str] = Field(default_factory=list)
    decision: str
    reason: str = ""
    adjudicator: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationTurn(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("turn"))
    index: int
    role: MessageRole
    content: str
    trajectory_id: str | None = None
    candidate_id: str | None = None
    response_id: str | None = None
    visibility: str = "target_visible"
    actor: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationTrace(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("conversation"))
    turns: list[ConversationTurn] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CumulativeRiskRecord(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("risk"))
    turn: int
    score: float
    normalized_score: float
    trajectory_id: str | None = None
    label: str | None = None
    reason: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryRecord(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("memory"))
    text: str
    source_objective_id: str | None = None
    source_trajectory_id: str | None = None
    source_candidate_id: str | None = None
    target_name: str | None = None
    score: float | None = None
    failure_mode: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TransferRecord(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("transfer"))
    memory_id: str
    source_objective_id: str | None = None
    target_objective_id: str | None = None
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class SystemSurface(MesmerModel):
    name: str = "default"
    chat_template: str | None = None
    role_layout: dict[str, str] = Field(default_factory=dict)
    classifiers: list[str] = Field(default_factory=list)
    tool_gates: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SerializedConversation(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("serialized"))
    surface_name: str
    messages: list[Message] = Field(default_factory=list)
    rendered: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClassifierDecision(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("classifier"))
    classifier: str
    flagged: bool
    label: str | None = None
    score: float | None = None
    reason: str = ""
    trajectory_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TransformProvenance(MesmerModel):
    name: str
    kind: str
    intent_preserving: bool | None = None
    scope: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
