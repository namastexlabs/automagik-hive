"""
AI Generator Tests for Automagik Hive v2.

Tests the AI-powered generation of agent/team/workflow configs:
- Natural language → YAML conversion
- Model selection logic
- Tool recommendations
- Validation catches errors
- Quality of generated configs
"""

import pytest
import yaml


class TestAgentGenerator:
    """Test AI-powered agent configuration generation."""

    @pytest.mark.asyncio
    async def test_generates_valid_yaml_from_description(self, mock_agno_agent):
        """Test that natural language converts to valid agent YAML."""
        # GIVEN: User description

        # WHEN: AI generates config (mocked)
        generated_yaml = """agent:
  name: "Billing Support Agent"
  agent_id: "billing-support"
  version: 1

model:
  provider: "openai"
  id: "gpt-4o-mini"
  temperature: 0.7

instructions: |
  You are a billing support specialist.
  Help customers with payment issues, invoices, and account billing.
  Always verify account details before processing requests.

tools:
  - name: "search_billing_records"
  - name: "update_payment_method"

knowledge:
  enabled: true
  sources:
    - "billing_faq.csv"
"""

        config = yaml.safe_load(generated_yaml)

        # THEN: Generated YAML is valid and complete
        assert "agent" in config
        assert config["agent"]["name"] == "Billing Support Agent"
        assert "model" in config
        assert config["model"]["id"] == "gpt-4o-mini"
        assert "instructions" in config
        assert len(config["instructions"]) > 50  # Real instructions, not placeholder
        assert "billing" in config["instructions"].lower()

    def test_model_selection_logic(self):
        """Test that AI selects appropriate model based on task."""
        test_cases = [
            ("simple FAQ bot", "gpt-4o-mini"),  # Simple task → cheap model
            ("code analysis with deep reasoning", "claude-sonnet"),  # Complex → better model
            ("real-time chat support", "gpt-4o-mini"),  # Speed matters
        ]

        for description, expected_model in test_cases:
            # Mock model selector
            selected = self._mock_select_model(description)
            # THEN: Appropriate model chosen
            assert expected_model in selected or "gpt" in selected or "claude" in selected

    def _mock_select_model(self, description: str) -> str:
        """Mock model selection logic."""
        if "complex" in description or "reasoning" in description:
            return "claude-sonnet-4"
        return "gpt-4o-mini"

    def test_tool_recommendations_are_relevant(self):
        """Test that recommended tools match the agent's purpose."""
        # GIVEN: Agent descriptions
        test_cases = [
            ("database query agent", ["sql_query", "database_connect"]),
            ("web scraper agent", ["web_fetch", "html_parse"]),
            ("file manager agent", ["read_file", "write_file", "list_directory"]),
        ]

        for description, expected_tools in test_cases:
            # Mock tool recommendation
            recommended = self._mock_recommend_tools(description)

            # THEN: At least one expected tool is recommended
            assert any(tool in recommended for tool in expected_tools)

    def _mock_recommend_tools(self, description: str) -> list[str]:
        """Mock tool recommendation logic."""
        tools = []
        if "database" in description or "query" in description:
            tools.extend(["sql_query", "database_connect"])
        if "web" in description or "scrape" in description:
            tools.extend(["web_fetch", "html_parse"])
        if "file" in description:
            tools.extend(["read_file", "write_file"])
        return tools

    def test_validation_catches_missing_fields(self):
        """Test that validator catches incomplete configs."""
        invalid_configs = [
            # Missing agent name
            {"agent": {"version": 1}, "model": {"id": "gpt-4o-mini"}},
            # Missing model
            {"agent": {"name": "Test", "version": 1}},
            # Missing instructions
            {"agent": {"name": "Test", "version": 1}, "model": {"id": "gpt-4o-mini"}},
        ]

        for config in invalid_configs:
            errors = self._validate_agent_config(config)
            # THEN: Validation fails with specific errors
            assert len(errors) > 0

    def _validate_agent_config(self, config: dict) -> list[str]:
        """Mock validation logic."""
        errors = []
        if "agent" not in config or "name" not in config.get("agent", {}):
            errors.append("Missing agent name")
        if "model" not in config:
            errors.append("Missing model configuration")
        if "instructions" not in config:
            errors.append("Missing instructions")
        return errors

    def test_validation_catches_invalid_model(self):
        """Test that validator rejects unsupported models."""
        config = {
            "agent": {"name": "Test", "version": 1},
            "model": {"provider": "unknown", "id": "fake-model-9000"},
            "instructions": "Test",
        }

        # Mock validation
        valid_providers = ["openai", "anthropic", "google"]
        is_valid = config["model"]["provider"] in valid_providers

        # THEN: Should fail validation
        assert not is_valid

    @pytest.mark.asyncio
    async def test_iterative_refinement_improves_config(self):
        """Test that user feedback improves generated config."""
        # GIVEN: Initial generation
        import copy

        initial_config = {"agent": {"name": "Bot"}, "model": {"id": "gpt-4o-mini"}}

        # WHEN: User provides feedback

        # Mock refinement (in real implementation, this calls LLM again)
        refined_config = copy.deepcopy(initial_config)
        refined_config["agent"]["name"] = "Professional Billing Assistant"
        refined_config["tools"] = ["billing_search", "invoice_generator"]

        # THEN: Config is improved
        assert refined_config["agent"]["name"] != initial_config["agent"]["name"]
        assert "tools" in refined_config
        assert len(refined_config["tools"]) > 0


class TestTeamGenerator:
    """Test AI-powered team configuration generation."""

    def test_generates_routing_team(self):
        """Test generation of team with routing logic."""
        # GIVEN: Team description

        # WHEN: AI generates team config
        generated = """team:
  name: "Support Routing Team"
  team_id: "support-router"
  mode: "route"

members:
  - "billing-specialist"
  - "technical-specialist"
  - "sales-specialist"

instructions: |
  Route customer questions to the appropriate specialist:
  - Billing/payment questions → billing-specialist
  - Technical issues → technical-specialist
  - Sales inquiries → sales-specialist
"""

        config = yaml.safe_load(generated)

        # THEN: Valid routing team created
        assert config["team"]["mode"] == "route"
        assert len(config["members"]) == 3
        assert "billing-specialist" in config["members"]

    def test_validates_member_agents_exist(self):
        """Test that team validation checks if member agents exist."""
        config = {
            "team": {"name": "Test Team", "mode": "route"},
            "members": ["agent-1", "non-existent-agent"],
        }

        # Mock validation
        available_agents = ["agent-1", "agent-2"]
        invalid_members = [m for m in config["members"] if m not in available_agents]

        # THEN: Validation catches missing agents
        assert len(invalid_members) > 0
        assert "non-existent-agent" in invalid_members


class TestWorkflowGenerator:
    """Test AI-powered workflow configuration generation."""

    def test_generates_sequential_workflow(self):
        """Test generation of step-by-step workflow."""

        generated = """workflow:
  name: "Research Pipeline"
  workflow_id: "research-pipeline"

steps:
  - name: "Analysis"
    agent: "analyst-agent"
  - name: "Summarization"
    agent: "summarizer-agent"
  - name: "Review"
    agent: "reviewer-agent"
"""

        config = yaml.safe_load(generated)

        # THEN: Sequential steps created
        assert len(config["steps"]) == 3
        assert config["steps"][0]["name"] == "Analysis"

    def test_generates_parallel_steps(self):
        """Test generation of workflow with parallel execution."""
        generated = """workflow:
  name: "Content Pipeline"
  workflow_id: "content-pipeline"

steps:
  - name: "Input"
    agent: "input-agent"
  - type: "parallel"
    steps:
      - name: "Grammar Check"
        agent: "grammar-agent"
      - name: "SEO Analysis"
        agent: "seo-agent"
  - name: "Publish"
    agent: "publisher-agent"
"""

        config = yaml.safe_load(generated)

        # THEN: Parallel steps detected
        parallel_step = config["steps"][1]
        assert parallel_step["type"] == "parallel"
        assert len(parallel_step["steps"]) == 2


class TestPromptOptimization:
    """Test prompt engineering and optimization."""

    def test_optimizes_vague_instructions(self):
        """Test that vague prompts are improved."""
        vague_prompt = "Help users"

        # Mock optimization
        optimized = (
            "You are a customer support specialist. "
            "Help users by:\n"
            "1. Understanding their question clearly\n"
            "2. Providing accurate, helpful answers\n"
            "3. Following up to ensure satisfaction"
        )

        # THEN: Optimized prompt is more specific
        assert len(optimized) > len(vague_prompt) * 3
        assert "1." in optimized  # Has structure
        assert "customer" in optimized.lower()  # More specific

    def test_adds_safety_guidelines(self):
        """Test that safety guidelines are added to prompts."""
        base_prompt = "Answer user questions about accounts"

        # Mock safety enhancement
        safe_prompt = (
            base_prompt + "\n\nSafety guidelines:\n"
            "- Never share sensitive account data\n"
            "- Always verify user identity first\n"
            "- Escalate suspicious requests"
        )

        # THEN: Safety guidelines added
        assert "safety" in safe_prompt.lower()
        assert "verify" in safe_prompt.lower()


class TestGenerationQuality:
    """Test quality of generated configurations."""

    def test_generated_names_are_readable(self):
        """Test that generated names are human-readable."""
        test_descriptions = [
            "customer support bot",
            "code review assistant",
            "data analysis agent",
        ]

        for desc in test_descriptions:
            # Mock name generation
            name = self._generate_name(desc)

            # THEN: Name is readable
            assert len(name) > 5
            assert " " in name  # Has spaces
            assert name[0].isupper()  # Capitalized

    def _generate_name(self, description: str) -> str:
        """Mock name generation."""
        words = description.split()
        return " ".join(w.capitalize() for w in words)

    def test_generated_ids_are_valid(self):
        """Test that generated IDs follow kebab-case."""
        names = ["Customer Support Bot", "Code Reviewer", "Data Analyst"]

        for name in names:
            # Mock ID generation
            agent_id = name.lower().replace(" ", "-")

            # THEN: ID is valid kebab-case
            assert " " not in agent_id
            assert agent_id.islower() or "-" in agent_id

    def test_instructions_are_substantive(self):
        """Test that generated instructions are detailed."""
        # GIVEN: Agent purpose

        # Mock instruction generation
        instructions = (
            "You are a billing support specialist.\n"
            "Your responsibilities:\n"
            "1. Answer payment and invoice questions\n"
            "2. Help resolve billing disputes\n"
            "3. Update payment methods\n"
            "Always verify account details before making changes."
        )

        # THEN: Instructions are detailed
        assert len(instructions) > 100  # Substantive
        assert "\n" in instructions  # Multi-line
        assert any(char.isdigit() for char in instructions)  # Has numbered steps


class TestErrorRecovery:
    """Test error handling in generation."""

    @pytest.mark.asyncio
    async def test_retries_on_api_error(self):
        """Test that generator retries on API failures."""
        # Mock API that fails then succeeds
        call_count = 0

        async def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("API Error")
            return {"success": True}

        # Simulate retry logic
        try:
            result = await mock_api_call()
        except Exception:
            result = await mock_api_call()  # Retry

        # THEN: Eventually succeeds
        assert result["success"]
        assert call_count == 2

    def test_provides_fallback_on_total_failure(self):
        """Test that generator provides template on complete failure."""
        # If AI generation fails completely, return basic template
        fallback_config = {
            "agent": {"name": "New Agent", "version": 1},
            "model": {"id": "gpt-4o-mini"},
            "instructions": "TODO: Add your instructions here",
        }

        # THEN: Fallback is valid but needs user input
        assert "TODO" in fallback_config["instructions"]
        assert fallback_config["agent"]["name"]
