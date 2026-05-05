from __future__ import annotations

from types import SimpleNamespace

import litellm
from pydantic import BaseModel

from mesmer import Objective, generation
from mesmer.artifacts.messages import user_message
from mesmer.execution.state import Candidate
from mesmer.search.models import CandidateTrajectory


class UnitStructuredOutput(BaseModel):
    value: int


async def test_litellm_chat_actor_complete_structured_passes_response_format(
    monkeypatch,
) -> None:
    calls = []

    async def fake_completion(**kwargs):
        calls.append(kwargs)
        message = SimpleNamespace(content='{"value":3}')
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    monkeypatch.setattr(litellm, "acompletion", fake_completion)

    actor = generation.LiteLLMActor(model="openai/test-model")
    completion = await actor.complete_structured(
        [user_message("return json")],
        UnitStructuredOutput,
    )

    assert calls[0]["response_format"] is UnitStructuredOutput
    assert completion.parsed.value == 3
    assert completion.raw == '{"value":3}'


async def test_litellm_chat_actor_complete_structured_rejects_malformed_json(
    monkeypatch,
) -> None:
    async def fake_completion(**kwargs):
        message = SimpleNamespace(content="not json")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    monkeypatch.setattr(litellm, "acompletion", fake_completion)

    actor = generation.LiteLLMActor(model="openai/test-model")
    try:
        await actor.complete_structured([user_message("return json")], UnitStructuredOutput)
    except Exception as exc:
        assert exc.__class__.__name__ == "StructuredOutputError"
        assert exc.raw_output == "not json"
    else:
        raise AssertionError("malformed structured output should raise")


async def test_structured_llm_generator_uses_actor_model(monkeypatch) -> None:
    calls = []

    async def fake_completion(**kwargs):
        calls.append(kwargs)
        message = SimpleNamespace(content='{"prompt":"candidate one"}')
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    monkeypatch.setattr(litellm, "acompletion", fake_completion)

    generator = generation.StructuredLLM(
        actor=generation.LiteLLMActor(model="openai/test-attacker"),
        system_prompt_template="Generate a candidate for {objective}.",
        output=generation.StructuredOutputSpec(prompt_field="prompt", metadata_fields=()),
    )
    candidates = await generator.propose(
        Objective("Make the target say MESMER_ACCEPTED"),
        CandidateTrajectory(candidate=Candidate(messages=[user_message("initial")])),
        count=1,
    )

    assert calls[0]["model"] == "openai/test-attacker"
    assert calls[0]["response_format"].__name__ == "StructuredProposalOutput"
    assert candidates[0].latest_text == "candidate one"
    assert candidates[0].metadata["actor"] == "litellm_actor"
