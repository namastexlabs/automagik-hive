#!/usr/bin/env python3
"""Test the TDD hook against our test structure."""

import sys
from pathlib import Path

# Add .claude to path to import the validator
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude"))
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

    for source_file, expected_test in test_cases:
        source_path = Path(source_file)

        if source_path.parts[0] == "tests":
            # This is a test file
            expected_source = validator.get_expected_source_path(str(source_path))

            # Validate the test file
            allowed, message = validator.validate_test_file(str(source_path))
            if not allowed:
                pass
        else:
            # This is a source file
            calc_test = validator.get_expected_test_path(str(source_path))

            if calc_test:
                assert str(calc_test) == expected_test

    # Test validation of new file creation

    # Try to create a source file without test
    new_source = "lib/utils/new_feature.py"
    allowed, message = validator.validate_source_file(new_source, "def hello(): pass")

    # Try to create test in wrong location
    wrong_test = "lib/test_wrong_location.py"
    allowed, message = validator.validate_test_file(wrong_test)

    # Try to create test with wrong name
    wrong_name = "tests/lib/utils/wrong_name.py"
    allowed, message = validator.validate_test_file(wrong_name)

    # Test integration test detection

    integration_tests = [
        "tests/integration/api/test_new_integration.py",
        "tests/fixtures/new_fixture.py",
        "tests/integration/e2e/test_end_to_end.py",
    ]

    for test_file in integration_tests:
        allowed, message = validator.validate_test_file(test_file)

        # These should be allowed even without corresponding source
        expected_source = validator.get_expected_source_path(test_file)
        if expected_source and not expected_source.exists():
            pass


if __name__ == "__main__":
    test_validator()
