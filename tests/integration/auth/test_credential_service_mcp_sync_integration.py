#!/usr/bin/env python3
"""
Integration tests for CredentialService MCP sync behavior.

RED PHASE TESTS: These tests validate real-world integration scenarios and ensure
the MCP sync behavior works correctly with the broader system.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call, Mock
import pytest
import json

from lib.auth.credential_service import CredentialService


class TestCredentialServiceMcpSyncRealWorldScenarios:
    """Test real-world usage scenarios for MCP sync behavior."""

    def test_makefile_workspace_install_no_mcp_sync(self, tmp_path):
        """
        FAILING TEST: Test Makefile-style workspace installation without MCP sync.
        
        This simulates how the Makefile currently calls credential service for workspace setup.
        Expected behavior: Should work without MCP sync by default.
        """
        # Simulate Makefile environment
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Simulate typical Makefile workspace install
            result = service.setup_complete_credentials(
                postgres_host="localhost",
                postgres_port=5532,
                postgres_database="hive"
            )
            
            # Should generate credentials successfully
            assert result is not None
            assert 'postgres_user' in result
            assert 'postgres_password' in result
            assert 'postgres_database' in result
            assert 'api_key' in result
            
            # CRITICAL: Should NOT sync MCP for workspace install
            mock_sync.assert_not_called()

    def test_makefile_agent_install_with_mcp_sync(self, tmp_path):
        """
        FAILING TEST: Test Makefile-style agent installation with MCP sync.
        
        This simulates how the Makefile should call credential service for agent setup.
        Expected behavior: Should support MCP sync when explicitly requested.
        """
        # Simulate Makefile environment for agent
        service = CredentialService(project_root=tmp_path)
        
        # Create .mcp.json file that would exist for agent development
        mcp_file = tmp_path / ".mcp.json"
        mcp_file.write_text('{"mcpServers": {}}')
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Simulate Makefile agent install with MCP sync
            result = service.setup_complete_credentials(
                postgres_host="localhost",
                postgres_port=5532,
                postgres_database="hive",
                sync_mcp=True  # Agent development needs MCP sync
            )
            
            # Should generate credentials successfully
            assert result is not None
            assert 'postgres_user' in result
            assert 'api_key' in result
            
            # Should sync MCP for agent install
            mock_sync.assert_called_once()

    def test_cli_workspace_mode_installation(self, tmp_path):
        """
        FAILING TEST: Test CLI-style workspace mode installation.
        
        This simulates how the CLI calls install_all_modes for workspace setup.
        Expected behavior: Should work without MCP sync by default.
        """
        # Simulate CLI environment
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                # Simulate CLI workspace install
                result = service.install_all_modes(modes=["workspace"])
                
                # Should install successfully
                assert result is not None
                assert "workspace" in result
                
                # Should NOT sync MCP for workspace by default
                mock_sync.assert_not_called()

    def test_cli_agent_mode_installation_with_mcp_sync(self, tmp_path):
        """
        FAILING TEST: Test CLI-style agent mode installation with MCP sync.
        
        This simulates how the CLI should support agent installation with MCP sync.
        Expected behavior: Should support sync_mcp parameter.
        """
        # Simulate CLI environment for agent mode
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                # Simulate CLI agent install with MCP sync
                result = service.install_all_modes(
                    modes=["agent"], 
                    sync_mcp=True
                )
                
                # Should install successfully
                assert result is not None
                assert "agent" in result
                
                # Should sync MCP for agent when requested
                mock_sync.assert_called_once()

    def test_development_workflow_mixed_modes(self, tmp_path):
        """
        FAILING TEST: Test development workflow with mixed workspace/agent modes.
        
        This simulates a developer setting up both workspace and agent environments.
        Expected behavior: Should control MCP sync appropriately.
        """
        # Simulate development environment
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                # Phase 1: Install workspace (no MCP sync needed)
                workspace_result = service.install_all_modes(modes=["workspace"])
                
                assert workspace_result is not None
                assert "workspace" in workspace_result
                mock_sync.assert_not_called()
                
                mock_sync.reset_mock()
                
                # Phase 2: Add agent mode with MCP sync for development
                agent_result = service.install_all_modes(
                    modes=["agent"], 
                    sync_mcp=True
                )
                
                assert agent_result is not None
                assert "agent" in agent_result
                mock_sync.assert_called_once()

    def test_production_deployment_automation(self, tmp_path):
        """
        Test production deployment automation scenarios.
        
        This simulates automated production deployments with specific MCP sync requirements.
        Expected behavior: Should support both automated and manual MCP sync control.
        """
        # Simulate production deployment environment
        service = CredentialService(project_root=tmp_path)
        
        # Create minimal .env.example for production template
        env_example = tmp_path / ".env.example"
        env_example.write_text("""
# Production Environment Template
HIVE_ENVIRONMENT=production
HIVE_LOG_LEVEL=INFO
HIVE_API_HOST=0.0.0.0
HIVE_API_PORT=8886
HIVE_DATABASE_URL=postgresql+psycopg://template-user:template-pass@localhost:5532/hive
HIVE_API_KEY=template-api-key
""")
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                
                # Production workspace deployment (no MCP sync)
                prod_result = service.install_all_modes(
                    modes=["workspace"],
                    force_regenerate=True,
                    sync_mcp=False  # Explicit no sync for production
                )
                
                assert prod_result is not None
                assert "workspace" in prod_result
                mock_sync.assert_not_called()
                
                # Verify .env was created from template
                env_file = tmp_path / ".env"
                assert env_file.exists()
                
                env_content = env_file.read_text()
                assert "HIVE_ENVIRONMENT=production" in env_content
                assert "template-user" not in env_content  # Should be replaced

    def test_docker_compose_integration_scenario(self, tmp_path):
        """
        Test integration with Docker Compose workflows.
        
        This simulates how credential service integrates with Docker-based development.
        Expected behavior: Should handle Docker environment variables correctly.
        """
        # Simulate Docker Compose environment
        service = CredentialService(project_root=tmp_path)
        
        # Create docker environment structure
        docker_dir = tmp_path / "docker" / "agent"
        docker_dir.mkdir(parents=True)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                
                # Install agent mode for Docker development
                result = service.install_all_modes(
                    modes=["agent"],
                    sync_mcp=True  # Docker agent needs MCP sync
                )
                
                assert result is not None
                assert "agent" in result
                mock_sync.assert_called_once()
                
                # Verify main environment file exists for docker-compose inheritance
                main_env = tmp_path / ".env"
                assert main_env.exists()
                
                main_content = main_env.read_text()
                # Should contain configuration that agent inherits via docker-compose
                assert "8886" in main_content  # Main API port, agent gets 38886 via docker-compose  
                assert result["agent"]["postgres_user"] in main_content


class TestCredentialServiceMcpSyncErrorHandling:
    """Test error handling and recovery scenarios for MCP sync."""

    def test_mcp_sync_failure_does_not_break_credential_generation(self, tmp_path):
        """
        FAILING TEST: MCP sync failure should not prevent credential generation.
        
        Expected behavior: Robust error handling for MCP sync failures.
        Current behavior: Need to implement error handling wrapper.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Create MCP file that will cause sync to fail
        mcp_file = tmp_path / ".mcp.json" 
        mcp_file.write_text("invalid json content")
        
        # Mock sync to raise exception
        def failing_sync():
            raise Exception("MCP file is corrupted")
            
        with patch.object(service, 'sync_mcp_config_with_credentials', side_effect=failing_sync):
            # Even with sync failure, credential generation should succeed
            result = service.setup_complete_credentials(sync_mcp=True)
            
            # Credentials should still be generated despite MCP sync failure
            assert result is not None
            assert 'postgres_user' in result
            assert 'api_key' in result
            
            # .env file should still be created
            env_file = tmp_path / ".env"
            assert env_file.exists()

    def test_missing_mcp_file_graceful_handling(self, tmp_path):
        """
        Test graceful handling when .mcp.json file doesn't exist.
        
        Expected behavior: Should not fail if MCP file doesn't exist.
        """
        # Create service with no MCP file
        service = CredentialService(project_root=tmp_path)
        
        # Should not raise exception even with sync_mcp=True
        result = service.setup_complete_credentials(sync_mcp=True)
        
        # Should still generate credentials
        assert result is not None
        assert 'postgres_user' in result
        assert 'api_key' in result

    def test_invalid_credentials_mcp_sync_handling(self, tmp_path):
        """
        Test MCP sync handling when credentials are invalid or missing.
        
        Expected behavior: Should handle invalid credentials gracefully.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Create MCP file
        mcp_file = tmp_path / ".mcp.json"
        mcp_file.write_text('{"mcpServers": {}}')
        
        # Create .env with incomplete credentials
        env_file = tmp_path / ".env"
        env_file.write_text("INCOMPLETE_CONFIG=true")
        
        # Should handle gracefully - either skip sync or handle missing creds
        try:
            service.sync_mcp_config_with_credentials()
            # If no exception, sync handled missing credentials gracefully
            assert True
        except Exception as e:
            # If exception, should be a reasonable error message
            assert "credentials" in str(e).lower() or "missing" in str(e).lower()


class TestCredentialServiceMcpSyncPerformance:
    """Test performance and efficiency of MCP sync operations."""

    def test_mcp_sync_performance_single_call(self, tmp_path):
        """
        Test that MCP sync is only called once during install_all_modes.
        
        Expected behavior: Regardless of number of modes, sync once per installation.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Create MCP file
        mcp_file = tmp_path / ".mcp.json"
        mcp_file.write_text('{"mcpServers": {}}')
        
        # Track call count
        sync_calls = []
        
        def track_sync():
            sync_calls.append(True)
            # Call original method
            return service.sync_mcp_config_with_credentials.__wrapped__(service)
            
        with patch.object(service, 'sync_mcp_config_with_credentials', side_effect=track_sync):
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                
                # Install multiple modes
                service.install_all_modes(
                    modes=["workspace", "agent", "genie"],
                    sync_mcp=True
                )
                
                # Should have called sync exactly once
                assert len(sync_calls) == 1

    def test_idempotent_mcp_sync_operations(self, tmp_path):
        """
        Test that multiple MCP sync operations are idempotent.
        
        Expected behavior: Multiple syncs should be safe and produce consistent results.
        """
        # Override environment variable to use .mcp.json in test temp dir
        with patch.dict('os.environ', {'HIVE_MCP_CONFIG_PATH': '.mcp.json'}):
            # Create service with temp directory
            service = CredentialService(project_root=tmp_path)
            
            # Create MCP file with initial content
            mcp_file = tmp_path / ".mcp.json"
            initial_content = {
                "mcpServers": {
                    "postgres": {
                        "command": "uv",
                        "args": ["tool", "run", "--from", "mcp-server-postgres", "mcp-server-postgres"],
                        "env": {
                            "POSTGRESQL_CONNECTION_STRING": "postgresql+psycopg://old-user:old-pass@localhost:5532/hive",
                            "HIVE_API_KEY": "old-key"
                        }
                    }
                }
            }
            mcp_file.write_text(json.dumps(initial_content, indent=2))
            
            # Generate credentials
            result = service.setup_complete_credentials(sync_mcp=True)
            
            # Capture state after first sync
            first_sync_content = mcp_file.read_text()
            
            # Sync again multiple times
            service.sync_mcp_config_with_credentials()
            service.sync_mcp_config_with_credentials()
            
            # Should be identical after multiple syncs
            final_content = mcp_file.read_text()
            assert first_sync_content == final_content
            
            # Should contain new credentials in the connection string, not old ones
            assert result['postgres_user'] in final_content
            assert result['postgres_password'] in final_content
            assert "old-user:old-pass" not in final_content


class TestCredentialServiceMcpSyncConfiguration:
    """Test configuration and customization of MCP sync behavior."""

    def test_custom_mcp_file_path_support(self, tmp_path):
        """
        Test support for custom MCP file paths via environment variable.
        
        Expected behavior: Should respect HIVE_MCP_CONFIG_PATH environment variable.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Create custom MCP file location
        custom_dir = tmp_path / "config"
        custom_dir.mkdir()
        custom_mcp_file = custom_dir / "custom.mcp.json"
        # Create MCP structure with postgres and automagik-hive servers for credential sync
        custom_mcp_file.write_text('''{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql+psycopg://old_user:old_pass@localhost:35532/hive_agent"
      ]
    },
    "automagik-hive": {
      "command": "uvx",
      "args": [
        "automagik-tools@0.8.17",
        "tool",
        "automagik-hive"
      ],
      "env": {
        "HIVE_API_BASE_URL": "http://localhost:38886",
        "HIVE_API_KEY": "old_api_key",
        "HIVE_TIMEOUT": "300"
      }
    }
  }
}''')
        
        # Set environment variable for custom path
        with patch.dict('os.environ', {'HIVE_MCP_CONFIG_PATH': str(custom_mcp_file)}):
            # Generate credentials with sync
            result = service.setup_complete_credentials(sync_mcp=True)
            
            # Verify custom file was updated
            custom_content = custom_mcp_file.read_text()
            
            # Should contain updated credentials
            assert result['postgres_user'] in custom_content
            assert result['api_key'] in custom_content
            
            # Original .mcp.json should not exist
            default_mcp = tmp_path / ".mcp.json"
            assert not default_mcp.exists()

    def test_mcp_sync_preserves_non_credential_config(self, tmp_path):
        """
        Test that MCP sync preserves existing non-credential configuration.
        
        Expected behavior: Should only update credential-related fields.
        """
        # Clear environment pollution to ensure test isolation
        import os
        original_env = os.environ.get('HIVE_MCP_CONFIG_PATH')
        if 'HIVE_MCP_CONFIG_PATH' in os.environ:
            del os.environ['HIVE_MCP_CONFIG_PATH']
        
        try:
            # Create service with temp directory
            service = CredentialService(project_root=tmp_path)
            
            # Create MCP file with complex configuration
            mcp_file = tmp_path / ".mcp.json"
            mcp_config = {
                "mcpServers": {
                    "postgres": {
                        "command": "npx",
                        "args": [
                            "-y",
                            "@modelcontextprotocol/server-postgres",
                            "postgresql+psycopg://old-user:old-pass@localhost:5532/hive"
                        ]
                    },
                    "automagik-hive": {
                        "command": "uvx",
                        "args": [
                            "automagik-tools@0.8.17",
                            "tool",
                            "automagik-hive"
                        ],
                        "env": {
                            "HIVE_API_BASE_URL": "http://localhost:38886",
                            "HIVE_API_KEY": "old-key",
                            "HIVE_TIMEOUT": "300"
                        }
                    },
                    "filesystem": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"],
                        "env": {}
                    },
                    "custom-server": {
                        "command": "python",
                        "args": ["-m", "custom.server"],
                        "env": {
                            "CUSTOM_CONFIG": "preserve-this",
                            "ANOTHER_SETTING": "keep-this-too"
                        }
                    }
                }
            }
            mcp_file.write_text(json.dumps(mcp_config, indent=2))
            
            # Generate credentials and sync MCP
            result = service.setup_complete_credentials(sync_mcp=True)
            
            # Parse content after sync
            final_content = json.loads(mcp_file.read_text())
            
            # Non-credential servers should be preserved
            assert "filesystem" in final_content["mcpServers"]
            assert "custom-server" in final_content["mcpServers"]
            
            # Custom environment variables should be preserved
            custom_server = final_content["mcpServers"]["custom-server"]
            assert custom_server["env"]["CUSTOM_CONFIG"] == "preserve-this"
            assert custom_server["env"]["ANOTHER_SETTING"] == "keep-this-too"
            
            # Postgres credentials should be updated in args array
            postgres_server = final_content["mcpServers"]["postgres"]
            connection_string = postgres_server["args"][-1]  # Last arg is the connection string
            assert result['postgres_user'] in connection_string
            assert result['postgres_password'] in connection_string
            assert "old-user:old-pass" not in connection_string
            
            # API key should be updated in automagik-hive server
            hive_server = final_content["mcpServers"]["automagik-hive"]
            assert hive_server["env"]["HIVE_API_KEY"] == result['api_key']
        
        finally:
            # Restore original environment
            if original_env is None:
                os.environ.pop('HIVE_MCP_CONFIG_PATH', None)
            else:
                os.environ['HIVE_MCP_CONFIG_PATH'] = original_env