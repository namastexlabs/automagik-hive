"""AI root resolution utilities for Automagik Hive.

This module provides centralized AI root path resolution functionality.
"""

import os
from pathlib import Path
from typing import Optional, Union

from lib.config.settings import HiveSettings


def resolve_ai_root(
    explicit_path: Optional[Union[str, Path]] = None,
    settings: Optional[HiveSettings] = None
) -> Path:
    """
    Resolve the AI root directory path with proper precedence.

    Precedence order:
    1. Explicit path argument
    2. HIVE_AI_ROOT environment variable
    3. Settings default (settings.hive_ai_root)

    Args:
        explicit_path: Explicit path to AI root directory
        settings: HiveSettings instance for configuration

    Returns:
        Path to the resolved AI root directory

    Raises:
        FileNotFoundError: If the resolved path doesn't exist
        ValueError: If the resolved path doesn't contain required subdirectories
    """
    # Priority 1: Explicit path argument
    if explicit_path is not None:
        ai_root = Path(explicit_path).resolve()
    else:
        # Priority 2: HIVE_AI_ROOT environment variable
        env_ai_root = os.getenv("HIVE_AI_ROOT")
        if env_ai_root:
            ai_root = Path(env_ai_root).resolve()
        else:
            # Priority 3: Settings default
            if settings is None:
                raise ValueError("Settings must be provided when no explicit path or HIVE_AI_ROOT is set")

            default_ai_root = settings.hive_ai_root
            # Resolve relative to current working directory
            ai_root = Path.cwd() / default_ai_root

    # Validate the resolved path exists
    if not ai_root.exists():
        raise FileNotFoundError(f"AI root directory does not exist: {ai_root}")

    # Validate required subdirectories exist
    required_dirs = ["agents", "teams", "workflows"]
    missing_dirs = []

    for dir_name in required_dirs:
        if not (ai_root / dir_name).exists():
            missing_dirs.append(dir_name)

    if missing_dirs:
        raise ValueError(
            f"AI root directory must contain the following subdirectories: {', '.join(required_dirs)}. "
            f"Missing: {', '.join(missing_dirs)}"
        )

    return ai_root