from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from mesmer.core.enums import PrimitiveKind
from mesmer.core.errors import RegistryError

T = TypeVar("T")


class PrimitiveRegistry:
    """Optional name-to-class registry for configs, plugins, and saved specs."""

    def __init__(self) -> None:
        self._items: dict[PrimitiveKind, dict[str, type[Any]]] = {
            kind: {} for kind in PrimitiveKind
        }

    def register(self, kind: PrimitiveKind, name: str, primitive: type[T]) -> type[T]:
        if not name:
            raise RegistryError("Primitive registry name cannot be empty.")
        self._items[kind][name] = primitive
        return primitive

    def decorator(self, kind: PrimitiveKind, name: str) -> Callable[[type[T]], type[T]]:
        def _register(primitive: type[T]) -> type[T]:
            return self.register(kind, name, primitive)

        return _register

    def resolve(self, kind: PrimitiveKind, name: str) -> type[Any]:
        try:
            return self._items[kind][name]
        except KeyError as exc:
            raise RegistryError(f"Unknown {kind.value} primitive: {name}") from exc

    def names(self, kind: PrimitiveKind) -> tuple[str, ...]:
        return tuple(sorted(self._items[kind]))


registry = PrimitiveRegistry()


def register_target(name: str, primitive: type[T]) -> type[T]:
    return registry.register(PrimitiveKind.TARGET, name, primitive)


def register_judge(name: str, primitive: type[T]) -> type[T]:
    return registry.register(PrimitiveKind.JUDGE, name, primitive)


def register_transform(name: str, primitive: type[T]) -> type[T]:
    return registry.register(PrimitiveKind.TRANSFORM, name, primitive)
