from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from mesmer.artifacts.messages import Message, to_litellm_messages
from mesmer.core.config import MesmerModel
from mesmer.core.enums import ActorRole
from mesmer.core.errors import ConfigError, StructuredOutputError

StructuredSchemaT = TypeVar("StructuredSchemaT", bound=BaseModel)


class StructuredCompletion(MesmerModel, Generic[StructuredSchemaT]):
    parsed: StructuredSchemaT
    raw: str


class ChatActor(MesmerModel, ABC):
    name: str
    role: ActorRole | None = None

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        **params: Any,
    ) -> str:
        raise NotImplementedError

    async def complete_structured(
        self,
        messages: list[Message],
        schema: type[StructuredSchemaT],
        **params: Any,
    ) -> StructuredCompletion[StructuredSchemaT]:
        raise ConfigError(
            f"{self.__class__.__name__} does not support structured output."
        )


class LiteLLMChatActor(ChatActor):
    model: str
    generation_params: dict[str, Any] = Field(default_factory=dict)
    name: str = "litellm_actor"

    async def complete(
        self,
        messages: list[Message],
        **params: Any,
    ) -> str:
        from litellm import acompletion

        merged_params = {**self.generation_params, **params}
        response = await acompletion(
            model=self.model,
            messages=to_litellm_messages(messages),
            **merged_params,
        )
        return response.choices[0].message.content or ""

    async def complete_structured(
        self,
        messages: list[Message],
        schema: type[StructuredSchemaT],
        **params: Any,
    ) -> StructuredCompletion[StructuredSchemaT]:
        from litellm import acompletion

        merged_params = {**self.generation_params, **params}
        merged_params.setdefault("response_format", schema)
        response = await acompletion(
            model=self.model,
            messages=to_litellm_messages(messages),
            **merged_params,
        )
        raw = response.choices[0].message.content or ""
        try:
            parsed = schema.model_validate_json(raw)
        except ValueError as exc:
            raise StructuredOutputError(
                f"Model output did not match structured schema {schema.__name__}.",
                raw_output=raw,
            ) from exc
        return StructuredCompletion(parsed=parsed, raw=raw)
