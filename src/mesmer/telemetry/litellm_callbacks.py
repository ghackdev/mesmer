from __future__ import annotations

from typing import Any


def attach_litellm_metadata(metadata: dict[str, Any], response: Any) -> dict[str, Any]:
    usage = getattr(response, "usage", None)
    if usage is not None:
        metadata["litellm.prompt_tokens"] = getattr(usage, "prompt_tokens", None)
        metadata["litellm.completion_tokens"] = getattr(usage, "completion_tokens", None)
    return metadata
