from __future__ import annotations

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_QUERIES = 32
DEFAULT_MAX_TURNS = 12
DEFAULT_MAX_STEPS = 20
DEFAULT_REPETITIONS = 1
DEFAULT_SQLITE_PATH = ".mesmer/runs.sqlite3"
DEFAULT_ARTIFACT_DIR = ".mesmer/artifacts"
DEFAULT_DATASET_CACHE_DIR = ".mesmer/cache/datasets"
DATASET_TARGET_METADATA_KEY = "target"
DATASET_SOURCE_URL_METADATA_KEY = "source_url"
DATASET_ROW_INDEX_METADATA_KEY = "row_index"

METADATA_REDACTED_VALUE = "[redacted]"
SENSITIVE_METADATA_KEYS = frozenset(
    {
        "authorization",
        "api_key",
        "apikey",
        "cookie",
        "password",
        "secret",
        "token",
    }
)
