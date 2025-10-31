"""AI-powered agent generation using real LLMs.

Uses MetaAgentGenerator to produce optimized agent configs from natural language.

Example:
    generator = AgentGenerator()
    result = generator.generate(
        name="support-bot",
        description="Customer support bot with FAQ knowledge base"
    )
    print(result.yaml_content)
"""

from dataclasses import dataclass

import yaml

from hive.generators.meta_agent import GenerationError, MetaAgentGenerator


@dataclass
class AgentConfig:
    """Complete agent configuration ready for scaffolding."""

    name: str
    agent_id: str
    description: str
    model_id: str
    provider: str
    instructions: str
    tools: list[str]  # Tool names
    version: str
    metadata: dict


@dataclass
class GenerationResult:
    """Result of agent generation process."""

    config: AgentConfig
    yaml_content: str
    analysis: dict  # Meta-agent's analysis
    warnings: list[str]
    next_steps: list[str]


class AgentGenerator:
    """Real AI-powered agent configuration generator.

    Uses MetaAgentGenerator (actual LLM) to analyze requirements and produce
    optimal agent configurations.

    Default model: gpt-4o-mini (fast, cheap, good quality)
    """

    def __init__(self, meta_model: str = "gpt-4o-mini"):
        """Initialize generator with meta-agent.

        Args:
            meta_model: Model for meta-agent (gpt-4o-mini, gpt-4o, claude-sonnet-4)
        """
        self.meta_agent = MetaAgentGenerator(model_id=meta_model)

    def generate(
        self,
        name: str,
        description: str,
        model_id: str | None = None,
        tools: list[str] | None = None,
        custom_instructions: str | None = None,
        version: str = "1.0.0",
    ) -> GenerationResult:
        """Generate complete agent configuration using AI.

        Args:
            name: Agent name (kebab-case)
            description: Natural language requirements
            model_id: Optional explicit model (overrides AI recommendation)
            tools: Optional explicit tools (overrides AI recommendation)
            custom_instructions: Optional custom instructions (overrides AI generation)
            version: Initial version

        Returns:
            GenerationResult with config and YAML

        Raises:
            GenerationError: If generation fails
        """
        warnings = []
        agent_id = name.lower().replace(" ", "-")

        try:
            # Use meta-agent to analyze and generate optimal config
            meta_analysis = self.meta_agent.analyze_requirements(description, agent_name=name)

            # Convert MetaAnalysis to dict format for compatibility
            analysis = {
                "model": meta_analysis.model_recommendation,
                "provider": self._infer_provider(meta_analysis.model_recommendation),
                "tools": meta_analysis.tools_recommended,
                "instructions": meta_analysis.instructions,
                "reasoning": meta_analysis.instructions_reasoning,
            }

            # Extract AI recommendations
            recommended_model: str = analysis.get("model", "gpt-4o-mini")  # type: ignore[assignment]
            recommended_provider: str = analysis.get("provider", "openai")  # type: ignore[assignment]
            recommended_tools: list[str] = analysis.get("tools", [])  # type: ignore[assignment]
            generated_instructions: str = analysis.get("instructions", "")  # type: ignore[assignment]

            # Apply overrides (user preferences take precedence)
            final_model = model_id or recommended_model
            final_provider = self._infer_provider(final_model) if model_id else recommended_provider
            final_tools = tools or recommended_tools
            final_instructions = custom_instructions or generated_instructions

            # Validate we have everything
            if not final_instructions:
                final_instructions = f"You are {name}. {description}"
                warnings.append("AI generation produced no instructions, using fallback")

        except GenerationError as e:
            # AI generation failed - use sensible defaults
            warnings.append(f"AI generation failed: {e}")
            warnings.append("Using fallback configuration with sensible defaults")

            final_model = model_id or "gpt-4o-mini"
            final_provider = self._infer_provider(final_model)
            final_tools = tools or []
            final_instructions = custom_instructions or f"You are {name}. {description}"

            analysis = {
                "model": final_model,
                "provider": final_provider,
                "tools": final_tools,
                "instructions": final_instructions,
                "reasoning": "Fallback due to generation failure",
            }

        except Exception as e:
            # Unexpected error - fail loudly
            raise GenerationError(f"Unexpected error during generation: {type(e).__name__}: {e}") from e

        # Build config
        config = AgentConfig(
            name=name,
            agent_id=agent_id,
            description=description,
            model_id=final_model,
            provider=final_provider,
            instructions=final_instructions,
            tools=final_tools,
            version=version,
            metadata={
                "generated_by": "AgentGenerator",
                "meta_agent_used": True,
                "generation_status": "success" if not warnings else "partial",
            },
        )

        # Generate YAML
        yaml_content = self._generate_yaml(config)

        # Validate YAML
        try:
            yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            warnings.append(f"YAML validation error: {e}")

        # Generate next steps
        next_steps = self._generate_next_steps(config)

        return GenerationResult(
            config=config,
            yaml_content=yaml_content,
            analysis=analysis,
            warnings=warnings,
            next_steps=next_steps,
        )

    def _generate_yaml(self, config: AgentConfig) -> str:
        """Generate YAML configuration from AgentConfig."""
        agent_dict = {
            "agent": {
                "name": config.name,
                "agent_id": config.agent_id,
                "version": config.version,
                "description": config.description,
            },
            "model": {
                "provider": config.provider,
                "id": config.model_id,
                "temperature": 0.7,
            },
            "instructions": config.instructions,
        }

        # Add tools if present
        if config.tools:
            agent_dict["tools"] = config.tools

        # Add storage
        agent_dict["storage"] = {
            "table_name": f"{config.agent_id}_sessions",
            "auto_upgrade_schema": True,
        }

        # Add metadata
        agent_dict["metadata"] = config.metadata

        return yaml.dump(
            agent_dict,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    def _generate_next_steps(self, config: AgentConfig) -> list[str]:
        """Generate suggested next steps."""
        steps = [
            f"Test your agent: `hive dev start` then visit /agents/{config.agent_id}",
            "Customize instructions in config.yaml to refine behavior",
        ]

        if config.tools:
            steps.append(f"Configure tool settings: {', '.join(config.tools)}")
        else:
            steps.append("Consider adding tools for enhanced capabilities")

        steps.append("Add knowledge base: Create data/kb.csv and configure in YAML")

        return steps

    def _infer_provider(self, model_id: str) -> str:
        """Infer provider from model ID.

        Simple pattern matching - if we don't recognize it, default to openai.
        """
        model_lower = model_id.lower()

        if any(p in model_lower for p in ["gpt", "o1", "o3"]):
            return "openai"
        elif any(p in model_lower for p in ["claude", "sonnet", "opus", "haiku"]):
            return "anthropic"
        elif any(p in model_lower for p in ["gemini", "palm", "bard"]):
            return "google"
        elif any(p in model_lower for p in ["llama", "meta"]):
            return "meta"
        elif "mistral" in model_lower or "mixtral" in model_lower:
            return "mistral"
        elif "command" in model_lower or "embed" in model_lower:
            return "cohere"
        elif "grok" in model_lower:
            return "xai"
        else:
            # Default to openai if unknown
            return "openai"
