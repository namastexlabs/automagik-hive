#!/usr/bin/env python3
"""Integration tests for single credential source implementation."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from lib.auth.credential_service import CredentialService
from cli.docker_manager import DockerManager


class TestSingleCredentialIntegration:
    """Test complete single credential integration."""

    def test_unified_service_port_calculation(self, tmp_path):
        """Test that CredentialService calculates ports correctly with prefixed database approach."""
        # Create .env with custom base ports
        env_file = tmp_path / ".env"
        env_file.write_text("""
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:6000/hive
HIVE_API_PORT=9000
""")
        
        service = CredentialService(project_root=tmp_path)
        
        # Test port calculation for all modes
        deployment_ports = service.get_deployment_ports()
        
        # Workspace uses base ports
        assert deployment_ports["workspace"]["db"] == 6000
        assert deployment_ports["workspace"]["api"] == 9000
        
        # PREFIXED DATABASE APPROACH: Each mode uses prefixed database and API ports
        # Agent uses prefixed db port and prefixed API port
        assert deployment_ports["agent"]["db"] == 36000   # Prefixed database port (3 + 6000)
        assert deployment_ports["agent"]["api"] == 39000  # Prefixed API port (3 + 9000)
        
        # Genie uses prefixed db port and prefixed API port  
        assert deployment_ports["genie"]["db"] == 46000   # Prefixed database port (4 + 6000)
        assert deployment_ports["genie"]["api"] == 49000  # Prefixed API port (4 + 9000)

    def test_unified_credential_generation(self, tmp_path):
        """Test that credentials are generated consistently across modes."""
        service = CredentialService(project_root=tmp_path)
        
        # Generate credentials for all modes
        all_credentials = service.install_all_modes()
        
        # All modes should exist
        assert "workspace" in all_credentials
        assert "agent" in all_credentials
        assert "genie" in all_credentials
        
        workspace_creds = all_credentials["workspace"]
        agent_creds = all_credentials["agent"]
        genie_creds = all_credentials["genie"]
        
        # Same user and password across all modes
        assert workspace_creds["postgres_user"] == agent_creds["postgres_user"]
        assert workspace_creds["postgres_user"] == genie_creds["postgres_user"]
        assert workspace_creds["postgres_password"] == agent_creds["postgres_password"]
        assert workspace_creds["postgres_password"] == genie_creds["postgres_password"]
        
        # PREFIXED DATABASE APPROACH: Different postgres port per mode, different API ports per mode  
        assert workspace_creds["postgres_port"] == "5532"   # Default base (workspace)
        assert agent_creds["postgres_port"] == "35532"      # Prefixed database port (3 + 5532)
        assert genie_creds["postgres_port"] == "45532"      # Prefixed database port (4 + 5532)
        
        assert workspace_creds["api_port"] == "8886"        # Default base
        assert agent_creds["api_port"] == "38886"           # 3 + 8886
        assert genie_creds["api_port"] == "48886"           # 4 + 8886
        
        # Different API keys with mode prefixes
        assert workspace_creds["api_key"].startswith("hive_workspace_")
        assert agent_creds["api_key"].startswith("hive_agent_")
        assert genie_creds["api_key"].startswith("hive_genie_")
        
        # Same base API key (after mode prefix)
        workspace_base = workspace_creds["api_key"].replace("hive_workspace_", "")
        agent_base = agent_creds["api_key"].replace("hive_agent_", "")
        genie_base = genie_creds["api_key"].replace("hive_genie_", "")
        
        assert workspace_base == agent_base == genie_base

    @patch('cli.docker_manager.time.sleep')  # Mock the 8-second health check delay
    @patch('cli.docker_manager.subprocess.run')
    def test_docker_manager_uses_unified_credentials(self, mock_subprocess, mock_sleep, tmp_path):
        """Test that DockerManager uses CredentialService - optimized for fast execution."""
        # Mock successful Docker operations
        mock_subprocess.return_value = MagicMock()
        
        # Create DockerManager with temporary project root
        with patch('cli.docker_manager.DockerManager._check_docker', return_value=True):
            with patch('cli.docker_manager.DockerManager._create_network'):
                with patch('cli.docker_manager.DockerManager._container_exists', return_value=False):
                    with patch('cli.docker_manager.DockerManager._container_running', return_value=False):
                        # Mock the actual container creation method that gets called
                        with patch('cli.docker_manager.DockerManager._create_containers_via_compose', return_value=True):
                            docker_manager = DockerManager()
                            docker_manager.project_root = tmp_path
                            docker_manager.credential_service = CredentialService(project_root=tmp_path)
                            
                            # Test that the credential service is CredentialService
                            assert isinstance(docker_manager.credential_service, CredentialService)
                            
                            # Test that install would use unified credentials
                            with patch.object(docker_manager.credential_service, 'install_all_modes') as mock_install:
                                mock_install.return_value = {
                                    "agent": {
                                        "postgres_user": "test_user",
                                        "postgres_password": "test_pass",
                                        "postgres_database": "hive_agent",
                                        "postgres_host": "localhost",
                                        "postgres_port": "35532",
                                        "api_port": "38886",
                                        "api_key": "hive_agent_test_key"
                                    }
                                }
                                
                                result = docker_manager.install("agent")
                                
                            # Should succeed and use unified credentials
                            assert result is True
                            mock_install.assert_called_once_with(["agent"])
                            # Verify that the sleep was called (but mocked, so no actual delay)
                            mock_sleep.assert_called_once_with(8)

    def test_environment_file_organization(self, tmp_path):
        """Test that environment files are created in proper docker folder structure."""
        service = CredentialService(project_root=tmp_path)
        
        # Install all modes
        service.install_all_modes()
        
        # Check that main .env exists
        assert (tmp_path / ".env").exists()
        
        # Agent inherits from main .env via docker-compose, no separate .env.agent needed
        # This matches the new docker-compose inheritance implementation
        
        # The workspace uses the main .env file
        main_env = (tmp_path / ".env").read_text()
        assert "HIVE_DATABASE_URL=" in main_env
        assert "HIVE_API_KEY=" in main_env
        
        # Agent inherits configuration from main .env via docker-compose
        # Verify main .env has the configuration that agent will inherit
        assert "HIVE_DATABASE_URL=" in main_env
        assert "8886" in main_env  # Main API port, agent gets 38886 via docker-compose
        
        # Genie inherits configuration from main .env via docker-compose as well
        # No separate .env.genie file needed - unified credential system

    def test_backward_compatibility(self, tmp_path):
        """Test that existing installations continue to work."""
        # Create existing .env file with workspace credentials
        env_file = tmp_path / ".env"
        env_file.write_text("""
HIVE_DATABASE_URL=postgresql+psycopg://existing_user:existing_pass@localhost:5532/hive
HIVE_API_KEY=hive_existing_key_12345
""")
        
        service = CredentialService(project_root=tmp_path)
        
        # Should reuse existing credentials
        existing_master = service._extract_existing_master_credentials()
        assert existing_master is not None
        assert existing_master["postgres_user"] == "existing_user"
        assert existing_master["postgres_password"] == "existing_pass"
        
        # When installing with existing credentials, should reuse them
        all_credentials = service.install_all_modes(force_regenerate=False)
        
        # All modes should use the same base credentials
        for mode in ["workspace", "agent", "genie"]:
            assert all_credentials[mode]["postgres_user"] == "existing_user"
            assert all_credentials[mode]["postgres_password"] == "existing_pass"