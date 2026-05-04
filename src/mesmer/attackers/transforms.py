from __future__ import annotations

from abc import ABC, abstractmethod

from mesmer.artifacts.messages import Message
from mesmer.core.config import MesmerModel
from mesmer.execution.state import Candidate
from mesmer.objectives.models import Objective


class Transform(MesmerModel, ABC):
    name: str

    @abstractmethod
    async def apply(self, objective: Objective, candidate: Candidate) -> list[Candidate]:
        raise NotImplementedError


class IdentityTransform(Transform):
    name: str = "identity"

    async def apply(self, objective: Objective, candidate: Candidate) -> list[Candidate]:
        return [candidate]


class StaticPrefixTransform(Transform):
    prefix: str
    name: str = "static_prefix"

    async def apply(self, objective: Objective, candidate: Candidate) -> list[Candidate]:
        messages = list(candidate.messages)
        if messages:
            first = messages[0]
            messages[0] = Message(
                role=first.role,
                content=f"{self.prefix}{first.content}",
                name=first.name,
                tool_call_id=first.tool_call_id,
                metadata=first.metadata,
            )
        return [
            Candidate(
                messages=messages,
                metadata={**candidate.metadata, "transform": self.name},
            )
        ]


class Paraphrase(Transform):
    """LiteLLM-backed paraphrase transform.

    If no model is configured, this behaves as identity so unit tests can run without API calls.
    """

    model: str | None = None
    name: str = "paraphrase"

    async def apply(self, objective: Objective, candidate: Candidate) -> list[Candidate]:
        if self.model is None:
            return [candidate]
        from litellm import acompletion

        prompt = "\n".join(message.content for message in candidate.messages)
        response = await acompletion(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Rewrite the following benign testing prompt while preserving its intent:\n"
                        f"{prompt}"
                    ),
                }
            ],
        )
        text = response.choices[0].message.content or prompt
        return [Candidate(messages=[Message(role=candidate.messages[0].role, content=text)])]
