#!/usr/bin/env python3
"""
TDD Hook - Enforces Test-Driven Development practices.

This hook runs before Write/Edit operations to ensure tests exist before implementation.
It checks for test files corresponding to the implementation files being modified.
"""

import json
import sys
import os
from pathlib import Path


def find_test_file(file_path: str) -> Path | None:
    """Find corresponding test file for an implementation file."""
    path = Path(file_path)
    
    # Skip if already a test file
    if 'test' in path.name.lower() or path.parts and 'tests' in path.parts:
        return None
        
    # Skip non-Python files
    if not path.suffix == '.py':
        return None
    
    # Common test file patterns
    test_patterns = [
        # Same directory with test_ prefix
        path.parent / f"test_{path.name}",
        # tests/ subdirectory
        path.parent / "tests" / f"test_{path.name}",
        # Project-level tests directory
        Path("tests") / path.parent.relative_to(Path.cwd()) / f"test_{path.name}"
        if path.is_absolute() else Path("tests") / path.parent / f"test_{path.name}",
    ]
    
    for test_path in test_patterns:
        if test_path.exists():
            return test_path
            
    return None


def main():
    """Main hook execution."""
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Get file path based on tool
    file_path = None
    if tool_name in ["Write", "Edit"]:
        file_path = tool_input.get("file_path")
    elif tool_name == "MultiEdit":
        file_path = tool_input.get("file_path")
    
    if not file_path:
        # No file path to check
        sys.exit(0)
    
    # Check if this is implementation code that needs tests
    path = Path(file_path)
    
    # Skip certain file types
    skip_extensions = {'.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.sh', '.bash'}
    if path.suffix in skip_extensions:
        sys.exit(0)
    
    # Skip certain directories
    skip_dirs = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', 'env', 'docs', '.claude', 'genie'}
    if any(part in skip_dirs for part in path.parts):
        sys.exit(0)
    
    # Check for corresponding test file
    test_file = find_test_file(str(path))
    
    if path.suffix == '.py' and not test_file and 'test' not in path.name.lower():
        # This is implementation code without tests - warn but don't block
        warning = (
            f"⚠️ TDD Warning: No test file found for {file_path}\n"
            f"Consider creating tests first:\n"
            f"  • tests/test_{path.name}\n"
            f"  • {path.parent}/test_{path.name}\n"
            f"Remember: Red → Green → Refactor"
        )
        print(warning, file=sys.stderr)
        # Exit with 2 (blocking error - shown to Claude)
        sys.exit(2)
    
    # All checks passed
    sys.exit(0)


if __name__ == "__main__":
    main()