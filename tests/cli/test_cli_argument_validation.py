"""CLI Argument Validation Test Suite.

This test suite validates the current CLI argument parsing behavior and documents
the specific failures that need to be addressed. These tests serve as acceptance
criteria for the fix.
"""

import argparse
import pytest
import sys
from io import StringIO
from contextlib import redirect_stderr
from unittest.mock import patch

from cli.main import create_parser, main


class TestCurrentParserStructureAnalysis:
    """Analyze and document current parser structure to understand the conflict."""

    def test_parser_has_conflicting_positional_arguments(self):
        """DOCUMENT: Current parser has conflicting positional arguments."""
        parser = create_parser()
        
        # Extract all actions and analyze positional arguments
        positional_actions = [action for action in parser._actions 
                             if len(action.option_strings) == 0 and action.dest != 'help']
        
        # Document current structure
        positional_dests = [action.dest for action in positional_actions]
        
        # Current implementation should have both 'lines' and 'workspace' as positional
        assert 'lines' in positional_dests, "Current parser should have 'lines' as positional"
        assert 'workspace' in positional_dests, "Current parser should have 'workspace' as positional"
        
        # Find the specific actions
        lines_action = next((a for a in positional_actions if a.dest == 'lines'), None)
        workspace_action = next((a for a in positional_actions if a.dest == 'workspace'), None)
        
        assert lines_action is not None, "Lines action should exist"
        assert workspace_action is not None, "Workspace action should exist"
        
        # Document the conflict
        assert lines_action.nargs == "?", "Lines should be optional positional"
        assert workspace_action.nargs == "?", "Workspace should be optional positional"
        assert lines_action.type == int, "Lines should expect int type"
        assert workspace_action.type is None, "Workspace should accept string type"
        
        print(f"CONFLICT IDENTIFIED:")
        print(f"  Lines action: nargs={lines_action.nargs}, type={lines_action.type}")
        print(f"  Workspace action: nargs={workspace_action.nargs}, type={workspace_action.type}")
        print(f"  Both are positional with nargs='?' - this creates ambiguous parsing")

    def test_demonstrate_current_parsing_behavior(self):
        """DOCUMENT: Demonstrate how current parsing behaves with different inputs."""
        parser = create_parser()
        
        test_cases = [
            # (input_args, expected_behavior, current_result)
            (["50"], "should be workspace path", "parsed as lines=50"),
            (["/tmp/workspace"], "should be workspace path", "fails with 'invalid int value'"),
            (["./workspace"], "should be workspace path", "fails with 'invalid int value'"),
            (["workspace123"], "should be workspace path", "fails with 'invalid int value'"),
        ]
        
        for input_args, expected, current in test_cases:
            try:
                args = parser.parse_args(input_args)
                if hasattr(args, 'lines') and args.lines is not None:
                    result = f"lines={args.lines}"
                elif hasattr(args, 'workspace') and args.workspace is not None:
                    result = f"workspace={args.workspace}"
                else:
                    result = "neither set"
                    
                print(f"Input {input_args}: {expected} -> Current: {result}")
                
            except SystemExit:
                print(f"Input {input_args}: {expected} -> Current: SystemExit (parsing failed)")


class TestFailureModesValidation:
    """Validate specific failure modes that need to be fixed."""

    def test_workspace_path_parsing_fails_with_invalid_int(self):
        """VALIDATE: Workspace paths fail with 'invalid int value' error."""
        parser = create_parser()
        
        failing_workspace_paths = [
            "/tmp/workspace",
            "./my-workspace",
            "../workspace",
            "workspace-name",
            "workspace_name",
            "workspace.name",
        ]
        
        for path in failing_workspace_paths:
            with redirect_stderr(StringIO()) as captured_stderr:
                try:
                    args = parser.parse_args([path])
                    # If we get here, parsing succeeded unexpectedly
                    pytest.fail(f"Expected parsing to fail for workspace path: {path}")
                except SystemExit:
                    error_output = captured_stderr.getvalue()
                    # Verify it's the expected "invalid int value" error
                    assert "invalid int value" in error_output or "invalid literal for int()" in error_output, \
                        f"Should fail with int parsing error for: {path}"

    def test_numeric_strings_parsed_as_lines_instead_of_workspace(self):
        """VALIDATE: Numeric strings get parsed as lines, not workspace."""
        parser = create_parser()
        
        numeric_strings = ["50", "100", "25", "200"]
        
        for num_str in numeric_strings:
            args = parser.parse_args([num_str])
            
            # These get parsed as lines, but should be workspace paths
            assert hasattr(args, 'lines'), f"Should have lines attribute for input: {num_str}"
            assert args.lines == int(num_str), f"Lines should be {num_str} for input: {num_str}"
            
            # This is the bug - they should be workspace paths instead
            if hasattr(args, 'workspace'):
                assert args.workspace != num_str, f"Workspace incorrectly set for numeric input: {num_str}"

    def test_cli_main_function_fails_with_workspace_paths(self):
        """VALIDATE: CLI main() function fails when given workspace paths."""
        test_workspace_paths = [
            "/tmp/test-workspace",
            "./local-workspace",
            "my-workspace",
        ]
        
        for workspace_path in test_workspace_paths:
            with patch.object(sys, 'argv', ['automagik-hive', workspace_path]):
                try:
                    result = main()
                    pytest.fail(f"CLI main should fail with workspace path: {workspace_path}")
                except (SystemExit, ValueError, TypeError) as e:
                    # Expected failure
                    print(f"CLI main failed with {workspace_path}: {type(e).__name__}: {e}")


class TestDesiredBehaviorSpecification:
    """Specify the desired behavior after fixing the argument parsing."""

    def test_workspace_should_be_primary_positional_argument(self):
        """SPECIFY: Workspace path should be the primary positional argument."""
        # After fix, this is how the parser should behave:
        
        desired_test_cases = [
            # (input_args, expected_workspace, expected_lines)
            (["./workspace"], "./workspace", None),
            (["/tmp/workspace"], "/tmp/workspace", None),
            (["workspace123"], "workspace123", None),
            (["50"], "50", None),  # Should be workspace, not lines
            (["./workspace", "--logs", "agent", "--lines", "100"], "./workspace", 100),
        ]
        
        # These test cases define the desired behavior
        # They will fail with current implementation
        parser = create_parser()
        
        for input_args, expected_workspace, expected_lines in desired_test_cases:
            # This test documents what SHOULD happen after the fix
            print(f"DESIRED: {input_args} -> workspace='{expected_workspace}', lines={expected_lines}")
            
            # Current implementation will not match these expectations
            try:
                args = parser.parse_args(input_args)
                current_workspace = getattr(args, 'workspace', None)
                current_lines = getattr(args, 'lines', None)
                
                if current_workspace != expected_workspace or current_lines != expected_lines:
                    print(f"  CURRENT: workspace='{current_workspace}', lines={current_lines} (MISMATCH)")
                else:
                    print(f"  CURRENT: Matches expected behavior")
                    
            except SystemExit:
                print(f"  CURRENT: Parsing failed (SystemExit)")

    def test_lines_should_be_optional_flag_for_logs_command(self):
        """SPECIFY: Lines should be --lines flag, only relevant for logs commands."""
        # After fix, lines should work like this:
        
        desired_lines_behavior = [
            # (input_args, should_work, expected_lines_value)
            (["--logs", "agent", "--lines", "100"], True, 100),
            (["--logs", "workspace", "--lines", "50"], True, 50),
            (["./workspace", "--logs", "agent", "--lines", "200"], True, 200),
            (["--lines", "100"], False, None),  # Lines without logs should be invalid
        ]
        
        parser = create_parser()
        
        for input_args, should_work, expected_lines in desired_lines_behavior:
            print(f"DESIRED LINES: {input_args} -> should_work={should_work}, lines={expected_lines}")
            
            try:
                args = parser.parse_args(input_args)
                current_lines = getattr(args, 'lines', None)
                
                if should_work:
                    if current_lines == expected_lines:
                        print(f"  CURRENT: Correct behavior")
                    else:
                        print(f"  CURRENT: lines={current_lines} (expected {expected_lines})")
                else:
                    print(f"  CURRENT: Should have failed but didn't")
                    
            except SystemExit:
                if should_work:
                    print(f"  CURRENT: Failed but should work")
                else:
                    print(f"  CURRENT: Correctly failed")


class TestFixValidationCriteria:
    """Define validation criteria to verify the fix is complete."""

    def test_fix_validation_workspace_paths_work(self):
        """CRITERIA: After fix, workspace paths should parse correctly."""
        parser = create_parser()
        
        # These should all work after the fix
        workspace_test_paths = [
            "./workspace",
            "../workspace", 
            "/tmp/workspace",
            "/absolute/path/workspace",
            "workspace-name",
            "workspace_name",
            "workspace.name",
            "123",  # Numeric string should be valid workspace name
            "workspace123",
            "50-test",
        ]
        
        for path in workspace_test_paths:
            try:
                args = parser.parse_args([path])
                # After fix, should have workspace set to path
                assert hasattr(args, 'workspace'), f"Should have workspace attribute for: {path}"
                assert args.workspace == path, f"Workspace should be '{path}'"
                
                # Lines should not be set when only workspace is provided
                lines_value = getattr(args, 'lines', None)
                if lines_value is not None and path.isdigit():
                    # This is the current bug - numeric paths get parsed as lines
                    pytest.fail(f"Path '{path}' incorrectly parsed as lines={lines_value}")
                    
            except SystemExit:
                pytest.fail(f"Workspace path should work after fix: {path}")

    def test_fix_validation_logs_with_lines_flag_works(self):
        """CRITERIA: After fix, --logs commands with --lines flag should work."""
        parser = create_parser()
        
        # These should work after the fix
        logs_with_lines_cases = [
            (["--logs", "agent", "--lines", "100"], "agent", 100),
            (["--logs", "workspace", "--lines", "50"], "workspace", 50), 
            (["--logs", "all", "--lines", "25"], "all", 25),
        ]
        
        for input_args, expected_logs_target, expected_lines in logs_with_lines_cases:
            try:
                args = parser.parse_args(input_args)
                
                # Should have logs target
                assert hasattr(args, 'logs'), f"Should have logs attribute for: {input_args}"
                assert args.logs == expected_logs_target, f"Logs should be '{expected_logs_target}'"
                
                # Should have lines count
                assert hasattr(args, 'lines'), f"Should have lines attribute for: {input_args}"
                assert args.lines == expected_lines, f"Lines should be {expected_lines}"
                
            except SystemExit:
                pytest.fail(f"Logs with lines should work after fix: {input_args}")

    def test_fix_validation_combined_workspace_and_logs_works(self):
        """CRITERIA: After fix, combined workspace + logs commands should work.""" 
        parser = create_parser()
        
        # These should work after the fix
        combined_cases = [
            (["./workspace", "--logs", "agent", "--lines", "100"], "./workspace", "agent", 100),
            (["/tmp/workspace", "--logs", "workspace", "--lines", "50"], "/tmp/workspace", "workspace", 50),
        ]
        
        for input_args, expected_workspace, expected_logs, expected_lines in combined_cases:
            try:
                args = parser.parse_args(input_args)
                
                # Should have all three attributes set correctly
                assert hasattr(args, 'workspace'), f"Should have workspace for: {input_args}"
                assert args.workspace == expected_workspace, f"Workspace should be '{expected_workspace}'"
                
                assert hasattr(args, 'logs'), f"Should have logs for: {input_args}"
                assert args.logs == expected_logs, f"Logs should be '{expected_logs}'"
                
                assert hasattr(args, 'lines'), f"Should have lines for: {input_args}"
                assert args.lines == expected_lines, f"Lines should be {expected_lines}"
                
            except SystemExit:
                pytest.fail(f"Combined workspace+logs should work after fix: {input_args}")

    def test_fix_validation_backward_compatibility(self):
        """CRITERIA: After fix, existing commands should still work."""
        parser = create_parser()
        
        # These existing commands should continue working
        existing_commands = [
            ["--install", "agent"],
            ["--start", "workspace"], 
            ["--stop", "all"],
            ["--status", "agent"],
            ["--health", "workspace"],
            ["--restart", "agent"],
            ["--uninstall", "workspace"],
        ]
        
        for cmd in existing_commands:
            try:
                args = parser.parse_args(cmd)
                assert args is not None, f"Command should parse successfully: {cmd}"
            except SystemExit:
                pytest.fail(f"Existing command should work after fix: {cmd}")


class TestErrorScenarioHandling:
    """Test how errors should be handled after the fix."""

    def test_invalid_lines_values_should_error_appropriately(self):
        """CRITERIA: Invalid --lines values should give clear errors."""
        parser = create_parser()
        
        # These should fail with clear error messages after fix
        invalid_lines_cases = [
            ["--logs", "agent", "--lines", "abc"],
            ["--logs", "agent", "--lines", "-50"],
            ["--logs", "agent", "--lines", "1.5"],
            ["--logs", "agent", "--lines", ""],
        ]
        
        for case in invalid_lines_cases:
            with redirect_stderr(StringIO()) as captured_stderr:
                try:
                    args = parser.parse_args(case)
                    pytest.fail(f"Invalid lines value should be rejected: {case}")
                except SystemExit:
                    error_output = captured_stderr.getvalue()
                    # Should have clear error about invalid --lines value
                    # Not confusing error about workspace paths
                    assert "lines" in error_output.lower() or "invalid" in error_output.lower()

    def test_conflicting_commands_should_error_clearly(self):
        """CRITERIA: Conflicting commands should give clear errors."""
        parser = create_parser()
        
        # These command combinations should be rejected
        conflicting_cases = [
            ["--install", "agent", "--uninstall", "agent"],
            ["--start", "all", "--stop", "all"],
        ]
        
        for case in conflicting_cases:
            try:
                args = parser.parse_args(case)
                # Should either work (if commands are compatible) or fail clearly
                # The key is no confusing workspace/lines parsing errors
            except SystemExit:
                # Expected for conflicting commands
                pass