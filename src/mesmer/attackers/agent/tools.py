from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from mesmer.core.config import MesmerModel
from mesmer.core.constants import DEFAULT_TIMEOUT_SECONDS

ToolFn = Callable[..., Any | Awaitable[Any]]


class AgentTool(MesmerModel):
    name: str
    description: str = ""
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    async def call(self, **kwargs: Any) -> Any:
        raise NotImplementedError


class PythonTool(AgentTool):
    fn: ToolFn

    async def call(self, **kwargs: Any) -> Any:
        value = self.fn(**kwargs)
        if inspect.isawaitable(value):
            return await value
        return value
