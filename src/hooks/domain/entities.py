"""Domain entities for pre-commit hook validation system.

This module contains the core business entities that represent the fundamental
concepts of the pre-commit validation system. These entities are pure domain
objects with no external dependencies.
"""

from dataclasses import dataclass
from enum import Enum


class FileOperation(Enum):
    """Enumeration of possible file operations detected by Git."""

    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"


class ValidationResult(Enum):
    """Enumeration of validation outcomes."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"
    BYPASS = "bypass"


@dataclass
class FileChange:
    """Core entity representing a file system change detected by Git.

    This entity encapsulates all information about a file change needed
    for validation decisions, including path analysis and suggestions.
    """

    path: str
    operation: FileOperation
    is_root_level: bool
    file_extension: str | None
    is_directory: bool

    def get_suggested_path(self) -> str | None:
        """Generate suggested alternative path based on file type.

        Returns:
            Suggested path for the file, or None if no suggestion available.
        """
        if not self.is_root_level:
            return None

        if self.file_extension == ".md":
            if "readme" in self.path.lower():
                return None  # README.md is allowed at root
            if any(word in self.path.lower() for word in ["plan", "wish", "todo"]):
                return f"/genie/wishes/{self.path}"
            if any(
                word in self.path.lower() for word in ["design", "architecture", "ddd"]
            ):
                return f"/genie/docs/{self.path}"
            if any(word in self.path.lower() for word in ["idea", "analysis", "brain"]):
                return f"/genie/ideas/{self.path}"
            if any(
                word in self.path.lower() for word in ["report", "complete", "summary"]
            ):
                return f"/genie/reports/{self.path}"
            return f"/genie/docs/{self.path}"
        if self.is_directory:
            return f"/lib/{self.path}/"

        return None


@dataclass
class ValidationRule:
    """Core entity defining validation rules for file operations.

    Represents a single validation rule that can be applied to determine
    whether a file operation should be allowed or blocked.
    """

    pattern: str
    rule_type: str  # "allow" or "block"
    description: str
    applies_to: list[FileOperation]


@dataclass
class HookValidationResult:
    """Result of pre-commit hook validation containing all outcomes.

    This entity aggregates the complete validation result including
    categorized files, error messages, and user-friendly suggestions.
    """

    result: ValidationResult
    blocked_files: list[FileChange]
    allowed_files: list[FileChange]
    bypass_files: list[FileChange]
    error_messages: list[str]
    suggestions: list[str]

    @property
    def has_violations(self) -> bool:
        """Check if validation found any violations."""
        return len(self.blocked_files) > 0

    @property
    def total_files_processed(self) -> int:
        """Get total number of files processed."""
        return (
            len(self.blocked_files) + len(self.allowed_files) + len(self.bypass_files)
        )

    def get_summary(self) -> str:
        """Get a human-readable summary of validation results."""
        if self.result == ValidationResult.BYPASS:
            return f"BYPASS: {self.total_files_processed} files processed with validation disabled"
        if self.result == ValidationResult.BLOCKED:
            return f"BLOCKED: {len(self.blocked_files)} violations found, {len(self.allowed_files)} files allowed"
        return f"ALLOWED: All {self.total_files_processed} files passed validation"
