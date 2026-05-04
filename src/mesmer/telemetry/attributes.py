from __future__ import annotations

from typing import Any

from mesmer.core.constants import METADATA_REDACTED_VALUE, SENSITIVE_METADATA_KEYS


def sanitize_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in attributes.items():
        key_text = key.lower()
        if any(sensitive in key_text for sensitive in SENSITIVE_METADATA_KEYS):
            clean[key] = METADATA_REDACTED_VALUE
        elif isinstance(value, str | int | float | bool) or value is None:
            clean[key] = value
        else:
            clean[key] = str(value)
    return clean
