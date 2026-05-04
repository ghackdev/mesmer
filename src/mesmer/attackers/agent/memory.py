from __future__ import annotations

from pydantic import Field

from mesmer.core.config import MesmerModel


class MemoryEntry(MesmerModel):
    key: str
    value: str


class EpisodicMemory(MesmerModel):
    entries: list[MemoryEntry] = Field(default_factory=list)

    def add(self, key: str, value: str) -> None:
        self.entries.append(MemoryEntry(key=key, value=value))

    def render(self) -> str:
        return "\n".join(f"{entry.key}: {entry.value}" for entry in self.entries)
