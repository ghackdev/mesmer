from __future__ import annotations

import inspect
import time
from collections.abc import Awaitable, Callable

from mesmer.artifacts.messages import Message
from mesmer.targets.base import Target, TargetContext, TargetResponse

CallableTargetResult = str | TargetResponse | Awaitable[str | TargetResponse]
CallableTargetFn = Callable[[list[Message], TargetContext], CallableTargetResult]


class PythonCallableTarget(Target):
    fn: CallableTargetFn
    name: str = "python_callable"

    async def call(self, messages: list[Message], context: TargetContext) -> TargetResponse:
        start = time.perf_counter()
        value = self.fn(messages, context)
        if inspect.isawaitable(value):
            value = await value
        latency_ms = (time.perf_counter() - start) * 1000
        if isinstance(value, TargetResponse):
            value.latency_ms = value.latency_ms or latency_ms
            return value
        return TargetResponse(text=str(value), latency_ms=latency_ms)
