"""Genie to Hive configuration mapper.

This module converts Genie agent frontmatter format to Hive-compatible
agent configuration. Handles model name conversion and field mapping
from Genie schema to Hive AGENT_SCHEMA structure.

12-year-old friendly: Translates Genie agent files into Hive's language!
"""

from typing import Any


# Model name conversion table: Genie -> Hive
# NOTE: Using OpenAI gpt-4o-mini as default (cost-effective)
MODEL_CONVERSION_MAP = {
    # Anthropic aliases -> OpenAI equivalents
    "sonnet": "openai:gpt-4o-mini",
    "opus": "openai:gpt-4o-mini",
    "haiku": "openai:gpt-4o-mini",
    # OpenAI models
    "gpt-5-codex": "openai:gpt-4o-mini",
    "gpt-4o": "openai:gpt-4o",
    "gpt-4o-mini": "openai:gpt-4o-mini",
    "opencode/glm-4.6": "openai:gpt-4o-mini",  # fallback
}


def convert_genie_model_to_hive(model_name: str) -> str:
    """Convert Genie model name to Hive model identifier.

    Args:
        model_name: Genie model name (e.g., "sonnet", "opus", "haiku")

    Returns:
        Hive model identifier (e.g., "anthropic:claude-sonnet-4-20250514")
        Falls back to "openai:gpt-4o" for unknown models.

    Examples:
        >>> convert_genie_model_to_hive("sonnet")
        'anthropic:claude-sonnet-4-20250514'
        >>> convert_genie_model_to_hive("unknown-model")
        'openai:gpt-4o'
    """
    return MODEL_CONVERSION_MAP.get(model_name, "openai:gpt-4o")


def map_genie_to_hive(genie_config: dict[str, Any], markdown_content: str) -> dict[str, Any]:
    """Convert Genie frontmatter configuration to Hive agent configuration.

    Args:
        genie_config: Parsed Genie frontmatter (YAML dict)
        markdown_content: Markdown content below frontmatter (agent instructions)

    Returns:
        Hive-compatible agent configuration dictionary matching AGENT_SCHEMA

    Field Mapping:
        - name -> agent.name
        - name -> agent.id (by default)
        - description -> agent.description
        - genie.executor -> agent.executor_chain (list, lowercase)
        - forge.<exec>.model -> agent.model (converted via convert_genie_model_to_hive)
        - markdown_content -> instructions
        - genie.background -> settings.background (if present)
        - forge.*.dangerously_skip_permissions -> settings.skip_permissions (if present)

    Examples:
        >>> genie_config = {
        ...     "name": "fix",
        ...     "description": "Apply fixes",
        ...     "genie": {"executor": ["CLAUDE_CODE"]},
        ...     "forge": {"CLAUDE_CODE": {"model": "sonnet"}}
        ... }
        >>> result = map_genie_to_hive(genie_config, "Fix agent instructions")
        >>> result["agent"]["name"]
        'fix'
        >>> result["agent"]["model"]
        'anthropic:claude-sonnet-4-20250514'
    """
    # Extract Genie sections (with defaults)
    genie_section = genie_config.get("genie", {})
    forge_section = genie_config.get("forge", {})

    # Determine primary executor (first in list, default to CLAUDE_CODE)
    executor_raw = genie_section.get("executor", "CLAUDE_CODE")
    if isinstance(executor_raw, list):
        primary_executor = executor_raw[0] if executor_raw else "CLAUDE_CODE"
        executor_chain = [e.lower() for e in executor_raw]
    else:
        primary_executor = executor_raw
        executor_chain = [executor_raw.lower()]

    # Get model from forge config (default to "sonnet")
    executor_config = forge_section.get(primary_executor, {})
    genie_model = executor_config.get("model", "sonnet")
    hive_model = convert_genie_model_to_hive(genie_model)

    # Build Hive configuration structure
    # Note: Genie agents don't need storage by default (they're orchestrated via CLI)
    # Storage can be enabled per-agent in frontmatter if needed
    hive_config: dict[str, Any] = {
        "agent": {
            "name": genie_config.get("name", "unnamed-agent"),
            "id": genie_config.get("name", "unnamed-agent"),
            "description": genie_config.get("description", ""),
            "model": hive_model,
        },
        "instructions": markdown_content,
        "tools": [],  # Genie doesn't specify tools
    }

    # Add executor_chain if present
    if executor_chain:
        hive_config["agent"]["executor_chain"] = executor_chain

    # Build optional settings section
    settings = {}

    # Add background flag if present
    if "background" in genie_section:
        settings["background"] = genie_section["background"]

    # Check for dangerously_skip_permissions in any forge executor
    skip_permissions = False
    for executor_config in forge_section.values():
        if isinstance(executor_config, dict) and executor_config.get("dangerously_skip_permissions"):
            skip_permissions = True
            break

    if skip_permissions:
        settings["skip_permissions"] = True

    # Add settings section if non-empty
    if settings:
        hive_config["settings"] = settings

    return hive_config
