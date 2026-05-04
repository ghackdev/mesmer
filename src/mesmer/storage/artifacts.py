from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mesmer.core.constants import DEFAULT_ARTIFACT_DIR


class ArtifactStore:
    def __init__(self, root: str | Path = DEFAULT_ARTIFACT_DIR) -> None:
        self.root = Path(root)

    def write_json(self, name: str, payload: dict[str, Any]) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{name}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path
