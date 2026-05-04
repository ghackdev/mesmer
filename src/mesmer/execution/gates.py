from __future__ import annotations

from abc import ABC, abstractmethod

from mesmer.core.config import MesmerModel
from mesmer.core.enums import Capability
from mesmer.core.errors import CapabilityError


class Gate(MesmerModel, ABC):
    name: str

    @abstractmethod
    def validate(self) -> None:
        raise NotImplementedError


class CapabilityGate(Gate):
    required: set[Capability]
    provided: set[Capability]
    name: str = "capability"

    def validate(self) -> None:
        missing = self.required - self.provided
        if missing:
            missing_text = ", ".join(sorted(item.value for item in missing))
            raise CapabilityError(f"Missing required capabilities: {missing_text}")
