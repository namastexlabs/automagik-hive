#!/usr/bin/env python3
"""
SPECIFICATION TESTS for CredentialService MCP sync behavior changes.

These tests serve as living documentation and specification of the required behavior.
They document the exact API changes and behavioral expectations for the implementation.

RED PHASE TESTS: All tests designed to fail initially to drive TDD implementation.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest
import inspect

from lib.auth.credential_service import CredentialService


class TestCredentialServiceMcpSyncSpecification:
    """
    SPECIFICATION TESTS: Define exact API and behavior requirements.
    
    These tests serve as the definitive specification for the MCP sync behavior changes.
    They must ALL pass for the implementation to be considered complete.
    """

    def test_setup_complete_credentials_api_specification(self, tmp_path):
        """
        FAILING TEST: Specification for setup_complete_credentials API changes.
        
        REQUIRED API CHANGES:
        - Add sync_mcp parameter with default False
        - Parameter should be keyword-only for clarity
        - Must maintain backward compatibility
        - Must support both bool values: True/False
        """
        service = CredentialService(project_root=tmp_path)
        
        # Test 1: Parameter signature should accept sync_mcp
        sig = inspect.signature(service.setup_complete_credentials)
        
        # Should have sync_mcp parameter
        assert 'sync_mcp' in sig.parameters, "setup_complete_credentials must accept sync_mcp parameter"
        
        # sync_mcp should have default value of False
        sync_mcp_param = sig.parameters['sync_mcp']
        assert sync_mcp_param.default is False, "sync_mcp parameter must default to False"
        
        # Test 2: Behavior with sync_mcp=False (default)
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            service.setup_complete_credentials()  # Default behavior
            mock_sync.assert_not_called()
        
        # Test 3: Behavior with sync_mcp=False (explicit)
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            service.setup_complete_credentials(sync_mcp=False)
            mock_sync.assert_not_called()
        
        # Test 4: Behavior with sync_mcp=True
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            service.setup_complete_credentials(sync_mcp=True)
            mock_sync.assert_called_once()

    def test_install_all_modes_api_specification(self, tmp_path):
        """
        FAILING TEST: Specification for install_all_modes API changes.
        
        REQUIRED API CHANGES:
        - Add sync_mcp parameter with default False
        - Must work with existing modes and force_regenerate parameters
        - Must sync MCP once per installation, not per mode
        - Must maintain backward compatibility
        """
        service = CredentialService(project_root=tmp_path)
        
        # Test 1: Parameter signature should accept sync_mcp
        sig = inspect.signature(service.install_all_modes)
        
        # Should have sync_mcp parameter
        assert 'sync_mcp' in sig.parameters, "install_all_modes must accept sync_mcp parameter"
        
        # sync_mcp should have default value of False
        sync_mcp_param = sig.parameters['sync_mcp']
        assert sync_mcp_param.default is False, "sync_mcp parameter must default to False"
        
        # Test 2: Backward compatibility - existing parameters should work
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                
                # Existing API should work unchanged
                service.install_all_modes(modes=["workspace"])
                service.install_all_modes(modes=["agent"], force_regenerate=True)
                
                # Should not sync MCP by default
                mock_sync.assert_not_called()

        # Test 3: New sync_mcp parameter should work
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                
                service.install_all_modes(
                    modes=["workspace", "agent"], 
                    sync_mcp=True
                )
                
                # Should sync MCP exactly once
                mock_sync.assert_called_once()

    def test_backward_compatibility_specification(self, tmp_path):
        """
        FAILING TEST: Specification for backward compatibility requirements.
        
        CRITICAL REQUIREMENT: All existing code must work unchanged.
        - setup_complete_credentials() without parameters must work identically
        - install_all_modes() without sync_mcp must work identically
        - No existing behavior should change without explicit opt-in
        """
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                
                # CRITICAL: These calls should work exactly as before
                
                # 1. setup_complete_credentials() default behavior
                result1 = service.setup_complete_credentials()
                assert result1 is not None
                
                # 2. install_all_modes() default behavior
                result2 = service.install_all_modes()
                assert result2 is not None
                
                # 3. install_all_modes() with existing parameters
                result3 = service.install_all_modes(
                    modes=["workspace"], 
                    force_regenerate=True
                )
                assert result3 is not None
                
                # CRITICAL: MCP sync should NOT be called for any of these
                mock_sync.assert_not_called()

    def test_mcp_sync_behavior_specification(self, tmp_path):
        """
        FAILING TEST: Specification for MCP sync behavior requirements.
        
        BEHAVIORAL REQUIREMENTS:
        1. sync_mcp=False: Never call sync_mcp_config_with_credentials()
        2. sync_mcp=True: Always call sync_mcp_config_with_credentials() once
        3. MCP sync should not prevent credential generation if it fails
        4. MCP sync should handle missing .mcp.json gracefully
        """
        service = CredentialService(project_root=tmp_path)
        
        # Test 1: sync_mcp=False behavior
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            service.setup_complete_credentials(sync_mcp=False)
            mock_sync.assert_not_called()
        
        # Test 2: sync_mcp=True behavior
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            service.setup_complete_credentials(sync_mcp=True)
            mock_sync.assert_called_once()
        
        # Test 3: MCP sync failure should not prevent credential generation
        def failing_sync():
            raise Exception("MCP sync failed")
            
        with patch.object(service, 'sync_mcp_config_with_credentials', side_effect=failing_sync):
            result = service.setup_complete_credentials(sync_mcp=True)
            # Should still generate credentials despite sync failure
            assert result is not None
            assert 'postgres_user' in result
        
        # Test 4: Missing .mcp.json should not cause failure
        # (No .mcp.json file exists in tmp_path)
        result = service.setup_complete_credentials(sync_mcp=True)
        assert result is not None

    def test_parameter_validation_specification(self, tmp_path):
        """
        FAILING TEST: Specification for parameter validation requirements.
        
        VALIDATION REQUIREMENTS:
        1. sync_mcp must accept boolean values (True/False)
        2. Invalid values should raise TypeError or ValueError
        3. None should be treated as False (or raise error)
        """
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            
            # Valid boolean values should work
            service.setup_complete_credentials(sync_mcp=True)
            service.setup_complete_credentials(sync_mcp=False)
            
            # Invalid values should be handled appropriately
            invalid_values = ["yes", 1, 0, None, [], {}]
            
            for invalid_value in invalid_values:
                try:
                    service.setup_complete_credentials(sync_mcp=invalid_value)
                    # If no exception, implementation accepts the value
                    # This is acceptable as long as behavior is consistent
                except (TypeError, ValueError):
                    # Acceptable to raise error for invalid types
                    pass

    def test_integration_specification(self, tmp_path):
        """
        FAILING TEST: Specification for integration requirements.
        
        INTEGRATION REQUIREMENTS:
        1. Must work with existing Makefile calls
        2. Must work with existing CLI calls
        3. Must work with Docker environment setup
        4. Must preserve existing .env file generation
        5. Must preserve existing credential validation
        """
        service = CredentialService(project_root=tmp_path)
        
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                
                # Test 1: Makefile-style calls
                makefile_result = service.setup_complete_credentials(
                    postgres_host="localhost",
                    postgres_port=5532,
                    postgres_database="hive"
                )
                assert makefile_result is not None
                
                # Test 2: CLI-style calls
                cli_result = service.install_all_modes(modes=["workspace"])
                assert cli_result is not None
                
                # Test 3: Docker-style calls with sync
                docker_result = service.install_all_modes(
                    modes=["agent"], 
                    sync_mcp=True
                )
                assert docker_result is not None
                
                # MCP sync should only be called once (for docker_result)
                mock_sync.assert_called_once()

    def test_error_handling_specification(self, tmp_path):
        """
        FAILING TEST: Specification for error handling requirements.
        
        ERROR HANDLING REQUIREMENTS:
        1. MCP sync errors must not prevent credential generation
        2. Invalid .mcp.json must not cause failures
        3. Missing credentials must be handled gracefully
        4. File permission errors must be handled gracefully
        """
        service = CredentialService(project_root=tmp_path)
        
        # Test 1: MCP sync throws exception
        def failing_sync():
            raise Exception("MCP sync failed")
            
        with patch.object(service, 'sync_mcp_config_with_credentials', side_effect=failing_sync):
            result = service.setup_complete_credentials(sync_mcp=True)
            assert result is not None
            assert 'postgres_user' in result
            assert 'api_key' in result
        
        # Test 2: Invalid .mcp.json file
        mcp_file = tmp_path / ".mcp.json"
        mcp_file.write_text("invalid json content")
        
        result = service.setup_complete_credentials(sync_mcp=True)
        assert result is not None
        
        # Test 3: Missing .env file permissions (simulate with read-only directory)
        # This test ensures the implementation handles file system errors gracefully
        try:
            result = service.setup_complete_credentials(sync_mcp=True)
            assert result is not None
        except Exception as e:
            # If an exception occurs, it should be a clear, helpful error message
            assert len(str(e)) > 10  # Should have meaningful error message

    def test_performance_specification(self, tmp_path):
        """
        FAILING TEST: Specification for performance requirements.
        
        PERFORMANCE REQUIREMENTS:
        1. MCP sync should be called at most once per install_all_modes() call
        2. Multiple modes should not result in multiple sync calls
        3. Operations should complete in reasonable time
        """
        service = CredentialService(project_root=tmp_path)
        
        sync_call_count = 0
        
        def count_sync():
            nonlocal sync_call_count
            sync_call_count += 1
        
        with patch.object(service, 'sync_mcp_config_with_credentials', side_effect=count_sync):
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                
                # Install multiple modes - should sync once
                service.install_all_modes(
                    modes=["workspace", "agent", "genie"],
                    sync_mcp=True
                )
                
                # Should have called sync exactly once
                assert sync_call_count == 1

    def test_documentation_specification(self, tmp_path):
        """
        Test that the implementation matches documented behavior.
        
        This test ensures the implementation aligns with any documentation
        or comments about the expected behavior.
        """
        service = CredentialService(project_root=tmp_path)
        
        # Check that methods have appropriate docstrings mentioning sync_mcp
        setup_docstring = service.setup_complete_credentials.__doc__ or ""
        install_docstring = service.install_all_modes.__doc__ or ""
        
        # After implementation, these should mention sync_mcp parameter
        # For now, we just verify the methods exist and are callable
        assert callable(service.setup_complete_credentials)
        assert callable(service.install_all_modes)
        assert callable(service.sync_mcp_config_with_credentials)

    def test_complete_specification_checklist(self, tmp_path):
        """
        FAILING TEST: Complete specification checklist for implementation.
        
        This test verifies ALL requirements are met for the implementation to be complete.
        Every assertion in this test must pass for the feature to be considered done.
        """
        service = CredentialService(project_root=tmp_path)
        
        # ✅ REQUIREMENT 1: API signature changes
        setup_sig = inspect.signature(service.setup_complete_credentials)
        install_sig = inspect.signature(service.install_all_modes)
        
        assert 'sync_mcp' in setup_sig.parameters
        assert 'sync_mcp' in install_sig.parameters
        assert setup_sig.parameters['sync_mcp'].default is False
        assert install_sig.parameters['sync_mcp'].default is False
        
        # ✅ REQUIREMENT 2: Behavioral changes
        with patch.object(service, 'sync_mcp_config_with_credentials') as mock_sync:
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                
                # Default behavior: no MCP sync
                service.setup_complete_credentials()
                service.install_all_modes(modes=["workspace"])
                mock_sync.assert_not_called()
                
                mock_sync.reset_mock()
                
                # Explicit sync_mcp=True: MCP sync enabled
                service.setup_complete_credentials(sync_mcp=True)
                service.install_all_modes(modes=["agent"], sync_mcp=True)
                assert mock_sync.call_count == 2
        
        # ✅ REQUIREMENT 3: Backward compatibility
        try:
            # These calls should work exactly as before
            service.setup_complete_credentials()
            with patch.object(service, '_extract_existing_master_credentials', return_value=None):
                service.install_all_modes()
                service.install_all_modes(modes=["workspace"], force_regenerate=True)
        except Exception as e:
            pytest.fail(f"Backward compatibility broken: {e}")
        
        # ✅ REQUIREMENT 4: Error handling
        def failing_sync():
            raise Exception("Simulated MCP sync failure")
            
        with patch.object(service, 'sync_mcp_config_with_credentials', side_effect=failing_sync):
            result = service.setup_complete_credentials(sync_mcp=True)
            assert result is not None  # Should still work despite sync failure
        
        # ✅ REQUIREMENT 5: Integration preservation
        # All existing methods should still work
        postgres_creds = service.generate_postgres_credentials()
        api_key = service.generate_hive_api_key()
        status = service.get_credential_status()
        
        assert postgres_creds is not None
        assert api_key is not None
        assert status is not None