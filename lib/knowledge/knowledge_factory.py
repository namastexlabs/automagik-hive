"""Lazy knowledge factory shim for tests and compatibility."""

from __future__ import annotations

from importlib import import_module
from typing import Any


def _factory_module():
    return import_module("lib.knowledge.factories.knowledge_factory")


def get_knowledge_base(*args: Any, **kwargs: Any):
    return _factory_module().get_knowledge_base(*args, **kwargs)


def create_knowledge_base(*args: Any, **kwargs: Any):
    return _factory_module().create_knowledge_base(*args, **kwargs)


__all__ = ["create_knowledge_base", "get_knowledge_base"]
