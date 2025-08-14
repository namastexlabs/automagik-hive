"""
Comprehensive test suite for lib/utils/agno_proxy.py
Testing core proxy system functionality to ensure 50%+ coverage.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Any

# Import the module under test
from lib.utils import agno_proxy


class TestAgnoProxyCore:
    """Core functionality tests for agno_proxy module."""

    def test_get_agno_proxy_singleton_pattern(self):
        """Test that get_agno_proxy implements singleton pattern correctly."""
        # Reset global state for clean test
        agno_proxy.reset_proxy_instances()
        
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_proxy_class:
            mock_instance = Mock()
            mock_proxy_class.return_value = mock_instance
            
            # First call creates instance
            proxy1 = agno_proxy.get_agno_proxy()
            # Second call returns same instance
            proxy2 = agno_proxy.get_agno_proxy()
            
            assert proxy1 is proxy2
            assert proxy1 is mock_instance
            # Constructor called only once due to singleton pattern
            mock_proxy_class.assert_called_once()

    def test_get_agno_team_proxy_singleton_pattern(self):
        """Test that get_agno_team_proxy implements singleton pattern correctly."""
        agno_proxy.reset_proxy_instances()
        
        with patch('lib.utils.proxy_teams.AgnoTeamProxy') as mock_proxy_class:
            mock_instance = Mock()
            mock_proxy_class.return_value = mock_instance
            
            proxy1 = agno_proxy.get_agno_team_proxy()
            proxy2 = agno_proxy.get_agno_team_proxy()
            
            assert proxy1 is proxy2
            assert proxy1 is mock_instance
            mock_proxy_class.assert_called_once()

    def test_get_agno_workflow_proxy_singleton_pattern(self):
        """Test that get_agno_workflow_proxy implements singleton pattern correctly."""
        agno_proxy.reset_proxy_instances()
        
        with patch('lib.utils.proxy_workflows.AgnoWorkflowProxy') as mock_proxy_class:
            mock_instance = Mock()
            mock_proxy_class.return_value = mock_instance
            
            proxy1 = agno_proxy.get_agno_workflow_proxy()
            proxy2 = agno_proxy.get_agno_workflow_proxy()
            
            assert proxy1 is proxy2
            assert proxy1 is mock_instance
            mock_proxy_class.assert_called_once()

    def test_reset_proxy_instances_functionality(self):
        """Test reset_proxy_instances clears all global proxy instances."""
        # Set up mock instances
        agno_proxy._agno_agent_proxy = Mock()
        agno_proxy._agno_team_proxy = Mock()
        agno_proxy._agno_workflow_proxy = Mock()
        
        with patch('lib.utils.agno_proxy.logger') as mock_logger:
            agno_proxy.reset_proxy_instances()
            
            # All instances should be reset to None
            assert agno_proxy._agno_agent_proxy is None
            assert agno_proxy._agno_team_proxy is None
            assert agno_proxy._agno_workflow_proxy is None
            
            mock_logger.info.assert_called_with("All proxy instances reset")

    def test_get_proxy_module_info_basic_structure(self):
        """Test get_proxy_module_info returns expected data structure."""
        info = agno_proxy.get_proxy_module_info()
        
        # Check required top-level keys
        required_keys = ["system", "modules", "features", "supported_storage_types", "proxy_instances"]
        for key in required_keys:
            assert key in info
        
        # Check system identification
        assert info["system"] == "Modular Agno Proxy System"
        
        # Check modules mapping
        assert "agent_proxy" in info["modules"]
        assert "team_proxy" in info["modules"]
        assert "workflow_proxy" in info["modules"]

    def test_get_proxy_module_info_proxy_status_tracking(self):
        """Test get_proxy_module_info tracks proxy instance status correctly."""
        # Start with clean state
        agno_proxy.reset_proxy_instances()
        
        info = agno_proxy.get_proxy_module_info()
        proxy_status = info["proxy_instances"]
        
        # Initially all should be False
        assert proxy_status["agent_proxy_loaded"] is False
        assert proxy_status["team_proxy_loaded"] is False
        assert proxy_status["workflow_proxy_loaded"] is False
        
        # Load one proxy
        with patch('lib.utils.proxy_agents.AgnoAgentProxy'):
            agno_proxy.get_agno_proxy()
        
        info_after = agno_proxy.get_proxy_module_info()
        proxy_status_after = info_after["proxy_instances"]
        
        # Should reflect loaded state
        assert proxy_status_after["agent_proxy_loaded"] is True
        assert proxy_status_after["team_proxy_loaded"] is False
        assert proxy_status_after["workflow_proxy_loaded"] is False

    @pytest.mark.asyncio
    async def test_create_agent_legacy_compatibility(self):
        """Test create_agent legacy wrapper function."""
        test_args = ("agent_config",)
        test_kwargs = {"name": "test_agent"}
        expected_result = Mock()
        
        with patch('lib.utils.version_factory.create_agent', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = expected_result
            
            result = await agno_proxy.create_agent(*test_args, **test_kwargs)
            
            assert result is expected_result
            mock_create.assert_called_once_with(*test_args, **test_kwargs)

    @pytest.mark.asyncio
    async def test_create_team_legacy_compatibility(self):
        """Test create_team legacy wrapper function."""
        test_args = ("team_config",)
        test_kwargs = {"team_name": "test_team"}
        expected_result = Mock()
        
        with patch('lib.utils.version_factory.create_team', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = expected_result
            
            result = await agno_proxy.create_team(*test_args, **test_kwargs)
            
            assert result is expected_result
            mock_create.assert_called_once_with(*test_args, **test_kwargs)

    @pytest.mark.asyncio
    async def test_create_workflow_legacy_compatibility(self):
        """Test create_workflow legacy wrapper function."""
        test_args = ("workflow_config",)
        test_kwargs = {"workflow_name": "test_workflow"}
        expected_result = Mock()
        
        with patch('lib.utils.agno_proxy.get_agno_workflow_proxy') as mock_get_proxy:
            mock_proxy = Mock()
            mock_proxy.create_workflow = AsyncMock(return_value=expected_result)
            mock_get_proxy.return_value = mock_proxy
            
            result = await agno_proxy.create_workflow(*test_args, **test_kwargs)
            
            assert result is expected_result
            mock_proxy.create_workflow.assert_called_once_with(*test_args, **test_kwargs)


class TestProxyLazyLoading:
    """Test lazy loading and import behavior."""

    def test_lazy_import_logging(self):
        """Test that proxy creation is properly logged."""
        agno_proxy.reset_proxy_instances()
        
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_proxy_class:
            with patch('lib.utils.agno_proxy.logger') as mock_logger:
                mock_instance = Mock()
                mock_proxy_class.return_value = mock_instance
                
                agno_proxy.get_agno_proxy()
                
                mock_logger.debug.assert_called_with("Created new AgnoAgentProxy instance")

    def test_independent_proxy_types(self):
        """Test that different proxy types are independent."""
        agno_proxy.reset_proxy_instances()
        
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_agent_class:
            with patch('lib.utils.proxy_teams.AgnoTeamProxy') as mock_team_class:
                mock_agent = Mock()
                mock_team = Mock()
                mock_agent_class.return_value = mock_agent
                mock_team_class.return_value = mock_team
                
                agent_proxy = agno_proxy.get_agno_proxy()
                team_proxy = agno_proxy.get_agno_team_proxy()
                
                # Should be different instances
                assert agent_proxy is not team_proxy
                assert agent_proxy is mock_agent
                assert team_proxy is mock_team


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_proxy_creation_error_propagation(self):
        """Test that proxy creation errors are properly propagated."""
        agno_proxy.reset_proxy_instances()
        
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_proxy_class:
            mock_proxy_class.side_effect = RuntimeError("Proxy initialization failed")
            
            with pytest.raises(RuntimeError, match="Proxy initialization failed"):
                agno_proxy.get_agno_proxy()
            
            # Global state should remain None after failure
            assert agno_proxy._agno_agent_proxy is None

    def test_reset_after_partial_creation(self):
        """Test reset behavior after partial proxy creation."""
        agno_proxy.reset_proxy_instances()
        
        # Successfully create agent proxy
        with patch('lib.utils.proxy_agents.AgnoAgentProxy') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            agent_proxy = agno_proxy.get_agno_proxy()
            assert agno_proxy._agno_agent_proxy is mock_agent
        
        # Reset should clear everything
        agno_proxy.reset_proxy_instances()
        assert agno_proxy._agno_agent_proxy is None
        assert agno_proxy._agno_team_proxy is None
        assert agno_proxy._agno_workflow_proxy is None


class TestProxySystemIntegration:
    """Integration tests for the complete proxy system."""

    def test_supported_storage_types_completeness(self):
        """Test that all expected storage types are supported."""
        info = agno_proxy.get_proxy_module_info()
        storage_types = info["supported_storage_types"]
        
        expected_types = [
            "postgres", "sqlite", "mongodb", "redis", "dynamodb",
            "json", "yaml", "singlestore"
        ]
        
        for storage_type in expected_types:
            assert storage_type in storage_types, f"Missing storage type: {storage_type}"

    def test_module_information_consistency(self):
        """Test that module information is consistent and complete."""
        info = agno_proxy.get_proxy_module_info()
        
        # Check module paths are properly defined
        modules = info["modules"]
        expected_modules = {
            "storage_utils": "lib.utils.agno_storage_utils",
            "agent_proxy": "lib.utils.proxy_agents",
            "team_proxy": "lib.utils.proxy_teams",
            "workflow_proxy": "lib.utils.proxy_workflows",
            "interface": "lib.utils.agno_proxy"
        }
        
        for module_key, expected_path in expected_modules.items():
            assert module_key in modules
            assert modules[module_key] == expected_path

    def test_feature_list_completeness(self):
        """Test that feature list includes all expected capabilities."""
        info = agno_proxy.get_proxy_module_info()
        features = info["features"]
        
        expected_features = [
            "Dynamic parameter discovery via introspection",
            "Shared storage utilities (zero duplication)",
            "Component-specific processing logic",
            "Lazy loading for performance",
            "Backward compatibility preserved"
        ]
        
        for feature in expected_features:
            assert feature in features, f"Missing feature: {feature}"