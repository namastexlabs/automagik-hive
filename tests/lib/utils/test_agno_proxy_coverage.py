"""
Comprehensive test suite for lib/utils/agno_proxy.py
Testing proxy system functionality, singleton patterns, and lazy loading.
Target: 50%+ coverage with failing tests that guide TDD implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call, AsyncMock
from typing import Any

# Import the module under test
from lib.utils import agno_proxy


class TestAgnoProxySingletonPattern:
    """Test singleton pattern implementation for proxy instances."""

    def test_get_agno_proxy_creates_instance_once(self):
        """Test get_agno_proxy creates single instance and reuses it."""
        # Reset global state
        agno_proxy._agno_agent_proxy = None
        
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_proxy_class:
            mock_instance = Mock()
            mock_proxy_class.return_value = mock_instance
            
            # First call should create instance
            proxy1 = agno_proxy.get_agno_proxy()
            
            # Second call should return same instance
            proxy2 = agno_proxy.get_agno_proxy()
            
            # Should be the same instance
            assert proxy1 is proxy2
            assert proxy1 is mock_instance
            
            # Constructor should be called only once
            mock_proxy_class.assert_called_once()

    def test_get_agno_proxy_lazy_import(self):
        """Test get_agno_proxy uses lazy import to avoid circular dependencies."""
        # Reset global state
        agno_proxy._agno_agent_proxy = None
        
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_proxy_class:
            with patch('lib.utils.agno_proxy.logger') as mock_logger:
                mock_instance = Mock()
                mock_proxy_class.return_value = mock_instance
                
                proxy = agno_proxy.get_agno_proxy()
                
                # Should log creation
                mock_logger.debug.assert_called_with("Created new AgnoAgentProxy instance")
                assert proxy is mock_instance

    def test_get_agno_team_proxy_creates_instance_once(self):
        """Test get_agno_team_proxy creates single instance and reuses it."""
        # Reset global state
        agno_proxy._agno_team_proxy = None
        
        with patch('lib.utils.proxy_teams.AgnoTeamProxy') as mock_proxy_class:
            mock_instance = Mock()
            mock_proxy_class.return_value = mock_instance
            
            # First call should create instance
            proxy1 = agno_proxy.get_agno_team_proxy()
            
            # Second call should return same instance
            proxy2 = agno_proxy.get_agno_team_proxy()
            
            # Should be the same instance
            assert proxy1 is proxy2
            assert proxy1 is mock_instance
            
            # Constructor should be called only once
            mock_proxy_class.assert_called_once()

    def test_get_agno_team_proxy_lazy_import(self):
        """Test get_agno_team_proxy uses lazy import."""
        # Reset global state
        agno_proxy._agno_team_proxy = None
        
        with patch('lib.utils.proxy_teams.AgnoTeamProxy') as mock_proxy_class:
            with patch('lib.utils.agno_proxy.logger') as mock_logger:
                mock_instance = Mock()
                mock_proxy_class.return_value = mock_instance
                
                proxy = agno_proxy.get_agno_team_proxy()
                
                # Should log creation
                mock_logger.debug.assert_called_with("Created new AgnoTeamProxy instance")
                assert proxy is mock_instance

    def test_get_agno_workflow_proxy_creates_instance_once(self):
        """Test get_agno_workflow_proxy creates single instance and reuses it."""
        # Reset global state
        agno_proxy._agno_workflow_proxy = None
        
        with patch('lib.utils.proxy_workflows.AgnoWorkflowProxy') as mock_proxy_class:
            mock_instance = Mock()
            mock_proxy_class.return_value = mock_instance
            
            # First call should create instance
            proxy1 = agno_proxy.get_agno_workflow_proxy()
            
            # Second call should return same instance
            proxy2 = agno_proxy.get_agno_workflow_proxy()
            
            # Should be the same instance
            assert proxy1 is proxy2
            assert proxy1 is mock_instance
            
            # Constructor should be called only once
            mock_proxy_class.assert_called_once()

    def test_get_agno_workflow_proxy_lazy_import(self):
        """Test get_agno_workflow_proxy uses lazy import."""
        # Reset global state
        agno_proxy._agno_workflow_proxy = None
        
        with patch('lib.utils.proxy_workflows.AgnoWorkflowProxy') as mock_proxy_class:
            with patch('lib.utils.agno_proxy.logger') as mock_logger:
                mock_instance = Mock()
                mock_proxy_class.return_value = mock_instance
                
                proxy = agno_proxy.get_agno_workflow_proxy()
                
                # Should log creation
                mock_logger.debug.assert_called_with("Created new AgnoWorkflowProxy instance")
                assert proxy is mock_instance


class TestResetProxyInstances:
    """Test proxy instance reset functionality."""

    def test_reset_proxy_instances_clears_all_globals(self):
        """Test reset_proxy_instances clears all global proxy instances."""
        # Set some mock instances
        agno_proxy._agno_agent_proxy = Mock()
        agno_proxy._agno_team_proxy = Mock() 
        agno_proxy._agno_workflow_proxy = Mock()
        
        with patch('lib.utils.agno_proxy.logger') as mock_logger:
            agno_proxy.reset_proxy_instances()
            
            # All instances should be None
            assert agno_proxy._agno_agent_proxy is None
            assert agno_proxy._agno_team_proxy is None
            assert agno_proxy._agno_workflow_proxy is None
            
            # Should log the reset
            mock_logger.info.assert_called_with("All proxy instances reset")

    def test_reset_forces_new_instance_creation(self):
        """Test reset forces creation of new instances on next call."""
        # Create initial instances
        agno_proxy._agno_agent_proxy = Mock()
        old_instance = agno_proxy._agno_agent_proxy
        
        # Reset
        agno_proxy.reset_proxy_instances()
        
        # Next call should create new instance
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_proxy_class:
            new_mock = Mock()
            mock_proxy_class.return_value = new_mock
            
            new_proxy = agno_proxy.get_agno_proxy()
            
            # Should be different from old instance
            assert new_proxy is not old_instance
            assert new_proxy is new_mock
            mock_proxy_class.assert_called_once()


class TestGetProxyModuleInfo:
    """Test proxy module information functionality."""

    def test_get_proxy_module_info_returns_system_info(self):
        """Test get_proxy_module_info returns correct system information."""
        info = agno_proxy.get_proxy_module_info()
        
        assert info["system"] == "Modular Agno Proxy System"
        assert "modules" in info
        assert "features" in info
        assert "supported_storage_types" in info
        
        # Check module information
        modules = info["modules"]
        assert modules["storage_utils"] == "lib.utils.agno_storage_utils"
        assert modules["agent_proxy"] == "lib.utils.proxy_agents"
        assert modules["team_proxy"] == "lib.utils.proxy_teams"
        assert modules["workflow_proxy"] == "lib.utils.proxy_workflows"
        assert modules["interface"] == "lib.utils.agno_proxy"

    def test_get_proxy_module_info_includes_features(self):
        """Test get_proxy_module_info includes expected features."""
        info = agno_proxy.get_proxy_module_info()
        
        features = info["features"]
        assert "Dynamic parameter discovery via introspection" in features
        assert "Shared storage utilities (zero duplication)" in features
        assert "Component-specific processing logic" in features
        assert "Lazy loading for performance" in features
        assert "Backward compatibility preserved" in features

    def test_get_proxy_module_info_includes_storage_types(self):
        """Test get_proxy_module_info includes supported storage types."""
        info = agno_proxy.get_proxy_module_info()
        
        storage_types = info["supported_storage_types"]
        expected_types = [
            "postgres", "sqlite", "mongodb", "redis", "dynamodb",
            "json", "yaml", "singlestore"
        ]
        
        for storage_type in expected_types:
            assert storage_type in storage_types

    def test_get_proxy_module_info_includes_instance_status(self):
        """Test get_proxy_module_info includes proxy instance status."""
        # Reset all instances
        agno_proxy.reset_proxy_instances()
        
        info = agno_proxy.get_proxy_module_info()
        proxy_instances = info["proxy_instances"]
        
        # All should be False initially
        assert proxy_instances["agent_proxy_loaded"] is False
        assert proxy_instances["team_proxy_loaded"] is False
        assert proxy_instances["workflow_proxy_loaded"] is False

    def test_get_proxy_module_info_reflects_loaded_instances(self):
        """Test get_proxy_module_info reflects which instances are loaded."""
        # Reset and load some instances
        agno_proxy.reset_proxy_instances()
        
        with patch('lib.utils.proxy_agents.AgnoAgentProxy'):
            agno_proxy.get_agno_proxy()  # Load agent proxy
        
        with patch('lib.utils.proxy_workflows.AgnoWorkflowProxy'):
            agno_proxy.get_agno_workflow_proxy()  # Load workflow proxy
        
        info = agno_proxy.get_proxy_module_info()
        proxy_instances = info["proxy_instances"]
        
        # Should reflect loaded state
        assert proxy_instances["agent_proxy_loaded"] is True
        assert proxy_instances["team_proxy_loaded"] is False  # Not loaded
        assert proxy_instances["workflow_proxy_loaded"] is True


class TestLegacyCompatibilityWrappers:
    """Test legacy compatibility wrapper functions."""

    @pytest.mark.asyncio
    async def test_create_agent_legacy_wrapper(self):
        """Test create_agent legacy compatibility wrapper."""
        mock_args = ("arg1", "arg2")
        mock_kwargs = {"key1": "value1", "key2": "value2"}
        expected_result = Mock()
        
        with patch('lib.utils.version_factory.create_agent', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = expected_result
            
            result = await agno_proxy.create_agent(*mock_args, **mock_kwargs)
            
            assert result is expected_result
            mock_create.assert_called_once_with(*mock_args, **mock_kwargs)

    @pytest.mark.asyncio
    async def test_create_team_legacy_wrapper(self):
        """Test create_team legacy compatibility wrapper."""
        mock_args = ("team_arg1", "team_arg2")
        mock_kwargs = {"team_key": "team_value"}
        expected_result = Mock()
        
        with patch('lib.utils.version_factory.create_team', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = expected_result
            
            result = await agno_proxy.create_team(*mock_args, **mock_kwargs)
            
            assert result is expected_result
            mock_create.assert_called_once_with(*mock_args, **mock_kwargs)

    @pytest.mark.asyncio
    async def test_create_workflow_legacy_wrapper(self):
        """Test create_workflow legacy compatibility wrapper."""
        mock_args = ("workflow_arg1",)
        mock_kwargs = {"workflow_key": "workflow_value"}
        expected_result = Mock()
        
        with patch('lib.utils.agno_proxy.get_agno_workflow_proxy') as mock_get_proxy:
            mock_proxy = Mock()
            mock_proxy.create_workflow = AsyncMock(return_value=expected_result)
            mock_get_proxy.return_value = mock_proxy
            
            result = await agno_proxy.create_workflow(*mock_args, **mock_kwargs)
            
            assert result is expected_result
            mock_proxy.create_workflow.assert_called_once_with(*mock_args, **mock_kwargs)


class TestProxyInstanceIsolation:
    """Test proxy instance isolation and independence."""

    def test_proxy_instances_are_independent(self):
        """Test that different proxy types maintain independent instances."""
        # Reset all instances
        agno_proxy.reset_proxy_instances()
        
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_agent_class:
            with patch('lib.utils.proxy_teams.AgnoTeamProxy') as mock_team_class:
                with patch('lib.utils.proxy_workflows.AgnoWorkflowProxy') as mock_workflow_class:
                    
                    mock_agent = Mock()
                    mock_team = Mock()
                    mock_workflow = Mock()
                    
                    mock_agent_class.return_value = mock_agent
                    mock_team_class.return_value = mock_team
                    mock_workflow_class.return_value = mock_workflow
                    
                    # Create different proxy types
                    agent_proxy = agno_proxy.get_agno_proxy()
                    team_proxy = agno_proxy.get_agno_team_proxy()
                    workflow_proxy = agno_proxy.get_agno_workflow_proxy()
                    
                    # Should be different instances
                    assert agent_proxy is not team_proxy
                    assert agent_proxy is not workflow_proxy
                    assert team_proxy is not workflow_proxy
                    
                    # Should be correct types
                    assert agent_proxy is mock_agent
                    assert team_proxy is mock_team
                    assert workflow_proxy is mock_workflow

    def test_partial_reset_behavior(self):
        """Test behavior when only some proxies are loaded before reset."""
        # Reset and create partial state
        agno_proxy.reset_proxy_instances()
        
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            
            # Only create agent proxy
            agent_proxy1 = agno_proxy.get_agno_proxy()
            
            # Reset all
            agno_proxy.reset_proxy_instances()
            
            # Create again with a fresh mock
            new_mock = Mock()
            mock_agent_class.return_value = new_mock
            
            agent_proxy2 = agno_proxy.get_agno_proxy()
            
            # Should be different instances
            assert agent_proxy1 is not agent_proxy2
            assert agent_proxy2 is new_mock
            # Both should be Mock objects but different instances
            assert mock_agent_class.call_count == 2


class TestProxyImportPatterns:
    """Test import patterns and module loading behavior."""

    def test_lazy_imports_avoid_circular_dependencies(self):
        """Test lazy imports prevent circular dependency issues."""
        # Reset state
        agno_proxy.reset_proxy_instances()
        
        # Mock the import to track when it happens
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_proxy_class:
            mock_instance = Mock()
            mock_proxy_class.return_value = mock_instance
            
            # Import should not happen until first call
            # (We can't directly test this without complex import mocking,
            # but we can verify the import only happens when needed)
            
            proxy = agno_proxy.get_agno_proxy()
            
            # Should have been imported and instantiated
            mock_proxy_class.assert_called_once()
            assert proxy is mock_instance

    def test_multiple_module_imports_are_independent(self):
        """Test that different proxy modules are imported independently."""
        # Reset state
        agno_proxy.reset_proxy_instances()
        
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_agent_class:
            with patch('lib.utils.proxy_teams.AgnoTeamProxy') as mock_team_class:
                mock_agent = Mock()
                mock_team = Mock()
                mock_agent_class.return_value = mock_agent
                mock_team_class.return_value = mock_team
                
                # Import only agent proxy
                agent_proxy = agno_proxy.get_agno_proxy()
                
                # Only agent proxy should be imported
                mock_agent_class.assert_called_once()
                mock_team_class.assert_not_called()
                
                # Now import team proxy
                team_proxy = agno_proxy.get_agno_team_proxy()
                
                # Now team proxy should also be imported
                mock_team_class.assert_called_once()
                
                assert agent_proxy is mock_agent
                assert team_proxy is mock_team


class TestErrorHandlingAndEdgeCases:
    """Test error conditions and edge cases."""

    def test_proxy_creation_failure_propagates_error(self):
        """Test that proxy creation failures are properly propagated."""
        # Reset state
        agno_proxy.reset_proxy_instances()
        
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_proxy_class:
            # Make proxy creation fail
            mock_proxy_class.side_effect = RuntimeError("Proxy creation failed")
            
            with pytest.raises(RuntimeError, match="Proxy creation failed"):
                agno_proxy.get_agno_proxy()
            
            # Global state should remain None after failure
            assert agno_proxy._agno_agent_proxy is None

    def test_global_state_consistency_after_errors(self):
        """Test global state remains consistent after proxy creation errors."""
        # Reset state
        agno_proxy.reset_proxy_instances()
        
        # Create one successful proxy
        with patch('lib.utils.proxy_teams.AgnoTeamProxy') as mock_team_class:
            mock_team = Mock()
            mock_team_class.return_value = mock_team
            
            team_proxy = agno_proxy.get_agno_team_proxy()
            assert agno_proxy._agno_team_proxy is mock_team
        
        # Try to create failing proxy
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_agent_class:
            mock_agent_class.side_effect = ValueError("Agent creation failed")
            
            with pytest.raises(ValueError):
                agno_proxy.get_agno_proxy()
        
        # Team proxy should still be available, agent proxy should be None
        assert agno_proxy._agno_team_proxy is mock_team
        assert agno_proxy._agno_agent_proxy is None
        
        # Getting team proxy should still work
        team_proxy2 = agno_proxy.get_agno_team_proxy()
        assert team_proxy2 is mock_team

    def test_reset_during_proxy_usage(self):
        """Test reset behavior during active proxy usage."""
        # Reset and create proxy
        agno_proxy.reset_proxy_instances()
        
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_proxy_class:
            mock_instance = Mock()
            mock_proxy_class.return_value = mock_instance
            
            # Create proxy
            proxy1 = agno_proxy.get_agno_proxy()
            assert proxy1 is mock_instance
            
            # Reset while proxy is "in use"
            agno_proxy.reset_proxy_instances()
            
            # Create a new mock for the second call
            new_mock_instance = Mock()
            mock_proxy_class.return_value = new_mock_instance
            
            # proxy1 should still work (it's a reference to the mock)
            # but getting a new proxy should create a new instance
            proxy2 = agno_proxy.get_agno_proxy()
            
            # Should be different instances
            assert proxy2 is not proxy1
            assert proxy2 is new_mock_instance
            # Should have called constructor twice
            assert mock_proxy_class.call_count == 2


@pytest.mark.integration
class TestAgnoProxyIntegration:
    """Integration tests for agno_proxy module."""

    def test_full_proxy_lifecycle(self):
        """Test complete proxy lifecycle from creation to reset."""
        # Start with clean state
        agno_proxy.reset_proxy_instances()
        
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_agent_class:
            with patch('lib.utils.proxy_teams.AgnoTeamProxy') as mock_team_class:
                with patch('lib.utils.proxy_workflows.AgnoWorkflowProxy') as mock_workflow_class:
                    with patch('lib.utils.agno_proxy.logger') as mock_logger:
                        
                        mock_agent = Mock()
                        mock_team = Mock()
                        mock_workflow = Mock()
                        
                        mock_agent_class.return_value = mock_agent
                        mock_team_class.return_value = mock_team
                        mock_workflow_class.return_value = mock_workflow
                        
                        # Test initial state
                        info = agno_proxy.get_proxy_module_info()
                        assert all(not loaded for loaded in info["proxy_instances"].values())
                        
                        # Create all proxies
                        agent_proxy = agno_proxy.get_agno_proxy()
                        team_proxy = agno_proxy.get_agno_team_proxy()
                        workflow_proxy = agno_proxy.get_agno_workflow_proxy()
                        
                        # Verify creation
                        assert agent_proxy is mock_agent
                        assert team_proxy is mock_team
                        assert workflow_proxy is mock_workflow
                        
                        # Check logging
                        expected_calls = [
                            call("Created new AgnoAgentProxy instance"),
                            call("Created new AgnoTeamProxy instance"),
                            call("Created new AgnoWorkflowProxy instance")
                        ]
                        mock_logger.debug.assert_has_calls(expected_calls, any_order=True)
                        
                        # Test singleton behavior
                        agent_proxy2 = agno_proxy.get_agno_proxy()
                        assert agent_proxy2 is agent_proxy
                        
                        # Test info after creation
                        info = agno_proxy.get_proxy_module_info()
                        assert all(loaded for loaded in info["proxy_instances"].values())
                        
                        # Test reset
                        agno_proxy.reset_proxy_instances()
                        mock_logger.info.assert_called_with("All proxy instances reset")
                        
                        # Test info after reset
                        info = agno_proxy.get_proxy_module_info()
                        assert all(not loaded for loaded in info["proxy_instances"].values())

    @pytest.mark.asyncio
    async def test_legacy_compatibility_integration(self):
        """Test integration of legacy compatibility functions."""
        with patch('lib.utils.version_factory.create_agent', new_callable=AsyncMock) as mock_create_agent:
            with patch('lib.utils.version_factory.create_team', new_callable=AsyncMock) as mock_create_team:
                with patch('lib.utils.agno_proxy.get_agno_workflow_proxy') as mock_get_workflow_proxy:
                    
                    # Setup mocks
                    mock_agent_result = Mock()
                    mock_team_result = Mock()
                    mock_workflow_result = Mock()
                    
                    mock_create_agent.return_value = mock_agent_result
                    mock_create_team.return_value = mock_team_result
                    
                    mock_workflow_proxy = Mock()
                    mock_workflow_proxy.create_workflow = AsyncMock(return_value=mock_workflow_result)
                    mock_get_workflow_proxy.return_value = mock_workflow_proxy
                    
                    # Test all legacy functions
                    agent_result = await agno_proxy.create_agent("agent_arg", key="agent_value")
                    team_result = await agno_proxy.create_team("team_arg", key="team_value")
                    workflow_result = await agno_proxy.create_workflow("workflow_arg", key="workflow_value")
                    
                    # Verify results
                    assert agent_result is mock_agent_result
                    assert team_result is mock_team_result
                    assert workflow_result is mock_workflow_result
                    
                    # Verify calls
                    mock_create_agent.assert_called_once_with("agent_arg", key="agent_value")
                    mock_create_team.assert_called_once_with("team_arg", key="team_value")
                    mock_workflow_proxy.create_workflow.assert_called_once_with("workflow_arg", key="workflow_value")