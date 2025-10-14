"""Configuration loader for knowledge processing.

Utilities to load and validate processing configuration from YAML files and dictionaries.
Provides fallback to defaults and searches multiple config paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from lib.logging import logger

from .processing_config import ProcessingConfig


def find_config_file(
    filename: str = "knowledge_processing.yaml",
    search_paths: list[str] | None = None,
) -> str | None:
    """Find configuration file by searching multiple paths.

    Args:
        filename: Name of the configuration file to find
        search_paths: List of directory paths to search (searches in order)

    Returns:
        Path to the found config file, or None if not found
    """
    if search_paths is None:
        # Default search paths
        knowledge_config_dir = Path(__file__).parent
        project_root = knowledge_config_dir.parent.parent.parent
        search_paths = [
            str(knowledge_config_dir),  # lib/knowledge/config/
            str(project_root / "config"),  # config/ (project root)
            str(project_root),  # Project root
        ]

    for search_path in search_paths:
        config_path = Path(search_path) / filename
        if config_path.exists():
            return str(config_path)

    return None


def load_processing_config(config_path: str | None = None) -> ProcessingConfig:
    """Load processing configuration from YAML file.

    Args:
        config_path: Path to configuration file. If None, searches default locations.

    Returns:
        ProcessingConfig instance loaded from file or defaults
    """
    if config_path is None:
        config_path = find_config_file()

    if config_path is None or not Path(config_path).exists():
        logger.warning(
            "Configuration file not found, using defaults",
            config_path=config_path,
        )
        return ProcessingConfig()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        if config_data is None:
            logger.warning("Empty configuration file, using defaults", config_path=config_path)
            return ProcessingConfig()

        return load_processing_config_from_dict(config_data)

    except yaml.YAMLError as e:
        logger.error(
            "Failed to parse YAML configuration, using defaults",
            config_path=config_path,
            error=str(e),
        )
        return ProcessingConfig()

    except Exception as e:
        logger.error(
            "Unexpected error loading configuration, using defaults",
            config_path=config_path,
            error=str(e),
        )
        return ProcessingConfig()


def load_processing_config_from_dict(config_dict: dict[str, Any]) -> ProcessingConfig:
    """Load processing configuration from dictionary.

    Args:
        config_dict: Configuration dictionary (typically from YAML)

    Returns:
        ProcessingConfig instance

    Raises:
        ValidationError: If config_dict contains invalid values
    """
    try:
        return ProcessingConfig(**config_dict)
    except ValidationError:
        # Re-raise validation errors - caller should handle
        raise


__all__ = [
    "load_processing_config",
    "load_processing_config_from_dict",
    "find_config_file",
]
