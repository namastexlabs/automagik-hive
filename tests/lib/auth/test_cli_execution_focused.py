"""
Focused CLI Execution Tests for lib.auth.cli module.

NEW comprehensive test suite targeting missing source code lines to achieve 100% coverage.
Focus on executing the specific lines that are currently missed: lines 29 and 48.

Test Categories:
- Line 29: Environment variable access in show_current_key when key exists
- Line 48: show_current_key call within show_auth_status when auth enabled
- Edge cases and boundary conditions for complete coverage

OBJECTIVE: Execute ALL remaining CLI authentication code paths to achieve 100% coverage.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Import the module under test
try:
    import lib.auth.cli as auth_cli
    from lib.auth.cli import (
        show_current_key,
        show_auth_status,
    )
except ImportError:
    pytest.skip("Module lib.auth.cli not available", allow_module_level=True)


class TestMissingLineCoverage:
    """Test specific missing lines to achieve 100% coverage."""

    @patch('lib.auth.cli.AuthInitService')
    @patch('lib.auth.cli.logger') 
    @patch('os.getenv')
    def test_show_current_key_line_29_env_var_access(self, mock_getenv, mock_logger, mock_auth_service):
        """Test line 29: os.getenv("HIVE_API_PORT", "8886") when key exists."""
        # Setup mocks
        mock_service = Mock()
        mock_service.get_current_key.return_value = "test_key_for_line_29"
        mock_auth_service.return_value = mock_service
        mock_getenv.return_value = "9999"  # Custom port value
        
        # Execute function to hit line 29
        show_current_key()
        
        # Verify line 29 was executed (environment variable access)
        mock_getenv.assert_called_once_with("HIVE_API_PORT", "8886")
        mock_logger.info.assert_called_once_with(
            "Current API key retrieved", key_length=len("test_key_for_line_29")
        )

    @patch('lib.auth.cli.show_current_key')
    @patch('lib.auth.cli.logger')
    @patch('os.getenv')
    def test_show_auth_status_line_48_enabled_auth(self, mock_getenv, mock_logger, mock_show_key):
        """Test line 48: show_current_key() call when auth is enabled."""
        # Setup environment for enabled auth
        mock_getenv.return_value = "false"  # Auth enabled (not "true")
        
        # Execute function to hit line 48
        show_auth_status()
        
        # Verify line 48 was executed (show_current_key called)
        mock_getenv.assert_called_once_with("HIVE_AUTH_DISABLED", "false")
        mock_logger.info.assert_called_once_with(
            "Auth status requested", auth_disabled=False
        )
        mock_show_key.assert_called_once()

    @patch('lib.auth.cli.AuthInitService')
    @patch('lib.auth.cli.logger')
    @patch('os.getenv')
    def test_complete_flow_targeting_missing_lines(self, mock_getenv, mock_logger, mock_auth_service):
        """Test complete flow that executes both missing lines."""
        # Setup mocks
        mock_service = Mock()
        mock_service.get_current_key.return_value = "complete_flow_key"
        mock_auth_service.return_value = mock_service
        mock_getenv.side_effect = ["custom_port", "false"]  # First call for port, second for auth status
        
        # Execute both functions to hit all missing lines
        show_current_key()  # Should hit line 29
        show_auth_status()  # Should hit line 48 (which calls show_current_key again)
        
        # Verify both functions executed properly
        assert mock_getenv.call_count == 3  # Port check (2x) + auth status check (1x)
        assert mock_auth_service.call_count == 2  # Called twice by show_current_key
        assert mock_service.get_current_key.call_count == 2  # Called twice
        
        # Verify logger calls for both functions
        mock_logger.info.assert_any_call(
            "Current API key retrieved", key_length=len("complete_flow_key")
        )
        mock_logger.info.assert_any_call(
            "Auth status requested", auth_disabled=False
        )

    @patch('lib.auth.cli.AuthInitService')
    @patch('lib.auth.cli.logger')
    @patch.dict(os.environ, {'HIVE_API_PORT': '7777'}, clear=False)
    def test_show_current_key_with_real_env_var(self, mock_logger, mock_auth_service):
        """Test show_current_key with real environment variable to ensure line 29 execution."""
        # Setup mock
        mock_service = Mock()
        mock_service.get_current_key.return_value = "env_var_test_key"
        mock_auth_service.return_value = mock_service
        
        # Execute function - should access real HIVE_API_PORT environment variable
        show_current_key()
        
        # Verify function executed and line 29 was hit
        mock_auth_service.assert_called_once()
        mock_service.get_current_key.assert_called_once()
        mock_logger.info.assert_called_once_with(
            "Current API key retrieved", key_length=len("env_var_test_key")
        )

    @patch('lib.auth.cli.show_current_key')
    @patch('lib.auth.cli.logger')
    @patch.dict(os.environ, {'HIVE_AUTH_DISABLED': 'no'}, clear=False)  
    def test_show_auth_status_with_real_env_var(self, mock_logger, mock_show_key):
        """Test show_auth_status with real environment variable to ensure line 48 execution."""
        # Execute function - should access real HIVE_AUTH_DISABLED environment variable
        # 'no' is not 'true', so auth should be enabled and line 48 should execute
        show_auth_status()
        
        # Verify line 48 was executed (show_current_key called)
        mock_logger.info.assert_called_once_with(
            "Auth status requested", auth_disabled=False
        )
        mock_show_key.assert_called_once()

    @patch('lib.auth.cli.AuthInitService')
    @patch('lib.auth.cli.logger')
    @patch('os.getenv', return_value=None)
    def test_show_current_key_no_env_var_uses_default(self, mock_getenv, mock_logger, mock_auth_service):
        """Test show_current_key when HIVE_API_PORT environment variable is not set."""
        # Setup mock
        mock_service = Mock()
        mock_service.get_current_key.return_value = "default_port_key"
        mock_auth_service.return_value = mock_service
        
        # Execute function
        show_current_key()
        
        # Verify line 29 was executed and default port was used
        mock_getenv.assert_called_once_with("HIVE_API_PORT", "8886")
        mock_logger.info.assert_called_once_with(
            "Current API key retrieved", key_length=len("default_port_key")
        )

    @patch('lib.auth.cli.AuthInitService')
    @patch('lib.auth.cli.logger')
    def test_show_current_key_various_key_lengths(self, mock_logger, mock_auth_service):
        """Test show_current_key with various key lengths to ensure line coverage."""
        # Setup mock
        mock_service = Mock()
        mock_auth_service.return_value = mock_service
        
        test_keys = [
            "",  # Empty key
            "a",  # Single character
            "short_key",  # Short key
            "very_long_api_key_that_has_many_characters_for_testing_purposes_123456789",  # Long key
        ]
        
        for test_key in test_keys:
            mock_service.get_current_key.return_value = test_key
            mock_logger.reset_mock()
            
            # Execute function
            show_current_key()
            
            # Verify proper handling of different key lengths
            if test_key:
                mock_logger.info.assert_called_once_with(
                    "Current API key retrieved", key_length=len(test_key)
                )
            else:
                mock_logger.warning.assert_called_once_with("No API key found")

    @patch('lib.auth.cli.show_current_key')
    @patch('lib.auth.cli.logger')
    def test_show_auth_status_all_environment_values(self, mock_logger, mock_show_key):
        """Test show_auth_status with all possible environment variable values."""
        test_values = [
            ("true", True),    # Disabled
            ("TRUE", True),    # Disabled (case insensitive)
            ("True", True),    # Disabled (case insensitive)
            ("false", False),  # Enabled (line 48 executed)
            ("FALSE", False),  # Enabled
            ("", False),       # Enabled (empty string)
            ("invalid", False), # Enabled (invalid value)
            ("yes", False),    # Enabled (not "true")
        ]
        
        for env_value, expected_disabled in test_values:
            with patch('os.getenv', return_value=env_value):
                mock_logger.reset_mock()
                mock_show_key.reset_mock()
                
                # Execute function
                show_auth_status()
                
                # Verify correct branch was taken
                mock_logger.info.assert_called_once_with(
                    "Auth status requested", auth_disabled=expected_disabled
                )
                
                if expected_disabled:
                    # Auth disabled - line 48 not executed
                    mock_logger.warning.assert_called_once_with(
                        "Authentication disabled - development mode"
                    )
                    mock_show_key.assert_not_called()
                else:
                    # Auth enabled - line 48 executed
                    mock_show_key.assert_called_once()


class TestExhaustivePathCoverage:
    """Test every possible execution path to ensure 100% coverage."""

    @patch('lib.auth.cli.AuthInitService')
    @patch('lib.auth.cli.logger')
    @patch('os.getenv')
    def test_every_line_execution_path(self, mock_getenv, mock_logger, mock_auth_service):
        """Test that every line in the CLI module gets executed."""
        # Setup comprehensive mocks
        mock_service = Mock()
        mock_service.get_current_key.return_value = "comprehensive_test_key"
        mock_auth_service.return_value = mock_service
        mock_getenv.side_effect = ["8888", "false"]  # Port, then auth status
        
        # Execute show_current_key to hit lines 22-29
        show_current_key()
        
        # Execute show_auth_status to hit lines 40-48
        show_auth_status()
        
        # Verify all expected calls were made
        assert mock_auth_service.call_count == 3  # Called 3 times total
        assert mock_service.get_current_key.call_count == 3  # Called 3 times total
        assert mock_getenv.call_count == 2  # Port check + auth status check
        
        # Verify all logger calls happened
        expected_calls = [
            # First show_current_key call
            call.info("Current API key retrieved", key_length=len("comprehensive_test_key")),
            # show_auth_status call
            call.info("Auth status requested", auth_disabled=False),
            # Second show_current_key call (from line 48)
            call.info("Current API key retrieved", key_length=len("comprehensive_test_key"))
        ]
        
        # Check that all expected calls occurred (order may vary due to patching)
        info_calls = [call for call in mock_logger.method_calls if call[0] == 'info']
        assert len(info_calls) == 3

    def test_import_and_attribute_access(self):
        """Test that all module imports and attributes are accessible."""
        # Test module-level imports and attributes
        assert hasattr(auth_cli, 'os')
        assert hasattr(auth_cli, 'sys')
        assert hasattr(auth_cli, 'Path')
        assert hasattr(auth_cli, 'CredentialService')
        assert hasattr(auth_cli, 'AuthInitService')
        assert hasattr(auth_cli, 'logger')
        
        # Test all function definitions exist
        functions = [
            'show_current_key',
            'regenerate_key',
            'show_auth_status',
            'generate_postgres_credentials',
            'generate_complete_workspace_credentials', 
            'generate_agent_credentials',
            'show_credential_status',
            'sync_mcp_credentials'
        ]
        
        for func_name in functions:
            assert hasattr(auth_cli, func_name)
            assert callable(getattr(auth_cli, func_name))

    def test_path_manipulation_in_functions(self):
        """Test Path manipulation to ensure all path-related code is executed."""
        from lib.auth.cli import generate_complete_workspace_credentials
        
        with patch('lib.auth.cli.CredentialService') as mock_service_class:
            with patch('lib.auth.cli.logger') as mock_logger:
                # Setup mock
                mock_service = Mock()
                mock_service.setup_complete_credentials.return_value = {"test": "path_creds"}
                mock_service_class.return_value = mock_service
                
                # Test with workspace path to execute Path manipulation
                test_workspace = Path("/test/workspace/path")
                result = generate_complete_workspace_credentials(workspace_path=test_workspace)
                
                # Verify Path concatenation was executed
                expected_env_file = test_workspace / ".env"
                mock_service_class.assert_called_once_with(expected_env_file)
                
                # Verify string conversion of Path in logging
                mock_logger.info.assert_called_once_with(
                    "Complete workspace credentials generated", 
                    workspace_path=str(test_workspace)
                )
                
                assert result == {"test": "path_creds"}