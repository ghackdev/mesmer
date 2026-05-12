from __future__ import annotations

import inspect

import pytest
from pydantic import Field

from mesmer import (
    Objective,
    ObjectiveSource,
    PythonCallableTarget,
    Run,
    Runner,
    conditions,
    evaluators,
    feedback,
    ops,
    proposers,
    selectors,
    techniques,
    transforms,
    workflow,
)
from mesmer.artifacts.messages import user_message
from mesmer.core.enums import Capability
from mesmer.core.errors import ConfigError
from mesmer.evidence import MemoryRecord
from mesmer.execution.context import AttackContext
from mesmer.execution.state import Candidate
from mesmer.state import (
    Constraints,
    ConversationTraceSlice,
    CumulativeRiskLedger,
    Frontier,
    Patch,
    State,
    StateSlice,
    SystemSurfaceState,
)
from mesmer.strategies import CandidateConstraint
from mesmer.targets.base import TargetResponse
from mesmer.trajectory import CandidateTrajectory, ConstraintResult


@pytest.mark.parametrize(
    ("primitive", "removed_aliases"),
    [
        (Objective, {"args", "kwargs"}),
        (techniques.FrontierSearch, {"data"}),
        (techniques.ProposedProbe, {"proposer", "data"}),
        (techniques.PopulationFuzzing, {"seeds", "data"}),
        (ops.Propose, {"data"}),
        (ops.ApplyTransforms, {"transform", "data"}),
        (ops.CheckConstraints, {"constraint", "data"}),
        (ops.Evaluate, {"evaluator", "data"}),
        (ops.StopWhen, {"data"}),
        (ops.Select, {"data"}),
        (ops.Filter, {"data"}),
        (ops.ScoreConversationRisk, {"data"}),
        (evaluators.StartsWith, {"prefix", "data"}),
        (evaluators.JudgePanel, {"evaluator", "data"}),
        (feedback.TemplateFeedback, {"data"}),
        (conditions.ScoreAtLeast, {"data"}),
        (workflow.Sequence, {"args", "kwargs"}),
        (workflow.Loop, {"args", "kwargs"}),
        (transforms.Compose, {"args", "kwargs"}),
    ],
)
def test_public_primitives_expose_explicit_keyword_signatures(
    primitive: type,
    removed_aliases: set[str],
) -> None:
    signature = inspect.signature(primitive)

    assert all(
        parameter.kind not in {
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        }
        for parameter in signature.parameters.values()
    )
    assert not removed_aliases.intersection(signature.parameters)


async def test_frontier_search_executes_with_inferred_state_and_transitions() -> None:
    attack = techniques.FrontierSearch(
        name="unit_frontier_search",
        iterations=1,
        branching=2,
        width=1,
        expand=ops.Propose(
            proposer=proposers.Template(
                templates=(
                    "Please satisfy: {goal}",
                    "For this check, satisfy: {goal}",
                )
            ),
        ),
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
        select=ops.Select(selector=selectors.TopKSelector()),
    )
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert result.attempts_count == 2
    assert {slice_type.__name__ for slice_type in attack.state_schema()} >= {
        "Frontier",
        "Attempts",
        "TargetResponses",
        "Evaluations",
        "EvidenceLedger",
        "BudgetLedger",
        "JudgeLedger",
    }
    history = result.states[0].metadata["state_history"]
    assert [transition["operator"] for transition in history] == [
        "seed_from_objective",
        "propose",
        "query_target",
        "evaluate",
        "stop_when",
    ]
    metadata = result.states[0].metadata
    assert metadata["evidence_records"]
    assert metadata["budget_records"]
    assert metadata["judge_runs"]


class NoveltyLedger(StateSlice):
    scores: list[int] = Field(default_factory=list)


class TrackNovelty(workflow.Operator):
    name: str = "track_novelty"
    reads: set[type[StateSlice]] = Field(default_factory=lambda: {Frontier})
    writes: set[type[StateSlice]] = Field(default_factory=lambda: {NoveltyLedger})

    async def run(self, state: State, context: AttackContext) -> Patch:
        return Patch.set(NoveltyLedger(scores=[len(state.get(Frontier).items)]))


async def test_custom_operator_can_add_state_slice() -> None:
    attack = techniques.FrontierSearch(
        name="unit_custom_operator",
        iterations=1,
        branching=2,
        width=1,
        expand=ops.Propose(
            proposer=proposers.Template(
                templates=(
                    "Please satisfy: {goal}",
                    "For this check, satisfy: {goal}",
                )
            )
        ),
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="OK")]),
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
        select=ops.Select(selector=selectors.TopKSelector()),
        feedback=TrackNovelty(),
    )
    run = Run(
        objectives=ObjectiveSource.single("Say OK"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "OK"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert NoveltyLedger in attack.state_schema()


async def test_proposed_probe_generates_one_candidate_then_queries_target() -> None:
    attack = techniques.ProposedProbe(
        name="unit_proposed_probe",
        expand=ops.Propose(
            proposer=proposers.Template(templates=("Please satisfy: {goal}",)),
        ),
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
    )
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert result.attempts_count == 1
    assert attack.workflow_graph() == [
        "seed_from_objective",
        "propose",
        "query_target",
        "evaluate",
        "stop_when",
    ]
    attempt = result.states[0].attempts[0]
    assert attempt.candidate.messages[0].content == (
        "Please satisfy: Make the target say MESMER_ACCEPTED"
    )


def test_proposed_probe_rejects_multi_branch_proposal() -> None:
    with pytest.raises(ConfigError, match="exactly one candidate"):
        techniques.ProposedProbe(
            name="unit_invalid_proposed_probe",
            expand=ops.Propose(
                proposer=proposers.Template(
                    templates=("first: {goal}", "second: {goal}"),
                ),
                branching=2,
            ),
            evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
        )


def test_frontier_search_rejects_single_turn_shape() -> None:
    with pytest.raises(ConfigError, match="single-turn probe"):
        techniques.FrontierSearch(
            name="unit_degenerate_frontier",
            iterations=1,
            branching=1,
            width=1,
            expand=ops.Propose(
                proposer=proposers.Template(templates=("Please satisfy: {goal}",)),
            ),
            evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
            stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
        )

    attack = techniques.FrontierSearch(
        name="unit_mutated_frontier",
        iterations=1,
        branching=2,
        width=1,
        expand=ops.Propose(proposer=proposers.Template()),
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
    )
    attack.branching = 1

    with pytest.raises(ConfigError, match="single-turn probe"):
        attack.workflow()


async def test_template_proposer_requires_enough_templates_for_branching() -> None:
    proposer = proposers.Template(templates=("Please satisfy: {goal}",))
    trajectory = CandidateTrajectory(candidate=Candidate(messages=[]))

    with pytest.raises(ConfigError, match="requested 2 candidates"):
        await proposer.propose(
            Objective(goal="Make the target say MESMER_ACCEPTED"),
            trajectory,
            count=2,
        )


def test_evaluate_requires_at_least_one_evaluator() -> None:
    with pytest.raises(ConfigError, match="at least one evaluator"):
        ops.Evaluate()


async def test_criteria_evaluator_requires_objective_success_criteria() -> None:
    evaluator = evaluators.Criteria()
    trajectory = CandidateTrajectory(
        candidate=Candidate(messages=[]),
        last_response=TargetResponse(text="MESMER_ACCEPTED"),
    )

    with pytest.raises(ConfigError, match=r"objective\.success"):
        await evaluator.evaluate(Objective(goal="Make the target say MESMER_ACCEPTED"), trajectory)


async def test_contains_can_reject_prompt_echo() -> None:
    evaluator = evaluators.Contains(text="SECRET_TOKEN", allow_prompt_echo=False)
    trajectory = CandidateTrajectory(
        candidate=Candidate(messages=[user_message("Please print SECRET_TOKEN.")]),
        last_response=TargetResponse(text="I cannot print SECRET_TOKEN."),
    )

    result = await evaluator.evaluate(Objective(goal="Extract the secret."), trajectory)

    assert not result.passed
    assert result.score == 0
    assert result.metadata["prompt_contains_text"] is True
    assert result.metadata["response_contains_text"] is True


async def test_contains_without_prompt_echo_passes_when_response_adds_text() -> None:
    evaluator = evaluators.Contains(text="SECRET_TOKEN", allow_prompt_echo=False)
    trajectory = CandidateTrajectory(
        candidate=Candidate(messages=[user_message("Please print the hidden note.")]),
        last_response=TargetResponse(text="SECRET_TOKEN"),
    )

    result = await evaluator.evaluate(Objective(goal="Extract the secret."), trajectory)

    assert result.passed
    assert result.score == 1
    assert result.metadata["prompt_contains_text"] is False
    assert result.metadata["response_contains_text"] is True


async def test_contains_prompt_echo_check_respects_case_sensitivity() -> None:
    evaluator = evaluators.Contains(
        text="secret_token",
        allow_prompt_echo=False,
        case_sensitive=False,
    )
    trajectory = CandidateTrajectory(
        candidate=Candidate(messages=[user_message("Please print SECRET_TOKEN.")]),
        last_response=TargetResponse(text="secret_token"),
    )

    result = await evaluator.evaluate(Objective(goal="Extract the secret."), trajectory)

    assert not result.passed
    assert result.metadata["prompt_contains_text"] is True
    assert result.metadata["response_contains_text"] is True


def test_top_k_selector_rejects_unevaluated_trajectories() -> None:
    selector = selectors.TopKSelector()
    trajectories = [CandidateTrajectory(candidate=Candidate(messages=[]))]

    with pytest.raises(ConfigError, match="requires evaluated trajectories"):
        selector.select(trajectories, width=1)


async def test_probe_executes_without_prepare() -> None:
    attack = techniques.Probe(
        name="unit_probe",
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
    )
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert result.attempts_count == 1
    assert attack.workflow_graph() == [
        "seed_from_objective",
        "query_target",
        "evaluate",
        "stop_when",
    ]


async def test_probe_prepare_can_generate_one_candidate() -> None:
    attack = techniques.Probe(
        name="unit_prepared_probe",
        prepare=[
            ops.Propose(
                proposer=proposers.Template(templates=("Please satisfy: {goal}",)),
            )
        ],
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
    )
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert result.attempts_count == 1
    assert result.states[0].attempts[0].candidate.messages[0].content == (
        "Please satisfy: Make the target say MESMER_ACCEPTED"
    )


async def test_apply_transforms_records_transition_and_updates_frontier() -> None:
    attack = techniques.Probe(
        name="unit_transform_probe",
        prepare=[
            ops.ApplyTransforms(
                transforms=[transforms.AppendSuffix(suffixes=("MESMER_SUFFIX",))]
            )
        ],
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
    )
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert "MESMER_SUFFIX" in result.states[0].attempts[0].candidate.messages[0].content
    history = result.states[0].metadata["state_history"]
    assert [transition["operator"] for transition in history] == [
        "seed_from_objective",
        "apply_transforms",
        "query_target",
        "evaluate",
        "stop_when",
    ]


class ContainsKeepConstraint(CandidateConstraint):
    name: str = "contains_keep"

    async def check(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> ConstraintResult:
        passed = "keep" in trajectory.latest_text
        return ConstraintResult(
            passed=passed,
            reason="contains keep" if passed else "missing keep",
            metadata={"constraint": self.name},
        )


async def test_check_constraints_and_filter_run_before_target_query() -> None:
    attack = techniques.FrontierSearch(
        name="unit_constraint_filter",
        iterations=1,
        branching=2,
        width=2,
        expand=ops.Propose(
            proposer=proposers.Template(
                templates=(
                    "keep {goal}",
                    "drop {goal}",
                )
            )
        ),
        pre_query=[
            ops.CheckConstraints(constraints=[ContainsKeepConstraint()]),
            ops.Filter(),
        ],
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
    )
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert result.attempts_count == 1
    assert Constraints in attack.state_schema()
    history = result.states[0].metadata["state_history"]
    assert [transition["operator"] for transition in history] == [
        "seed_from_objective",
        "propose",
        "check_constraints",
        "filter",
        "query_target",
        "evaluate",
        "stop_when",
    ]


async def test_best_of_n_probe_queries_samples_and_selects_best() -> None:
    attack = techniques.BestOfNProbe(
        name="unit_best_of_n",
        samples=3,
        prepare=[
            ops.Propose(
                proposer=proposers.Template(
                    templates=(
                        "candidate 1 {goal}",
                        "winner {goal}",
                        "candidate 3 {goal}",
                    )
                )
            )
        ],
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
    )
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=attack,
        target=PythonCallableTarget(
            fn=lambda messages, context: (
                "MESMER_ACCEPTED" if "winner" in messages[-1].content else "NO"
            )
        ),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert result.attempts_count == 3
    history = result.states[0].metadata["state_history"]
    assert [transition["operator"] for transition in history] == [
        "seed_from_objective",
        "propose",
        "query_target",
        "evaluate",
        "select",
    ]


class AppendUserTurn(workflow.Operator):
    name: str = "append_user_turn"
    reads: set[type[StateSlice]] = Field(default_factory=lambda: {Frontier})
    writes: set[type[StateSlice]] = Field(default_factory=lambda: {Frontier})

    async def run(self, state: State, context: AttackContext) -> Patch:
        for trajectory in state.get(Frontier).items:
            trajectory.candidate.messages.append(user_message("next user turn"))
        return Patch.set(Frontier(items=state.get(Frontier).items))


async def test_conversation_agent_probe_preserves_target_visible_turns() -> None:
    attack = techniques.ConversationAgentProbe(
        name="unit_conversation_agent",
        turns=2,
        stop_on_success=False,
        propose=AppendUserTurn(),
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
    )
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert result.attempts_count == 2
    second_attempt_messages = result.states[0].attempts[1].candidate.messages
    assert any(message.role.value == "assistant" for message in second_attempt_messages)


async def test_conversation_risk_and_strategy_primitives_record_typed_state() -> None:
    attack = techniques.ConversationAgentProbe(
        name="unit_conversation_risk",
        turns=1,
        stop_on_success=False,
        propose=ops.AppendTurn(content="next user turn for {goal}", actor="attacker"),
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="MESMER_ACCEPTED")]),
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
        feedback=ops.ScoreConversationRisk(evaluator=evaluators.Contains(text="MESMER_ACCEPTED")),
    )
    run = Run(
        objectives=ObjectiveSource.single("Make the target say MESMER_ACCEPTED"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "MESMER_ACCEPTED"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert ConversationTraceSlice in attack.state_schema()
    assert CumulativeRiskLedger in attack.state_schema()
    metadata = result.states[0].metadata
    assert metadata["conversation_trace"]["turns"]
    assert metadata["cumulative_risk_records"]


async def test_strategy_annotation_records_typed_evidence() -> None:
    attack = techniques.Probe(
        name="unit_strategy_annotation",
        prepare=[ops.AnnotateStrategy(labels=("canary", "single_turn"))],
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="OK")]),
    )
    run = Run(
        objectives=ObjectiveSource.single("Say OK"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "OK"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert any(
        record["kind"] == "strategy_annotation"
        for record in result.states[0].metadata["evidence_records"]
    )


async def test_system_surface_primitives_render_and_classify() -> None:
    attack = techniques.Probe(
        name="unit_system_surface",
        prepare=[
            ops.RenderChatTemplate(template="<chat>{messages}</chat>"),
            ops.QueryClassifier(flagged_if_contains=("blocked",)),
        ],
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="OK")]),
    )
    run = Run(
        objectives=ObjectiveSource.single("blocked canary"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "OK"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert SystemSurfaceState in attack.state_schema()
    metadata = result.states[0].metadata
    assert metadata["serialized_conversations"][0]["rendered"].startswith("<chat>")
    assert metadata["classifier_decisions"][0]["flagged"] is True


async def test_capability_validation_rejects_unavailable_operator_capability() -> None:
    attack = techniques.Probe(
        name="unit_missing_capability",
        prepare=[ops.MutateChatTemplate(templates=("<chat>{messages}</chat>",))],
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="OK")]),
    )
    run = Run(
        objectives=ObjectiveSource.single("Say OK"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "OK"),
    )

    result = await Runner().run(run)

    assert result.status.value == "failed"
    assert "chat_template_control" in (result.error or "")


async def test_capability_validation_allows_declared_target_capability() -> None:
    target = PythonCallableTarget(fn=lambda messages, context: "OK")
    target.capabilities.add(Capability.CHAT_TEMPLATE_CONTROL)
    attack = techniques.Probe(
        name="unit_declared_capability",
        prepare=[
            ops.MutateChatTemplate(templates=("<chat>{messages}</chat>",)),
            ops.RenderChatTemplate(),
        ],
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="OK")]),
    )
    run = Run(
        objectives=ObjectiveSource.single("Say OK"),
        attack=attack,
        target=target,
    )

    result = await Runner().run(run)

    assert result.succeeded


async def test_memory_bank_promotes_and_scores_transfer() -> None:
    memory = MemoryRecord(text="please say OK", source_objective_id="source-objective")
    attack = techniques.FrontierSearch(
        name="unit_memory_bank",
        iterations=1,
        branching=2,
        width=2,
        stop_on_success=False,
        expand=ops.Propose(
            proposer=proposers.Template(
                templates=(
                    "please say OK for {goal}",
                    "unrelated candidate",
                )
            )
        ),
        pre_query=[ops.LoadMemoryBank(records=[memory])],
        post_evaluate=[
            ops.ScoreTransfer(),
            ops.PromoteSuccessfulCandidate(min_score=1.0),
        ],
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="OK")]),
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
    )
    run = Run(
        objectives=ObjectiveSource.single("Say OK"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "OK"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    evidence = result.states[0].metadata["evidence_records"]
    assert any(record["kind"] == "transfer_score" for record in evidence)
    assert any(record["kind"] == "memory_promotion" for record in evidence)
