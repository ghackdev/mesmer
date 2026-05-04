from __future__ import annotations

from types import SimpleNamespace

import litellm

from mesmer import (
    AgentFlow,
    Contains,
    ConversationPolicy,
    LLMPlanner,
    ObjectiveSource,
    PythonCallableTarget,
    Run,
    Runner,
)

MARKER = "MESMER_ACCEPTED"


async def test_agent_flow_preserves_full_conversation_history(monkeypatch) -> None:
    async def fake_completion(**kwargs):
        message = SimpleNamespace(content="Please continue the marker test.")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    def target(messages, context) -> str:
        prior_target_reply_seen = any(
            message.role.value == "assistant" and message.content == "not yet"
            for message in messages
        )
        return MARKER if prior_target_reply_seen else "not yet"

    monkeypatch.setattr(litellm, "acompletion", fake_completion)

    run = Run(
        objectives=ObjectiveSource.single(f"Get the target to output exactly {MARKER}."),
        attack=AgentFlow(
            planner=LLMPlanner(model="openai/test-attacker"),
            policy=ConversationPolicy(max_turns=3),
        ),
        target=PythonCallableTarget(fn=target),
        judges=[Contains(text=MARKER)],
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert result.attempts_count == 2
    second_attempt = result.states[0].attempts[1]
    assert any(
        message.role.value == "assistant" and message.content == "not yet"
        for message in second_attempt.candidate.messages
    )
