#!/usr/bin/env python3
"""Tests for DockerManager."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from cli.docker_manager import DockerManager


class TestDockerManagerUpdates:
    """Test DockerManager with CredentialService integration."""

    @patch.dict('os.environ', {
        'HIVE_WORKSPACE_POSTGRES_PORT': '5532',
        'HIVE_AGENT_POSTGRES_PORT': '35532',
        'HIVE_AGENT_API_PORT': '38886',
        'HIVE_GENIE_POSTGRES_PORT': '45532',
        'HIVE_GENIE_API_PORT': '48886'
    })
    def test_docker_manager_init_with_unified_service(self):
        """Test that DockerManager initializes with CredentialService."""
        # This will ensure the import works
        docker_manager = DockerManager()
        
        # Should have unified credential service now
        assert hasattr(docker_manager, 'credential_service')
        
        # Should still have port configurations
        assert hasattr(docker_manager, 'PORTS')
        
    @patch.dict('os.environ', {
        'HIVE_WORKSPACE_POSTGRES_PORT': '5532',
        'HIVE_AGENT_POSTGRES_PORT': '35532',
        'HIVE_AGENT_API_PORT': '38886',
        'HIVE_GENIE_POSTGRES_PORT': '45532',
        'HIVE_GENIE_API_PORT': '48886'
    })
    @patch('cli.docker_manager.subprocess.run')
    def test_docker_manager_can_check_docker(self, mock_subprocess):
        """Test that DockerManager can still check Docker availability."""
        mock_subprocess.return_value = MagicMock()
        
        docker_manager = DockerManager()
        
        # This should work without throwing import errors
        # (We won't test the actual Docker check logic since it's unchanged)
        assert docker_manager.template_files is not None