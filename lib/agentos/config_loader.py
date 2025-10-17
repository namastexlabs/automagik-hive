"""YAML loader utilities for AgentOS configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from agno.os.config import AgentOSConfig
from pydantic import ValidationError

from lib.config.settings import HiveSettings
from lib.logging import logger

from .config_models import build_default_agentos_config
from .exceptions import AgentOSConfigError


def load_agentos_config(
    config_path: str | Path | None = None,
    *,
    overrides: dict[str, Any] | None = None,
    settings: HiveSettings | None = None,
) -> AgentOSConfig:
    """Load an ``AgentOSConfig`` from YAML with Automagik defaults."""

    active_settings = _initialise_settings(settings, config_path)
    resolved_path = _resolve_candidate_path(config_path, active_settings)

    config: AgentOSConfig | None = None

    if resolved_path is not None:
        if resolved_path.exists():
            config = _load_from_file(resolved_path)
        else:
            message = f"AgentOS configuration file not found at {resolved_path}"
            if active_settings and not active_settings.hive_agentos_enable_defaults:
                raise AgentOSConfigError(message + " and defaults are disabled")
            logger.warning(message + ", falling back to built-in defaults")

    if config is None:
        if active_settings is None:
            raise AgentOSConfigError("HiveSettings validation failed; cannot build AgentOS defaults")
        config = build_default_agentos_config(settings=active_settings)

    if overrides:
        try:
            config = config.model_copy(update=overrides)
        except ValidationError as exc:
            raise AgentOSConfigError("Overrides could not be applied to AgentOS configuration") from exc

    return config


def _initialise_settings(
    settings: HiveSettings | None,
    config_path: str | Path | None,
) -> HiveSettings | None:
    if settings is not None:
        return settings

    try:
        return HiveSettings()
    except ValidationError:
        if config_path is None:
            return None
        return None


def _resolve_candidate_path(
    config_path: str | Path | None,
    settings: HiveSettings | None,
) -> Path | None:
    candidate = config_path
    if candidate is None and settings is not None:
        candidate = settings.hive_agentos_config_path

    if candidate is None:
        return None

    path = Path(candidate)
    if not path.is_absolute():
        base = settings.project_root if settings is not None else Path.cwd()
        path = (base / path).resolve()

    return path


def _load_from_file(path: Path) -> AgentOSConfig:
    try:
        with path.open(encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
    except Exception as exc:  # pragma: no cover - defensive logging
        raise AgentOSConfigError(f"Unable to load AgentOS configuration from {path}: {exc}") from exc

    try:
        return AgentOSConfig.model_validate(payload)
    except ValidationError as exc:
        raise AgentOSConfigError(f"AgentOS configuration at {path} failed validation") from exc
