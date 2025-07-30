"""
FastAPI Dependencies for Message Validation

Provides dependency injection for validating agent messages
before they reach the Agno Playground endpoints.
"""

import json

from fastapi import Form, HTTPException, Request, status

from lib.logging import logger


async def validate_message_dependency(message: str = Form(...)) -> str:
    """
    FastAPI dependency to validate message content from form data.

    Args:
        message: Message content from multipart/form-data

    Returns:
        Validated message string

    Raises:
        HTTPException: If message validation fails
    """
    # Check for empty or whitespace-only messages
    if not message or not message.strip():
        logger.warning("Empty message detected in Agno Playground endpoint")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
        logger.warning(
            f"🌐 Message too long in Agno Playground endpoint: {len(message)} characters"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "MESSAGE_TOO_LONG",
                    "message": "Message content is too long",
                    "details": f"Message length ({len(message)} characters) exceeds the maximum allowed length of 10,000 characters.",
                },
                "data": None,
            },
        )

    return message


async def validate_optional_message_dependency(
    message: str | None = Form(None),
) -> str | None:
    """
    FastAPI dependency to validate optional message content from form data.

    This is for endpoints where message might be optional.

    Args:
        message: Optional message content from multipart/form-data

    Returns:
        Validated message string or None

    Raises:
        HTTPException: If message validation fails (when message is provided but invalid)
    """
    if message is None:
        return None

    # If message is provided, validate it
    return await validate_message_dependency(message)


async def validate_runs_request(request: Request) -> None:
    """
    Alternative dependency that works with both JSON and form data.

    This can be used as a dependency for endpoints that need to handle
    both application/json and multipart/form-data content types.

    Args:
        request: FastAPI request object

    Raises:
        HTTPException: If message validation fails
    """
    content_type = request.headers.get("content-type", "")

    try:
        if content_type.startswith("multipart/form-data"):
            # Handle form data
            form = await request.form()
            message = form.get("message", "")
        elif content_type.startswith("application/json"):
            # Handle JSON data
            body = await request.body()
            if body:
                data = json.loads(body.decode())
                message = data.get("message", "")
            else:
                message = ""
        else:
            # For other content types, skip validation
            return

        # Validate message content
        if not message or not message.strip():
            logger.warning(f"🌐 Empty message detected in {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "EMPTY_MESSAGE",
                        "message": "Message content is required",
                        "details": "The 'message' parameter cannot be empty. Please provide a message for the agent to process.",
                    },
                    "data": None,
                },
            )

        # Check for overly long messages
        if len(message) > 10000:
            logger.warning(
                f"🌐 Message too long in {request.url.path}: {len(message)} characters"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "MESSAGE_TOO_LONG",
                        "message": "Message content is too long",
                        "details": f"Message length ({len(message)} characters) exceeds the maximum allowed length of 10,000 characters.",
                    },
                    "data": None,
                },
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"🌐 Error during request validation: {e}")
        # Don't fail the request for validation errors, let the endpoint handle it
