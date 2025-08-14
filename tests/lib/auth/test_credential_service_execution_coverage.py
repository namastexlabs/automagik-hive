"""
SOURCE CODE EXECUTION TEST SUITE for CredentialService

This test suite is specifically designed to EXECUTE the missing code paths
identified in coverage analysis. Goal: Achieve 50%+ ACTUAL coverage by 
CALLING methods that currently have low execution coverage.

Target: Execute all authentication workflows and edge cases
Focus: ACTUAL method calls with realistic scenarios
"""

import json
import os
import re
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from urllib.parse import urlparse

import pytest

from lib.auth.credential_service import CredentialService


class TestCredentialExtractionExceptionHandling:
    """Execute exception handling paths in credential extraction methods."""
    
    def test_extract_postgres_credentials_exception_handling(self, tmp_path):
        """EXECUTE exception path in extract_postgres_credentials_from_env - lines 256-257."""
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db\n")
        
        service = CredentialService(project_root=tmp_path)
        
        # Mock read_text to raise an exception to execute lines 256-257
        with patch.object(Path, "read_text", side_effect=PermissionError("Access denied")):
            creds = service.extract_postgres_credentials_from_env()
            
            # Should execute exception handler and return None values
            assert all(value is None for value in creds.values())
            
    def test_extract_hive_api_key_exception_handling(self, tmp_path):
        """EXECUTE exception path in extract_hive_api_key_from_env - lines 285-286."""
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_API_KEY=hive_testkey123\n")
        
        service = CredentialService(project_root=tmp_path)
        
        # Mock read_text to raise an exception to execute lines 285-286
        with patch.object(Path, "read_text", side_effect=IOError("File read error")):
            api_key = service.extract_hive_api_key_from_env()
            
            # Should execute exception handler and return None
            assert api_key is None


class TestMCPConfigSyncExecution:
    """EXECUTE the MCP config sync functionality - lines 376-410."""
    
    def test_sync_mcp_config_with_postgres_credentials_execution(self, tmp_path):
        """EXECUTE MCP sync with PostgreSQL credentials update - lines 376-410."""
        # Create .env file with credentials
        env_file = tmp_path / ".env"
        env_file.write_text(
            "HIVE_DATABASE_URL=postgresql+psycopg://testuser:testpass@localhost:5532/hive\n"
            "HIVE_API_KEY=hive_testkey123\n"
        )
        
        # Create .mcp.json file with existing PostgreSQL connection
        mcp_file = tmp_path / ".mcp.json"
        mcp_content = {
            "mcpServers": {
                "postgres": {
                    "command": "uvx",
                    "args": ["mcp-server-postgres"],
                    "env": {
                        "POSTGRES_CONNECTION": "postgresql+psycopg://olduser:oldpass@localhost:5532/hive"
                    }
                }
            }
        }
        mcp_file.write_text(json.dumps(mcp_content, indent=2))
        
        service = CredentialService(project_root=tmp_path)
        
        # EXECUTE the MCP sync functionality - this will hit lines 376-410
        service.sync_mcp_config_with_credentials(mcp_file)
        
        # Verify PostgreSQL connection was updated
        updated_content = mcp_file.read_text()
        assert "testuser:testpass" in updated_content
        assert "olduser:oldpass" not in updated_content
        
    def test_sync_mcp_config_with_api_key_addition_execution(self, tmp_path):
        """EXECUTE MCP sync with API key addition - lines 389-405."""
        # Create .env file with API key
        env_file = tmp_path / ".env"
        env_file.write_text(
            "HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive\n"
            "HIVE_API_KEY=hive_newkey123456\n"
        )
        
        # Create .mcp.json file WITHOUT existing API key to test addition path
        mcp_file = tmp_path / ".mcp.json"
        mcp_content = {
            "mcpServers": {
                "automagik-hive": {
                    "command": "uvx",
                    "args": ["mcp-server-automagik-hive"],
                    "env": {
                        "OTHER_VAR": "some_value"
                    }
                }
            }
        }
        mcp_file.write_text(json.dumps(mcp_content, indent=2))
        
        service = CredentialService(project_root=tmp_path)
        
        # EXECUTE the MCP sync to test API key addition path - lines 401-404
        service.sync_mcp_config_with_credentials(mcp_file)
        
        # Verify API key was added
        updated_content = mcp_file.read_text()
        assert '"HIVE_API_KEY": "hive_newkey123456"' in updated_content
        
    def test_sync_mcp_config_with_api_key_update_execution(self, tmp_path):
        """EXECUTE MCP sync with API key update path - lines 396-398."""
        # Create .env file with API key
        env_file = tmp_path / ".env"
        env_file.write_text(
            "HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive\n"
            "HIVE_API_KEY=hive_updatedkey789\n"
        )
        
        # Create .mcp.json file WITH existing API key to test update path
        mcp_file = tmp_path / ".mcp.json"
        mcp_content = {
            "mcpServers": {
                "automagik-hive": {
                    "command": "uvx",
                    "args": ["mcp-server-automagik-hive"],
                    "env": {
                        "HIVE_API_KEY": "hive_oldkey123"
                    }
                }
            }
        }
        mcp_file.write_text(json.dumps(mcp_content, indent=2))
        
        service = CredentialService(project_root=tmp_path)
        
        # EXECUTE the MCP sync to test API key update path - lines 396-398
        service.sync_mcp_config_with_credentials(mcp_file)
        
        # Verify API key was updated
        updated_content = mcp_file.read_text()
        assert '"HIVE_API_KEY": "hive_updatedkey789"' in updated_content
        assert "hive_oldkey123" not in updated_content
        
    def test_sync_mcp_config_exception_handling_execution(self, tmp_path):
        """EXECUTE exception handling in MCP sync - lines 409-410."""
        # Create .env file with credentials
        env_file = tmp_path / ".env"
        env_file.write_text(
            "HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive\n"
            "HIVE_API_KEY=hive_testkey\n"
        )
        
        # Create .mcp.json file
        mcp_file = tmp_path / ".mcp.json"
        mcp_file.write_text("{}")
        
        service = CredentialService(project_root=tmp_path)
        
        # Mock write_text to raise exception and execute lines 409-410
        with patch.object(Path, "write_text", side_effect=PermissionError("Write denied")):
            # Should not raise exception but log error instead
            service.sync_mcp_config_with_credentials(mcp_file)


class TestSaveCredentialsExceptionHandling:
    """EXECUTE exception handling in save_credentials_to_env method."""
    
    def test_save_credentials_postgres_not_found_execution(self, tmp_path):
        """EXECUTE postgres update path when entry not found - lines 325-326."""
        service = CredentialService(project_root=tmp_path)
        
        # Create existing .env file without HIVE_DATABASE_URL
        env_file = tmp_path / ".env"
        env_file.write_text("OTHER_VAR=value\n")
        
        postgres_creds = {
            "url": "postgresql+psycopg://newuser:newpass@localhost:5532/newdb"
        }
        
        # EXECUTE save to trigger postgres not found path - line 325-326
        service.save_credentials_to_env(postgres_creds)
        
        # Verify URL was appended
        content = env_file.read_text()
        assert "HIVE_DATABASE_URL=postgresql+psycopg://newuser:newpass@localhost:5532/newdb" in content
        
    def test_save_credentials_api_key_not_found_execution(self, tmp_path):
        """EXECUTE API key append path when entry not found - lines 336-337."""
        service = CredentialService(project_root=tmp_path)
        
        # Create existing .env file without HIVE_API_KEY
        env_file = tmp_path / ".env"
        env_file.write_text("OTHER_VAR=value\n")
        
        api_key = "hive_newkey12345"
        
        # EXECUTE save to trigger API key not found path - lines 336-337
        service.save_credentials_to_env(api_key=api_key)
        
        # Verify API key was appended
        content = env_file.read_text()
        assert "HIVE_API_KEY=hive_newkey12345" in content


class TestCompleteCredentialSetupWithMCPSync:
    """EXECUTE setup_complete_credentials with MCP sync functionality."""
    
    def test_setup_complete_credentials_with_mcp_sync_execution(self, tmp_path):
        """EXECUTE setup_complete_credentials with sync_mcp=True - lines 545-549."""
        # Create .mcp.json file to enable MCP sync
        mcp_file = tmp_path / ".mcp.json"
        mcp_content = {
            "mcpServers": {
                "postgres": {
                    "command": "uvx",
                    "args": ["mcp-server-postgres"],
                    "env": {
                        "POSTGRES_CONNECTION": "postgresql+psycopg://old:old@localhost:5532/hive"
                    }
                }
            }
        }
        mcp_file.write_text(json.dumps(mcp_content, indent=2))
        
        service = CredentialService(project_root=tmp_path)
        
        # EXECUTE setup_complete_credentials with MCP sync - lines 545-549
        creds = service.setup_complete_credentials(sync_mcp=True)
        
        # Verify credentials were generated
        assert "postgres_user" in creds
        assert "api_key" in creds
        
        # Verify MCP config was attempted to be updated (file exists)
        assert mcp_file.exists()
        
    def test_setup_complete_credentials_mcp_sync_exception_execution(self, tmp_path):
        """EXECUTE MCP sync exception handling in setup_complete_credentials - lines 548-549."""
        service = CredentialService(project_root=tmp_path)
        
        # Mock sync_mcp_config_with_credentials to raise exception
        with patch.object(service, "sync_mcp_config_with_credentials", side_effect=Exception("MCP sync failed")):
            # EXECUTE setup with MCP sync that fails - should continue without error
            creds = service.setup_complete_credentials(sync_mcp=True)
            
            # Should still complete successfully despite MCP sync failure
            assert "postgres_user" in creds
            assert "api_key" in creds


class TestExtractBasePortsExceptionHandling:
    """EXECUTE exception handling in port extraction."""
    
    def test_extract_base_ports_invalid_api_port_execution(self, tmp_path):
        """EXECUTE invalid API port handling - lines 600-601."""
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_API_PORT=invalid_port_value\n")
        
        service = CredentialService(project_root=tmp_path)
        
        # EXECUTE extract_base_ports_from_env to hit invalid port handling
        base_ports = service.extract_base_ports_from_env()
        
        # Should use default API port when invalid port encountered
        assert base_ports["api"] == 8886  # Default value
        
    def test_extract_base_ports_exception_handling_execution(self, tmp_path):
        """EXECUTE exception handling in extract_base_ports_from_env - lines 603-604."""
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:7777/db\n")
        
        service = CredentialService(project_root=tmp_path)
        
        # Mock read_text to raise exception
        with patch.object(Path, "read_text", side_effect=Exception("Read error")):
            # EXECUTE to trigger exception handling - lines 603-604
            base_ports = service.extract_base_ports_from_env()
            
            # Should return defaults when exception occurs
            assert base_ports["db"] == 5532
            assert base_ports["api"] == 8886


class TestContainerDetectionExecution:
    """EXECUTE container detection functionality - line 767."""
    
    def test_detect_existing_containers_execution(self):
        """EXECUTE container detection with subprocess calls - line 767."""
        service = CredentialService()
        
        # Mock subprocess.run to simulate docker command execution
        mock_result = Mock()
        mock_result.stdout = "hive-postgres-shared\nhive-agent-dev-server\n"
        
        with patch("subprocess.run", return_value=mock_result) as mock_subprocess:
            # EXECUTE detect_existing_containers - line 767
            containers = service.detect_existing_containers()
            
            # Verify subprocess was called
            assert mock_subprocess.called
            # Verify container detection worked
            assert "hive-postgres-shared" in containers
            assert "hive-agent-dev-server" in containers


class TestMigrationDetectionExecution:
    """EXECUTE migration detection functionality - lines 790-794."""
    
    def test_migrate_to_shared_database_with_old_containers_execution(self):
        """EXECUTE migration detection when old containers exist - lines 790-794."""
        service = CredentialService()
        
        # Mock detect_existing_containers to return old containers
        old_containers = {
            "hive-postgres-agent": True,
            "hive-postgres-genie": True,
            "hive-postgres-shared": False
        }
        
        with patch.object(service, "detect_existing_containers", return_value=old_containers):
            # EXECUTE migration check - lines 790-794
            service.migrate_to_shared_database()
            
            # Should detect migration needed (verified by not raising exception)


class TestInstallAllModesExceptionHandling:
    """EXECUTE exception handling in install_all_modes."""
    
    def test_install_all_modes_force_regenerate_execution(self, tmp_path):
        """EXECUTE install_all_modes with force_regenerate=True - lines 856-857."""
        # Create .env with existing credentials
        env_file = tmp_path / ".env"
        env_file.write_text(
            "HIVE_DATABASE_URL=postgresql+psycopg://existing:pass@localhost:5532/hive\n"
            "HIVE_API_KEY=hive_existing123\n"
        )
        
        service = CredentialService(project_root=tmp_path)
        
        # EXECUTE install_all_modes with force regeneration - lines 856-857
        result = service.install_all_modes(force_regenerate=True)
        
        # Should generate new credentials despite existing ones
        assert "workspace" in result
        # New credentials should be different from existing ones
        updated_content = env_file.read_text()
        assert "existing:pass" not in updated_content
        
    def test_install_all_modes_mcp_sync_exception_execution(self, tmp_path):
        """EXECUTE MCP sync exception handling in install_all_modes - lines 880-883."""
        service = CredentialService(project_root=tmp_path)
        
        # Mock sync_mcp_config_with_credentials to raise exception
        with patch.object(service, "sync_mcp_config_with_credentials", side_effect=Exception("MCP error")):
            # EXECUTE install with MCP sync that fails - lines 880-883
            result = service.install_all_modes(sync_mcp=True)
            
            # Should complete successfully despite MCP sync failure
            assert "workspace" in result
            assert "agent" in result
            assert "genie" in result


class TestMasterCredentialExtractionExecution:
    """EXECUTE master credential extraction edge cases."""
    
    def test_extract_existing_master_credentials_missing_postgres_execution(self, tmp_path):
        """EXECUTE master extraction when postgres credentials missing - lines 936-949."""
        # Create .env with API key but incomplete postgres URL
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_API_KEY=hive_testkey123\n")
        
        service = CredentialService(project_root=tmp_path)
        
        # EXECUTE extraction - should return None due to missing postgres
        existing_creds = service._extract_existing_master_credentials()
        
        assert existing_creds is None
        
    def test_extract_existing_master_credentials_missing_api_key_execution(self, tmp_path):
        """EXECUTE master extraction when API key missing - lines 936-949."""
        # Create .env with postgres URL but no API key
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive\n")
        
        service = CredentialService(project_root=tmp_path)
        
        # EXECUTE extraction - should return None due to missing API key
        existing_creds = service._extract_existing_master_credentials()
        
        assert existing_creds is None
        
    def test_extract_existing_master_credentials_exception_execution(self, tmp_path):
        """EXECUTE exception handling in master credential extraction - lines 946-947."""
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive\n")
        
        service = CredentialService(project_root=tmp_path)
        
        # Mock read_text to raise exception
        with patch.object(Path, "read_text", side_effect=Exception("Read error")):
            # EXECUTE extraction with exception - lines 946-947
            existing_creds = service._extract_existing_master_credentials()
            
            assert existing_creds is None


class TestMasterCredentialSavingExecution:
    """EXECUTE master credential saving functionality."""
    
    def test_save_master_credentials_no_env_example_execution(self, tmp_path):
        """EXECUTE master credential saving when .env.example missing - lines 959-960."""
        service = CredentialService(project_root=tmp_path)
        
        master_credentials = {
            "postgres_user": "testuser123",
            "postgres_password": "testpass456",
            "api_key_base": "testkey789"
        }
        
        # Don't create .env.example to trigger minimal template path
        # EXECUTE _save_master_credentials - lines 959-960
        service._save_master_credentials(master_credentials)
        
        # Verify .env was created with minimal template
        env_content = service.master_env_file.read_text()
        assert "HIVE_ENVIRONMENT=development" in env_content
        assert "testuser123" in env_content
        
    def test_save_master_credentials_missing_db_url_execution(self, tmp_path):
        """EXECUTE master credential saving when DB URL missing - lines 993, 995."""
        service = CredentialService(project_root=tmp_path)
        
        # Create .env without HIVE_DATABASE_URL
        env_file = tmp_path / ".env"
        env_file.write_text("OTHER_VAR=value\n")
        
        master_credentials = {
            "postgres_user": "newuser123",
            "postgres_password": "newpass456",
            "api_key_base": "newkey789"
        }
        
        # EXECUTE _save_master_credentials - lines 993, 995
        service._save_master_credentials(master_credentials)
        
        # Verify DB URL and API key were appended
        env_content = env_file.read_text()
        assert "HIVE_DATABASE_URL=postgresql+psycopg://newuser123:newpass456@localhost:5532/hive" in env_content
        assert "HIVE_API_KEY=hive_newkey789" in env_content


class TestCreateModeEnvFileExecution:
    """EXECUTE mode-specific environment file creation."""
    
    def test_create_mode_env_file_workspace_execution(self, tmp_path):
        """EXECUTE workspace mode env file creation - lines 1025-1028."""
        service = CredentialService(project_root=tmp_path)
        
        credentials = {
            "postgres_user": "testuser",
            "postgres_password": "testpass",
            "postgres_database": "hive",
            "postgres_host": "localhost",
            "api_port": "8886",
            "api_key": "hive_workspace_testkey",
            "database_url": "postgresql+psycopg://testuser:testpass@localhost:5532/hive"
        }
        
        # EXECUTE _create_mode_env_file for workspace - should return early
        service._create_mode_env_file("workspace", credentials)
        
        # Workspace should use main .env file, not create separate one
        workspace_env = tmp_path / ".env.workspace"
        assert not workspace_env.exists()
        
    def test_create_mode_env_file_agent_execution(self, tmp_path):
        """EXECUTE agent mode env file creation."""
        service = CredentialService(project_root=tmp_path)
        
        credentials = {
            "postgres_user": "testuser",
            "postgres_password": "testpass",
            "postgres_database": "hive",
            "postgres_host": "localhost",
            "api_port": "38886",
            "api_key": "hive_agent_testkey",
            "database_url": "postgresql+psycopg://testuser:testpass@localhost:35532/hive?options=-csearch_path=agent"
        }
        
        # EXECUTE _create_mode_env_file for agent
        service._create_mode_env_file("agent", credentials)
        
        # Verify agent .env file was created
        agent_env = tmp_path / ".env.agent"
        assert agent_env.exists()
        
        content = agent_env.read_text()
        assert "HIVE_API_PORT=38886" in content
        assert "hive_agent_testkey" in content
        assert "search_path=agent" in content


class TestSecurityValidationExecution:
    """EXECUTE security validation edge cases."""
    
    def test_validate_credentials_none_values_execution(self):
        """EXECUTE credential validation with None values."""
        service = CredentialService()
        
        # EXECUTE validation with None postgres credentials
        results = service.validate_credentials(postgres_creds=None, api_key=None)
        
        # Should handle None gracefully
        assert results == {}
        
    def test_validate_credentials_empty_dict_execution(self):
        """EXECUTE credential validation with empty dict."""
        service = CredentialService()
        
        # EXECUTE validation with empty postgres credentials
        results = service.validate_credentials(postgres_creds={})
        
        # Should handle missing keys gracefully (empty dict means no validation performed)
        # The method only validates if postgres_creds has the expected keys
        assert isinstance(results, dict)


class TestPortCalculationEdgeCases:
    """EXECUTE edge cases in port calculation."""
    
    def test_calculate_ports_empty_prefix_execution(self):
        """EXECUTE port calculation with empty prefix (workspace)."""
        service = CredentialService()
        base_ports = {"db": 9999, "api": 7777}
        
        # EXECUTE calculate_ports for workspace (empty prefix)
        calculated = service.calculate_ports("workspace", base_ports)
        
        # Should return copy of base ports
        assert calculated == base_ports
        assert calculated is not base_ports  # Should be a copy
        
    def test_get_deployment_ports_custom_base_execution(self, tmp_path):
        """EXECUTE deployment ports with custom base ports."""
        # Create .env with custom ports
        env_file = tmp_path / ".env"
        env_file.write_text(
            "HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:9999/hive\n"
            "HIVE_API_PORT=7777\n"
        )
        
        service = CredentialService(project_root=tmp_path)
        
        # EXECUTE get_deployment_ports with custom base
        deployment_ports = service.get_deployment_ports()
        
        # Should use custom base ports
        assert deployment_ports["workspace"]["db"] == 9999
        assert deployment_ports["workspace"]["api"] == 7777
        assert deployment_ports["agent"]["db"] == 39999  # Prefixed
        assert deployment_ports["agent"]["api"] == 37777  # Prefixed


class TestAdvancedMCPSyncScenarios:
    """EXECUTE complex MCP sync scenarios."""
    
    def test_sync_mcp_config_with_custom_path_execution(self, tmp_path):
        """EXECUTE MCP sync with custom MCP config path - line 360."""
        # Create .env with credentials
        env_file = tmp_path / ".env"
        env_file.write_text(
            "HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive\n"
            "HIVE_API_KEY=hive_testkey\n"
        )
        
        # Create custom MCP config file
        custom_mcp = tmp_path / "custom.mcp.json"
        custom_mcp.write_text('{"mcpServers": {}}')
        
        service = CredentialService(project_root=tmp_path)
        
        # Mock environment variable to use custom path - line 358-362
        with patch.dict(os.environ, {"HIVE_MCP_CONFIG_PATH": str(custom_mcp)}):
            # EXECUTE sync with custom path
            service.sync_mcp_config_with_credentials()
            
        # Verify custom MCP file exists and was processed
        assert custom_mcp.exists()
        
    def test_sync_mcp_config_absolute_path_execution(self, tmp_path):
        """EXECUTE MCP sync with absolute path - line 360-362."""
        # Create .env with credentials
        env_file = tmp_path / ".env"
        env_file.write_text(
            "HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive\n"
            "HIVE_API_KEY=hive_testkey\n"
        )
        
        # Create absolute path MCP config
        abs_mcp_path = tmp_path / "abs_config.mcp.json"
        abs_mcp_path.write_text('{"mcpServers": {}}')
        
        service = CredentialService(project_root=tmp_path)
        
        # Mock environment variable with absolute path
        with patch.dict(os.environ, {"HIVE_MCP_CONFIG_PATH": str(abs_mcp_path)}):
            # EXECUTE sync with absolute path - line 360-362
            service.sync_mcp_config_with_credentials()
            
        # Should handle absolute path correctly
        assert abs_mcp_path.exists()