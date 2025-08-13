"""
Validation utilities for Automagik Hive.

Provides Pydantic models for API validation and naming convention validation
to prevent violations of project standards.
"""

from .models import AgentRequest, BaseValidatedRequest, TeamRequest, WorkflowRequest
from .naming_conventions import (
    NamingConventionValidator,
    NamingViolation,
    naming_validator,
    validate_before_creation,
    validate_file_creation,
    validate_function_creation,
    validate_class_creation
)

__all__ = [
    # API validation models
    "AgentRequest", 
    "BaseValidatedRequest", 
    "TeamRequest", 
    "WorkflowRequest",
    # Naming convention validation
    "NamingConventionValidator",
    "NamingViolation", 
    "naming_validator",
    "validate_before_creation",
    "validate_file_creation",
    "validate_function_creation",
    "validate_class_creation"
]
