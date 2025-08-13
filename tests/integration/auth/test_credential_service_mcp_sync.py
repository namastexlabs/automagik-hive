#!/usr/bin/env python3
"""
Comprehensive tests for CredentialService MCP sync behavior changes.

RED PHASE TESTS: These tests are designed to FAIL initially to drive TDD implementation.

Key test scenarios:
1. Test setup_complete_credentials() with sync_mcp=False (default) - should NOT call sync_mcp_config_with_credentials()
2. Test setup_complete_credentials() with sync_mcp=True - should call sync_mcp_config_with_credentials()
3. Test that workspace installations don't trigger MCP sync
4. Test that agent installations do trigger MCP sync when requested
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

from lib.auth.credential_service import CredentialService


class TestCredentialServiceMcpSync:
    """Test MCP sync behavior changes for CredentialService."""

    def test_setup_complete_credentials_sync_mcp_false_by_default(self, tmp_path):
        """
        FAILING TEST: setup_complete_credentials() should NOT call sync_mcp_config_with_credentials() by default.
        
        Expected behavior: sync_mcp parameter should default to False and NOT trigger MCP sync.
        Current behavior: ALWAYS calls sync_mcp_config_with_credentials() (will fail).
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock the sync_mcp_config_with_credentials method
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Call setup_complete_credentials without sync_mcp parameter
            # This should default to sync_mcp=False and NOT call sync method
            result = service.setup_complete_credentials()
            
            # ASSERTION THAT WILL FAIL: sync_mcp_config_with_credentials should NOT be called
            mock_sync.assert_not_called()
            
            # Verify credentials were still generated
            assert result is not None
            assert 'postgres_user' in result
            assert 'api_key' in result

    @pytest.mark.skip(reason="BLOCKED: Source fix needed - TASK-cd4d8f02-118d-4a62-b8ec-05ae6b220376")
    def test_setup_complete_credentials_sync_mcp_false_explicit(self, tmp_path):
        """
        FAILING TEST: setup_complete_credentials(sync_mcp=False) should NOT call sync_mcp_config_with_credentials().
        
        Expected behavior: Explicitly passing sync_mcp=False should prevent MCP sync.
        Current behavior: Method signature doesn't support sync_mcp parameter (will fail).
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock the sync_mcp_config_with_credentials method
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
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock the sync_mcp_config_with_credentials method
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # This call will fail because sync_mcp parameter doesn't exist yet
            result = service.setup_complete_credentials(sync_mcp=True)
            
            # ASSERTION THAT WILL PASS: sync_mcp_config_with_credentials should be called once
            mock_sync.assert_called_once()
            
            # Verify credentials were still generated
            assert result is not None
            assert 'postgres_user' in result
            assert 'api_key' in result

    def test_workspace_installation_no_mcp_sync_by_default(self, tmp_path):
        """
        FAILING TEST: Workspace installations should not trigger MCP sync by default.
        
        Expected behavior: install_all_modes() for workspace should not sync MCP.
        Current behavior: Will need implementation of sync control (will fail).
        """
        # Create service with temp directory  
        service = CredentialService(project_root=tmp_path)
        
        # Mock the sync_mcp_config_with_credentials method
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Mock master credential extraction to avoid file dependencies
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                # Install workspace mode only
                result = service.install_all_modes(modes=["workspace"])
                
                # ASSERTION THAT WILL FAIL: MCP sync should not be called for workspace installation
                mock_sync.assert_not_called()
                
                # Verify installation succeeded
                assert result is not None
                assert "workspace" in result

    def test_workspace_installation_with_explicit_mcp_sync(self, tmp_path):
        """
        FAILING TEST: Workspace installations should support explicit MCP sync when requested.
        
        Expected behavior: install_all_modes() with sync_mcp=True should sync MCP even for workspace.
        Current behavior: Method signature doesn't support sync_mcp parameter (will fail).
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock the sync_mcp_config_with_credentials method
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Mock master credential extraction to avoid file dependencies
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                # This call will fail because sync_mcp parameter doesn't exist yet
                result = service.install_all_modes(modes=["workspace"], sync_mcp=True)
                
                # ASSERTION: MCP sync should be called when explicitly requested
                mock_sync.assert_called_once()
                
                # Verify installation succeeded
                assert result is not None
                assert "workspace" in result

    def test_agent_installation_triggers_mcp_sync_when_requested(self, tmp_path):
        """
        FAILING TEST: Agent installations should trigger MCP sync when requested.
        
        Expected behavior: install_all_modes() for agent with sync_mcp=True should sync MCP.
        Current behavior: Method signature doesn't support sync_mcp parameter (will fail).
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock the sync_mcp_config_with_credentials method
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Mock master credential extraction to avoid file dependencies
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                # This call will fail because sync_mcp parameter doesn't exist yet
                result = service.install_all_modes(modes=["agent"], sync_mcp=True)
                
                # ASSERTION: MCP sync should be called for agent installation when requested
                mock_sync.assert_called_once()
                
                # Verify installation succeeded
                assert result is not None
                assert "agent" in result

    def test_agent_installation_no_mcp_sync_by_default(self, tmp_path):
        """
        FAILING TEST: Agent installations should not trigger MCP sync by default.
        
        Expected behavior: install_all_modes() for agent should not sync MCP by default.
        Current behavior: Will need implementation of sync control (will fail).
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock the sync_mcp_config_with_credentials method
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Mock master credential extraction to avoid file dependencies
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                # Install agent mode only without explicit sync_mcp
                result = service.install_all_modes(modes=["agent"])
                
                # ASSERTION THAT WILL FAIL: MCP sync should not be called by default
                mock_sync.assert_not_called()
                
                # Verify installation succeeded
                assert result is not None
                assert "agent" in result

    def test_mixed_mode_installation_sync_mcp_behavior(self, tmp_path):
        """
        FAILING TEST: Mixed mode installations should respect sync_mcp parameter.
        
        Expected behavior: install_all_modes() for multiple modes should sync once when requested.
        Current behavior: Method signature doesn't support sync_mcp parameter (will fail).
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock the sync_mcp_config_with_credentials method
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Mock master credential extraction to avoid file dependencies
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                # This call will fail because sync_mcp parameter doesn't exist yet
                result = service.install_all_modes(
                    modes=["workspace", "agent"], 
                    sync_mcp=True
                )
                
                # ASSERTION: MCP sync should be called once regardless of number of modes
                mock_sync.assert_called_once()
                
                # Verify installation succeeded for all modes
                assert result is not None
                assert "workspace" in result
                assert "agent" in result

    def test_install_all_modes_sync_mcp_parameter_signature(self, tmp_path):
        """
        FAILING TEST: install_all_modes should accept sync_mcp parameter.
        
        Expected behavior: Method should accept sync_mcp parameter without error.
        Current behavior: Parameter doesn't exist in method signature (will fail).
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock dependencies to focus on parameter acceptance
        with patch.object(service, 'sync_mcp_config_with_credentials'), \
             patch.object(service, '_extract_existing_master_credentials', return_value=None):
            
            # These calls will fail due to missing sync_mcp parameter
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

    def test_setup_complete_credentials_parameter_signature(self, tmp_path):
        """
        FAILING TEST: setup_complete_credentials should accept sync_mcp parameter.
        
        Expected behavior: Method should accept sync_mcp parameter without error.
        Current behavior: Parameter doesn't exist in method signature (will fail).
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock dependencies to focus on parameter acceptance
        with patch.object(service, 'sync_mcp_config_with_credentials'):
            
            try:
                # Test with sync_mcp=False
                service.setup_complete_credentials(sync_mcp=False)
                # Test with sync_mcp=True  
                service.setup_complete_credentials(sync_mcp=True)
                
                # If we get here, the parameter was accepted
                assert True, "sync_mcp parameter was accepted"
                
            except TypeError as e:
                # This exception will occur because parameter doesn't exist yet
                pytest.fail(f"setup_complete_credentials doesn't accept sync_mcp parameter: {e}")

    def test_mcp_sync_called_with_correct_parameters(self, tmp_path):
        """
        Test that sync_mcp_config_with_credentials is called with correct parameters.
        
        This test assumes the MCP sync functionality works correctly and focuses on
        ensuring it's called properly when requested.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Create a mock MCP file to ensure sync doesn't fail
        mcp_file = tmp_path / ".mcp.json"
        mcp_file.write_text('{"mcpServers": {}}')
        
        # Mock the sync_mcp_config_with_credentials method to capture calls
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # This test will initially fail due to missing sync_mcp parameter
            service.setup_complete_credentials(sync_mcp=True)
            
            # Verify the method was called once with no parameters
            # (since sync_mcp_config_with_credentials takes optional mcp_file parameter)
            mock_sync.assert_called_once_with()

    def test_backward_compatibility_existing_behavior(self, tmp_path):
        """
        FAILING TEST: Ensure backward compatibility - existing code should work but not sync MCP.
        
        Expected behavior: Existing calls without sync_mcp should work but not sync MCP.
        Current behavior: Always syncs MCP (will fail assertion).
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock the sync_mcp_config_with_credentials method
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Call existing method without new parameter (backward compatibility)
            result = service.setup_complete_credentials()
            
            # ASSERTION THAT WILL FAIL: Should NOT sync MCP by default for backward compatibility
            mock_sync.assert_not_called()
            
            # Verify normal functionality still works
            assert result is not None
            assert 'postgres_user' in result
            assert 'api_key' in result

    def test_integration_existing_makefile_behavior(self, tmp_path):
        """
        FAILING TEST: Ensure Makefile integration continues to work with proper MCP sync control.
        
        Expected behavior: Makefile calls should be able to control MCP sync behavior.
        Current behavior: No control mechanism exists (will fail).
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock the sync_mcp_config_with_credentials method
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Mock master credential extraction
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                
                # Simulate Makefile calling install_all_modes for workspace (no MCP sync)
                workspace_result = service.install_all_modes(modes=["workspace"])
                
                # Simulate Makefile calling install_all_modes for agent (with MCP sync)
                # This will fail due to missing sync_mcp parameter
                agent_result = service.install_all_modes(modes=["agent"], sync_mcp=True)
                
                # ASSERTIONS:
                # MCP sync should be called once (only for agent installation)
                mock_sync.assert_called_once()
                
                # Both installations should succeed
                assert workspace_result is not None
                assert agent_result is not None
                assert "workspace" in workspace_result  
                assert "agent" in agent_result


class TestCredentialServiceMcpSyncEdgeCases:
    """Test edge cases and error conditions for MCP sync behavior."""

    def test_mcp_sync_with_missing_mcp_file(self, tmp_path):
        """
        Test that MCP sync handles missing .mcp.json file gracefully.
        
        Expected behavior: Should not fail if .mcp.json doesn't exist.
        """
        # Create service with temp directory (no .mcp.json file)
        service = CredentialService(project_root=tmp_path)
        
        # This should not raise an exception even if sync_mcp=True
        # The implementation should handle missing .mcp.json gracefully
        result = service.setup_complete_credentials(sync_mcp=True)
        
        # Verify credentials were generated despite missing MCP file
        assert result is not None
        assert 'postgres_user' in result
        assert 'api_key' in result

    def test_mcp_sync_with_invalid_credentials(self, tmp_path):
        """
        Test MCP sync behavior when credentials are invalid/missing.
        
        Expected behavior: Should not crash if credentials are invalid.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Create MCP file
        mcp_file = tmp_path / ".mcp.json"
        mcp_file.write_text('{"mcpServers": {}}')
        
        # Mock credential extraction to return invalid credentials
        with patch.object(service, 'extract_postgres_credentials_from_env') as mock_extract_pg, \
             patch.object(service, 'extract_hive_api_key_from_env') as mock_extract_api:
            
            # Return invalid/missing credentials
            mock_extract_pg.return_value = {"user": None, "password": None, "url": None}
            mock_extract_api.return_value = None
            
            # This should not raise an exception
            service.sync_mcp_config_with_credentials()
            
            # Verify the method handled missing credentials gracefully
            assert True  # If we get here, no exception was raised

    def test_multiple_mcp_syncs_idempotent(self, tmp_path):
        """
        Test that multiple MCP syncs are idempotent and don't cause issues.
        
        Expected behavior: Multiple sync calls should not cause problems.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Create ai directory and MCP file (respecting HIVE_MCP_CONFIG_PATH=ai/.mcp.json)
        ai_dir = tmp_path / "ai"
        ai_dir.mkdir(exist_ok=True)
        mcp_file = ai_dir / ".mcp.json" 
        mcp_file.write_text('''
{
  "mcpServers": {
    "postgres": {
      "command": "uv",
      "args": ["tool", "run", "--from", "mcp-server-postgres", "mcp-server-postgres"],
      "env": {
        "POSTGRESQL_CONNECTION_STRING": "postgresql+psycopg://old-user:old-pass@localhost:5532/hive"
      }
    }
  }
}
''')
        
        # Generate credentials
        result = service.setup_complete_credentials(sync_mcp=True)
        
        # Call sync multiple times - should be idempotent
        service.sync_mcp_config_with_credentials()
        service.sync_mcp_config_with_credentials()
        service.sync_mcp_config_with_credentials()
        
        # Verify final state is consistent
        mcp_content = mcp_file.read_text()
        
        # Should contain the new credentials (not old ones)
        assert "old-user:old-pass" not in mcp_content
        assert result['postgres_user'] in mcp_content
        assert result['postgres_password'] in mcp_content
        assert result['api_key'] in mcp_content


class TestCredentialServiceMcpSyncValidation:
    """Test validation and configuration aspects of MCP sync behavior."""

    def test_sync_mcp_parameter_type_validation(self, tmp_path):
        """
        Test that sync_mcp parameter handles different value types correctly.
        
        Expected behavior: Parameter uses Python's truthy/falsy evaluation.
        Boolean values work as expected, other types are evaluated in boolean context.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock dependencies to focus on parameter behavior
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            
            # Valid boolean values should work
            service.setup_complete_credentials(sync_mcp=True)
            assert mock_sync.call_count == 1, "sync_mcp=True should trigger MCP sync"
            
            mock_sync.reset_mock()
            service.setup_complete_credentials(sync_mcp=False)
            assert mock_sync.call_count == 0, "sync_mcp=False should not trigger MCP sync"
            
            # Truthy values should trigger sync (Python boolean context evaluation)
            mock_sync.reset_mock()
            service.setup_complete_credentials(sync_mcp="yes")
            assert mock_sync.call_count == 1, "sync_mcp='yes' (truthy string) should trigger MCP sync"
                
            mock_sync.reset_mock()
            service.setup_complete_credentials(sync_mcp=1)
            assert mock_sync.call_count == 1, "sync_mcp=1 (truthy int) should trigger MCP sync"
            
            # Falsy values should not trigger sync
            mock_sync.reset_mock()
            service.setup_complete_credentials(sync_mcp="")
            assert mock_sync.call_count == 0, "sync_mcp='' (falsy string) should not trigger MCP sync"
            
            mock_sync.reset_mock()
            service.setup_complete_credentials(sync_mcp=0)
            assert mock_sync.call_count == 0, "sync_mcp=0 (falsy int) should not trigger MCP sync"
            
            mock_sync.reset_mock()
            service.setup_complete_credentials(sync_mcp=None)
            assert mock_sync.call_count == 0, "sync_mcp=None (falsy) should not trigger MCP sync"

    def test_install_all_modes_sync_mcp_applies_to_all_modes(self, tmp_path):
        """
        Test that sync_mcp parameter in install_all_modes applies correctly.
        
        Expected behavior: sync_mcp=True should sync MCP once regardless of mode count.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock the sync_mcp_config_with_credentials method to count calls
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Mock master credential extraction
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                
                # Install all modes with sync_mcp=True
                service.install_all_modes(
                    modes=["workspace", "agent", "genie"], 
                    sync_mcp=True
                )
                
                # Should call sync exactly once, not once per mode
                assert mock_sync.call_count == 1
                
                # Reset mock
                mock_sync.reset_mock()
                
                # Install all modes with sync_mcp=False (default)
                service.install_all_modes(modes=["workspace", "agent", "genie"])
                
                # Should not call sync at all
                mock_sync.assert_not_called()

    def test_documented_behavior_matches_implementation(self, tmp_path):
        """
        Test that the implemented behavior matches documented expectations.
        
        This test serves as living documentation of the expected behavior.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Create MCP file for testing
        mcp_file = tmp_path / ".mcp.json"
        mcp_file.write_text('{"mcpServers": {}}')
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            
            # DOCUMENTED BEHAVIOR 1: Default behavior is NO MCP sync
            service.setup_complete_credentials()
            mock_sync.assert_not_called()
            
            mock_sync.reset_mock()
            
            # DOCUMENTED BEHAVIOR 2: Explicit sync_mcp=False prevents MCP sync
            service.setup_complete_credentials(sync_mcp=False)
            mock_sync.assert_not_called()
            
            mock_sync.reset_mock()
            
            # DOCUMENTED BEHAVIOR 3: Explicit sync_mcp=True enables MCP sync
            service.setup_complete_credentials(sync_mcp=True)
            mock_sync.assert_called_once()
            
            mock_sync.reset_mock()
            
            # DOCUMENTED BEHAVIOR 4: install_all_modes respects sync_mcp parameter
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                service.install_all_modes(modes=["workspace"], sync_mcp=True)
                mock_sync.assert_called_once()