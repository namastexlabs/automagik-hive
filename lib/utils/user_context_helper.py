"""
Simple User Context Helper using Agno's session_state
No complex middleware or separate database tables needed
"""

from typing import Any

from agno.utils.log import logger


def create_user_context_state(
    user_id: str | None = None,
    user_name: str | None = None,
    phone_number: str | None = None,
    cpf: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Create session_state dictionary with user context.

    This follows Agno's session_state pattern for maintaining user data
    across runs without needing separate database tables.

    Args:
        user_id: User identifier
        user_name: User's full name
        phone_number: User's phone number
        cpf: User's CPF
        **kwargs: Additional user context data

    Returns:
        Dictionary suitable for agent.session_state
    """

    # Build user context, filtering out None values
    user_context = {}

    if user_id:
        user_context["user_id"] = user_id
    if user_name:
        user_context["user_name"] = user_name
    if phone_number:
        user_context["phone_number"] = phone_number
    if cpf:
        user_context["cpf"] = cpf

    # Add any additional context
    user_context.update(
        {key: value for key, value in kwargs.items() if value is not None}
    )

    # Return session_state structure
    session_state = {"user_context": user_context}

    if user_context:
        logger.info(f"📝 Created user context state: {list(user_context.keys())}")

    return session_state


def get_user_context_from_agent(agent) -> dict[str, Any]:
    """
    Get user context from agent's session_state.

    Args:
        agent: Agno Agent instance

    Returns:
        Dictionary with user context data
    """

    if not hasattr(agent, "session_state") or not agent.session_state:
        return {}

    return agent.session_state.get("user_context", {})


# Note: Only the functions above are actively used in the codebase.
# Previously contained unused helper functions that have been removed.
