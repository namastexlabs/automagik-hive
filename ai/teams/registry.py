"""Team registry for dynamic loading of team instances."""

from typing import Dict, Callable, Optional, Any, List
from agno.team import Team
from pathlib import Path
import importlib.util
import yaml
from lib.logging import logger


def _get_factory_function_patterns(team_name: str, config: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Generate factory function name patterns to try for team discovery.
    
    Args:
        team_name: The team directory name
        config: Optional team configuration containing factory settings
        
    Returns:
        List of factory function names to attempt, in order of preference
    """
    patterns = []
    
    # Check for custom factory pattern in config
    if config and 'factory' in config and 'function_name' in config['factory']:
        custom_name = config['factory']['function_name']
        # Support template variables
        if '{team_name}' in custom_name:
            patterns.append(custom_name.format(team_name=team_name))
        elif '{team_name_underscore}' in custom_name:
            patterns.append(custom_name.format(team_name_underscore=team_name.replace('-', '_')))
        else:
            patterns.append(custom_name)
    
    # Check for additional factory patterns in config
    if config and 'factory' in config and 'patterns' in config['factory']:
        for pattern in config['factory']['patterns']:
            if '{team_name}' in pattern:
                patterns.append(pattern.format(team_name=team_name))
            elif '{team_name_underscore}' in pattern:
                patterns.append(pattern.format(team_name_underscore=team_name.replace('-', '_')))
            else:
                patterns.append(pattern)
    
    # Default patterns (for backward compatibility)
    team_name_underscore = team_name.replace('-', '_')
    patterns.extend([
        f"get_{team_name_underscore}_team",  # Current default
        f"create_{team_name_underscore}_team",
        f"build_{team_name_underscore}_team",
        f"make_{team_name_underscore}_team",
        f"{team_name_underscore}_factory",
        f"get_{team_name}_team",  # Hyphen version
        f"create_{team_name}_team",
        "get_team",  # Generic fallback
        "create_team",
        "team_factory"
    ])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_patterns = []
    for pattern in patterns:
        if pattern not in seen:
            seen.add(pattern)
            unique_patterns.append(pattern)
    
    return unique_patterns


def _load_team_config(config_file: Path) -> Optional[Dict[str, Any]]:
    """
    Load team configuration from YAML file.
    
    Args:
        config_file: Path to the config.yaml file
        
    Returns:
        Dictionary containing configuration or None if load fails
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning("Failed to load team config", config_file=str(config_file), error=str(e))
        return None


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
                # Load team configuration for factory patterns
                config = _load_team_config(config_file)
                
                # Load the team module dynamically
                spec = importlib.util.spec_from_file_location(
                    f"ai.teams.{team_name}.team",
                    team_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Try factory function patterns
                factory_patterns = _get_factory_function_patterns(team_name, config)
                factory_func = None
                used_pattern = None
                
                for pattern in factory_patterns:
                    if hasattr(module, pattern):
                        factory_func = getattr(module, pattern)
                        used_pattern = pattern
                        logger.debug("Found factory function", team_name=team_name, pattern=used_pattern)
                        break
                
                if factory_func:
                    registry[team_name] = factory_func
                    logger.info(f"Registered team: {team_name}", factory=used_pattern)
                else:
                    attempted_patterns = ", ".join(factory_patterns[:5])  # Show first 5 attempts
                    logger.warning("No factory function found for team", 
                                 team_name=team_name, 
                                 attempted_patterns=attempted_patterns)
                    
            except Exception as e:
                logger.warning("Failed to load team", team_name=team_name, error=str(e))
                continue
    
    return registry


# Dynamic team registry - lazy initialization
_TEAM_REGISTRY: Optional[Dict[str, Callable[..., Team]]] = None


def get_team_registry() -> Dict[str, Callable[..., Team]]:
    """Get team registry with lazy initialization"""
    global _TEAM_REGISTRY
    if _TEAM_REGISTRY is None:
        logger.debug("Initializing team registry (lazy)")
        _TEAM_REGISTRY = _discover_teams()
        logger.info("Team registry initialized", team_count=len(_TEAM_REGISTRY), teams=list(_TEAM_REGISTRY.keys()))
    else:
        logger.debug("Using cached team registry", team_count=len(_TEAM_REGISTRY))
    return _TEAM_REGISTRY


async def get_team(team_id: str, version: Optional[int] = None, **kwargs) -> Team:
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
    # Get registry with lazy initialization
    registry = get_team_registry()
    
    if team_id not in registry:
        available_teams = ", ".join(sorted(registry.keys()))
        raise ValueError(
            f"Team '{team_id}' not found in registry. "
            f"Available teams: {available_teams}"
        )
    
    # Get the factory function for the team
    team_factory = registry[team_id]
    
    # Create and return the team instance
    # Pass version if provided, along with any other kwargs
    if version is not None:
        kwargs['version'] = version
        
    return await team_factory(**kwargs)


def list_available_teams() -> list[str]:
    """
    List all available team IDs in the registry.
    
    Returns:
        list[str]: Sorted list of team IDs
    """
    # Get registry with lazy initialization
    registry = get_team_registry()
    return sorted(registry.keys())


def is_team_registered(team_id: str) -> bool:
    """
    Check if a team is registered.
    
    Args:
        team_id: The team ID to check
        
    Returns:
        bool: True if the team is registered, False otherwise
    """
    # Get registry with lazy initialization
    registry = get_team_registry()
    return team_id in registry