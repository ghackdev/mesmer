from __future__ import annotations

import json
import time
from typing import Any

import websockets
from pydantic import Field

from mesmer.artifacts.messages import Message
from mesmer.core.constants import DEFAULT_TIMEOUT_SECONDS
from mesmer.core.enums import Capability
from mesmer.targets.base import Target, TargetContext, TargetResponse
from mesmer.targets.http_json import _extract_json_path, _render_template


class WebSocketTarget(Target):
    url: str
    send_template: dict[str, Any] = Field(default_factory=lambda: {"prompt": "{prompt}"})
    response_path: str = "text"
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    name: str = "websocket"
    capabilities: set[Capability] = Field(default_factory=lambda: {Capability.STREAMING})

    async def call(self, messages: list[Message], context: TargetContext) -> TargetResponse:
        start = time.perf_counter()
        payload = _render_template(self.send_template, messages, context)
        async with websockets.connect(self.url, open_timeout=self.timeout_seconds) as ws:
            await ws.send(json.dumps(payload))
            raw = json.loads(await ws.recv())
        text = str(_extract_json_path(raw, self.response_path))
        return TargetResponse(text=text, raw=raw, latency_ms=(time.perf_counter() - start) * 1000)
