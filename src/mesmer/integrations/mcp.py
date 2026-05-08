from __future__ import annotations

from pathlib import Path

from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.core.constants import DEFAULT_TIMEOUT_SECONDS


class MCPServerSpec(MesmerModel):
    name: str
    command: list[str]
    cwd: Path | None = None
    env: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

__all__ = ["MCPServerSpec"]
