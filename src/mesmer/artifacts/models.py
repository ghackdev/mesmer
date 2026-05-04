from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field

from mesmer.artifacts.messages import Message
from mesmer.core.config import MesmerModel
from mesmer.core.enums import ArtifactKind
from mesmer.core.ids import new_id


class Artifact(MesmerModel):
    id: str = Field(default_factory=lambda: new_id("artifact"))
    kind: ArtifactKind
    metadata: dict[str, Any] = Field(default_factory=dict)


class TextArtifact(Artifact):
    kind: ArtifactKind = ArtifactKind.TEXT
    text: str


class JsonArtifact(Artifact):
    kind: ArtifactKind = ArtifactKind.JSON
    value: dict[str, Any] | list[Any]


class ImageArtifact(Artifact):
    kind: ArtifactKind = ArtifactKind.IMAGE
    path: Path | None = None
    url: str | None = None
    mime_type: str | None = None


class FileArtifact(Artifact):
    kind: ArtifactKind = ArtifactKind.FILE
    path: Path
    mime_type: str | None = None


class MessageListArtifact(Artifact):
    kind: ArtifactKind = ArtifactKind.MESSAGES
    messages: list[Message]


AnyArtifact = TextArtifact | JsonArtifact | ImageArtifact | FileArtifact | MessageListArtifact
