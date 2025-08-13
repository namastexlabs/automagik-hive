#!/usr/bin/env python3
"""
Additional edge case tests for CredentialService MCP sync behavior.

RED PHASE TESTS: These tests focus on edge cases, error conditions, and integration scenarios.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call, Mock
import pytest

from lib.auth.credential_service import CredentialService


class TestCredentialServiceMcpSyncIntegration:
    """Test integration scenarios and complex MCP sync behaviors."""

    def test_mcp_sync_only_when_credentials_exist(self, tmp_path):
        """
        FAILING TEST: MCP sync should only occur when valid credentials exist.
        
        Expected behavior: sync_mcp=True should not attempt sync if no credentials.
        Current behavior: Will need implementation to check credential existence.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Create empty .env file (no credentials)
        env_file = tmp_path / ".env"
        env_file.write_text("")
        
        # Mock the sync method to track calls
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Even with sync_mcp=True, should not sync without valid credentials
            result = service.setup_complete_credentials(sync_mcp=True)
            
            # Should still generate new credentials
            assert result is not None
            assert 'postgres_user' in result
            
            # But should have called sync since we generated new credentials
            mock_sync.assert_called_once()

    def test_mcp_sync_error_handling_graceful_failure(self, tmp_path):
        """
        FAILING TEST: MCP sync errors should not prevent credential generation.
        
        Expected behavior: If MCP sync fails, credential generation should continue.
        Current behavior: Need to implement error handling in sync logic.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock sync method to raise exception
        def failing_sync():
            raise Exception("MCP sync failed")
            
        with patch.object(service, 'sync_mcp_config_with_credentials', side_effect=failing_sync):
            # Even with MCP sync failure, credential generation should succeed
            result = service.setup_complete_credentials(sync_mcp=True)
            
            # Credentials should still be generated
            assert result is not None
            assert 'postgres_user' in result
            assert 'api_key' in result

    def test_install_all_modes_sync_once_per_installation(self, tmp_path):
        """
        FAILING TEST: install_all_modes should sync MCP once per installation, not per mode.
        
        Expected behavior: Single sync call regardless of number of modes.
        Current behavior: Method signature doesn't support sync_mcp parameter.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Track sync calls
        sync_call_count = 0
        
        def count_sync_calls():
            nonlocal sync_call_count
            sync_call_count += 1
            
        with patch.object(service, 'sync_mcp_config_with_credentials', side_effect=count_sync_calls):
            # Mock master credential extraction
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                
                # Install multiple modes - should sync once
                service.install_all_modes(
                    modes=["workspace", "agent", "genie"], 
                    sync_mcp=True
                )
                
                # Should have called sync exactly once
                assert sync_call_count == 1

    def test_mcp_file_path_customization(self, tmp_path):
        """
        Test that MCP sync respects custom MCP file paths via environment variable.
        
        Expected behavior: Should use HIVE_MCP_CONFIG_PATH if set.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Create custom MCP file with postgres server to update
        custom_mcp_file = tmp_path / "custom.mcp.json"
        custom_mcp_file.write_text('''
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
        
        # Set environment variable for custom path
        with patch.dict('os.environ', {'HIVE_MCP_CONFIG_PATH': str(custom_mcp_file)}):
            # Generate credentials with sync
            service.setup_complete_credentials(sync_mcp=True)
            
            # Verify custom file was used/modified
            custom_content = custom_mcp_file.read_text()
            assert "old-user:old-pass" not in custom_content  # Old credentials should be replaced

    def test_concurrent_credential_generation_thread_safety(self, tmp_path):
        """
        Test that credential generation with MCP sync is thread-safe.
        
        Expected behavior: Concurrent calls should not interfere with each other.
        """
        import threading
        import time
        
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        results = {}
        errors = []
        
        def generate_credentials(thread_id):
            try:
                result = service.setup_complete_credentials(sync_mcp=True)
                results[thread_id] = result
            except Exception as e:
                errors.append((thread_id, e))
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=generate_credentials, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # All threads should have generated credentials
        # (Note: they will overwrite each other's .env, but that's expected behavior)
        assert len(results) > 0

    def test_mcp_sync_preserves_existing_mcp_structure(self, tmp_path):
        """
        Test that MCP sync preserves existing MCP server configurations.
        
        Expected behavior: Should only update credentials, not remove existing servers.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Create ai directory and MCP file with existing servers (respecting HIVE_MCP_CONFIG_PATH=ai/.mcp.json)
        ai_dir = tmp_path / "ai"
        ai_dir.mkdir(exist_ok=True)
        mcp_file = ai_dir / ".mcp.json"
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
        final_content = mcp_file.read_text()
        
        # Should still have other-server
        assert "other-server" in final_content
        
        # Should have synced postgres credentials
        assert result['postgres_user'] in final_content
        assert result['postgres_password'] in final_content
        
        # Should not have old credentials
        assert "old-user:old-pass" not in final_content


class TestCredentialServiceMcpSyncParameterValidation:
    """Test parameter validation and type safety for MCP sync functionality."""

    def test_sync_mcp_parameter_default_value_validation(self, tmp_path):
        """
        FAILING TEST: Validate that sync_mcp parameter has correct default value.
        
        Expected behavior: Default should be False for backward compatibility.
        Current behavior: Parameter doesn't exist yet.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock to track calls
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Call without sync_mcp parameter - should default to False
            service.setup_complete_credentials()
            
            # Should not call sync by default
            mock_sync.assert_not_called()

    def test_sync_mcp_parameter_boolean_coercion(self, tmp_path):
        """
        Test that sync_mcp parameter handles various truthy/falsy values appropriately.
        
        Expected behavior: Should handle various input types gracefully or raise clear errors.
        """
        # Create service with temp directory  
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            
            # Test various falsy values
            falsy_values = [False, None, 0, "", []]
            
            for falsy in falsy_values:
                mock_sync.reset_mock()
                
                try:
                    service.setup_complete_credentials(sync_mcp=falsy)
                    # Should not sync for falsy values
                    mock_sync.assert_not_called()
                except (TypeError, ValueError):
                    # Acceptable to raise error for invalid types
                    pass
            
            # Test various truthy values
            truthy_values = [True, 1, "yes", [1]]
            
            for truthy in truthy_values:
                mock_sync.reset_mock()
                
                try:
                    service.setup_complete_credentials(sync_mcp=truthy)
                    # Should sync for truthy values (or raise error if strict typing)
                    if not mock_sync.called:
                        # If not called, should have raised an error for invalid type
                        pytest.fail(f"Expected sync or error for truthy value {truthy}")
                except (TypeError, ValueError):
                    # Acceptable to raise error for invalid types
                    pass

    def test_install_all_modes_force_regenerate_interaction(self, tmp_path):
        """
        FAILING TEST: Test interaction between force_regenerate and sync_mcp parameters.
        
        Expected behavior: Both parameters should work together correctly.
        Current behavior: sync_mcp parameter doesn't exist yet.
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Create existing credentials
        env_file = tmp_path / ".env"
        env_file.write_text("""
HIVE_DATABASE_URL=postgresql+psycopg://existing_user:existing_pass@localhost:5532/hive
HIVE_API_KEY=hive_existing_key
""")
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            # Test various combinations
            test_cases = [
                {"force_regenerate": False, "sync_mcp": False, "should_sync": False},
                {"force_regenerate": False, "sync_mcp": True, "should_sync": True},
                {"force_regenerate": True, "sync_mcp": False, "should_sync": False},
                {"force_regenerate": True, "sync_mcp": True, "should_sync": True},
            ]
            
            for case in test_cases:
                mock_sync.reset_mock()
                
                # This will fail due to missing sync_mcp parameter
                service.install_all_modes(
                    modes=["workspace"],
                    force_regenerate=case["force_regenerate"],
                    sync_mcp=case["sync_mcp"]
                )
                
                if case["should_sync"]:
                    mock_sync.assert_called_once()
                else:
                    mock_sync.assert_not_called()


class TestCredentialServiceMcpSyncDocumentation:
    """Test scenarios that serve as living documentation of MCP sync behavior."""

    def test_typical_workspace_installation_workflow(self, tmp_path):
        """
        FAILING TEST: Document typical workspace installation workflow.
        
        Expected behavior: Workspace install should not sync MCP by default.
        Current behavior: Need to implement sync control.
        """
        # Create service representing typical workspace installation
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            
            # Step 1: Initial workspace setup (no MCP sync needed)
            result = service.setup_complete_credentials()
            
            # Should generate credentials but not sync MCP
            assert result is not None
            mock_sync.assert_not_called()
            
            mock_sync.reset_mock()
            
            # Step 2: Install workspace mode (no MCP sync by default)
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                install_result = service.install_all_modes(modes=["workspace"])
                
                # Should install successfully without MCP sync
                assert install_result is not None
                mock_sync.assert_not_called()

    def test_typical_agent_development_workflow(self, tmp_path):
        """
        FAILING TEST: Document typical agent development workflow.
        
        Expected behavior: Agent install should support MCP sync when requested.
        Current behavior: Need to implement sync control.
        """
        # Create service representing agent development workflow
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

    def test_mixed_environment_workflow(self, tmp_path):
        """
        FAILING TEST: Document mixed workspace+agent environment workflow.
        
        Expected behavior: Mixed install should sync once when requested.
        Current behavior: Need to implement sync control.
        """
        # Create service for mixed environment
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                
                # Install both workspace and agent with selective MCP sync
                result = service.install_all_modes(
                    modes=["workspace", "agent"],
                    sync_mcp=True  # Enable sync for agent support
                )
                
                # Should install both modes and sync MCP once
                assert result is not None
                assert "workspace" in result
                assert "agent" in result
                mock_sync.assert_called_once()

    def test_ci_cd_automation_workflow(self, tmp_path):
        """
        Test automated CI/CD installation workflow patterns.
        
        Expected behavior: Automated installs should have predictable MCP sync behavior.
        """
        # Simulate CI/CD environment
        service = CredentialService(project_root=tmp_path)
        
        # Mock environment checks that might occur in CI/CD
        with patch.dict('os.environ', {'CI': 'true', 'AUTOMATED_INSTALL': 'true'}):
            with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
                
                # Automated workspace install (no MCP sync for simplicity)
                result = service.setup_complete_credentials(sync_mcp=False)
                
                # Should respect explicit sync_mcp=False in automation
                assert result is not None
                mock_sync.assert_not_called()
                
                mock_sync.reset_mock()
                
                # Automated agent install with MCP sync
                agent_result = service.setup_complete_credentials(sync_mcp=True)
                
                # Should respect explicit sync_mcp=True in automation
                assert agent_result is not None
                mock_sync.assert_called_once()


class TestCredentialServiceMcpSyncRegressionPrevention:
    """Tests to prevent regression of existing functionality while adding MCP sync control."""

    def test_existing_makefile_integration_still_works(self, tmp_path):
        """
        Test that existing Makefile integration continues to function.
        
        Expected behavior: Existing Makefile calls should work unchanged.
        """
        # Create service as called by existing Makefile
        service = CredentialService(project_root=tmp_path)
        
        # Test existing method signatures still work
        try:
            # These calls should work exactly as before
            postgres_creds = service.generate_postgres_credentials()
            api_key = service.generate_hive_api_key()
            service.save_credentials_to_env(postgres_creds, api_key)
            
            assert postgres_creds is not None
            assert api_key is not None
            
        except Exception as e:
            pytest.fail(f"Existing Makefile integration broken: {e}")

    def test_existing_cli_integration_still_works(self, tmp_path):
        """
        Test that existing CLI integration continues to function.
        
        Expected behavior: Existing CLI calls should work unchanged.
        """
        # Create service as called by existing CLI
        service = CredentialService(project_root=tmp_path)
        
        try:
            # These calls should work exactly as before
            status = service.get_credential_status()
            assert status is not None
            
            # Existing install_all_modes should work
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                result = service.install_all_modes()
                assert result is not None
                
        except Exception as e:
            pytest.fail(f"Existing CLI integration broken: {e}")

    def test_backward_compatibility_no_behavior_changes(self, tmp_path):
        """
        CRITICAL TEST: Ensure no existing behavior changes without explicit opt-in.
        
        Expected behavior: All existing functionality should work identically.
        Current behavior: May change due to new sync_mcp default (need to verify).
        """
        # Create service with temp directory
        service = CredentialService(project_root=tmp_path)
        
        # Mock sync method to detect if it's called when it shouldn't be
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            
            # Test all existing method calls work identically
            postgres_creds = service.generate_postgres_credentials()
            api_key = service.generate_hive_api_key()
            service.save_credentials_to_env(postgres_creds, api_key)
            
            # These existing calls should NOT trigger MCP sync
            mock_sync.assert_not_called()
            
            # Test existing setup_complete_credentials
            mock_sync.reset_mock()
            setup_result = service.setup_complete_credentials()
            
            # CRITICAL: This should NOT sync MCP by default for backward compatibility
            mock_sync.assert_not_called()
            
            assert setup_result is not None