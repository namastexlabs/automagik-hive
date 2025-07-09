"""PagBank Teams Module - Specialist team implementations."""

from teams.base_team import BaseTeam, SpecialistTeam, TeamResponse
from teams.insurance_team import InsuranceTeam, create_insurance_team
from teams.team_config import TeamConfig, TeamConfigManager
from teams.team_prompts import TeamPrompts, team_prompts
from teams.team_tools import (
    TEAM_TOOLS,
    financial_calculator,
    get_team_tools,
    pagbank_validator,
    security_checker,
)

__all__ = [
    # Base classes
    "BaseTeam",
    "SpecialistTeam",
    "TeamResponse",
    
    # Specialist teams
    "InsuranceTeam",
    "create_insurance_team",
    
    # Configuration
    "TeamConfigManager",
    "TeamConfig",
    
    # Prompts
    "TeamPrompts",
    "team_prompts",
    
    # Tools
    "pagbank_validator",
    "security_checker",
    "financial_calculator",
    "get_team_tools",
    "TEAM_TOOLS"
]