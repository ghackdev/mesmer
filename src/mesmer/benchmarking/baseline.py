from __future__ import annotations

from typing import Any

from mesmer.core.config import MesmerModel


class Baseline(MesmerModel):
    name: str
    config: dict[str, Any]
