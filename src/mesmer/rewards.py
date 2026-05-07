from __future__ import annotations

from pydantic import Field

from mesmer.core.config import MesmerModel


class Score(MesmerModel):
    scale: float = Field(default=1.0, ge=0)


__all__ = [
    "Score",
]
