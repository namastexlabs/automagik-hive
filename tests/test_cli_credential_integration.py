#!/usr/bin/env python3
"""Test CLI integration with single credential system."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from cli.docker_manager import DockerManager


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
                                    agent_env = temp_path / ".env.agent"
                                    
                                    assert main_env.exists(), "Main .env file should be created"
                                    assert agent_env.exists(), "Agent .env file should be created"
                                    
                                    # Check main env has workspace credentials
                                    main_content = main_env.read_text()
                                    assert "HIVE_DATABASE_URL=" in main_content
                                    assert "localhost:5532" in main_content  # Workspace uses base port
                                    assert "HIVE_API_KEY=" in main_content
                                    
                                    # Check agent env has agent-specific ports
                                    agent_content = agent_env.read_text()
                                    assert "HIVE_DATABASE_URL=" in agent_content
                                    assert "localhost:35532" in agent_content  # Agent uses prefixed port
                                    assert "HIVE_API_KEY=" in agent_content
                                    
                                    # Extract credentials to verify they share the same base
                                    main_lines = main_content.splitlines()
                                    agent_lines = agent_content.splitlines()
                                    
                                    main_db_url = next(line for line in main_lines if line.startswith("HIVE_DATABASE_URL="))
                                    agent_db_url = next(line for line in agent_lines if line.startswith("HIVE_DATABASE_URL="))
                                    
                                    # Extract user/password from URLs
                                    main_user = main_db_url.split("://")[1].split(":")[0]
                                    agent_user = agent_db_url.split("://")[1].split(":")[0]
                                    
                                    main_pass = main_db_url.split(":")[2].split("@")[0] 
                                    agent_pass = agent_db_url.split(":")[2].split("@")[0]
                                    
                                    # Should be the same user and password
                                    assert main_user == agent_user, "User should be the same across modes"
                                    assert main_pass == agent_pass, "Password should be the same across modes"


if __name__ == "__main__":
    test_cli_install_uses_single_credential_system()
    print("✅ CLI credential integration test passed!")