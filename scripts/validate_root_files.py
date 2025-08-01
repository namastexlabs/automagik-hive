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
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("🔧 Make sure the src/hooks package is properly installed")
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
            print("❌ Error: Not in a Git repository")
            return 2

        # Get staged file changes
        print("🔍 Checking staged changes...")
        file_changes = git_adapter.get_staged_changes()

        if not file_changes:
            print("ℹ️  No staged changes to validate")
            return 0

        print(f"📊 Found {len(file_changes)} staged changes")

        # Check bypass flag
        bypass_flag = fs_adapter.check_bypass_flag()
        if bypass_flag:
            bypass_info = fs_adapter.get_bypass_info()
            if bypass_info:
                print(f"⚠️  BYPASS ACTIVE: {bypass_info.get('reason', 'No reason provided')}")
                print(f"   Created by: {bypass_info.get('created_by', 'unknown')}")
                print(f"   Expires: {bypass_info.get('expires_at', 'unknown')}")

        # Initialize validation components
        whitelist = RootWhitelist.default()
        genie_structure = GenieStructure.default()
        config = ValidationConfig.default()
        use_case = ValidatePreCommitUseCase(whitelist, genie_structure, config)

        # Execute validation
        print("🔎 Running validation...")
        result = use_case.execute(file_changes, bypass_flag)

        # Display results
        display_validation_result(result)

        # Record metrics
        metrics = ValidationMetrics()
        metrics.record_validation(result)
        fs_adapter.record_validation_metrics({
            "files_checked": result.total_files_processed,
            "blocked_count": len(result.blocked_files),
            "bypass_used": result.result == ValidationResult.BYPASS,
            "validation_result": result.result.value
        })

        # Return appropriate exit code
        if result.result == ValidationResult.BLOCKED:
            return 1
        return 0

    except Exception as e:
        print(f"❌ Pre-commit hook error: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
        return 2


def run_test_mode() -> int:
    """Run the validation system in test mode.
    
    Returns:
        Exit code: 0 for success, 1 for test failure
    """
    print("🧪 Running pre-commit hook validation in test mode...")

    try:
        # Test Git adapter
        git_adapter = GitAdapter()
        if not git_adapter.is_git_repository():
            print("❌ Test failed: Not in a Git repository")
            return 1

        print("✅ Git repository detected")

        # Test filesystem adapter
        fs_adapter = FileSystemAdapter()
        project_root = fs_adapter.get_project_root()
        print(f"✅ Project root: {project_root}")

        # Test validation components
        whitelist = RootWhitelist.default()
        genie_structure = GenieStructure.default()
        config = ValidationConfig.default()
        use_case = ValidatePreCommitUseCase(whitelist, genie_structure, config)

        print("✅ Validation components initialized")
        print(f"📋 Whitelist patterns: {len(whitelist.patterns)}")
        print(f"📁 Genie paths: {len(genie_structure.allowed_paths)}")

        # Test with empty changes
        empty_result = use_case.execute([])
        print(f"✅ Empty validation test: {empty_result.result.value}")

        print("🎉 All tests passed!")
        return 0

    except Exception as e:
        print(f"❌ Test failed: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
        return 1


def display_validation_result(result) -> None:
    """Display validation results to user with colored output.
    
    Args:
        result: HookValidationResult to display
    """
    print("\n" + "="*60)
    print(f"📊 VALIDATION RESULT: {result.result.value.upper()}")
    print("="*60)

    if result.result == ValidationResult.BYPASS:
        print("⚠️  BYPASS MODE ACTIVE - Validation skipped")
        for msg in result.error_messages:
            print(f"   {msg}")
        if result.suggestions:
            print("\n💡 Bypass reminders:")
            for suggestion in result.suggestions:
                print(f"   {suggestion}")
        return

    # Display allowed files
    if result.allowed_files:
        print(f"\n✅ ALLOWED FILES ({len(result.allowed_files)}):")
        for file_change in result.allowed_files:
            operation_icon = {
                "create": "📄",
                "modify": "✏️",
                "delete": "🗑️",
                "rename": "📝"
            }.get(file_change.operation.value, "📄")
            print(f"   {operation_icon} {file_change.path}")

    # Display blocked files
    if result.blocked_files:
        print(f"\n❌ BLOCKED FILES ({len(result.blocked_files)}):")
        for i, msg in enumerate(result.error_messages):
            print(f"\n{i+1}. {msg}")

    # Display suggestions
    if result.suggestions:
        print("\n💡 SUGGESTIONS:")
        for suggestion in result.suggestions:
            print(f"   {suggestion}")

    # Display helpful information
    if result.blocked_files:
        print("\n🛠️  QUICK FIXES:")
        print("   • Move .md files to /genie/docs/ or /genie/ideas/")
        print("   • Move source code to /lib/ or existing modules")
        print("   • Check CLAUDE.md workspace organization rules")
        print("\n🚨 EMERGENCY BYPASS (use sparingly):")
        print("   • git commit --no-verify")
        print("   • make bypass-hooks")
        print("   • touch .git/hooks/BYPASS_ROOT_VALIDATION")

    print("\n" + "="*60)


def print_usage() -> None:
    """Print usage information for the script."""
    print("Usage: python scripts/validate_root_files.py [options]")
    print("\nOptions:")
    print("  --test    Run in test mode (validate system components)")
    print("  --debug   Show detailed error information")
    print("  --help    Show this help message")
    print("\nThis script is typically called automatically by Git pre-commit hooks.")
    print("It validates staged changes against root-level file organization rules.")


if __name__ == "__main__":
    if "--help" in sys.argv:
        print_usage()
        sys.exit(0)

    exit_code = main()
    sys.exit(exit_code)
