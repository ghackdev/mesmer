from __future__ import annotations

from typing import Any

from mesmer.core.config import MesmerModel
from mesmer.telemetry.logger import NULL_LOGGER, RunLogger


class AttackContext(MesmerModel):
    target: object
    judges: list[object]
    budget_tracker: object
    policy: Any = None
    recorder: object | None = None
    logger: RunLogger = NULL_LOGGER
