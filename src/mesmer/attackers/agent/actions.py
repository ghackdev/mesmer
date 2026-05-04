from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.core.ids import new_id


class AgentActionKind(StrEnum):
    SEND_MESSAGE = "send_message"
    START_CONVERSATION = "start_conversation"
    FORK_CONVERSATION = "fork_conversation"
    CALL_TOOL = "call_tool"
    OBSERVE = "observe"
    STOP = "stop"


class AgentAction(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("agent_action"))
    kind: AgentActionKind
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
