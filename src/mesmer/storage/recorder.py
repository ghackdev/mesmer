from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.execution.state import Attempt


class Recorder(MesmerModel, ABC):
    name: str

    async def start_run(self, run_id: str) -> None:
        return None

    @abstractmethod
    async def record_attempt(self, attempt: Attempt) -> None:
        raise NotImplementedError

    async def finish_run(self, run_id: str) -> None:
        return None


class MemoryRecorder(Recorder):
    name: str = "memory"
    attempts: list[Attempt] = Field(default_factory=list)

    async def record_attempt(self, attempt: Attempt) -> None:
        self.attempts.append(attempt)
