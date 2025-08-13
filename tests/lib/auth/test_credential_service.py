#!/usr/bin/env python3

"""
Comprehensive tests for lib.auth.credential_service module.

RED PHASE TESTS: These tests are designed to FAIL initially to drive TDD implementation.
This file consolidates all MCP sync behavior tests previously scattered across multiple files.

Key test scenarios:
1. Basic credential service functionality
2. MCP sync behavior and parameter control
3. Integration scenarios and real-world workflows
4. Edge cases and error handling
5. Backward compatibility validation
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call, Mock
import pytest
import json
import threading
import time
import inspect

# Import the module under test
try:
    from lib.auth.credential_service import CredentialService
except ImportError:
    pytest.skip(f"Module lib.auth.credential_service not available", allow_module_level=True)


class TestCredentialService:
    """Test basic credential service functionality."""

    def test_module_imports(self):
        """Test that the module can be imported without errors."""
        from lib.auth.credential_service import CredentialService
        assert CredentialService is not None

    def test_credential_service_instantiation(self, tmp_path):
        """Test that CredentialService can be instantiated."""
        service = CredentialService(project_root=tmp_path)
        assert service is not None
        assert service.project_root == tmp_path

    def test_generate_postgres_credentials(self, tmp_path):
        """Test basic PostgreSQL credential generation."""
        service = CredentialService(project_root=tmp_path)
        credentials = service.generate_postgres_credentials()
        
        assert credentials is not None
        assert 'user' in credentials
        assert 'password' in credentials
        assert 'database' in credentials
        assert len(credentials['user']) > 0
        assert len(credentials['password']) > 0

    def test_generate_hive_api_key(self, tmp_path):
        """Test Hive API key generation."""
        service = CredentialService(project_root=tmp_path)
        api_key = service.generate_hive_api_key()
        
        assert api_key is not None
        assert len(api_key) > 0
        assert api_key.startswith('hive_')


class TestCredentialServiceMcpSync:
    """Test MCP sync behavior changes for CredentialService."""

    def test_setup_complete_credentials_sync_mcp_false_by_default(self, tmp_path):
        """
        FAILING TEST: setup_complete_credentials() should NOT call sync_mcp_config_with_credentials() by default.
        
        Expected behavior: sync_mcp parameter should default to False and NOT trigger MCP sync.
        Current behavior: ALWAYS calls sync_mcp_config_with_credentials() (will fail).
        """
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Call setup_complete_credentials without sync_mcp parameter
            result = service.setup_complete_credentials()
            
            # ASSERTION THAT WILL FAIL: sync_mcp_config_with_credentials should NOT be called
            mock_sync.assert_not_called()
            
            # Verify credentials were still generated
            assert result is not None
            assert 'postgres_user' in result
            assert 'api_key' in result

    def test_setup_complete_credentials_sync_mcp_false_explicit(self, tmp_path):
        """
        FAILING TEST: setup_complete_credentials(sync_mcp=False) should NOT call sync_mcp_config_with_credentials().
        
        Expected behavior: Explicitly passing sync_mcp=False should prevent MCP sync.
        Current behavior: Method signature doesn't support sync_mcp parameter (will fail).
        """
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # This call will fail because sync_mcp parameter doesn't exist yet
            result = service.setup_complete_credentials(sync_mcp=False)
            
            # ASSERTION THAT WILL FAIL: sync_mcp_config_with_credentials should NOT be called
            mock_sync.assert_not_called()
            
            # Verify credentials were still generated
            assert result is not None
            assert 'postgres_user' in result
            assert 'api_key' in result

    def test_setup_complete_credentials_sync_mcp_true(self, tmp_path):
        """
        FAILING TEST: setup_complete_credentials(sync_mcp=True) should call sync_mcp_config_with_credentials().
        
        Expected behavior: Explicitly passing sync_mcp=True should trigger MCP sync.
        Current behavior: Method signature doesn't support sync_mcp parameter (will fail).
        """
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # This call will fail because sync_mcp parameter doesn't exist yet
            result = service.setup_complete_credentials(sync_mcp=True)
            
            # ASSERTION THAT WILL PASS: sync_mcp_config_with_credentials should be called once
            mock_sync.assert_called_once()
            
            # Verify credentials were still generated
            assert result is not None
            assert 'postgres_user' in result
            assert 'api_key' in result

    def test_install_all_modes_sync_mcp_parameter_signature(self, tmp_path):
        """
        FAILING TEST: install_all_modes should accept sync_mcp parameter.
        
        Expected behavior: Method should accept sync_mcp parameter without error.
        Current behavior: Parameter doesn't exist in method signature (will fail).
        """
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials'), \
             patch.object(service, '_extract_existing_master_credentials', return_value=None):
            
            try:
                # Test with sync_mcp=False
                service.install_all_modes(modes=["workspace"], sync_mcp=False)
                # Test with sync_mcp=True
                service.install_all_modes(modes=["agent"], sync_mcp=True)
                
                # If we get here, the parameter was accepted
                assert True, "sync_mcp parameter was accepted"
                
            except TypeError as e:
                # This exception will occur because parameter doesn't exist yet
                pytest.fail(f"install_all_modes doesn't accept sync_mcp parameter: {e}")


class TestCredentialServiceMcpSyncEdgeCases:
    """Test edge cases and error conditions for MCP sync behavior."""

    def test_mcp_sync_with_missing_mcp_file(self, tmp_path):
        """
        Test that MCP sync handles missing .mcp.json file gracefully.
        
        Expected behavior: Should not fail if .mcp.json doesn't exist.
        """
        service = CredentialService(project_root=tmp_path)
        
        # This should not raise an exception even if sync_mcp=True
        result = service.setup_complete_credentials(sync_mcp=True)
        
        # Verify credentials were generated despite missing MCP file
        assert result is not None
        assert 'postgres_user' in result
        assert 'api_key' in result

    def test_mcp_sync_error_handling_graceful_failure(self, tmp_path):
        """
        FAILING TEST: MCP sync errors should not prevent credential generation.
        
        Expected behavior: If MCP sync fails, credential generation should continue.
        Current behavior: Need to implement error handling in sync logic.
        """
        service = CredentialService(project_root=tmp_path)
        
        def failing_sync():
            raise Exception("MCP sync failed")
            
        with patch.object(service, 'sync_mcp_config_with_credentials', side_effect=failing_sync):
            # Even with MCP sync failure, credential generation should succeed
            result = service.setup_complete_credentials(sync_mcp=True)
            
            # Credentials should still be generated
            assert result is not None
            assert 'postgres_user' in result
            assert 'api_key' in result

    def test_mcp_sync_preserves_existing_mcp_structure(self, tmp_path):
        """
        Test that MCP sync preserves existing MCP server configurations.
        
        Expected behavior: Should only update credentials, not remove existing servers.
        """
        service = CredentialService(project_root=tmp_path)
        
        # Create MCP file with existing servers
        mcp_file = tmp_path / ".mcp.json"
        mcp_content = '''
{
  "mcpServers": {
    "postgres": {
      "command": "uv",
      "args": ["tool", "run", "--from", "mcp-server-postgres", "mcp-server-postgres"],
      "env": {
        "POSTGRESQL_CONNECTION_STRING": "postgresql+psycopg://old-user:old-pass@localhost:5532/hive"
      }
    },
    "other-server": {
      "command": "other-command",
      "args": ["arg1", "arg2"]
    }
  }
}
'''
        mcp_file.write_text(mcp_content)
        
        # Generate credentials with MCP sync
        result = service.setup_complete_credentials(sync_mcp=True)
        
        # Read updated MCP content
        updated_content = mcp_file.read_text()
        
        # Should still have other-server
        assert "other-server" in updated_content
        
        # Should have updated postgres credentials
        assert result['postgres_user'] in updated_content
        assert result['postgres_password'] in updated_content
        
        # Should not have old credentials
        assert "old-user:old-pass" not in updated_content


class TestCredentialServiceIntegration:
    """Test integration scenarios and real-world workflows."""

    def test_makefile_workspace_install_no_mcp_sync(self, tmp_path):
        """
        FAILING TEST: Test Makefile-style workspace installation without MCP sync.
        
        This simulates how the Makefile currently calls credential service for workspace setup.
        Expected behavior: Should work without MCP sync by default.
        """
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

    def test_agent_development_workflow(self, tmp_path):
        """
        FAILING TEST: Document typical agent development workflow.
        
        Expected behavior: Agent install should support MCP sync when requested.
        Current behavior: Need to implement sync control.
        """
        service = CredentialService(project_root=tmp_path)
        
        # Create MCP file for agent development
        mcp_file = tmp_path / ".mcp.json"
        mcp_file.write_text('{"mcpServers": {}}')
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            
            # Step 1: Setup agent credentials with MCP sync
            result = service.setup_complete_credentials(sync_mcp=True)
            
            # Should sync MCP for agent development
            assert result is not None
            mock_sync.assert_called_once()
            
            mock_sync.reset_mock()
            
            # Step 2: Install agent mode with MCP sync
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                install_result = service.install_all_modes(
                    modes=["agent"], 
                    sync_mcp=True
                )
                
                # Should sync MCP for agent installation
                assert install_result is not None
                mock_sync.assert_called_once()

    def test_backward_compatibility_existing_behavior(self, tmp_path):
        """
        FAILING TEST: Ensure backward compatibility - existing code should work but not sync MCP.
        
        Expected behavior: Existing calls without sync_mcp should work but not sync MCP.
        Current behavior: Always syncs MCP (will fail assertion).
        """
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Call existing method without new parameter (backward compatibility)
            result = service.setup_complete_credentials()
            
            # ASSERTION THAT WILL FAIL: Should NOT sync MCP by default for backward compatibility
            mock_sync.assert_not_called()
            
            # Verify normal functionality still works
            assert result is not None
            assert 'postgres_user' in result
            assert 'api_key' in result


class TestCredentialServiceSpecification:
    """
    SPECIFICATION TESTS: Define exact API and behavior requirements.
    
    These tests serve as the definitive specification for the MCP sync behavior changes.
    They must ALL pass for the implementation to be considered complete.
    """

    def test_setup_complete_credentials_api_specification(self, tmp_path):
        """
        FAILING TEST: Specification for setup_complete_credentials API changes.
        
        Required API signature:
        setup_complete_credentials(sync_mcp: bool = False, **kwargs) -> Dict[str, str]
        
        Expected behavior:
        - sync_mcp=False (default): Does NOT call sync_mcp_config_with_credentials()
        - sync_mcp=True: Calls sync_mcp_config_with_credentials() once
        - Returns same credential structure as before
        - Backward compatible with existing calls
        """
        service = CredentialService(project_root=tmp_path)
        
        # Test API signature compatibility
        sig = inspect.signature(service.setup_complete_credentials)
        
        # Should have sync_mcp parameter with default False
        assert 'sync_mcp' in sig.parameters
        assert sig.parameters['sync_mcp'].default is False
        assert sig.parameters['sync_mcp'].annotation == bool or sig.parameters['sync_mcp'].annotation == inspect.Parameter.empty

    def test_install_all_modes_api_specification(self, tmp_path):
        """
        FAILING TEST: Specification for install_all_modes API changes.
        
        Required API signature:
        install_all_modes(modes: List[str] = None, sync_mcp: bool = False, **kwargs) -> Dict[str, Any]
        
        Expected behavior:
        - sync_mcp=False (default): Does NOT call sync_mcp_config_with_credentials()
        - sync_mcp=True: Calls sync_mcp_config_with_credentials() once regardless of mode count
        - Backward compatible with existing calls
        """
        service = CredentialService(project_root=tmp_path)
        
        # Test API signature compatibility
        sig = inspect.signature(service.install_all_modes)
        
        # Should have sync_mcp parameter with default False
        assert 'sync_mcp' in sig.parameters
        assert sig.parameters['sync_mcp'].default is False
        assert sig.parameters['sync_mcp'].annotation == bool or sig.parameters['sync_mcp'].annotation == inspect.Parameter.empty

    def test_sync_mcp_config_with_credentials_method_exists(self, tmp_path):
        """
        Test that sync_mcp_config_with_credentials method exists and is callable.
        
        This method should handle the actual MCP configuration synchronization.
        """
        service = CredentialService(project_root=tmp_path)
        
        # Method should exist and be callable
        assert hasattr(service, 'sync_mcp_config_with_credentials')
        assert callable(service.sync_mcp_config_with_credentials)
        
        # Should accept optional mcp_file parameter
        sig = inspect.signature(service.sync_mcp_config_with_credentials)
        # Can be called with no parameters or with optional mcp_file parameter
        assert len(sig.parameters) <= 1