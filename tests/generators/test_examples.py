"""Example generation scenarios demonstrating the AI-powered agent generator.

These tests validate real-world usage patterns and serve as documentation.

NOTE: These are INTEGRATION tests that require OPENAI_API_KEY to be set.
They actually call the OpenAI API to generate agent configurations.
"""

import os
import sys
from pathlib import Path

import pytest

# Path setup for imports
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hive.generators.agent_generator import AgentGenerator

# Skip all tests in this file if OPENAI_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set - these are integration tests requiring real API calls",
)


class TestExampleScenarios:
    """Real-world example scenarios for agent generation."""

    @pytest.fixture
    def generator(self) -> AgentGenerator:
        """Create AgentGenerator instance."""
        return AgentGenerator()

    def test_example_customer_support_bot(self, generator: AgentGenerator) -> None:
        """Example: Customer support bot with knowledge base."""
        result = generator.generate(
            name="support-bot",
            description=(
                "I need a customer support bot that answers questions about our product "
                "using a CSV knowledge base. It should be friendly and helpful."
            ),
        )

        print("\n" + "=" * 80)
        print("EXAMPLE 1: Customer Support Bot")
        print("=" * 80)
        print("\nGenerated Configuration:")
        print(result.yaml_content)
        print("\n" + "-" * 80)
        print("Analysis:")
        for key, value in result.analysis.items():
            print(f"\n{key.upper()}:")
            if isinstance(value, dict):
                for k, v in value.items():
                    print(f"  {k}: {v}")
            elif isinstance(value, list):
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"  {value}")
        print("\n" + "-" * 80)
        print("Next Steps:")
        for i, step in enumerate(result.next_steps, 1):
            print(f"{i}. {step}")
        print("=" * 80 + "\n")

        # Validations
        assert result.config.name == "support-bot"
        assert "support" in result.config.description.lower() or "customer" in result.config.description.lower()
        assert len(result.config.instructions) > 100

    def test_example_code_assistant(self, generator: AgentGenerator) -> None:
        """Example: Code assistant for Python development."""
        result = generator.generate(
            name="code-helper",
            description=(
                "I need a code assistant that reviews Python code, suggests improvements, "
                "and can execute code to test solutions. It should follow best practices."
            ),
        )

        print("\n" + "=" * 80)
        print("EXAMPLE 2: Python Code Assistant")
        print("=" * 80)
        print("\nGenerated Configuration:")
        print(result.yaml_content)
        print("\n" + "-" * 80)
        print("Selected Model:", result.config.model_id)
        print("Provider:", result.config.provider)
        print("\nRecommended Tools:")
        for tool in result.config.tools:
            print(f"  - {tool}")
        print("=" * 80 + "\n")

        # Validations
        assert result.config.name == "code-helper"
        # Should select a capable model for code (AI decides)
        assert result.config.model_id
        assert len(result.config.model_id) > 0

    def test_example_data_analyst(self, generator: AgentGenerator) -> None:
        """Example: Data analyst with visualization capabilities."""
        result = generator.generate(
            name="data-analyzer",
            description=(
                "I need a data analyst that processes CSV files, performs statistical analysis, "
                "and provides insights. Should handle pandas dataframes."
            ),
        )

        print("\n" + "=" * 80)
        print("EXAMPLE 3: Data Analyst Agent")
        print("=" * 80)
        print("\nSelected Model:", result.config.model_id)
        print("\nTools Configuration:")
        for tool in result.config.tools:
            print(f"  - {tool}")
        print("\n" + "=" * 80 + "\n")

        # Validations
        assert result.config.name == "data-analyzer"
        # Should recommend data analysis tools
        assert any(tool in result.config.tools for tool in ["CSVTools", "PandasTools", "FileTools"])

    def test_example_research_assistant(self, generator: AgentGenerator) -> None:
        """Example: Research assistant with web search."""
        result = generator.generate(
            name="researcher",
            description=(
                "I need a research assistant that searches the web for information, "
                "analyzes sources, and provides comprehensive summaries with citations."
            ),
        )

        print("\n" + "=" * 80)
        print("EXAMPLE 4: Research Assistant")
        print("=" * 80)
        print("\nInstructions Preview:")
        print(result.config.instructions[:500] + "...")
        print("\nTools:")
        for tool in result.config.tools:
            print(f"  - {tool}")
        print("=" * 80 + "\n")

        # Validations
        assert result.config.name == "researcher"
        # Should recommend search or web-related tools (flexible check)
        assert any(
            keyword in tool.lower()
            for tool in result.config.tools
            for keyword in ["duckduckgo", "tavily", "webpage", "search", "web"]
        )

    @pytest.mark.skip(reason="generate_from_template() method not implemented yet")
    def test_example_template_usage(self, generator: AgentGenerator) -> None:
        """Example: Using predefined templates."""
        # TODO: Implement generate_from_template() in AgentGenerator
        result = generator.generate_from_template(  # type: ignore[attr-defined]
            "customer_support", customizations={"name": "my-support-bot", "description": "Support for SaaS platform"}
        )

        print("\n" + "=" * 80)
        print("EXAMPLE 5: Using Template (Customer Support)")
        print("=" * 80)
        print("\nYAML Output:")
        print(result.yaml_content)
        print("=" * 80 + "\n")

        # Validations
        assert result.config.name == "my-support-bot"
        assert result.config.version == "1.0.0"

    def test_example_explicit_configuration(self, generator: AgentGenerator) -> None:
        """Example: Explicit model and tool selection."""
        result = generator.generate(
            name="custom-agent",
            description="A custom agent with specific requirements",
            model_id="claude-sonnet-4-20250514",
            tools=["PythonTools", "FileTools"],
        )

        print("\n" + "=" * 80)
        print("EXAMPLE 6: Explicit Configuration")
        print("=" * 80)
        print("\nSelected Model:", result.config.model_id)
        print("Requested Tools:", ["PythonTools", "FileTools"])
        print("\nWarnings:", result.warnings if result.warnings else "None")
        print("=" * 80 + "\n")

        # Validations
        assert result.config.model_id == "claude-sonnet-4-20250514"
        assert "PythonTools" in result.config.tools
        assert "FileTools" in result.config.tools

    @pytest.mark.skip(reason="refine() method not implemented yet")
    def test_example_refinement_workflow(self, generator: AgentGenerator) -> None:
        """Example: Iterative refinement based on feedback."""
        # TODO: Implement refine() in AgentGenerator
        # Initial generation
        result = generator.generate(name="chat-bot", description="A basic chatbot")

        print("\n" + "=" * 80)
        print("EXAMPLE 7: Refinement Workflow")
        print("=" * 80)
        print("\nOriginal Instructions (preview):")
        print(result.config.instructions[:300] + "...")

        # Refine instructions
        refined_yaml, warnings = generator.refine(  # type: ignore[attr-defined]
            result.yaml_content,
            feedback="Make the tone more professional and add technical depth",
            aspect="instructions",
        )

        print("\n" + "-" * 80)
        print("After Refinement:")
        print("Warnings:", warnings if warnings else "None")
        print("\nRefined YAML (preview):")
        print(refined_yaml[:500] + "...")
        print("=" * 80 + "\n")

        # Validations
        assert refined_yaml != result.yaml_content
        assert isinstance(warnings, list)

    @pytest.mark.skip(reason="validate() method not implemented yet")
    def test_example_validation_workflow(self, generator: AgentGenerator) -> None:
        """Example: Validation of generated configuration."""
        # TODO: Implement validate() in AgentGenerator
        result = generator.generate(name="test-agent", description="Test agent for validation")

        print("\n" + "=" * 80)
        print("EXAMPLE 8: Validation Workflow")
        print("=" * 80)

        # Validate
        is_valid, issues = generator.validate(result.yaml_content)  # type: ignore[attr-defined]

        print(f"\nValidation Result: {'PASS' if is_valid else 'FAIL'}")
        if issues:
            print("Issues:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("No issues found - configuration is valid!")
        print("=" * 80 + "\n")

        # Validations
        assert is_valid
        assert len(issues) == 0

    def test_example_comparison_simple_vs_complex(self, generator: AgentGenerator) -> None:
        """Example: Comparing simple vs complex agent configurations."""
        # Simple agent
        simple = generator.generate(name="simple-bot", description="A simple FAQ bot for quick responses")

        # Complex agent
        complex_agent = generator.generate(
            name="complex-bot",
            description=(
                "An advanced research and analysis bot that performs deep investigation, "
                "cross-references multiple sources, and provides comprehensive reports"
            ),
        )

        print("\n" + "=" * 80)
        print("EXAMPLE 9: Simple vs Complex Comparison")
        print("=" * 80)
        print("\nSIMPLE AGENT:")
        print(f"  Model: {simple.config.model_id}")
        print(f"  Tools: {len(simple.config.tools)} tools")
        print(f"  Instructions Length: {len(simple.config.instructions)} chars")

        print("\nCOMPLEX AGENT:")
        print(f"  Model: {complex_agent.config.model_id}")
        print(f"  Tools: {len(complex_agent.config.tools)} tools")
        print(f"  Instructions Length: {len(complex_agent.config.instructions)} chars")

        print("\nMODEL COMPARISON:")
        print(f"  Simple uses: {simple.config.model_id}")
        print(f"  Complex uses: {complex_agent.config.model_id}")
        print("=" * 80 + "\n")

        # Validations
        # Simple should use cheaper/faster model
        assert "mini" in simple.config.model_id.lower() or "haiku" in simple.config.model_id.lower()

    @pytest.mark.skip(reason="validate() and export_config_file() methods not implemented yet")
    def test_example_complete_workflow(self, generator: AgentGenerator, tmp_path: Path) -> None:
        """Example: Complete end-to-end workflow."""
        # TODO: Implement validate() and export_config_file() in AgentGenerator
        print("\n" + "=" * 80)
        print("EXAMPLE 10: Complete Workflow")
        print("=" * 80)

        # Step 1: Generate
        print("\n[1/4] Generating agent configuration...")
        result = generator.generate(
            name="email-assistant",
            description=(
                "An email assistant that helps draft professional emails, "
                "maintains consistent tone, and follows email best practices"
            ),
        )
        print(f"✓ Generated {result.config.name}")

        # Step 2: Validate
        print("\n[2/4] Validating configuration...")
        is_valid, issues = generator.validate(result.yaml_content)  # type: ignore[attr-defined]
        print(f"✓ Validation: {'PASS' if is_valid else 'FAIL'}")
        assert is_valid

        # Step 3: Export
        print("\n[3/4] Exporting to file...")
        output_path = tmp_path / "email-assistant" / "config.yaml"
        generator.export_config_file(result, str(output_path))  # type: ignore[attr-defined]
        print(f"✓ Exported to: {output_path}")
        assert output_path.exists()

        # Step 4: Summary
        print("\n[4/4] Generation Summary:")
        print(f"  Name: {result.config.name}")
        print(f"  Model: {result.config.model_id}")
        print(f"  Tools: {len(result.config.tools)}")
        print(f"  Warnings: {len(result.warnings)}")
        print(f"  Next Steps: {len(result.next_steps)}")

        print("\n✓ Complete workflow finished successfully!")
        print("=" * 80 + "\n")

        # Validations
        assert result.config.name == "email-assistant"
        assert output_path.read_text() == result.yaml_content
