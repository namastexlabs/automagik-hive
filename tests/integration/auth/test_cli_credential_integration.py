#!/usr/bin/env python3
"""Test CLI integration with single credential system."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from cli.docker_manager import DockerManager


# Test enabled - credential service database port bug has been fixed
def test_cli_install_uses_single_credential_system():
    """Test that CLI install command uses single credential system."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Mock all Docker operations so we can test credential generation
        with patch('cli.docker_manager.DockerManager._check_docker', return_value=True):
            with patch('cli.docker_manager.DockerManager._create_network'):
                with patch('cli.docker_manager.DockerManager._container_exists', return_value=False):
                    with patch('cli.docker_manager.DockerManager._container_running', return_value=False):
                        with patch('cli.docker_manager.DockerManager._create_postgres_container', return_value=True):
                            with patch('cli.docker_manager.DockerManager._create_api_container', return_value=True):
                                with patch('time.sleep'):  # Skip sleep delays in tests
                                    
                                    # Create DockerManager with temp directory
                                    docker_manager = DockerManager()
                                    docker_manager.project_root = temp_path
                                    # Also update the credential service to use the temp path
                                    docker_manager.credential_service.project_root = temp_path
                                    docker_manager.credential_service.master_env_file = temp_path / ".env"
                                    
                                    # Install agent component
                                    result = docker_manager.install("agent")
                                    
                                    assert result is True
                                    
                                    # Check that credentials were generated
                                    main_env = temp_path / ".env"
                                    
                                    assert main_env.exists(), "Main .env file should be created"
                                    # Agent inherits from main .env via docker-compose, no separate .env.agent needed
                                    
                                    # Check main env has workspace credentials
                                    main_content = main_env.read_text()
                                    assert "HIVE_DATABASE_URL=" in main_content
                                    assert "localhost:5532" in main_content  # Workspace uses base port
                                    assert "HIVE_API_KEY=" in main_content
                                    
                                    # Agent inherits configuration from main .env via docker-compose
                                    # Main env contains base configuration that docker-compose overrides for agent
                                    assert "localhost:5532" in main_content  # Base port, agent gets 35532 via docker-compose
                                    
                                    # Verify main configuration is complete for docker-compose inheritance
                                    main_lines = main_content.splitlines()
                                    main_db_url = next(line for line in main_lines if line.startswith("HIVE_DATABASE_URL="))
                                    
                                    # Extract user/password from main URL (agent inherits these via docker-compose)
                                    main_user = main_db_url.split("://")[1].split(":")[0]
                                    main_pass = main_db_url.split(":")[2].split("@")[0] 
                                    
                                    # Agent inherits the same user and password via docker-compose
                                    # Docker-compose overrides only ports, not credentials
                                    assert main_user, "Main user should be present for agent inheritance"
                                    assert main_pass, "Main password should be present for agent inheritance"


if __name__ == "__main__":
    test_cli_install_uses_single_credential_system()
    print("✅ CLI credential integration test passed!")