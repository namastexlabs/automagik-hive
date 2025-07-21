"""
Template System Exceptions

Custom exception classes for the YAML templating system.
"""

from typing import Any


class TemplateProcessingError(Exception):
    """Base exception for template processing errors."""

    def __init__(
        self,
        message: str,
        template_path: str | None = None,
        context_data: dict[str, Any] | None = None,
        original_error: Exception | None = None
    ):
        self.template_path = template_path
        self.context_data = context_data
        self.original_error = original_error

        error_details = []
        if template_path:
            error_details.append(f"template={template_path}")
        if original_error:
            error_details.append(f"cause={type(original_error).__name__}: {original_error}")

        full_message = message
        if error_details:
            full_message += f" [{', '.join(error_details)}]"

        super().__init__(full_message)


class ContextMissingError(TemplateProcessingError):
    """Raised when required context data is missing."""

    def __init__(
        self,
        missing_key: str,
        template_path: str | None = None,
        available_keys: list | None = None
    ):
        message = f"Required context key '{missing_key}' is missing"
        if available_keys:
            message += f". Available keys: {available_keys}"

        super().__init__(message, template_path=template_path)
        self.missing_key = missing_key
        self.available_keys = available_keys


class SecurityViolationError(TemplateProcessingError):
    """Raised when template contains security violations."""

    def __init__(
        self,
        violation_type: str,
        details: str,
        template_path: str | None = None
    ):
        message = f"Security violation ({violation_type}): {details}"
        super().__init__(message, template_path=template_path)
        self.violation_type = violation_type
        self.details = details



class TemplateRenderError(TemplateProcessingError):
    """Raised when Jinja2 template rendering fails."""

    def __init__(
        self,
        jinja_error: Exception,
        template_path: str | None = None,
        line_number: int | None = None
    ):
        message = f"Template rendering failed: {jinja_error}"
        if line_number:
            message += f" at line {line_number}"

        super().__init__(message, template_path=template_path, original_error=jinja_error)
        self.line_number = line_number


class ContextValidationError(TemplateProcessingError):
    """Raised when context data validation fails."""

    def __init__(
        self,
        validation_error: str,
        context_type: str,
        invalid_data: dict[str, Any] | None = None
    ):
        message = f"Context validation failed for {context_type}: {validation_error}"
        super().__init__(message, context_data=invalid_data)
        self.context_type = context_type
        self.validation_error = validation_error
