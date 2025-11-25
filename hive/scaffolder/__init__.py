"""Automagik Hive scaffolder - YAML-first agent/team/workflow creation.

This module provides tools for creating and validating AI components
from YAML configuration files.

12-year-old friendly: Build agents like filling out a form!
"""

from hive.scaffolder.generator import (
    ConfigGenerator,
    GeneratorError,
    generate_agent_from_yaml,
    generate_team_from_yaml,
    generate_workflow_from_yaml,
)
from hive.scaffolder.genie_mapper import (
    MODEL_CONVERSION_MAP,
    convert_genie_model_to_hive,
    map_genie_to_hive,
)
from hive.scaffolder.validator import (
    ConfigValidator,
    ValidationError,
    validate_yaml,
)

__all__ = [
    # Generator
    "ConfigGenerator",
    "GeneratorError",
    "generate_agent_from_yaml",
    "generate_team_from_yaml",
    "generate_workflow_from_yaml",
    # Validator
    "ConfigValidator",
    "ValidationError",
    "validate_yaml",
    # Genie Mapper
    "MODEL_CONVERSION_MAP",
    "convert_genie_model_to_hive",
    "map_genie_to_hive",
]
