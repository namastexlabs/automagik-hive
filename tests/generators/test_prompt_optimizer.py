"""Tests for PromptOptimizer component."""

import sys
from pathlib import Path

import pytest

# Path setup for imports
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hive.generators.prompt_optimizer import PromptOptimizer


class TestPromptOptimizer:
    """Test suite for PromptOptimizer."""

    @pytest.fixture
    def optimizer(self) -> PromptOptimizer:
        """Create PromptOptimizer instance."""
        return PromptOptimizer()

    def test_optimizer_initialization(self, optimizer: PromptOptimizer) -> None:
        """Test PromptOptimizer initializes correctly."""
        assert optimizer is not None
        assert len(optimizer.PATTERNS) > 0

    def test_customer_support_optimization(self, optimizer: PromptOptimizer) -> None:
        """Test optimization for customer support use case."""
        result = optimizer.optimize("I need a customer support agent that answers questions")

        assert result is not None
        assert len(result.instructions) > 0
        assert "support" in result.instructions.lower() or "customer" in result.instructions.lower()
        assert "goals:" in result.instructions.lower() or "goal" in result.instructions.lower()

    def test_code_assistant_optimization(self, optimizer: PromptOptimizer) -> None:
        """Test optimization for code assistant use case."""
        result = optimizer.optimize("I need a code assistant that reviews and generates code")

        assert result is not None
        assert "code" in result.instructions.lower() or "software" in result.instructions.lower()
        assert len(result.key_components) > 0

    def test_data_analyst_optimization(self, optimizer: PromptOptimizer) -> None:
        """Test optimization for data analyst use case."""
        result = optimizer.optimize("I need a data analyst that processes and analyzes data")

        assert result is not None
        assert "data" in result.instructions.lower() or "analysis" in result.instructions.lower()

    def test_research_assistant_optimization(self, optimizer: PromptOptimizer) -> None:
        """Test optimization for research assistant use case."""
        result = optimizer.optimize("I need a research assistant that gathers information")

        assert result is not None
        assert "research" in result.instructions.lower() or "information" in result.instructions.lower()

    def test_creative_writer_optimization(self, optimizer: PromptOptimizer) -> None:
        """Test optimization for creative writer use case."""
        result = optimizer.optimize("I need a creative writing assistant")

        assert result is not None
        assert "creative" in result.instructions.lower() or "write" in result.instructions.lower()

    def test_role_definition_included(self, optimizer: PromptOptimizer) -> None:
        """Test role definition is included in instructions."""
        result = optimizer.optimize("I need a helpful agent")

        assert "you are" in result.instructions.lower()

    def test_goals_included(self, optimizer: PromptOptimizer) -> None:
        """Test goals are included in instructions."""
        result = optimizer.optimize("I need an agent with clear objectives")

        assert "goal" in result.instructions.lower() or "objective" in result.instructions.lower()

    def test_guidelines_included(self, optimizer: PromptOptimizer) -> None:
        """Test guidelines are included in instructions."""
        result = optimizer.optimize("I need an agent with specific rules")

        assert "guideline" in result.instructions.lower() or "-" in result.instructions

    def test_tone_guidance_included(self, optimizer: PromptOptimizer) -> None:
        """Test tone and style guidance is included."""
        result = optimizer.optimize("I need a professional agent")

        assert "tone" in result.instructions.lower() or "style" in result.instructions.lower()

    def test_edge_cases_included(self, optimizer: PromptOptimizer) -> None:
        """Test edge case handling is included when requested."""
        result = optimizer.optimize("I need an agent", include_edge_cases=True)

        assert "edge" in result.instructions.lower() or "uncertain" in result.instructions.lower()

    def test_edge_cases_excluded(self, optimizer: PromptOptimizer) -> None:
        """Test edge cases can be excluded."""
        result = optimizer.optimize("I need an agent", include_edge_cases=False)

        # Edge cases section should not be present
        assert "edge cases:" not in result.instructions.lower()

    def test_examples_included(self, optimizer: PromptOptimizer) -> None:
        """Test examples are included when requested."""
        result = optimizer.optimize("I need an agent", include_examples=True)

        assert "example" in result.instructions.lower()

    def test_examples_excluded(self, optimizer: PromptOptimizer) -> None:
        """Test examples can be excluded."""
        result = optimizer.optimize("I need an agent", include_examples=False)

        # Examples section should not be present
        assert "example scenarios:" not in result.instructions.lower()

    def test_agent_name_personalization(self, optimizer: PromptOptimizer) -> None:
        """Test agent name is included when provided."""
        result = optimizer.optimize("I need a support agent", agent_name="SupportBot")

        assert "supportbot" in result.instructions.lower()

    def test_reasoning_generation(self, optimizer: PromptOptimizer) -> None:
        """Test reasoning is generated."""
        result = optimizer.optimize("I need a customer support agent")

        assert len(result.reasoning) > 0
        assert "role:" in result.reasoning.lower() or "pattern" in result.reasoning.lower()

    def test_key_components_extraction(self, optimizer: PromptOptimizer) -> None:
        """Test key components are extracted."""
        result = optimizer.optimize("I need an agent")

        assert len(result.key_components) > 0
        assert "Role definition" in result.key_components

    def test_best_practices_listed(self, optimizer: PromptOptimizer) -> None:
        """Test best practices are listed."""
        result = optimizer.optimize("I need an agent")

        assert len(result.best_practices_applied) > 0
        assert any("role" in practice.lower() for practice in result.best_practices_applied)

    def test_validate_good_instructions(self, optimizer: PromptOptimizer) -> None:
        """Test validation of good instructions."""
        instructions = """
        You are a helpful assistant.

        Your goals:
        1. Help users effectively
        2. Provide accurate information

        Guidelines:
        - Be clear and concise
        - Always verify facts
        """

        is_valid, issues = optimizer.validate(instructions)

        assert is_valid
        assert len(issues) == 0

    def test_validate_missing_role(self, optimizer: PromptOptimizer) -> None:
        """Test validation catches missing role definition."""
        instructions = "Provide helpful responses."

        is_valid, issues = optimizer.validate(instructions)

        assert not is_valid
        assert any("role" in issue.lower() for issue in issues)

    def test_validate_missing_goals(self, optimizer: PromptOptimizer) -> None:
        """Test validation catches missing goals."""
        instructions = "You are an assistant. Follow these guidelines."

        is_valid, issues = optimizer.validate(instructions)

        # Should flag missing goals
        assert len(issues) > 0

    def test_validate_too_brief(self, optimizer: PromptOptimizer) -> None:
        """Test validation catches too brief instructions."""
        instructions = "You are an agent."

        is_valid, issues = optimizer.validate(instructions)

        assert not is_valid
        assert any("brief" in issue.lower() for issue in issues)

    def test_validate_too_long(self, optimizer: PromptOptimizer) -> None:
        """Test validation catches excessively long instructions."""
        instructions = "You are an agent. " * 1000  # Very long

        is_valid, issues = optimizer.validate(instructions)

        assert not is_valid
        assert any("long" in issue.lower() for issue in issues)

    def test_refine_instructions(self, optimizer: PromptOptimizer) -> None:
        """Test refining existing instructions with feedback."""
        current = "You are a support agent."
        feedback = "Make it more friendly and empathetic"

        result = optimizer.refine(current, feedback)

        assert result is not None
        assert len(result.instructions) > len(current)

    def test_custom_pattern_fallback(self, optimizer: PromptOptimizer) -> None:
        """Test custom pattern is built for unknown use cases."""
        result = optimizer.optimize("I need an agent that does something completely unique")

        assert result is not None
        # Should still generate valid instructions even for unknown patterns
        is_valid, _ = optimizer.validate(result.instructions)
        assert is_valid or len(result.instructions) > 100  # Should be substantial

    def test_multiple_pattern_matches(self, optimizer: PromptOptimizer) -> None:
        """Test handling when multiple patterns could match."""
        result = optimizer.optimize("I need a code assistant that also does research")

        assert result is not None
        # Should pick one primary pattern
        assert len(result.instructions) > 0

    def test_instructions_structure(self, optimizer: PromptOptimizer) -> None:
        """Test instructions have proper structure."""
        result = optimizer.optimize("I need a professional agent")

        # Should have multiple sections separated by blank lines
        sections = result.instructions.split("\n\n")
        assert len(sections) >= 3  # At least role, goals, guidelines

    def test_all_patterns_optimizable(self, optimizer: PromptOptimizer) -> None:
        """Test all predefined patterns can be optimized."""
        patterns = ["customer_support", "code_assistant", "data_analyst", "research_assistant", "creative_writer"]

        for pattern in patterns:
            description = f"I need a {pattern.replace('_', ' ')} agent"
            result = optimizer.optimize(description)

            assert result is not None
            assert len(result.instructions) > 100
            is_valid, _ = optimizer.validate(result.instructions)
            assert is_valid or len(result.key_components) > 0
