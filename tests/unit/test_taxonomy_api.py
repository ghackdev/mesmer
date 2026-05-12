from __future__ import annotations

import mesmer


def test_removed_public_names_are_not_exported() -> None:
    removed = [
        "runtime",
        "topology",
        "generation",
        "evaluation",
        "selection",
        "variation",
        "population",
        "stopping",
        "targeting",
        "initialization",
        "constraints",
        "data",
        "search",
        "flows",
        "attackers",
    ]

    assert all(not hasattr(mesmer, name) for name in removed)


def test_taxonomy_modules_are_exported() -> None:
    assert mesmer.BestOfNProbe
    assert mesmer.ConversationAgentProbe
    assert mesmer.ElicitationSearch
    assert mesmer.Probe
    assert mesmer.ProposedProbe
    assert mesmer.EvidenceMatrix
    assert mesmer.BudgetCurve
    assert mesmer.sources.ObjectiveSource
    assert mesmer.techniques.FrontierSearch
    assert mesmer.techniques.BestOfNProbe
    assert mesmer.techniques.ConversationAgentProbe
    assert mesmer.techniques.ElicitationSearch
    assert mesmer.techniques.Probe
    assert mesmer.techniques.ProposedProbe
    assert mesmer.ops.ApplyTransforms
    assert mesmer.ops.CheckConstraints
    assert mesmer.ops.Filter
    assert mesmer.ops.Propose
    assert mesmer.ops.QueryTarget
    assert mesmer.ops.ExtractClaims
    assert mesmer.ops.AnnotateClaimProvenance
    assert mesmer.ops.SynthesizeHypothesis
    assert mesmer.ops.CalibrateEvidenceScores
    assert mesmer.ops.Evaluate
    assert mesmer.ops.StopWhen
    assert mesmer.ops.StopWhenHypothesisConfidence
    assert mesmer.proposers.Template
    assert mesmer.proposers.SuffixOnlyLLMProposer
    assert mesmer.evaluators.Contains
    assert mesmer.evaluators.NotContainsAny
    assert mesmer.evaluators.StartsWith
    assert mesmer.selectors.TopKSelector
    assert mesmer.conditions.ScoreAtLeast
    assert mesmer.evaluators.JudgePanel
    assert mesmer.feedback.InferenceFeedback
    assert mesmer.state.Constraints
    assert mesmer.state.InferenceLedger
    assert mesmer.state.EvidenceLedger
    assert mesmer.state.BudgetLedger
    assert mesmer.state.JudgeLedger
    assert mesmer.state.ConversationTraceSlice
    assert mesmer.state.CumulativeRiskLedger
    assert mesmer.state.SystemSurfaceState
    assert mesmer.evidence.CapabilityProfile
    assert mesmer.evidence.ClaimRecord
    assert mesmer.evidence.EvidenceRecord
    assert mesmer.evidence.HypothesisRecord
    assert mesmer.transforms.AppendSuffix
    assert mesmer.transforms.StyleTransfer
    assert mesmer.transforms.LexicalAnchorInject
    assert mesmer.ops.AppendTurn
    assert mesmer.ops.ScoreConversationRisk
    assert mesmer.ops.RenderChatTemplate
    assert mesmer.ops.QueryClassifier
    assert mesmer.ops.LoadMemoryBank
    assert mesmer.ops.PromoteTacticMemory
    assert mesmer.ops.PromoteSuccessfulCandidate
    assert mesmer.ops.ScoreTransfer
    assert mesmer.selectors.InferenceDiversitySelector
