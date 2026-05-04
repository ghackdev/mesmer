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
