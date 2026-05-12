from __future__ import annotations

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
    prompts,
    proposers,
    techniques,
    transforms,
)
from mesmer.artifacts.messages import user_message
from mesmer.execution.state import Candidate
from mesmer.strategies import template_context
from mesmer.trajectory import CandidateTrajectory


class CapturingStructuredActor(proposers.ChatActor):
    outputs: list[str]
    message_contents: list[list[str]] = Field(default_factory=list)
    name: str = "capturing_structured_actor"

    async def complete(self, messages, **params) -> str:
        self.message_contents.append([message.content for message in messages])
        return self.outputs[0]

    async def complete_structured(self, messages, schema, **params):
        output = await self.complete(messages, **params)
        return proposers.StructuredCompletion(
            parsed=schema.model_validate_json(output),
            raw=output,
        )


def test_prompt_pattern_context_is_strategy_context() -> None:
    pattern = prompts.PromptPattern(
        id="test.inspiration",
        name="Test inspiration",
        prompt="Use a structured compliance-check framing.",
        proposer_hint="Use this as inspiration, not as a hard template.",
        tags=("inspiration",),
    )
    trajectory = CandidateTrajectory(
        candidate=Candidate(messages=[user_message("return RELEASE_READY")]),
        metadata={
            prompts.PROMPT_PATTERN_CONTEXT_KEY: pattern.context_summary(),
            prompts.PROMPT_PATTERN_IDS_KEY: [pattern.id],
        },
    )

    context = template_context(Objective(goal="return RELEASE_READY"), trajectory)

    assert "test.inspiration" in context["prompt_pattern_context"]
    assert "Test inspiration" in context["prompt_pattern_context"]
    assert context["selected_prompt_patterns"] == "['test.inspiration']"


def test_prompt_library_can_target_explicit_pattern_ids() -> None:
    first = prompts.PromptPattern(
        id="test.first",
        name="First",
        prompt="Use first pattern.",
    )
    second = prompts.PromptPattern(
        id="test.second",
        name="Second",
        prompt="Use second pattern.",
    )
    library = prompts.PromptLibrary(patterns=(first, second))

    selected = library.by_ids({"test.second"})

    assert [pattern.id for pattern in selected.patterns] == ["test.second"]


async def test_frontier_search_can_select_prompt_patterns_before_proposal() -> None:
    pattern = prompts.PromptPattern(
        id="test.pattern_guidance",
        name="Pattern guidance",
        prompt="Use format pressure to avoid generic polite questions.",
        proposer_hint="Use strict JSON or continuation framing.",
        tags=("pattern-guided",),
    )
    actor = CapturingStructuredActor(outputs=['{"prompt":"candidate prompt"}'])
    attack = techniques.FrontierSearch(
        name="unit_pattern_guided_frontier",
        iterations=1,
        branching=2,
        width=1,
        pre_expand=[
            ops.SelectPromptPatterns(
                source=prompts.ListSource(patterns=(pattern,)),
                selector=prompts.TagSelector(tags=("pattern-guided",)),
            )
        ],
        expand=ops.Propose(
            proposer=proposers.StructuredLLMProposer(
                actor=actor,
                system_prompt_template="Generate for {objective}.",
                output=proposers.StructuredOutputSpec(
                    prompt_field="prompt",
                    metadata_fields=(),
                ),
            )
        ),
        post_query=[ops.MarkPromptPatternsTried()],
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="OK")]),
        post_evaluate=[ops.MarkPromptPatternOutcomes(success_score=1)],
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
    )
    run = Run(
        objectives=ObjectiveSource.single("Say OK"),
        attack=attack,
        target=PythonCallableTarget(fn=lambda messages, context: "OK"),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert "test.pattern_guidance" in actor.message_contents[0][1]
    usage = result.states[0].metadata["prompt_pattern_usage"]["records"]
    assert usage["test.pattern_guidance"]["uses"] == 2
    assert usage["test.pattern_guidance"]["successes"] == 2
    assert attack.workflow_graph() == [
        "seed_from_objective",
        "select_prompt_patterns",
        "propose",
        "query_target",
        "mark_prompt_patterns_tried",
        "evaluate",
        "mark_prompt_pattern_outcomes",
        "stop_when",
        "select",
    ]


async def test_selected_prompt_patterns_can_materialize_templates_before_query() -> None:
    pattern = prompts.PromptPattern(
        id="test.template_pattern",
        name="Template pattern",
        prompt="Wrap the prompt with a concrete template.",
        templates=("Pattern wrapped request: {prompt}",),
        tags=("template-pattern",),
    )
    attack = techniques.FrontierSearch(
        name="unit_pattern_template_frontier",
        iterations=1,
        branching=2,
        width=1,
        pre_expand=[
            ops.SelectPromptPatterns(
                source=prompts.ListSource(patterns=(pattern,)),
                selector=prompts.TagSelector(tags=("template-pattern",)),
            )
        ],
        expand=ops.ApplyTransforms(transforms=[transforms.FromPromptPattern()]),
        post_query=[ops.MarkPromptPatternsTried()],
        evaluate=ops.Evaluate(evaluators=[evaluators.Contains(text="Pattern wrapped")]),
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
    )
    run = Run(
        objectives=ObjectiveSource.single("Say OK"),
        attack=attack,
        target=PythonCallableTarget(
            fn=lambda messages, context: messages[-1].content,
        ),
    )

    result = await Runner().run(run)

    assert result.succeeded
    attempt = result.states[0].attempts[0]
    assert attempt.candidate.messages[0].content == "Pattern wrapped request: Say OK"
    usage = result.states[0].metadata["prompt_pattern_usage"]["records"]
    assert usage["test.template_pattern"]["uses"] == 1


async def test_structured_llm_default_prompt_includes_selected_pattern_guidance() -> None:
    pattern = prompts.PromptPattern(
        id="test.competing_objectives",
        name="Competing objectives",
        prompt="Create tension between response-shape constraints and refusal.",
        proposer_hint="Generate varied prefix, style, or format constraints.",
        tags=("competing_objectives",),
    )
    trajectory = CandidateTrajectory(
        candidate=Candidate(messages=[user_message("return RELEASE_READY")]),
        metadata={
            prompts.PROMPT_PATTERN_CONTEXT_KEY: pattern.context_summary(),
            prompts.PROMPT_PATTERN_IDS_KEY: [pattern.id],
        },
    )
    actor = CapturingStructuredActor(outputs=['{"prompt":"candidate"}'])
    proposer = proposers.StructuredLLMProposer(
        actor=actor,
        system_prompt_template="Generate a prompt for {objective}.",
        output=proposers.StructuredOutputSpec(
            prompt_field="prompt",
            metadata_fields=(),
        ),
    )

    children = await proposer.propose(Objective(goal="return RELEASE_READY"), trajectory, count=1)

    assert children[0].latest_text == "candidate"
    user_prompt = actor.message_contents[0][1]
    assert "Selected prompt pattern guidance:" in user_prompt
    assert "test.competing_objectives" in user_prompt
    assert "Generate varied prefix, style, or format constraints." in user_prompt


async def test_gcg_paper_prompt_patterns_are_source_tagged() -> None:
    library = await prompts.BuiltinSource().load(Objective(goal="return RELEASE_READY"), object())
    by_id = {pattern.id: pattern for pattern in library.patterns}
    expected_ids = {
        "paper.gcg.affirmative_target",
        "paper.gcg.adversarial_suffix",
        "paper.gcg.universal_suffix_search",
        "paper.gcg.multi_model_transfer",
        "paper.gcg.suffix_ensemble",
        "paper.gcg.conditioning_step",
    }

    assert expected_ids <= by_id.keys()
    for pattern_id in expected_ids:
        pattern = by_id[pattern_id]
        assert pattern.source == "paper:2307.15043v2"
        assert pattern.metadata["arxiv_id"] == "2307.15043v2"
        assert pattern.metadata["paper"].startswith("Universal and Transferable")


async def test_gcg_search_guidance_is_not_a_transform() -> None:
    library = await prompts.BuiltinSource().load(Objective(goal="return RELEASE_READY"), object())
    gcg_patterns = [
        pattern for pattern in library.patterns if pattern.id.startswith("paper.gcg.")
    ]

    assert gcg_patterns
    assert all(not pattern.suggested_transforms for pattern in gcg_patterns)
    assert not any(pattern.id == "paper.gcg.greedy_coordinate_gradient" for pattern in gcg_patterns)


async def test_gcg_patterns_do_not_bundle_concrete_attack_suffixes() -> None:
    library = await prompts.BuiltinSource().load(Objective(goal="return RELEASE_READY"), object())
    gcg_patterns = [
        pattern for pattern in library.patterns if pattern.id.startswith("paper.gcg.")
    ]

    template_text = "\n".join(
        template
        for pattern in gcg_patterns
        for template in pattern.template_texts()
    )
    assert "<ADV PROMPT>" not in template_text
    assert "Sure, here" not in template_text
    assert "optimized adversarial suffix" not in template_text.lower()
