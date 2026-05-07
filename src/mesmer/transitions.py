from __future__ import annotations

from typing import Any

from pydantic import Field

from mesmer.core.config import MesmerModel


class Transition(MesmerModel):
    operator: str
    before: dict[str, Any]
    patch: dict[str, Any]
    after: dict[str, Any]
    events: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    duration_ms: float | None = None
    error: str | None = None
