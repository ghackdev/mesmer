from __future__ import annotations

from typing import Any

from mesmer.artifacts.models import AnyArtifact


def artifact_to_json(artifact: AnyArtifact) -> dict[str, Any]:
    return artifact.model_dump(mode="json")
