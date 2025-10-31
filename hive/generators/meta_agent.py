"""Meta-agent for generating agent configurations using REAL AI.

This is NOT keyword matching. This uses actual LLM intelligence to:
- Analyze natural language requirements
- Select optimal models based on true understanding
- Generate context-aware system instructions
- Recommend appropriate tools with reasoning
"""

from dataclasses import dataclass
from typing import Any

from agno.agent import Agent


class GenerationError(Exception):
    """Error during AI generation process."""

    pass


@dataclass
class MetaAnalysis:
    """Complete AI analysis of agent requirements."""

    model_recommendation: str
    model_reasoning: str
    tools_recommended: list[str]
    tools_reasoning: str
    instructions: str
    instructions_reasoning: str
    complexity_score: int  # 1-10
    warnings: list[str]


class MetaAgentGenerator:
    """REAL AI-powered agent generation using LLMs.

    This is the meta concept: Use Agno agents to generate Agno agent configurations.
    No keyword matching, no rule-based logic. Pure LLM intelligence.

    Usage:
        meta = MetaAgentGenerator()
        analysis = meta.analyze_requirements(
            "Create a customer support bot that can search the web and access our knowledge base"
        )
        print(analysis.model_recommendation)  # Real AI decision
        print(analysis.instructions)  # AI-generated prompt
    """

    def __init__(self, model_id: str = "gpt-4o"):
        """Initialize meta-agent with specified model.

        Args:
            model_id: LLM to use for generation (gpt-4o, gpt-4o-mini, claude-sonnet-4, etc.)
        """
        # Detect provider from model_id
        model: Any
        if model_id.startswith("gpt") or model_id.startswith("o1"):
            from agno.models.openai import OpenAIChat

            model = OpenAIChat(id=model_id)
        elif model_id.startswith("claude"):
            from agno.models.anthropic import Claude

            model = Claude(id=model_id)
        elif model_id.startswith("gemini"):
            from agno.models.google import Gemini

            model = Gemini(id=model_id)
        else:
            # Default to OpenAI
            from agno.models.openai import OpenAIChat

            model = OpenAIChat(id=model_id)

        # Create the meta-agent with REAL AI capabilities
        self.meta_agent = Agent(
            name="Meta-Agent Generator",
            model=model,
            description="AI that generates optimal agent configurations",
            instructions="""You are an expert AI system architect specializing in Agno framework.

Your role: Analyze requirements and generate optimal agent configurations.

ANALYSIS FRAMEWORK:
1. Model Selection:
   - gpt-4o-mini: Simple tasks, fast responses, cost-effective
   - gpt-4o: Balanced general-purpose work
   - gpt-4.1-mini: High-volume, cost-sensitive tasks
   - o1: Complex reasoning, math, science, planning
   - claude-sonnet-4: Code analysis, long context, writing
   - claude-opus-4: Maximum quality, complex tasks
   - claude-haiku-4: Realtime chat, high throughput

2. Tool Recommendation (Agno builtin tools):
   - DuckDuckGoTools: Web search (privacy-focused)
   - TavilyTools: AI-optimized search
   - PythonTools: Code execution
   - ShellTools: System automation
   - FileTools: File operations
   - CSVTools: Data processing
   - WebpageTools: Web scraping
   - PandasTools: Data analysis
   - PostgresTools: Database operations
   - SlackTools, EmailTools: Notifications
   - GitHubTools, JiraTools: Integrations

3. Instruction Generation:
   - Clear role definition
   - Specific goals and guidelines
   - Tone and style specification
   - Edge case handling
   - Example scenarios

RESPONSE FORMAT:
Provide structured analysis in this exact format:

MODEL: <model_id>
MODEL_REASONING: <why this model is optimal>

TOOLS: <comma-separated list>
TOOLS_REASONING: <why each tool is needed>

INSTRUCTIONS:
<complete system instructions for the agent>

COMPLEXITY: <1-10 score>
WARNINGS: <any concerns or requirements, or "none">

Be specific, practical, and optimization-focused.""",
            markdown=False,
        )
        # Set agent_id as attribute (not in constructor)
        self.meta_agent.id = "meta-agent-generator"  # type: ignore[attr-defined]

    def analyze_requirements(
        self, description: str, agent_name: str | None = None, constraints: dict | None = None
    ) -> MetaAnalysis:
        """Analyze requirements using REAL AI and generate configuration.

        Args:
            description: Natural language description of what the agent should do
            agent_name: Optional agent name for personalization
            constraints: Optional constraints (model_preference, max_tools, etc.)

        Returns:
            MetaAnalysis with AI-generated recommendations
        """
        constraints = constraints or {}

        # Build the analysis prompt
        prompt = f"""Analyze this agent requirement and provide optimal configuration:

REQUIREMENT:
{description}
"""

        if agent_name:
            prompt += f"\nAGENT NAME: {agent_name}"

        if constraints:
            prompt += f"\nCONSTRAINTS: {constraints}"

        prompt += "\n\nProvide your analysis in the specified format."

        # Get AI analysis (REAL LLM call, not keyword matching!)
        response = self.meta_agent.run(prompt)
        analysis_text = response.content

        if not isinstance(analysis_text, str):
            raise GenerationError("AI response content was not a string")

        # Parse the structured response
        return self._parse_analysis(analysis_text, description)

    def _parse_analysis(self, analysis_text: str, original_description: str) -> MetaAnalysis:
        """Parse AI response into structured MetaAnalysis."""
        lines = analysis_text.strip().split("\n")

        model_recommendation = ""
        model_reasoning = ""
        tools_recommended = []
        tools_reasoning = ""
        instructions = []
        complexity_score = 5
        warnings = []

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("MODEL:"):
                model_recommendation = line.replace("MODEL:", "").strip()
                current_section = None
            elif line.startswith("MODEL_REASONING:"):
                model_reasoning = line.replace("MODEL_REASONING:", "").strip()
                current_section = "model_reasoning"
            elif line.startswith("TOOLS:"):
                tools_str = line.replace("TOOLS:", "").strip()
                tools_recommended = [t.strip() for t in tools_str.split(",") if t.strip()]
                current_section = None
            elif line.startswith("TOOLS_REASONING:"):
                tools_reasoning = line.replace("TOOLS_REASONING:", "").strip()
                current_section = "tools_reasoning"
            elif line.startswith("INSTRUCTIONS:"):
                current_section = "instructions"
                continue
            elif line.startswith("COMPLEXITY:"):
                try:
                    complexity_score = int(line.replace("COMPLEXITY:", "").strip())
                except ValueError:
                    complexity_score = 5
                current_section = None
            elif line.startswith("WARNINGS:"):
                warnings_str = line.replace("WARNINGS:", "").strip()
                if warnings_str.lower() != "none":
                    warnings = [w.strip() for w in warnings_str.split(",")]
                current_section = "warnings"
            elif current_section == "model_reasoning" and line:
                model_reasoning += " " + line
            elif current_section == "tools_reasoning" and line:
                tools_reasoning += " " + line
            elif current_section == "instructions" and line:
                instructions.append(line)
            elif current_section == "warnings" and line:
                if line.lower() != "none":
                    warnings.append(line)

        # Clean up parsed data
        instructions_text = "\n".join(instructions).strip()
        if not instructions_text:
            # Fallback if parsing failed
            instructions_text = self._generate_fallback_instructions(original_description)
            warnings.append("Instructions parsing incomplete, using enhanced fallback")

        instructions_reasoning = f"AI-generated instructions based on: {original_description[:100]}..."

        return MetaAnalysis(
            model_recommendation=model_recommendation or "gpt-4o-mini",
            model_reasoning=model_reasoning or "Default selection",
            tools_recommended=tools_recommended,
            tools_reasoning=tools_reasoning or "Based on requirements",
            instructions=instructions_text,
            instructions_reasoning=instructions_reasoning,
            complexity_score=complexity_score,
            warnings=warnings,
        )

    def _generate_fallback_instructions(self, description: str) -> str:
        """Generate basic instructions if parsing fails."""
        return f"""You are a helpful AI agent.

Your purpose: {description}

Guidelines:
- Be helpful and accurate
- Provide clear, actionable responses
- Ask for clarification when needed
- Maintain a professional tone
- Use available tools effectively

Always strive to fulfill user requests while following best practices."""

    def refine_configuration(self, current_config: str, feedback: str) -> MetaAnalysis:
        """Refine existing configuration based on feedback using REAL AI.

        Args:
            current_config: Current agent configuration (YAML or description)
            feedback: User feedback or improvement suggestions

        Returns:
            MetaAnalysis with refined recommendations
        """
        prompt = f"""Refine this agent configuration based on feedback:

CURRENT CONFIGURATION:
{current_config}

FEEDBACK:
{feedback}

Analyze and provide improved configuration in the specified format."""

        response = self.meta_agent.run(prompt)
        analysis_text = response.content

        if not isinstance(analysis_text, str):
            raise GenerationError("AI response content was not a string")

        return self._parse_analysis(analysis_text, f"{current_config}\n\nFeedback: {feedback}")

    def compare_models(self, description: str, model_ids: list[str]) -> dict[str, str]:
        """Compare multiple models for a use case using REAL AI.

        Args:
            description: Use case description
            model_ids: List of model IDs to compare

        Returns:
            Dict mapping model_id to AI reasoning about fit
        """
        prompt = f"""Compare these models for this use case:

USE CASE: {description}

MODELS: {", ".join(model_ids)}

For each model, provide a brief assessment of its suitability.
Format: MODEL_ID: assessment"""

        response = self.meta_agent.run(prompt)
        content = response.content

        if not isinstance(content, str):
            raise GenerationError("AI response content was not a string")

        # Parse comparisons
        comparisons = {}
        for line in content.split("\n"):
            if ":" in line:
                parts = line.split(":", 1)
                model = parts[0].strip()
                if model in model_ids:
                    comparisons[model] = parts[1].strip()

        return comparisons


def quick_generate(description: str, model: str = "gpt-4o-mini") -> MetaAnalysis:
    """Quick API for generating agent configs with REAL AI.

    Args:
        description: What the agent should do
        model: Meta-agent model to use for generation

    Returns:
        MetaAnalysis with complete configuration

    Example:
        >>> analysis = quick_generate("Build a code review bot")
        >>> print(analysis.model_recommendation)
        claude-sonnet-4
        >>> print(analysis.tools_recommended)
        ['FileTools', 'GitHubTools', 'PythonTools']
    """
    meta = MetaAgentGenerator(model_id=model)
    return meta.analyze_requirements(description)
