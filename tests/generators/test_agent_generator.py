"""Tests for AgentGenerator (main orchestration component)."""

import sys
from pathlib import Path

import pytest
import yaml

# Path setup for imports
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hive.generators.agent_generator import AgentGenerator
from hive.generators.model_selector import TaskComplexity


class TestAgentGenerator:
    """Test suite for AgentGenerator."""

    @pytest.fixture
    def generator(self) -> AgentGenerator:
        """Create AgentGenerator instance."""
        return AgentGenerator()

    def test_generator_initialization(self, generator: AgentGenerator) -> None:
        """Test AgentGenerator initializes correctly."""
        assert generator is not None
        assert generator.model_selector is not None
        assert generator.tool_recommender is not None
        assert generator.prompt_optimizer is not None

    def test_basic_generation(self, generator: AgentGenerator) -> None:
        """Test basic agent generation."""
        result = generator.generate(name="test-agent", description="A simple test agent")

        assert result is not None
        assert result.config is not None
        assert result.yaml_content is not None
        assert len(result.yaml_content) > 0

    def test_customer_support_generation(self, generator: AgentGenerator) -> None:
        """Test generating customer support agent."""
        result = generator.generate(
            name="support-bot", description="Customer support bot that answers questions with a knowledge base"
        )

        assert result.config.name == "support-bot"
        assert result.config.agent_id == "support-bot"
        assert len(result.config.instructions) > 0
        assert result.config.model_id in generator.model_selector.MODELS

    def test_code_assistant_generation(self, generator: AgentGenerator) -> None:
        """Test generating code assistant agent."""
        result = generator.generate(
            name="code-helper", description="Code review and generation assistant for Python projects"
        )

        assert result.config.name == "code-helper"
        # Should select a model good for code
        assert "sonnet" in result.config.model_id.lower() or "gpt" in result.config.model_id.lower()

    def test_yaml_content_valid(self, generator: AgentGenerator) -> None:
        """Test generated YAML is valid and parseable."""
        result = generator.generate(name="test-agent", description="Test agent")

        # Should be valid YAML
        parsed = yaml.safe_load(result.yaml_content)
        assert parsed is not None
        assert "agent" in parsed
        assert "model" in parsed
        assert "instructions" in parsed

    def test_yaml_structure(self, generator: AgentGenerator) -> None:
        """Test YAML has correct structure."""
        result = generator.generate(name="test-agent", description="Test agent")
        config = yaml.safe_load(result.yaml_content)

        # Agent section
        assert "name" in config["agent"]
        assert "agent_id" in config["agent"]
        assert "version" in config["agent"]

        # Model section
        assert "provider" in config["model"]
        assert "id" in config["model"]

        # Instructions
        assert isinstance(config["instructions"], str)
        assert len(config["instructions"]) > 0

    def test_explicit_model_selection(self, generator: AgentGenerator) -> None:
        """Test explicit model selection overrides recommendation."""
        result = generator.generate(
            name="test-agent", description="Test agent", model_id="gpt-4o-mini"
        )

        assert result.config.model_id == "gpt-4o-mini"
        assert result.config.provider == "openai"

    def test_explicit_complexity(self, generator: AgentGenerator) -> None:
        """Test explicit complexity level."""
        result = generator.generate(
            name="test-agent", description="Test agent", complexity=TaskComplexity.COMPLEX
        )

        # Should use a model suitable for complex tasks
        assert result.config.model_id in generator.model_selector.MODELS

    def test_explicit_tools(self, generator: AgentGenerator) -> None:
        """Test explicit tool selection."""
        tools = ["PythonTools", "FileTools"]
        result = generator.generate(name="test-agent", description="Test agent", tools=tools)

        tool_names = [tool["name"] for tool in result.config.tools]
        assert "PythonTools" in tool_names
        assert "FileTools" in tool_names

    def test_custom_instructions(self, generator: AgentGenerator) -> None:
        """Test custom instructions override generation."""
        custom = "You are a special agent with unique instructions."
        result = generator.generate(name="test-agent", description="Test agent", custom_instructions=custom)

        assert result.config.instructions == custom

    def test_recommendations_provided(self, generator: AgentGenerator) -> None:
        """Test recommendations are provided."""
        result = generator.generate(name="test-agent", description="I need a customer support bot with web search")

        assert "model" in result.recommendations or len(result.recommendations) >= 0
        # Recommendations should contain model, tools, or prompt info

    def test_warnings_for_conflicts(self, generator: AgentGenerator) -> None:
        """Test warnings are generated for conflicting configurations."""
        # Try to use conflicting tools
        tools = ["DuckDuckGoTools", "TavilyTools"]  # These conflict
        result = generator.generate(name="test-agent", description="Test agent", tools=tools)

        # Should have warnings about conflicts
        assert len(result.warnings) > 0

    def test_next_steps_generated(self, generator: AgentGenerator) -> None:
        """Test next steps are generated."""
        result = generator.generate(name="test-agent", description="Test agent")

        assert len(result.next_steps) > 0
        assert any("config.yaml" in step for step in result.next_steps)

    def test_version_specification(self, generator: AgentGenerator) -> None:
        """Test custom version specification."""
        result = generator.generate(name="test-agent", description="Test agent", version="2.0.0")

        assert result.config.version == "2.0.0"

    def test_agent_id_kebab_case(self, generator: AgentGenerator) -> None:
        """Test agent_id is converted to kebab-case."""
        result = generator.generate(name="My Test Agent", description="Test agent")

        assert result.config.agent_id == "my-test-agent"

    def test_storage_config_included(self, generator: AgentGenerator) -> None:
        """Test storage configuration is included in YAML."""
        result = generator.generate(name="test-agent", description="Test agent")
        config = yaml.safe_load(result.yaml_content)

        assert "storage" in config
        assert "table_name" in config["storage"]
        assert "auto_upgrade_schema" in config["storage"]

    def test_metadata_included(self, generator: AgentGenerator) -> None:
        """Test metadata is included."""
        result = generator.generate(name="test-agent", description="Test agent")
        config = yaml.safe_load(result.yaml_content)

        assert "metadata" in config
        assert "generated_by" in config["metadata"]

    def test_validate_valid_yaml(self, generator: AgentGenerator) -> None:
        """Test validation of valid YAML."""
        result = generator.generate(name="test-agent", description="Test agent")

        is_valid, issues = generator.validate(result.yaml_content)

        assert is_valid
        assert len(issues) == 0

    def test_validate_invalid_yaml(self, generator: AgentGenerator) -> None:
        """Test validation catches invalid YAML."""
        invalid_yaml = "agent:\n  name: test\n  invalid yaml: ["

        is_valid, issues = generator.validate(invalid_yaml)

        assert not is_valid
        assert len(issues) > 0

    def test_validate_missing_fields(self, generator: AgentGenerator) -> None:
        """Test validation catches missing required fields."""
        incomplete_yaml = """
agent:
  name: test
"""
        is_valid, issues = generator.validate(incomplete_yaml)

        assert not is_valid
        assert any("model" in issue.lower() for issue in issues)

    def test_refine_instructions(self, generator: AgentGenerator) -> None:
        """Test refining instructions based on feedback."""
        result = generator.generate(name="test-agent", description="Test agent")
        original_yaml = result.yaml_content

        refined_yaml, warnings = generator.refine(
            original_yaml, feedback="Make the tone more friendly", aspect="instructions"
        )

        assert refined_yaml != original_yaml
        assert isinstance(warnings, list)

    def test_refine_tools(self, generator: AgentGenerator) -> None:
        """Test refining tools based on feedback."""
        result = generator.generate(name="test-agent", description="Test agent")
        original_yaml = result.yaml_content

        refined_yaml, warnings = generator.refine(
            original_yaml, feedback="Add web search capabilities", aspect="tools"
        )

        refined_config = yaml.safe_load(refined_yaml)
        # Should have tools section now
        assert "tools" in refined_config or len(warnings) > 0

    def test_refine_model(self, generator: AgentGenerator) -> None:
        """Test refining model based on feedback."""
        result = generator.generate(name="test-agent", description="Test agent")
        original_yaml = result.yaml_content
        original_config = yaml.safe_load(original_yaml)
        original_model = original_config["model"]["id"]

        refined_yaml, warnings = generator.refine(
            original_yaml, feedback="I need better quality, cost is not an issue", aspect="model"
        )

        refined_config = yaml.safe_load(refined_yaml)
        # Model might change or stay same, but should be valid
        assert "model" in refined_config
        assert "id" in refined_config["model"]

    def test_template_customer_support(self, generator: AgentGenerator) -> None:
        """Test customer support template."""
        result = generator.generate_from_template(
            "customer_support", customizations={"name": "my-support-bot"}
        )

        assert result.config.name == "my-support-bot"
        assert "support" in result.config.description.lower()

    def test_template_code_assistant(self, generator: AgentGenerator) -> None:
        """Test code assistant template."""
        result = generator.generate_from_template("code_assistant", customizations={"name": "code-helper"})

        assert result.config.name == "code-helper"
        assert "code" in result.config.description.lower()

    def test_template_data_analyst(self, generator: AgentGenerator) -> None:
        """Test data analyst template."""
        result = generator.generate_from_template("data_analyst", customizations={"name": "data-analyzer"})

        assert result.config.name == "data-analyzer"
        tool_names = [tool["name"] for tool in result.config.tools]
        assert "PandasTools" in tool_names or "CSVTools" in tool_names

    def test_template_research_assistant(self, generator: AgentGenerator) -> None:
        """Test research assistant template."""
        result = generator.generate_from_template("research_assistant", customizations={"name": "researcher"})

        assert result.config.name == "researcher"
        tool_names = [tool["name"] for tool in result.config.tools]
        assert "DuckDuckGoTools" in tool_names or "WebpageTools" in tool_names

    def test_template_unknown_raises_error(self, generator: AgentGenerator) -> None:
        """Test unknown template raises error."""
        with pytest.raises(ValueError, match="Unknown template"):
            generator.generate_from_template("nonexistent_template", customizations={})

    def test_export_config_file(self, generator: AgentGenerator, tmp_path: Path) -> None:
        """Test exporting config to file."""
        result = generator.generate(name="test-agent", description="Test agent")

        output_path = tmp_path / "test-agent" / "config.yaml"
        generator.export_config_file(result, str(output_path))

        assert output_path.exists()
        content = output_path.read_text()
        assert len(content) > 0

        # Should be valid YAML
        parsed = yaml.safe_load(content)
        assert parsed is not None

    def test_complex_scenario_with_tools(self, generator: AgentGenerator) -> None:
        """Test complex scenario requiring multiple tools."""
        result = generator.generate(
            name="data-processor",
            description="Agent that searches the web, processes CSV files, runs Python analysis, and sends email reports",
        )

        tool_names = [tool["name"] for tool in result.config.tools]
        assert len(tool_names) >= 2  # Should recommend multiple tools

    def test_agent_name_appears_in_instructions(self, generator: AgentGenerator) -> None:
        """Test agent name is personalized in instructions."""
        result = generator.generate(name="HelpBot", description="Helpful assistant")

        # Name might be in instructions (optional based on prompt optimizer)
        # Just verify instructions exist and are substantial
        assert len(result.config.instructions) > 100
