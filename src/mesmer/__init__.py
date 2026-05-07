from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from mesmer import (
    conditions,
    constraints,
    data,
    evaluation,
    evaluators,
    feedback,
    generation,
    initialization,
    mutators,
    ops,
    population,
    prompts,
    proposers,
    rewards,
    runtime,
    selection,
    selectors,
    sources,
    state,
    stopping,
    targeting,
    techniques,
    transforms,
    variation,
    workflow,
)
from mesmer.artifacts.messages import (
    Message,
    assistant_message,
    system_message,
    to_litellm_messages,
    user_message,
)
from mesmer.benchmarking.benchmark import Benchmark
from mesmer.benchmarking.metrics import AttackSuccessRate, MeanCost, MeanQueries, MeanTurns
from mesmer.benchmarking.runner import BenchmarkRunner
from mesmer.core.enums import (
    ActorRole,
    BinaryLabel,
    DatasetFormat,
    EvaluationField,
    EvaluatorFailurePolicy,
    EvaluatorFailureReason,
    LogFormat,
    ProposalMessageMode,
    StateFact,
    TargetBinding,
)
from mesmer.core.registry import register_attacker, register_judge, register_target
from mesmer.datasets import DatasetColumnMap, RemoteDatasetSource
from mesmer.execution.budgets import Budget
from mesmer.execution.run import Run
from mesmer.execution.runner import Runner
from mesmer.execution.state import ReproductionArtifact, ReproductionTarget
from mesmer.judging.exact import Contains, CriteriaJudge
from mesmer.judging.leakage import PromptLeakageJudge
from mesmer.judging.refusal import RefusalJudge
from mesmer.objectives.criteria import Contains as ContainsCriterion
from mesmer.objectives.models import InitialState, Objective
from mesmer.objectives.sources import ObjectiveSource
from mesmer.storage.recorder import MemoryRecorder
from mesmer.storage.sqlite import SQLiteRecorder
from mesmer.targets.callable import PythonCallableTarget
from mesmer.targets.http_json import HTTPJsonTarget
from mesmer.targets.http_sse import HTTPSseTarget
from mesmer.targets.litellm import LiteLLMTarget
from mesmer.targets.websocket import WebSocketTarget

try:
    __version__ = version("mesmer-ai")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "ActorRole",
    "AttackSuccessRate",
    "Benchmark",
    "BenchmarkRunner",
    "BinaryLabel",
    "Budget",
    "Contains",
    "ContainsCriterion",
    "CriteriaJudge",
    "DatasetColumnMap",
    "DatasetFormat",
    "EvaluationField",
    "EvaluatorFailurePolicy",
    "EvaluatorFailureReason",
    "HTTPJsonTarget",
    "HTTPSseTarget",
    "InitialState",
    "LiteLLMTarget",
    "LogFormat",
    "MeanCost",
    "MeanQueries",
    "MeanTurns",
    "MemoryRecorder",
    "Message",
    "Objective",
    "ObjectiveSource",
    "PromptLeakageJudge",
    "ProposalMessageMode",
    "PythonCallableTarget",
    "RefusalJudge",
    "RemoteDatasetSource",
    "ReproductionArtifact",
    "ReproductionTarget",
    "Run",
    "Runner",
    "SQLiteRecorder",
    "StateFact",
    "TargetBinding",
    "WebSocketTarget",
    "__version__",
    "assistant_message",
    "conditions",
    "constraints",
    "data",
    "evaluation",
    "evaluators",
    "feedback",
    "generation",
    "initialization",
    "mutators",
    "ops",
    "population",
    "prompts",
    "proposers",
    "register_attacker",
    "register_judge",
    "register_target",
    "rewards",
    "runtime",
    "selection",
    "selectors",
    "sources",
    "state",
    "stopping",
    "system_message",
    "targeting",
    "techniques",
    "to_litellm_messages",
    "transforms",
    "user_message",
    "variation",
    "workflow",
]
