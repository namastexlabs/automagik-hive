"""AI Teams Package - Automatic discovery from filesystem"""

# Registry auto-discovers teams from ai/teams/ folders
# No manual imports needed - just use the registry functions

from .registry import (
    get_team,
    get_team_registry,
    is_team_registered,
    list_available_teams,
)

__all__ = [
    # Registry and factory functions
    "get_team_registry",
    "get_team",
    "list_available_teams",
    "is_team_registered",
]
