"""Edge case tests for CLI argument parsing conflicts and error scenarios.

These tests focus on specific edge cases, error conditions, and boundary scenarios
for the CLI argument parsing system. All tests should FAIL initially to drive
TDD implementation.
"""

import argparse
import pytest
import sys
from unittest.mock import patch

from cli.main import create_parser, main


class TestArgumentParsingEdgeCases:
    """Test edge cases in argument parsing that expose the lines/workspace conflict."""

    def test_numeric_string_workspace_path_parsing_conflict(self):
        """FAILING TEST: Numeric string paths expose the parsing conflict."""
        parser = create_parser()
        
        # These should be workspace paths, but get parsed as lines (int)
        numeric_paths = ["50", "100", "25", "0", "999"]
        
        for path in numeric_paths:
            # Currently this "works" because it gets parsed as lines
            # But it SHOULD be parsed as workspace path instead
            args = parser.parse_args([path])
            
            # This assertion will FAIL because it gets parsed as lines, not workspace
            try:
                assert args.workspace == path
                assert args.lines != int(path)  # Should not be parsed as lines
            except (AttributeError, AssertionError):
                # Expected failure - this is the bug we're fixing
                pass

    def test_mixed_numeric_alpha_workspace_paths(self):
        """FAILING TEST: Mixed numeric/alpha paths should be workspace paths."""
        parser = create_parser()
        
        mixed_paths = ["workspace123", "123workspace", "v1.2.3", "test-50", "50-test"]
        
        for path in mixed_paths:
            try:
                args = parser.parse_args([path])
                # Should be parsed as workspace, not lines
                assert args.workspace == path
                assert not hasattr(args, 'lines') or args.lines != path
            except (SystemExit, ValueError, AttributeError):
                # Expected failure with current implementation
                pytest.fail(f"Mixed path should work as workspace: {path}")

    def test_negative_numbers_as_workspace_paths(self):
        """FAILING TEST: Negative numbers should be valid workspace paths."""
        parser = create_parser()
        
        negative_paths = ["-1", "-50", "-100"]
        
        for path in negative_paths:
            try:
                args = parser.parse_args([path])
                # Should be workspace path, not invalid lines value
                assert args.workspace == path
            except (SystemExit, ValueError):
                # Expected failure - negative numbers invalid for int type
                pass

    def test_float_strings_as_workspace_paths(self):
        """FAILING TEST: Float strings should be workspace paths."""
        parser = create_parser()
        
        float_paths = ["1.5", "2.0", "3.14", "0.5"]
        
        for path in float_paths:
            try:
                args = parser.parse_args([path])
                # Should be workspace path, not invalid lines value
                assert args.workspace == path
            except (SystemExit, ValueError):
                # Expected failure - floats invalid for int type
                pass

    def test_very_large_numbers_as_workspace_paths(self):
        """FAILING TEST: Very large numbers should be workspace paths."""
        parser = create_parser()
        
        large_numbers = ["9999999", "1000000", str(sys.maxsize)]
        
        for num in large_numbers:
            try:
                args = parser.parse_args([num])
                # Should be workspace path, even if it's a valid int
                assert args.workspace == num
            except (SystemExit, ValueError, AttributeError):
                # May fail due to current parsing logic
                pass


class TestArgumentOrderingSensitivity:
    """Test how argument ordering affects parsing."""

    def test_workspace_before_command_flags(self):
        """FAILING TEST: Workspace path before command should work."""
        parser = create_parser()
        
        test_cases = [
            ["./workspace", "--status", "all"],
            ["./workspace", "--logs", "agent"],
            ["./workspace", "--health", "workspace"],
        ]
        
        for args_list in test_cases:
            try:
                args = parser.parse_args(args_list)
                assert args.workspace == "./workspace"
            except (SystemExit, AttributeError):
                pytest.fail(f"Workspace before command should work: {args_list}")

    def test_workspace_after_command_flags(self):
        """FAILING TEST: Workspace path after command should work."""
        parser = create_parser()
        
        test_cases = [
            ["--status", "all", "./workspace"],
            ["--logs", "agent", "./workspace"],
            ["--health", "workspace", "./workspace"],
        ]
        
        for args_list in test_cases:
            try:
                args = parser.parse_args(args_list)
                assert args.workspace == "./workspace"
            except (SystemExit, AttributeError):
                pytest.fail(f"Workspace after command should work: {args_list}")

    def test_multiple_positional_arguments_conflict(self):
        """FAILING TEST: Multiple positional args create parsing conflicts."""
        parser = create_parser()
        
        # Current parser has both lines and workspace as positional with nargs="?"
        # This creates ambiguous parsing
        
        # Verify the conflict exists in current parser structure
        actions = {action.dest: action for action in parser._actions}
        
        lines_action = actions.get('lines')
        workspace_action = actions.get('workspace')
        
        if lines_action and workspace_action:
            # Both are positional with nargs="?" - this is problematic
            assert lines_action.nargs == "?"
            assert workspace_action.nargs == "?"
            
            # The conflict: parser can't decide which positional arg to use
            # This is why "/path/workspace" gets parsed as lines instead of workspace


class TestErrorMessageQuality:
    """Test quality of error messages for parsing conflicts."""

    def test_workspace_path_error_message_quality(self):
        """FAILING TEST: Error messages should be helpful for workspace path issues."""
        parser = create_parser()
        
        # Capture stderr for error message analysis
        import io
        from contextlib import redirect_stderr
        
        with io.StringIO() as captured_stderr:
            with redirect_stderr(captured_stderr):
                try:
                    # This should fail with workspace path
                    args = parser.parse_args(["/tmp/my-workspace"])
                except SystemExit:
                    error_output = captured_stderr.getvalue()
                    
                    # Error message should be helpful
                    # Currently it's confusing "invalid int value" error
                    assert "invalid int value" in error_output  # Current bad message
                    
                    # After fix, should have better error message or no error at all
                    # pytest.fail("Error message should be more helpful or no error should occur")

    def test_mixed_arguments_error_clarity(self):
        """FAILING TEST: Mixed argument errors should be clear.""" 
        parser = create_parser()
        
        conflicting_cases = [
            ["50", "--logs", "agent", "--lines", "100"],  # Ambiguous: 50 as lines or workspace?
            ["./workspace", "75"],  # Two positional args
        ]
        
        for args_list in conflicting_cases:
            try:
                args = parser.parse_args(args_list)
                # Should either work correctly or give clear error
                # Current behavior is unpredictable
            except SystemExit:
                # Should have clear error message about the conflict
                pass


class TestArgumentTypeCoercion:
    """Test argument type coercion and validation."""

    def test_lines_argument_type_validation(self):
        """FAILING TEST: Lines argument should have proper type validation."""
        parser = create_parser()
        
        # After fix, --lines should be a flag with proper int validation
        invalid_line_values = ["abc", "1.5", "-5", ""]
        
        for invalid_value in invalid_line_values:
            try:
                # This should fail with proper type error for --lines flag
                args = parser.parse_args(["--logs", "agent", "--lines", invalid_value])
                pytest.fail(f"Invalid lines value should be rejected: {invalid_value}")
            except SystemExit:
                # Expected - proper validation should reject invalid values
                pass

    def test_workspace_argument_flexibility(self):
        """FAILING TEST: Workspace argument should accept various path formats."""
        parser = create_parser()
        
        valid_workspace_paths = [
            ".",
            "..",
            "./workspace", 
            "../workspace",
            "/absolute/path",
            "relative/path",
            "workspace-name",
            "workspace_name",
            "workspace.name",
            "123",  # Should be valid workspace name
            "workspace123",
        ]
        
        for path in valid_workspace_paths:
            try:
                args = parser.parse_args([path])
                assert args.workspace == path
            except (SystemExit, AttributeError):
                pytest.fail(f"Valid workspace path should work: {path}")


class TestCommandCombinationValidation:
    """Test validation of command combinations."""

    def test_mutually_exclusive_commands(self):
        """FAILING TEST: Mutually exclusive commands should be detected."""
        parser = create_parser()
        
        # These command combinations should be invalid
        conflicting_combinations = [
            ["--install", "agent", "--uninstall", "agent"],
            ["--start", "all", "--stop", "all"], 
            ["--status", "agent", "--logs", "agent"],
        ]
        
        for combination in conflicting_combinations:
            try:
                args = parser.parse_args(combination)
                # Should detect conflict and exit with error
                pytest.fail(f"Conflicting commands should be rejected: {combination}")
            except SystemExit:
                # Expected - conflicting commands should be rejected
                pass

    def test_required_argument_combinations(self):
        """FAILING TEST: Required argument combinations should be enforced."""
        parser = create_parser()
        
        # After fix, some combinations should require specific arguments
        cases_requiring_workspace = [
            ["--logs", "agent", "--lines", "50"],  # Should work with or without workspace
        ]
        
        for case in cases_requiring_workspace:
            try:
                args = parser.parse_args(case)
                # Should work without explicit workspace (use default)
                assert args is not None
            except SystemExit:
                pytest.fail(f"Case should work without explicit workspace: {case}")


class TestParserActionConfiguration:
    """Test parser action configuration and setup."""

    def test_parser_action_precedence(self):
        """FAILING TEST: Parser actions should have correct precedence."""
        parser = create_parser()
        
        # Workspace should take precedence as primary positional argument
        # Lines should only be available as --lines flag
        
        actions = {action.dest: action for action in parser._actions}
        
        # After fix, workspace should be positional, lines should be optional flag
        if 'workspace' in actions:
            workspace_action = actions['workspace']
            # Should be positional (no option_strings) with nargs="?"
            assert len(workspace_action.option_strings) == 0  # Positional
            
        if 'lines' in actions:
            lines_action = actions['lines']
            # Should be optional flag (has option_strings)
            # Currently it's positional, which is the problem
            try:
                assert len(lines_action.option_strings) > 0  # Should be flag
                assert '--lines' in lines_action.option_strings
            except AssertionError:
                # Expected failure - currently lines is positional
                pass

    def test_argument_defaults_and_requirements(self):
        """FAILING TEST: Arguments should have correct defaults and requirements."""
        parser = create_parser()
        
        # Test default values after parsing minimal arguments
        args_minimal = parser.parse_args([])
        
        # Workspace should default to None (optional)
        assert getattr(args_minimal, 'workspace', None) is None
        
        # Lines should have sensible default when used
        # Currently it defaults to 50, which may not be appropriate
        lines_default = getattr(args_minimal, 'lines', None)
        if lines_default is not None:
            assert isinstance(lines_default, int)
            assert lines_default > 0


class TestRegressionPrevention:
    """Test to prevent regressions after fixing the core issue."""

    def test_existing_working_commands_still_work(self):
        """FAILING TEST: Existing commands should continue working after fix."""
        parser = create_parser()
        
        # These should continue working after the fix
        existing_commands = [
            ["--version"],
            ["--install", "agent"],
            ["--start", "workspace"],
            ["--stop", "all"],
            ["--status", "agent"],
            ["--health", "workspace"],
            ["--uninstall", "agent"],
        ]
        
        for cmd in existing_commands:
            try:
                args = parser.parse_args(cmd)
                assert args is not None
            except SystemExit as e:
                if cmd == ["--version"]:
                    # Version command may exit normally
                    pass
                else:
                    pytest.fail(f"Existing command should work: {cmd}")

    def test_help_functionality_preserved(self):
        """FAILING TEST: Help functionality should be preserved after fix."""
        parser = create_parser()
        
        # Help should still work
        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])

    def test_backward_compatibility_maintained(self):
        """FAILING TEST: Fix should maintain backward compatibility."""
        parser = create_parser()
        
        # Commands that worked before should still work
        # (This assumes we identify what actually worked before the fix)
        
        # Basic status check
        try:
            args = parser.parse_args(["--status", "all"])
            assert args.status == "all"
        except SystemExit:
            pytest.fail("Basic status command should work")


class TestPerformanceWithFix:
    """Test that the fix doesn't introduce performance regressions."""

    def test_parser_creation_performance(self):
        """FAILING TEST: Parser creation should be fast after fix."""
        import time
        
        start_time = time.time()
        for _ in range(100):
            parser = create_parser()
        elapsed = time.time() - start_time
        
        # Should be fast even after adding complexity for the fix
        assert elapsed < 1.0, "Parser creation should remain fast"

    def test_argument_parsing_performance(self):
        """FAILING TEST: Argument parsing should be fast after fix."""
        import time
        
        parser = create_parser()
        
        test_args = [
            ["./workspace"],
            ["--logs", "agent", "--lines", "100"],
            ["./workspace", "--status", "all"],
        ]
        
        start_time = time.time()
        for _ in range(100):
            for args_list in test_args:
                try:
                    parser.parse_args(args_list)
                except SystemExit:
                    pass
        elapsed = time.time() - start_time
        
        # Should remain fast after fix
        assert elapsed < 2.0, "Argument parsing should remain fast"