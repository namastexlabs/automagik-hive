#!/usr/bin/env python3
"""Pre-commit validation script for root-level file organization.

This script serves as the main entry point for the pre-commit hook system.
It validates staged changes against root-level organization rules and
provides clear feedback to developers about violations.
"""

import os
import sys

# Add src directory to Python path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

try:
    from hooks.application.validate_precommit import (
        ValidatePreCommitUseCase,
        ValidationMetrics,
    )
    from hooks.domain.entities import ValidationResult
    from hooks.domain.value_objects import (
        GenieStructure,
        RootWhitelist,
        ValidationConfig,
    )
    from hooks.infrastructure.filesystem_adapter import FileSystemAdapter
    from hooks.infrastructure.git_adapter import GitAdapter
except ImportError:
    sys.exit(1)


def main() -> int:
    """Main pre-commit validation entry point.

    Returns:
        Exit code: 0 for success, 1 for validation failure, 2 for system error
    """
    try:
        # Check if we're in test mode
        test_mode = "--test" in sys.argv

        if test_mode:
            return run_test_mode()

        # Initialize components
        git_adapter = GitAdapter()
        fs_adapter = FileSystemAdapter()

        # Verify we're in a Git repository
        if not git_adapter.is_git_repository():
            return 2

        # Get staged file changes
        file_changes = git_adapter.get_staged_changes()

        if not file_changes:
            return 0

        # Check bypass flag
        bypass_flag = fs_adapter.check_bypass_flag()
        if bypass_flag:
            bypass_info = fs_adapter.get_bypass_info()
            if bypass_info:
                pass

        # Initialize validation components
        whitelist = RootWhitelist.default()
        genie_structure = GenieStructure.default()
        config = ValidationConfig.default()
        use_case = ValidatePreCommitUseCase(whitelist, genie_structure, config)

        # Execute validation
        result = use_case.execute(file_changes, bypass_flag)

        # Display results
        display_validation_result(result)

        # Record metrics
        metrics = ValidationMetrics()
        metrics.record_validation(result)
        fs_adapter.record_validation_metrics(
            {
                "files_checked": result.total_files_processed,
                "blocked_count": len(result.blocked_files),
                "bypass_used": result.result == ValidationResult.BYPASS,
                "validation_result": result.result.value,
            }
        )

        # Return appropriate exit code
        if result.result == ValidationResult.BLOCKED:
            return 1
        return 0

    except Exception:
        if "--debug" in sys.argv:
            import traceback

            traceback.print_exc()
        return 2


def run_test_mode() -> int:
    """Run the validation system in test mode.

    Returns:
        Exit code: 0 for success, 1 for test failure
    """
    try:
        # Test Git adapter
        git_adapter = GitAdapter()
        if not git_adapter.is_git_repository():
            return 1

        # Test filesystem adapter
        fs_adapter = FileSystemAdapter()
        fs_adapter.get_project_root()

        # Test validation components
        whitelist = RootWhitelist.default()
        genie_structure = GenieStructure.default()
        config = ValidationConfig.default()
        use_case = ValidatePreCommitUseCase(whitelist, genie_structure, config)

        # Test with empty changes
        use_case.execute([])

        return 0

    except Exception:
        if "--debug" in sys.argv:
            import traceback

            traceback.print_exc()
        return 1


def display_validation_result(result) -> None:
    """Display validation results to user with colored output.

    Args:
        result: HookValidationResult to display
    """
    if result.result == ValidationResult.BYPASS:
        for _msg in result.error_messages:
            pass
        if result.suggestions:
            for _suggestion in result.suggestions:
                pass
        return

    # Display allowed files
    if result.allowed_files:
        for file_change in result.allowed_files:
            {
                "create": "📄",
                "modify": "✏️",
                "delete": "🗑️",
                "rename": "📝",
            }.get(file_change.operation.value, "📄")

    # Display blocked files
    if result.blocked_files:
        for _i, _msg in enumerate(result.error_messages):
            pass

    # Display suggestions
    if result.suggestions:
        for _suggestion in result.suggestions:
            pass

    # Display helpful information
    if result.blocked_files:
        pass


def print_usage() -> None:
    """Print usage information for the script."""


if __name__ == "__main__":
    if "--help" in sys.argv:
        print_usage()
        sys.exit(0)

    exit_code = main()
    sys.exit(exit_code)
