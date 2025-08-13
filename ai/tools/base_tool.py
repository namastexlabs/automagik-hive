# Base Tool Class for Automagik Hive Tools
# Provides common functionality and interface for all tools

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from lib.logging import logger


class ToolConfig(BaseModel):
    """Configuration model for tool metadata"""

    tool_id: str = Field(..., description="Unique tool identifier")
    name: str = Field(..., description="Human-readable tool name")
    description: str = Field(..., description="Tool description and purpose")
    version: int = Field(default=1, description="Tool version number")
    category: str = Field(default="general", description="Tool category")
    tags: list[str] = Field(default_factory=list, description="Tool tags")
    dependencies: list[str] = Field(
        default_factory=list, description="Required dependencies"
    )
    enabled: bool = Field(default=True, description="Whether tool is enabled")

    # Integration settings
    integration: dict[str, Any] = Field(
        default_factory=dict, description="Integration configuration"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Tool-specific parameters"
    )


class BaseTool(ABC):
    """
    Base class for all Automagik Hive tools.

    Provides common functionality for tool registration, configuration management,
    and standardized tool interface patterns.
    """

    def __init__(self, config_path: Path | None = None, **kwargs):
        """
        Initialize base tool with configuration.

        Args:
            config_path: Path to tool configuration file
            **kwargs: Additional initialization parameters
        """
        self.config_path = config_path
        self.config: ToolConfig | None = None
        self._is_initialized = False

        # Load configuration if path provided
        if config_path:
            if not isinstance(config_path, Path):
                raise TypeError(f"config_path must be a Path object, got {type(config_path).__name__}")
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            self.load_config()

        # Initialize tool-specific setup
        self.initialize(**kwargs)

    def load_config(self) -> None:
        """Load tool configuration from YAML file"""
        if not self.config_path or not self.config_path.exists():
            logger.warning("Tool configuration file not found", path=self.config_path)
            return

        try:
            with open(self.config_path) as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                raise ValueError("Configuration file is empty or invalid")

            # Handle both nested 'tool:' structure and flat structure
            if "tool" in config_data:
                # Nested structure: use tool section
                tool_config = config_data["tool"]
            else:
                # Flat structure: check if it has required fields
                if "tool_id" in config_data or "name" in config_data:
                    tool_config = config_data
                else:
                    raise ValueError("Configuration must contain 'tool' section or valid tool fields")

            self.config = ToolConfig(**tool_config)

        except Exception as e:
            logger.error(
                "Failed to load tool configuration", path=self.config_path, error=str(e)
            )
            raise

    @abstractmethod
    def initialize(self, **kwargs) -> None:
        """
        Initialize tool-specific functionality.

        This method should be implemented by each tool to handle
        tool-specific initialization requirements.

        Args:
            **kwargs: Tool-specific initialization parameters
        """

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the main tool functionality.

        This method should be implemented by each tool to provide
        the core tool execution logic.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Tool execution result
        """

    @abstractmethod
    def validate_inputs(self, inputs: dict[str, Any]) -> bool:
        """
        Validate tool inputs.

        This method should be implemented by each tool to validate
        input parameters before execution.

        Args:
            inputs: Dictionary of input parameters to validate

        Returns:
            True if inputs are valid, False otherwise
        """

    def validate_config(self) -> bool:
        """
        Validate tool configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.config:
            logger.warning("No configuration loaded for tool")
            return False

        # Basic validation
        if not self.config.tool_id or not self.config.name:
            logger.warning("Tool missing required fields", config=self.config)
            return False

        return True

    def get_info(self) -> dict[str, Any]:
        """
        Get tool information dictionary.

        Returns:
            Dictionary containing tool metadata and status
        """
        if not self.config:
            return {"tool_id": "unknown", "name": "Unknown Tool", "status": "no_config"}

        return {
            "tool_id": self.config.tool_id,
            "name": self.config.name,
            "description": self.config.description,
            "version": self.config.version,
            "category": self.config.category,
            "tags": self.config.tags,
            "enabled": self.config.enabled,
            "status": "ready" if self._is_initialized else "not_initialized",
            "config_path": str(self.config_path) if self.config_path else None,
        }

    def is_enabled(self) -> bool:
        """Check if tool is enabled"""
        return self.config.enabled if self.config else False

    def get_dependencies(self) -> list[str]:
        """Get tool dependencies"""
        return self.config.dependencies if self.config else []

    def __repr__(self) -> str:
        """String representation of tool"""
        if self.config:
            return f"<{self.__class__.__name__}(tool_id='{self.config.tool_id}', version={self.config.version})>"
        return f"<{self.__class__.__name__}(no_config)>"
