"""
AI Root Resolution System

Provides AI directory resolution with multi-level precedence handling, directory
structure validation, helper functions, and exception handling for TDD implementation.

Key functions:
- resolve_ai_root(): 4-level precedence logic for AI root resolution
- validate_ai_structure(): comprehensive directory validation with detailed report
- get_ai_subdirectory(): helper function for subdirectory access
- AIRootError: custom exception class for AI root validation errors

Precedence order for AI root resolution:
1. explicit_path (CLI argument) - highest priority
2. HIVE_AI_ROOT environment variable
3. settings.hive_ai_root attribute
4. Default to "ai" directory - lowest priority
"""

import os
from pathlib import Path
from typing import Any


class AIRootError(Exception):
    """Custom exception for AI root validation errors."""

    def __init__(self, message: str):
        """Initialize AIRootError with custom message.

        Args:
            message: Error message describing the validation failure
        """
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        """Return the error message as string representation."""
        return self.message


def resolve_ai_root(explicit_path: str | Path | None = None, settings: Any | None = None) -> Path:
    """
    Resolve AI root directory with 4-level precedence handling.

    Precedence order (highest to lowest):
    1. explicit_path (CLI argument)
    2. HIVE_AI_ROOT environment variable
    3. settings.hive_ai_root attribute
    4. Default to "ai" directory

    Args:
        explicit_path: Explicit path provided via CLI or direct call
        settings: Settings object that may contain hive_ai_root attribute

    Returns:
        Path: Absolute path to the resolved AI root directory

    Raises:
        AIRootError: If resolved path doesn't exist or isn't a directory
    """
    from lib.logging import logger

    logger.debug(
        "AI root resolution started",
        explicit_path=explicit_path,
        settings=settings,
    )

    resolved_path = None

    # Level 1: Explicit path (highest precedence) - treat empty string as None
    if explicit_path is not None and explicit_path != "":
        resolved_path = Path(explicit_path)
        logger.debug("AI root resolution", step="explicit_path", resolved_path=resolved_path)

    # Level 2: HIVE_AI_ROOT environment variable
    elif "HIVE_AI_ROOT" in os.environ:
        env_path = os.environ["HIVE_AI_ROOT"].strip()
        if env_path:  # Only use non-empty environment variables
            resolved_path = Path(env_path)
            logger.debug("AI root resolution", step="env_var", resolved_path=resolved_path)

    # Level 3: Settings object hive_ai_root attribute
    if resolved_path is None and settings is not None:
        if hasattr(settings, "hive_ai_root"):
            settings_path = settings.hive_ai_root
            if settings_path:
                resolved_path = Path(settings_path)
                logger.debug("AI root resolution", step="settings", resolved_path=resolved_path)

    # Level 4: Default to "ai" directory (lowest precedence)
    if resolved_path is None:
        resolved_path = Path("ai")
        logger.debug("AI root resolution", step="default", resolved_path=resolved_path)

    # Convert to absolute path only if validation passes
    absolute_path = resolved_path.resolve()
    logger.debug("AI root resolution", step="resolved", absolute_path=absolute_path)

    # Validate the resolved path
    if not absolute_path.exists():
        logger.error(
            "AI root validation failed",
            reason="path_missing",
            path=str(absolute_path),
        )
        raise AIRootError(f"AI root directory '{absolute_path}' does not exist")

    if not absolute_path.is_dir():
        logger.error(
            "AI root validation failed",
            reason="not_a_directory",
            path=str(absolute_path),
        )
        raise AIRootError(f"AI root '{absolute_path}' is not a directory")

    # Return original Path if it was relative "ai", otherwise absolute path
    if str(resolved_path) == "ai":
        logger.debug("AI root resolution complete", return_type="relative", resolved_path=resolved_path)
        return resolved_path
    else:
        logger.debug("AI root resolution complete", return_type="absolute", resolved_path=absolute_path)
        return absolute_path


def validate_ai_structure(ai_root: Path) -> dict[str, Any]:
    """
    Validate AI directory structure and return detailed validation report.

    Checks for required subdirectories (agents, teams, workflows) and optional
    subdirectories (tools, templates), providing comprehensive validation results.

    Args:
        ai_root: Path to the AI root directory to validate

    Returns:
        Dict containing detailed validation results:
        - valid: bool indicating overall validation status
        - ai_root: string path to the AI root
        - required_subdirs: dict mapping required subdirs to their existence
        - optional_subdirs: dict mapping optional subdirs to their existence
        - extra_subdirs: list of additional subdirectories found
        - missing_subdirs: list of missing required subdirectories
        - errors: list of error messages encountered

    Raises:
        AIRootError: If AI root doesn't exist, isn't a directory, or has permission issues
    """
    # Validate AI root exists and is a directory
    if not ai_root.exists():
        raise AIRootError(f"AI root directory '{ai_root}' does not exist")

    if not ai_root.is_dir():
        raise AIRootError(f"AI root '{ai_root}' is not a directory")

    # Check for permission issues by attempting to read a specific subdirectory
    try:
        all_items = list(ai_root.iterdir())
        # Check for permission issues on subdirectories
        for item in all_items:
            if item.is_dir() and item.name in ["agents", "teams", "workflows"]:
                try:
                    list(item.iterdir())
                except PermissionError as e:
                    raise AIRootError(f"Permission denied accessing subdirectory '{item.name}': {e}")
    except PermissionError as e:
        raise AIRootError(f"Permission denied accessing AI root directory: {e}")

    # Define required and optional subdirectories
    required_subdirs = ["agents", "teams", "workflows"]
    optional_subdirs = ["tools", "templates"]

    # Initialize validation results
    validation_result = {
        "valid": True,
        "ai_root": str(ai_root),
        "required_subdirs": {},
        "optional_subdirs": {},
        "missing_subdirs": [],
        "errors": [],
    }

    # Get all existing subdirectories
    existing_subdirs = [item.name for item in ai_root.iterdir() if item.is_dir()]

    # Check required subdirectories
    for subdir in required_subdirs:
        subdir_path = ai_root / subdir
        exists_and_is_dir = subdir_path.exists() and subdir_path.is_dir()
        validation_result["required_subdirs"][subdir] = exists_and_is_dir

        if not exists_and_is_dir:
            validation_result["valid"] = False
            validation_result["missing_subdirs"].append(subdir)
            validation_result["errors"].append(f"Required subdirectory '{subdir}' missing from AI root")

    # Check optional subdirectories
    for subdir in optional_subdirs:
        subdir_path = ai_root / subdir
        exists_and_is_dir = subdir_path.exists() and subdir_path.is_dir()
        validation_result["optional_subdirs"][subdir] = exists_and_is_dir

    # Find extra subdirectories and add to result if any exist
    known_subdirs = set(required_subdirs + optional_subdirs)
    extra_subdirs = [subdir for subdir in existing_subdirs if subdir not in known_subdirs]
    if extra_subdirs:
        validation_result["extra_subdirs"] = extra_subdirs

    return validation_result


def get_ai_subdirectory(ai_root: Path, subdirectory: str) -> Path:
    """
    Get a specific subdirectory within the AI root directory.

    Helper function to safely access AI subdirectories with validation
    and error handling.

    Args:
        ai_root: Path to the AI root directory
        subdirectory: Name of the subdirectory to retrieve

    Returns:
        Path: Absolute path to the requested subdirectory

    Raises:
        AIRootError: If AI root doesn't exist, subdirectory name is invalid,
                    or subdirectory doesn't exist
    """
    # Validate input types
    if not isinstance(subdirectory, str):
        raise AIRootError("Subdirectory name must be a string")

    # Validate AI root exists
    ai_root = ai_root.resolve()
    if not ai_root.exists():
        raise AIRootError(f"AI root directory '{ai_root}' does not exist")

    if not ai_root.is_dir():
        raise AIRootError(f"AI root '{ai_root}' is not a directory")

    # Validate subdirectory name
    valid_subdirs = ["agents", "teams", "workflows", "tools", "templates"]
    if subdirectory not in valid_subdirs:
        raise AIRootError(f"Invalid subdirectory '{subdirectory}' - must be one of: {', '.join(valid_subdirs)}")

    # Construct subdirectory path
    subdir_path = ai_root / subdirectory

    # Validate subdirectory exists
    if not subdir_path.exists():
        raise AIRootError(f"Subdirectory '{subdirectory}' does not exist in AI root '{ai_root}'")

    if not subdir_path.is_dir():
        raise AIRootError(f"Subdirectory '{subdirectory}' exists but is not a directory")

    return subdir_path.resolve()
