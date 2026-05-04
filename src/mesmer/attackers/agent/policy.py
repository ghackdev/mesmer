from __future__ import annotations

from mesmer.core.config import MesmerModel
from mesmer.core.constants import DEFAULT_MAX_STEPS, DEFAULT_MAX_TURNS


class AgentPolicy(MesmerModel):
    max_steps: int = DEFAULT_MAX_STEPS
    max_turns: int = DEFAULT_MAX_TURNS
    max_conversations: int = 1
    allow_tools: bool = True
    allow_mcp: bool = False
