"""AI-powered agent generation system.

Meta concept: Use Agno agents to generate Agno agent configurations.

The AgentGenerator orchestrates:
- ModelSelector: Choose optimal model
- ToolRecommender: Suggest appropriate tools
- PromptOptimizer: Generate system instructions
- YAML generation: Create valid Hive agent config
"""

import os
from dataclasses import dataclass
from typing import Optional

import yaml

from hive.generators.model_selector import ModelSelector, TaskComplexity
from hive.generators.prompt_optimizer import PromptOptimizer
from hive.generators.tool_recommender import ToolRecommender


@dataclass
class AgentConfig:
    """Complete agent configuration ready for scaffolding."""

    name: str
    agent_id: str
    description: str
    model_id: str
    provider: str
    instructions: str
    tools: list[dict]  # Tool configurations
    version: str
    metadata: dict


@dataclass
class GenerationResult:
    """Result of agent generation process."""

    config: AgentConfig
    yaml_content: str
    recommendations: dict  # Model, tools, prompt recommendations
    warnings: list[str]  # Configuration warnings
    next_steps: list[str]  # Suggested actions


class AgentGenerator:
    """AI-powered agent configuration generator.

    Usage:
        generator = AgentGenerator()
        result = generator.generate(
            name="support-bot",
            description="Customer support bot with knowledge base"
        )
        print(result.yaml_content)
    """

    def __init__(self):
        """Initialize generator with component services."""
        self.model_selector = ModelSelector()
        self.tool_recommender = ToolRecommender()
        self.prompt_optimizer = PromptOptimizer()

    def generate(
        self,
        name: str,
        description: str,
        complexity: Optional[TaskComplexity] = None,
        model_id: Optional[str] = None,
        tools: Optional[list[str]] = None,
        custom_instructions: Optional[str] = None,
        version: str = "1.0.0",
    ) -> GenerationResult:
        """Generate complete agent configuration.

        Args:
            name: Agent name (kebab-case)
            description: Natural language description of requirements
            complexity: Optional explicit complexity level
            model_id: Optional explicit model choice (overrides recommendation)
            tools: Optional explicit tool list (overrides recommendation)
            custom_instructions: Optional custom instructions (overrides generation)
            version: Initial version number

        Returns:
            GenerationResult with config and YAML content
        """
        warnings = []
        recommendations = {}

        # 1. Model selection
        if model_id:
            # Use explicit model
            model_info = self.model_selector.get_model_info(model_id)
            if not model_info:
                warnings.append(f"Unknown model '{model_id}', using recommendation")
                model_recommendation = self.model_selector.suggest_for_use_case(description)
            else:
                provider = model_info["provider"]
                model_recommendation = None
        else:
            # Get recommendation
            model_recommendation = self.model_selector.suggest_for_use_case(description)
            model_id = model_recommendation.model_id
            provider = model_recommendation.provider

        if model_recommendation:
            recommendations["model"] = {
                "selected": model_id,
                "reasoning": model_recommendation.reasoning,
                "alternatives": model_recommendation.alternatives,
            }

        # 2. Tool recommendation
        if tools:
            # Use explicit tools
            tool_configs = [{"name": tool_name, "class": f"agno.tools.{tool_name.lower()}"} for tool_name in tools]

            # Validate combination
            is_valid, conflicts = self.tool_recommender.validate_tool_combination(tools)
            if not is_valid:
                warnings.extend(conflicts)
        else:
            # Get recommendations
            tool_recommendations = self.tool_recommender.recommend(description, include_optional=True, max_tools=5)

            tool_configs = []
            for rec in tool_recommendations:
                tool_config = {"name": rec.tool_name, "class": rec.tool_class}
                if rec.config_hints:
                    tool_config["config_hints"] = rec.config_hints
                tool_configs.append(tool_config)

            recommendations["tools"] = {
                "selected": [rec.tool_name for rec in tool_recommendations],
                "reasoning": {rec.tool_name: rec.reasoning for rec in tool_recommendations},
                "required": [rec.tool_name for rec in tool_recommendations if rec.required],
            }

        # 3. Prompt optimization
        if custom_instructions:
            # Use custom instructions
            instructions = custom_instructions
            is_valid, issues = self.prompt_optimizer.validate(instructions)
            if not is_valid:
                warnings.extend([f"Instruction issue: {issue}" for issue in issues])
        else:
            # Generate optimized instructions
            optimized_prompt = self.prompt_optimizer.optimize(
                description=description, agent_name=name, include_edge_cases=True, include_examples=True
            )
            instructions = optimized_prompt.instructions

            recommendations["prompt"] = {
                "reasoning": optimized_prompt.reasoning,
                "components": optimized_prompt.key_components,
                "best_practices": optimized_prompt.best_practices_applied,
            }

        # 4. Build config
        agent_id = name.lower().replace(" ", "-")
        config = AgentConfig(
            name=name,
            agent_id=agent_id,
            description=description,
            model_id=model_id,
            provider=provider,
            instructions=instructions,
            tools=tool_configs,
            version=version,
            metadata={"generated_by": "AgentGenerator", "source": "ai_powered"},
        )

        # 5. Generate YAML
        yaml_content = self._generate_yaml(config)

        # 6. Validate YAML
        try:
            yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            warnings.append(f"YAML validation error: {e}")

        # 7. Build next steps
        next_steps = self._generate_next_steps(config, tool_configs)

        return GenerationResult(
            config=config, yaml_content=yaml_content, recommendations=recommendations, warnings=warnings, next_steps=next_steps
        )

    def _generate_yaml(self, config: AgentConfig) -> str:
        """Generate YAML configuration from AgentConfig."""
        # Build agent config dict
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
                "temperature": 0.7,  # Default
            },
            "instructions": config.instructions,
        }

        # Add tools if present
        if config.tools:
            agent_dict["tools"] = []
            for tool_config in config.tools:
                tool_entry = {"name": tool_config["name"]}
                if "config_hints" in tool_config:
                    tool_entry["config_hints"] = tool_config["config_hints"]
                agent_dict["tools"].append(tool_entry)

        # Add storage config
        agent_dict["storage"] = {"table_name": f"{config.agent_id}_sessions", "auto_upgrade_schema": True}

        # Add metadata
        agent_dict["metadata"] = config.metadata

        # Generate YAML with proper formatting
        yaml_content = yaml.dump(agent_dict, default_flow_style=False, sort_keys=False, allow_unicode=True)

        return yaml_content

    def _generate_next_steps(self, config: AgentConfig, tool_configs: list[dict]) -> list[str]:
        """Generate suggested next steps for user."""
        steps = []

        # Environment setup
        env_vars_needed = []
        for tool_config in tool_configs:
            if "config_hints" in tool_config:
                env_vars_needed.extend(tool_config["config_hints"].values())

        if env_vars_needed:
            steps.append(f"Set environment variables: {', '.join(env_vars_needed)}")

        # File creation
        steps.append(f"Save configuration to: ai/agents/{config.agent_id}/config.yaml")
        steps.append(f"Create agent factory: ai/agents/{config.agent_id}/agent.py")

        # Testing
        steps.append("Test agent with: hive dev (coming soon)")
        steps.append("Access agent at: http://localhost:8000/agents/{agent_id}")

        # Documentation
        steps.append(f"Document agent behavior in: ai/agents/{config.agent_id}/README.md")

        return steps

    def refine(
        self, current_yaml: str, feedback: str, aspect: str = "instructions"
    ) -> tuple[str, list[str]]:
        """Refine existing agent configuration based on feedback.

        Args:
            current_yaml: Current YAML configuration
            feedback: User feedback or improvement suggestions
            aspect: What to refine ("instructions", "tools", "model")

        Returns:
            (refined_yaml, warnings) tuple
        """
        warnings = []

        try:
            config_dict = yaml.safe_load(current_yaml)
        except yaml.YAMLError as e:
            warnings.append(f"Invalid YAML: {e}")
            return current_yaml, warnings

        # Refine based on aspect
        if aspect == "instructions":
            current_instructions = config_dict.get("instructions", "")
            optimized = self.prompt_optimizer.refine(current_instructions, feedback)
            config_dict["instructions"] = optimized.instructions

        elif aspect == "tools":
            # Re-recommend tools based on feedback
            combined_description = f"{config_dict.get('description', '')} {feedback}"
            tool_recommendations = self.tool_recommender.recommend(combined_description)
            config_dict["tools"] = [{"name": rec.tool_name} for rec in tool_recommendations]

        elif aspect == "model":
            # Re-recommend model based on feedback
            combined_description = f"{config_dict.get('description', '')} {feedback}"
            model_recommendation = self.model_selector.suggest_for_use_case(combined_description)
            config_dict["model"]["id"] = model_recommendation.model_id
            config_dict["model"]["provider"] = model_recommendation.provider

        # Regenerate YAML
        refined_yaml = yaml.dump(config_dict, default_flow_style=False, sort_keys=False, allow_unicode=True)

        return refined_yaml, warnings

    def validate(self, yaml_content: str) -> tuple[bool, list[str]]:
        """Validate agent configuration YAML.

        Args:
            yaml_content: YAML configuration to validate

        Returns:
            (is_valid, list_of_issues) tuple
        """
        issues = []

        # Check YAML syntax
        try:
            config = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            issues.append(f"YAML syntax error: {e}")
            return False, issues

        # Check required fields
        required_fields = ["agent", "model", "instructions"]
        for field in required_fields:
            if field not in config:
                issues.append(f"Missing required field: {field}")

        # Check agent fields
        if "agent" in config:
            agent_fields = ["name", "agent_id", "version"]
            for field in agent_fields:
                if field not in config["agent"]:
                    issues.append(f"Missing agent field: {field}")

        # Check model fields
        if "model" in config:
            model_fields = ["provider", "id"]
            for field in model_fields:
                if field not in config["model"]:
                    issues.append(f"Missing model field: {field}")

        # Validate instructions
        if "instructions" in config:
            is_valid, instruction_issues = self.prompt_optimizer.validate(config["instructions"])
            if not is_valid:
                issues.extend([f"Instruction issue: {issue}" for issue in instruction_issues])

        # Validate tools if present
        if "tools" in config and isinstance(config["tools"], list):
            tool_names = [tool.get("name") for tool in config["tools"] if isinstance(tool, dict)]
            is_valid, conflicts = self.tool_recommender.validate_tool_combination(tool_names)
            if not is_valid:
                issues.extend(conflicts)

        return len(issues) == 0, issues

    def generate_from_template(self, template_name: str, customizations: dict) -> GenerationResult:
        """Generate agent from predefined template with customizations.

        Args:
            template_name: Template name (e.g., "customer_support", "code_assistant")
            customizations: Dict of customization parameters

        Returns:
            GenerationResult with customized config
        """
        # Template definitions
        templates = {
            "customer_support": {
                "description": "Customer support agent with knowledge base",
                "complexity": TaskComplexity.SIMPLE,
                "required_tools": ["FileTools", "CSVTools"],
            },
            "code_assistant": {
                "description": "Code review and generation assistant",
                "complexity": TaskComplexity.COMPLEX,
                "required_tools": ["PythonTools", "FileTools"],
            },
            "data_analyst": {
                "description": "Data analysis and visualization agent",
                "complexity": TaskComplexity.BALANCED,
                "required_tools": ["PandasTools", "CSVTools", "FileTools"],
            },
            "research_assistant": {
                "description": "Research and information gathering agent",
                "complexity": TaskComplexity.BALANCED,
                "required_tools": ["DuckDuckGoTools", "WebpageTools"],
            },
        }

        if template_name not in templates:
            raise ValueError(f"Unknown template: {template_name}. Available: {list(templates.keys())}")

        template = templates[template_name]

        # Merge customizations
        name = customizations.get("name", template_name)
        description = customizations.get("description", template["description"])
        tools = customizations.get("tools", template["required_tools"])

        # Generate with template base
        return self.generate(
            name=name,
            description=description,
            complexity=template.get("complexity"),
            tools=tools,
        )

    def export_config_file(self, result: GenerationResult, output_path: str) -> None:
        """Export generated configuration to file.

        Args:
            result: GenerationResult from generate()
            output_path: Path to write YAML file
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.yaml_content)
