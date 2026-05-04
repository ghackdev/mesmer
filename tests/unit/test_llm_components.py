from __future__ import annotations

from types import SimpleNamespace

import litellm
from pydantic import BaseModel

from mesmer import LiteLLMChatActor, LLMCandidateExpander, Objective
from mesmer.artifacts.messages import user_message
from mesmer.execution.state import Candidate


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

    actor = LiteLLMChatActor(model="openai/test-model")
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

    actor = LiteLLMChatActor(model="openai/test-model")
    try:
        await actor.complete_structured([user_message("return json")], UnitStructuredOutput)
    except Exception as exc:
        assert exc.__class__.__name__ == "StructuredOutputError"
        assert exc.raw_output == "not json"
    else:
        raise AssertionError("malformed structured output should raise")


async def test_llm_candidate_expander_uses_attacker_model(monkeypatch) -> None:
    calls = []

    async def fake_completion(**kwargs):
        calls.append(kwargs)
        message = SimpleNamespace(content='{"candidates":["candidate one","candidate two"]}')
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    monkeypatch.setattr(litellm, "acompletion", fake_completion)

    expander = LLMCandidateExpander(model="openai/test-attacker", n=2)
    candidates = await expander.expand(
        Objective("Make the target say MESMER_ACCEPTED"),
        Candidate(messages=[user_message("initial")]),
        branching_factor=2,
    )

    assert calls[0]["model"] == "openai/test-attacker"
    assert calls[0]["response_format"].__name__ == "CandidateExpansionOutput"
    assert [candidate.messages[-1].content for candidate in candidates] == [
        "candidate one",
        "candidate two",
    ]
    assert candidates[0].metadata["attacker_model"] == "openai/test-attacker"
