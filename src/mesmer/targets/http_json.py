from __future__ import annotations

import time
from typing import Any

import httpx
from pydantic import Field

from mesmer.artifacts.messages import Message
from mesmer.core.constants import DEFAULT_TIMEOUT_SECONDS
from mesmer.targets.base import Target, TargetContext, TargetResponse


def _render_template(value: Any, messages: list[Message], context: TargetContext) -> Any:
    if isinstance(value, str):
        latest_user = next((m.content for m in reversed(messages) if m.role.value == "user"), "")
        return value.format(
            prompt=latest_user,
            goal=context.objective.goal,
            messages=[m.model_dump(mode="json") for m in messages],
            **context.variables,
        )
    if isinstance(value, list):
        return [_render_template(item, messages, context) for item in value]
    if isinstance(value, dict):
        return {key: _render_template(item, messages, context) for key, item in value.items()}
    return value


def _extract_json_path(payload: Any, path: str) -> Any:
    current = payload
    for part in path.split("."):
        if not part:
            continue
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


class HTTPJsonTarget(Target):
    url: str
    method: str = "POST"
    headers: dict[str, str] = Field(default_factory=dict)
    body_template: dict[str, Any] = Field(default_factory=lambda: {"prompt": "{prompt}"})
    response_path: str = "text"
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    name: str = "http_json"

    async def call(self, messages: list[Message], context: TargetContext) -> TargetResponse:
        start = time.perf_counter()
        body = _render_template(self.body_template, messages, context)
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.request(self.method, self.url, headers=self.headers, json=body)
            response.raise_for_status()
        payload = response.json()
        text = str(_extract_json_path(payload, self.response_path))
        return TargetResponse(
            text=text,
            raw=payload,
            latency_ms=(time.perf_counter() - start) * 1000,
            metadata={"status_code": response.status_code},
        )
