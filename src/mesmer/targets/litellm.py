from __future__ import annotations

import time
from typing import Any

from pydantic import Field

from mesmer.artifacts.messages import Message, system_message, to_litellm_messages
from mesmer.core.constants import DEFAULT_TIMEOUT_SECONDS
from mesmer.core.enums import Capability
from mesmer.targets.base import Target, TargetContext, TargetResponse


class LiteLLMTarget(Target):
    model: str
    system_prompt: str | None = None
    generation_params: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    name: str = "litellm"
    capabilities: set[Capability] = Field(
        default_factory=lambda: {Capability.MULTI_TURN, Capability.TOOLS}
    )

    async def call(self, messages: list[Message], context: TargetContext) -> TargetResponse:
        from litellm import acompletion

        start = time.perf_counter()
        target_messages = list(messages)
        if self.system_prompt:
            target_messages = [system_message(self.system_prompt), *target_messages]
        response = await acompletion(
            model=self.model,
            messages=to_litellm_messages(target_messages),
            timeout=self.timeout_seconds,
            **self.generation_params,
        )
        choice = response.choices[0]
        text = choice.message.content or ""
        usage = getattr(response, "usage", None)
        finish_reason = getattr(choice, "finish_reason", None)
        return TargetResponse(
            text=text,
            raw=response.model_dump() if hasattr(response, "model_dump") else response,
            finish_reason=finish_reason,
            metadata={"finish_reason": finish_reason},
            latency_ms=(time.perf_counter() - start) * 1000,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
        )
