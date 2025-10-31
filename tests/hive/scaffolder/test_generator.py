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
        mock_agent.agent_id = "test-agent"
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
        mock_agent.agent_id = "existing-agent"
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
        yaml_agent.agent_id = "yaml-agent"

        registry_agent = MagicMock()
        registry_agent.agent_id = "registry-agent"

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
        available_agent.agent_id = "available-agent"

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
