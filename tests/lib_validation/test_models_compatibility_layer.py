"""
Compatibility layer for testing Pydantic V1 models with V2 environment.
This module provides mocked versions of the validation models for testing.
"""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


class MockBaseValidatedRequest(BaseModel):
    """Mock base model for testing with V2-compatible syntax."""

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
        "use_enum_values": True,
    }


class MockAgentRequest(MockBaseValidatedRequest):
    """Mock AgentRequest for testing purposes."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Message to send to the agent",
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
        None,
        description="Optional context data for the agent",
    )
    stream: bool = Field(False, description="Whether to stream the response")

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v):
        """Sanitize message content."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")

        # Remove potentially dangerous characters but keep reasonable punctuation
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


class MockTeamRequest(MockBaseValidatedRequest):
    """Mock TeamRequest for testing purposes."""

    task: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Task description for the team",
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
        default_factory=dict,
        description="Context data for the team",
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


class MockWorkflowRequest(MockBaseValidatedRequest):
    """Mock WorkflowRequest for testing purposes."""

    workflow_id: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=50,
        description="Workflow identifier",
    )
    input_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Input data for workflow execution",
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


class MockHealthRequest(MockBaseValidatedRequest):
    """Mock HealthRequest for testing purposes."""


class MockVersionRequest(MockBaseValidatedRequest):
    """Mock VersionRequest for testing purposes."""


class MockErrorResponse(BaseModel):
    """Mock ErrorResponse for testing purposes."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Additional error details")
    error_code: str | None = Field(
        None,
        description="Error code for programmatic handling",
    )


class MockSuccessResponse(BaseModel):
    """Mock SuccessResponse for testing purposes."""

    success: bool = Field(True, description="Operation success status")
    message: str | None = Field(None, description="Success message")
    data: Any | None = Field(None, description="Response data")
