
from __future__ import annotations

from typing import TYPE_CHECKING

from lib.utils.version_factory import create_team

if TYPE_CHECKING:
    from agno.team import Team


async def get_code_development_team(
    session_id: str | None = None,
    user_id: str | None = None,
    debug_mode: bool = False,
) -> Team:
    """
    Create code development team using factory pattern.

    Provides comprehensive software development capabilities through
    coordinated multi-agent collaboration including project onboarding,
    code analysis, file operations, and intelligent code modifications.

    Args:
        session_id: Session ID for conversation tracking
        user_id: User ID for team context
        debug_mode: Enable debug mode

    Returns:
        Configured team instance
    """
    # Create team using factory pattern
    team = await create_team(
        "code-development-team",
        session_id=session_id,
        user_id=user_id,
        debug_mode=debug_mode,
    )

    # Add team-specific metadata
    if team.metadata is None:
        team.metadata = {}

    team.metadata.update(
        {
            "team_type": "coordinate",
            "purpose": "Comprehensive software development capabilities",
            "specialization": [
                "project_onboarding",
                "code_analysis",
                "file_operations",
                "code_modifications",
            ],
        }
    )

    return team
