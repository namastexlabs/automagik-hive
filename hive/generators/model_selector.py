"""Model selection logic based on use case analysis.

Selection criteria:
- Task complexity (simple, balanced, complex, maximum)
- Latency requirements (realtime, normal, batch)
- Cost sensitivity (minimize, balanced, maximize_quality)
- Context length needs (short, medium, long, very_long)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TaskComplexity(Enum):
    """Task complexity levels."""

    SIMPLE = "simple"  # FAQ, basic routing, simple responses
    BALANCED = "balanced"  # General purpose, moderate reasoning
    COMPLEX = "complex"  # Code analysis, long context, deep reasoning
    MAXIMUM = "maximum"  # Highest quality, most complex reasoning


class LatencyRequirement(Enum):
    """Latency sensitivity levels."""

    REALTIME = "realtime"  # <1s response critical (chat, support)
    NORMAL = "normal"  # <5s acceptable (most use cases)
    BATCH = "batch"  # Minutes acceptable (analysis, reports)


class CostSensitivity(Enum):
    """Cost optimization preferences."""

    MINIMIZE = "minimize"  # Use cheapest viable model
    BALANCED = "balanced"  # Balance cost and quality
    MAXIMIZE_QUALITY = "maximize_quality"  # Best model regardless of cost


class ContextLength(Enum):
    """Context length requirements."""

    SHORT = "short"  # <4K tokens
    MEDIUM = "medium"  # 4K-32K tokens
    LONG = "long"  # 32K-128K tokens
    VERY_LONG = "very_long"  # >128K tokens


@dataclass
class ModelRecommendation:
    """Model recommendation with reasoning."""

    model_id: str
    provider: str
    reasoning: str
    cost_estimate: str  # tokens/$1
    latency_estimate: str  # typical response time
    context_window: int  # max tokens
    alternatives: list[str]  # fallback options


class ModelSelector:
    """Intelligent model selection based on use case analysis.

    Usage:
        selector = ModelSelector()
        recommendation = selector.select(
            complexity=TaskComplexity.BALANCED,
            latency=LatencyRequirement.NORMAL,
            cost=CostSensitivity.BALANCED
        )
    """

    # Model catalog with capabilities and costs
    MODELS = {
        # OpenAI models
        "gpt-4o-mini": {
            "provider": "openai",
            "complexity": TaskComplexity.SIMPLE,
            "cost": "1M tokens/$0.15",
            "latency": "<1s",
            "context": 128_000,
            "best_for": ["chat", "support", "simple_qa", "routing"],
        },
        "gpt-4o": {
            "provider": "openai",
            "complexity": TaskComplexity.BALANCED,
            "cost": "1M tokens/$2.50",
            "latency": "1-2s",
            "context": 128_000,
            "best_for": ["general", "analysis", "moderate_code", "research"],
        },
        "gpt-4.1-mini": {
            "provider": "openai",
            "complexity": TaskComplexity.SIMPLE,
            "cost": "1M tokens/$0.10",
            "latency": "<1s",
            "context": 128_000,
            "best_for": ["high_volume", "cost_sensitive", "simple_tasks"],
        },
        "o1": {
            "provider": "openai",
            "complexity": TaskComplexity.MAXIMUM,
            "cost": "1M tokens/$15",
            "latency": "5-30s",
            "context": 200_000,
            "best_for": ["complex_reasoning", "math", "science", "planning"],
        },
        # Anthropic models
        "claude-sonnet-4-20250514": {
            "provider": "anthropic",
            "complexity": TaskComplexity.COMPLEX,
            "cost": "1M tokens/$3",
            "latency": "2-3s",
            "context": 200_000,
            "best_for": ["code", "analysis", "long_context", "writing"],
        },
        "claude-opus-4-20250514": {
            "provider": "anthropic",
            "complexity": TaskComplexity.MAXIMUM,
            "cost": "1M tokens/$15",
            "latency": "3-5s",
            "context": 200_000,
            "best_for": ["complex_code", "research", "creative_writing", "max_quality"],
        },
        "claude-haiku-4-20250311": {
            "provider": "anthropic",
            "complexity": TaskComplexity.SIMPLE,
            "cost": "1M tokens/$0.25",
            "latency": "<1s",
            "context": 200_000,
            "best_for": ["fast_chat", "realtime", "high_throughput"],
        },
    }

    def select(
        self,
        complexity: TaskComplexity = TaskComplexity.BALANCED,
        latency: LatencyRequirement = LatencyRequirement.NORMAL,
        cost: CostSensitivity = CostSensitivity.BALANCED,
        context_length: ContextLength = ContextLength.MEDIUM,
        use_case_keywords: Optional[list[str]] = None,
    ) -> ModelRecommendation:
        """Select optimal model based on requirements.

        Args:
            complexity: Task complexity level
            latency: Latency requirement
            cost: Cost sensitivity
            context_length: Context length needs
            use_case_keywords: Optional keywords for better matching

        Returns:
            ModelRecommendation with primary model and alternatives
        """
        use_case_keywords = use_case_keywords or []

        # Score each model based on criteria
        scored_models = []
        for model_id, specs in self.MODELS.items():
            score = self._score_model(model_id, specs, complexity, latency, cost, context_length, use_case_keywords)
            scored_models.append((score, model_id, specs))

        # Sort by score (highest first)
        scored_models.sort(reverse=True, key=lambda x: x[0])

        # Get top recommendation
        _, best_model_id, best_specs = scored_models[0]

        # Get alternatives (top 3, excluding best)
        alternatives = [model_id for _, model_id, _ in scored_models[1:4]]

        # Build reasoning
        reasoning = self._build_reasoning(
            best_model_id, best_specs, complexity, latency, cost, context_length, use_case_keywords
        )

        return ModelRecommendation(
            model_id=best_model_id,
            provider=best_specs["provider"],
            reasoning=reasoning,
            cost_estimate=best_specs["cost"],
            latency_estimate=best_specs["latency"],
            context_window=best_specs["context"],
            alternatives=alternatives,
        )

    def _score_model(
        self,
        model_id: str,
        specs: dict,
        complexity: TaskComplexity,
        latency: LatencyRequirement,
        cost: CostSensitivity,
        context_length: ContextLength,
        use_case_keywords: list[str],
    ) -> float:
        """Score a model based on requirements (0-100)."""
        score = 50.0  # Base score

        # Complexity match (most important: 30 points)
        if specs["complexity"] == complexity:
            score += 30
        elif abs(list(TaskComplexity).index(specs["complexity"]) - list(TaskComplexity).index(complexity)) == 1:
            score += 15  # Adjacent complexity level

        # Cost optimization (20 points)
        if cost == CostSensitivity.MINIMIZE:
            # Prefer cheaper models
            if "mini" in model_id or "haiku" in model_id:
                score += 20
            elif "4o" in model_id:
                score += 10
        elif cost == CostSensitivity.MAXIMIZE_QUALITY:
            # Prefer premium models
            if "opus" in model_id or "o1" in model_id:
                score += 20
            elif "sonnet" in model_id or "gpt-4o" in model_id:
                score += 10
        else:  # BALANCED
            # Prefer mid-tier models
            if "sonnet" in model_id or "gpt-4o" in model_id:
                score += 20
            elif "mini" in model_id or "haiku" in model_id:
                score += 5

        # Latency requirements (15 points)
        latency_match = {
            LatencyRequirement.REALTIME: ["<1s"],
            LatencyRequirement.NORMAL: ["<1s", "1-2s", "2-3s"],
            LatencyRequirement.BATCH: ["<1s", "1-2s", "2-3s", "3-5s", "5-30s"],
        }
        if specs["latency"] in latency_match[latency]:
            score += 15

        # Context length requirements (15 points)
        required_context = {
            ContextLength.SHORT: 8_000,
            ContextLength.MEDIUM: 32_000,
            ContextLength.LONG: 128_000,
            ContextLength.VERY_LONG: 200_000,
        }
        if specs["context"] >= required_context[context_length]:
            score += 15

        # Use case keyword matching (20 points)
        if use_case_keywords:
            matches = sum(1 for keyword in use_case_keywords if keyword in specs["best_for"])
            score += min(matches * 5, 20)

        return score

    def _build_reasoning(
        self,
        model_id: str,
        specs: dict,
        complexity: TaskComplexity,
        latency: LatencyRequirement,
        cost: CostSensitivity,
        context_length: ContextLength,
        use_case_keywords: list[str],
    ) -> str:
        """Build human-readable reasoning for model selection."""
        reasons = [f"Selected {model_id} ({specs['provider']}) because:"]

        # Complexity reasoning
        if specs["complexity"] == complexity:
            reasons.append(f"- Matches {complexity.value} task complexity perfectly")
        else:
            reasons.append(f"- Best available option for {complexity.value} tasks")

        # Cost reasoning
        if cost == CostSensitivity.MINIMIZE:
            reasons.append(f"- Cost-effective at {specs['cost']}")
        elif cost == CostSensitivity.MAXIMIZE_QUALITY:
            reasons.append(f"- Premium quality model ({specs['cost']})")
        else:
            reasons.append(f"- Balanced cost/performance ({specs['cost']})")

        # Latency reasoning
        if latency == LatencyRequirement.REALTIME and specs["latency"] == "<1s":
            reasons.append("- Sub-second latency for realtime requirements")
        elif latency == LatencyRequirement.NORMAL:
            reasons.append(f"- Fast response time ({specs['latency']})")

        # Context reasoning
        if context_length == ContextLength.VERY_LONG:
            reasons.append(f"- Supports very long context ({specs['context']:,} tokens)")
        elif specs["context"] >= 128_000:
            reasons.append(f"- Large context window ({specs['context']:,} tokens)")

        # Use case reasoning
        if use_case_keywords:
            matched = [kw for kw in use_case_keywords if kw in specs["best_for"]]
            if matched:
                reasons.append(f"- Optimized for: {', '.join(matched)}")

        return "\n".join(reasons)

    def get_model_info(self, model_id: str) -> Optional[dict]:
        """Get detailed information about a specific model."""
        return self.MODELS.get(model_id)

    def list_models_by_provider(self, provider: str) -> list[str]:
        """List all models for a given provider."""
        return [model_id for model_id, specs in self.MODELS.items() if specs["provider"] == provider]

    def suggest_for_use_case(self, description: str) -> ModelRecommendation:
        """Suggest model based on natural language use case description.

        Args:
            description: Natural language description of the use case

        Returns:
            ModelRecommendation based on detected patterns
        """
        description_lower = description.lower()

        # Detect complexity
        complexity = TaskComplexity.BALANCED
        if any(word in description_lower for word in ["simple", "faq", "basic", "chat", "support"]):
            complexity = TaskComplexity.SIMPLE
        elif any(word in description_lower for word in ["complex", "advanced", "deep", "research", "science"]):
            complexity = TaskComplexity.COMPLEX
        elif any(word in description_lower for word in ["maximum", "best", "highest", "premium"]):
            complexity = TaskComplexity.MAXIMUM

        # Detect latency requirements
        latency = LatencyRequirement.NORMAL
        if any(word in description_lower for word in ["realtime", "instant", "fast", "quick", "chat"]):
            latency = LatencyRequirement.REALTIME
        elif any(word in description_lower for word in ["batch", "report", "analysis", "overnight"]):
            latency = LatencyRequirement.BATCH

        # Detect cost sensitivity
        cost = CostSensitivity.BALANCED
        if any(word in description_lower for word in ["cheap", "cost", "affordable", "budget"]):
            cost = CostSensitivity.MINIMIZE
        elif any(word in description_lower for word in ["quality", "premium", "best"]):
            cost = CostSensitivity.MAXIMIZE_QUALITY

        # Detect context length needs
        context_length = ContextLength.MEDIUM
        if any(word in description_lower for word in ["long", "large", "document", "book"]):
            context_length = ContextLength.LONG
        elif any(word in description_lower for word in ["huge", "massive", "entire"]):
            context_length = ContextLength.VERY_LONG

        # Extract use case keywords
        keywords = []
        for model_id, specs in self.MODELS.items():
            for keyword in specs["best_for"]:
                if keyword.replace("_", " ") in description_lower:
                    keywords.append(keyword)

        return self.select(
            complexity=complexity,
            latency=latency,
            cost=cost,
            context_length=context_length,
            use_case_keywords=keywords,
        )
