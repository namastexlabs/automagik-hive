"""YAML configuration validator with helpful error messages.

This module validates agent, team, workflow, and tool configurations
against their schemas. Provides clear, actionable error messages for
configuration issues.

12-year-old friendly: If this complains, it tells you EXACTLY what's wrong!
"""

import os
from typing import Any

import yaml


class ValidationError(Exception):
    """Configuration validation failed."""

    def __init__(self, message: str, field: str | None = None, value: Any = None):
        self.field = field
        self.value = value
        super().__init__(message)


class ConfigValidator:
    """Validates YAML configurations against schemas."""

    # Agent configuration schema - Complete Agno Agent parameters
    # Reference: https://docs.agno.com/reference/agents/agent
    AGENT_SCHEMA = {
        "agent": {
            "required": True,
            "type": dict,
            "fields": {
                "name": {"required": True, "type": str, "min_length": 1},
                "id": {"required": False, "type": str},
                "description": {"required": False, "type": str},
                "model": {"required": True, "type": str, "min_length": 1},
                "role": {"required": False, "type": str},  # Role when part of a team
            },
        },
        "instructions": {"required": True, "type": str, "min_length": 10},
        "tools": {"required": False, "type": list},
        "knowledge": {"required": False, "type": dict},
        "mcp_servers": {"required": False, "type": list},
        "storage": {"required": False, "type": dict},
        # Session/State management
        "session": {
            "required": False,
            "type": dict,
            "fields": {
                "user_id": {"required": False, "type": str},
                "session_id": {"required": False, "type": str},
                "session_state": {"required": False, "type": dict},
                "add_session_state_to_context": {"required": False, "type": bool},
                "enable_agentic_state": {"required": False, "type": bool},
                "overwrite_db_session_state": {"required": False, "type": bool},
                "cache_session": {"required": False, "type": bool},
            },
        },
        # Reasoning configuration
        "reasoning": {
            "required": False,
            "type": dict,
            "fields": {
                "enabled": {"required": False, "type": bool},
                "model": {"required": False, "type": str},
                "min_steps": {"required": False, "type": int},
                "max_steps": {"required": False, "type": int},
            },
        },
        # Memory configuration
        "memory": {
            "required": False,
            "type": dict,
            "fields": {
                "enable_agentic_memory": {"required": False, "type": bool},
                "enable_user_memories": {"required": False, "type": bool},
                "add_memories_to_context": {"required": False, "type": bool},
                "enable_session_summaries": {"required": False, "type": bool},
                "add_session_summary_to_context": {"required": False, "type": bool},
            },
        },
        # History configuration
        "history": {
            "required": False,
            "type": dict,
            "fields": {
                "add_history_to_context": {"required": False, "type": bool},
                "num_history_runs": {"required": False, "type": int},
                "num_history_messages": {"required": False, "type": int},
                "search_session_history": {"required": False, "type": bool},
                "num_history_sessions": {"required": False, "type": int},
                "read_chat_history": {"required": False, "type": bool},
                "read_tool_call_history": {"required": False, "type": bool},
            },
        },
        # Tool control
        "tool_control": {
            "required": False,
            "type": dict,
            "fields": {
                "tool_choice": {"required": False, "type": (str, dict)},
                "tool_call_limit": {"required": False, "type": int},
                "max_tool_calls_from_history": {"required": False, "type": int},
                "search_knowledge": {"required": False, "type": bool},
                "update_knowledge": {"required": False, "type": bool},
            },
        },
        # Context enrichment
        "context": {
            "required": False,
            "type": dict,
            "fields": {
                "add_name_to_context": {"required": False, "type": bool},
                "add_datetime_to_context": {"required": False, "type": bool},
                "add_location_to_context": {"required": False, "type": bool},
                "timezone_identifier": {"required": False, "type": str},
                "additional_context": {"required": False, "type": str},
                "expected_output": {"required": False, "type": str},
            },
        },
        # Output configuration
        "output": {
            "required": False,
            "type": dict,
            "fields": {
                "output_schema": {"required": False, "type": str},  # Pydantic model import path
                "input_schema": {"required": False, "type": str},  # Pydantic model import path
                "use_json_mode": {"required": False, "type": bool},
                "structured_outputs": {"required": False, "type": bool},
                "parse_response": {"required": False, "type": bool},
                "references_format": {"required": False, "type": str},  # "json" or "yaml"
                "save_response_to_file": {"required": False, "type": str},
            },
        },
        # Retry configuration
        "retry": {
            "required": False,
            "type": dict,
            "fields": {
                "retries": {"required": False, "type": int},
                "delay_between_retries": {"required": False, "type": int},
                "exponential_backoff": {"required": False, "type": bool},
            },
        },
        # Storage behavior
        "store": {
            "required": False,
            "type": dict,
            "fields": {
                "store_media": {"required": False, "type": bool},
                "store_tool_messages": {"required": False, "type": bool},
                "store_history_messages": {"required": False, "type": bool},
                "send_media_to_model": {"required": False, "type": bool},
            },
        },
        # Hooks (function import paths)
        "hooks": {
            "required": False,
            "type": dict,
            "fields": {
                "pre_hooks": {"required": False, "type": list},
                "post_hooks": {"required": False, "type": list},
                "tool_hooks": {"required": False, "type": list},
            },
        },
        # Streaming and events
        "streaming": {
            "required": False,
            "type": dict,
            "fields": {
                "stream": {"required": False, "type": bool},
                "stream_events": {"required": False, "type": bool},
                "store_events": {"required": False, "type": bool},
            },
        },
        # Legacy settings (for backward compatibility)
        "settings": {"required": False, "type": dict},
        # Metadata
        "metadata": {"required": False, "type": dict},
        # Dependencies
        "dependencies": {"required": False, "type": dict},
    }

    # Team configuration schema - Complete Agno Team parameters
    # Reference: https://docs.agno.com/reference/teams/team
    TEAM_SCHEMA = {
        "team": {
            "required": True,
            "type": dict,
            "fields": {
                "name": {"required": True, "type": str, "min_length": 1},
                "id": {"required": False, "type": str},
                "description": {"required": False, "type": str},
                "role": {"required": False, "type": str},  # Position in parent team
                "mode": {
                    "required": False,  # Made optional - can use behavior flags instead
                    "type": str,
                    "choices": ["default", "collaboration", "router", "passthrough"],
                },
            },
        },
        "members": {
            "required": True,
            "type": list,
            "min_length": 1,  # Changed from 2 - single member teams are valid
            "item_type": str,
        },
        "instructions": {"required": False, "type": str},  # Made optional
        "model": {"required": False, "type": str},
        "storage": {"required": False, "type": dict},
        # Team behavior flags
        "behavior": {
            "required": False,
            "type": dict,
            "fields": {
                "respond_directly": {"required": False, "type": bool},
                "delegate_to_all_members": {"required": False, "type": bool},
                "determine_input_for_members": {"required": False, "type": bool},
                "share_member_interactions": {"required": False, "type": bool},
                "get_member_information_tool": {"required": False, "type": bool},
                "add_member_tools_to_context": {"required": False, "type": bool},
            },
        },
        # Session/State management (same as Agent)
        "session": {
            "required": False,
            "type": dict,
            "fields": {
                "user_id": {"required": False, "type": str},
                "session_id": {"required": False, "type": str},
                "session_state": {"required": False, "type": dict},
                "add_session_state_to_context": {"required": False, "type": bool},
                "enable_agentic_state": {"required": False, "type": bool},
                "cache_session": {"required": False, "type": bool},
            },
        },
        # Reasoning configuration
        "reasoning": {
            "required": False,
            "type": dict,
            "fields": {
                "enabled": {"required": False, "type": bool},
                "model": {"required": False, "type": str},
                "min_steps": {"required": False, "type": int},
                "max_steps": {"required": False, "type": int},
            },
        },
        # Memory configuration
        "memory": {
            "required": False,
            "type": dict,
            "fields": {
                "enable_agentic_memory": {"required": False, "type": bool},
                "enable_user_memories": {"required": False, "type": bool},
                "add_memories_to_context": {"required": False, "type": bool},
                "enable_session_summaries": {"required": False, "type": bool},
            },
        },
        # History configuration
        "history": {
            "required": False,
            "type": dict,
            "fields": {
                "add_history_to_context": {"required": False, "type": bool},
                "num_history_runs": {"required": False, "type": int},
                "num_history_messages": {"required": False, "type": int},
                "add_team_history_to_members": {"required": False, "type": bool},
                "num_team_history_runs": {"required": False, "type": int},
                "search_session_history": {"required": False, "type": bool},
                "read_chat_history": {"required": False, "type": bool},
            },
        },
        # Context enrichment
        "context": {
            "required": False,
            "type": dict,
            "fields": {
                "add_name_to_context": {"required": False, "type": bool},
                "add_datetime_to_context": {"required": False, "type": bool},
                "add_location_to_context": {"required": False, "type": bool},
                "timezone_identifier": {"required": False, "type": str},
                "additional_context": {"required": False, "type": str},
                "expected_output": {"required": False, "type": str},
            },
        },
        # Tool control
        "tool_control": {
            "required": False,
            "type": dict,
            "fields": {
                "tool_choice": {"required": False, "type": (str, dict)},
                "tool_call_limit": {"required": False, "type": int},
                "search_knowledge": {"required": False, "type": bool},
                "update_knowledge": {"required": False, "type": bool},
            },
        },
        "tools": {"required": False, "type": list},
        "knowledge": {"required": False, "type": dict},
        # Output configuration
        "output": {
            "required": False,
            "type": dict,
            "fields": {
                "output_schema": {"required": False, "type": str},
                "input_schema": {"required": False, "type": str},
                "use_json_mode": {"required": False, "type": bool},
                "parse_response": {"required": False, "type": bool},
            },
        },
        # Retry configuration
        "retry": {
            "required": False,
            "type": dict,
            "fields": {
                "retries": {"required": False, "type": int},
                "delay_between_retries": {"required": False, "type": int},
                "exponential_backoff": {"required": False, "type": bool},
            },
        },
        # Streaming
        "streaming": {
            "required": False,
            "type": dict,
            "fields": {
                "stream": {"required": False, "type": bool},
                "stream_events": {"required": False, "type": bool},
                "stream_member_events": {"required": False, "type": bool},
                "store_events": {"required": False, "type": bool},
                "store_member_responses": {"required": False, "type": bool},
            },
        },
        # Hooks
        "hooks": {
            "required": False,
            "type": dict,
            "fields": {
                "pre_hooks": {"required": False, "type": list},
                "post_hooks": {"required": False, "type": list},
                "tool_hooks": {"required": False, "type": list},
            },
        },
        # Debug
        "debug": {
            "required": False,
            "type": dict,
            "fields": {
                "debug_mode": {"required": False, "type": bool},
                "debug_level": {"required": False, "type": int},
                "show_members_responses": {"required": False, "type": bool},
            },
        },
        # Legacy settings (backward compatibility)
        "settings": {"required": False, "type": dict},
        "metadata": {"required": False, "type": dict},
        "dependencies": {"required": False, "type": dict},
    }

    # Workflow configuration schema - Complete Agno Workflow parameters
    # Reference: https://docs.agno.com/reference/workflows/workflow
    WORKFLOW_SCHEMA = {
        "workflow": {
            "required": True,
            "type": dict,
            "fields": {
                "name": {"required": True, "type": str, "min_length": 1},
                "id": {"required": False, "type": str},
                "description": {"required": False, "type": str},
            },
        },
        "steps": {
            "required": True,
            "type": list,
            "min_length": 1,
            "item_type": dict,
        },
        "storage": {"required": False, "type": dict},
        # Session/State management
        "session": {
            "required": False,
            "type": dict,
            "fields": {
                "user_id": {"required": False, "type": str},
                "session_id": {"required": False, "type": str},
                "session_state": {"required": False, "type": dict},
                "cache_session": {"required": False, "type": bool},
            },
        },
        # History configuration
        "history": {
            "required": False,
            "type": dict,
            "fields": {
                "add_workflow_history_to_steps": {"required": False, "type": bool},
                "num_history_runs": {"required": False, "type": int},
            },
        },
        # Streaming
        "streaming": {
            "required": False,
            "type": dict,
            "fields": {
                "stream": {"required": False, "type": bool},
                "stream_events": {"required": False, "type": bool},
                "stream_executor_events": {"required": False, "type": bool},
                "store_events": {"required": False, "type": bool},
                "store_executor_outputs": {"required": False, "type": bool},
            },
        },
        # Output configuration
        "output": {
            "required": False,
            "type": dict,
            "fields": {
                "input_schema": {"required": False, "type": str},
            },
        },
        # Debug
        "debug": {
            "required": False,
            "type": dict,
            "fields": {
                "debug_mode": {"required": False, "type": bool},
            },
        },
        # Legacy settings (backward compatibility)
        "settings": {"required": False, "type": dict},
        "metadata": {"required": False, "type": dict},
    }

    # Tool configuration schema
    TOOL_SCHEMA = {
        "tool": {
            "required": True,
            "type": dict,
            "fields": {
                "name": {"required": True, "type": str, "min_length": 1},
                "description": {"required": True, "type": str, "min_length": 10},
                "category": {"required": False, "type": str},
            },
        },
        "implementation": {
            "required": True,
            "type": dict,
            "fields": {
                "import_path": {"required": True, "type": str},
                "class_name": {"required": True, "type": str},
            },
        },
        "parameters": {"required": False, "type": dict},
        "schema": {"required": True, "type": dict},
        "error_handling": {"required": False, "type": dict},
        "settings": {"required": False, "type": dict},
    }

    # Genie agent configuration schema
    GENIE_AGENT_SCHEMA = {
        "name": {"required": True, "type": str, "min_length": 1},
        "description": {"required": False, "type": str},  # Optional field
        "genie": {
            "required": False,
            "type": dict,
            "fields": {
                "executor": {"required": False, "type": (str, list)},
                "background": {"required": False, "type": bool},
                "variant": {"required": False, "type": str},
                "permissionMode": {"required": False, "type": str},
            },
        },
        "forge": {"required": False, "type": dict},
    }

    @classmethod
    def validate_agent(cls, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate agent configuration.

        Args:
            config: Agent configuration dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        return cls._validate_config(config, cls.AGENT_SCHEMA, "agent")

    @classmethod
    def validate_team(cls, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate team configuration.

        Args:
            config: Team configuration dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        return cls._validate_config(config, cls.TEAM_SCHEMA, "team")

    @classmethod
    def validate_workflow(cls, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate workflow configuration.

        Args:
            config: Workflow configuration dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        return cls._validate_config(config, cls.WORKFLOW_SCHEMA, "workflow")

    @classmethod
    def validate_tool(cls, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate tool configuration.

        Args:
            config: Tool configuration dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        return cls._validate_config(config, cls.TOOL_SCHEMA, "tool")

    @classmethod
    def validate_genie_agent(cls, config: dict[str, Any]) -> bool:
        """Validate Genie agent frontmatter against schema.

        Args:
            config: Parsed Genie frontmatter YAML

        Returns:
            True if valid, raises ValueError if invalid

        Raises:
            ValueError: If configuration is invalid, with clear error message
        """
        errors = []

        # Check required fields
        if "name" not in config:
            errors.append("Missing required field: 'name'")
        elif not isinstance(config["name"], str):
            errors.append(f"Field 'name' must be a string, got {type(config['name']).__name__}")
        elif len(config["name"]) == 0:
            errors.append("Field 'name' cannot be empty")

        # Description is optional, but validate type if present
        if "description" in config:
            if not isinstance(config["description"], str):
                errors.append(f"Field 'description' must be a string, got {type(config['description']).__name__}")

        # Validate optional genie section
        if "genie" in config:
            if not isinstance(config["genie"], dict):
                errors.append(f"Field 'genie' must be a dict, got {type(config['genie']).__name__}")
            else:
                genie = config["genie"]

                # Validate executor (can be str or list)
                if "executor" in genie:
                    if not isinstance(genie["executor"], (str, list)):
                        errors.append(
                            f"Field 'genie.executor' must be a string or list, got {type(genie['executor']).__name__}"
                        )
                    elif isinstance(genie["executor"], list):
                        for i, item in enumerate(genie["executor"]):
                            if not isinstance(item, str):
                                errors.append(
                                    f"Field 'genie.executor[{i}]' must be a string, got {type(item).__name__}"
                                )

                # Validate background (must be bool)
                if "background" in genie:
                    if not isinstance(genie["background"], bool):
                        errors.append(
                            f"Field 'genie.background' must be a boolean, got {type(genie['background']).__name__}"
                        )

                # Validate variant (must be str)
                if "variant" in genie:
                    if not isinstance(genie["variant"], str):
                        errors.append(f"Field 'genie.variant' must be a string, got {type(genie['variant']).__name__}")

                # Validate permissionMode (must be str)
                if "permissionMode" in genie:
                    if not isinstance(genie["permissionMode"], str):
                        errors.append(
                            f"Field 'genie.permissionMode' must be a string, got {type(genie['permissionMode']).__name__}"
                        )

        # Validate optional forge section
        if "forge" in config:
            if not isinstance(config["forge"], dict):
                errors.append(f"Field 'forge' must be a dict, got {type(config['forge']).__name__}")

        # Raise ValueError if any errors found
        if errors:
            error_msg = "Genie agent validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
            raise ValueError(error_msg)

        return True

    @classmethod
    def validate_file(cls, file_path: str) -> tuple[bool, list[str]]:
        """Validate a YAML configuration file.

        Args:
            file_path: Path to YAML file

        Returns:
            Tuple of (is_valid, error_messages)
        """

        # Check file exists
        if not os.path.exists(file_path):
            return False, [f"❌ File not found: {file_path}"]

        # Try to load YAML
        try:
            with open(file_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return False, [f"❌ Invalid YAML syntax: {e}"]
        except Exception as e:
            return False, [f"❌ Failed to read file: {e}"]

        # Detect config type and validate
        config_type = cls._detect_config_type(config)
        if not config_type:
            return False, ["❌ Unknown configuration type. Expected: agent, team, workflow, or tool"]

        # Validate based on type
        if config_type == "agent":
            return cls.validate_agent(config)
        elif config_type == "team":
            return cls.validate_team(config)
        elif config_type == "workflow":
            return cls.validate_workflow(config)
        elif config_type == "tool":
            return cls.validate_tool(config)

        return False, ["❌ Configuration type detection failed"]

    @classmethod
    def _detect_config_type(cls, config: dict[str, Any]) -> str | None:
        """Detect configuration type from structure.

        Args:
            config: Configuration dictionary

        Returns:
            Config type: 'agent', 'team', 'workflow', 'tool', or None
        """
        if "agent" in config and "instructions" in config:
            return "agent"
        elif "team" in config and "members" in config:
            return "team"
        elif "workflow" in config and "steps" in config:
            return "workflow"
        elif "tool" in config and "implementation" in config:
            return "tool"
        return None

    @classmethod
    def _validate_config(
        cls, config: dict[str, Any], schema: dict[str, Any], config_type: str
    ) -> tuple[bool, list[str]]:
        """Validate configuration against schema.

        Args:
            config: Configuration dictionary
            schema: Schema to validate against
            config_type: Type of configuration (for error messages)

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        for field, rules in schema.items():
            # Check required fields
            if rules.get("required") and field not in config:
                errors.append(f"❌ Missing required field: '{field}'\n   💡 Add this to your {config_type}.yaml file")
                continue

            # Skip if field not present and not required
            if field not in config:
                continue

            value = config[field]

            # Type validation
            expected_type = rules.get("type")
            if expected_type and not isinstance(value, expected_type):
                errors.append(
                    f"❌ Field '{field}' has wrong type\n"
                    f"   Expected: {expected_type.__name__}\n"
                    f"   Got: {type(value).__name__}\n"
                    f"   Value: {value}"
                )
                continue

            # String length validation
            if isinstance(value, str):
                min_length = rules.get("min_length")
                if min_length and len(value) < min_length:
                    errors.append(
                        f"❌ Field '{field}' is too short\n"
                        f"   Minimum length: {min_length} characters\n"
                        f"   Current length: {len(value)} characters\n"
                        f"   💡 Add more descriptive content"
                    )

            # List length validation
            if isinstance(value, list):
                min_length = rules.get("min_length")
                if min_length and len(value) < min_length:
                    errors.append(
                        f"❌ Field '{field}' needs more items\n"
                        f"   Minimum items: {min_length}\n"
                        f"   Current items: {len(value)}\n"
                        f"   💡 Add at least {min_length - len(value)} more"
                    )

                # List item type validation
                item_type = rules.get("item_type")
                if item_type:
                    for i, item in enumerate(value):
                        if not isinstance(item, item_type):
                            errors.append(
                                f"❌ Item {i} in '{field}' has wrong type\n"
                                f"   Expected: {item_type.__name__}\n"
                                f"   Got: {type(item).__name__}"
                            )

            # Choice validation
            choices = rules.get("choices")
            if choices and value not in choices:
                errors.append(
                    f"❌ Field '{field}' has invalid value\n"
                    f"   Value: '{value}'\n"
                    f"   Valid choices: {', '.join(choices)}\n"
                    f"   💡 Pick one of the valid options"
                )

            # Nested field validation (for dict types)
            if isinstance(value, dict) and "fields" in rules:
                nested_errors = cls._validate_nested_fields(value, rules["fields"], field)
                errors.extend(nested_errors)

        # Environment variable validation (warnings only, don't block validation)
        # These are informational - runtime agents may use variables passed by orchestrator
        # env_warnings = cls._validate_env_vars(config)
        # Note: Removed from errors - env vars are handled at runtime, not validation time

        return len(errors) == 0, errors

    @classmethod
    def _validate_nested_fields(cls, config: dict[str, Any], schema: dict[str, Any], parent_field: str) -> list[str]:
        """Validate nested dictionary fields.

        Args:
            config: Configuration dictionary
            schema: Schema for nested fields
            parent_field: Parent field name (for error messages)

        Returns:
            List of error messages
        """
        errors = []

        for field, rules in schema.items():
            full_field = f"{parent_field}.{field}"

            # Check required nested fields
            if rules.get("required") and field not in config:
                errors.append(
                    f"❌ Missing required nested field: '{full_field}'\n   💡 Add this under '{parent_field}' section"
                )
                continue

            # Skip if not present and not required
            if field not in config:
                continue

            value = config[field]

            # Type validation for nested fields
            expected_type = rules.get("type")
            if expected_type and not isinstance(value, expected_type):
                errors.append(
                    f"❌ Nested field '{full_field}' has wrong type\n"
                    f"   Expected: {expected_type.__name__}\n"
                    f"   Got: {type(value).__name__}"
                )

            # Choice validation for nested fields
            choices = rules.get("choices")
            if choices and value not in choices:
                errors.append(
                    f"❌ Nested field '{full_field}' has invalid value\n"
                    f"   Value: '{value}'\n"
                    f"   Valid choices: {', '.join(choices)}"
                )

        return errors

    @classmethod
    def _validate_env_vars(cls, config: dict[str, Any]) -> list[str]:
        """Validate that referenced environment variables exist.

        Args:
            config: Configuration dictionary

        Returns:
            List of warning messages for missing env vars
        """
        warnings = []
        env_vars = cls._extract_env_vars(config)

        for var in env_vars:
            if not os.getenv(var):
                warnings.append(f"⚠️  Environment variable not set: {var}\n   💡 Add this to your .env file")

        return warnings

    @classmethod
    def _extract_env_vars(cls, obj: Any, vars_set: set | None = None) -> set:
        """Recursively extract ${VAR} references from config.

        Args:
            obj: Configuration object (dict, list, str, etc.)
            vars_set: Set to accumulate found variables

        Returns:
            Set of environment variable names
        """
        if vars_set is None:
            vars_set = set()

        if isinstance(obj, dict):
            for value in obj.values():
                cls._extract_env_vars(value, vars_set)
        elif isinstance(obj, list):
            for item in obj:
                cls._extract_env_vars(item, vars_set)
        elif isinstance(obj, str):
            # Extract ${VAR_NAME} patterns
            import re

            matches = re.findall(r"\$\{(\w+)\}", obj)
            vars_set.update(matches)

        return vars_set


def validate_yaml(file_path: str, verbose: bool = True) -> bool:
    """Validate a YAML configuration file.

    Args:
        file_path: Path to YAML file
        verbose: Print validation results

    Returns:
        True if valid, False otherwise
    """
    is_valid, messages = ConfigValidator.validate_file(file_path)

    if verbose:
        if is_valid:
            print(f"✅ {file_path} is valid!")
        else:
            print(f"\n❌ Validation failed for {file_path}\n")
            for msg in messages:
                print(f"{msg}\n")

    return is_valid
