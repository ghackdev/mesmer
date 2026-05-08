from __future__ import annotations

from pydantic import Field

from mesmer import Objective, prompts, proposers
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

    context = template_context(Objective("return RELEASE_READY"), trajectory)

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

    children = await proposer.propose(Objective("return RELEASE_READY"), trajectory, count=1)

    assert children[0].latest_text == "candidate"
    user_prompt = actor.message_contents[0][1]
    assert "Selected prompt pattern guidance:" in user_prompt
    assert "test.competing_objectives" in user_prompt
    assert "Generate varied prefix, style, or format constraints." in user_prompt
