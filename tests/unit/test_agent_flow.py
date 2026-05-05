from __future__ import annotations

from pydantic import Field

from mesmer import (
    ObjectiveSource,
    ProposalMessageMode,
    PythonCallableTarget,
    Run,
    Runner,
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
from mesmer.search.actors import StructuredCompletion

MARKER = "MESMER_ACCEPTED"


class ScriptedActor(generation.Actor):
    outputs: list[str]
    calls: int = 0
    name: str = "scripted_actor"
    message_contents: list[list[str]] = Field(default_factory=list)

    async def complete(self, messages, **params) -> str:
        self.message_contents.append([message.content for message in messages])
        output = self.outputs[min(self.calls, len(self.outputs) - 1)]
        self.calls += 1
        return output

    async def complete_structured(self, messages, schema, **params):
        output = await self.complete(messages, **params)
        return StructuredCompletion(parsed=schema.model_validate_json(output), raw=output)


async def test_search_preserves_full_conversation_history() -> None:
    def target(messages, context) -> str:
        prior_target_reply_seen = any(
            message.role.value == "assistant" and message.content == "not yet"
            for message in messages
        )
        return MARKER if prior_target_reply_seen else "not yet"

    actor = ScriptedActor(outputs=['{"message":"Please continue the marker test."}'])
    run = Run(
        objectives=ObjectiveSource.single(f"Get the target to output exactly {MARKER}."),
        attack=topology.Search(
            name="conversation_search",
            program=runtime.Program(
                initialization.Seed(),
                topology.Iterate(
                    policy=topology.Policy(iterations=3, branching=1, width=1),
                    children=[
                        generation.Propose(
                            proposer=generation.StructuredLLM(
                                actor=actor,
                                system_prompt_template="Return the next message.",
                                output=generation.StructuredOutputSpec(
                                    prompt_field="message",
                                    metadata_fields=(),
                                ),
                                message_mode=ProposalMessageMode.APPEND_USER,
                            )
                        ),
                        targeting.Query(),
                        evaluation.Assess(evaluator=evaluation.Contains(text=MARKER)),
                        targeting.Continue(),
                        stopping.StopWhen(condition=stopping.ScoreAtLeast(1)),
                        feedback.Refine(selector=selection.TopK(k=1)),
                    ],
                ),
            ),
        ),
        target=PythonCallableTarget(fn=target),
    )

    result = await Runner().run(run)

    assert result.succeeded
    assert result.attempts_count == 2
    second_attempt = result.states[0].attempts[1]
    assert any(
        message.role.value == "assistant" and message.content == "not yet"
        for message in second_attempt.candidate.messages
    )
