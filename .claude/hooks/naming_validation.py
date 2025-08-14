#!/usr/bin/env python3
"""
Naming Convention Validation Hook

CRITICAL PREVENTION: Pre-creation validation to prevent forbidden naming patterns.
USER FEEDBACK: "its completly forbidden, across all codebase, to write files and functionsm etc, with fixed, enhanced, etc"

This hook integrates with the agent environment to prevent naming convention violations
before they occur in any file or code creation operation.
"""

import sys
import os
import re
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from lib.validation.naming_conventions import (
        naming_validator,
        validate_file_creation,
        NamingViolation
    )
except ImportError:
    # Fallback validation if import fails
    print("⚠️  WARNING: Could not import naming validation module")
    sys.exit(0)


def validate_operation_name(operation_path: str) -> None:
    """
    Validate file or function names before creation operations.
    
    Args:
        operation_path: Path to file being created or modified
        
    Raises:
        SystemExit: If naming convention violations are detected
    """
    try:
        # Extract filename from path
        file_path = Path(operation_path)
        filename = file_path.name
        
        # Skip validation for certain system files
        skip_patterns = [
            r'__pycache__',
            r'\.git/',
            r'\.venv/',
            r'\.pytest_cache/',
            r'alembic/versions/',
            r'\.pyc$',
            r'\.pyo$',
            r'\.so$'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, str(operation_path)):
                return
        
        # Validate the filename
        is_valid, violations = naming_validator.validate_file_path(operation_path)
        
        if not is_valid:
            violation_report = naming_validator.get_violation_report(violations, filename)
            
            print("🚨 NAMING CONVENTION VIOLATION PREVENTED")
            print("=" * 60)
            print(f"FILE: {operation_path}")
            print(violation_report)
            print("\n" + "=" * 60)
            print("💡 PREVENTION SUCCESS: Blocked creation of file with forbidden naming pattern")
            print("📚 USER FEEDBACK: 'its completly forbidden, across all codebase, to write files and functionsm etc, with fixed, enhanced, etc'")
            print("🎯 BEHAVIORAL LEARNING: Zero tolerance for modification-status naming patterns")
            
            sys.exit(1)
            
    except Exception as e:
        print(f"⚠️  WARNING: Naming validation hook error: {e}")
        # Don't block operation if hook fails - just warn
        sys.exit(0)


def main():
    """Main hook execution."""
    if len(sys.argv) < 2:
        print("Usage: naming-validation.py <file_path>")
        sys.exit(1)
    
    operation_path = sys.argv[1]
    validate_operation_name(operation_path)
    
    # If we get here, validation passed
    print(f"✅ NAMING VALIDATION PASSED: {Path(operation_path).name}")


if __name__ == "__main__":
    main()