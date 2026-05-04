from __future__ import annotations

from mesmer import PythonCallableTarget, register_target
from mesmer.core.enums import PrimitiveKind
from mesmer.core.registry import registry


def test_optional_registry_resolves_named_target() -> None:
    register_target("unit_callable", PythonCallableTarget)

    assert registry.resolve(PrimitiveKind.TARGET, "unit_callable") is PythonCallableTarget
