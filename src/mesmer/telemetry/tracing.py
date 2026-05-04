from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace

from mesmer.telemetry.attributes import sanitize_attributes

TRACER_NAME = "mesmer"


def get_tracer() -> trace.Tracer:
    return trace.get_tracer(TRACER_NAME)


@contextmanager
def start_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[None]:
    with get_tracer().start_as_current_span(
        name,
        attributes=sanitize_attributes(attributes or {}),
    ):
        yield
