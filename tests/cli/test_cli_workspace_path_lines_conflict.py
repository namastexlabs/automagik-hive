"""Comprehensive failing tests for CLI workspace path vs lines argument parsing conflict.

This test suite specifically targets the CLI argument parsing issue where workspace paths
get incorrectly parsed as the lines (int) argument, causing the CLI to fail with 
"invalid int value" errors.

Current Issue:
- `uv run automagik-hive /path/to/workspace` fails with "invalid int value"
- Workspace path gets parsed as lines argument (expecting int) 
- Need to fix so workspace path is primary positional argument
- Lines should be --lines flag for --logs command only

These tests MUST FAIL FIRST to drive TDD implementation.
"""

import argparse
import pytest
import sys
from io import StringIO
from unittest.mock import Mock, patch

from cli.main import create_parser, main


class TestWorkspacePathVsLinesConflict:
    """Test the core conflict between workspace path and lines arguments."""

    def test_workspace_path_parsed_as_lines_fails_currently(self):
        """FAILING TEST: Workspace path incorrectly parsed as lines argument."""
        parser = create_parser()
        
        # This should work but currently fails because "/tmp/workspace" 
        # gets parsed as the lines argument (expecting int)
        with pytest.raises(SystemExit):  # argparse exits on type error
            args = parser.parse_args(["/tmp/workspace"])
        
        # This test documents the current broken behavior
        # After fix, this test should be updated to expect success

    def test_workspace_path_with_numbers_fails_currently(self):
        """FAILING TEST: Numeric workspace path incorrectly parsed as lines."""
        parser = create_parser()
        
        # Path like "/workspace123" should be workspace, not lines
        with pytest.raises(SystemExit):  # argparse exits on type error
            args = parser.parse_args(["/workspace123"])

    def test_absolute_workspace_path_fails_currently(self):
        """FAILING TEST: Absolute paths fail due to lines parsing."""
        parser = create_parser()
        
        # Absolute paths should work as workspace argument
        test_paths = [
            "/home/user/workspace",
            "/tmp/test-workspace", 
            "/var/lib/workspace",
            "C:\\Users\\workspace",  # Windows path
        ]
        
        for path in test_paths:
            with pytest.raises(SystemExit):  # Currently fails
                args = parser.parse_args([path])

    def test_relative_workspace_path_fails_currently(self):
        """FAILING TEST: Relative paths fail due to lines parsing.""" 
        parser = create_parser()
        
        # Relative paths should work as workspace argument
        test_paths = [
            "./workspace",
            "../workspace", 
            "my-workspace",
            "workspace-123",
        ]
        
        for path in test_paths:
            with pytest.raises(SystemExit):  # Currently fails
                args = parser.parse_args([path])


class TestExpectedWorkspaceBehaviorAfterFix:
    """Test expected behavior after fixing workspace path parsing."""

    def test_workspace_path_should_be_primary_positional_argument(self):
        """FAILING TEST: Workspace path should be primary positional arg."""
        parser = create_parser()
        
        # After fix, this should work
        # Currently fails because lines argument takes precedence
        try:
            args = parser.parse_args(["./test-workspace"])
            assert args.workspace == "./test-workspace"
            assert args.lines == 50  # lines should have default value, not be parsed from input
        except (SystemExit, AttributeError):
            pytest.fail("Workspace path should be primary positional argument")

    def test_lines_should_only_exist_with_logs_flag(self):
        """FAILING TEST: Lines should only be available with --logs commands."""
        parser = create_parser()
        
        # After fix, lines should be --lines flag, not positional argument
        try:
            args = parser.parse_args(["--logs", "agent", "--lines", "100"])
            assert args.lines == 100
        except (SystemExit, AttributeError):
            pytest.fail("--lines flag should work with --logs commands")

    def test_workspace_with_logs_command_should_work(self):
        """FAILING TEST: Should handle workspace + logs command properly."""
        parser = create_parser()
        
        # After fix, should be able to specify workspace and lines separately
        try:
            args = parser.parse_args(["./workspace", "--logs", "agent", "--lines", "50"])
            assert args.workspace == "./workspace"
            assert args.lines == 50
        except (SystemExit, AttributeError):
            pytest.fail("Should handle workspace and logs separately")


class TestCLIIntegrationWithWorkspacePaths:
    """Test CLI integration scenarios with workspace paths."""

    @patch('cli.main.DockerManager')
    @patch('cli.main.WorkspaceManager')
    def test_cli_main_with_workspace_path_fails_currently(self, mock_workspace_mgr, mock_docker):
        """FAILING TEST: CLI main function fails with workspace path."""
        mock_workspace_mgr.return_value.start_server.return_value = True
        
        # Mock sys.argv to simulate command line invocation
        with patch.object(sys, 'argv', ['automagik-hive', '/tmp/test-workspace']):
            # Currently fails because workspace path gets parsed as lines
            with pytest.raises((SystemExit, ValueError)):
                result = main()

    @patch('cli.main.DockerManager') 
    @patch('cli.main.WorkspaceManager')
    def test_cli_main_with_workspace_should_call_workspace_manager(self, mock_workspace_mgr, mock_docker):
        """FAILING TEST: Should call workspace manager when workspace path provided."""
        mock_workspace_instance = mock_workspace_mgr.return_value
        mock_workspace_instance.start_server.return_value = True
        
        # After fix, this should work
        with patch.object(sys, 'argv', ['automagik-hive', './test-workspace']):
            try:
                result = main()
                # Should call workspace manager with the path
                mock_workspace_instance.start_server.assert_called_once_with('./test-workspace')
                assert result == 0
            except (SystemExit, ValueError):
                pytest.fail("Should successfully handle workspace path")

    @patch('cli.main.DockerManager')
    def test_cli_logs_command_with_lines_should_work(self, mock_docker):
        """FAILING TEST: Logs command with --lines flag should work."""
        mock_docker_instance = mock_docker.return_value
        
        # After fix, this should work
        with patch.object(sys, 'argv', ['automagik-hive', '--logs', 'agent', '--lines', '75']):
            try:
                result = main()
                # Should call logs with correct line count
                mock_docker_instance.logs.assert_called_once_with('agent', 75)
                assert result == 0
            except (SystemExit, AttributeError):
                pytest.fail("Should handle --logs command with --lines flag")


class TestEdgeCasesWorkspacePathParsing:
    """Test edge cases for workspace path parsing."""

    def test_workspace_path_that_looks_like_number_fails_currently(self):
        """FAILING TEST: Workspace path that looks like number should work."""
        parser = create_parser()
        
        # Paths like "123" or "50" should be workspace paths, not lines
        numeric_looking_paths = ["123", "50", "100"]
        
        for path in numeric_looking_paths:
            with pytest.raises(SystemExit):  # Currently fails
                args = parser.parse_args([path])

    def test_empty_workspace_path_should_be_handled(self):
        """FAILING TEST: Empty workspace path should be handled gracefully."""
        parser = create_parser()
        
        # Empty string should be valid workspace path (current directory)
        try:
            args = parser.parse_args([""])
            assert args.workspace == ""
        except (SystemExit, AttributeError):
            pytest.fail("Empty workspace path should be handled")

    def test_special_characters_in_workspace_path(self):
        """FAILING TEST: Special characters in workspace path should work."""
        parser = create_parser()
        
        special_paths = [
            "./workspace-with-dashes",
            "./workspace_with_underscores", 
            "./workspace.with.dots",
            "./workspace with spaces",  # Might need quoting
        ]
        
        for path in special_paths:
            try:
                args = parser.parse_args([path])
                assert args.workspace == path
            except (SystemExit, AttributeError):
                pytest.fail(f"Special character path should work: {path}")

    def test_mixed_workspace_and_command_arguments_order(self):
        """FAILING TEST: Mixed argument order should work consistently."""
        parser = create_parser()
        
        # After fix, these should all work regardless of order
        test_cases = [
            (["./workspace", "--status", "agent"], "./workspace"),
            (["--status", "agent", "./workspace"], "./workspace"),
            (["./workspace", "--logs", "agent", "--lines", "100"], "./workspace"),
        ]
        
        for args_list, expected_workspace in test_cases:
            try:
                args = parser.parse_args(args_list)
                assert args.workspace == expected_workspace
            except (SystemExit, AttributeError):
                pytest.fail(f"Mixed argument order should work: {args_list}")


class TestCurrentBrokenBehaviorDocumentation:
    """Document the current broken behavior for reference."""

    def test_lines_positional_argument_exists_currently(self):
        """DOCUMENT: Current parser has lines as positional argument."""
        parser = create_parser()
        
        # This test documents current state - lines is positional
        args = parser.parse_args(["50"])  # This works - parsed as lines
        assert args.lines == 50
        # But this breaks workspace functionality

    def test_workspace_positional_argument_exists_currently(self):
        """DOCUMENT: Current parser has workspace as positional argument.""" 
        parser = create_parser()
        
        # This test documents current state - both exist as positional
        # This is the root cause of the conflict
        # Parser has both lines (nargs="?", type=int) and workspace (nargs="?") 
        # which creates ambiguous parsing
        
        # Check parser structure
        actions = {action.dest: action for action in parser._actions}
        assert 'lines' in actions
        assert 'workspace' in actions
        
        # Both are positional arguments with nargs="?" - this is the problem!
        lines_action = actions['lines']
        workspace_action = actions['workspace']
        
        assert lines_action.nargs == "?"
        assert workspace_action.nargs == "?" 
        # This creates the conflict - parser doesn't know which one to use


class TestProposedFixValidation:
    """Test validation scenarios for the proposed fix."""

    def test_proposed_fix_workspace_primary_lines_flag(self):
        """FAILING TEST: Validate proposed fix design."""
        # This test validates the proposed solution:
        # 1. workspace should be primary positional argument
        # 2. lines should be --lines flag for --logs command only
        
        # After implementing the fix, parser should work like this:
        parser = create_parser()
        
        try:
            # Primary use case: workspace path
            args1 = parser.parse_args(["./my-workspace"])
            assert args1.workspace == "./my-workspace"
            assert not hasattr(args1, 'lines') or args1.lines is None
            
            # Logs command with lines flag
            args2 = parser.parse_args(["--logs", "agent", "--lines", "100"])
            assert args2.logs == "agent"
            assert args2.lines == 100
            assert args2.workspace is None
            
            # Combined workspace + logs command
            args3 = parser.parse_args(["./workspace", "--logs", "agent", "--lines", "75"])
            assert args3.workspace == "./workspace"
            assert args3.logs == "agent"  
            assert args3.lines == 75
            
        except (SystemExit, AttributeError, AssertionError):
            pytest.fail("Proposed fix should enable these usage patterns")

    def test_backward_compatibility_after_fix(self):
        """FAILING TEST: Ensure backward compatibility is maintained."""
        parser = create_parser()
        
        # Existing commands should still work after fix
        backward_compatible_cases = [
            ["--install", "agent"],
            ["--start", "workspace"],
            ["--stop", "all"],
            ["--status", "agent"],
            ["--health", "workspace"],
            ["--version"],
        ]
        
        for case in backward_compatible_cases:
            try:
                args = parser.parse_args(case)
                # Should parse without errors
                assert args is not None
            except SystemExit:
                pytest.fail(f"Backward compatibility broken for: {case}")


class TestRealWorldUsageScenariosAfterFix:
    """Test real-world usage scenarios that should work after fix."""

    def test_typical_workspace_startup_scenario(self):
        """FAILING TEST: Typical workspace startup should work."""
        # Real command: uv run automagik-hive /tmp/my-workspace
        parser = create_parser()
        
        try:
            args = parser.parse_args(["/tmp/my-workspace"])
            assert args.workspace == "/tmp/my-workspace"
        except SystemExit:
            pytest.fail("Basic workspace startup should work")

    def test_logs_with_custom_lines_scenario(self):
        """FAILING TEST: Logs with custom line count should work."""
        # Real command: uv run automagik-hive --logs agent --lines 200
        parser = create_parser()
        
        try:
            args = parser.parse_args(["--logs", "agent", "--lines", "200"])
            assert args.logs == "agent"
            assert args.lines == 200
        except SystemExit:
            pytest.fail("Logs with custom lines should work")

    def test_workspace_status_check_scenario(self):
        """FAILING TEST: Workspace status check should work."""
        # Real command: uv run automagik-hive ./my-workspace --status all
        parser = create_parser()
        
        try:
            args = parser.parse_args(["./my-workspace", "--status", "all"])
            assert args.workspace == "./my-workspace"
            assert args.status == "all"
        except SystemExit:
            pytest.fail("Workspace with status check should work")

    def test_help_and_version_still_work(self):
        """FAILING TEST: Help and version should still work after fix.""" 
        parser = create_parser()
        
        # Test --help raises SystemExit
        with pytest.raises(SystemExit):  # Expected for help
            parser.parse_args(["--help"])
            
        # Test --version can be parsed (it just sets a flag, doesn't exit)
        args = parser.parse_args(["--version"])
        assert args.version is True


# Integration test to validate the entire fix
class TestCLIWorkspacePathFixIntegration:
    """Integration tests to validate the complete fix."""
    
    @patch('pathlib.Path.exists')
    @patch('cli.main.WorkspaceManager')
    @patch('cli.main.DockerManager')
    def test_end_to_end_workspace_startup_after_fix(self, mock_docker, mock_workspace, mock_path_exists):
        """FAILING TEST: End-to-end workspace startup should work after fix."""
        # Setup mocks
        mock_path_exists.return_value = True
        mock_workspace_instance = mock_workspace.return_value
        mock_workspace_instance.start_server.return_value = True
        
        # Test the actual command that fails currently
        with patch.object(sys, 'argv', ['automagik-hive', '/tmp/test-workspace']):
            try:
                result = main()
                assert result == 0
                mock_workspace_instance.start_server.assert_called_once_with('/tmp/test-workspace')
            except (SystemExit, ValueError):
                pytest.fail("End-to-end workspace startup should work after fix")

    @patch('cli.main.DockerManager')
    def test_end_to_end_logs_with_lines_after_fix(self, mock_docker):
        """FAILING TEST: End-to-end logs with lines should work after fix."""
        mock_docker_instance = mock_docker.return_value
        
        # Test logs command with --lines flag
        with patch.object(sys, 'argv', ['automagik-hive', '--logs', 'agent', '--lines', '150']):
            try:
                result = main()
                assert result == 0
                mock_docker_instance.logs.assert_called_once_with('agent', 150)
            except (SystemExit, AttributeError):
                pytest.fail("End-to-end logs with lines should work after fix")