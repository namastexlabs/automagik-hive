from typing import Optional, Union
from lib.utils.version_factory import create_team
from .models import UserContext


def get_ana_team(
    user_context: Optional[Union[UserContext, dict]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    debug_mode: bool = False
) -> "Team":
    # Convert dict to UserContext if needed
    if isinstance(user_context, dict):
        user_context = UserContext(**user_context)
    
    # Create team using factory pattern
    team = create_team("ana", session_id=session_id, user_id=user_id, debug_mode=debug_mode)
    
    # Add team-specific user context
    if user_context:
        team.metadata = team.metadata or {}
        team.metadata["user_context"] = user_context
        for member in team.members:
            if hasattr(member, 'metadata'):
                member.metadata = member.metadata or {}
                member.metadata["pb_phone_number"] = user_context.pb_phone_number
                member.metadata["pb_cpf"] = user_context.pb_cpf
    
    return team