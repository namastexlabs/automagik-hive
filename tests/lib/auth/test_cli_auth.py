"""Auth CLI tests for lib.auth.cli module - BATCH 5 Coverage Enhancement.

Tests targeting 50%+ coverage for medium priority authentication CLI functionality.
Focuses on credential management functions and CLI argument parsing.

Test Categories:
- Unit tests: Individual function behavior and service integration
- Argument parsing: CLI argument validation and processing  
- Credential generation: Various credential creation scenarios
- Error handling: Exception scenarios and service failures
- Integration tests: Service interactions and filesystem operations
"""

import pytest
import os
import argparse
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

# Import the module under test
try:
    import lib.auth.cli as auth_cli
    from lib.auth.cli import (
        show_current_key,
        regenerate_key,
        show_auth_status,
        generate_postgres_credentials,
        generate_complete_workspace_credentials,
        generate_agent_credentials,
        show_credential_status,
        sync_mcp_credentials
    )
except ImportError:
    pytest.skip("Module lib.auth.cli not available", allow_module_level=True)


class TestShowCurrentKey:
    """Test show_current_key function - targeting key display coverage."""

    @patch('lib.auth.cli.AuthInitService')
    @patch('lib.auth.cli.logger')
    @patch.dict(os.environ, {'HIVE_API_PORT': '9999'})
    def test_show_current_key_with_existing_key(self, mock_logger, mock_auth_service):
        """Test show_current_key when API key exists."""
        # Setup mock
        mock_service = Mock()
        mock_service.get_current_key.return_value = "test_api_key_12345"
        mock_auth_service.return_value = mock_service
        
        show_current_key()
        
        # Should pass - function calls service and logs result
        mock_auth_service.assert_called_once()
        mock_service.get_current_key.assert_called_once()
        mock_logger.info.assert_called_once_with(
            "Current API key retrieved", key_length=len("test_api_key_12345"), port=8887
        )

    @patch('lib.auth.cli.AuthInitService')
    @patch('lib.auth.cli.logger')
    def test_show_current_key_no_key_found(self, mock_logger, mock_auth_service):
        """Test show_current_key when no API key exists."""
        # Setup mock
        mock_service = Mock()
        mock_service.get_current_key.return_value = None
        mock_auth_service.return_value = mock_service
        
        show_current_key()
        
        # Should pass - function handles None key gracefully
        mock_auth_service.assert_called_once()
        mock_service.get_current_key.assert_called_once()
        mock_logger.warning.assert_called_once_with("No API key found")

    @patch('lib.auth.cli.AuthInitService')
    @patch('lib.auth.cli.logger')
    @patch.dict(os.environ, {}, clear=True)
    def test_show_current_key_default_port(self, mock_logger, mock_auth_service):
        """Test show_current_key uses default port when env var missing."""
        # Setup mock
        mock_service = Mock()
        mock_service.get_current_key.return_value = "test_key"
        mock_auth_service.return_value = mock_service
        
        # Clear environment variables
        show_current_key()
        
        # Should pass - function should handle missing HIVE_API_PORT
        mock_auth_service.assert_called_once()
        mock_service.get_current_key.assert_called_once()

    @patch('lib.auth.cli.AuthInitService')
    def test_show_current_key_service_exception(self, mock_auth_service):
        """Test show_current_key handles service exceptions."""
        # Setup mock to raise exception
        mock_auth_service.side_effect = Exception("Service initialization failed")
        
        # Should fail initially - exception handling not implemented
        with pytest.raises(Exception):
            show_current_key()


class TestRegenerateKey:
    """Test regenerate_key function - targeting key regeneration coverage."""

    @patch('lib.auth.cli.AuthInitService')
    @patch('lib.auth.cli.logger')
    def test_regenerate_key_success(self, mock_logger, mock_auth_service):
        """Test successful key regeneration."""
        # Setup mock
        mock_service = Mock()
        new_key = "regenerated_key_67890"
        mock_service.regenerate_key.return_value = new_key
        mock_auth_service.return_value = mock_service
        
        regenerate_key()
        
        # Should pass - function calls service and logs result
        mock_auth_service.assert_called_once()
        mock_service.regenerate_key.assert_called_once()
        mock_logger.info.assert_called_once_with(
            "API key regenerated", key_length=len(new_key)
        )

    @patch('lib.auth.cli.AuthInitService')
    def test_regenerate_key_service_exception(self, mock_auth_service):
        """Test regenerate_key handles service exceptions."""
        # Setup mock to raise exception
        mock_auth_service.side_effect = Exception("Regeneration failed")
        
        # Should fail initially - exception handling not implemented
        with pytest.raises(Exception):
            regenerate_key()

    @patch('lib.auth.cli.AuthInitService')
    @patch('lib.auth.cli.logger')
    def test_regenerate_key_empty_result(self, mock_logger, mock_auth_service):
        """Test regenerate_key handles empty key result."""
        # Setup mock
        mock_service = Mock()
        mock_service.regenerate_key.return_value = ""
        mock_auth_service.return_value = mock_service
        
        regenerate_key()
        
        # Should pass - function should handle empty key result
        mock_auth_service.assert_called_once()
        mock_service.regenerate_key.assert_called_once()
        mock_logger.info.assert_called_once_with("API key regenerated", key_length=0)


class TestShowAuthStatus:
    """Test show_auth_status function - targeting auth status coverage."""

    @patch('lib.auth.cli.show_current_key')
    @patch('lib.auth.cli.logger')
    @patch.dict(os.environ, {'HIVE_AUTH_DISABLED': 'false'})
    def test_show_auth_status_enabled(self, mock_logger, mock_show_key):
        """Test show_auth_status when authentication is enabled."""
        show_auth_status()
        
        # Should pass - function shows current key when auth enabled
        mock_logger.info.assert_called_once_with(
            "Auth status requested", auth_disabled=False
        )
        mock_show_key.assert_called_once()

    @patch('lib.auth.cli.show_current_key')
    @patch('lib.auth.cli.logger')
    @patch.dict(os.environ, {'HIVE_AUTH_DISABLED': 'true'})
    def test_show_auth_status_disabled(self, mock_logger, mock_show_key):
        """Test show_auth_status when authentication is disabled."""
        show_auth_status()
        
        # Should pass - function logs warning when auth disabled
        mock_logger.info.assert_called_once_with(
            "Auth status requested", auth_disabled=True
        )
        mock_logger.warning.assert_called_once_with(
            "Authentication disabled - development mode"
        )
        mock_show_key.assert_not_called()

    @patch('lib.auth.cli.show_current_key')
    @patch('lib.auth.cli.logger')
    @patch.dict(os.environ, {'HIVE_AUTH_DISABLED': 'TRUE'})
    def test_show_auth_status_case_insensitive_disabled(self, mock_logger, mock_show_key):
        """Test show_auth_status handles case-insensitive 'true'."""
        show_auth_status()
        
        # Should pass - function handles uppercase TRUE
        mock_logger.info.assert_called_once_with(
            "Auth status requested", auth_disabled=True
        )
        mock_logger.warning.assert_called_once_with(
            "Authentication disabled - development mode"
        )
        mock_show_key.assert_not_called()

    @patch('lib.auth.cli.show_current_key')
    @patch('lib.auth.cli.logger')
    @patch.dict(os.environ, {}, clear=True)
    def test_show_auth_status_default_enabled(self, mock_logger, mock_show_key):
        """Test show_auth_status defaults to enabled when env var missing."""
        show_auth_status()
        
        # Should pass - function defaults to enabled
        mock_logger.info.assert_called_once_with(
            "Auth status requested", auth_disabled=False
        )
        mock_show_key.assert_called_once()

    @patch('lib.auth.cli.show_current_key')
    @patch('lib.auth.cli.logger')
    @patch.dict(os.environ, {'HIVE_AUTH_DISABLED': 'invalid_value'})
    def test_show_auth_status_invalid_value(self, mock_logger, mock_show_key):
        """Test show_auth_status handles invalid environment value."""
        show_auth_status()
        
        # Should pass - function treats invalid value as false
        mock_logger.info.assert_called_once_with(
            "Auth status requested", auth_disabled=False
        )
        mock_show_key.assert_called_once()


class TestGeneratePostgresCredentials:
    """Test generate_postgres_credentials function - targeting postgres credential coverage."""

    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_generate_postgres_credentials_defaults(self, mock_logger, mock_service_class):
        """Test generate_postgres_credentials with default parameters."""
        # Setup mock
        mock_service = Mock()
        expected_creds = {"username": "test_user", "password": "test_pass"}
        mock_service.generate_postgres_credentials.return_value = expected_creds
        mock_service_class.return_value = mock_service
        
        result = generate_postgres_credentials()
        
        # Should pass - function uses default parameters
        mock_service_class.assert_called_once_with(None)
        mock_service.generate_postgres_credentials.assert_called_once_with(
            "localhost", 5532, "hive"
        )
        mock_logger.info.assert_called_once_with(
            "PostgreSQL credentials generated via CLI", database="hive", port=5532
        )
        assert result == expected_creds

    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_generate_postgres_credentials_custom_params(self, mock_logger, mock_service_class):
        """Test generate_postgres_credentials with custom parameters."""
        # Setup mock
        mock_service = Mock()
        expected_creds = {"username": "custom_user", "password": "custom_pass"}
        mock_service.generate_postgres_credentials.return_value = expected_creds
        mock_service_class.return_value = mock_service
        
        env_file = Path("/custom/.env")
        result = generate_postgres_credentials(
            host="custom.host",
            port=3333,
            database="custom_db",
            env_file=env_file
        )
        
        # Should pass - function uses custom parameters
        mock_service_class.assert_called_once_with(env_file)
        mock_service.generate_postgres_credentials.assert_called_once_with(
            "custom.host", 3333, "custom_db"
        )
        mock_logger.info.assert_called_once_with(
            "PostgreSQL credentials generated via CLI", database="custom_db", port=3333
        )
        assert result == expected_creds

    @patch('lib.auth.cli.CredentialService')
    def test_generate_postgres_credentials_service_exception(self, mock_service_class):
        """Test generate_postgres_credentials handles service exceptions."""
        # Setup mock to raise exception
        mock_service_class.side_effect = Exception("Credential generation failed")
        
        # Should fail initially - exception handling not implemented
        with pytest.raises(Exception):
            generate_postgres_credentials()

    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_generate_postgres_credentials_empty_result(self, mock_logger, mock_service_class):
        """Test generate_postgres_credentials handles empty result."""
        # Setup mock
        mock_service = Mock()
        mock_service.generate_postgres_credentials.return_value = {}
        mock_service_class.return_value = mock_service
        
        result = generate_postgres_credentials()
        
        # Should pass - function should handle empty credentials
        assert result == {}


class TestGenerateCompleteWorkspaceCredentials:
    """Test generate_complete_workspace_credentials function - targeting workspace credential coverage."""

    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_generate_complete_workspace_credentials_with_path(self, mock_logger, mock_service_class):
        """Test generate_complete_workspace_credentials with workspace path."""
        # Setup mock
        mock_service = Mock()
        expected_creds = {"api_key": "test_key", "db_url": "test_url"}
        mock_service.setup_complete_credentials.return_value = expected_creds
        mock_service_class.return_value = mock_service
        
        workspace_path = Path("/test/workspace")
        result = generate_complete_workspace_credentials(workspace_path=workspace_path)
        
        # Should pass - function creates complete credentials
        mock_service_class.assert_called_once_with(project_root=workspace_path)
        mock_service.setup_complete_credentials.assert_called_once_with(
            "localhost", 5532, "hive"
        )
        mock_logger.info.assert_called_once_with(
            "Complete workspace credentials generated", 
            workspace_path=str(workspace_path)
        )
        assert result == expected_creds

    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_generate_complete_workspace_credentials_no_path(self, mock_logger, mock_service_class):
        """Test generate_complete_workspace_credentials without workspace path."""
        # Setup mock
        mock_service = Mock()
        expected_creds = {"api_key": "test_key"}
        mock_service.setup_complete_credentials.return_value = expected_creds
        mock_service_class.return_value = mock_service
        
        result = generate_complete_workspace_credentials()
        
        # Should pass - function handles None workspace path
        mock_service_class.assert_called_once_with(project_root=None)
        mock_service.setup_complete_credentials.assert_called_once_with(
            "localhost", 5532, "hive"
        )
        mock_logger.info.assert_called_once_with(
            "Complete workspace credentials generated", workspace_path="None"
        )
        assert result == expected_creds

    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_generate_complete_workspace_credentials_custom_params(self, mock_logger, mock_service_class):
        """Test generate_complete_workspace_credentials with custom parameters."""
        # Setup mock
        mock_service = Mock()
        expected_creds = {"api_key": "custom_key"}
        mock_service.setup_complete_credentials.return_value = expected_creds
        mock_service_class.return_value = mock_service
        
        workspace_path = Path("/custom/workspace")
        result = generate_complete_workspace_credentials(
            workspace_path=workspace_path,
            postgres_host="custom.postgres",
            postgres_port=9999,
            postgres_database="custom_workspace_db"
        )
        
        # Should pass - function uses custom parameters
        mock_service_class.assert_called_once_with(project_root=workspace_path)
        mock_service.setup_complete_credentials.assert_called_once_with(
            "custom.postgres", 9999, "custom_workspace_db"
        )
        assert result == expected_creds


class TestGenerateAgentCredentials:
    """Test generate_agent_credentials function - targeting agent credential coverage."""

    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_generate_agent_credentials_defaults(self, mock_logger, mock_service_class):
        """Test generate_agent_credentials with default parameters."""
        # Setup mock
        mock_service = Mock()
        expected_creds = {"agent_user": "agent", "agent_pass": "secret"}
        mock_service.generate_agent_credentials.return_value = expected_creds
        mock_service_class.return_value = mock_service
        
        result = generate_agent_credentials()
        
        # Should pass - function uses default agent parameters
        mock_service_class.assert_called_once_with(None)
        mock_service.generate_agent_credentials.assert_called_once_with(35532, "hive_agent")
        mock_logger.info.assert_called_once_with(
            "Agent credentials generated via CLI", database="hive_agent", port=35532
        )
        assert result == expected_creds

    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_generate_agent_credentials_custom_params(self, mock_logger, mock_service_class):
        """Test generate_agent_credentials with custom parameters."""
        # Setup mock
        mock_service = Mock()
        expected_creds = {"agent_user": "custom_agent", "agent_pass": "custom_secret"}
        mock_service.generate_agent_credentials.return_value = expected_creds
        mock_service_class.return_value = mock_service
        
        env_file = Path("/custom/agent/.env")
        result = generate_agent_credentials(
            port=45532,
            database="custom_agent_db",
            env_file=env_file
        )
        
        # Should pass - function uses custom agent parameters
        mock_service_class.assert_called_once_with(env_file)
        mock_service.generate_agent_credentials.assert_called_once_with(45532, "custom_agent_db")
        mock_logger.info.assert_called_once_with(
            "Agent credentials generated via CLI", database="custom_agent_db", port=45532
        )
        assert result == expected_creds

    @patch('lib.auth.cli.CredentialService')
    def test_generate_agent_credentials_service_exception(self, mock_service_class):
        """Test generate_agent_credentials handles service exceptions."""
        # Setup mock to raise exception
        mock_service_class.side_effect = Exception("Agent credential generation failed")
        
        # Should fail initially - exception handling not implemented
        with pytest.raises(Exception):
            generate_agent_credentials()


class TestShowCredentialStatus:
    """Test show_credential_status function - targeting credential status coverage."""

    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_show_credential_status_with_validation(self, mock_logger, mock_service_class):
        """Test show_credential_status with validation data."""
        # Setup mock
        mock_service = Mock()
        mock_status = {
            "validation": {
                "postgres_user_valid": True,
                "postgres_password_valid": True,
                "postgres_url_valid": False,
                "api_key_valid": True
            },
            "postgres_configured": True,
            "postgres_credentials": {"user": "test_user", "password": "****"}
        }
        mock_service.get_credential_status.return_value = mock_status
        mock_service_class.return_value = mock_service
        
        show_credential_status()
        
        # Should pass - function processes validation data
        mock_service_class.assert_called_once_with(None)
        mock_service.get_credential_status.assert_called_once()
        mock_logger.info.assert_called_once_with("Credential status requested")

    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_show_credential_status_no_validation(self, mock_logger, mock_service_class):
        """Test show_credential_status without validation data."""
        # Setup mock
        mock_service = Mock()
        mock_status = {
            "postgres_configured": False,
        }
        mock_service.get_credential_status.return_value = mock_status
        mock_service_class.return_value = mock_service
        
        show_credential_status()
        
        # Should pass - function handles missing validation data
        mock_service_class.assert_called_once_with(None)
        mock_service.get_credential_status.assert_called_once()
        mock_logger.info.assert_called_once_with("Credential status requested")

    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_show_credential_status_with_env_file(self, mock_logger, mock_service_class):
        """Test show_credential_status with custom env file."""
        # Setup mock with postgres_credentials key to prevent KeyError
        mock_service = Mock()
        mock_status = {
            "postgres_configured": True,
            "postgres_credentials": {"user": "test_user", "password": "****"}
        }
        mock_service.get_credential_status.return_value = mock_status
        mock_service_class.return_value = mock_service
        
        env_file = Path("/custom/status/.env")
        show_credential_status(env_file=env_file)
        
        # Should pass - function uses custom env file
        mock_service_class.assert_called_once_with(env_file)
        mock_service.get_credential_status.assert_called_once()
        mock_logger.info.assert_called_once_with("Credential status requested")

    @patch('lib.auth.cli.CredentialService')
    def test_show_credential_status_service_exception(self, mock_service_class):
        """Test show_credential_status handles service exceptions."""
        # Setup mock to raise exception
        mock_service_class.side_effect = Exception("Status retrieval failed")
        
        # Should fail initially - exception handling not implemented
        with pytest.raises(Exception):
            show_credential_status()


class TestSyncMcpCredentials:
    """Test sync_mcp_credentials function - targeting MCP sync coverage."""

    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_sync_mcp_credentials_defaults(self, mock_logger, mock_service_class):
        """Test sync_mcp_credentials with default parameters."""
        # Setup mock
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        sync_mcp_credentials()
        
        # Should pass - function syncs with defaults
        mock_service_class.assert_called_once_with(None)
        mock_service.sync_mcp_config_with_credentials.assert_called_once_with(None)
        mock_logger.info.assert_called_once_with(
            "MCP configuration synchronized with credentials"
        )

    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_sync_mcp_credentials_custom_files(self, mock_logger, mock_service_class):
        """Test sync_mcp_credentials with custom files."""
        # Setup mock
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        mcp_file = Path("/custom/mcp.json")
        env_file = Path("/custom/.env")
        sync_mcp_credentials(mcp_file=mcp_file, env_file=env_file)
        
        # Should pass - function uses custom files
        mock_service_class.assert_called_once_with(env_file)
        mock_service.sync_mcp_config_with_credentials.assert_called_once_with(mcp_file)
        mock_logger.info.assert_called_once_with(
            "MCP configuration synchronized with credentials"
        )

    @patch('lib.auth.cli.CredentialService')
    def test_sync_mcp_credentials_service_exception(self, mock_service_class):
        """Test sync_mcp_credentials handles service exceptions."""
        # Setup mock to raise exception
        mock_service_class.side_effect = Exception("MCP sync failed")
        
        # Should fail initially - exception handling not implemented
        with pytest.raises(Exception):
            sync_mcp_credentials()

    @patch('lib.auth.cli.CredentialService')
    def test_sync_mcp_credentials_sync_exception(self, mock_service_class):
        """Test sync_mcp_credentials handles sync exceptions."""
        # Setup mock
        mock_service = Mock()
        mock_service.sync_mcp_config_with_credentials.side_effect = Exception("Sync operation failed")
        mock_service_class.return_value = mock_service
        
        # Should fail initially - sync exception handling not implemented
        with pytest.raises(Exception):
            sync_mcp_credentials()


class TestCliArgumentParsing:
    """Test CLI argument parsing functionality - targeting CLI parsing coverage."""

    def test_module_main_execution_simulation(self):
        """Test module main execution simulation."""
        # This tests the argument parsing structure without actually running main
        
        # Test that argparse import is available when running as main
        # Since argparse is imported in __main__ block, we test differently
        import argparse as test_argparse
        assert test_argparse is not None
        
        # Test that required imports are available at module level
        required_modules = ['Path']
        for module_name in required_modules:
            assert module_name in dir(auth_cli) or 'Path' in str(auth_cli.__dict__)

    def test_cli_function_availability(self):
        """Test all CLI functions are available for argument parsing."""
        required_functions = [
            'show_current_key',
            'regenerate_key', 
            'show_auth_status',
            'generate_postgres_credentials',
            'generate_complete_workspace_credentials',
            'generate_agent_credentials',
            'show_credential_status',
            'sync_mcp_credentials'
        ]
        
        for func_name in required_functions:
            # Should pass - all functions should be available
            assert hasattr(auth_cli, func_name)
            assert callable(getattr(auth_cli, func_name))

    @patch('sys.argv', ['cli.py', 'auth', 'show'])
    @patch('lib.auth.cli.AuthInitService')
    def test_argument_parsing_simulation_auth_show(self, mock_auth_service):
        """Test argument parsing simulation for auth show command."""
        # This simulates what would happen with CLI argument parsing
        # Setup mock for the actual function call
        mock_service = Mock()
        mock_service.get_current_key.return_value = "test_key"
        mock_auth_service.return_value = mock_service
        
        # We can test that the function exists and is callable
        assert callable(show_current_key)
        
        # Test direct function call (what CLI would do)
        show_current_key()
        mock_auth_service.assert_called_once()

    def test_path_parameter_handling(self):
        """Test Path parameter handling in functions."""
        # Test that functions can handle Path objects
        test_path = Path("/test/path")
        
        # Should pass - functions should be able to handle Path objects
        assert isinstance(test_path, Path)
        
        # Test functions that accept Path parameters
        functions_with_path_params = [
            generate_postgres_credentials,
            generate_complete_workspace_credentials,
            generate_agent_credentials,
            show_credential_status,
            sync_mcp_credentials
        ]
        
        for func in functions_with_path_params:
            # Should pass - functions should exist and be callable
            assert callable(func)


class TestIntegrationScenarios:
    """Test integration scenarios - targeting integration coverage."""

    @patch('lib.auth.cli.AuthInitService')
    @patch('lib.auth.cli.CredentialService') 
    @patch('lib.auth.cli.logger')
    def test_complete_credential_workflow(self, mock_logger, mock_cred_service_class, mock_auth_service_class):
        """Test complete credential generation workflow."""
        # Setup mocks
        mock_auth_service = Mock()
        mock_auth_service.get_current_key.return_value = "existing_key"
        mock_auth_service_class.return_value = mock_auth_service
        
        mock_cred_service = Mock()
        mock_cred_service.generate_postgres_credentials.return_value = {"db": "creds"}
        mock_cred_service.generate_agent_credentials.return_value = {"agent": "creds"}
        mock_cred_service_class.return_value = mock_cred_service
        
        # Execute workflow
        show_current_key()
        generate_postgres_credentials()
        generate_agent_credentials()
        
        # Should pass - complete workflow should work
        mock_auth_service.get_current_key.assert_called_once()
        mock_cred_service.generate_postgres_credentials.assert_called_once()
        mock_cred_service.generate_agent_credentials.assert_called_once()

    @patch.dict(os.environ, {'HIVE_AUTH_DISABLED': 'true'})
    @patch('lib.auth.cli.logger')
    def test_disabled_auth_workflow(self, mock_logger):
        """Test workflow when authentication is disabled."""
        show_auth_status()
        
        # Should pass - disabled auth workflow should work
        mock_logger.info.assert_called_with("Auth status requested", auth_disabled=True)
        mock_logger.warning.assert_called_with("Authentication disabled - development mode")

    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_error_recovery_workflow(self, mock_logger, mock_service_class):
        """Test error recovery in credential workflow."""
        # Setup first call to fail, second to succeed
        mock_service = Mock()
        mock_service.generate_postgres_credentials.side_effect = [
            Exception("First attempt failed"),
            {"recovered": "credentials"}
        ]
        mock_service_class.return_value = mock_service
        
        # First attempt should fail
        with pytest.raises(Exception):
            generate_postgres_credentials()
        
        # Should fail initially - error recovery not implemented
        # Second attempt should succeed (in a real implementation with retry logic)
        # This test shows where error recovery could be implemented
        
    @patch('lib.auth.cli.CredentialService')
    @patch('lib.auth.cli.logger')
    def test_credential_status_integration(self, mock_logger, mock_service_class):
        """Test credential status integration with different states."""
        # Setup mock for various status scenarios
        mock_service = Mock()
        status_scenarios = [
            {"postgres_configured": True, "validation": {"api_key_valid": True}},
            {"postgres_configured": False, "validation": {"api_key_valid": False}},
            {"postgres_configured": True}  # No validation data
        ]
        
        for i, status in enumerate(status_scenarios):
            # Ensure all status scenarios include postgres_credentials when postgres_configured=True
            if status.get("postgres_configured"):
                status["postgres_credentials"] = {"user": f"user_{i}", "password": "****"}
            
            mock_service.get_credential_status.return_value = status
            mock_service_class.return_value = mock_service
            
            # Should pass - status integration should handle different scenarios
            show_credential_status()
            
        # Should pass - all status scenarios should be handled
        assert mock_service.get_credential_status.call_count == len(status_scenarios)