from __future__ import annotations

from enum import StrEnum


class PrimitiveKind(StrEnum):
    OBJECTIVE_SOURCE = "objective_source"
    TRANSFORM = "transform"
    GATE = "gate"
    SELECTOR = "selector"
    ATTACKER = "attacker"
    TARGET = "target"
    JUDGE = "judge"
    DETECTOR = "detector"
    RECORDER = "recorder"
    METRIC = "metric"


class Capability(StrEnum):
    MULTI_TURN = "multi_turn"
    MULTI_CONVERSATION = "multi_conversation"
    VISION_INPUT = "vision_input"
    FILES = "files"
    TOOLS = "tools"
    MCP = "mcp"
    STREAMING = "streaming"
    LOGPROBS = "logprobs"
    HIDDEN_STATES = "hidden_states"
    BROWSER = "browser"


class ArtifactKind(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    MESSAGES = "messages"
    JSON = "json"


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunOutcome(StrEnum):
    OBJECTIVE_SUCCEEDED = "objective_succeeded"
    OBJECTIVE_FAILED = "objective_failed"
    EXECUTION_FAILED = "execution_failed"


class LogFormat(StrEnum):
    RICH = "rich"
    COMPACT = "compact"


class DatasetFormat(StrEnum):
    CSV = "csv"
    JSONL = "jsonl"


class JudgementStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class SpanName(StrEnum):
    RUN = "mesmer.run"
    OBJECTIVE = "mesmer.objective"
    ATTACKER_STEP = "mesmer.attacker.step"
    AGENT_ACTION = "mesmer.agent.action"
    TOOL_CALL = "mesmer.tool.call"
    MCP_CALL = "mesmer.mcp.call"
    TRANSFORM = "mesmer.transform"
    SELECTOR = "mesmer.selector"
    TARGET_CALL = "mesmer.target.call"
    JUDGE = "mesmer.judge"
    DETECTOR = "mesmer.detector"
    RECORDER = "mesmer.recorder"
    BENCHMARK = "mesmer.benchmark"
    METRIC = "mesmer.metric"


class MetricName(StrEnum):
    ATTACK_SUCCESS_RATE = "attack_success_rate"
    REFUSAL_RATE = "refusal_rate"
    PASS_AT_K = "pass_at_k"
    MEAN_QUERIES = "mean_queries"
    MEAN_TURNS = "mean_turns"
    MEAN_LATENCY_MS = "mean_latency_ms"
    MEAN_COST = "mean_cost"
    JUDGE_AGREEMENT = "judge_agreement"
    ROBUSTNESS_DELTA = "robustness_delta"
