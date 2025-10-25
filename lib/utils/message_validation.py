"""Message Validation Utilities.

Provides validation functions for agent messages to prevent empty message
errors from reaching the Claude API.
"""

from typing import Any

from fastapi import HTTPException

from lib.logging import logger


def validate_agent_message(message: str, context: str = "agent execution") -> None:
    """Validate message content before sending to agent.

    Checks for empty or whitespace-only messages and enforces a maximum
    message length to prevent abuse. Raises HTTPException with detailed
    error information if validation fails.

    Args:
        message (str): The message to validate.
        context (str, optional): Context description for error messages.
            Defaults to "agent execution".

    Raises:
        HTTPException: If message is empty, contains only whitespace, or
            exceeds the maximum length of 10,000 characters.

    Example:
        >>> validate_agent_message("Hello, agent!")
        >>> validate_agent_message("")  # Raises HTTPException
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


def validate_request_data(request_data: dict[str, Any], context: str = "request") -> str:
    """Extract and validate message from request data.

    Extracts the 'message' field from a request data dictionary and
    validates it using validate_agent_message().

    Args:
        request_data (dict[str, Any]): Dictionary containing request data
            with a 'message' field.
        context (str, optional): Context description for error messages.
            Defaults to "request".

    Returns:
        str: The validated message string extracted from request_data.

    Raises:
        HTTPException: If message validation fails (empty, whitespace-only,
            or too long).

    Example:
        >>> data = {"message": "Process this"}
        >>> msg = validate_request_data(data)
        >>> print(msg)
        Process this
    """
    message: str = request_data.get("message", "")
    validate_agent_message(message, context)
    return message


def safe_agent_run(agent: Any, message: str, context: str = "agent execution") -> Any:
    """Safely run an agent with message validation.

    Validates the message before passing it to the agent's run() method.
    Catches and transforms Claude API empty message errors into consistent
    HTTPException responses.

    Args:
        agent (Any): The agent instance to run. Must have a run() method
            that accepts a message string.
        message (str): The message to send to the agent.
        context (str, optional): Context description for error messages.
            Defaults to "agent execution".

    Returns:
        Any: The response from agent.run(message).

    Raises:
        HTTPException: If message validation fails or if the agent raises
            a Claude API empty message error.
        Exception: Re-raises any other exceptions from agent.run().

    Example:
        >>> from agno import Agent
        >>> agent = Agent(name="helper")
        >>> response = safe_agent_run(agent, "Hello")
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
