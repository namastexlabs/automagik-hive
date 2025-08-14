"""
Comprehensive test coverage boost for lib/utils/proxy_teams.py
Target: Increase coverage from 0% to 50%+ by testing untested functionality.

This test file focuses on the specific areas that need coverage:
1. MCP servers handling (_handle_mcp_servers)
2. Native tools configuration (_handle_tools_config) 
3. Model configuration edge cases and fallbacks
4. Error handling paths in team creation
5. Parameter filtering and validation
6. Storage configuration edge cases
7. Memory configuration error handling
8. Team lifecycle and coordination patterns
"""

import inspect
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

import pytest
from agno.agent import Agent
from agno.team import Team

from lib.utils.proxy_teams import AgnoTeamProxy


class TestAgnoTeamProxyMCPServersHandling:
    """Test MCP servers configuration handling - currently 0% coverage."""
    
    @pytest.fixture
    def proxy(self):
        """Create proxy instance for testing."""
        return AgnoTeamProxy()
    
    def test_handle_mcp_servers_with_valid_config(self, proxy):
        """Test MCP servers handling with valid configuration."""
        mcp_servers_config = ["automagik-forge", "search-repo-docs", "postgres"]
        
        with patch("lib.utils.proxy_teams.logger") as mock_logger:
            result = proxy._handle_mcp_servers(
                mcp_servers_config, {}, "test-team", None
            )
            
            assert result == mcp_servers_config
            mock_logger.info.assert_called_once()
            assert "automagik-forge" in mock_logger.info.call_args[0][0]
            assert "search-repo-docs" in mock_logger.info.call_args[0][0]
            assert "postgres" in mock_logger.info.call_args[0][0]
    
    def test_handle_mcp_servers_with_empty_config(self, proxy):
        """Test MCP servers handling with empty configuration."""
        result = proxy._handle_mcp_servers([], {}, "test-team", None)
        
        assert result == []
    
    def test_handle_mcp_servers_with_none_config(self, proxy):
        """Test MCP servers handling with None configuration."""
        result = proxy._handle_mcp_servers(None, {}, "test-team", None)
        
        assert result == []
    
    def test_handle_mcp_servers_logging_format(self, proxy):
        """Test proper logging format for MCP servers."""
        mcp_servers_config = ["server1", "server2", "server3"]
        
        with patch("lib.utils.proxy_teams.logger") as mock_logger:
            proxy._handle_mcp_servers(mcp_servers_config, {}, "my-team", "db_url")
            
            # Verify logging includes component_id and server list
            log_call = mock_logger.info.call_args[0][0]
            assert "my-team" in log_call
            assert "server1, server2, server3" in log_call
            assert "🌐" in log_call  # Should include emoji


class TestAgnoTeamProxyNativeToolsHandling:
    """Test native Agno tools configuration - currently 0% coverage."""
    
    @pytest.fixture
    def proxy(self):
        """Create proxy instance for testing."""
        return AgnoTeamProxy()
    
    def test_handle_tools_config_empty(self, proxy):
        """Test tools handling with empty configuration."""
        result = proxy._handle_tools_config([], {}, "test-team", None)
        
        assert result == []
    
    def test_handle_tools_config_none(self, proxy):
        """Test tools handling with None configuration.""" 
        result = proxy._handle_tools_config(None, {}, "test-team", None)
        
        assert result == []
    
    def test_handle_tools_config_shell_tools_success(self, proxy):
        """Test successful loading of ShellTools."""
        tools_config = [{"name": "ShellTools"}]
        mock_shell_tool = MagicMock()
        
        with (
            patch("lib.tools.registry.ToolRegistry._load_native_agno_tool") as mock_load,
            patch("lib.utils.proxy_teams.logger") as mock_logger,
        ):
            mock_load.return_value = mock_shell_tool
            
            result = proxy._handle_tools_config(tools_config, {}, "test-team", None)
            
            assert len(result) == 1
            assert result[0] == mock_shell_tool
            mock_load.assert_called_once_with("ShellTools")
            mock_logger.info.assert_called_once()
            assert "ShellTools" in mock_logger.info.call_args[0][0]
    
    def test_handle_tools_config_shell_tools_failure(self, proxy):
        """Test ShellTools loading failure."""
        tools_config = [{"name": "ShellTools"}]
        
        with (
            patch("lib.tools.registry.ToolRegistry._load_native_agno_tool") as mock_load,
            patch("lib.utils.proxy_teams.logger") as mock_logger,
        ):
            mock_load.return_value = None  # Tool loading failed
            
            result = proxy._handle_tools_config(tools_config, {}, "test-team", None)
            
            assert result == []
            mock_logger.warning.assert_called_once()
            assert "Failed to load native Agno tool: ShellTools" in mock_logger.warning.call_args[0][0]
    
    def test_handle_tools_config_unknown_tool_type(self, proxy):
        """Test handling of unknown tool types."""
        tools_config = [{"name": "UnknownTool"}]
        
        with patch("lib.utils.proxy_teams.logger") as mock_logger:
            result = proxy._handle_tools_config(tools_config, {}, "test-team", None)
            
            assert result == []
            mock_logger.warning.assert_called_once()
            assert "Unknown native tool type: UnknownTool" in mock_logger.warning.call_args[0][0]
    
    def test_handle_tools_config_mixed_tool_types(self, proxy):
        """Test handling of mixed tool configurations."""
        mock_shell_tool = MagicMock()
        custom_tool = MagicMock()
        string_tool = "string_tool_config"
        
        tools_config = [
            {"name": "ShellTools"},  # Should load via registry
            custom_tool,  # Should pass through as-is
            string_tool,  # Should pass through as-is
            {"name": "UnknownTool"},  # Should log warning
        ]
        
        with (
            patch("lib.tools.registry.ToolRegistry._load_native_agno_tool") as mock_load,
            patch("lib.utils.proxy_teams.logger") as mock_logger,
        ):
            mock_load.return_value = mock_shell_tool
            
            result = proxy._handle_tools_config(tools_config, {}, "test-team", None)
            
            # Should have 3 tools (ShellTools, custom_tool, string_tool)
            assert len(result) == 3
            assert result[0] == mock_shell_tool
            assert result[1] == custom_tool
            assert result[2] == string_tool
            
            # Should log info for loaded tools and warning for unknown
            assert mock_logger.info.call_count == 1
            assert mock_logger.warning.call_count == 1
    
    def test_handle_tools_config_non_dict_tools(self, proxy):
        """Test handling of non-dictionary tool configurations."""
        custom_function = lambda x: x  # Custom tool function
        tool_instance = MagicMock()
        
        tools_config = [custom_function, tool_instance, "string_config"]
        
        with patch("lib.utils.proxy_teams.logger") as mock_logger:
            result = proxy._handle_tools_config(tools_config, {}, "test-team", None)
            
            assert len(result) == 3
            assert result[0] == custom_function
            assert result[1] == tool_instance
            assert result[2] == "string_config"
            
            # Should log info about loaded tools
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "test-team" in log_message
            assert "3" in log_message or "custom" in log_message


class TestAgnoTeamProxyModelConfigurationEdgeCases:
    """Test model configuration edge cases and fallback scenarios."""
    
    @pytest.fixture
    def proxy(self):
        """Create proxy instance for testing."""
        return AgnoTeamProxy()
    
    def test_handle_model_config_no_model_id(self, proxy):
        """Test model configuration without model ID."""
        model_config = {"temperature": 0.7, "max_tokens": 1000}
        
        with patch("lib.config.models.resolve_model") as mock_resolve:
            mock_model = MagicMock()
            mock_resolve.return_value = mock_model
            
            result = proxy._handle_model_config(model_config, {}, "test-team", None)
            
            assert result == mock_model
            mock_resolve.assert_called_once_with(model_id=None, **model_config)
    
    def test_handle_model_config_provider_detection_failure(self, proxy):
        """Test model configuration when provider detection fails."""
        model_config = {"id": "unknown-provider-model"}
        
        with (
            patch("lib.config.provider_registry.get_provider_registry") as mock_registry,
            patch("lib.config.models.resolve_model") as mock_resolve,
        ):
            mock_provider_registry = MagicMock()
            mock_registry.return_value = mock_provider_registry
            mock_provider_registry.detect_provider.return_value = None  # No provider found
            
            mock_model = MagicMock()
            mock_resolve.return_value = mock_model
            
            result = proxy._handle_model_config(model_config, {}, "test-team", None)
            
            assert result == mock_model
            mock_resolve.assert_called_once_with(model_id="unknown-provider-model", **model_config)
    
    def test_handle_model_config_model_class_resolution_failure(self, proxy):
        """Test model configuration when model class resolution fails."""
        model_config = {"id": "claude-3-sonnet"}
        
        with (
            patch("lib.config.provider_registry.get_provider_registry") as mock_registry,
            patch("lib.config.models.resolve_model") as mock_resolve,
        ):
            mock_provider_registry = MagicMock()
            mock_registry.return_value = mock_provider_registry
            mock_provider_registry.detect_provider.return_value = "anthropic"
            mock_provider_registry.resolve_model_class.return_value = None  # Resolution failed
            
            mock_model = MagicMock()
            mock_resolve.return_value = mock_model
            
            result = proxy._handle_model_config(model_config, {}, "test-team", None)
            
            assert result == mock_model
            mock_resolve.assert_called_once_with(model_id="claude-3-sonnet", **model_config)
    
    def test_handle_model_config_temperature_default_injection(self, proxy):
        """Test automatic temperature default injection for teams."""
        model_config = {"id": "claude-3-sonnet"}
        
        with (
            patch("lib.config.provider_registry.get_provider_registry") as mock_registry,
            patch("lib.utils.dynamic_model_resolver.filter_model_parameters") as mock_filter,
            patch("inspect.signature") as mock_signature,
        ):
            # Setup provider registry mocks
            mock_provider_registry = MagicMock()
            mock_registry.return_value = mock_provider_registry
            mock_provider_registry.detect_provider.return_value = "anthropic"
            
            mock_model_class = MagicMock()
            mock_provider_registry.resolve_model_class.return_value = mock_model_class
            
            # Mock filter to return config without temperature
            mock_filter.return_value = {"id": "claude-3-sonnet"}
            
            # Mock inspect.signature to show temperature parameter is supported
            mock_param = MagicMock()
            mock_sig = MagicMock()
            mock_sig.parameters = {"temperature": mock_param}
            mock_signature.return_value = mock_sig
            
            result = proxy._handle_model_config(model_config, {}, "test-team", None)
            
            # Should inject default temperature for teams
            assert result["temperature"] == 1.0
            assert result["id"] == "claude-3-sonnet"


class TestAgnoTeamProxyParameterFiltering:
    """Test parameter filtering functionality - currently partially covered."""
    
    @pytest.fixture
    def proxy(self):
        """Create proxy instance for testing.""" 
        return AgnoTeamProxy()
    
    @pytest.mark.asyncio
    async def test_create_team_parameter_filtering(self, proxy):
        """Test that unsupported parameters are filtered out."""
        # Mock a restrictive set of supported parameters
        proxy._supported_params = {"name", "mode", "members"}
        
        config = {"name": "Test Team", "mode": "route"}
        
        with (
            patch.object(proxy, "_process_config", new_callable=AsyncMock) as mock_process,
            patch("lib.utils.proxy_teams.Team") as mock_team_class,
            patch.object(proxy, "_create_metadata") as mock_metadata,
        ):
            # Return config with both supported and unsupported parameters
            mock_process.return_value = {
                "name": "Test Team",  # supported
                "mode": "route",  # supported
                "members": [],  # supported
                "unsupported_param": "value",  # unsupported - should be filtered
                "another_unsupported": "value2",  # unsupported - should be filtered
            }
            mock_metadata.return_value = {"version": 1}
            mock_team = MagicMock()
            mock_team_class.return_value = mock_team
            
            await proxy.create_team("test-team", config)
            
            # Verify only supported parameters were passed to Team constructor
            call_kwargs = mock_team_class.call_args[1]
            assert "name" in call_kwargs
            assert "mode" in call_kwargs
            assert "members" in call_kwargs
            assert "unsupported_param" not in call_kwargs
            assert "another_unsupported" not in call_kwargs
    
    @pytest.mark.asyncio
    async def test_create_team_none_value_filtering(self, proxy):
        """Test that None values are filtered out."""
        proxy._supported_params = {"name", "mode", "description", "instructions"}
        
        config = {"name": "Test Team"}
        
        with (
            patch.object(proxy, "_process_config", new_callable=AsyncMock) as mock_process,
            patch("lib.utils.proxy_teams.Team") as mock_team_class,
            patch.object(proxy, "_create_metadata") as mock_metadata,
        ):
            # Return config with None values
            mock_process.return_value = {
                "name": "Test Team",  # valid value
                "mode": "route",  # valid value  
                "description": None,  # None - should be filtered
                "instructions": None,  # None - should be filtered
            }
            mock_metadata.return_value = {"version": 1}
            mock_team = MagicMock()
            mock_team_class.return_value = mock_team
            
            await proxy.create_team("test-team", config)
            
            # Verify None values were filtered out
            call_kwargs = mock_team_class.call_args[1]
            assert "name" in call_kwargs
            assert "mode" in call_kwargs
            assert "description" not in call_kwargs
            assert "instructions" not in call_kwargs


class TestAgnoTeamProxyErrorHandling:
    """Test error handling paths - currently low coverage."""
    
    @pytest.fixture
    def proxy(self):
        """Create proxy instance for testing."""
        return AgnoTeamProxy()
    
    @pytest.mark.asyncio
    async def test_process_config_storage_handler_exception(self, proxy):
        """Test exception handling in storage configuration."""
        config = {"storage": {"type": "invalid"}}
        
        with patch("lib.utils.proxy_teams.create_dynamic_storage") as mock_create:
            mock_create.side_effect = ValueError("Invalid storage type")
            
            with pytest.raises(ValueError, match="Invalid storage type"):
                await proxy._process_config(config, "test-team", None)
    
    @pytest.mark.asyncio
    async def test_process_config_model_handler_exception(self, proxy):
        """Test exception handling in model configuration."""
        config = {"model": {"id": "invalid-model"}}
        
        with (
            patch("lib.config.provider_registry.get_provider_registry") as mock_registry,
            patch("lib.config.models.resolve_model") as mock_resolve,
        ):
            mock_provider_registry = MagicMock()
            mock_registry.return_value = mock_provider_registry
            mock_provider_registry.detect_provider.return_value = None
            mock_resolve.side_effect = ImportError("Model not found")
            
            with pytest.raises(ImportError, match="Model not found"):
                await proxy._process_config(config, "test-team", None)
    
    @pytest.mark.asyncio
    async def test_process_config_memory_handler_exception(self, proxy):
        """Test exception handling in memory configuration."""
        config = {"memory": {"enable_user_memories": True}}
        
        with patch("lib.memory.memory_factory.create_team_memory") as mock_create:
            mock_create.side_effect = RuntimeError("Memory service unavailable")
            
            with pytest.raises(RuntimeError, match="Memory service unavailable"):
                await proxy._process_config(config, "test-team", "db_url")


class TestAgnoTeamProxyParameterDiscoveryEdgeCases:
    """Test parameter discovery edge cases and fallback behavior."""
    
    def test_parameter_discovery_signature_exception(self):
        """Test parameter discovery when inspect.signature fails."""
        with patch("lib.utils.proxy_teams.inspect.signature") as mock_signature:
            mock_signature.side_effect = AttributeError("No signature available")
            
            with patch("lib.utils.proxy_teams.logger") as mock_logger:
                proxy = AgnoTeamProxy()
                
                # Should use fallback parameters
                assert len(proxy._supported_params) > 50  # Should have substantial fallback coverage
                mock_logger.error.assert_called_once()
                assert "Failed to introspect Agno Team parameters" in str(mock_logger.error.call_args)
    
    def test_parameter_discovery_generic_exception(self):
        """Test parameter discovery with generic exception."""
        with patch("lib.utils.proxy_teams.inspect.signature") as mock_signature:
            mock_signature.side_effect = Exception("Generic error")
            
            with patch("lib.utils.proxy_teams.logger") as mock_logger:
                proxy = AgnoTeamProxy()
                
                # Should still initialize with fallback parameters
                assert isinstance(proxy._supported_params, set)
                assert len(proxy._supported_params) > 0
                mock_logger.error.assert_called_once()
    
    def test_fallback_parameters_contain_core_functionality(self):
        """Test that fallback parameters cover all core Team functionality."""
        proxy = AgnoTeamProxy()
        fallback_params = proxy._get_fallback_parameters()
        
        # Core team functionality categories
        core_categories = {
            # Team basics
            "members", "mode", "model", "name", "team_id", "user_id",
            # Session management
            "session_id", "session_name", "session_state",
            # Instructions and context
            "description", "instructions", "context", "additional_context",
            # Knowledge and memory
            "knowledge", "memory", "enable_agentic_memory", "enable_user_memories",
            # Tools and integrations
            "tools", "mcp_servers", "show_tool_calls",
            # Storage and persistence
            "storage", "extra_data",
            # Streaming and events
            "stream", "stream_intermediate_steps", "store_events",
            # Debug and monitoring
            "debug_mode", "monitoring", "telemetry",
        }
        
        missing_core = core_categories - fallback_params
        assert len(missing_core) == 0, f"Missing core parameters in fallback: {missing_core}"
        
        # Should have comprehensive coverage
        assert len(fallback_params) >= 60, "Fallback parameters should be comprehensive"


class TestAgnoTeamProxyMetadataHandling:
    """Test metadata creation and handling - partially covered."""
    
    @pytest.fixture
    def proxy(self):
        """Create proxy instance for testing."""
        return AgnoTeamProxy()
    
    def test_create_metadata_with_all_custom_parameters(self, proxy):
        """Test metadata creation with all supported custom parameters."""
        config = {
            "team": {"version": 5, "name": "Advanced Team"},
            "suggested_actions": ["analyze", "implement", "test", "deploy"],
            "escalation_triggers": {
                "error_count": 3,
                "timeout_seconds": 300,
                "memory_threshold": 0.9
            },
            "streaming_config": {
                "enabled": True,
                "chunk_size": 1024,
                "buffer_size": 4096
            },
            "events_config": {
                "log_level": "INFO",
                "handlers": ["console", "file"],
                "format": "json"
            },
            "context_config": {
                "max_history": 100,
                "include_metadata": True,
                "compression": "gzip"
            },
            "display_config": {
                "theme": "dark",
                "font_size": 14,
                "line_numbers": True
            }
        }
        
        metadata = proxy._create_metadata(config, "advanced-team")
        
        # Verify core metadata
        assert metadata["version"] == 5
        assert metadata["loaded_from"] == "proxy_teams"
        assert metadata["team_id"] == "advanced-team"
        assert metadata["agno_parameters_count"] == len(proxy._supported_params)
        
        # Verify all custom parameters are preserved
        custom_params = metadata["custom_parameters"]
        assert custom_params["suggested_actions"] == ["analyze", "implement", "test", "deploy"]
        assert custom_params["escalation_triggers"]["error_count"] == 3
        assert custom_params["streaming_config"]["enabled"] is True
        assert custom_params["events_config"]["log_level"] == "INFO"
        assert custom_params["context_config"]["max_history"] == 100
        assert custom_params["display_config"]["theme"] == "dark"
    
    def test_create_metadata_empty_custom_parameters(self, proxy):
        """Test metadata creation with empty custom parameters."""
        config = {"team": {"version": 1}}
        
        metadata = proxy._create_metadata(config, "minimal-team")
        
        custom_params = metadata["custom_parameters"]
        # All custom parameters should have empty defaults
        assert custom_params["suggested_actions"] == {}
        assert custom_params["escalation_triggers"] == {}
        assert custom_params["streaming_config"] == {}
        assert custom_params["events_config"] == {}
        assert custom_params["context_config"] == {}
        assert custom_params["display_config"] == {}


class TestAgnoTeamProxyConfigurationValidation:
    """Test configuration validation functionality - partially covered."""
    
    @pytest.fixture
    def proxy(self):
        """Create proxy instance for testing."""
        return AgnoTeamProxy()
    
    def test_validate_config_comprehensive_coverage(self, proxy):
        """Test validation with comprehensive configuration coverage."""
        # Mock specific supported and custom parameters for predictable testing
        proxy._supported_params = {
            "name", "mode", "description", "instructions", "members",
            "session_id", "user_id", "model", "storage", "memory"
        }
        proxy._custom_params = {
            "model", "storage", "memory", "team", "members", 
            "suggested_actions", "escalation_triggers"
        }
        
        config = {
            # Supported Agno parameters
            "name": "Validation Team",
            "mode": "coordinate",
            "description": "Team for validation testing",
            "instructions": "Validate all configurations",
            "session_id": "session-123",
            "user_id": "user-456",
            # Custom parameters (also supported)
            "model": {"id": "claude-3-sonnet"},
            "storage": {"type": "postgres"},
            "memory": {"enable_user_memories": True},
            # Custom parameters (handled by handlers)
            "team": {"version": 2},
            "suggested_actions": ["validate", "verify"],
            "escalation_triggers": {"timeout": 300},
            # Unknown parameters
            "unknown_param1": "value1",
            "unknown_param2": "value2",
            "mystery_setting": {"nested": "value"}
        }
        
        result = proxy.validate_config(config)
        
        # Should correctly categorize parameters
        expected_supported = {
            "name", "mode", "description", "instructions", 
            "session_id", "user_id", "model", "storage", "memory"
        }
        expected_custom = {"team", "suggested_actions", "escalation_triggers"}
        expected_unknown = {"unknown_param1", "unknown_param2", "mystery_setting"}
        
        assert set(result["supported_agno_params"]) == expected_supported
        assert set(result["custom_params"]) == expected_custom
        assert set(result["unknown_params"]) == expected_unknown
        assert result["total_agno_params_available"] == 10
        assert result["coverage_percentage"] == 90.0  # 9 out of 10 supported params used
    
    def test_validate_config_edge_case_empty_handlers(self, proxy):
        """Test validation when custom handlers return empty results."""
        # Mock scenario where handlers exist but return nothing useful
        proxy._supported_params = {"name", "mode"}
        proxy._custom_params = {"empty_handler1", "empty_handler2"}
        
        config = {
            "name": "Edge Case Team",
            "empty_handler1": {"config": "value"},
            "empty_handler2": None,
            "truly_unknown": "mystery"
        }
        
        result = proxy.validate_config(config)
        
        assert result["supported_agno_params"] == ["name"]
        assert set(result["custom_params"]) == {"empty_handler1", "empty_handler2"}
        assert result["unknown_params"] == ["truly_unknown"]
        assert result["coverage_percentage"] == 50.0


class TestAgnoTeamProxyIntegrationScenarios:
    """Test complex integration scenarios - low coverage areas."""
    
    @pytest.fixture
    def proxy(self):
        """Create proxy instance for testing."""
        return AgnoTeamProxy()
    
    @pytest.mark.asyncio
    async def test_complex_configuration_processing_workflow(self, proxy):
        """Test complex configuration with all handlers involved."""
        complex_config = {
            "team": {"name": "Complex Team", "mode": "hybrid", "version": 3},
            "model": {"id": "claude-3-opus", "temperature": 0.6},
            "members": ["agent-alpha", "agent-beta"],
            "storage": {"type": "postgres", "pool_size": 10},
            "memory": {"enable_user_memories": True},
            "mcp_servers": ["automagik-forge", "postgres"],
            "tools": [
                {"name": "ShellTools"},
                {"name": "UnknownTool"},  # Should log warning
                "custom_tool_object"
            ],
            "suggested_actions": ["coordinate", "execute"],
            "escalation_triggers": {"max_retries": 5}
        }
        
        # Mock all external dependencies
        mock_agents = [MagicMock(), MagicMock()]
        mock_storage = MagicMock()
        mock_memory = MagicMock()
        mock_shell_tool = MagicMock()
        
        with (
            patch("ai.agents.registry.get_agent", new_callable=AsyncMock) as mock_get_agent,
            patch("lib.config.provider_registry.get_provider_registry") as mock_registry,
            patch("lib.utils.dynamic_model_resolver.filter_model_parameters") as mock_filter,
            patch("lib.utils.proxy_teams.create_dynamic_storage") as mock_create_storage,
            patch("lib.memory.memory_factory.create_team_memory") as mock_create_memory,
            patch("lib.tools.registry.ToolRegistry._load_native_agno_tool") as mock_load_tool,
            patch("lib.utils.proxy_teams.logger") as mock_logger,
        ):
            # Setup all mocks
            mock_get_agent.side_effect = mock_agents
            
            mock_provider_registry = MagicMock()
            mock_registry.return_value = mock_provider_registry
            mock_provider_registry.detect_provider.return_value = "anthropic"
            mock_provider_registry.resolve_model_class.return_value = MagicMock()
            mock_filter.return_value = {"id": "claude-3-opus", "temperature": 0.6}
            
            mock_create_storage.return_value = mock_storage
            mock_create_memory.return_value = mock_memory
            mock_load_tool.return_value = mock_shell_tool
            
            result = await proxy._process_config(
                complex_config, "complex-team", "postgresql://localhost/db"
            )
            
            # Verify all handlers were called and results integrated
            assert "name" in result  # team handler
            assert "id" in result  # model handler
            assert "members" in result  # members handler
            assert "storage" in result  # storage handler  
            assert "memory" in result  # memory handler
            assert "mcp_servers" in result  # mcp_servers handler
            assert "tools" in result  # tools handler
            
            # Verify specific handler results
            assert result["name"] == "Complex Team"
            assert result["members"] == mock_agents
            assert result["storage"] == mock_storage
            assert result["memory"] == mock_memory
            assert result["mcp_servers"] == ["automagik-forge", "postgres"]
            assert len(result["tools"]) == 2  # ShellTools + custom_tool_object (UnknownTool filtered)
            
            # Verify appropriate logging occurred
            assert mock_logger.info.call_count >= 2  # MCP servers + tools
            assert mock_logger.warning.call_count >= 1  # Unknown tool
    
    @pytest.mark.asyncio
    async def test_team_creation_with_metrics_integration(self, proxy):
        """Test complete team creation with metrics integration."""
        config = {
            "team": {"name": "Metrics Team", "metrics_enabled": True},
            "model": {"id": "claude-3-sonnet"},
            "members": ["metrics-agent"],
            "metrics_enabled": False  # Should be overridden by team.metrics_enabled
        }
        
        mock_metrics_service = MagicMock()
        mock_metrics_service.collect_from_response = MagicMock(return_value=True)
        mock_agent = MagicMock()
        mock_team = MagicMock()
        
        with (
            patch.object(proxy, "_process_config", new_callable=AsyncMock) as mock_process,
            patch("lib.utils.proxy_teams.Team") as mock_team_class,
            patch.object(proxy, "_create_metadata") as mock_metadata,
            patch.object(proxy, "_wrap_team_with_metrics") as mock_wrap,
        ):
            mock_process.return_value = {
                "name": "Metrics Team", 
                "members": [mock_agent],
                "id": "claude-3-sonnet"
            }
            mock_metadata.return_value = {"version": 1}
            mock_team_class.return_value = mock_team
            mock_wrap.return_value = mock_team
            
            result = await proxy.create_team(
                component_id="metrics-team",
                config=config,
                metrics_service=mock_metrics_service
            )
            
            # Verify metrics service was stored in metadata
            assert mock_team.metadata["metrics_service"] == mock_metrics_service
            
            # Verify team was wrapped with metrics
            mock_wrap.assert_called_once_with(
                mock_team, "metrics-team", config, mock_metrics_service
            )
            
            assert result == mock_team


# Export test classes for pytest discovery
__all__ = [
    "TestAgnoTeamProxyMCPServersHandling",
    "TestAgnoTeamProxyNativeToolsHandling", 
    "TestAgnoTeamProxyModelConfigurationEdgeCases",
    "TestAgnoTeamProxyParameterFiltering",
    "TestAgnoTeamProxyErrorHandling",
    "TestAgnoTeamProxyParameterDiscoveryEdgeCases",
    "TestAgnoTeamProxyMetadataHandling",
    "TestAgnoTeamProxyConfigurationValidation",
    "TestAgnoTeamProxyIntegrationScenarios",
]