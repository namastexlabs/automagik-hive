#!/usr/bin/env python3
"""
Unified TDD Hook - Enforces Test-Driven Development with proper test structure.

This sophisticated hook:
1. Enforces proper test file structure (mirror pattern in tests/ directory)
2. Validates TDD cycle (Red-Green-Refactor) by running tests when needed
3. Prevents creation of tests in wrong locations
4. Detects and warns about orphaned tests
"""

import json
import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


class TDDValidator:
    """Validates TDD practices and test structure."""
    
    # Directories that should have tests
    SOURCE_DIRS = {'api', 'lib', 'ai', 'common', 'cli'}
    
    # Directories to skip
    SKIP_DIRS = {
        '__pycache__', '.git', '.venv', 'venv', 'env', 
        'node_modules', '.pytest_cache', '.mypy_cache',
        'build', 'dist', '.eggs', 'data', 'logs', 
        '.claude', 'genie', 'scripts', 'docs', 'alembic'
    }
    
    # File extensions to skip
    SKIP_EXTENSIONS = {
        '.md', '.txt', '.json', '.yaml', '.yml', '.toml', 
        '.ini', '.cfg', '.conf', '.sh', '.bash', '.sql',
        '.csv', '.html', '.css', '.js', '.jsx', '.ts', '.tsx'
    }
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.tests_dir = self.project_root / 'tests'
    
    def get_expected_test_path(self, source_path: str) -> Optional[Path]:
        """Get the expected test file path following mirror structure."""
        path = Path(source_path)
        
        # Make path relative to project root
        try:
            if path.is_absolute():
                rel_path = path.relative_to(self.project_root)
            else:
                rel_path = path
        except ValueError:
            # Path is outside project
            return None
        
        # Check if in a source directory we care about
        parts = rel_path.parts
        if not parts or parts[0] not in self.SOURCE_DIRS:
            return None
        
        # Build expected test path (mirror structure)
        test_path = self.tests_dir / rel_path.parent / f"test_{rel_path.name}"
        return test_path
    
    def get_expected_source_path(self, test_path: str) -> Optional[Path]:
        """Get expected source file for a test file."""
        path = Path(test_path)
        
        # Check if it's in tests directory
        try:
            rel_path = path.relative_to(self.tests_dir)
        except ValueError:
            # Not in tests directory - wrong location!
            return None
        
        # Extract source name from test name
        if path.name.startswith('test_'):
            source_name = path.name[5:]  # Remove 'test_' prefix
        elif path.name.endswith('_test.py'):
            source_name = path.name[:-8] + '.py'  # Remove '_test.py' suffix
        else:
            # Not a properly named test file
            return None
        
        # Build expected source path
        if rel_path.parts:
            # Has subdirectories under tests/
            source_path = self.project_root / Path(*rel_path.parts[:-1]) / source_name
        else:
            # Direct child of tests/ - shouldn't happen with mirror structure
            return None
        
        return source_path
    
    def run_tests(self, test_file: Optional[str] = None) -> Dict:
        """Run pytest and return results."""
        try:
            cmd = ["uv", "run", "pytest", "--tb=short", "-q"]
            if test_file and Path(test_file).exists():
                cmd.append(test_file)
            
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30  # 30 second timeout
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "has_failures": "FAILED" in result.stdout or result.returncode != 0,
                "ran": True
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "Tests timed out after 30 seconds",
                "has_failures": True,
                "ran": False
            }
        except Exception as e:
            return {
                "success": False,
                "output": str(e),
                "has_failures": False,
                "ran": False
            }
    
    def validate_file_operation(self, tool_name: str, file_path: str, content: str = "") -> Tuple[bool, str]:
        """
        Validate file operation according to TDD and structure rules.
        Returns (allowed, message).
        """
        path = Path(file_path)
        
        # Skip certain directories
        if any(skip_dir in path.parts for skip_dir in self.SKIP_DIRS):
            return True, f"File in skipped directory - allowed"
        
        # Check if this is a test file
        is_test_file = (
            'test_' in path.name or 
            path.name.endswith('_test.py') or
            'tests' in path.parts
        )
        
        if is_test_file:
            return self.validate_test_file(file_path)
        else:
            return self.validate_source_file(file_path, content)
    
    def validate_test_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate test file creation/modification."""
        path = Path(file_path)
        
        # Special files always allowed
        if path.name in ('__init__.py', 'conftest.py'):
            return True, "Special test file - allowed"
        
        # Check if test is in proper location
        if 'tests' not in path.parts:
            return False, (
                "❌ TEST STRUCTURE VIOLATION\n"
                f"Test file must be in tests/ directory!\n"
                f"File: {file_path}\n"
                f"Use proper mirror structure: tests/<source_dir>/test_<name>.py"
            )
        
        # Integration and support directories with special rules
        INTEGRATION_PATTERNS = {'integration', 'fixtures', 'mocks', 'utilities', 'e2e', 'scenarios'}
        is_integration = any(part in INTEGRATION_PATTERNS for part in path.parts)
        
        # Fixture and utility files don't need test_ prefix
        if 'fixtures' in path.parts or 'utilities' in path.parts or 'mocks' in path.parts:
            # These are support files, not actual test files
            return True, "Test support file (fixture/utility/mock) - allowed"
        
        # Check if test follows naming convention (for actual test files)
        if not (path.name.startswith('test_') or path.name.endswith('_test.py')):
            return False, (
                "❌ TEST NAMING VIOLATION\n"
                f"Test file must start with 'test_' or end with '_test.py'\n"
                f"File: {path.name}\n"
                f"Rename to: test_{path.name}"
            )
        
        # Check if test has corresponding source (warn only, don't block)
        expected_source = self.get_expected_source_path(file_path)
        if expected_source and not expected_source.exists():
            # For integration tests, this is expected
            if is_integration:
                message = (
                    "✅ Integration test - no source file needed\n"
                    f"Test: {file_path}\n"
                    "Integration tests don't require mirror source files"
                )
            else:
                # This is an orphaned test - warn but allow (might be creating test first)
                message = (
                    "⚠️ TDD WARNING: Creating test for non-existent source file\n"
                    f"Test: {file_path}\n"
                    f"Expected source: {expected_source}\n"
                    "This is OK if you're in RED phase (test-first development)"
                )
            print(message, file=sys.stderr)
        
        return True, "Test file creation/modification allowed"
    
    def validate_source_file(self, file_path: str, content: str) -> Tuple[bool, str]:
        """Validate source file creation/modification with TDD rules."""
        path = Path(file_path)
        
        # Skip if not in a tracked source directory
        try:
            rel_path = path.relative_to(self.project_root) if path.is_absolute() else path
            if not any(str(rel_path).startswith(src_dir) for src_dir in self.SOURCE_DIRS):
                return True, "File not in tracked source directory - allowed"
        except ValueError:
            return True, "File outside project - allowed"
        
        # Get expected test path
        expected_test = self.get_expected_test_path(file_path)
        if not expected_test:
            return True, "No test required for this file - allowed"
        
        # Check if test exists
        test_exists = expected_test.exists()
        
        # If creating new source file without test, block it
        if not path.exists() and not test_exists:
            return False, (
                "❌ TDD VIOLATION: RED PHASE REQUIRED\n"
                f"Cannot create source file without test!\n"
                f"Source: {file_path}\n"
                f"Create test first: {expected_test}\n"
                "Follow TDD: Write failing test → Implement → Refactor"
            )
        
        # If test doesn't exist for existing file, warn but allow
        if not test_exists:
            message = (
                "⚠️ TDD WARNING: No test file found\n"
                f"Source: {file_path}\n"
                f"Expected test: {expected_test}\n"
                "Consider creating tests before making changes"
            )
            print(message, file=sys.stderr)
            return True, "Modification allowed with warning"
        
        # Test exists - check if we should run it (only for significant changes)
        if path.exists() and content and len(content) > 100:
            # Run tests to check TDD phase
            test_results = self.run_tests(str(expected_test))
            
            if test_results["ran"]:
                if test_results["has_failures"]:
                    # GREEN PHASE - tests failing, implementation allowed
                    message = (
                        "✅ TDD GREEN PHASE: Tests failing, implementation allowed\n"
                        f"Implement code to make tests pass"
                    )
                    print(message, file=sys.stderr)
                else:
                    # REFACTOR PHASE - tests passing
                    message = (
                        "♻️ TDD REFACTOR PHASE: All tests passing\n"
                        "Ensure new functionality has failing tests first"
                    )
                    print(message, file=sys.stderr)
        
        return True, "Source file modification allowed"


def main():
    """Main hook entry point."""
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Get file path based on tool
    file_path = None
    content = ""
    
    if tool_name in ["Write", "Edit"]:
        file_path = tool_input.get("file_path")
        content = tool_input.get("content", "") or tool_input.get("new_string", "")
    elif tool_name == "MultiEdit":
        file_path = tool_input.get("file_path")
        edits = tool_input.get("edits", [])
        if edits:
            content = " ".join(edit.get("new_string", "") for edit in edits)
    
    if not file_path:
        # No file path to check
        sys.exit(0)
    
    # ONLY CHECK PYTHON FILES
    if not file_path.endswith('.py'):
        # Not a Python file - skip validation
        sys.exit(0)
    
    # Validate the operation
    validator = TDDValidator()
    allowed, message = validator.validate_file_operation(tool_name, file_path, content)
    
    if not allowed:
        # Block the operation with error message
        print(message, file=sys.stderr)
        sys.exit(2)  # Exit with 2 to show message to user
    
    # Operation allowed
    sys.exit(0)


if __name__ == "__main__":
    main()