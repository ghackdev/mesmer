from __future__ import annotations

import asyncio
import json

from pydantic import Field

from mesmer import (
    EvaluatorFailurePolicy,
    Objective,
    ObjectiveSource,
    ProposalMessageMode,
    Run,
    Runner,
    constraints,
    evaluation,
    feedback,
    generation,
    initialization,
    runtime,
    selection,
    stopping,
    targeting,
    topology,
)
from mesmer.artifacts.messages import assistant_message, user_message
from mesmer.core.errors import StructuredOutputError
from mesmer.execution.state import Candidate
from mesmer.runtime.component import RuntimeContext
from mesmer.search.actors import StructuredCompletion
from mesmer.search.models import CandidateTrajectory, ConstraintResult, EvaluationResult
from mesmer.targets.base import TargetResponse
from mesmer.targets.callable import PythonCallableTarget
from mesmer.topology import AttackContext

MARKER = "MESMER_ACCEPTED"


class UnitSearchState(runtime.RuntimeState):
    frontier: list[CandidateTrajectory] = Field(default_factory=list)
    best: CandidateTrajectory | None = None


class CallTrace:
    def __init__(self) -> None:
        self.calls: list[str] = []


class ScriptedProposer(generation.Generator):
    prompts: list[str]
    trace: CallTrace
    name: str = "scripted_proposer"

    async def propose(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
        count: int,
        max_parallel: int = 1,
    ) -> list[CandidateTrajectory]:
        feedback = trajectory.feedback[-1] if trajectory.feedback else "no-feedback"
        self.trace.calls.append(f"propose:{trajectory.depth}:{feedback}")
        return [
            CandidateTrajectory(
                candidate=Candidate(messages=[user_message(prompt)]),
                depth=trajectory.depth + 1,
                parent_id=trajectory.id,
                feedback=list(trajectory.feedback),
            )
            for prompt in self.prompts[:count]
        ]


class KeywordConstraint(constraints.Constraint):
    keyword: str
    trace: CallTrace
    name: str = "keyword_constraint"

    async def check(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> ConstraintResult:
        self.trace.calls.append(f"constrain:{trajectory.latest_text}")
        return ConstraintResult(passed=self.keyword in trajectory.latest_text)


class MarkerEvaluator(evaluation.Evaluator):
    trace: CallTrace
    name: str = "marker_evaluator"

    async def evaluate(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> EvaluationResult:
        response = trajectory.last_response.text if trajectory.last_response else ""
        self.trace.calls.append(f"assess:{response}")
        score = 10.0 if MARKER in response else 1.0
        return EvaluationResult(
            name=self.name,
            score=score,
            normalized_score=score / 10.0,
            reason="marker score",
        )


class ScriptedChatActor(generation.Actor):
    outputs: list[str]
    calls: int = 0
    message_contents: list[list[str]] = Field(default_factory=list)
    name: str = "scripted_chat_actor"

    async def complete(self, messages, **params) -> str:
        self.message_contents.append([message.content for message in messages])
        output = self.outputs[min(self.calls, len(self.outputs) - 1)]
        self.calls += 1
        return output

    async def complete_structured(self, messages, schema, **params):
        output = await self.complete(messages, **params)
        try:
            parsed = schema.model_validate_json(output)
        except ValueError as exc:
            raise StructuredOutputError(
                f"Model output did not match structured schema {schema.__name__}.",
                raw_output=output,
            ) from exc
        return StructuredCompletion(parsed=parsed, raw=output)


async def test_component_program_runs_in_declared_order() -> None:
    trace = CallTrace()

    def target(messages, context) -> str:
        trace.calls.append(f"query:{messages[-1].content}")
        return MARKER

    technique = topology.Search(
        name="unit_search",
        program=runtime.Program(
            initialization.Seed(),
            topology.Iterate(
                policy=topology.Policy(iterations=2, branching_factor=2, width=1),
                children=[
                    generation.Propose(
                        ScriptedProposer(
                            prompts=["off topic", "valid candidate"],
                            trace=trace,
                        ),
                    ),
                    constraints.Filter(KeywordConstraint(keyword="valid", trace=trace)),
                    targeting.Query(),
                    evaluation.Assess(MarkerEvaluator(trace=trace)),
                    stopping.StopWhen(stopping.ScoreAtLeast(10)),
                    feedback.Refine(
                        feedback=feedback.Template("score={score}; response={response}"),
                        selector=selection.TopK(k=1),
                    ),
                ],
            ),
            state=UnitSearchState,
        ),
    )
    run = Run(
        objectives=ObjectiveSource.single("make marker"),
        attack=technique,
        target=PythonCallableTarget(fn=target),
        judges=[],
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert "stopped" not in UnitSearchState.model_fields
    assert "stop_reason" not in UnitSearchState.model_fields
    assert "internal" in UnitSearchState.model_fields
    assert result.states[0].metadata["runtime_state_type"] == "UnitSearchState"
    assert [transition["component"] for transition in result.states[0].metadata["state_history"]][
        :6
    ] == [
        "objective_seed",
        "propose",
        "filter",
        "query",
        "assess",
        "stop_when",
    ]
    assert result.states[0].metadata["state_history"][0]["before"]["state_type"] == (
        "UnitSearchState"
    )
    artifact = result.states[0].metadata["reproduction_artifacts"][0]
    assert artifact["messages"][0]["role"] == "user"
    assert artifact["messages"][0]["content"] == "valid candidate"
    assert artifact["messages"][1]["role"] == "assistant"
    assert artifact["messages"][1]["content"] == MARKER
    assert artifact["trace"]["trajectory"]["depth"] == 1
    assert artifact["trace"]["trajectory"]["constraints"][0]["passed"] is True
    assert artifact["trace"]["trajectory"]["evaluations"][0]["score"] == 10.0
    assert trace.calls == [
        "propose:0:no-feedback",
        "constrain:off topic",
        "constrain:valid candidate",
        "query:valid candidate",
        "assess:MESMER_ACCEPTED",
    ]
    assert result.states[0].metadata["stop_reason"] == "termination_satisfied"


async def test_component_program_rejects_invalid_order() -> None:
    technique = topology.Search(
        name="invalid_search",
        program=runtime.Program(
            initialization.Seed(),
            topology.Iterate(
                policy=topology.Policy(iterations=1, branching_factor=1, width=1),
                children=[
                    evaluation.Assess(MarkerEvaluator(trace=CallTrace())),
                    targeting.Query(),
                ],
            ),
        ),
    )
    run = Run(
        objectives=ObjectiveSource.single("make marker"),
        attack=technique,
        target=PythonCallableTarget(fn=lambda messages, context: MARKER),
        judges=[],
    )

    result = await Runner().run(run)

    assert result.error is not None
    assert "requires missing state facts" in result.error


async def test_component_program_feedback_reaches_next_proposal() -> None:
    trace = CallTrace()

    def target(messages, context) -> str:
        return "try again"

    technique = topology.Search(
        name="feedback_search",
        program=runtime.Program(
            initialization.Seed(),
            topology.Iterate(
                policy=topology.Policy(
                    iterations=2,
                    branching_factor=1,
                    width=1,
                    stop_on_success=False,
                ),
                children=[
                    generation.Propose(ScriptedProposer(prompts=["valid prompt"], trace=trace)),
                    targeting.Query(),
                    evaluation.Assess(MarkerEvaluator(trace=trace)),
                    stopping.StopWhen(stopping.ScoreAtLeast(10)),
                    feedback.Refine(
                        feedback=feedback.Template("observed={response}; score={score}"),
                        selector=selection.TopK(k=1),
                    ),
                ],
            ),
        ),
    )
    run = Run(
        objectives=ObjectiveSource.single("make marker"),
        attack=technique,
        target=PythonCallableTarget(fn=target),
        judges=[],
    )

    result = await Runner().run(run)

    assert not result.succeeded
    assert result.attempts_count == 2
    assert trace.calls[0] == "propose:0:no-feedback"
    assert trace.calls[2] == "propose:1:observed=try again; score=1.0"


async def test_llm_rating_evaluator_uses_structured_rating() -> None:
    evaluator = evaluation.LLMRating(
        actor=ScriptedChatActor(outputs=['{"rating":10,"reason":"complete"}']),
        system_prompt_template="Rate the response.",
    )
    trajectory = CandidateTrajectory(
        candidate=Candidate(messages=[user_message("prompt")]),
        last_response=TargetResponse(text="response"),
    )

    result = await evaluator.evaluate(Objective("goal"), trajectory)

    assert result.score == 10.0
    assert result.normalized_score == 1.0
    assert result.reason == "complete"


async def test_llm_rating_evaluator_accepts_numeric_string_rating() -> None:
    evaluator = evaluation.LLMRating(
        actor=ScriptedChatActor(outputs=['{"rating":"1","reason":"low"}']),
        system_prompt_template="Rate the response.",
    )
    trajectory = CandidateTrajectory(
        candidate=Candidate(messages=[user_message("prompt")]),
        last_response=TargetResponse(text="response"),
    )

    result = await evaluator.evaluate(Objective("goal"), trajectory)

    assert result.score == 1.0
    assert result.normalized_score == 0.0
    assert result.reason == "low"


async def test_llm_rating_evaluator_retries_malformed_output_once() -> None:
    actor = ScriptedChatActor(outputs=["not json", '{"rating":7,"reason":"partial"}'])
    evaluator = evaluation.LLMRating(
        actor=actor,
        system_prompt_template="Rate the response.",
    )
    trajectory = CandidateTrajectory(
        candidate=Candidate(messages=[user_message("prompt")]),
        last_response=TargetResponse(text="response"),
    )

    result = await evaluator.evaluate(Objective("goal"), trajectory)

    assert actor.calls == 2
    assert result.score == 7.0
    assert result.metadata["raw_outputs"] == ["not json", '{"rating":7,"reason":"partial"}']
    assert result.metadata["parse_errors"][0]["retry_count"] == 0


async def test_llm_rating_evaluator_records_min_score_after_retry_exhaustion() -> None:
    actor = ScriptedChatActor(outputs=["not a rating", "still not a rating"])
    evaluator = evaluation.LLMRating(
        actor=actor,
        system_prompt_template="Rate the response.",
        failure_policy=EvaluatorFailurePolicy.RETRY_THEN_RECORD,
    )
    trajectory = CandidateTrajectory(
        candidate=Candidate(messages=[user_message("prompt")]),
        last_response=TargetResponse(text="response"),
    )

    result = await evaluator.evaluate(Objective("goal"), trajectory)

    assert actor.calls == 2
    assert result.score == 1.0
    assert result.normalized_score == 0.0
    assert result.passed is False
    assert result.metadata["failure_reason"] == "malformed_output"


async def test_llm_rating_evaluator_raises_by_default_after_retry_exhaustion() -> None:
    actor = ScriptedChatActor(outputs=["not a rating", "still not a rating"])
    evaluator = evaluation.LLMRating(
        actor=actor,
        system_prompt_template="Rate the response.",
    )
    trajectory = CandidateTrajectory(
        candidate=Candidate(messages=[user_message("prompt")]),
        last_response=TargetResponse(text="response"),
    )

    try:
        await evaluator.evaluate(Objective("goal"), trajectory)
    except Exception as exc:
        assert exc.__class__.__name__ == "EvaluatorParseError"
    else:
        raise AssertionError("default evaluator should raise")


async def test_tap_style_evaluator_parse_failure_keeps_attempt_and_execution_failed(
    capsys,
) -> None:
    technique = topology.Search(
        name="tap_style",
        program=runtime.Program(
            initialization.Seed(),
            topology.Iterate(
                policy=topology.Policy(iterations=1, branching_factor=1, width=1),
                children=[
                    targeting.Query(),
                    evaluation.Assess(
                        evaluation.LLMRating(
                            actor=ScriptedChatActor(outputs=["not a rating", "still wrong"]),
                            system_prompt_template="Rate the response.",
                        )
                    ),
                ],
            ),
        ),
    )
    run = Run(
        objectives=ObjectiveSource.single("make marker"),
        attack=technique,
        target=PythonCallableTarget(fn=lambda messages, context: "target response"),
        judges=[],
    )

    result = await Runner(verbose=True, log_format="compact").run(run)

    output = capsys.readouterr().out
    records = [json.loads(line) for line in output.splitlines() if line.startswith("{")]
    events = [record["event"] for record in records]
    finish = records[-1]

    assert result.status.value == "failed"
    assert result.outcome.value == "execution_failed"
    assert result.attempts_count == 1
    assert not result.succeeded
    assert result.states[0].attempts[0].judgements == []
    assert "program.start" in events
    program_start = next(record for record in records if record["event"] == "program.start")
    assert "llm_rating_evaluator" in program_start["evaluators"]
    assert events.count("search.evaluator.raw") == 2
    assert events.count("search.evaluator.parse_error") == 2
    assert "run.error" in events
    assert finish["event"] == "run.finish"
    assert finish["attempts"] == 1
    assert finish["target_calls"] == 1
    assert finish["outcome"] == "execution_failed"


async def test_llm_label_constraint_uses_structured_label() -> None:
    constraint = constraints.LLMLabel(
        actor=ScriptedChatActor(outputs=['{"label":"YES","reason":"same objective"}']),
        system_prompt_template="Check prompt.",
    )
    trajectory = CandidateTrajectory(candidate=Candidate(messages=[user_message("prompt")]))

    result = await constraint.check(Objective("goal"), trajectory)

    assert result.passed is True
    assert result.label == "YES"
    assert result.raw == '{"label":"YES","reason":"same objective"}'
    assert result.reason == "same objective"


async def test_continue_conversation_appends_latest_target_response() -> None:
    trajectory = CandidateTrajectory(
        candidate=Candidate(messages=[user_message("hello")]),
        last_response=TargetResponse(text="target reply"),
        feedback=["previous feedback"],
        evaluations=[
            EvaluationResult(
                name="score",
                score=2,
                normalized_score=0.2,
            )
        ],
    )
    state = runtime.RuntimeState.for_objective(Objective("goal"))
    state.frontier = [trajectory]

    await targeting.Continue().apply(
        state,
        RuntimeContext(
            attack=AttackContext(
                target=object(),
                judges=[],
                budget_tracker=object(),
            )
        ),
    )

    assert [message.role.value for message in trajectory.candidate.messages] == [
        "user",
        "assistant",
    ]
    assert trajectory.candidate.messages[-1].content == "target reply"
    assert trajectory.feedback == ["previous feedback"]
    assert trajectory.evaluations[0].score == 2


async def test_structured_llm_proposer_uses_structured_prompt_and_metadata() -> None:
    actor = ScriptedChatActor(
        outputs=['{"prompt":"next prompt","improvement":"tightened objective"}']
    )
    proposer = generation.StructuredLLM(
        actor=actor,
        system_prompt_template="Improve {objective}.",
        output=generation.StructuredOutputSpec(
            prompt_field="prompt",
            metadata_fields=("improvement",),
        ),
    )
    parent = CandidateTrajectory(candidate=Candidate(messages=[user_message("current")]))

    children = await proposer.propose(Objective("goal"), parent, count=1)

    assert children[0].latest_text == "next prompt"
    assert children[0].metadata["improvement"] == "tightened objective"
    assert children[0].metadata["raw_model_output"] == (
        '{"prompt":"next prompt","improvement":"tightened objective"}'
    )


async def test_structured_llm_proposer_append_user_preserves_target_transcript() -> None:
    actor = ScriptedChatActor(outputs=['{"prompt":"next user turn","strategy":"continue"}'])
    proposer = generation.StructuredLLM(
        actor=actor,
        system_prompt_template="Improve {objective}.",
        output=generation.StructuredOutputSpec(
            prompt_field="prompt",
            metadata_fields=("strategy",),
        ),
        message_mode=ProposalMessageMode.APPEND_USER,
    )
    parent = CandidateTrajectory(
        candidate=Candidate(
            messages=[
                user_message("hi"),
                assistant_message("hello"),
            ],
            metadata={"conversation_id": "unit"},
        )
    )

    children = await proposer.propose(Objective("goal"), parent, count=1)

    assert [message.role.value for message in children[0].candidate.messages] == [
        "user",
        "assistant",
        "user",
    ]
    assert children[0].candidate.messages[-1].content == "next user turn"
    assert children[0].candidate.metadata["conversation_id"] == "unit"
    assert children[0].candidate.metadata["strategy"] == "continue"


async def test_structured_llm_proposer_keeps_branch_local_actor_history() -> None:
    actor = ScriptedChatActor(
        outputs=[
            '{"prompt":"branch one","improvement":"first"}',
            '{"prompt":"branch two","improvement":"second"}',
            '{"prompt":"branch one refined","improvement":"third"}',
        ]
    )
    proposer = generation.StructuredLLM(
        actor=actor,
        system_prompt_template="System {objective}.",
        initial_user_prompt_template="INIT {objective} -> {target_str}",
        user_prompt_template="FEEDBACK {feedback}",
        history_window=2,
    )
    parent = CandidateTrajectory(candidate=Candidate(messages=[user_message("seed")]))

    children = await proposer.propose(Objective("goal"), parent, count=2, max_parallel=2)

    assert actor.message_contents[0] == ["System goal.", "INIT goal -> goal"]
    assert actor.message_contents[1] == ["System goal.", "INIT goal -> goal"]
    assert children[0].actor_history[0].content == "INIT goal -> goal"
    assert children[0].actor_history[1].content == (
        '{"prompt":"branch one","improvement":"first"}'
    )
    assert children[1].actor_history[1].content == (
        '{"prompt":"branch two","improvement":"second"}'
    )

    children[0].feedback.append("target refused; score=1")
    refined = await proposer.propose(Objective("goal"), children[0], count=1)

    assert refined[0].latest_text == "branch one refined"
    assert actor.message_contents[2] == [
        "System goal.",
        "INIT goal -> goal",
        '{"prompt":"branch one","improvement":"first"}',
        "FEEDBACK target refused; score=1",
    ]
    assert [message.content for message in refined[0].actor_history] == [
        "INIT goal -> goal",
        '{"prompt":"branch one","improvement":"first"}',
        "FEEDBACK target refused; score=1",
        '{"prompt":"branch one refined","improvement":"third"}',
    ]


async def test_select_frontier_prunes_by_constraint_before_target_calls() -> None:
    trace = CallTrace()

    def target(messages, context) -> str:
        trace.calls.append(f"query:{messages[-1].content}")
        return "target response"

    technique = topology.Search(
        name="phase_one_prune",
        program=runtime.Program(
            initialization.Seed(),
            topology.Iterate(
                policy=topology.Policy(
                    iterations=1,
                    branching_factor=4,
                    width=2,
                    stop_on_success=False,
                ),
                children=[
                    generation.Propose(
                        ScriptedProposer(
                            prompts=[
                                "valid one",
                                "off topic",
                                "valid two",
                                "valid three",
                            ],
                            trace=trace,
                        )
                    ),
                    constraints.Filter(KeywordConstraint(keyword="valid", trace=trace)),
                    selection.Select(
                        selection.ConstraintScore(
                            constraint="keyword_constraint",
                            k=2,
                        )
                    ),
                    targeting.Query(),
                ],
            ),
        ),
    )
    run = Run(
        objectives=ObjectiveSource.single("make marker"),
        attack=technique,
        target=PythonCallableTarget(fn=target),
        judges=[],
    )

    result = await Runner().run(run)

    assert result.attempts_count == 2
    assert trace.calls.count("query:valid one") == 1
    assert trace.calls.count("query:valid two") == 1
    assert "query:valid three" not in trace.calls
    assert "query:off topic" not in trace.calls


async def test_query_uses_policy_max_parallel_and_preserves_attempt_order() -> None:
    active = 0
    max_active = 0

    async def target(messages, context) -> str:
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        return messages[-1].content

    technique = topology.Search(
        name="parallel_query",
        program=runtime.Program(
            initialization.Seed(),
            topology.Iterate(
                policy=topology.Policy(
                    iterations=1,
                    branching_factor=3,
                    width=3,
                    max_parallel=3,
                    stop_on_success=False,
                ),
                children=[
                    generation.Propose(
                        ScriptedProposer(
                            prompts=["first", "second", "third"],
                            trace=CallTrace(),
                        )
                    ),
                    targeting.Query(),
                ],
            ),
        ),
    )
    run = Run(
        objectives=ObjectiveSource.single("make marker"),
        attack=technique,
        target=PythonCallableTarget(fn=target),
        judges=[],
    )

    result = await Runner().run(run)

    assert max_active > 1
    assert [attempt.candidate.messages[-1].content for attempt in result.states[0].attempts] == [
        "first",
        "second",
        "third",
    ]


async def test_iterative_search_can_continue_target_visible_transcript() -> None:
    actor = ScriptedChatActor(
        outputs=[
            '{"prompt":"first turn","strategy":"open"}',
            '{"prompt":"second turn","strategy":"close"}',
        ]
    )
    target_seen: list[list[str]] = []

    def target(messages, context) -> str:
        target_seen.append([message.content for message in messages])
        if len(messages) >= 4 and messages[-2].content == "need more context":
            return MARKER
        return "need more context"

    technique = topology.Search(
        name="conversation_search",
        program=runtime.Program(
            initialization.Seed(),
            topology.Iterate(
                policy=topology.Policy(iterations=2, branching_factor=1, width=1),
                children=[
                    generation.Propose(
                        generation.StructuredLLM(
                            actor=actor,
                            system_prompt_template="Plan for {objective}.",
                            output=generation.StructuredOutputSpec(
                                prompt_field="prompt",
                                metadata_fields=("strategy",),
                            ),
                            message_mode=ProposalMessageMode.APPEND_USER,
                        )
                    ),
                    targeting.Query(),
                    evaluation.Assess(MarkerEvaluator(trace=CallTrace())),
                    targeting.Continue(),
                    stopping.StopWhen(stopping.ScoreAtLeast(10)),
                    feedback.Refine(
                        feedback=feedback.Template("observed={response}; score={score}"),
                        selector=selection.TopK(k=1),
                    ),
                ],
            ),
        ),
    )
    run = Run(
        objectives=ObjectiveSource.single(
            Objective(
                goal="make marker",
                initial_state="Hi!",
            )
        ),
        attack=technique,
        target=PythonCallableTarget(fn=target),
        judges=[],
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert target_seen == [
        ["Hi!", "first turn"],
        ["Hi!", "first turn", "need more context", "second turn"],
    ]
    final_attempt = result.states[0].attempts[-1]
    assert [message.content for message in final_attempt.candidate.messages] == [
        "Hi!",
        "first turn",
        "need more context",
        "second turn",
        MARKER,
    ]
