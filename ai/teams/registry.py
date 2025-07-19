"""Team registry for dynamic loading of team instances."""

from typing import Dict, Callable, Optional, Any
from agno.team import Team
from pathlib import Path
import importlib.util


def _discover_teams() -> Dict[str, Callable[..., Team]]:
    """Dynamically discover teams from filesystem"""
    teams_dir = Path("ai/teams")
    registry = {}
    
    if not teams_dir.exists():
        return registry
    
    for team_path in teams_dir.iterdir():
        if not team_path.is_dir() or team_path.name.startswith('_'):
            continue
            
        config_file = team_path / "config.yaml"
        team_file = team_path / "team.py"
        
        if config_file.exists() and team_file.exists():
            team_name = team_path.name
            
            try:
                # Load the team module dynamically
                spec = importlib.util.spec_from_file_location(
                    f"ai.teams.{team_name}.team",
                    team_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for the factory function
                factory_func_name = f"get_{team_name.replace('-', '_')}_team"
                if hasattr(module, factory_func_name):
                    factory_func = getattr(module, factory_func_name)
                    registry[team_name] = factory_func
                    
            except Exception as e:
                print(f"⚠️ Failed to load team {team_name}: {e}")
                continue
    
    return registry


# Dynamic team registry - no hardcoded imports
TEAM_REGISTRY: Dict[str, Callable[..., Team]] = _discover_teams()


def get_team(team_id: str, version: Optional[int] = None, **kwargs) -> Team:
    """
    Retrieve and instantiate a team by its ID.
    
    Args:
        team_id: The unique identifier of the team
        version: Optional version number for the team
        **kwargs: Additional keyword arguments to pass to the team factory
        
    Returns:
        Team: The instantiated team
        
    Raises:
        ValueError: If the team_id is not found in the registry
    """
    # Refresh registry to pick up new teams
    global TEAM_REGISTRY
    TEAM_REGISTRY = _discover_teams()
    
    if team_id not in TEAM_REGISTRY:
        available_teams = ", ".join(sorted(TEAM_REGISTRY.keys()))
        raise ValueError(
            f"Team '{team_id}' not found in registry. "
            f"Available teams: {available_teams}"
        )
    
    # Get the factory function for the team
    team_factory = TEAM_REGISTRY[team_id]
    
    # Create and return the team instance
    # Pass version if provided, along with any other kwargs
    if version is not None:
        kwargs['version'] = version
        
    return team_factory(**kwargs)


def list_available_teams() -> list[str]:
    """
    List all available team IDs in the registry.
    
    Returns:
        list[str]: Sorted list of team IDs
    """
    # Refresh registry to pick up new teams
    global TEAM_REGISTRY
    TEAM_REGISTRY = _discover_teams()
    return sorted(TEAM_REGISTRY.keys())


def is_team_registered(team_id: str) -> bool:
    """
    Check if a team is registered.
    
    Args:
        team_id: The team ID to check
        
    Returns:
        bool: True if the team is registered, False otherwise
    """
    # Refresh registry to pick up new teams
    global TEAM_REGISTRY
    TEAM_REGISTRY = _discover_teams()
    return team_id in TEAM_REGISTRY