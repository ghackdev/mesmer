from __future__ import annotations

import time

import httpx
from pydantic import Field

from mesmer.artifacts.messages import Message
from mesmer.core.enums import Capability
from mesmer.targets.base import TargetContext, TargetResponse
from mesmer.targets.http_json import HTTPJsonTarget, _render_template


class HTTPSseTarget(HTTPJsonTarget):
    event_prefix: str = "data:"
    done_marker: str = "[DONE]"
    name: str = "http_sse"
    capabilities: set[Capability] = Field(default_factory=lambda: {Capability.STREAMING})

    async def call(self, messages: list[Message], context: TargetContext) -> TargetResponse:
        start = time.perf_counter()
        body = _render_template(self.body_template, messages, context)
        chunks: list[str] = []
        async with (
            httpx.AsyncClient(timeout=self.timeout_seconds) as client,
            client.stream(self.method, self.url, headers=self.headers, json=body) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith(self.event_prefix):
                    continue
                data = line.removeprefix(self.event_prefix).strip()
                if data == self.done_marker:
                    break
                chunks.append(data)
        return TargetResponse(text="".join(chunks), latency_ms=(time.perf_counter() - start) * 1000)
