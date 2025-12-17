"""Genie to Hive configuration mapper.

This module converts Genie agent frontmatter format to Hive-compatible
agent configuration. Handles model name conversion and field mapping
from Genie schema to Hive AGENT_SCHEMA structure.

12-year-old friendly: Translates Genie agent files into Hive's language!
"""

from typing import Any

# Model name conversion table: Genie -> Hive
MODEL_CONVERSION_MAP = {
    # Anthropic models (primary)
    "sonnet": "anthropic:claude-sonnet-4-20250514",
    "opus": "anthropic:claude-opus-4-20250514",
    "haiku": "anthropic:claude-haiku-3-5-20241022",
    # OpenAI models
    "gpt-4o": "openai:gpt-4o",
    "gpt-4o-mini": "openai:gpt-4o-mini",
}


def convert_genie_model_to_hive(model_name: str) -> str:
    """Convert Genie model name to Hive model identifier.

    Args:
        model_name: Genie model name (e.g., "sonnet", "opus", "haiku")
                   or already-formatted Hive model (e.g., "openai:gpt-4o-mini")

    Returns:
        Hive model identifier (e.g., "anthropic:claude-sonnet-4-20250514")
        Falls back to "openai:gpt-4o-mini" for unknown models.

    Examples:
        >>> convert_genie_model_to_hive("sonnet")
        'anthropic:claude-sonnet-4-20250514'
        >>> convert_genie_model_to_hive("openai:gpt-4o-mini")
        'openai:gpt-4o-mini'
        >>> convert_genie_model_to_hive("unknown-model")
        'openai:gpt-4o-mini'
    """
    # If model is already in Hive format (provider:model), pass through
    if ":" in model_name:
        return model_name
    return MODEL_CONVERSION_MAP.get(model_name, "openai:gpt-4o-mini")


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

    # Get model: check top-level first (Hive format), then forge config (Genie format)
    if "model" in genie_config:
        # Top-level model field (Hive format or short name)
        genie_model = genie_config["model"]
    else:
        # Fallback to forge section (Genie format)
        executor_config = forge_section.get(primary_executor, {})
        genie_model = executor_config.get("model", "gpt-4o-mini")
    hive_model = convert_genie_model_to_hive(genie_model)

    # Build Hive configuration structure
    hive_config: dict[str, Any] = {
        "agent": {
            "name": genie_config.get("name", "unnamed-agent"),
            "id": genie_config.get("id", genie_config.get("name", "unnamed-agent")),
            "description": genie_config.get("description", ""),
            "model": hive_model,
        },
        "instructions": markdown_content,
        "tools": genie_config.get("tools", []),  # Pass through tools from frontmatter
    }

    # Pass through storage configuration if present
    if "storage" in genie_config:
        hive_config["storage"] = genie_config["storage"]

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
