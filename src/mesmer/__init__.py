from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from mesmer import (
    conditions,
    evaluators,
    feedback,
    mutators,
    ops,
    prompts,
    proposers,
    rewards,
    selectors,
    sources,
    state,
    techniques,
    transforms,
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
from mesmer.benchmarking.report import BudgetCurve, EvidenceMatrix
from mesmer.benchmarking.runner import BenchmarkRunner
from mesmer.core.enums import (
    ActorRole,
    BinaryLabel,
    Capability,
    DatasetFormat,
    EvaluationField,
    EvaluatorFailurePolicy,
    EvaluatorFailureReason,
    LogFormat,
    ProposalMessageMode,
    TargetBinding,
)
from mesmer.core.registry import register_judge, register_target
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
from mesmer.techniques import BestOfNProbe, ConversationAgentProbe, Probe, ProposedProbe

try:
    __version__ = version("mesmer-ai")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "ActorRole",
    "AttackSuccessRate",
    "Benchmark",
    "BenchmarkRunner",
    "BestOfNProbe",
    "BinaryLabel",
    "Budget",
    "BudgetCurve",
    "Capability",
    "Contains",
    "ContainsCriterion",
    "ConversationAgentProbe",
    "CriteriaJudge",
    "DatasetColumnMap",
    "DatasetFormat",
    "EvaluationField",
    "EvaluatorFailurePolicy",
    "EvaluatorFailureReason",
    "EvidenceMatrix",
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
    "Probe",
    "PromptLeakageJudge",
    "ProposalMessageMode",
    "ProposedProbe",
    "PythonCallableTarget",
    "RefusalJudge",
    "RemoteDatasetSource",
    "ReproductionArtifact",
    "ReproductionTarget",
    "Run",
    "Runner",
    "SQLiteRecorder",
    "TargetBinding",
    "WebSocketTarget",
    "__version__",
    "assistant_message",
    "conditions",
    "evaluators",
    "feedback",
    "mutators",
    "ops",
    "prompts",
    "proposers",
    "register_judge",
    "register_target",
    "rewards",
    "selectors",
    "sources",
    "state",
    "system_message",
    "techniques",
    "to_litellm_messages",
    "transforms",
    "user_message",
    "workflow",
]
