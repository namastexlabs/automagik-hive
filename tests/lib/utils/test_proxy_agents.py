"""
Comprehensive tests for lib/utils/proxy_agents.py
Targeting 152 uncovered lines for 2.2% coverage boost.
Focus on AgnoAgentProxy class methods, configuration processing, metrics wrapping, and error handling.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
import yaml

from lib.utils.proxy_agents import AgnoAgentProxy


class TestProxyAgentsImports:
    """Test proxy agents module imports."""

    def test_module_import(self):
        """Test that proxy_agents module can be imported."""
        try:
            import lib.utils.proxy_agents

            assert lib.utils.proxy_agents is not None
        except ImportError as e:
            pytest.fail(f"Failed to import proxy_agents: {e}")

    def test_agno_imports(self):
        """Test Agno framework imports in proxy_agents."""
        # These should be available in proxy_agents module
        from agno.agent import Agent
        from agno.models.anthropic import Claude

        assert Agent is not None
        assert Claude is not None

    def test_utility_imports(self):
        """Test utility imports."""

        assert Path is not None
        assert yaml is not None


class TestProxyAgentConfiguration:
    """Test proxy agent configuration handling."""

    @pytest.fixture
    def sample_agent_config(self):
        """Sample agent configuration for testing."""
        return {
            "agent": {
                "name": "Test Proxy Agent",
                "agent_id": "test-proxy-agent",
                "version": "1.0.0",
                "description": "A test proxy agent",
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4-20250514",
                "temperature": 0.7,
            },
            "instructions": "You are a test proxy agent that helps with testing.",
            "tools": [{"name": "test_tool", "type": "function"}],
        }

    def test_agent_config_structure(self, sample_agent_config):
        """Test agent configuration structure validation."""
        # Test that configuration has required keys
        assert "agent" in sample_agent_config
        assert "model" in sample_agent_config
        assert "instructions" in sample_agent_config

        # Test agent section
        agent_config = sample_agent_config["agent"]
        assert "name" in agent_config
        assert "agent_id" in agent_config
        assert "version" in agent_config

        # Test model section
        model_config = sample_agent_config["model"]
        assert "provider" in model_config
        assert "id" in model_config

    def test_agent_config_validation(self, sample_agent_config):
        """Test agent configuration validation."""
        # Test valid configuration
        assert sample_agent_config["agent"]["name"] is not None
        assert sample_agent_config["agent"]["agent_id"] is not None
        assert sample_agent_config["agent"]["version"] is not None

        # Test model configuration
        assert sample_agent_config["model"]["provider"] in ["anthropic", "openai"]
        assert isinstance(sample_agent_config["model"]["temperature"], int | float)

    def test_tools_configuration(self, sample_agent_config):
        """Test tools configuration in agent config."""
        tools = sample_agent_config.get("tools", [])
        assert isinstance(tools, list)

        if tools:
            for tool in tools:
                assert "name" in tool
                assert "type" in tool


class TestAgnoAgentProxyInitialization:
    """Test AgnoAgentProxy initialization and parameter discovery."""

    @patch("lib.utils.proxy_agents.Agent")
    def test_proxy_initialization(self, mock_agent):
        """Test AgnoAgentProxy initialization with parameter discovery."""
        # Mock Agent constructor signature
        mock_signature = MagicMock()
        mock_params = {
            "self": MagicMock(name="self"),
            "model": MagicMock(name="model"),
            "name": MagicMock(name="name"),
            "instructions": MagicMock(name="instructions"),
            "tools": MagicMock(name="tools"),
        }
        mock_signature.parameters.items.return_value = mock_params.items()

        with patch("inspect.signature", return_value=mock_signature):
            proxy = AgnoAgentProxy()

            assert proxy is not None
            assert hasattr(proxy, "_supported_params")
            assert hasattr(proxy, "_custom_params")
            assert "model" in proxy._supported_params
            assert "name" in proxy._supported_params
            assert "instructions" in proxy._supported_params
            assert "tools" in proxy._supported_params
            assert "self" not in proxy._supported_params

    def test_parameter_discovery_fallback(self):
        """Test parameter discovery fallback when introspection fails."""
        with patch(
            "inspect.signature", side_effect=Exception("Mock inspection failure")
        ):
            proxy = AgnoAgentProxy()

            # Should fallback to hardcoded parameters
            assert len(proxy._supported_params) > 0
            assert "model" in proxy._supported_params
            assert "name" in proxy._supported_params
            assert "instructions" in proxy._supported_params

    def test_custom_parameter_handlers_initialization(self):
        """Test custom parameter handlers are properly initialized."""
        proxy = AgnoAgentProxy()

        expected_handlers = {
            "knowledge_filter",
            "model",
            "storage",
            "memory",
            "agent",
            "suggested_actions",
            "escalation_triggers",
            "streaming_config",
            "events_config",
            "context_config",
            "display_config",
            "display",
        }

        for handler_name in expected_handlers:
            assert handler_name in proxy._custom_params
            assert callable(proxy._custom_params[handler_name])

    def test_get_supported_parameters(self):
        """Test get_supported_parameters method."""
        proxy = AgnoAgentProxy()
        params = proxy.get_supported_parameters()

        assert isinstance(params, set)
        assert len(params) > 0
        # Should return a copy, not the original set
        params.add("test_param")
        assert "test_param" not in proxy._supported_params


class TestAgnoAgentProxyCreateAgent:
    """Test create_agent method and configuration processing."""

    @pytest.fixture
    def proxy(self):
        """Create AgnoAgentProxy instance for testing."""
        with patch("inspect.signature") as mock_sig:
            mock_params = {
                "model": MagicMock(name="model"),
                "name": MagicMock(name="name"),
                "instructions": MagicMock(name="instructions"),
                "agent_id": MagicMock(name="agent_id"),
                "session_id": MagicMock(name="session_id"),
                "debug_mode": MagicMock(name="debug_mode"),
                "user_id": MagicMock(name="user_id"),
            }
            mock_sig.return_value.parameters.items.return_value = mock_params.items()
            return AgnoAgentProxy()

    @pytest.fixture
    def sample_config(self):
        """Sample agent configuration."""
        return {
            "agent": {
                "name": "Test Agent",
                "version": 1,
                "description": "Test agent description",
                "role": "test_role",
            },
            "model": {
                "id": "claude-sonnet-4-20250514",  # Use a valid model ID
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            "instructions": "You are a test agent",
            "tools": [{"name": "test_tool"}],
        }

    @pytest.mark.asyncio
    @patch("lib.utils.proxy_agents.Agent")
    @patch("lib.config.models.resolve_model")
    async def test_create_agent_basic(
        self, mock_resolve_model, mock_agent_class, proxy, sample_config
    ):
        """Test basic agent creation."""
        mock_resolve_model.return_value = "mock_model"
        mock_agent = MagicMock()
        mock_agent.metadata = {}
        mock_agent_class.return_value = mock_agent

        agent = await proxy.create_agent(
            component_id="test-agent",
            config=sample_config,
        )

        assert agent is not None
        assert agent == mock_agent
        mock_agent_class.assert_called_once()

    @pytest.mark.asyncio
    @patch("lib.utils.proxy_agents.Agent")
    @patch("lib.config.models.resolve_model")
    async def test_create_agent_with_session_and_debug(
        self, mock_resolve_model, mock_agent_class, proxy, sample_config
    ):
        """Test agent creation with session_id and debug_mode."""
        mock_resolve_model.return_value = "mock_model"
        mock_agent = MagicMock()
        mock_agent.metadata = {}
        mock_agent_class.return_value = mock_agent

        agent = await proxy.create_agent(
            component_id="test-agent",
            config=sample_config,
            session_id="test-session",
            debug_mode=True,
            user_id="test-user",
        )

        assert agent is not None
        # Verify the correct parameters were passed to Agent constructor
        call_args, call_kwargs = mock_agent_class.call_args
        assert call_kwargs.get("agent_id") == "test-agent"
        assert call_kwargs.get("session_id") == "test-session"
        assert call_kwargs.get("debug_mode") is True
        assert call_kwargs.get("user_id") == "test-user"

    @pytest.mark.asyncio
    async def test_create_agent_none_config_error(self, proxy):
        """Test create_agent with None config raises ValueError."""
        with pytest.raises(ValueError, match="Config is None for agent test-agent"):
            await proxy.create_agent(
                component_id="test-agent",
                config=None,
            )

    @pytest.mark.asyncio
    @patch("lib.utils.proxy_agents.Agent")
    @patch("lib.config.models.resolve_model")
    async def test_create_agent_with_metrics_service(
        self, mock_resolve_model, mock_agent_class, proxy, sample_config
    ):
        """Test agent creation with metrics service."""
        mock_resolve_model.return_value = "mock_model"
        mock_agent = MagicMock()
        mock_agent.metadata = {}
        mock_agent_class.return_value = mock_agent

        mock_metrics = MagicMock()
        mock_metrics.collect_from_response = MagicMock()

        agent = await proxy.create_agent(
            component_id="test-agent",
            config=sample_config,
            metrics_service=mock_metrics,
        )

        assert agent is not None
        assert agent.metadata.get("metrics_service") == mock_metrics

    @pytest.mark.asyncio
    @patch(
        "lib.utils.proxy_agents.Agent",
        side_effect=Exception("Mock agent creation error"),
    )
    @patch("lib.config.models.resolve_model")
    async def test_create_agent_creation_error(
        self, mock_resolve_model, mock_agent_class, proxy, sample_config
    ):
        """Test create_agent error handling."""
        mock_resolve_model.return_value = "mock_model"
        with pytest.raises(Exception, match="Mock agent creation error"):
            await proxy.create_agent(
                component_id="test-agent",
                config=sample_config,
            )


class TestConfigurationProcessing:
    """Test configuration processing methods."""

    @pytest.fixture
    def proxy(self):
        """Create AgnoAgentProxy instance for testing."""
        with patch("inspect.signature") as mock_sig:
            mock_params = {
                "model": MagicMock(name="model"),
                "name": MagicMock(name="name"),
                "instructions": MagicMock(name="instructions"),
                "knowledge": MagicMock(name="knowledge"),
                "storage": MagicMock(name="storage"),
                "memory": MagicMock(name="memory"),
            }
            mock_sig.return_value.parameters.items.return_value = mock_params.items()
            return AgnoAgentProxy()

    def test_process_config_direct_mapping(self, proxy):
        """Test direct parameter mapping in config processing."""
        config = {
            "name": "Test Agent",
            "instructions": "Test instructions",
            "unknown_param": "should be ignored",
        }

        processed = proxy._process_config(config, "test-agent", None)

        assert processed["name"] == "Test Agent"
        assert processed["instructions"] == "Test instructions"
        assert "unknown_param" not in processed

    def test_process_config_with_custom_handlers(self, proxy):
        """Test config processing with custom handlers."""
        config = {
            "model": {"id": "claude-sonnet-4-20250514", "temperature": 0.7},
            "agent": {"name": "Test Agent", "version": 1},
            "storage": {"type": "sqlite"},
        }

        # Test that _process_config handles all config sections
        result = proxy._process_config(config, "test-agent", None)
        
        # Verify that the result contains processed configuration
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # Check that custom handlers were used by verifying result structure
        # The model handler returns a dict that gets merged into top-level
        assert "id" in result  # model id should be in top-level
        assert result["id"] == "claude-sonnet-4-20250514"
        assert "temperature" in result  # model temperature should be in top-level
        assert result["temperature"] == 0.7
        
        # The agent handler returns a dict that gets merged
        assert "name" in result
        assert result["name"] == "Test Agent"
        
        # The storage handler should return a storage object
        assert "storage" in result

    def test_validate_config(self, proxy):
        """Test configuration validation."""
        config = {
            "name": "Test Agent",
            "instructions": "Test instructions",
            "model": {"id": "claude-sonnet-4-20250514"},
            "knowledge_filter": {"max_results": 10},
            "unknown_param": "value",
        }

        validation_result = proxy.validate_config(config)

        assert "supported_agno_params" in validation_result
        assert "custom_params" in validation_result
        assert "unknown_params" in validation_result
        assert "total_agno_params_available" in validation_result
        assert "coverage_percentage" in validation_result

        assert "name" in validation_result["supported_agno_params"]
        assert "instructions" in validation_result["supported_agno_params"]
        assert "knowledge_filter" in validation_result["custom_params"]
        assert "unknown_param" in validation_result["unknown_params"]


class TestCustomParameterHandlers:
    """Test custom parameter handlers."""

    @pytest.fixture
    def proxy(self):
        """Create AgnoAgentProxy instance for testing."""
        return AgnoAgentProxy()

    @patch('lib.config.provider_registry.get_provider_registry')
    @patch('lib.utils.dynamic_model_resolver.filter_model_parameters')
    def test_handle_model_config(self, mock_filter, mock_registry, proxy):
        """Test model configuration handler with provider detection."""
        model_config = {
            "id": "claude-sonnet-4-20250514",
            "temperature": 0.8,
            "max_tokens": 3000,
            "custom_param": "value",
        }

        # Mock provider registry
        mock_provider_registry = MagicMock()
        mock_registry.return_value = mock_provider_registry
        mock_provider_registry.detect_provider.return_value = "anthropic"
        
        # Mock model class
        mock_model_class = MagicMock()
        mock_provider_registry.resolve_model_class.return_value = mock_model_class
        
        # Mock filter to return filtered parameters (remove custom_param)
        filtered_config = {
            "id": "claude-sonnet-4-20250514",
            "temperature": 0.8,
            "max_tokens": 3000,
        }
        mock_filter.return_value = filtered_config

        result = proxy._handle_model_config(model_config, {}, "test-agent", None)

        # Verify provider detection was called
        mock_provider_registry.detect_provider.assert_called_once_with("claude-sonnet-4-20250514")
        
        # Verify model class resolution was called
        mock_provider_registry.resolve_model_class.assert_called_once_with("anthropic", "claude-sonnet-4-20250514")
        
        # Verify filtering was called with the model class and original config
        mock_filter.assert_called_once_with(mock_model_class, model_config)
        
        # The result should be the filtered configuration for lazy instantiation
        assert result == {"id": "claude-sonnet-4-20250514", **filtered_config}

    @patch("lib.config.models.resolve_model")
    def test_handle_model_config_no_model_id(self, mock_resolve_model, proxy):
        """Test model configuration handler when no model ID is provided."""
        mock_model_instance = MagicMock()
        mock_resolve_model.return_value = mock_model_instance

        model_config = {"temperature": 0.5}  # No model ID

        result = proxy._handle_model_config(model_config, {}, "test-agent", None)

        # Should fallback to resolve_model when no model ID is specified
        mock_resolve_model.assert_called_once_with(model_id=None, **model_config)
        assert result == mock_model_instance

    @patch("lib.utils.proxy_agents.create_dynamic_storage")
    def test_handle_storage_config(self, mock_create_storage, proxy):
        """Test storage configuration handler."""
        mock_create_storage.return_value = "mock_storage"

        storage_config = {"type": "postgres", "url": "test://url"}

        result = proxy._handle_storage_config(
            storage_config, {}, "test-agent", "test://db"
        )

        mock_create_storage.assert_called_once_with(
            storage_config=storage_config,
            component_id="test-agent",
            component_mode="agent",
            db_url="test://db",
        )
        assert result == "mock_storage"

    @patch("lib.memory.memory_factory.create_agent_memory")
    def test_handle_memory_config_enabled(self, mock_create_memory, proxy):
        """Test memory configuration handler when enabled."""
        mock_create_memory.return_value = "mock_memory"

        memory_config = {"enable_user_memories": True}

        result = proxy._handle_memory_config(
            memory_config, {}, "test-agent", "test://db"
        )

        mock_create_memory.assert_called_once_with("test-agent", "test://db")
        assert result == "mock_memory"

    def test_handle_memory_config_disabled(self, proxy):
        """Test memory configuration handler when disabled."""
        memory_config = {"enable_user_memories": False}

        result = proxy._handle_memory_config(
            memory_config, {}, "test-agent", "test://db"
        )

        assert result is None

    def test_handle_memory_config_none(self, proxy):
        """Test memory configuration handler with None config."""
        result = proxy._handle_memory_config(None, {}, "test-agent", "test://db")

        assert result is None

    def test_handle_agent_metadata(self, proxy):
        """Test agent metadata handler."""
        agent_config = {
            "name": "Test Agent",
            "description": "Test description",
            "role": "test_role",
        }

        result = proxy._handle_agent_metadata(agent_config, {}, "test-agent", None)

        expected = {
            "name": "Test Agent",
            "description": "Test description",
            "role": "test_role",
        }
        assert result == expected

    def test_handle_agent_metadata_defaults(self, proxy):
        """Test agent metadata handler with default values."""
        agent_config = {}

        result = proxy._handle_agent_metadata(agent_config, {}, "test-agent", None)

        assert result["name"] == "Agent test-agent"
        assert result["description"] is None
        assert result["role"] is None

    def test_handle_custom_metadata(self, proxy):
        """Test custom metadata handler."""
        # These handlers don't return anything, just None
        result = proxy._handle_custom_metadata("value", {}, "test-agent", None)
        assert result is None

    def test_handle_display_section_valid(self, proxy):
        """Test display section handler with valid config."""
        # Mock supported params to include some display parameters
        proxy._supported_params = {"markdown", "stream", "unknown_param"}

        display_config = {
            "markdown": True,
            "stream": False,
            "unknown_param": "value",
            "unsupported_param": "ignored",
        }

        result = proxy._handle_display_section(display_config, {}, "test-agent", None)

        expected = {
            "markdown": True,
            "stream": False,
            "unknown_param": "value",
        }
        assert result == expected

    def test_handle_display_section_invalid(self, proxy):
        """Test display section handler with invalid config."""
        result = proxy._handle_display_section("not_a_dict", {}, "test-agent", None)

        assert result == {}

    @patch("lib.knowledge.knowledge_factory.get_knowledge_base")
    @patch("lib.utils.version_factory.load_global_knowledge_config")
    def test_handle_knowledge_filter_success(
        self, mock_load_global, mock_get_kb, proxy
    ):
        """Test knowledge filter handler success path."""
        mock_load_global.return_value = {
            "csv_file_path": "test.csv",
            "max_results": 20,
        }
        mock_get_kb.return_value = "mock_knowledge_base"

        knowledge_filter = {"max_results": 10}

        result = proxy._handle_knowledge_filter(
            knowledge_filter, {}, "test-agent", "test://db"
        )

        assert result == "mock_knowledge_base"
        mock_get_kb.assert_called_once()

    @patch(
        "lib.utils.version_factory.load_global_knowledge_config",
        side_effect=Exception("Config error"),
    )
    def test_handle_knowledge_filter_config_error(self, mock_load_global, proxy):
        """Test knowledge filter handler when global config fails."""
        knowledge_filter = {"max_results": 10}

        result = proxy._handle_knowledge_filter(
            knowledge_filter, {}, "test-agent", "test://db"
        )

        assert result is None

    def test_handle_knowledge_filter_no_db_url(self, proxy):
        """Test knowledge filter handler without db_url."""
        knowledge_filter = {"max_results": 10}

        with patch(
            "lib.utils.version_factory.load_global_knowledge_config",
            return_value={"csv_file_path": "test.csv"},
        ):
            result = proxy._handle_knowledge_filter(
                knowledge_filter, {}, "test-agent", None
            )

        assert result is None

    @patch("lib.knowledge.knowledge_factory.get_knowledge_base", return_value=None)
    @patch("lib.utils.version_factory.load_global_knowledge_config")
    @patch("lib.utils.proxy_agents.logger")
    def test_handle_knowledge_filter_warns_agent_csv_path(
        self, mock_logger, mock_load_global, mock_get_kb, proxy
    ):
        """Test knowledge filter handler warns about agent-level csv_file_path."""
        mock_load_global.return_value = {"csv_file_path": "global.csv"}

        knowledge_filter = {
            "csv_file_path": "agent.csv",  # Should warn about this
            "max_results": 10,
        }

        result = proxy._handle_knowledge_filter(
            knowledge_filter, {}, "test-agent", "test://db"
        )

        # Should return None as mocked get_knowledge_base returns None
        assert result is None
        
        # Verify that the warning was logged (check that our specific warning is in the calls)
        expected_call = call(
            "csv_file_path found in agent config - should use global config instead",
            component="test-agent",
            agent_path="agent.csv",
        )
        assert expected_call in mock_logger.warning.call_args_list
        
        # Verify that at least one warning was logged  
        assert mock_logger.warning.called


class TestMetricsWrapping:
    """Test metrics wrapping functionality."""

    @pytest.fixture
    def proxy(self):
        """Create AgnoAgentProxy instance for testing."""
        return AgnoAgentProxy()

    @pytest.fixture
    def mock_agent(self):
        """Create mock agent for testing."""
        agent = MagicMock()
        agent.run = MagicMock(return_value="test_response")
        agent.arun = AsyncMock(return_value="test_async_response")
        return agent

    @pytest.fixture
    def mock_metrics_service(self):
        """Create mock metrics service."""
        metrics = MagicMock()
        metrics.collect_from_response = MagicMock(return_value=True)
        return metrics

    def test_wrap_agent_with_metrics_sync(
        self, proxy, mock_agent, mock_metrics_service
    ):
        """Test wrapping agent with metrics for synchronous execution."""
        config = {"agent": {"name": "Test Agent"}}

        # Save reference to original run method before wrapping
        original_run = mock_agent.run

        wrapped_agent = proxy._wrap_agent_with_metrics(
            mock_agent, "test-agent", config, mock_metrics_service
        )

        # Test that the agent is returned (same instance, but run method is wrapped)
        assert wrapped_agent == mock_agent

        # Test wrapped run method
        result = wrapped_agent.run("test_input")
        assert result == "test_response"

        # Verify original run was called
        original_run.assert_called_once_with("test_input")

        # Verify metrics collection was called
        mock_metrics_service.collect_from_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_wrap_agent_with_metrics_async(
        self, proxy, mock_agent, mock_metrics_service
    ):
        """Test wrapping agent with metrics for asynchronous execution."""
        config = {"agent": {"name": "Test Agent"}}

        # Save reference to original arun method before wrapping
        original_arun = mock_agent.arun

        wrapped_agent = proxy._wrap_agent_with_metrics(
            mock_agent, "test-agent", config, mock_metrics_service
        )

        # Test wrapped arun method
        result = await wrapped_agent.arun("test_input")
        assert result == "test_async_response"

        # Verify original arun was called
        original_arun.assert_called_once_with("test_input")

        # Verify metrics collection was called (only once for this test)
        mock_metrics_service.collect_from_response.assert_called_once()

    def test_wrap_agent_without_arun(self, proxy, mock_metrics_service):
        """Test wrapping agent that doesn't have arun method."""
        # Create a more controlled mock that doesn't auto-create attributes
        agent = MagicMock(spec=['run'])  # Only allow 'run' attribute
        agent.run = MagicMock(return_value="test_response")

        config = {"agent": {"name": "Test Agent"}}

        # Verify agent doesn't have arun before wrapping
        assert not hasattr(agent, "arun")

        wrapped_agent = proxy._wrap_agent_with_metrics(
            agent, "test-agent", config, mock_metrics_service
        )

        # Should only wrap run method
        assert wrapped_agent == agent
        assert hasattr(wrapped_agent, "run")
        assert not hasattr(wrapped_agent, "arun")
        
        # Test that the wrapped run method works
        result = wrapped_agent.run("test_input")
        assert result == "test_response"

    def test_wrapped_run_with_metrics_error(
        self, proxy, mock_agent, mock_metrics_service
    ):
        """Test wrapped run method when metrics collection fails."""
        mock_metrics_service.collect_from_response.side_effect = Exception(
            "Metrics error"
        )
        config = {"agent": {"name": "Test Agent"}}

        wrapped_agent = proxy._wrap_agent_with_metrics(
            mock_agent, "test-agent", config, mock_metrics_service
        )

        # Should still return response even if metrics fail
        result = wrapped_agent.run("test_input")
        assert result == "test_response"

    def test_wrapped_run_with_agent_error(self, proxy, mock_metrics_service):
        """Test wrapped run method when agent execution fails."""
        agent = MagicMock()
        agent.run = MagicMock(side_effect=Exception("Agent error"))

        config = {"agent": {"name": "Test Agent"}}

        wrapped_agent = proxy._wrap_agent_with_metrics(
            agent, "test-agent", config, mock_metrics_service
        )

        # Should re-raise agent execution error
        with pytest.raises(Exception, match="Agent error"):
            wrapped_agent.run("test_input")

    def test_wrapped_run_with_none_response(self, proxy, mock_metrics_service):
        """Test wrapped run method when agent returns None."""
        agent = MagicMock()
        agent.run = MagicMock(return_value=None)

        config = {"agent": {"name": "Test Agent"}}

        wrapped_agent = proxy._wrap_agent_with_metrics(
            agent, "test-agent", config, mock_metrics_service
        )

        result = wrapped_agent.run("test_input")
        assert result is None

        # Should not call metrics collection for None response
        mock_metrics_service.collect_from_response.assert_not_called()

    def test_extract_metrics_overrides(self, proxy):
        """Test metrics overrides extraction."""
        config = {
            "metrics_enabled": True,
            "agent": {
                "metrics_enabled": False,  # Should override root level
            },
        }

        overrides = proxy._extract_metrics_overrides(config)

        assert overrides["metrics_enabled"] is False  # Agent level takes precedence

    def test_extract_metrics_overrides_root_only(self, proxy):
        """Test metrics overrides extraction with root level only."""
        config = {
            "metrics_enabled": True,
            "agent": {},
        }

        overrides = proxy._extract_metrics_overrides(config)

        assert overrides["metrics_enabled"] is True

    def test_extract_metrics_overrides_none(self, proxy):
        """Test metrics overrides extraction with no metrics config."""
        config = {"agent": {}}

        overrides = proxy._extract_metrics_overrides(config)

        assert overrides == {}


class TestMetadataCreation:
    """Test metadata creation functionality."""

    @pytest.fixture
    def proxy(self):
        """Create AgnoAgentProxy instance for testing."""
        return AgnoAgentProxy()

    def test_create_metadata_complete(self, proxy):
        """Test metadata creation with complete config."""
        config = {
            "agent": {
                "version": 2,
            },
            "knowledge_filter": {"max_results": 10},
            "suggested_actions": ["action1", "action2"],
            "escalation_triggers": {"error_count": 5},
            "streaming_config": {"enabled": True},
            "events_config": {"store_events": True},
            "context_config": {"max_context": 1000},
            "display_config": {"markdown": True},
            "display": {"stream": False},
        }

        metadata = proxy._create_metadata(config, "test-agent")

        assert metadata["version"] == 2
        assert metadata["loaded_from"] == "proxy_agents"
        assert metadata["agent_id"] == "test-agent"
        assert metadata["agno_parameters_count"] == len(proxy._supported_params)

        custom_params = metadata["custom_parameters"]
        assert custom_params["knowledge_filter"] == {"max_results": 10}
        assert custom_params["suggested_actions"] == ["action1", "action2"]
        assert custom_params["escalation_triggers"] == {"error_count": 5}
        assert custom_params["streaming_config"] == {"enabled": True}
        assert custom_params["events_config"] == {"store_events": True}
        assert custom_params["context_config"] == {"max_context": 1000}
        assert custom_params["display_config"] == {"markdown": True}
        assert custom_params["display"] == {"stream": False}

    def test_create_metadata_minimal(self, proxy):
        """Test metadata creation with minimal config."""
        config = {}

        metadata = proxy._create_metadata(config, "test-agent")

        assert metadata["version"] == 1  # Default version
        assert metadata["loaded_from"] == "proxy_agents"
        assert metadata["agent_id"] == "test-agent"
        assert metadata["agno_parameters_count"] == len(proxy._supported_params)

        # All custom parameters should have empty defaults
        custom_params = metadata["custom_parameters"]
        for param_name in [
            "knowledge_filter",
            "suggested_actions",
            "escalation_triggers",
            "streaming_config",
            "events_config",
            "context_config",
            "display_config",
            "display",
        ]:
            assert custom_params[param_name] == {}


class TestProxyAgentCreation:
    """Test proxy agent creation functionality."""

    @patch("lib.utils.proxy_agents.Agent")
    def test_create_proxy_agent(self, mock_agent):
        """Test creating a proxy agent from configuration."""
        # Mock dependencies
        mock_agent_instance = MagicMock()
        mock_agent.return_value = mock_agent_instance

        # Import the module (this will test the import path)
        import lib.utils.proxy_agents

        # Test that Agent class is available (Claude is not imported in this module)
        assert lib.utils.proxy_agents.Agent == mock_agent

        # Test that the AgnoAgentProxy class exists
        assert hasattr(lib.utils.proxy_agents, "AgnoAgentProxy")

        # Test creating a proxy instance
        proxy = lib.utils.proxy_agents.AgnoAgentProxy()
        assert proxy is not None
        assert hasattr(proxy, "_supported_params")
        assert hasattr(proxy, "_custom_params")


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""

    @pytest.fixture
    def proxy(self):
        """Create AgnoAgentProxy instance for testing."""
        return AgnoAgentProxy()

    @pytest.mark.asyncio
    @patch("lib.utils.proxy_agents.Agent")
    async def test_create_agent_with_knowledge_filter_special_handling(
        self, mock_agent_class, proxy
    ):
        """Test create_agent with knowledge_filter special handling."""
        mock_agent = MagicMock()
        mock_agent.metadata = {}
        mock_agent_class.return_value = mock_agent

        config = {
            "knowledge_filter": {"max_results": 10},
            "instructions": "Test instructions",
        }

        # Test that knowledge_filter gets processed and mapped to 'knowledge' parameter
        await proxy.create_agent(
            component_id="test-agent",
            config=config,
        )

        # Verify that knowledge_filter was processed (doesn't appear in final params)
        call_args, call_kwargs = mock_agent_class.call_args
        assert "knowledge_filter" not in call_kwargs  # knowledge_filter should be processed and removed
        
        # The handler might return None due to missing database, but that's OK for this test
        # We just need to verify the key transformation happened

    def test_process_config_dict_return_from_handler(self, proxy):
        """Test _process_config when handler returns a dictionary."""
        config = {"custom_param": {"setting": "value"}}

        def mock_handler(value, config, component_id, db_url):
            return {"flattened_param1": "value1", "flattened_param2": "value2"}

        proxy._custom_params["custom_param"] = mock_handler

        processed = proxy._process_config(config, "test-agent", None)

        assert processed["flattened_param1"] == "value1"
        assert processed["flattened_param2"] == "value2"
        assert "custom_param" not in processed

    def test_fallback_parameters_coverage(self, proxy):
        """Test that fallback parameters include expected Agno parameters."""
        fallback_params = proxy._get_fallback_parameters()

        # Check for key categories of parameters
        core_params = {"model", "name", "agent_id", "instructions"}
        assert core_params.issubset(fallback_params)

        session_params = {"session_id", "session_name", "cache_session"}
        assert session_params.issubset(fallback_params)

        memory_params = {"memory", "enable_user_memories", "enable_agentic_memory"}
        assert memory_params.issubset(fallback_params)

        tool_params = {"tools", "show_tool_calls", "tool_call_limit"}
        assert tool_params.issubset(fallback_params)

        # Verify it's a reasonably complete set
        assert len(fallback_params) > 50

    @pytest.mark.asyncio
    async def test_create_agent_filters_none_values(self, proxy):
        """Test that create_agent filters out None values from parameters."""
        config = {
            "name": "Test Agent",
            "instructions": "Test instructions",
        }

        # Mock _process_config to return some None values
        def mock_process_config(config, component_id, db_url):
            return {
                "name": "Test Agent",
                "instructions": "Test instructions",
                "description": None,  # Should be filtered out (None value)
                "role": "assistant",   # Should be included (valid supported parameter)
            }

        with (
            patch.object(proxy, "_process_config", side_effect=mock_process_config),
            patch("lib.utils.proxy_agents.Agent") as mock_agent_class,
        ):
            mock_agent = MagicMock()
            mock_agent.metadata = {}
            mock_agent_class.return_value = mock_agent

            await proxy.create_agent(
                component_id="test-agent",
                config=config,
            )

            # Verify None values were filtered out
            call_args, call_kwargs = mock_agent_class.call_args
            assert "description" not in call_kwargs  # None value filtered out
            assert call_kwargs.get("name") == "Test Agent"
            assert call_kwargs.get("role") == "assistant"  # Valid parameter included

    def test_handle_knowledge_filter_no_csv_path(self, proxy):
        """Test knowledge filter handler when no csv_file_path in global config."""
        knowledge_filter = {"max_results": 10}

        with patch(
            "lib.utils.version_factory.load_global_knowledge_config", return_value={}
        ):
            result = proxy._handle_knowledge_filter(
                knowledge_filter, {}, "test-agent", "test://db"
            )

        assert result is None

    @patch(
        "lib.knowledge.knowledge_factory.get_knowledge_base",
        side_effect=Exception("KB creation failed"),
    )
    @patch("lib.utils.version_factory.load_global_knowledge_config")
    def test_handle_knowledge_filter_kb_creation_failure(
        self, mock_load_global, mock_get_kb, proxy
    ):
        """Test knowledge filter handler when knowledge base creation fails."""
        mock_load_global.return_value = {"csv_file_path": "test.csv"}
        knowledge_filter = {"max_results": 10}

        result = proxy._handle_knowledge_filter(
            knowledge_filter, {}, "test-agent", "test://db"
        )

        assert result is None  # Should return None on failure

    @pytest.mark.asyncio
    async def test_wrap_agent_without_collect_from_response_method(self, proxy):
        """Test metrics wrapping when service doesn't have collect_from_response."""
        agent = MagicMock()
        agent.run = MagicMock(return_value="test_response")

        # Metrics service without the expected method
        metrics_service = MagicMock()
        del metrics_service.collect_from_response  # Remove the method

        config = {"agent": {"name": "Test Agent"}}

        wrapped_agent = proxy._wrap_agent_with_metrics(
            agent, "test-agent", config, metrics_service
        )

        # Should still wrap but not call non-existent method
        result = wrapped_agent.run("test_input")
        assert result == "test_response"

    def test_metrics_wrapping_false_return(self, proxy):
        """Test metrics wrapping when collect_from_response returns False."""
        agent = MagicMock()
        agent.run = MagicMock(return_value="test_response")

        metrics_service = MagicMock()
        metrics_service.collect_from_response = MagicMock(return_value=False)

        config = {"agent": {"name": "Test Agent"}}

        wrapped_agent = proxy._wrap_agent_with_metrics(
            agent, "test-agent", config, metrics_service
        )

        result = wrapped_agent.run("test_input")
        assert result == "test_response"

        # Should still call the metrics method even if it returns False
        metrics_service.collect_from_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_wrapped_run_complete_flow(self, proxy):
        """Test complete async wrapped run flow."""
        agent = MagicMock()
        agent.arun = AsyncMock(return_value="async_response")

        metrics_service = MagicMock()
        metrics_service.collect_from_response = MagicMock(return_value=True)

        config = {"metrics_enabled": True, "agent": {"metrics_enabled": True}}

        wrapped_agent = proxy._wrap_agent_with_metrics(
            agent, "test-agent", config, metrics_service
        )

        result = await wrapped_agent.arun("async_input")
        assert result == "async_response"

        # Verify metrics collection was called with correct parameters
        metrics_call = metrics_service.collect_from_response.call_args
        assert metrics_call[1]["response"] == "async_response"
        assert metrics_call[1]["agent_name"] == "test-agent"
        assert metrics_call[1]["execution_type"] == "agent"
        assert metrics_call[1]["yaml_overrides"] == {"metrics_enabled": True}


class TestComprehensiveIntegration:
    """Test comprehensive integration scenarios."""

    @pytest.fixture
    def proxy(self):
        """Create AgnoAgentProxy instance for testing."""
        return AgnoAgentProxy()

    @pytest.mark.asyncio
    @patch("lib.utils.proxy_agents.Agent")
    @patch("lib.config.models.resolve_model")
    @patch("lib.utils.proxy_agents.create_dynamic_storage")
    @patch("lib.memory.memory_factory.create_agent_memory")
    async def test_comprehensive_agent_creation(
        self, mock_memory, mock_storage, mock_model, mock_agent_class, proxy
    ):
        """Test comprehensive agent creation with all features."""
        # Setup mocks
        mock_model.return_value = "mock_model"
        mock_storage.return_value = "mock_storage"
        mock_memory.return_value = "mock_memory"

        mock_agent = MagicMock()
        mock_agent.metadata = {}
        mock_agent_class.return_value = mock_agent

        # Comprehensive config
        config = {
            "agent": {
                "name": "Comprehensive Test Agent",
                "version": 3,
                "description": "Full feature test",
                "role": "testing",
            },
            "model": {
                "id": "test-model-advanced",
                "temperature": 0.9,
                "max_tokens": 4000,
                "custom_model_param": "value",
            },
            "storage": {
                "type": "postgres",  # Use correct storage type name
                "connection_string": "test://connection",
            },
            "memory": {
                "enable_user_memories": True,
            },
            "instructions": "Comprehensive test instructions",
            "tools": [{"name": "advanced_tool", "config": {}}],
            "display": {
                "markdown": True,
                "stream": False,
            },
            "knowledge_filter": {
                "max_results": 15,
            },
            "suggested_actions": ["action1", "action2"],
            "escalation_triggers": {"threshold": 10},
        }

        # Create agent
        agent = await proxy.create_agent(
            component_id="comprehensive-test-agent",
            config=config,
            session_id="test-session-123",
            debug_mode=True,
            user_id="test-user-456",
            db_url="sqlite:///:memory:",  # Use valid SQLAlchemy URL for in-memory SQLite
        )

        # Verify storage and memory handlers were called
        # Note: resolve_model is NOT called when model_id is present (uses lazy instantiation)
        mock_storage.assert_called_once()
        mock_memory.assert_called_once()

        # Verify agent creation
        assert agent is not None
        assert agent == mock_agent

        # Verify metadata was set correctly
        metadata = proxy._create_metadata(config, "comprehensive-test-agent")
        assert metadata["version"] == 3
        assert metadata["agent_id"] == "comprehensive-test-agent"
        assert metadata["custom_parameters"]["suggested_actions"] == [
            "action1",
            "action2",
        ]
        assert metadata["custom_parameters"]["escalation_triggers"] == {"threshold": 10}

    @pytest.mark.asyncio
    @patch("lib.utils.proxy_agents.Agent")
    async def test_agent_creation_with_metrics_full_flow(self, mock_agent_class, proxy):
        """Test complete agent creation and metrics wrapping flow."""
        # Setup agent mock
        mock_agent = MagicMock()
        mock_agent.metadata = {}
        mock_agent.run = MagicMock(return_value="execution_response")
        mock_agent.arun = AsyncMock(return_value="async_execution_response")
        mock_agent_class.return_value = mock_agent

        # Setup metrics service
        metrics_service = MagicMock()
        metrics_service.collect_from_response = MagicMock(return_value=True)

        config = {
            "agent": {"name": "Metrics Test Agent"},
            "instructions": "Test agent with metrics",
            "metrics_enabled": True,
        }

        # Create agent with metrics
        agent = await proxy.create_agent(
            component_id="metrics-test-agent",
            config=config,
            metrics_service=metrics_service,
        )

        # Test sync execution with metrics
        sync_result = agent.run("test input")
        assert sync_result == "execution_response"
        metrics_service.collect_from_response.assert_called()

        # Reset mock to test async
        metrics_service.collect_from_response.reset_mock()

        # Test async execution with metrics
        async_result = await agent.arun("async test input")
        assert async_result == "async_execution_response"
        metrics_service.collect_from_response.assert_called()

        # Verify metrics service is stored in metadata
        assert agent.metadata.get("metrics_service") == metrics_service


# All old test classes have been replaced with comprehensive real functionality tests above
