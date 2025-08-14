#!/usr/bin/env python3
"""
Test script for the Automagik Hive pre-commit hook system.

This script creates test scenarios to validate the pre-commit hook functionality:
1. Test file without corresponding test file (should fail)
2. Test file with failing tests (should fail) 
3. Test file with low coverage (should fail)
4. Test file with good tests and coverage (should pass)
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple


class PreCommitHookTester:
    """Test the pre-commit hook system with various scenarios."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.temp_files: List[Path] = []
        
    def cleanup(self) -> None:
        """Clean up temporary test files."""
        for file_path in self.temp_files:
            try:
                if file_path.exists():
                    file_path.unlink()
                # Also unstage the file if it was staged
                subprocess.run(
                    ["git", "reset", "HEAD", str(file_path)],
                    cwd=self.project_root,
                    capture_output=True,
                    check=False
                )
            except Exception as e:
                print(f"Warning: Could not clean up {file_path}: {e}")
        self.temp_files.clear()
    
    def create_temp_file(self, relative_path: str, content: str) -> Path:
        """Create a temporary file for testing."""
        file_path = self.project_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        self.temp_files.append(file_path)
        return file_path
    
    def run_git_command(self, cmd: List[str]) -> Tuple[bool, str, str]:
        """Run a git command and return success status, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def stage_file(self, file_path: Path) -> bool:
        """Stage a file for commit."""
        success, stdout, stderr = self.run_git_command(["git", "add", str(file_path)])
        if not success:
            print(f"Failed to stage {file_path}: {stderr}")
        return success
    
    def run_pre_commit_hook(self) -> Tuple[bool, str]:
        """Run the pre-commit hook and return success status and output."""
        hook_path = self.project_root / ".git" / "hooks" / "pre-commit"
        if not hook_path.exists():
            return False, "Pre-commit hook not found"
            
        try:
            result = subprocess.run(
                [str(hook_path)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def test_scenario_1_missing_test_file(self) -> bool:
        """Test scenario: Source file without corresponding test file."""
        print("\n=== Test Scenario 1: Missing Test File ===")
        
        # Create a source file without a test file
        source_file = self.create_temp_file(
            "lib/test_scenarios/missing_test.py",
            '''"""Module without a corresponding test file."""

def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers."""
    return a + b

def multiply(x: int, y: int) -> int:
    """Multiply two numbers."""
    return x * y
'''
        )
        
        print(f"Created source file: {source_file}")
        
        # Stage the file
        if not self.stage_file(source_file):
            return False
            
        # Run the pre-commit hook (should fail)
        success, output = self.run_pre_commit_hook()
        
        print(f"Hook result: {'PASS' if success else 'FAIL (expected)'}")
        print("Hook output:")
        print(output)
        
        # This should fail because there's no test file
        return not success
    
    def test_scenario_2_failing_test(self) -> bool:
        """Test scenario: Source file with failing test."""
        print("\n=== Test Scenario 2: Failing Test ===")
        
        # Create a source file
        source_file = self.create_temp_file(
            "lib/test_scenarios/failing_test_module.py",
            '''"""Module with failing tests."""

def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def divide_numbers(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
'''
        )
        
        # Create a corresponding test file with failing tests
        test_file = self.create_temp_file(
            "tests/lib/test_scenarios/test_failing_test_module.py",
            '''"""Tests for failing_test_module."""
import pytest
from lib.test_scenarios.failing_test_module import add_numbers, divide_numbers

def test_add_numbers():
    """Test adding numbers."""
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0

def test_divide_numbers():
    """Test dividing numbers."""
    assert divide_numbers(10, 2) == 5
    assert divide_numbers(7, 3) == pytest.approx(2.333, rel=1e-2)

def test_failing_case():
    """This test intentionally fails."""
    assert add_numbers(2, 2) == 5  # This is wrong!

def test_divide_by_zero():
    """Test division by zero raises error."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide_numbers(10, 0)
'''
        )
        
        print(f"Created source file: {source_file}")
        print(f"Created test file: {test_file}")
        
        # Stage both files
        if not self.stage_file(source_file) or not self.stage_file(test_file):
            return False
            
        # Run the pre-commit hook (should fail)
        success, output = self.run_pre_commit_hook()
        
        print(f"Hook result: {'PASS' if success else 'FAIL (expected)'}")
        print("Hook output:")
        print(output)
        
        # This should fail because tests are failing
        return not success
    
    def test_scenario_3_low_coverage(self) -> bool:
        """Test scenario: Source file with low test coverage."""
        print("\n=== Test Scenario 3: Low Coverage ===")
        
        # Create a source file with multiple functions
        source_file = self.create_temp_file(
            "lib/test_scenarios/low_coverage_module.py",
            '''"""Module with low test coverage."""

def covered_function(x: int) -> int:
    """This function will be tested."""
    return x * 2

def uncovered_function_1(a: str, b: str) -> str:
    """This function will NOT be tested."""
    return f"{a} {b}".upper()

def uncovered_function_2(data: list) -> int:
    """This function will NOT be tested."""
    if not data:
        return 0
    return len([x for x in data if x > 0])

def uncovered_function_3(value: float) -> bool:
    """This function will NOT be tested."""
    return value > 10.0

class UncoveredClass:
    """This class will NOT be tested."""
    
    def __init__(self, name: str):
        self.name = name
    
    def get_name(self) -> str:
        return self.name.title()
    
    def process_data(self, items: list) -> dict:
        return {"count": len(items), "name": self.name}
'''
        )
        
        # Create a test file that only tests one function (low coverage)
        test_file = self.create_temp_file(
            "tests/lib/test_scenarios/test_low_coverage_module.py",
            '''"""Tests for low_coverage_module (only covers one function)."""
from lib.test_scenarios.low_coverage_module import covered_function

def test_covered_function():
    """Test the only function we cover."""
    assert covered_function(5) == 10
    assert covered_function(0) == 0
    assert covered_function(-3) == -6

# Note: We're not testing the other functions, resulting in low coverage
'''
        )
        
        print(f"Created source file: {source_file}")
        print(f"Created test file: {test_file}")
        
        # Stage both files
        if not self.stage_file(source_file) or not self.stage_file(test_file):
            return False
            
        # Run the pre-commit hook (should fail due to low coverage)
        success, output = self.run_pre_commit_hook()
        
        print(f"Hook result: {'PASS' if success else 'FAIL (expected)'}")
        print("Hook output:")
        print(output)
        
        # This should fail because coverage is below 50%
        return not success
    
    def test_scenario_4_good_coverage(self) -> bool:
        """Test scenario: Source file with good tests and coverage."""
        print("\n=== Test Scenario 4: Good Coverage ===")
        
        # Create a source file
        source_file = self.create_temp_file(
            "lib/test_scenarios/good_coverage_module.py",
            '''"""Module with good test coverage."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

def format_name(first: str, last: str) -> str:
    """Format a full name."""
    return f"{first.strip().title()} {last.strip().title()}"

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.last_result = 0
    
    def calculate(self, operation: str, a: int, b: int) -> int:
        """Perform a calculation."""
        if operation == "add":
            result = add(a, b)
        elif operation == "multiply":
            result = multiply(a, b)
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        self.last_result = result
        return result
    
    def get_last_result(self) -> int:
        """Get the last calculation result."""
        return self.last_result
'''
        )
        
        # Create a comprehensive test file
        test_file = self.create_temp_file(
            "tests/lib/test_scenarios/test_good_coverage_module.py",
            '''"""Comprehensive tests for good_coverage_module."""
import pytest
from lib.test_scenarios.good_coverage_module import add, multiply, format_name, Calculator

def test_add():
    """Test the add function."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_multiply():
    """Test the multiply function."""
    assert multiply(3, 4) == 12
    assert multiply(-2, 5) == -10
    assert multiply(0, 100) == 0

def test_format_name():
    """Test the format_name function."""
    assert format_name("john", "doe") == "John Doe"
    assert format_name("  alice  ", "  smith  ") == "Alice Smith"
    assert format_name("bob", "jones") == "Bob Jones"

class TestCalculator:
    """Test the Calculator class."""
    
    def test_init(self):
        """Test calculator initialization."""
        calc = Calculator()
        assert calc.last_result == 0
    
    def test_calculate_add(self):
        """Test calculator addition."""
        calc = Calculator()
        result = calc.calculate("add", 5, 3)
        assert result == 8
        assert calc.get_last_result() == 8
    
    def test_calculate_multiply(self):
        """Test calculator multiplication."""
        calc = Calculator()
        result = calc.calculate("multiply", 4, 6)
        assert result == 24
        assert calc.get_last_result() == 24
    
    def test_calculate_unknown_operation(self):
        """Test calculator with unknown operation."""
        calc = Calculator()
        with pytest.raises(ValueError, match="Unknown operation: divide"):
            calc.calculate("divide", 10, 2)
    
    def test_get_last_result(self):
        """Test getting last result."""
        calc = Calculator()
        calc.calculate("add", 10, 5)
        assert calc.get_last_result() == 15
        
        calc.calculate("multiply", 3, 3)
        assert calc.get_last_result() == 9
'''
        )
        
        print(f"Created source file: {source_file}")
        print(f"Created test file: {test_file}")
        
        # Stage both files
        if not self.stage_file(source_file) or not self.stage_file(test_file):
            return False
            
        # Run the pre-commit hook (should pass)
        success, output = self.run_pre_commit_hook()
        
        print(f"Hook result: {'PASS (expected)' if success else 'FAIL'}")
        print("Hook output:")
        print(output)
        
        # This should pass because tests pass and coverage is good
        return success
    
    def run_all_tests(self) -> bool:
        """Run all test scenarios."""
        print("=== Pre-commit Hook Test Suite ===")
        print(f"Project root: {self.project_root}")
        
        results = []
        
        try:
            # Test scenario 1: Missing test file
            results.append(("Missing Test File", self.test_scenario_1_missing_test_file()))
            self.cleanup()
            
            # Test scenario 2: Failing test
            results.append(("Failing Test", self.test_scenario_2_failing_test()))
            self.cleanup()
            
            # Test scenario 3: Low coverage  
            results.append(("Low Coverage", self.test_scenario_3_low_coverage()))
            self.cleanup()
            
            # Test scenario 4: Good coverage
            results.append(("Good Coverage", self.test_scenario_4_good_coverage()))
            self.cleanup()
            
        finally:
            # Always clean up
            self.cleanup()
        
        # Print summary
        print("\n=== Test Results Summary ===")
        all_passed = True
        for test_name, passed in results:
            status = "PASS" if passed else "FAIL"
            print(f"{test_name}: {status}")
            if not passed:
                all_passed = False
        
        print(f"\nOverall result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
        return all_passed


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test the Automagik Hive pre-commit hook system"
    )
    parser.add_argument(
        "--scenario",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run a specific test scenario (1-4)"
    )
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path.cwd()
    if not (project_root / "pyproject.toml").exists():
        print("ERROR: Not in an Automagik Hive project directory!")
        return 1
    
    # Initialize tester
    tester = PreCommitHookTester(project_root)
    
    try:
        if args.scenario:
            # Run specific scenario
            if args.scenario == 1:
                success = tester.test_scenario_1_missing_test_file()
            elif args.scenario == 2:
                success = tester.test_scenario_2_failing_test()
            elif args.scenario == 3:
                success = tester.test_scenario_3_low_coverage()
            elif args.scenario == 4:
                success = tester.test_scenario_4_good_coverage()
            else:
                print(f"Invalid scenario: {args.scenario}")
                return 1
                
            return 0 if success else 1
        else:
            # Run all tests
            success = tester.run_all_tests()
            return 0 if success else 1
            
    finally:
        tester.cleanup()


if __name__ == "__main__":
    exit(main())