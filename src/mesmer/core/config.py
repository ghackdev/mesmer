from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MesmerModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=False,
        validate_assignment=True,
    )
