"""Lazy knowledge factory shim for tests and compatibility."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Protocol


class _FactoryModule(Protocol):
    def get_knowledge_base(self, *args: Any, **kwargs: Any) -> Any: ...
    def create_knowledge_base(self, *args: Any, **kwargs: Any) -> Any: ...


def _factory_module() -> _FactoryModule:
    return import_module("lib.knowledge.factories.knowledge_factory")  # type: ignore[return-value]


def get_knowledge_base(*args: Any, **kwargs: Any) -> Any:
    return _factory_module().get_knowledge_base(*args, **kwargs)


def create_knowledge_base(*args: Any, **kwargs: Any) -> Any:
    return _factory_module().create_knowledge_base(*args, **kwargs)


__all__ = ["create_knowledge_base", "get_knowledge_base"]
