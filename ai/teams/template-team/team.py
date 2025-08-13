from __future__ import annotations

from typing import TYPE_CHECKING

from lib.utils.version_factory import create_team

if TYPE_CHECKING:
    from agno.team import Team


async def get_template_team(
    session_id: str | None = None,
    user_id: str | None = None,
    debug_mode: bool = False,
) -> Team:
    """
    Create template team using factory pattern.

    This is a comprehensive template team showcasing all 74 Agno Team parameters
    and their proper usage patterns.

    Args:
        session_id: Session ID for conversation tracking
        user_id: User ID for session management
        debug_mode: Enable debug mode

    Returns:
        Configured template team instance
    """
    # Create team using factory pattern
    team = await create_team(
        team_id="template-team", session_id=session_id, user_id=user_id, debug_mode=debug_mode
    )

    # Add template-specific metadata
    if team.metadata is None:
        team.metadata = {}

    team.metadata.update(
        {
            "template_type": "comprehensive",
            "purpose": "Demonstrates all 74 Agno Team parameters",
            "usage": "Reference implementation for team development",
        }
    )

    return team
