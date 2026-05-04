from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from mesmer.core.constants import DEFAULT_SQLITE_PATH
from mesmer.execution.state import Attempt
from mesmer.storage.recorder import Recorder
from mesmer.storage.schemas import CREATE_ATTEMPTS_TABLE


class SQLiteRecorder(Recorder):
    path: Path = Path(DEFAULT_SQLITE_PATH)
    name: str = "sqlite"

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.execute(CREATE_ATTEMPTS_TABLE)
        return connection

    async def record_attempt(self, attempt: Attempt) -> None:
        payload = json.dumps(attempt.model_dump(mode="json"), sort_keys=True)
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO attempts (id, objective_id, payload) VALUES (?, ?, ?)",
                (attempt.id, attempt.objective.id, payload),
            )
