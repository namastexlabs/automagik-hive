"""Agente Entrevistador — Generic interviewer agent created from YAML configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agno.agent import Agent


def get_agente_entrevistador(**runtime_kwargs: Any):
    """Return Agente Entrevistador instantiated via YAML."""

    config_path = Path(__file__).with_name("config.yaml")
    return Agent.from_yaml(config_path, **runtime_kwargs)


__all__ = ["get_agente_entrevistador"]
