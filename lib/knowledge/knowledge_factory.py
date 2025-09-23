"""Lazy knowledge factory shim for tests and compatibility."""

from __future__ import annotations

from importlib import import_module
from typing import Any


def get_knowledge_base(*args: Any, **kwargs: Any):
    module = import_module("lib.knowledge.factories.knowledge_factory")
    return module.get_knowledge_base(*args, **kwargs)


__all__ = ["get_knowledge_base"]
