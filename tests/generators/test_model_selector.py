"""Tests for ModelSelector component."""

import sys
from pathlib import Path

import pytest

# Path setup for imports
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hive.generators.model_selector import (
    CostSensitivity,
    ContextLength,
    LatencyRequirement,
    ModelSelector,
    TaskComplexity,
)


class TestModelSelector:
    """Test suite for ModelSelector."""

    @pytest.fixture
    def selector(self) -> ModelSelector:
        """Create ModelSelector instance."""
        return ModelSelector()

    def test_selector_initialization(self, selector: ModelSelector) -> None:
        """Test ModelSelector initializes correctly."""
        assert selector is not None
        assert len(selector.MODELS) > 0

    def test_simple_task_selection(self, selector: ModelSelector) -> None:
        """Test model selection for simple tasks."""
        recommendation = selector.select(complexity=TaskComplexity.SIMPLE, cost=CostSensitivity.MINIMIZE)

        assert recommendation is not None
        assert "mini" in recommendation.model_id.lower() or "haiku" in recommendation.model_id.lower()
        assert recommendation.provider in ["openai", "anthropic"]
        assert len(recommendation.alternatives) > 0

    def test_complex_task_selection(self, selector: ModelSelector) -> None:
        """Test model selection for complex tasks."""
        recommendation = selector.select(complexity=TaskComplexity.COMPLEX, cost=CostSensitivity.MAXIMIZE_QUALITY)

        assert recommendation is not None
        assert "sonnet" in recommendation.model_id.lower() or "opus" in recommendation.model_id.lower()
        assert recommendation.context_window >= 128_000

    def test_realtime_latency_selection(self, selector: ModelSelector) -> None:
        """Test model selection with realtime latency requirements."""
        recommendation = selector.select(complexity=TaskComplexity.SIMPLE, latency=LatencyRequirement.REALTIME)

        assert recommendation is not None
        assert recommendation.latency_estimate == "<1s"

    def test_long_context_selection(self, selector: ModelSelector) -> None:
        """Test model selection with long context requirements."""
        recommendation = selector.select(context_length=ContextLength.VERY_LONG)

        assert recommendation is not None
        # Should prefer models with large context (128K+)
        assert recommendation.context_window >= 128_000

    def test_use_case_keyword_matching(self, selector: ModelSelector) -> None:
        """Test use case keyword matching influences selection."""
        # Code-related use case
        recommendation = selector.select(complexity=TaskComplexity.COMPLEX, use_case_keywords=["code", "analysis"])

        assert recommendation is not None
        # Should prefer Claude Sonnet for code
        assert "claude" in recommendation.model_id.lower() or "gpt" in recommendation.model_id.lower()

    def test_natural_language_suggestion(self, selector: ModelSelector) -> None:
        """Test natural language use case description."""
        recommendation = selector.suggest_for_use_case(
            "I need a simple customer support chatbot that responds quickly and is cost-effective"
        )

        assert recommendation is not None
        assert "mini" in recommendation.model_id.lower() or "haiku" in recommendation.model_id.lower()
        assert recommendation.latency_estimate == "<1s"

    def test_complex_research_use_case(self, selector: ModelSelector) -> None:
        """Test complex research use case detection."""
        recommendation = selector.suggest_for_use_case(
            "I need the best model for deep research and analysis of scientific papers"
        )

        assert recommendation is not None
        # Should select complex/premium model (sonnet, opus, or o1)
        assert any(
            keyword in recommendation.model_id.lower() for keyword in ["sonnet", "opus", "o1"]
        )

    def test_reasoning_generation(self, selector: ModelSelector) -> None:
        """Test reasoning text is generated."""
        recommendation = selector.select(complexity=TaskComplexity.BALANCED)

        assert recommendation is not None
        assert len(recommendation.reasoning) > 0
        assert "because" in recommendation.reasoning.lower()

    def test_alternatives_provided(self, selector: ModelSelector) -> None:
        """Test alternative models are provided."""
        recommendation = selector.select(complexity=TaskComplexity.BALANCED)

        assert recommendation is not None
        assert len(recommendation.alternatives) >= 1
        assert all(isinstance(alt, str) for alt in recommendation.alternatives)

    def test_model_info_retrieval(self, selector: ModelSelector) -> None:
        """Test retrieving model information."""
        info = selector.get_model_info("gpt-4o-mini")

        assert info is not None
        assert info["provider"] == "openai"
        assert "cost" in info
        assert "latency" in info
        assert "context" in info

    def test_list_models_by_provider(self, selector: ModelSelector) -> None:
        """Test listing models by provider."""
        openai_models = selector.list_models_by_provider("openai")
        anthropic_models = selector.list_models_by_provider("anthropic")

        assert len(openai_models) > 0
        assert len(anthropic_models) > 0
        assert all("gpt" in model or "o1" in model for model in openai_models)
        assert all("claude" in model for model in anthropic_models)

    def test_cost_sensitivity_minimize(self, selector: ModelSelector) -> None:
        """Test cost minimization preference."""
        recommendation = selector.select(complexity=TaskComplexity.BALANCED, cost=CostSensitivity.MINIMIZE)

        assert recommendation is not None
        # Should prefer cheaper models
        assert "mini" in recommendation.model_id.lower() or "4o" in recommendation.model_id

    def test_cost_sensitivity_maximize_quality(self, selector: ModelSelector) -> None:
        """Test quality maximization preference."""
        recommendation = selector.select(complexity=TaskComplexity.MAXIMUM, cost=CostSensitivity.MAXIMIZE_QUALITY)

        assert recommendation is not None
        # Should prefer premium models
        assert "opus" in recommendation.model_id.lower() or "o1" in recommendation.model_id

    def test_balanced_selection(self, selector: ModelSelector) -> None:
        """Test balanced cost/performance selection."""
        recommendation = selector.select(
            complexity=TaskComplexity.BALANCED,
            latency=LatencyRequirement.NORMAL,
            cost=CostSensitivity.BALANCED,
        )

        assert recommendation is not None
        # Should prefer mid-tier models
        assert "sonnet" in recommendation.model_id.lower() or "gpt-4o" in recommendation.model_id

    def test_all_complexity_levels(self, selector: ModelSelector) -> None:
        """Test all complexity levels produce valid recommendations."""
        for complexity in TaskComplexity:
            recommendation = selector.select(complexity=complexity)
            assert recommendation is not None
            assert recommendation.model_id in selector.MODELS

    def test_all_latency_levels(self, selector: ModelSelector) -> None:
        """Test all latency levels produce valid recommendations."""
        for latency in LatencyRequirement:
            recommendation = selector.select(latency=latency)
            assert recommendation is not None

    def test_all_cost_levels(self, selector: ModelSelector) -> None:
        """Test all cost sensitivity levels produce valid recommendations."""
        for cost in CostSensitivity:
            recommendation = selector.select(cost=cost)
            assert recommendation is not None

    def test_all_context_lengths(self, selector: ModelSelector) -> None:
        """Test all context length requirements produce valid recommendations."""
        for context_length in ContextLength:
            recommendation = selector.select(context_length=context_length)
            assert recommendation is not None
