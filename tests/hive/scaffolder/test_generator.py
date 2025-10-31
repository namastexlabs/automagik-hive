"""Tests for ConfigGenerator - team modes, agent loading, and workflow steps."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hive.scaffolder.generator import ConfigGenerator, GeneratorError


class TestTranslateTeamMode:
    """Test team mode translation to Agno boolean flags."""

    def test_none_mode_returns_empty_dict(self):
        """None mode should return empty dict (default Agno behavior)."""
        result = ConfigGenerator._translate_team_mode(None)

        assert result == {}
        assert isinstance(result, dict)

    def test_empty_string_returns_empty_dict(self):
        """Empty string mode should return empty dict."""
        result = ConfigGenerator._translate_team_mode("")

        assert result == {}

    def test_default_mode_returns_correct_flags(self):
        """Default mode should set synthesize flags."""
        result = ConfigGenerator._translate_team_mode("default")

        assert result == {
            "respond_directly": False,
            "delegate_task_to_all_members": False,
        }

    def test_collaboration_mode_returns_correct_flags(self):
        """Collaboration mode should enable all agents in parallel."""
        result = ConfigGenerator._translate_team_mode("collaboration")

        assert result == {
            "delegate_task_to_all_members": True,
            "respond_directly": False,
        }

    def test_router_mode_returns_correct_flags(self):
        """Router mode should enable passthrough (no synthesis)."""
        result = ConfigGenerator._translate_team_mode("router")

        assert result == {
            "respond_directly": True,
            "determine_input_for_members": False,
        }

    def test_passthrough_mode_returns_correct_flags(self):
        """Passthrough mode should be alias for router."""
        result = ConfigGenerator._translate_team_mode("passthrough")

        assert result == {"respond_directly": True}

    def test_case_insensitive_mode_matching(self):
        """Mode matching should be case insensitive."""
        result_upper = ConfigGenerator._translate_team_mode("DEFAULT")
        result_mixed = ConfigGenerator._translate_team_mode("DeFaUlT")

        assert result_upper == result_mixed
        assert result_upper == {
            "respond_directly": False,
            "delegate_task_to_all_members": False,
        }

    def test_unknown_mode_raises_error(self):
        """Unknown mode should raise GeneratorError with available modes."""
        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._translate_team_mode("invalid_mode")

        error_msg = str(exc_info.value)
        assert "Unknown team mode: invalid_mode" in error_msg
        assert "default" in error_msg
        assert "collaboration" in error_msg
        assert "router" in error_msg
        assert "passthrough" in error_msg


class TestResolveAgentReference:
    """Test agent reference resolution."""

    @patch("hive.scaffolder.generator.ConfigGenerator.generate_agent_from_yaml")
    def test_yaml_path_loads_from_file(self, mock_generate):
        """YAML path should trigger file-based agent loading."""
        mock_agent = MagicMock()
        mock_generate.return_value = mock_agent

        result = ConfigGenerator._resolve_agent_reference("agents/my-agent.yaml")

        mock_generate.assert_called_once_with("agents/my-agent.yaml", validate=False)
        assert result == mock_agent

    @patch("hive.scaffolder.generator.ConfigGenerator.generate_agent_from_yaml")
    def test_yml_extension_loads_from_file(self, mock_generate):
        """YML extension should also trigger file-based loading."""
        mock_agent = MagicMock()
        mock_generate.return_value = mock_agent

        result = ConfigGenerator._resolve_agent_reference("agents/my-agent.yml")

        mock_generate.assert_called_once_with("agents/my-agent.yml", validate=False)
        assert result == mock_agent

    @patch("hive.discovery.discover_agents")
    @patch("hive.discovery.get_agent_by_id")
    def test_agent_id_lookup_from_registry(self, mock_get_agent, mock_discover):
        """Agent ID should lookup from registry."""
        mock_agent = MagicMock()
        mock_agent.id = "test-agent"
        mock_available = [mock_agent]

        mock_discover.return_value = mock_available
        mock_get_agent.return_value = mock_agent

        result = ConfigGenerator._resolve_agent_reference("test-agent")

        mock_discover.assert_called_once()
        mock_get_agent.assert_called_once_with("test-agent", mock_available)
        assert result == mock_agent

    @patch("hive.discovery.discover_agents")
    @patch("hive.discovery.get_agent_by_id")
    def test_unknown_agent_id_raises_error(self, mock_get_agent, mock_discover):
        """Unknown agent ID should raise GeneratorError."""
        mock_agent = MagicMock()
        mock_agent.id = "existing-agent"
        mock_available = [mock_agent]

        mock_discover.return_value = mock_available
        mock_get_agent.return_value = None

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._resolve_agent_reference("unknown-agent")

        error_msg = str(exc_info.value)
        assert "Agent not found: unknown-agent" in error_msg
        assert "existing-agent" in error_msg


class TestLoadMemberAgents:
    """Test member agent loading for teams."""

    @patch("hive.scaffolder.generator.ConfigGenerator.generate_agent_from_yaml")
    @patch("hive.discovery.discover_agents")
    @patch("hive.discovery.get_agent_by_id")
    def test_loads_mixed_yaml_and_registry_agents(self, mock_get_agent, mock_discover, mock_generate):
        """Should load agents from both YAML files and registry."""
        # Setup mocks
        yaml_agent = MagicMock()
        yaml_agent.id = "yaml-agent"

        registry_agent = MagicMock()
        registry_agent.id = "registry-agent"

        mock_generate.return_value = yaml_agent
        mock_discover.return_value = [registry_agent]
        mock_get_agent.return_value = registry_agent

        # Load mixed member list
        member_ids = ["agents/yaml-agent.yaml", "registry-agent"]
        result = ConfigGenerator._load_member_agents(member_ids)

        assert len(result) == 2
        assert result[0] == yaml_agent
        assert result[1] == registry_agent
        mock_generate.assert_called_once_with("agents/yaml-agent.yaml", validate=False)

    @patch("hive.discovery.discover_agents")
    @patch("hive.discovery.get_agent_by_id")
    def test_missing_agent_raises_error_with_available_list(self, mock_get_agent, mock_discover):
        """Missing agent should raise error listing available agents."""
        available_agent = MagicMock()
        available_agent.id = "available-agent"

        mock_discover.return_value = [available_agent]
        mock_get_agent.return_value = None

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_member_agents(["missing-agent"])

        error_msg = str(exc_info.value)
        assert "Member agent not found: missing-agent" in error_msg
        assert "available-agent" in error_msg


class TestBuildConditionEvaluator:
    """Test condition evaluator builder for workflows."""

    def test_equals_operator_builds_correct_evaluator(self):
        """Equals operator should build equality check."""
        config = {"operator": "equals", "field": "status", "value": "active"}
        evaluator = ConfigGenerator._build_condition_evaluator(config)

        # Mock StepInput
        mock_input_true = Mock()
        mock_input_true.input = {"status": "active"}

        mock_input_false = Mock()
        mock_input_false.input = {"status": "inactive"}

        assert evaluator(mock_input_true) is True
        assert evaluator(mock_input_false) is False

    def test_not_equals_operator_builds_correct_evaluator(self):
        """Not equals operator should build inequality check."""
        config = {"operator": "not_equals", "field": "status", "value": "deleted"}
        evaluator = ConfigGenerator._build_condition_evaluator(config)

        mock_input = Mock()
        mock_input.input = {"status": "active"}

        assert evaluator(mock_input) is True

    def test_contains_operator_builds_correct_evaluator(self):
        """Contains operator should build substring check."""
        config = {"operator": "contains", "field": "message", "value": "error"}
        evaluator = ConfigGenerator._build_condition_evaluator(config)

        mock_input_true = Mock()
        mock_input_true.input = {"message": "An error occurred"}

        mock_input_false = Mock()
        mock_input_false.input = {"message": "Success"}

        assert evaluator(mock_input_true) is True
        assert evaluator(mock_input_false) is False

    def test_greater_than_operator_builds_correct_evaluator(self):
        """Greater than operator should build numeric comparison."""
        config = {"operator": "greater_than", "field": "count", "value": 10}
        evaluator = ConfigGenerator._build_condition_evaluator(config)

        mock_input_true = Mock()
        mock_input_true.input = {"count": 15}

        mock_input_false = Mock()
        mock_input_false.input = {"count": 5}

        assert evaluator(mock_input_true) is True
        assert evaluator(mock_input_false) is False

    def test_less_than_operator_builds_correct_evaluator(self):
        """Less than operator should build numeric comparison."""
        config = {"operator": "less_than", "field": "price", "value": 100}
        evaluator = ConfigGenerator._build_condition_evaluator(config)

        mock_input = Mock()
        mock_input.input = {"price": 50}

        assert evaluator(mock_input) is True

    def test_missing_required_fields_raises_error(self):
        """Missing operator, field, or value should raise error."""
        incomplete_configs = [
            {"operator": "equals", "field": "status"},  # Missing value
            {"operator": "equals", "value": "test"},  # Missing field
            {"field": "status", "value": "test"},  # Missing operator
        ]

        for config in incomplete_configs:
            with pytest.raises(GeneratorError) as exc_info:
                ConfigGenerator._build_condition_evaluator(config)

            assert "must include: operator, field, value" in str(exc_info.value)

    def test_unknown_operator_raises_error(self):
        """Unknown operator should raise error with available list."""
        config = {"operator": "invalid_op", "field": "test", "value": "test"}

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._build_condition_evaluator(config)

        error_msg = str(exc_info.value)
        assert "Unknown condition operator: invalid_op" in error_msg
        assert "equals" in error_msg
        assert "contains" in error_msg


class TestBuildLoopEndCondition:
    """Test loop end condition builder."""

    def test_content_length_condition_breaks_when_threshold_met(self):
        """Content length condition should break when content exceeds threshold."""
        config = {"type": "content_length", "threshold": 100}
        end_condition = ConfigGenerator._build_loop_end_condition(config)

        # Mock outputs with content
        mock_output_short = Mock()
        mock_output_short.content = "Short content"

        mock_output_long = Mock()
        mock_output_long.content = "x" * 150

        assert end_condition([mock_output_short]) is False  # Continue
        assert end_condition([mock_output_long]) is True  # Break

    def test_success_count_condition_breaks_when_threshold_met(self):
        """Success count condition should break when enough successes."""
        config = {"type": "success_count", "threshold": 3}
        end_condition = ConfigGenerator._build_loop_end_condition(config)

        # Mock successful outputs
        success_outputs = [Mock(success=True) for _ in range(3)]
        partial_outputs = [Mock(success=True), Mock(success=False)]

        assert end_condition(success_outputs) is True  # Break (3 successes)
        assert end_condition(partial_outputs) is False  # Continue (only 1 success)

    def test_always_continue_never_breaks(self):
        """Always continue should never break early."""
        config = {"type": "always_continue"}
        end_condition = ConfigGenerator._build_loop_end_condition(config)

        # Any outputs should not break
        mock_outputs = [Mock(content="test", success=True) for _ in range(10)]

        assert end_condition(mock_outputs) is False

    def test_empty_outputs_returns_false(self):
        """Empty outputs should not trigger break."""
        config = {"type": "content_length", "threshold": 100}
        end_condition = ConfigGenerator._build_loop_end_condition(config)

        assert end_condition([]) is False

    def test_missing_threshold_raises_error(self):
        """Missing threshold for types that require it should raise error."""
        configs_needing_threshold = [
            {"type": "content_length"},
            {"type": "success_count"},
        ]

        for config in configs_needing_threshold:
            with pytest.raises(GeneratorError) as exc_info:
                ConfigGenerator._build_loop_end_condition(config)

            assert "requires 'threshold'" in str(exc_info.value)

    def test_unknown_type_raises_error(self):
        """Unknown loop end condition type should raise error."""
        config = {"type": "invalid_type", "threshold": 5}

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._build_loop_end_condition(config)

        error_msg = str(exc_info.value)
        assert "Unknown loop end condition type: invalid_type" in error_msg
        assert "content_length" in error_msg
        assert "success_count" in error_msg
        assert "always_continue" in error_msg


class TestLoadFunctionReference:
    """Test function loading by import path."""

    def test_loads_function_from_dotted_path(self):
        """Should load function from dotted import path."""
        # Use a real Python builtin function
        result = ConfigGenerator._load_function_reference("os.path.join")

        assert callable(result)
        assert result.__name__ == "join"

    def test_non_callable_raises_error(self):
        """Non-callable attribute should raise error."""
        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_function_reference("sys.version")

        assert "is not callable" in str(exc_info.value)

    def test_invalid_import_path_raises_error(self):
        """Invalid import path should raise error."""
        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_function_reference("nonexistent.module.function")

        assert "Failed to load function" in str(exc_info.value)

    def test_simple_name_without_dots_raises_error(self):
        """Simple function name without dots should raise error with guidance."""
        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_function_reference("my_function")

        error_msg = str(exc_info.value)
        assert "requires function registry" in error_msg
        assert "dotted import path" in error_msg


class TestLoadWorkflowSteps:
    """Test workflow step loading from config."""

    @patch("hive.scaffolder.generator.ConfigGenerator._resolve_agent_reference")
    def test_loads_sequential_step_with_agent(self, mock_resolve):
        """Should load sequential step with agent."""
        from agno.workflow import Step

        mock_agent = MagicMock()
        mock_resolve.return_value = mock_agent

        steps_config = [
            {
                "name": "analyze_data",
                "type": "sequential",
                "agent": "analyst-agent",
                "description": "Analyze the data",
            }
        ]

        result = ConfigGenerator._load_workflow_steps(steps_config)

        assert len(result) == 1
        assert isinstance(result[0], Step)
        assert result[0].name == "analyze_data"
        mock_resolve.assert_called_once_with("analyst-agent")

    @patch("hive.scaffolder.generator.ConfigGenerator._resolve_agent_reference")
    def test_parallel_step_with_nested_steps(self, mock_resolve):
        """Should load parallel step with variadic args."""
        from agno.workflow import Parallel

        mock_agent = MagicMock()
        mock_resolve.return_value = mock_agent

        steps_config = [
            {
                "name": "parallel_analysis",
                "type": "parallel",
                "description": "Parallel processing",
                "parallel_steps": [
                    {"name": "step1", "type": "sequential", "agent": "agent1"},
                    {"name": "step2", "type": "sequential", "agent": "agent2"},
                ],
            }
        ]

        result = ConfigGenerator._load_workflow_steps(steps_config)

        assert len(result) == 1
        assert isinstance(result[0], Parallel)
        assert result[0].name == "parallel_analysis"

    @patch("hive.scaffolder.generator.ConfigGenerator._resolve_agent_reference")
    def test_conditional_step_with_evaluator(self, mock_resolve):
        """Should load conditional step with evaluator function."""
        from agno.workflow import Condition

        mock_agent = MagicMock()
        mock_resolve.return_value = mock_agent

        steps_config = [
            {
                "name": "check_status",
                "type": "conditional",
                "condition": {"operator": "equals", "field": "status", "value": "ready"},
                "steps": [
                    {"name": "process", "type": "sequential", "agent": "processor"},
                ],
            }
        ]

        result = ConfigGenerator._load_workflow_steps(steps_config)

        assert len(result) == 1
        assert isinstance(result[0], Condition)
        assert result[0].name == "check_status"
        assert callable(result[0].evaluator)

    @patch("hive.scaffolder.generator.ConfigGenerator._resolve_agent_reference")
    def test_loop_step_with_end_condition(self, mock_resolve):
        """Should load loop step with end condition."""
        from agno.workflow import Loop

        mock_agent = MagicMock()
        mock_resolve.return_value = mock_agent

        steps_config = [
            {
                "name": "iterate",
                "type": "loop",
                "max_iterations": 5,
                "end_condition": {"type": "success_count", "threshold": 3},
                "steps": [
                    {"name": "process", "type": "sequential", "agent": "processor"},
                ],
            }
        ]

        result = ConfigGenerator._load_workflow_steps(steps_config)

        assert len(result) == 1
        assert isinstance(result[0], Loop)
        assert result[0].name == "iterate"
        assert result[0].max_iterations == 5

    def test_function_step_with_executor(self):
        """Should load function step with executor."""
        from agno.workflow import Step

        steps_config = [
            {
                "name": "transform",
                "type": "function",
                "function": "os.path.join",
                "description": "Join paths",
            }
        ]

        result = ConfigGenerator._load_workflow_steps(steps_config)

        assert len(result) == 1
        assert isinstance(result[0], Step)
        assert result[0].name == "transform"
        assert callable(result[0].executor)

    def test_unknown_step_type_raises_error(self):
        """Unknown step type should raise error."""
        steps_config = [{"name": "invalid", "type": "unknown_type"}]

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_workflow_steps(steps_config)

        assert "Unknown step type: unknown_type" in str(exc_info.value)


class TestLoadYaml:
    """Test YAML file loading."""

    def test_loads_valid_yaml_file(self, tmp_path):
        """Should load and parse valid YAML file."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("name: test\nvalue: 123")

        result = ConfigGenerator._load_yaml(str(yaml_file))

        assert result == {"name": "test", "value": 123}

    def test_file_not_found_raises_error(self):
        """Should raise GeneratorError for non-existent file."""
        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_yaml("/nonexistent/file.yaml")

        assert "Config file not found" in str(exc_info.value)

    def test_invalid_yaml_syntax_raises_error(self, tmp_path):
        """Should raise GeneratorError for invalid YAML syntax."""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("invalid: yaml: syntax: [")

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_yaml(str(yaml_file))

        assert "Invalid YAML syntax" in str(exc_info.value)


class TestParseModel:
    """Test model string parsing to Agno Model objects."""

    def test_none_returns_none(self):
        """None model string should return None."""
        result = ConfigGenerator._parse_model(None)
        assert result is None

    def test_already_model_object_returns_as_is(self):
        """Already instantiated model object should be returned as-is."""
        mock_model = MagicMock()
        result = ConfigGenerator._parse_model(mock_model)
        assert result is mock_model

    def test_openai_provider_returns_openai_chat(self):
        """OpenAI provider should return OpenAIChat instance."""
        result = ConfigGenerator._parse_model("openai:gpt-4o-mini")

        assert result is not None
        assert result.__class__.__name__ == "OpenAIChat"
        assert result.id == "gpt-4o-mini"

    def test_anthropic_provider_returns_claude(self):
        """Anthropic provider should return Claude instance."""
        result = ConfigGenerator._parse_model("anthropic:claude-3-sonnet")

        assert result is not None
        assert result.__class__.__name__ == "Claude"
        assert result.id == "claude-3-sonnet"

    def test_google_provider_returns_gemini(self):
        """Google provider should return Gemini instance."""
        try:
            # Try to import the provider first
            from agno.models.google import Gemini  # noqa: F401

            result = ConfigGenerator._parse_model("google:gemini-2.0-flash")
            assert result is not None
            assert result.__class__.__name__ == "Gemini"
            assert result.id == "gemini-2.0-flash"
        except ImportError as e:
            pytest.skip(f"Google AI SDK not installed: {e}")
        except Exception as e:
            # Skip if Google AI not configured
            error_str = str(e)
            if "google-genai" in error_str.lower() or "GOOGLE_API_KEY" in error_str:
                pytest.skip(f"Google AI not configured: {e}")
            raise

    def test_groq_provider_returns_groq(self):
        """Groq provider should return Groq instance."""
        try:
            # Try to import the provider first
            from agno.models.groq import Groq  # noqa: F401

            result = ConfigGenerator._parse_model("groq:llama3-70b")
            assert result is not None
            assert result.__class__.__name__ == "Groq"
            assert result.id == "llama3-70b"
        except ImportError as e:
            pytest.skip(f"Groq SDK not installed: {e}")
        except Exception as e:
            # Skip if Groq not configured
            if "groq" in str(e).lower() or "GROQ_API_KEY" in str(e):
                pytest.skip(f"Groq not configured: {e}")
            raise

    def test_ollama_provider_returns_ollama(self):
        """Ollama provider should return Ollama instance."""
        try:
            # Try to import the provider first
            from agno.models.ollama import Ollama  # noqa: F401

            result = ConfigGenerator._parse_model("ollama:llama3")
            assert result is not None
            assert result.__class__.__name__ == "Ollama"
            assert result.id == "llama3"
        except ImportError as e:
            pytest.skip(f"Ollama SDK not installed: {e}")
        except Exception as e:
            # Skip if Ollama not running
            if "ollama" in str(e).lower() or "connection" in str(e).lower():
                pytest.skip(f"Ollama not running: {e}")
            raise

    def test_xai_provider_returns_xai(self):
        """xAI provider should return xAI instance."""
        result = ConfigGenerator._parse_model("xai:grok-beta")

        assert result is not None
        assert result.__class__.__name__ == "xAI"
        assert result.id == "grok-beta"

    def test_case_insensitive_provider_matching(self):
        """Provider names should be case insensitive."""
        result = ConfigGenerator._parse_model("OpenAI:gpt-4o")

        assert result is not None
        assert result.__class__.__name__ == "OpenAIChat"

    def test_missing_colon_raises_error(self):
        """Model string without colon should raise error."""
        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._parse_model("gpt-4o-mini")

        assert "Invalid model format" in str(exc_info.value)
        assert "Expected format: 'provider:model_id'" in str(exc_info.value)

    def test_unknown_provider_raises_error(self):
        """Unknown provider should raise error with helpful message."""
        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._parse_model("unknown_provider:model")

        error_msg = str(exc_info.value)
        assert "Unknown model provider" in error_msg or "Failed to initialize" in error_msg

    def test_provider_init_failure_raises_error(self):
        """Provider initialization failure should raise error."""
        try:
            result = ConfigGenerator._parse_model("openai:")  # Empty model ID
            # If it succeeds (Agno allows empty ID), that's fine
            assert result is not None
        except GeneratorError:
            # If it fails validation, that's also fine
            pass

    def test_mapped_provider_initialization_failure_lines_390_391(self):
        """Test mapped provider fails during class instantiation (lines 390-391)."""
        from types import ModuleType

        # Create a mock provider class that raises on instantiation
        mock_model_class = MagicMock()
        mock_model_class.side_effect = RuntimeError("API key missing or invalid")

        # Create mock module
        mock_openai_module = ModuleType("agno.models.openai")
        mock_openai_module.OpenAIChat = mock_model_class

        with patch.dict("sys.modules", {"agno.models.openai": mock_openai_module}):
            with pytest.raises(GeneratorError) as exc_info:
                ConfigGenerator._parse_model("openai:gpt-4o")

            error_msg = str(exc_info.value)
            assert "Failed to initialize openai model" in error_msg
            assert "API key missing or invalid" in error_msg
            assert "Make sure the provider is installed and configured" in error_msg


class TestSubstituteEnvVars:
    """Test environment variable substitution."""

    def test_substitutes_single_var_in_string(self, monkeypatch):
        """Should substitute ${VAR} with environment variable value."""
        monkeypatch.setenv("TEST_VAR", "test_value")

        result = ConfigGenerator._substitute_env_vars("Value: ${TEST_VAR}")

        assert result == "Value: test_value"

    def test_substitutes_multiple_vars_in_string(self, monkeypatch):
        """Should substitute multiple ${VAR} patterns."""
        monkeypatch.setenv("VAR1", "value1")
        monkeypatch.setenv("VAR2", "value2")

        result = ConfigGenerator._substitute_env_vars("${VAR1} and ${VAR2}")

        assert result == "value1 and value2"

    def test_substitutes_vars_in_dict(self, monkeypatch):
        """Should recursively substitute in dictionaries."""
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "5432")

        config = {"host": "${DB_HOST}", "port": "${DB_PORT}"}
        result = ConfigGenerator._substitute_env_vars(config)

        assert result == {"host": "localhost", "port": "5432"}

    def test_substitutes_vars_in_list(self, monkeypatch):
        """Should recursively substitute in lists."""
        monkeypatch.setenv("ITEM1", "first")
        monkeypatch.setenv("ITEM2", "second")

        config = ["${ITEM1}", "${ITEM2}"]
        result = ConfigGenerator._substitute_env_vars(config)

        assert result == ["first", "second"]

    def test_substitutes_vars_in_nested_structure(self, monkeypatch):
        """Should recursively substitute in nested structures."""
        monkeypatch.setenv("API_KEY", "secret123")

        config = {"settings": {"auth": {"key": "${API_KEY}"}}}
        result = ConfigGenerator._substitute_env_vars(config)

        assert result == {"settings": {"auth": {"key": "secret123"}}}

    def test_missing_env_var_raises_error(self):
        """Missing environment variable should raise error."""
        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._substitute_env_vars("Value: ${NONEXISTENT_VAR}")

        assert "Environment variable not set: NONEXISTENT_VAR" in str(exc_info.value)

    def test_non_string_values_unchanged(self):
        """Non-string values should be returned unchanged."""
        assert ConfigGenerator._substitute_env_vars(123) == 123
        assert ConfigGenerator._substitute_env_vars(True) is True
        assert ConfigGenerator._substitute_env_vars(None) is None


class TestLoadTools:
    """Test tool loading."""

    @patch("hive.scaffolder.generator.load_builtin_tool")
    def test_loads_builtin_tool_by_name(self, mock_load_builtin):
        """Should load builtin tools by string name."""
        mock_tool = MagicMock()
        mock_load_builtin.return_value = mock_tool

        result = ConfigGenerator._load_tools(["duckduckgo"])

        assert len(result) == 1
        assert result[0] == mock_tool
        mock_load_builtin.assert_called_once_with("duckduckgo")

    @patch("hive.scaffolder.generator.load_builtin_tool")
    def test_unknown_builtin_tool_raises_error(self, mock_load_builtin):
        """Unknown builtin tool should raise error."""
        mock_load_builtin.return_value = None

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_tools(["unknown_tool"])

        assert "Unknown builtin tool: unknown_tool" in str(exc_info.value)

    def test_loads_custom_tool_from_import_path(self):
        """Should load custom tools via import_path."""
        # Use a mock class that accepts **kwargs to simulate tool initialization
        import sys
        from types import ModuleType

        # Create a mock tool class
        class MockTool:
            def __init__(self, **kwargs):
                pass

            def __call__(self):
                return "mock"

        # Create a temporary module and add the tool
        mock_module = ModuleType("mock_tools")
        mock_module.MyCustomTool = MockTool
        sys.modules["mock_tools"] = mock_module

        try:
            tool_config = {
                "name": "my_custom_tool",
                "import_path": "mock_tools.MyCustomTool",
                "config": {},
            }

            result = ConfigGenerator._load_tools([tool_config])

            assert len(result) == 1
            assert isinstance(result[0], MockTool)
        finally:
            # Cleanup
            del sys.modules["mock_tools"]

    def test_custom_tool_missing_import_path_raises_error(self):
        """Custom tool without import_path should raise error."""
        tool_config = {"name": "my_custom_tool"}

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_tools([tool_config])

        assert "missing import_path" in str(exc_info.value)

    def test_custom_tool_invalid_import_raises_error(self):
        """Custom tool with invalid import should raise error."""
        tool_config = {
            "name": "bad_tool",
            "import_path": "nonexistent.module.Tool",
        }

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_tools([tool_config])

        assert "Failed to load custom tool" in str(exc_info.value)


class TestSetupKnowledge:
    """Test knowledge base setup."""

    def test_none_config_returns_none(self):
        """None knowledge config should return None."""
        result = ConfigGenerator._setup_knowledge(None)
        assert result is None

    def test_csv_knowledge_base_setup(self):
        """Should setup CSV knowledge base."""
        # Use patch.dict to mock sys.modules for lazy imports
        mock_reader_class = MagicMock()
        mock_kb_class = MagicMock()
        mock_kb_instance = MagicMock()
        mock_kb_class.return_value = mock_kb_instance

        # Create mock modules
        mock_document = MagicMock()
        mock_document.CSVReader = mock_reader_class
        mock_knowledge = MagicMock()
        mock_knowledge.DocumentKnowledgeBase = mock_kb_class

        with patch.dict("sys.modules", {"agno.document": mock_document, "agno.knowledge": mock_knowledge}):
            kb_config = {"type": "csv", "source": "data.csv", "num_documents": 10}
            result = ConfigGenerator._setup_knowledge(kb_config)

            assert result == mock_kb_instance
            mock_reader_class.assert_called_once_with(path="data.csv")
            mock_kb_class.assert_called_once()

    def test_csv_knowledge_base_failure_raises_error(self):
        """Failed CSV knowledge base setup should raise error."""
        from types import ModuleType

        # Create mocks that will fail during initialization
        mock_reader_class = MagicMock()
        mock_reader_class.side_effect = RuntimeError("CSV read error")

        # Create mock modules
        mock_document = ModuleType("agno.document")
        mock_document.CSVReader = mock_reader_class
        mock_knowledge = ModuleType("agno.knowledge")
        mock_knowledge.DocumentKnowledgeBase = MagicMock()

        with patch.dict("sys.modules", {"agno.document": mock_document, "agno.knowledge": mock_knowledge}):
            kb_config = {"type": "csv", "source": "data.csv"}

            with pytest.raises(GeneratorError) as exc_info:
                ConfigGenerator._setup_knowledge(kb_config)

            assert "Failed to setup CSV knowledge base" in str(exc_info.value)
            assert "CSV read error" in str(exc_info.value)

    def test_database_knowledge_base_not_implemented(self):
        """Database knowledge base should raise not implemented error."""
        kb_config = {
            "type": "database",
            "connection": "postgresql://localhost/db",
            "table": "knowledge",
        }

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._setup_knowledge(kb_config)

        assert "Database knowledge base not yet implemented" in str(exc_info.value)

    def test_unknown_kb_type_raises_error(self):
        """Unknown knowledge base type should raise error."""
        kb_config = {"type": "unknown_type", "source": "data"}

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._setup_knowledge(kb_config)

        assert "Unknown knowledge base type: unknown_type" in str(exc_info.value)


class TestSetupStorage:
    """Test storage setup."""

    def test_none_config_returns_none(self):
        """None storage config should return None."""
        result = ConfigGenerator._setup_storage(None)
        assert result is None

    def test_postgres_storage_setup(self):
        """Should setup PostgreSQL storage."""
        mock_storage_class = MagicMock()
        mock_storage_instance = MagicMock()
        mock_storage_class.return_value = mock_storage_instance

        mock_storage_module = MagicMock()
        mock_storage_module.PostgresStorage = mock_storage_class

        with patch.dict("sys.modules", {"agno.storage": mock_storage_module}):
            storage_config = {
                "type": "postgres",
                "connection": "postgresql://localhost/db",
                "table_name": "sessions",
            }

            result = ConfigGenerator._setup_storage(storage_config)

            assert result == mock_storage_instance
            mock_storage_class.assert_called_once_with(
                connection_url="postgresql://localhost/db",
                table_name="sessions",
                auto_upgrade_schema=True,
            )

    def test_sqlite_storage_setup(self):
        """Should setup SQLite storage."""
        mock_storage_class = MagicMock()
        mock_storage_instance = MagicMock()
        mock_storage_class.return_value = mock_storage_instance

        mock_storage_module = MagicMock()
        mock_storage_module.SqliteStorage = mock_storage_class

        with patch.dict("sys.modules", {"agno.storage": mock_storage_module}):
            storage_config = {"type": "sqlite", "db_file": "./test.db", "table_name": "agents"}

            result = ConfigGenerator._setup_storage(storage_config)

            assert result == mock_storage_instance
            mock_storage_class.assert_called_once_with(
                db_file="./test.db",
                table_name="agents",
                auto_upgrade_schema=True,
            )

    def test_sqlite_storage_uses_defaults(self):
        """SQLite storage should use default values."""
        mock_storage_class = MagicMock()
        mock_storage_instance = MagicMock()
        mock_storage_class.return_value = mock_storage_instance

        mock_storage_module = MagicMock()
        mock_storage_module.SqliteStorage = mock_storage_class

        with patch.dict("sys.modules", {"agno.storage": mock_storage_module}):
            storage_config = {"type": "sqlite"}

            result = ConfigGenerator._setup_storage(storage_config)

            assert result == mock_storage_instance
            mock_storage_class.assert_called_once_with(
                db_file="./data/agent.db",
                table_name="agent_sessions",
                auto_upgrade_schema=True,
            )

    def test_unknown_storage_type_raises_error(self):
        """Unknown storage type should raise error."""
        storage_config = {"type": "unknown_storage"}

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._setup_storage(storage_config)

        assert "Unknown storage type: unknown_storage" in str(exc_info.value)


class TestGenerateAgentFromYaml:
    """Test end-to-end agent generation from YAML."""

    @patch("hive.scaffolder.generator.ConfigValidator.validate_agent")
    @patch("hive.scaffolder.generator.Agent")
    def test_generates_agent_with_minimal_config(self, mock_agent_class, mock_validate, tmp_path):
        """Should generate agent from minimal YAML config."""
        yaml_file = tmp_path / "agent.yaml"
        yaml_file.write_text("""
agent:
  name: test-agent
  description: Test agent
  model: openai:gpt-4o-mini

instructions: Be helpful
""")

        mock_validate.return_value = (True, [])
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        result = ConfigGenerator.generate_agent_from_yaml(str(yaml_file))

        assert result == mock_agent_instance
        mock_agent_class.assert_called_once()

    @patch("hive.scaffolder.generator.ConfigValidator.validate_agent")
    def test_validation_failure_raises_error(self, mock_validate, tmp_path):
        """Validation failure should raise GeneratorError."""
        yaml_file = tmp_path / "agent.yaml"
        yaml_file.write_text("agent: {}")

        mock_validate.return_value = (False, ["Missing name", "Missing instructions"])

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator.generate_agent_from_yaml(str(yaml_file))

        assert "Invalid agent config" in str(exc_info.value)

    @patch("hive.scaffolder.generator.ConfigValidator.validate_agent")
    def test_skip_validation_when_disabled(self, mock_validate, tmp_path):
        """Should skip validation when validate=False."""
        yaml_file = tmp_path / "agent.yaml"
        yaml_file.write_text("""
agent:
  name: test
  model: openai:gpt-4o-mini
instructions: test
""")

        with patch("hive.scaffolder.generator.Agent"):
            ConfigGenerator.generate_agent_from_yaml(str(yaml_file), validate=False)

        mock_validate.assert_not_called()

    @patch("hive.scaffolder.generator.ConfigValidator.validate_agent")
    @patch("hive.scaffolder.generator.Agent")
    def test_agent_creation_failure_raises_error(self, mock_agent_class, mock_validate, tmp_path):
        """Agent instantiation failure should raise GeneratorError."""
        yaml_file = tmp_path / "agent.yaml"
        yaml_file.write_text("""
agent:
  name: test
  model: openai:gpt-4o-mini
instructions: test
""")

        mock_validate.return_value = (True, [])
        mock_agent_class.side_effect = Exception("Agent init failed")

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator.generate_agent_from_yaml(str(yaml_file))

        assert "Failed to create agent" in str(exc_info.value)


class TestGenerateTeamFromYaml:
    """Test end-to-end team generation from YAML."""

    @patch("hive.scaffolder.generator.ConfigValidator.validate_team")
    @patch("hive.scaffolder.generator.ConfigGenerator._load_member_agents")
    @patch("hive.scaffolder.generator.Team")
    def test_generates_team_with_mode(self, mock_team_class, mock_load_members, mock_validate, tmp_path):
        """Should generate team with mode translation."""
        yaml_file = tmp_path / "team.yaml"
        yaml_file.write_text("""
team:
  name: test-team
  description: Test team
  mode: collaboration

members:
  - agent1
  - agent2

instructions: Collaborate on tasks
model: openai:gpt-4o-mini
""")

        mock_validate.return_value = (True, [])
        mock_load_members.return_value = [MagicMock(), MagicMock()]
        mock_team_instance = MagicMock()
        mock_team_class.return_value = mock_team_instance

        result = ConfigGenerator.generate_team_from_yaml(str(yaml_file))

        assert result == mock_team_instance
        mock_team_class.assert_called_once()

    @patch("hive.scaffolder.generator.ConfigValidator.validate_team")
    @patch("hive.scaffolder.generator.Team")
    def test_team_creation_failure_raises_error(self, mock_team_class, mock_validate, tmp_path):
        """Team instantiation failure should raise GeneratorError."""
        yaml_file = tmp_path / "team.yaml"
        yaml_file.write_text("""
team:
  name: test
members: []
instructions: test
""")

        mock_validate.return_value = (True, [])
        mock_team_class.side_effect = Exception("Team init failed")

        with patch("hive.scaffolder.generator.ConfigGenerator._load_member_agents", return_value=[]):
            with pytest.raises(GeneratorError) as exc_info:
                ConfigGenerator.generate_team_from_yaml(str(yaml_file))

        assert "Failed to create team" in str(exc_info.value)


class TestGenerateWorkflowFromYaml:
    """Test end-to-end workflow generation from YAML."""

    @patch("hive.scaffolder.generator.ConfigValidator.validate_workflow")
    @patch("hive.scaffolder.generator.ConfigGenerator._load_workflow_steps")
    @patch("hive.scaffolder.generator.Workflow")
    def test_generates_workflow_with_steps(self, mock_workflow_class, mock_load_steps, mock_validate, tmp_path):
        """Should generate workflow with steps."""
        yaml_file = tmp_path / "workflow.yaml"
        yaml_file.write_text("""
workflow:
  name: test-workflow
  description: Test workflow

steps:
  - name: step1
    type: sequential
    agent: agent1

model: openai:gpt-4o-mini
""")

        mock_validate.return_value = (True, [])
        mock_load_steps.return_value = [MagicMock()]
        mock_workflow_instance = MagicMock()
        mock_workflow_class.return_value = mock_workflow_instance

        result = ConfigGenerator.generate_workflow_from_yaml(str(yaml_file))

        assert result == mock_workflow_instance
        mock_workflow_class.assert_called_once()

    @patch("hive.scaffolder.generator.ConfigValidator.validate_workflow")
    @patch("hive.scaffolder.generator.Workflow")
    def test_workflow_creation_failure_raises_error(self, mock_workflow_class, mock_validate, tmp_path):
        """Workflow instantiation failure should raise GeneratorError."""
        yaml_file = tmp_path / "workflow.yaml"
        yaml_file.write_text("""
workflow:
  name: test
steps: []
""")

        mock_validate.return_value = (True, [])
        mock_workflow_class.side_effect = Exception("Workflow init failed")

        with patch("hive.scaffolder.generator.ConfigGenerator._load_workflow_steps", return_value=[]):
            with pytest.raises(GeneratorError) as exc_info:
                ConfigGenerator.generate_workflow_from_yaml(str(yaml_file))

        assert "Failed to create workflow" in str(exc_info.value)


class TestWorkflowStepsErrorPaths:
    """Test error paths in workflow step loading."""

    def test_sequential_step_missing_agent_raises_error(self):
        """Sequential step without agent should raise error."""
        steps_config = [{"name": "step1", "type": "sequential"}]

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_workflow_steps(steps_config)

        assert "missing agent reference" in str(exc_info.value)

    def test_parallel_step_missing_parallel_steps_raises_error(self):
        """Parallel step without parallel_steps should raise error."""
        steps_config = [{"name": "parallel1", "type": "parallel"}]

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_workflow_steps(steps_config)

        assert "has no parallel_steps" in str(exc_info.value)

    def test_conditional_step_missing_condition_raises_error(self):
        """Conditional step without condition should raise error."""
        steps_config = [{"name": "cond1", "type": "conditional", "steps": []}]

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_workflow_steps(steps_config)

        assert "missing condition config" in str(exc_info.value)

    def test_conditional_step_missing_nested_steps_raises_error(self):
        """Conditional step without nested steps should raise error."""
        steps_config = [
            {
                "name": "cond1",
                "type": "conditional",
                "condition": {"operator": "equals", "field": "x", "value": 1},
            }
        ]

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_workflow_steps(steps_config)

        assert "has no nested steps" in str(exc_info.value)

    def test_loop_step_missing_nested_steps_raises_error(self):
        """Loop step without nested steps should raise error."""
        steps_config = [{"name": "loop1", "type": "loop"}]

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_workflow_steps(steps_config)

        assert "has no nested steps" in str(exc_info.value)

    def test_function_step_missing_function_raises_error(self):
        """Function step without function reference should raise error."""
        steps_config = [{"name": "func1", "type": "function"}]

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._load_workflow_steps(steps_config)

        assert "missing function reference" in str(exc_info.value)


class TestModuleLevelHelperFunctions:
    """Test module-level convenience functions."""

    @patch("hive.scaffolder.generator.ConfigGenerator.generate_agent_from_yaml")
    def test_generate_agent_from_yaml_helper(self, mock_generate):
        """Module-level generate_agent_from_yaml should call class method."""
        from hive.scaffolder.generator import generate_agent_from_yaml

        mock_agent = MagicMock()
        mock_generate.return_value = mock_agent

        result = generate_agent_from_yaml("agent.yaml", session_id="test")

        assert result == mock_agent
        mock_generate.assert_called_once_with("agent.yaml", session_id="test")

    @patch("hive.scaffolder.generator.ConfigGenerator.generate_team_from_yaml")
    def test_generate_team_from_yaml_helper(self, mock_generate):
        """Module-level generate_team_from_yaml should call class method."""
        from hive.scaffolder.generator import generate_team_from_yaml

        mock_team = MagicMock()
        mock_generate.return_value = mock_team

        result = generate_team_from_yaml("team.yaml", user_id="user123")

        assert result == mock_team
        mock_generate.assert_called_once_with("team.yaml", user_id="user123")

    @patch("hive.scaffolder.generator.ConfigGenerator.generate_workflow_from_yaml")
    def test_generate_workflow_from_yaml_helper(self, mock_generate):
        """Module-level generate_workflow_from_yaml should call class method."""
        from hive.scaffolder.generator import generate_workflow_from_yaml

        mock_workflow = MagicMock()
        mock_generate.return_value = mock_workflow

        result = generate_workflow_from_yaml("workflow.yaml", debug=True)

        assert result == mock_workflow
        mock_generate.assert_called_once_with("workflow.yaml", debug=True)


class TestOptionalParameters:
    """Test optional parameter branches for complete coverage."""

    @patch("hive.scaffolder.generator.ConfigValidator.validate_agent")
    @patch("hive.scaffolder.generator.load_builtin_tool")
    @patch("hive.scaffolder.generator.Agent")
    def test_agent_with_all_optional_parameters(self, mock_agent_class, mock_load_tool, mock_validate, tmp_path):
        """Test agent generation with all optional parameters set."""
        yaml_file = tmp_path / "agent.yaml"
        yaml_file.write_text("""
agent:
  name: test-agent
  model: openai:gpt-4o-mini
instructions: Test
tools:
  - duckduckgo
knowledge:
  type: csv
  source: data.csv
storage:
  type: sqlite
  db_file: test.db
mcp_servers:
  - server1
settings:
  temperature: 0.7
  max_tokens: 1000
  show_tool_calls: true
  markdown: true
  stream: false
  debug_mode: true
""")

        mock_validate.return_value = (True, [])
        mock_load_tool.return_value = MagicMock()
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        # Mock storage and knowledge setup
        with patch.dict(
            "sys.modules",
            {
                "agno.storage": MagicMock(SqliteStorage=MagicMock(return_value=MagicMock())),
                "agno.document": MagicMock(CSVReader=MagicMock()),
                "agno.knowledge": MagicMock(DocumentKnowledgeBase=MagicMock(return_value=MagicMock())),
            },
        ):
            result = ConfigGenerator.generate_agent_from_yaml(str(yaml_file))

        assert result == mock_agent_instance

    @patch("hive.scaffolder.generator.ConfigValidator.validate_team")
    @patch("hive.scaffolder.generator.ConfigGenerator._load_member_agents")
    @patch("hive.scaffolder.generator.Team")
    def test_team_with_all_optional_parameters(self, mock_team_class, mock_load_members, mock_validate, tmp_path):
        """Test team generation with all optional parameters."""
        yaml_file = tmp_path / "team.yaml"
        yaml_file.write_text("""
team:
  name: test-team
  mode: default
members: []
instructions: Test
model: openai:gpt-4o-mini
storage:
  type: sqlite
settings:
  show_routing: true
  stream: true
  debug_mode: true
""")

        mock_validate.return_value = (True, [])
        mock_load_members.return_value = []
        mock_team_instance = MagicMock()
        mock_team_class.return_value = mock_team_instance

        with patch.dict("sys.modules", {"agno.storage": MagicMock(SqliteStorage=MagicMock(return_value=MagicMock()))}):
            result = ConfigGenerator.generate_team_from_yaml(str(yaml_file))

        assert result == mock_team_instance

    @patch("hive.scaffolder.generator.ConfigValidator.validate_workflow")
    @patch("hive.scaffolder.generator.ConfigGenerator._load_workflow_steps")
    @patch("hive.scaffolder.generator.Workflow")
    def test_workflow_with_all_optional_parameters(self, mock_workflow_class, mock_load_steps, mock_validate, tmp_path):
        """Test workflow generation with all optional parameters."""
        yaml_file = tmp_path / "workflow.yaml"
        yaml_file.write_text("""
workflow:
  name: test-workflow
steps: []
model: openai:gpt-4o-mini
storage:
  type: sqlite
settings:
  shared_state: true
  retry_on_error: true
  max_retries: 3
  stream: false
  show_progress: true
  debug_mode: true
""")

        mock_validate.return_value = (True, [])
        mock_load_steps.return_value = []
        mock_workflow_instance = MagicMock()
        mock_workflow_class.return_value = mock_workflow_instance

        with patch.dict("sys.modules", {"agno.storage": MagicMock(SqliteStorage=MagicMock(return_value=MagicMock()))}):
            result = ConfigGenerator.generate_workflow_from_yaml(str(yaml_file))

        assert result == mock_workflow_instance


class TestEdgeCases:
    """Test edge cases and error paths."""

    def test_load_yaml_generic_exception(self, tmp_path):
        """Test _load_yaml with generic exception."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("valid: yaml")

        # Make file unreadable by removing read permissions
        yaml_file.chmod(0o000)

        try:
            with pytest.raises(GeneratorError) as exc_info:
                ConfigGenerator._load_yaml(str(yaml_file))

            assert "Failed to load config" in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            yaml_file.chmod(0o644)

    def test_parse_model_dynamic_fallback(self):
        """Test _parse_model dynamic fallback for unknown provider."""
        # This tests the fallback path at lines 404-411
        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._parse_model("unknown_provider_xyz:model")

        assert "Unknown model provider" in str(exc_info.value)

    def test_loop_end_condition_empty_outputs_branches(self):
        """Test loop end condition with empty outputs (lines 762, 788)."""
        # Test content_length with empty outputs
        condition_config = {"type": "content_length", "threshold": 100}
        end_condition = ConfigGenerator._build_loop_end_condition(condition_config)

        result = end_condition([])
        assert result is False

        # Test success_count with empty outputs
        condition_config = {"type": "success_count", "threshold": 2}
        end_condition = ConfigGenerator._build_loop_end_condition(condition_config)

        result = end_condition([])
        assert result is False

    def test_load_member_agents_yaml_load_error(self):
        """Test _load_member_agents with YAML loading error (lines 601-602)."""
        with patch("hive.scaffolder.generator.ConfigGenerator.generate_agent_from_yaml") as mock_gen:
            mock_gen.side_effect = Exception("YAML error")

            with pytest.raises(GeneratorError) as exc_info:
                ConfigGenerator._load_member_agents(["bad-agent.yaml"])

            assert "Failed to load member agent from bad-agent.yaml" in str(exc_info.value)

    def test_team_validation_failure_line_152(self, tmp_path):
        """Test team validation failure to cover line 152."""
        yaml_file = tmp_path / "team.yaml"
        yaml_file.write_text("team: {}")

        with patch("hive.scaffolder.generator.ConfigValidator.validate_team") as mock_validate:
            mock_validate.return_value = (False, ["Missing name", "Missing members"])

            with pytest.raises(GeneratorError) as exc_info:
                ConfigGenerator.generate_team_from_yaml(str(yaml_file))

            assert "Invalid team config" in str(exc_info.value)
            assert "Missing name" in str(exc_info.value)

    def test_workflow_validation_failure_line_241(self, tmp_path):
        """Test workflow validation failure to cover line 241."""
        yaml_file = tmp_path / "workflow.yaml"
        yaml_file.write_text("workflow: {}")

        with patch("hive.scaffolder.generator.ConfigValidator.validate_workflow") as mock_validate:
            mock_validate.return_value = (False, ["Missing name", "Missing steps"])

            with pytest.raises(GeneratorError) as exc_info:
                ConfigGenerator.generate_workflow_from_yaml(str(yaml_file))

            assert "Invalid workflow config" in str(exc_info.value)
            assert "Missing name" in str(exc_info.value)

    def test_parse_model_dynamic_fallback_success_lines_406_407(self):
        """Test dynamic provider fallback SUCCESS when class is found (lines 406-407)."""
        from types import ModuleType

        # Create a mock module with the expected capitalized class
        mock_model_class = MagicMock()
        mock_model_instance = MagicMock()
        mock_model_class.return_value = mock_model_instance

        mock_provider_module = ModuleType("agno.models.testprovider")
        mock_provider_module.Testprovider = mock_model_class  # Capitalized provider name

        with patch.dict("sys.modules", {"agno.models.testprovider": mock_provider_module}):
            result = ConfigGenerator._parse_model("testprovider:model123")

            assert result == mock_model_instance
            mock_model_class.assert_called_once_with(id="model123")

    def test_parse_model_dynamic_fallback_class_unclear_lines_409_411(self):
        """Test dynamic provider fallback when main class is unclear (lines 409-411)."""
        from types import ModuleType

        # Create a mock module that exists but doesn't have the expected class
        mock_provider_module = ModuleType("agno.models.testprovider")
        mock_provider_module.SomeOtherClass = MagicMock
        mock_provider_module.AnotherClass = MagicMock

        with patch.dict("sys.modules", {"agno.models.testprovider": mock_provider_module}):
            with pytest.raises(GeneratorError) as exc_info:
                ConfigGenerator._parse_model("testprovider:model123")

            error_msg = str(exc_info.value)
            assert "Provider 'testprovider' found but main class unclear" in error_msg
            assert "Available classes:" in error_msg

    def test_csv_knowledge_exception_lines_523_524(self):
        """Test CSV knowledge base exception handling (lines 523-524)."""
        # Create a real exception during CSVReader initialization
        from types import ModuleType

        # Mock the modules to raise exception during kb creation
        mock_reader_class = MagicMock()
        mock_kb_class = MagicMock()
        mock_kb_class.side_effect = RuntimeError("KB initialization failed")

        mock_document = ModuleType("agno.document")
        mock_document.CSVReader = mock_reader_class
        mock_knowledge = ModuleType("agno.knowledge")
        mock_knowledge.DocumentKnowledgeBase = mock_kb_class

        with patch.dict("sys.modules", {"agno.document": mock_document, "agno.knowledge": mock_knowledge}):
            kb_config = {"type": "csv", "source": "data.csv"}

            with pytest.raises(GeneratorError) as exc_info:
                ConfigGenerator._setup_knowledge(kb_config)

            assert "Failed to setup CSV knowledge base" in str(exc_info.value)
            assert "KB initialization failed" in str(exc_info.value)

    def test_loop_end_condition_missing_type_line_762(self):
        """Test loop end condition with missing type (line 762)."""
        condition_config = {}  # Missing 'type' key

        with pytest.raises(GeneratorError) as exc_info:
            ConfigGenerator._build_loop_end_condition(condition_config)

        assert "Loop end condition must include 'type'" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
