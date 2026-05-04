from __future__ import annotations

from types import SimpleNamespace

import litellm

from mesmer import LLMCandidateExpander, Objective
from mesmer.artifacts.messages import user_message
from mesmer.execution.state import Candidate


async def test_llm_candidate_expander_uses_attacker_model(monkeypatch) -> None:
    calls = []

    async def fake_completion(**kwargs):
        calls.append(kwargs)
        message = SimpleNamespace(content="candidate one\ncandidate two")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    monkeypatch.setattr(litellm, "acompletion", fake_completion)

    expander = LLMCandidateExpander(model="openai/test-attacker", n=2)
    candidates = await expander.expand(
        Objective("Make the target say MESMER_ACCEPTED"),
        Candidate(messages=[user_message("initial")]),
        branching_factor=2,
    )

    assert calls[0]["model"] == "openai/test-attacker"
    assert [candidate.messages[-1].content for candidate in candidates] == [
        "candidate one",
        "candidate two",
    ]
    assert candidates[0].metadata["attacker_model"] == "openai/test-attacker"
