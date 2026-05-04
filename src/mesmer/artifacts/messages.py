from __future__ import annotations

from typing import Any

from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.core.enums import MessageRole


class Message(MesmerModel):
    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


def user_message(content: str) -> Message:
    return Message(role=MessageRole.USER, content=content)


def assistant_message(content: str) -> Message:
    return Message(role=MessageRole.ASSISTANT, content=content)


def system_message(content: str) -> Message:
    return Message(role=MessageRole.SYSTEM, content=content)


def to_litellm_messages(messages: list[Message]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for message in messages:
        item: dict[str, Any] = {"role": message.role.value, "content": message.content}
        if message.name is not None:
            item["name"] = message.name
        if message.tool_call_id is not None:
            item["tool_call_id"] = message.tool_call_id
        result.append(item)
    return result
