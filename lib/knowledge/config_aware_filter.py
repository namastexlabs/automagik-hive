"""Helpers for configuration-driven knowledge filters."""

from __future__ import annotations

from typing import Any, Dict

from lib.logging import logger
from lib.utils.version_factory import load_global_knowledge_config as _load_config


def load_global_knowledge_config() -> dict[str, Any]:
    """Expose knowledge configuration loader for easy patching in tests."""

    return _load_config()


def get_business_unit_configuration() -> dict[str, Any]:
    """Return the business unit configuration block from the global settings."""

    config = load_global_knowledge_config()
    return config.get("business_units", {})


class ConfigAwareFilter:
    """Thin wrapper around BusinessUnitFilter for compatibility layers."""

    def __init__(self) -> None:
        from lib.knowledge.filters.business_unit_filter import BusinessUnitFilter

        self._delegate = BusinessUnitFilter()
        logger.debug(
            "Config aware filter initialized",
            business_units=len(self._delegate.business_units),
        )

    def detect_business_unit(self, text: str) -> str | None:
        return self._delegate.detect_business_unit_from_text(text)

    def get_search_params(self) -> Dict[str, Any]:
        return self._delegate.get_search_params()

    def get_performance_settings(self) -> Dict[str, Any]:
        return self._delegate.get_performance_settings()

    def list_business_units(self) -> Dict[str, str]:
        return self._delegate.list_business_units()


__all__ = [
    "ConfigAwareFilter",
    "get_business_unit_configuration",
    "load_global_knowledge_config",
]
