from __future__ import annotations

from typing import TYPE_CHECKING

from lib.utils.version_factory import create_team

if TYPE_CHECKING:
    from agno.team import Team


async def get_genie_team(
    session_id: str | None = None,
    user_id: str | None = None,
    debug_mode: bool = False,
) -> Team:
    """
    Create the magical Genie team using factory pattern.

    Provides comprehensive development capabilities through charismatic,
    relentless coordination of specialized agents. GENIE commands an army
    of specialists to fulfill all coding wishes!

    Args:
        session_id: Session ID for conversation tracking
        user_id: User ID for team context
        debug_mode: Enable debug mode

    Returns:
        Configured Genie team instance with tool format fix applied
    """
    # Create team using factory pattern with correct team ID
    team = await create_team(
        team_id="genie",
        session_id=session_id,
        user_id=user_id,
        debug_mode=debug_mode,
    )

    # Add Genie-specific metadata
    if team.metadata is None:
        team.metadata = {}

    team.metadata.update(
        {
            "team_type": "coordinate",
            "purpose": "Magical development companion with tool format fix",
            "specialization": [
                "strategic_orchestration",
                "agent_spawning",
                "mcp_mastery",
                "chaos_brilliance",
                "tool_format_conversion",  # Our critical fix!
            ],
            "claude_api_fix": "Applied OpenAI function format conversion for tools",
        }
    )

    return team
