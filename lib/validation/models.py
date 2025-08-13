"""
Pydantic validation models for API requests.

Provides input validation and sanitization for all API endpoints.
"""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


class BaseValidatedRequest(BaseModel):
    """Base model for all validated requests."""

    model_config = {
        # Allow extra fields but validate known ones
        "extra": "forbid",
        # Validate assignment to prevent modification after creation
        "validate_assignment": True,
        # Use enum values instead of names
        "use_enum_values": True,
    }


class AgentRequest(BaseValidatedRequest):
    """Request model for agent interactions."""

    message: str = Field(
        ..., min_length=1, max_length=10000, description="Message to send to the agent"
    )
    session_id: str | None = Field(
        None,
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=100,
        description="Optional session ID for conversation continuity",
    )
    user_id: str | None = Field(
        None,
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=100,
        description="Optional user ID for personalization",
    )
    context: dict[str, Any] | None = Field(
        None, description="Optional context data for the agent"
    )
    stream: bool = Field(False, description="Whether to stream the response")

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v):
        """Sanitize message content."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")

        # Remove potentially dangerous characters but keep reasonable punctuation
        # This is a basic sanitization - adjust based on your needs
        return re.sub(r'[<>"\']', "", v.strip())

    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        """Validate context dictionary."""
        if v is None:
            return v

        # Limit context size
        if len(str(v)) > 5000:
            raise ValueError("Context too large (max 5000 characters)")

        # Ensure no dangerous keys
        dangerous_keys = ["__", "eval", "exec", "import", "open", "file"]
        for key in v:
            if any(danger in str(key).lower() for danger in dangerous_keys):
                raise ValueError(f"Invalid context key: {key}")

        return v


class TeamRequest(BaseValidatedRequest):
    """Request model for team interactions."""

    task: str = Field(
        ..., min_length=1, max_length=5000, description="Task description for the team"
    )
    team_id: str | None = Field(
        None,
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=50,
        description="Optional specific team ID",
    )
    session_id: str | None = Field(
        None,
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=100,
        description="Optional session ID for conversation continuity",
    )
    user_id: str | None = Field(
        None,
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=100,
        description="Optional user ID",
    )
    context: dict[str, Any] | None = Field(
        default_factory=dict, description="Context data for the team"
    )
    stream: bool = Field(False, description="Whether to stream the response")

    @field_validator("task")
    @classmethod
    def sanitize_task(cls, v):
        """Sanitize task description."""
        if not v or not v.strip():
            raise ValueError("Task cannot be empty")

        # Basic sanitization
        return re.sub(r'[<>"\']', "", v.strip())


class WorkflowRequest(BaseValidatedRequest):
    """Request model for workflow execution."""

    workflow_id: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=50,
        description="Workflow identifier",
    )
    input_data: dict[str, Any] = Field(
        default_factory=dict, description="Input data for workflow execution"
    )
    session_id: str | None = Field(
        None,
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=100,
        description="Optional session ID",
    )
    user_id: str | None = Field(
        None,
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=100,
        description="Optional user ID",
    )

    @field_validator("input_data")
    @classmethod
    def validate_input_data(cls, v):
        """Validate workflow input data."""
        if len(str(v)) > 10000:
            raise ValueError("Input data too large (max 10000 characters)")

        # Check for dangerous keys
        dangerous_keys = ["__", "eval", "exec", "import", "open", "file"]

        def check_dict_recursive(d):
            if isinstance(d, dict):
                for key, value in d.items():
                    if any(danger in str(key).lower() for danger in dangerous_keys):
                        raise ValueError(f"Invalid input key: {key}")
                    if isinstance(value, dict):
                        check_dict_recursive(value)

        check_dict_recursive(v)
        return v


class HealthRequest(BaseValidatedRequest):
    """Request model for health check (minimal validation)."""


class VersionRequest(BaseValidatedRequest):
    """Request model for version info (minimal validation)."""


# Common response models
class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Additional error details")
    error_code: str | None = Field(
        None, description="Error code for programmatic handling"
    )


class SuccessResponse(BaseModel):
    """Standard success response model."""

    success: bool = Field(True, description="Operation success status")
    message: str | None = Field(None, description="Success message")
    data: Any | None = Field(None, description="Response data")
