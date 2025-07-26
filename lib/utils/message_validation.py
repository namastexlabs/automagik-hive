"""
Message Validation Utilities

Provides validation functions for agent messages to prevent empty message
errors from reaching the Claude API.
"""

from typing import Any

from fastapi import HTTPException

from lib.logging import logger


def validate_agent_message(message: str, context: str = "agent execution") -> None:
    """
    Validate message content before sending to agent.

    Args:
        message: The message to validate
        context: Context description for error messages

    Raises:
        HTTPException: If message validation fails
    """
    # Check for empty or whitespace-only messages
    if not message or not message.strip():
        logger.warning(f"🌐 Empty message detected in {context}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "EMPTY_MESSAGE",
                    "message": "Message content is required",
                    "details": "The 'message' parameter cannot be empty. Please provide a message for the agent to process.",
                },
                "data": None,
            },
        )

    # Check for overly long messages (prevent abuse)
    if len(message) > 10000:  # 10KB limit
        logger.warning(f"🌐 Message too long in {context}: {len(message)} characters")
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "MESSAGE_TOO_LONG",
                    "message": "Message content is too long",
                    "details": f"Message length ({len(message)} characters) exceeds the maximum allowed length of 10,000 characters.",
                },
                "data": None,
            },
        )


def validate_request_data(
    request_data: dict[str, Any], context: str = "request"
) -> str:
    """
    Extract and validate message from request data.

    Args:
        request_data: Dictionary containing request data
        context: Context description for error messages

    Returns:
        Validated message string

    Raises:
        HTTPException: If message validation fails
    """
    message: str = request_data.get("message", "")
    validate_agent_message(message, context)
    return message


def safe_agent_run(agent: Any, message: str, context: str = "agent execution") -> Any:
    """
    Safely run an agent with message validation.

    Args:
        agent: The agent instance to run
        message: The message to send to the agent
        context: Context description for error messages

    Returns:
        Agent response

    Raises:
        HTTPException: If message validation fails
    """
    validate_agent_message(message, context)

    try:
        return agent.run(message)
    except Exception as e:
        # Check if this is a Claude API error about empty messages
        error_msg = str(e).lower()
        if "text content blocks must be non-empty" in error_msg:
            logger.error(f"🌐 Claude API empty message error caught: {e}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "EMPTY_MESSAGE",
                        "message": "Message content is required",
                        "details": "The message content cannot be empty. Please provide a valid message for the agent to process.",
                    },
                    "data": None,
                },
            )
        # Re-raise other exceptions
        raise
