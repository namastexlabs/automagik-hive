"""Utilities for constructing AgentOS configuration models."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from agno.os.config import AgentOSConfig
from pydantic import ValidationError

from lib.config.settings import HiveSettings
from lib.logging import logger

from .exceptions import AgentOSConfigError

MAX_QUICK_PROMPTS = 3


@dataclass(frozen=True)
class ComponentMetadata:
    """Metadata captured from agent, team, or workflow configs."""

    component_type: str
    identifier: str
    display_name: str
    model_ids: tuple[str, ...]


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CONFIG_PATH = Path(__file__).with_name("default_agentos.yaml")

_COMPONENT_SPECS: dict[str, dict[str, Any]] = {
    "agent": {
        "directory": _PROJECT_ROOT / "ai" / "agents",
        "section": "agent",
        "id_key": "agent_id",
        "name_key": "name",
    },
    "team": {
        "directory": _PROJECT_ROOT / "ai" / "teams",
        "section": "team",
        "id_key": "team_id",
        "name_key": "name",
    },
    "workflow": {
        "directory": _PROJECT_ROOT / "ai" / "workflows",
        "section": "workflow",
        "id_key": "workflow_id",
        "name_key": "name",
    },
}


def collect_component_metadata() -> list[ComponentMetadata]:
    """Return discovered AgentOS component metadata for agents, teams, and workflows."""

    return _collect_component_metadata()


def build_default_agentos_config(settings: HiveSettings | None = None) -> AgentOSConfig:
    """Build an ``AgentOSConfig`` instance populated with Automagik defaults."""

    active_settings = _resolve_settings(settings)

    base_payload = _load_default_payload()
    components = _collect_component_metadata()

    quick_prompts = _resolve_quick_prompts(
        base_payload.get("chat", {}).get("quick_prompts", {}),
        components,
    )

    payload: dict[str, Any] = dict(base_payload)

    payload["available_models"] = _resolve_available_models(
        base_payload.get("available_models", []),
        components,
        active_settings,
    )

    if quick_prompts:
        payload.setdefault("chat", {})
        payload["chat"]["quick_prompts"] = quick_prompts

    payload["session"] = _merge_domain_section(
        base_payload.get("session"),
        display_name="Sessions",
        db_ids=[active_settings.hive_agno_v2_sessions_table],
    )
    payload["memory"] = _merge_domain_section(
        base_payload.get("memory"),
        display_name="Memories",
        db_ids=[active_settings.hive_agno_v2_memories_table],
    )
    payload["metrics"] = _merge_domain_section(
        base_payload.get("metrics"),
        display_name="Metrics",
        db_ids=[active_settings.hive_agno_v2_metrics_table],
    )
    payload["knowledge"] = _merge_domain_section(
        base_payload.get("knowledge"),
        display_name="Knowledge Base",
        db_ids=[active_settings.hive_agno_v2_knowledge_table],
    )
    payload["evals"] = _merge_domain_section(
        base_payload.get("evals"),
        display_name="Evaluations",
        db_ids=[active_settings.hive_agno_v2_evals_table],
    )

    try:
        return AgentOSConfig.model_validate(payload)
    except ValidationError as exc:
        raise AgentOSConfigError("Generated AgentOS defaults failed validation") from exc


def _resolve_settings(settings: HiveSettings | None) -> HiveSettings:
    if settings is not None:
        return settings

    try:
        return HiveSettings()
    except ValidationError as exc:  # pragma: no cover - depends on runtime env
        raise AgentOSConfigError("HiveSettings validation failed while building AgentOS defaults") from exc


def _load_default_payload() -> dict[str, Any]:
    if _DEFAULT_CONFIG_PATH.exists():
        try:
            with _DEFAULT_CONFIG_PATH.open(encoding="utf-8") as handle:
                payload = yaml.safe_load(handle) or {}
                if isinstance(payload, dict):
                    return payload
                logger.warning(
                    "AgentOS default YAML did not return a mapping; ignoring contents",
                    path=str(_DEFAULT_CONFIG_PATH),
                )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Unable to load AgentOS default YAML, using empty payload",
                path=str(_DEFAULT_CONFIG_PATH),
                error=str(exc),
            )
    return {}


def _collect_component_metadata() -> list[ComponentMetadata]:
    components: list[ComponentMetadata] = []
    for component_type, spec in _COMPONENT_SPECS.items():
        directory: Path = spec["directory"]
        section: str = spec["section"]
        id_key: str = spec["id_key"]
        name_key: str = spec["name_key"]

        if not directory.exists():
            continue

        for config_path in directory.glob("*/config.yaml"):
            data = _safe_load_yaml(config_path)
            section_data = data.get(section, {}) if isinstance(data, dict) else {}
            identifier = section_data.get(id_key)
            if not isinstance(identifier, str) or not identifier:
                continue

            display_name = section_data.get(name_key) or _fallback_display_name(identifier)
            model_ids = _collect_model_ids(data)

            components.append(
                ComponentMetadata(
                    component_type=component_type,
                    identifier=identifier,
                    display_name=display_name,
                    model_ids=tuple(model_ids),
                )
            )

    return components


def _safe_load_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
            if isinstance(payload, dict):
                return payload
            logger.warning(
                "AgentOS metadata config is not a mapping",
                path=str(path),
            )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Unable to parse AgentOS metadata config", path=str(path), error=str(exc))
    return {}


def _collect_model_ids(data: dict[str, Any]) -> list[str]:
    candidates: list[str] = []

    def _extract_model(block: Any) -> None:
        if isinstance(block, dict):
            identifier = block.get("id")
            if isinstance(identifier, str):
                candidates.append(identifier)

    # Top-level model definitions
    _extract_model(data.get("model"))
    _extract_model(data.get("output_model"))

    # Nested definitions under primary section
    for section in ("agent", "team", "workflow"):
        section_block = data.get(section)
        if isinstance(section_block, dict):
            _extract_model(section_block.get("model"))
            _extract_model(section_block.get("output_model"))

    return _unique_preserving_order(candidates)


def _fallback_display_name(identifier: str) -> str:
    words = identifier.replace("_", " ").replace("-", " ").split()
    return " ".join(word.capitalize() for word in words) if words else identifier


def _resolve_quick_prompts(
    base_prompts: dict[str, list[str]] | None,
    components: list[ComponentMetadata],
) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}

    if isinstance(base_prompts, dict):
        for key, prompts in base_prompts.items():
            merged[key] = _normalize_prompts(prompts)

    for component in components:
        key = f"{component.component_type}:{component.identifier}"
        existing = merged.get(key, [])
        prompts = existing + _component_prompts(component)
        normalized = _normalize_prompts(prompts)
        if normalized:
            merged[key] = normalized

    return merged


def _component_prompts(component: ComponentMetadata) -> list[str]:
    display_name = component.display_name
    return [
        f"Summarize {display_name}'s current focus and responsibilities.",
        f"List three high-value actions {display_name} can take next.",
        f"Highlight recent wins achieved by {display_name}.",
    ]


def _normalize_prompts(prompts: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()

    for prompt in prompts:
        if not isinstance(prompt, str):
            continue
        cleaned = " ".join(prompt.strip().split())
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(cleaned)
        if len(normalized) == MAX_QUICK_PROMPTS:
            break

    return normalized


def _resolve_available_models(
    base_models: list[str] | None,
    components: list[ComponentMetadata],
    settings: HiveSettings,
) -> list[str]:
    models: list[str] = []

    if isinstance(base_models, list):
        models.extend(model for model in base_models if isinstance(model, str))

    models.append(settings.hive_default_model)

    for component in components:
        models.extend(component.model_ids)

    return _unique_preserving_order(models)


def _merge_domain_section(
    base_section: dict[str, Any] | None,
    *,
    display_name: str,
    db_ids: list[str],
) -> dict[str, Any]:
    section: dict[str, Any] = dict(base_section or {})
    section_display_name = section.get("display_name")
    if not isinstance(section_display_name, str) or not section_display_name.strip():
        section_display_name = display_name
        section["display_name"] = display_name

    section["dbs"] = [
        {
            "db_id": db_id,
            "domain_config": {"display_name": section_display_name},
        }
        for db_id in db_ids
        if isinstance(db_id, str) and db_id
    ]

    return section


def _unique_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique
