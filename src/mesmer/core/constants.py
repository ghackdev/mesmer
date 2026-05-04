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

DEFAULT_PROPOSAL_PROMPT_FIELD = "prompt"
DEFAULT_PROPOSAL_IMPROVEMENT_FIELD = "improvement"
DEFAULT_SEARCH_STOP_REASON = "search_exhausted"
SUCCESS_TERMINATION_REASON = "termination_satisfied"
EVALUATION_SCORE_METADATA_KEY = "evaluation_score"
EVALUATION_NORMALIZED_SCORE_METADATA_KEY = "evaluation_normalized_score"
DEFAULT_EVALUATOR_PARSE_RETRIES = 1
EVALUATOR_FAILURE_REASON_METADATA_KEY = "failure_reason"
EVALUATOR_FAILURE_POLICY_METADATA_KEY = "failure_policy"
EVALUATOR_PARSE_RETRIES_METADATA_KEY = "parse_retries"
EVALUATOR_PARSE_ERRORS_METADATA_KEY = "parse_errors"
EVALUATOR_RAW_OUTPUTS_METADATA_KEY = "raw_outputs"

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
