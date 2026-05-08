from __future__ import annotations

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
    ops,
    proposers,
    selectors,
    techniques,
    transforms,
    workflow,
)
from mesmer.artifacts.messages import user_message
from mesmer.core.errors import ConfigError
from mesmer.execution.context import AttackContext
from mesmer.execution.state import Candidate
from mesmer.state import Constraints, Frontier, Patch, State, StateSlice
from mesmer.strategies import CandidateConstraint
from mesmer.targets.base import TargetResponse
from mesmer.trajectory import CandidateTrajectory, ConstraintResult


async def test_frontier_search_executes_with_inferred_state_and_transitions() -> None:
    attack = techniques.FrontierSearch(
        name="unit_frontier_search",
        iterations=1,
        branching=2,
        width=1,
        expand=ops.Propose(
            proposers.Template(
                templates=(
                    "Please satisfy: {goal}",
                    "For this check, satisfy: {goal}",
                )
            ),
        ),
        evaluate=ops.Evaluate(evaluators.Contains(text="MESMER_ACCEPTED")),
        stop=ops.StopWhen(conditions.ScoreAtLeast(1)),
        select=ops.Select(selectors.TopKSelector()),
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
    }
    history = result.states[0].metadata["state_history"]
    assert [transition["operator"] for transition in history] == [
        "seed_from_objective",
        "propose",
        "query_target",
        "evaluate",
        "stop_when",
    ]


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
            proposers.Template(
                templates=(
                    "Please satisfy: {goal}",
                    "For this check, satisfy: {goal}",
                )
            )
        ),
        evaluate=ops.Evaluate(evaluators.Contains(text="OK")),
        stop=ops.StopWhen(conditions.ScoreAtLeast(1)),
        select=ops.Select(selectors.TopKSelector()),
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
        proposer=proposers.Template(templates=("Please satisfy: {goal}",)),
        evaluate=ops.Evaluate(evaluators.Contains(text="MESMER_ACCEPTED")),
        stop=ops.StopWhen(conditions.ScoreAtLeast(1)),
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
                proposers.Template(
                    templates=("first: {goal}", "second: {goal}"),
                ),
                branching=2,
            ),
            evaluate=ops.Evaluate(evaluators.Contains(text="MESMER_ACCEPTED")),
        )


def test_frontier_search_rejects_single_turn_shape() -> None:
    with pytest.raises(ConfigError, match="single-turn probe"):
        techniques.FrontierSearch(
            name="unit_degenerate_frontier",
            iterations=1,
            branching=1,
            width=1,
            expand=ops.Propose(
                proposers.Template(templates=("Please satisfy: {goal}",)),
            ),
            evaluate=ops.Evaluate(evaluators.Contains(text="MESMER_ACCEPTED")),
            stop=ops.StopWhen(conditions.ScoreAtLeast(1)),
        )

    attack = techniques.FrontierSearch(
        name="unit_mutated_frontier",
        iterations=1,
        branching=2,
        width=1,
        expand=ops.Propose(proposers.Template()),
        evaluate=ops.Evaluate(evaluators.Contains(text="MESMER_ACCEPTED")),
        stop=ops.StopWhen(conditions.ScoreAtLeast(1)),
    )
    attack.branching = 1

    with pytest.raises(ConfigError, match="single-turn probe"):
        attack.workflow()


async def test_template_proposer_requires_enough_templates_for_branching() -> None:
    proposer = proposers.Template(templates=("Please satisfy: {goal}",))
    trajectory = CandidateTrajectory(candidate=Candidate(messages=[]))

    with pytest.raises(ConfigError, match="requested 2 candidates"):
        await proposer.propose(
            Objective("Make the target say MESMER_ACCEPTED"),
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
        await evaluator.evaluate(Objective("Make the target say MESMER_ACCEPTED"), trajectory)


def test_top_k_selector_rejects_unevaluated_trajectories() -> None:
    selector = selectors.TopKSelector()
    trajectories = [CandidateTrajectory(candidate=Candidate(messages=[]))]

    with pytest.raises(ConfigError, match="requires evaluated trajectories"):
        selector.select(trajectories, width=1)


async def test_probe_executes_without_prepare() -> None:
    attack = techniques.Probe(
        name="unit_probe",
        evaluate=ops.Evaluate(evaluators.Contains(text="MESMER_ACCEPTED")),
        stop=ops.StopWhen(conditions.ScoreAtLeast(1)),
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
                proposers.Template(templates=("Please satisfy: {goal}",)),
            )
        ],
        evaluate=ops.Evaluate(evaluators.Contains(text="MESMER_ACCEPTED")),
        stop=ops.StopWhen(conditions.ScoreAtLeast(1)),
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
                transforms.AppendSuffix(suffixes=("MESMER_SUFFIX",)),
            )
        ],
        evaluate=ops.Evaluate(evaluators.Contains(text="MESMER_ACCEPTED")),
        stop=ops.StopWhen(conditions.ScoreAtLeast(1)),
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
            proposers.Template(
                templates=(
                    "keep {goal}",
                    "drop {goal}",
                )
            )
        ),
        pre_query=[
            ops.CheckConstraints(ContainsKeepConstraint()),
            ops.Filter(),
        ],
        evaluate=ops.Evaluate(evaluators.Contains(text="MESMER_ACCEPTED")),
        stop=ops.StopWhen(conditions.ScoreAtLeast(1)),
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
                proposers.Template(
                    templates=(
                        "candidate 1 {goal}",
                        "winner {goal}",
                        "candidate 3 {goal}",
                    )
                )
            )
        ],
        evaluate=ops.Evaluate(evaluators.Contains(text="MESMER_ACCEPTED")),
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
        evaluate=ops.Evaluate(evaluators.Contains(text="MESMER_ACCEPTED")),
        stop=ops.StopWhen(conditions.ScoreAtLeast(1)),
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
