#!/usr/bin/env python3
"""Test the TDD hook against our test structure."""

import sys
import json
from pathlib import Path

# Add .claude to path to import the validator
sys.path.insert(0, str(Path(__file__).parent.parent / '.claude'))
from tdd_hook import TDDValidator

def test_validator():
    """Test the TDD validator against our structure."""
    validator = TDDValidator()
    
    # Test cases for our structure
    test_cases = [
        # Source files that should have tests
        ("lib/utils/proxy_agents.py", "tests/lib/utils/test_proxy_agents.py"),
        ("api/serve.py", "tests/api/test_serve.py"),
        ("ai/agents/registry.py", "tests/ai/agents/test_registry.py"),
        
        # Integration tests (no source needed)
        ("tests/integration/api/test_e2e_integration.py", None),
        ("tests/integration/cli/test_cli_integration_comprehensive.py", None),
        
        # Fixture files (not test files)
        ("tests/fixtures/shared_fixtures.py", None),
    ]
    
    print("Testing TDD Validator against our structure:")
    print("=" * 60)
    
    for source_file, expected_test in test_cases:
        source_path = Path(source_file)
        
        if source_path.parts[0] == 'tests':
            # This is a test file
            expected_source = validator.get_expected_source_path(str(source_path))
            print(f"\nTest file: {source_file}")
            print(f"  Expected source: {expected_source}")
            
            # Validate the test file
            allowed, message = validator.validate_test_file(str(source_path))
            print(f"  Validation: {'✅ Allowed' if allowed else '❌ Blocked'}")
            if not allowed:
                print(f"  Message: {message}")
        else:
            # This is a source file
            calc_test = validator.get_expected_test_path(str(source_path))
            print(f"\nSource file: {source_file}")
            print(f"  Expected test: {calc_test}")
            print(f"  Actual test: {expected_test}")
            
            if calc_test:
                matches = str(calc_test) == expected_test
                print(f"  Match: {'✅' if matches else '❌'}")
    
    # Test validation of new file creation
    print("\n" + "=" * 60)
    print("Testing file creation validation:")
    print("=" * 60)
    
    # Try to create a source file without test
    new_source = "lib/utils/new_feature.py"
    allowed, message = validator.validate_source_file(new_source, "def hello(): pass")
    print(f"\nCreating {new_source} without test:")
    print(f"  Result: {'✅ Allowed' if allowed else '❌ Blocked'}")
    print(f"  Message: {message[:100]}...")
    
    # Try to create test in wrong location
    wrong_test = "lib/test_wrong_location.py"
    allowed, message = validator.validate_test_file(wrong_test)
    print(f"\nCreating test in wrong location ({wrong_test}):")
    print(f"  Result: {'✅ Allowed' if allowed else '❌ Blocked'}")
    print(f"  Message: {message[:100]}...")
    
    # Try to create test with wrong name
    wrong_name = "tests/lib/utils/wrong_name.py"
    allowed, message = validator.validate_test_file(wrong_name)
    print(f"\nCreating test with wrong name ({wrong_name}):")
    print(f"  Result: {'✅ Allowed' if allowed else '❌ Blocked'}")
    print(f"  Message: {message[:100]}...")
    
    # Test integration test detection
    print("\n" + "=" * 60)
    print("Testing integration test handling:")
    print("=" * 60)
    
    integration_tests = [
        "tests/integration/api/test_new_integration.py",
        "tests/fixtures/new_fixture.py",
        "tests/integration/e2e/test_end_to_end.py"
    ]
    
    for test_file in integration_tests:
        allowed, message = validator.validate_test_file(test_file)
        print(f"\nIntegration/fixture: {test_file}")
        print(f"  Result: {'✅ Allowed' if allowed else '❌ Blocked'}")
        
        # These should be allowed even without corresponding source
        expected_source = validator.get_expected_source_path(test_file)
        print(f"  Expected source: {expected_source}")
        if expected_source and not expected_source.exists():
            print(f"  Note: No source needed for integration tests")

if __name__ == "__main__":
    test_validator()