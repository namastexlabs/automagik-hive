"""Comprehensive tests for cli.utils module.

These tests provide extensive coverage for CLI utility functions including
command execution, Docker validation, status formatting, and user interaction.
All tests are designed with RED phase compliance for TDD workflow.
"""

import pytest
import subprocess
from unittest.mock import MagicMock, Mock, patch, call
from io import StringIO

from cli.utils import (
    run_command,
    check_docker_available,
    format_status,
    confirm_action,
)


class TestRunCommand:
    """Test run_command function for subprocess execution."""

    def test_run_command_success_without_capture(self):
        """Test successful command execution without output capture."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            result = run_command(["echo", "test"], capture_output=False)
            
            assert result is None
            mock_run.assert_called_once_with(["echo", "test"], check=True, cwd=None)

    def test_run_command_success_with_capture(self):
        """Test successful command execution with output capture."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "command output\n"
            mock_run.return_value.returncode = 0
            
            result = run_command(["echo", "test"], capture_output=True)
            
            assert result == "command output"
            mock_run.assert_called_once_with(
                ["echo", "test"], capture_output=True, text=True, check=True, cwd=None
            )

    def test_run_command_with_working_directory(self):
        """Test command execution with specified working directory."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "output"
            
            result = run_command(["ls"], capture_output=True, cwd="/tmp")
            
            assert result == "output"
            mock_run.assert_called_once_with(
                ["ls"], capture_output=True, text=True, check=True, cwd="/tmp"
            )

    def test_run_command_called_process_error_with_capture(self):
        """Test command execution handles CalledProcessError with output capture."""
        error = subprocess.CalledProcessError(1, ["false"], stderr="error message")
        
        with patch('subprocess.run', side_effect=error), \
             patch('builtins.print') as mock_print:
            
            result = run_command(["false"], capture_output=True)
            
            assert result is None
            # Verify error message is printed
            mock_print.assert_any_call("❌ Command failed: false")
            mock_print.assert_any_call("Error: error message")

    def test_run_command_called_process_error_without_capture(self):
        """Test command execution handles CalledProcessError without output capture."""
        error = subprocess.CalledProcessError(1, ["false"])
        
        with patch('subprocess.run', side_effect=error):
            result = run_command(["false"], capture_output=False)
            
            assert result is None

    def test_run_command_file_not_found_error(self):
        """Test command execution handles FileNotFoundError for missing commands."""
        with patch('subprocess.run', side_effect=FileNotFoundError()), \
             patch('builtins.print') as mock_print:
            
            result = run_command(["nonexistent_command"], capture_output=True)
            
            assert result is None
            mock_print.assert_called_once_with("❌ Command not found: nonexistent_command")

    def test_run_command_timeout_error(self):
        """Test command execution handles timeout scenarios."""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired(["sleep", "10"], 5)):
            result = run_command(["sleep", "10"], capture_output=True)
            
            assert result is None

    def test_run_command_permission_error(self):
        """Test command execution handles permission errors."""
        with patch('subprocess.run', side_effect=PermissionError("Permission denied")):
            result = run_command(["restricted_command"], capture_output=True)
            
            assert result is None

    def test_run_command_unicode_output(self):
        """Test command execution handles Unicode output correctly."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "Hello 世界\n"
            
            result = run_command(["echo", "Hello 世界"], capture_output=True)
            
            assert result == "Hello 世界"

    def test_run_command_empty_output(self):
        """Test command execution handles empty output."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = ""
            
            result = run_command(["echo"], capture_output=True)
            
            assert result == ""

    def test_run_command_multiline_output(self):
        """Test command execution handles multiline output with proper stripping."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "line1\nline2\nline3\n"
            
            result = run_command(["echo", "multiline"], capture_output=True)
            
            assert result == "line1\nline2\nline3"


class TestCheckDockerAvailable:
    """Test check_docker_available function for Docker validation."""

    def test_check_docker_available_success(self):
        """Test Docker availability check when Docker is available and running."""
        with patch('cli.utils.run_command') as mock_run:
            mock_run.side_effect = ["Docker version 20.10.0", "CONTAINER ID"]
            
            result = check_docker_available()
            
            assert result is True
            assert mock_run.call_count == 2
            mock_run.assert_has_calls([
                call(["docker", "--version"], capture_output=True),
                call(["docker", "ps"], capture_output=True)
            ])

    def test_check_docker_not_installed(self):
        """Test Docker availability check when Docker is not installed."""
        with patch('cli.utils.run_command') as mock_run, \
             patch('builtins.print') as mock_print:
            mock_run.side_effect = [None, None]  # First call fails
            
            result = check_docker_available()
            
            assert result is False
            mock_print.assert_called_once_with("❌ Docker not found. Please install Docker first.")

    def test_check_docker_daemon_not_running(self):
        """Test Docker availability check when Docker is installed but daemon not running."""
        with patch('cli.utils.run_command') as mock_run, \
             patch('builtins.print') as mock_print:
            mock_run.side_effect = ["Docker version 20.10.0", None]  # Second call fails
            
            result = check_docker_available()
            
            assert result is False
            mock_print.assert_called_once_with("❌ Docker daemon not running. Please start Docker.")

    def test_check_docker_permission_error(self):
        """Test Docker availability check handles permission errors."""
        with patch('cli.utils.run_command') as mock_run, \
             patch('builtins.print') as mock_print:
            mock_run.side_effect = ["Docker version 20.10.0", None]  # ps fails due to permission
            
            result = check_docker_available()
            
            assert result is False
            mock_print.assert_called_once_with("❌ Docker daemon not running. Please start Docker.")

    def test_check_docker_version_command_timeout(self):
        """Test Docker availability check handles command timeouts."""
        with patch('cli.utils.run_command') as mock_run, \
             patch('builtins.print') as mock_print:
            mock_run.side_effect = [None, None]  # Timeout on version check
            
            result = check_docker_available()
            
            assert result is False
            mock_print.assert_called_once_with("❌ Docker not found. Please install Docker first.")

    def test_check_docker_ps_command_failure(self):
        """Test Docker availability check when ps command fails with specific error."""
        with patch('cli.utils.run_command') as mock_run, \
             patch('builtins.print') as mock_print:
            mock_run.side_effect = ["Docker version 20.10.0", None]
            
            result = check_docker_available()
            
            assert result is False
            mock_print.assert_called_once_with("❌ Docker daemon not running. Please start Docker.")


class TestFormatStatus:
    """Test format_status function for status message formatting."""

    def test_format_status_basic_formatting(self):
        """Test basic status formatting with name and status."""
        result = format_status("Test Service", "running")
        
        expected = "Test Service            🟢 Running"
        assert result == expected

    def test_format_status_with_details(self):
        """Test status formatting with additional details."""
        result = format_status("Database", "healthy", "Connected to localhost:5432")
        
        expected = "Database                🟢 Healthy - Connected to localhost:5432"
        assert result == expected

    def test_format_status_all_status_types(self):
        """Test status formatting with all supported status icons."""
        test_cases = [
            ("Service", "running", "🟢 Running"),
            ("Service", "stopped", "🔴 Stopped"),
            ("Service", "missing", "❌ Missing"),
            ("Service", "healthy", "🟢 Healthy"),
            ("Service", "unhealthy", "🟡 Unhealthy"),
            ("Service", "unknown", "❓ Unknown"),
        ]
        
        for name, status, expected_icon_text in test_cases:
            result = format_status(name, status)
            expected = f"{name:23} {expected_icon_text}"
            assert result == expected

    def test_format_status_case_insensitive(self):
        """Test status formatting is case insensitive."""
        result1 = format_status("Service", "RUNNING")
        result2 = format_status("Service", "running")
        result3 = format_status("Service", "Running")
        
        # All should produce same result
        assert result1 == result2 == result3
        assert "🟢 Running" in result1

    def test_format_status_long_service_name(self):
        """Test status formatting with service names longer than column width."""
        long_name = "Very Long Service Name That Exceeds Normal Width"
        result = format_status(long_name, "running")
        
        # Should still format properly, name just extends beyond normal width
        assert long_name in result
        assert "🟢 Running" in result

    def test_format_status_empty_name(self):
        """Test status formatting with empty service name."""
        result = format_status("", "running")
        
        expected = f"{'':23} 🟢 Running"
        assert result == expected

    def test_format_status_special_characters_in_name(self):
        """Test status formatting with special characters in service name."""
        result = format_status("Service-123_test", "running")
        
        assert "Service-123_test" in result
        assert "🟢 Running" in result

    def test_format_status_unicode_in_details(self):
        """Test status formatting with Unicode characters in details."""
        result = format_status("Service", "running", "连接到数据库")
        
        assert "连接到数据库" in result
        assert "🟢 Running" in result

    def test_format_status_multiline_details_handling(self):
        """Test status formatting handles multiline details appropriately."""
        multiline_details = "Line 1\nLine 2"
        result = format_status("Service", "running", multiline_details)
        
        # Should include details but might handle newlines
        assert "Service" in result
        assert "🟢 Running" in result


class TestConfirmAction:
    """Test confirm_action function for user interaction."""

    def test_confirm_action_yes_response(self):
        """Test confirm_action with various yes responses."""
        yes_responses = ["y", "yes", "Y", "YES", "Yes"]
        
        for response in yes_responses:
            with patch('builtins.input', return_value=response):
                result = confirm_action("Proceed?", default=False)
                assert result is True

    def test_confirm_action_no_response(self):
        """Test confirm_action with various no responses."""
        no_responses = ["n", "no", "N", "NO", "No"]
        
        for response in no_responses:
            with patch('builtins.input', return_value=response):
                result = confirm_action("Proceed?", default=True)
                assert result is False

    def test_confirm_action_empty_response_default_true(self):
        """Test confirm_action with empty response and default True."""
        with patch('builtins.input', return_value=""):
            result = confirm_action("Proceed?", default=True)
            assert result is True

    def test_confirm_action_empty_response_default_false(self):
        """Test confirm_action with empty response and default False."""
        with patch('builtins.input', return_value=""):
            result = confirm_action("Proceed?", default=False)
            assert result is False

    def test_confirm_action_whitespace_response(self):
        """Test confirm_action handles whitespace-only responses."""
        with patch('builtins.input', return_value="   "):
            result = confirm_action("Proceed?", default=True)
            assert result is True  # Should use default for whitespace

    def test_confirm_action_invalid_response_default_true(self):
        """Test confirm_action with invalid responses defaults to True."""
        invalid_responses = ["maybe", "123", "sure", "whatever"]
        
        for response in invalid_responses:
            with patch('builtins.input', return_value=response):
                result = confirm_action("Proceed?", default=True)
                assert result is True

    def test_confirm_action_invalid_response_default_false(self):
        """Test confirm_action with invalid responses defaults to False."""
        invalid_responses = ["maybe", "123", "sure", "whatever"]
        
        for response in invalid_responses:
            with patch('builtins.input', return_value=response):
                result = confirm_action("Proceed?", default=False)
                assert result is False

    def test_confirm_action_prompt_formatting_default_true(self):
        """Test confirm_action formats prompt correctly with default True."""
        with patch('builtins.input', return_value="") as mock_input:
            confirm_action("Delete files?", default=True)
            mock_input.assert_called_once_with("Delete files? (Y/n): ")

    def test_confirm_action_prompt_formatting_default_false(self):
        """Test confirm_action formats prompt correctly with default False."""
        with patch('builtins.input', return_value="") as mock_input:
            confirm_action("Delete files?", default=False)
            mock_input.assert_called_once_with("Delete files? (y/N): ")

    def test_confirm_action_keyboard_interrupt(self):
        """Test confirm_action handles KeyboardInterrupt gracefully."""
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            # Should not crash, should return default or False
            result = confirm_action("Proceed?", default=True)
            # Behavior may vary - could return default or False
            assert isinstance(result, bool)

    def test_confirm_action_eof_error(self):
        """Test confirm_action handles EOFError (Ctrl+D) gracefully."""
        with patch('builtins.input', side_effect=EOFError):
            result = confirm_action("Proceed?", default=True)
            # Should handle EOF gracefully
            assert isinstance(result, bool)

    def test_confirm_action_multiple_prompts(self):
        """Test confirm_action can be called multiple times independently."""
        with patch('builtins.input', side_effect=["yes", "no", ""]):
            result1 = confirm_action("First?", default=False)
            result2 = confirm_action("Second?", default=False)
            result3 = confirm_action("Third?", default=True)
            
            assert result1 is True   # "yes"
            assert result2 is False  # "no"
            assert result3 is True   # empty, default True


class TestUtilsIntegration:
    """Test integration scenarios across utility functions."""

    def test_docker_check_integration_with_command_execution(self):
        """Test Docker availability check integrates properly with command execution."""
        # This test verifies the integration between check_docker_available and run_command
        with patch('subprocess.run') as mock_run:
            # Mock successful Docker installation and running daemon
            mock_run.side_effect = [
                Mock(stdout="Docker version 20.10.0\n", returncode=0),
                Mock(stdout="CONTAINER ID   IMAGE\n", returncode=0)
            ]
            
            result = check_docker_available()
            
            assert result is True
            assert mock_run.call_count == 2

    def test_status_formatting_with_docker_status(self):
        """Test status formatting integrates with Docker status information."""
        # Mock Docker service status
        docker_status = "running"
        details = "3 containers active"
        
        result = format_status("Docker Service", docker_status, details)
        
        assert "Docker Service" in result
        assert "🟢 Running" in result
        assert "3 containers active" in result

    def test_user_confirmation_with_command_execution(self):
        """Test user confirmation integrates with subsequent command execution."""
        import sys
        current_module = sys.modules[__name__]
        
        with patch('builtins.input', return_value="yes"), \
             patch.object(current_module, 'run_command') as mock_run:
            
            # User confirms action
            confirmed = confirm_action("Execute dangerous command?", default=False)
            
            if confirmed:
                run_command(["rm", "-rf", "/tmp/test"], capture_output=False)
            
            assert confirmed is True
            mock_run.assert_called_once_with(["rm", "-rf", "/tmp/test"], capture_output=False)

    def test_error_handling_chain_across_functions(self):
        """Test error handling propagates correctly across utility functions."""
        with patch('subprocess.run', side_effect=FileNotFoundError), \
             patch('builtins.print') as mock_print:
            
            # Docker check should fail gracefully
            docker_available = check_docker_available()
            
            # Status formatting should still work
            status = format_status("Docker", "missing")
            
            # Confirmation should still work
            with patch('builtins.input', return_value="no"):
                confirmed = confirm_action("Continue without Docker?")
            
            assert docker_available is False
            assert "❌ Missing" in status
            assert confirmed is False
            # Should have printed Docker not found message
            mock_print.assert_called_with("❌ Docker not found. Please install Docker first.")


class TestUtilsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_command_execution_with_very_long_output(self):
        """Test command execution handles very long output efficiently."""
        # Simulate command with large output
        large_output = "x" * 100000 + "\n"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = large_output
            
            result = run_command(["generate_large_output"], capture_output=True)
            
            assert result == "x" * 100000

    def test_status_formatting_with_extreme_lengths(self):
        """Test status formatting with extremely long service names and details."""
        very_long_name = "x" * 1000
        very_long_details = "y" * 1000
        
        result = format_status(very_long_name, "running", very_long_details)
        
        # Should not crash and should include all components
        assert very_long_name in result
        assert "🟢 Running" in result
        assert very_long_details in result

    def test_user_input_with_extreme_responses(self):
        """Test user confirmation handles extreme input scenarios."""
        extreme_inputs = ["x" * 1000, "", "\n" * 100, "😀🎉🔥"]
        
        for extreme_input in extreme_inputs:
            with patch('builtins.input', return_value=extreme_input), \
                 patch('pathlib.Path.mkdir', side_effect=Exception("Directory creation blocked during extreme input test")) as mock_mkdir:
                result = confirm_action("Test?", default=True)
                # Should not crash and should return boolean
                assert isinstance(result, bool)
                # Ensure no directories were created with extreme input
                assert not mock_mkdir.called, f"Directory creation attempted with extreme input: {extreme_input[:50]}..."

    def test_concurrent_utility_function_calls(self):
        """Test utility functions handle concurrent access safely."""
        import threading
        results = []
        
        def test_status_formatting():
            for i in range(10):
                result = format_status(f"Service{i}", "running", f"Details{i}")
                results.append(result)
        
        # Run concurrent formatting operations
        threads = [threading.Thread(target=test_status_formatting) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Should have 30 results (3 threads × 10 operations each)
        assert len(results) == 30
        # All should be properly formatted
        assert all("🟢 Running" in result for result in results)
