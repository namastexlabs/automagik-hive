"""AI Root Path Resolution Utilities.

Provides centralized path resolution for AI folder locations,
supporting both internal (project-embedded) and external AI folders.
"""

import os
from pathlib import Path
from typing import Optional


class AIRootResolver:
    """Resolves AI folder paths with support for external locations."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize resolver with optional base path.

        Args:
            base_path: Base directory to search from. Defaults to current working directory.
        """
        self.base_path = base_path or Path.cwd()

    def find_ai_root(self, external_path: Optional[str] = None) -> Path:
        """Find the AI root directory.

        Priority order:
        1. Explicit external path if provided
        2. HIVE_AI_ROOT environment variable if set
        3. Internal ai/ directory in current project
        4. Search upwards for ai/ directory

        Args:
            external_path: Explicit path to external AI folder

        Returns:
            Path to AI root directory

        Raises:
            FileNotFoundError: If no AI directory can be found
        """
        # Priority 1: Explicit external path
        if external_path:
            ai_path = Path(external_path).resolve()
            if ai_path.is_dir():
                return ai_path
            else:
                raise FileNotFoundError(f"External AI path does not exist: {external_path}")

        # Priority 2: HIVE_AI_ROOT environment variable
        env_ai_root = os.getenv("HIVE_AI_ROOT")
        if env_ai_root:
            ai_path = Path(env_ai_root).resolve()
            if ai_path.is_dir():
                return ai_path
            else:
                # Log warning but continue to fallback
                import logging
                logging.warning(f"HIVE_AI_ROOT path does not exist: {env_ai_root}, falling back to default discovery")

        # Priority 3: Internal ai/ directory
        internal_ai = self.base_path / "ai"
        if internal_ai.is_dir():
            return internal_ai

        # Priority 4: Search upwards
        current = self.base_path
        for _ in range(10):  # Prevent infinite loops
            ai_dir = current / "ai"
            if ai_dir.is_dir():
                return ai_dir
            parent = current.parent
            if parent == current:  # Reached filesystem root
                break
            current = parent

        raise FileNotFoundError("Could not find AI directory (ai/) in current project or parent directories")

    def get_agents_path(self, external_path: Optional[str] = None) -> Path:
        """Get path to agents directory."""
        return self.find_ai_root(external_path) / "agents"

    def get_teams_path(self, external_path: Optional[str] = None) -> Path:
        """Get path to teams directory."""
        return self.find_ai_root(external_path) / "teams"

    def get_workflows_path(self, external_path: Optional[str] = None) -> Path:
        """Get path to workflows directory."""
        return self.find_ai_root(external_path) / "workflows"

    def get_tools_path(self, external_path: Optional[str] = None) -> Path:
        """Get path to tools directory."""
        return self.find_ai_root(external_path) / "tools"


# Global instance for convenience
ai_root = AIRootResolver()


def find_ai_root(external_path: Optional[str] = None) -> Path:
    """Convenience function to find AI root directory."""
    return ai_root.find_ai_root(external_path)


def get_agents_path(external_path: Optional[str] = None) -> Path:
    """Convenience function to get agents path."""
    return ai_root.get_agents_path(external_path)


def get_teams_path(external_path: Optional[str] = None) -> Path:
    """Convenience function to get teams path."""
    return ai_root.get_teams_path(external_path)


def get_workflows_path(external_path: Optional[str] = None) -> Path:
    """Convenience function to get workflows path."""
    return ai_root.get_workflows_path(external_path)


def get_tools_path(external_path: Optional[str] = None) -> Path:
    """Convenience function to get tools path."""
    return ai_root.get_tools_path(external_path)