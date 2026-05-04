from __future__ import annotations

CREATE_ATTEMPTS_TABLE = """
CREATE TABLE IF NOT EXISTS attempts (
    id TEXT PRIMARY KEY,
    objective_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""
