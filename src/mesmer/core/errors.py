from __future__ import annotations


class MesmerError(Exception):
    """Base exception for Mesmer."""


class ConfigError(MesmerError):
    """Raised when a configuration is invalid."""


class RegistryError(MesmerError):
    """Raised when named primitive resolution fails."""


class CapabilityError(MesmerError):
    """Raised when a primitive requires unsupported capabilities."""


class BudgetExceededError(MesmerError):
    """Raised when a run exceeds a configured budget."""


class TargetError(MesmerError):
    """Raised when target invocation fails."""


class JudgeError(MesmerError):
    """Raised when judging fails."""


class EvaluatorParseError(MesmerError):
    """Raised when evaluator model output cannot be parsed."""

    def __init__(
        self,
        message: str,
        *,
        raw_outputs: list[str],
        parse_errors: list[dict[str, object]],
    ) -> None:
        super().__init__(message)
        self.raw_outputs = raw_outputs
        self.parse_errors = parse_errors


class StructuredOutputError(MesmerError, ValueError):
    """Raised when structured model output cannot be validated."""

    def __init__(self, message: str, *, raw_output: str | None = None) -> None:
        super().__init__(message)
        self.raw_output = raw_output

