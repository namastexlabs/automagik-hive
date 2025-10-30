"""Prompt optimization for agent generation.

Transforms natural language requirements into optimized system instructions
following Agno best practices and prompt engineering principles.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OptimizedPrompt:
    """Optimized system instructions with metadata."""

    instructions: str  # Final optimized instructions
    reasoning: str  # Why these instructions were chosen
    key_components: list[str]  # Main components of the prompt
    best_practices_applied: list[str]  # Prompt engineering techniques used


class PromptOptimizer:
    """Generate optimized system instructions for agents.

    Applies prompt engineering best practices:
    - Clear role definition
    - Specific guidelines
    - Output format specification
    - Edge case handling
    - Tone and style guidance
    """

    # Prompt engineering patterns
    PATTERNS = {
        "customer_support": {
            "role": "friendly and helpful customer support agent",
            "goals": [
                "Answer customer questions accurately",
                "Provide helpful, citation-backed responses",
                "Maintain a warm, professional tone",
                "Escalate to human when uncertain",
            ],
            "guidelines": [
                "Always cite sources from knowledge base",
                "Keep responses concise but complete",
                "Use a warm, professional tone",
                "Admit when you don't know something",
            ],
            "tone": "friendly, professional, empathetic",
        },
        "code_assistant": {
            "role": "expert software engineer and code reviewer",
            "goals": [
                "Write clean, maintainable code",
                "Follow best practices and design patterns",
                "Explain code changes clearly",
                "Identify potential issues",
            ],
            "guidelines": [
                "Provide complete, runnable code",
                "Include comments for complex logic",
                "Follow language-specific conventions",
                "Consider edge cases and error handling",
            ],
            "tone": "technical, precise, helpful",
        },
        "data_analyst": {
            "role": "experienced data analyst",
            "goals": [
                "Analyze data accurately",
                "Provide actionable insights",
                "Create clear visualizations",
                "Explain findings in plain language",
            ],
            "guidelines": [
                "Show your work (calculations, queries)",
                "Validate data quality first",
                "Use appropriate statistical methods",
                "Highlight key findings and trends",
            ],
            "tone": "analytical, clear, objective",
        },
        "research_assistant": {
            "role": "thorough research assistant",
            "goals": [
                "Gather comprehensive information",
                "Evaluate source credibility",
                "Synthesize findings clearly",
                "Provide proper citations",
            ],
            "guidelines": [
                "Search multiple sources",
                "Verify information accuracy",
                "Distinguish facts from opinions",
                "Cite all sources properly",
            ],
            "tone": "scholarly, thorough, objective",
        },
        "creative_writer": {
            "role": "creative writing assistant",
            "goals": [
                "Generate engaging content",
                "Match requested style and tone",
                "Maintain consistency",
                "Revise based on feedback",
            ],
            "guidelines": [
                "Follow genre conventions",
                "Show, don't tell",
                "Vary sentence structure",
                "Maintain character consistency",
            ],
            "tone": "creative, engaging, adaptable",
        },
    }

    def optimize(
        self,
        description: str,
        agent_name: Optional[str] = None,
        include_edge_cases: bool = True,
        include_examples: bool = True,
    ) -> OptimizedPrompt:
        """Generate optimized instructions from natural language description.

        Args:
            description: Natural language description of agent requirements
            agent_name: Optional agent name for personalization
            include_edge_cases: Include edge case handling guidance
            include_examples: Include example scenarios

        Returns:
            OptimizedPrompt with system instructions and metadata
        """
        # Detect pattern
        pattern_name = self._detect_pattern(description)
        pattern = self.PATTERNS.get(pattern_name, self._build_custom_pattern(description))

        # Build optimized instructions
        instructions = self._build_instructions(pattern, description, agent_name, include_edge_cases, include_examples)

        # Build reasoning
        reasoning = self._build_reasoning(pattern_name, pattern, description)

        # Extract key components
        key_components = self._extract_components(instructions)

        # List best practices applied
        best_practices = self._list_best_practices(include_edge_cases, include_examples)

        return OptimizedPrompt(
            instructions=instructions,
            reasoning=reasoning,
            key_components=key_components,
            best_practices_applied=best_practices,
        )

    def _detect_pattern(self, description: str) -> Optional[str]:
        """Detect which pattern best matches the description."""
        description_lower = description.lower()

        # Pattern detection keywords
        patterns_keywords = {
            "customer_support": ["support", "customer", "help", "ticket", "service"],
            "code_assistant": ["code", "programming", "software", "developer", "engineer"],
            "data_analyst": ["data", "analysis", "statistics", "metrics", "analytics"],
            "research_assistant": ["research", "investigate", "study", "gather", "sources"],
            "creative_writer": ["write", "story", "content", "blog", "creative"],
        }

        # Score each pattern
        scores = {}
        for pattern_name, keywords in patterns_keywords.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            scores[pattern_name] = score

        # Return best match if score > 0
        best_pattern = max(scores.items(), key=lambda x: x[1])
        return best_pattern[0] if best_pattern[1] > 0 else None

    def _build_custom_pattern(self, description: str) -> dict:
        """Build a custom pattern from description."""
        description_lower = description.lower()

        # Extract role from description
        role = "helpful assistant"
        if "agent" in description_lower:
            role = "intelligent agent"

        # Build basic pattern
        return {
            "role": role,
            "goals": [
                "Understand user requirements",
                "Provide accurate responses",
                "Be helpful and informative",
            ],
            "guidelines": [
                "Follow user instructions carefully",
                "Ask for clarification when needed",
                "Provide complete, accurate information",
            ],
            "tone": "professional, helpful",
        }

    def _build_instructions(
        self,
        pattern: dict,
        description: str,
        agent_name: Optional[str],
        include_edge_cases: bool,
        include_examples: bool,
    ) -> str:
        """Build the final instruction text."""
        sections = []

        # Role definition
        role_section = f"You are a {pattern['role']}."
        if agent_name:
            role_section += f"\n\nYour name is {agent_name}."
        sections.append(role_section)

        # Goals section
        if pattern["goals"]:
            goals_text = "Your goals:\n"
            goals_text += "\n".join(f"{i+1}. {goal}" for i, goal in enumerate(pattern["goals"]))
            sections.append(goals_text)

        # Guidelines section
        if pattern["guidelines"]:
            guidelines_text = "Guidelines:\n"
            guidelines_text += "\n".join(f"- {guideline}" for guideline in pattern["guidelines"])
            sections.append(guidelines_text)

        # Tone guidance
        tone_text = f"Tone and Style: {pattern['tone']}"
        sections.append(tone_text)

        # Edge cases (if requested)
        if include_edge_cases:
            edge_cases = self._generate_edge_cases(pattern, description)
            if edge_cases:
                sections.append("Edge Cases:\n" + "\n".join(f"- {case}" for case in edge_cases))

        # Examples (if requested)
        if include_examples:
            examples = self._generate_examples(pattern, description)
            if examples:
                sections.append("Example Scenarios:\n" + examples)

        # Join all sections
        return "\n\n".join(sections)

    def _generate_edge_cases(self, pattern: dict, description: str) -> list[str]:
        """Generate edge case handling guidelines."""
        edge_cases = []

        # Common edge cases
        edge_cases.append("If information is ambiguous, ask clarifying questions")
        edge_cases.append("If you're uncertain, acknowledge limitations honestly")

        # Pattern-specific edge cases
        if "customer_support" in str(pattern):
            edge_cases.extend(
                [
                    "For angry customers, remain calm and empathetic",
                    "For technical issues beyond your scope, escalate to human support",
                ]
            )
        elif "code_assistant" in str(pattern):
            edge_cases.extend(
                [
                    "For security-sensitive code, highlight potential vulnerabilities",
                    "For incomplete requirements, request clarification before coding",
                ]
            )
        elif "data_analyst" in str(pattern):
            edge_cases.extend(
                ["For missing data, document assumptions clearly", "For outliers, investigate before excluding"]
            )

        return edge_cases

    def _generate_examples(self, pattern: dict, description: str) -> str:
        """Generate example scenarios."""
        # For now, return a placeholder - in production, this would generate
        # contextual examples based on the pattern and description
        return """
Example 1:
User: [Example query]
You: [Example response following guidelines]

Example 2:
User: [Example query]
You: [Example response showing best practices]
        """.strip()

    def _build_reasoning(self, pattern_name: Optional[str], pattern: dict, description: str) -> str:
        """Build reasoning for instruction choices."""
        reasons = []

        if pattern_name:
            reasons.append(f"Detected '{pattern_name}' use case pattern")
        else:
            reasons.append("Built custom pattern from description")

        reasons.append(f"Role: {pattern['role']}")
        reasons.append(f"Tone: {pattern['tone']}")
        reasons.append(f"Goals: {len(pattern['goals'])} objectives defined")
        reasons.append(f"Guidelines: {len(pattern['guidelines'])} specific guidelines")

        return "\n".join(reasons)

    def _extract_components(self, instructions: str) -> list[str]:
        """Extract key components from instructions."""
        components = []

        if "You are" in instructions:
            components.append("Role definition")
        if "goals:" in instructions.lower():
            components.append("Goal specification")
        if "guidelines:" in instructions.lower():
            components.append("Operational guidelines")
        if "tone" in instructions.lower():
            components.append("Tone and style guidance")
        if "edge cases:" in instructions.lower():
            components.append("Edge case handling")
        if "example" in instructions.lower():
            components.append("Example scenarios")

        return components

    def _list_best_practices(self, include_edge_cases: bool, include_examples: bool) -> list[str]:
        """List prompt engineering best practices applied."""
        practices = [
            "Clear role definition",
            "Specific goals and objectives",
            "Operational guidelines",
            "Tone and style specification",
        ]

        if include_edge_cases:
            practices.append("Edge case handling")
        if include_examples:
            practices.append("Example scenarios")

        return practices

    def refine(self, current_instructions: str, feedback: str) -> OptimizedPrompt:
        """Refine existing instructions based on feedback.

        Args:
            current_instructions: Current instruction text
            feedback: User feedback or improvement suggestions

        Returns:
            OptimizedPrompt with refined instructions
        """
        # For now, just re-optimize with feedback context
        # In production, this would use an LLM to intelligently refine
        combined_description = f"{current_instructions}\n\nFeedback: {feedback}"
        return self.optimize(combined_description)

    def validate(self, instructions: str) -> tuple[bool, list[str]]:
        """Validate instruction quality.

        Args:
            instructions: Instruction text to validate

        Returns:
            (is_valid, list_of_issues) tuple
        """
        issues = []

        # Check for role definition
        if "you are" not in instructions.lower():
            issues.append("Missing role definition")

        # Check for goals or objectives
        if "goal" not in instructions.lower() and "objective" not in instructions.lower():
            issues.append("No clear goals or objectives specified")

        # Check for guidelines
        if "guideline" not in instructions.lower() and "-" not in instructions:
            issues.append("No operational guidelines provided")

        # Check length (should be substantial but not too long)
        if len(instructions) < 100:
            issues.append("Instructions too brief (may lack detail)")
        elif len(instructions) > 5000:
            issues.append("Instructions too long (may overwhelm agent)")

        return len(issues) == 0, issues
