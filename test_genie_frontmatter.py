"""Comprehensive test suite for Genie Frontmatter Interpreter.

This test suite validates all components:
1. Frontmatter parser (parse_markdown_frontmatter)
2. Genie->Hive mapper (map_genie_to_hive)
3. Schema validator (validate_genie_agent)
4. Agent ID derivation (derive_genie_agent_id)
5. Full discovery pipeline integration
"""


import pytest

from hive.discovery import derive_genie_agent_id, discover_agents_with_frontmatter
from hive.scaffolder.frontmatter_parser import parse_markdown_frontmatter
from hive.scaffolder.genie_mapper import convert_genie_model_to_hive, map_genie_to_hive
from hive.scaffolder.validator import ConfigValidator

# ============================================================================
# TEST 1: Frontmatter Parser Tests
# ============================================================================


class TestFrontmatterParser:
    """Test parse_markdown_frontmatter function."""

    def test_valid_frontmatter(self, tmp_path):
        """Test parsing valid frontmatter."""
        content = """---
name: test-agent
description: Test description
genie:
  executor: CLAUDE_CODE
---

# Agent Instructions
This is the agent content.
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        result = parse_markdown_frontmatter(str(test_file))

        assert "frontmatter" in result
        assert "content" in result
        assert result["frontmatter"]["name"] == "test-agent"
        assert result["frontmatter"]["description"] == "Test description"
        assert "# Agent Instructions" in result["content"]

    def test_missing_frontmatter(self, tmp_path):
        """Test file without frontmatter raises ValueError."""
        content = "# Just markdown content\nNo frontmatter here."
        test_file = tmp_path / "no_frontmatter.md"
        test_file.write_text(content)

        with pytest.raises(ValueError, match="No frontmatter found"):
            parse_markdown_frontmatter(str(test_file))

    def test_invalid_yaml_in_frontmatter(self, tmp_path):
        """Test malformed YAML raises ValueError."""
        content = """---
name: test
invalid: [yaml: structure
---

Content here.
"""
        test_file = tmp_path / "invalid_yaml.md"
        test_file.write_text(content)

        with pytest.raises(ValueError, match="Invalid YAML"):
            parse_markdown_frontmatter(str(test_file))

    def test_file_not_found(self):
        """Test non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_markdown_frontmatter("/nonexistent/path/file.md")

    def test_empty_frontmatter(self, tmp_path):
        """Test empty frontmatter (no YAML content)."""
        content = """---
---

Content here.
"""
        test_file = tmp_path / "empty_frontmatter.md"
        test_file.write_text(content)

        result = parse_markdown_frontmatter(str(test_file))
        assert result["frontmatter"] == {}
        assert result["content"] == "Content here."

    def test_multiline_yaml(self, tmp_path):
        """Test complex multiline YAML frontmatter."""
        content = """---
name: complex-agent
description: Multi-line description here
genie:
  executor:
    - CLAUDE_CODE
    - CODEX
  background: true
forge:
  CLAUDE_CODE:
    model: sonnet
    dangerously_skip_permissions: true
---

# Complex Agent
Multi-paragraph content.
"""
        test_file = tmp_path / "complex.md"
        test_file.write_text(content)

        result = parse_markdown_frontmatter(str(test_file))

        assert result["frontmatter"]["name"] == "complex-agent"
        assert isinstance(result["frontmatter"]["genie"]["executor"], list)
        assert len(result["frontmatter"]["genie"]["executor"]) == 2
        assert result["frontmatter"]["forge"]["CLAUDE_CODE"]["model"] == "sonnet"


# ============================================================================
# TEST 2: Genie Mapper Tests
# ============================================================================


class TestGenieMapper:
    """Test map_genie_to_hive conversion."""

    def test_model_conversion(self):
        """Test model name conversion mapping."""
        assert convert_genie_model_to_hive("sonnet") == "anthropic:claude-sonnet-4-20250514"
        assert convert_genie_model_to_hive("opus") == "anthropic:claude-opus-4-20250514"
        assert convert_genie_model_to_hive("haiku") == "anthropic:claude-haiku-3-5-20241022"
        assert convert_genie_model_to_hive("gpt-5-codex") == "openai:gpt-4o"
        assert convert_genie_model_to_hive("unknown-model") == "openai:gpt-4o"  # fallback

    def test_basic_mapping(self):
        """Test basic Genie to Hive mapping."""
        genie_config = {
            "name": "test-agent",
            "description": "Test agent description",
            "genie": {"executor": "CLAUDE_CODE"},
            "forge": {"CLAUDE_CODE": {"model": "sonnet"}},
        }
        content = "Test agent instructions"

        result = map_genie_to_hive(genie_config, content)

        assert result["agent"]["name"] == "test-agent"
        assert result["agent"]["id"] == "test-agent"
        assert result["agent"]["description"] == "Test agent description"
        assert result["agent"]["model"] == "anthropic:claude-sonnet-4-20250514"
        assert result["instructions"] == content
        assert result["agent"]["executor_chain"] == ["claude_code"]

    def test_executor_list_mapping(self):
        """Test executor as list conversion."""
        genie_config = {
            "name": "multi-executor",
            "description": "Multi-executor agent",
            "genie": {"executor": ["CLAUDE_CODE", "CODEX", "OPENCODE"]},
            "forge": {
                "CLAUDE_CODE": {"model": "sonnet"},
                "CODEX": {"model": "gpt-5-codex"},
            },
        }
        content = "Instructions"

        result = map_genie_to_hive(genie_config, content)

        assert result["agent"]["executor_chain"] == ["claude_code", "codex", "opencode"]
        # Primary executor (first in list) determines model
        assert result["agent"]["model"] == "anthropic:claude-sonnet-4-20250514"

    def test_background_flag_mapping(self):
        """Test background flag conversion."""
        genie_config = {
            "name": "bg-agent",
            "description": "Background agent",
            "genie": {"executor": "CLAUDE_CODE", "background": True},
            "forge": {"CLAUDE_CODE": {"model": "sonnet"}},
        }
        content = "Instructions"

        result = map_genie_to_hive(genie_config, content)

        assert "settings" in result
        assert result["settings"]["background"] is True

    def test_skip_permissions_mapping(self):
        """Test dangerously_skip_permissions flag mapping."""
        genie_config = {
            "name": "dangerous-agent",
            "description": "Agent with skip permissions",
            "genie": {"executor": "CLAUDE_CODE"},
            "forge": {"CLAUDE_CODE": {"model": "sonnet", "dangerously_skip_permissions": True}},
        }
        content = "Instructions"

        result = map_genie_to_hive(genie_config, content)

        assert "settings" in result
        assert result["settings"]["skip_permissions"] is True

    def test_default_values(self):
        """Test default values when fields are missing."""
        genie_config = {
            "name": "minimal-agent",
            "description": "Minimal config",
        }
        content = "Instructions"

        result = map_genie_to_hive(genie_config, content)

        # Check defaults
        assert result["agent"]["name"] == "minimal-agent"
        assert result["agent"]["model"] == "anthropic:claude-sonnet-4-20250514"  # default model
        assert result["agent"]["executor_chain"] == ["claude_code"]  # default executor
        assert result["instructions"] == content
        assert result["tools"] == []
        assert result["storage"]["type"] == "sqlite"

    def test_model_fallback_from_unknown_executor(self):
        """Test model fallback when executor not in forge section."""
        genie_config = {
            "name": "no-forge-agent",
            "description": "Agent without forge config",
            "genie": {"executor": "UNKNOWN_EXECUTOR"},
            "forge": {},
        }
        content = "Instructions"

        result = map_genie_to_hive(genie_config, content)

        # Should fall back to default model (sonnet -> anthropic:claude-sonnet-4-20250514)
        assert result["agent"]["model"] == "anthropic:claude-sonnet-4-20250514"


# ============================================================================
# TEST 3: Schema Validator Tests
# ============================================================================


class TestGenieValidator:
    """Test validate_genie_agent schema validation."""

    def test_valid_minimal_config(self):
        """Test validation of minimal valid config."""
        config = {
            "name": "test-agent",
            "description": "Test description",
        }

        # Should not raise
        assert ConfigValidator.validate_genie_agent(config) is True

    def test_valid_full_config(self):
        """Test validation of complete config."""
        config = {
            "name": "full-agent",
            "description": "Full agent description",
            "genie": {
                "executor": ["CLAUDE_CODE", "CODEX"],
                "background": True,
                "variant": "standard",
                "permissionMode": "ask",
            },
            "forge": {
                "CLAUDE_CODE": {"model": "sonnet"},
                "CODEX": {"model": "gpt-5-codex"},
            },
        }

        assert ConfigValidator.validate_genie_agent(config) is True

    def test_missing_name(self):
        """Test validation fails when name is missing."""
        config = {"description": "Missing name"}

        with pytest.raises(ValueError, match="Missing required field: 'name'"):
            ConfigValidator.validate_genie_agent(config)

    def test_missing_description(self):
        """Test validation fails when description is missing."""
        config = {"name": "test-agent"}

        with pytest.raises(ValueError, match="Missing required field: 'description'"):
            ConfigValidator.validate_genie_agent(config)

    def test_empty_name(self):
        """Test validation fails when name is empty."""
        config = {"name": "", "description": "Test"}

        with pytest.raises(ValueError, match="Field 'name' cannot be empty"):
            ConfigValidator.validate_genie_agent(config)

    def test_empty_description(self):
        """Test validation fails when description is empty."""
        config = {"name": "test", "description": ""}

        with pytest.raises(ValueError, match="Field 'description' cannot be empty"):
            ConfigValidator.validate_genie_agent(config)

    def test_invalid_name_type(self):
        """Test validation fails when name is not a string."""
        config = {"name": 123, "description": "Test"}

        with pytest.raises(ValueError, match="Field 'name' must be a string"):
            ConfigValidator.validate_genie_agent(config)

    def test_invalid_genie_section_type(self):
        """Test validation fails when genie section is not a dict."""
        config = {"name": "test", "description": "Test", "genie": "not-a-dict"}

        with pytest.raises(ValueError, match="Field 'genie' must be a dict"):
            ConfigValidator.validate_genie_agent(config)

    def test_invalid_executor_type(self):
        """Test validation fails when executor is not str or list."""
        config = {
            "name": "test",
            "description": "Test",
            "genie": {"executor": 123},
        }

        with pytest.raises(ValueError, match="Field 'genie.executor' must be a string or list"):
            ConfigValidator.validate_genie_agent(config)

    def test_invalid_executor_list_item(self):
        """Test validation fails when executor list contains non-strings."""
        config = {
            "name": "test",
            "description": "Test",
            "genie": {"executor": ["CLAUDE_CODE", 123, "CODEX"]},
        }

        with pytest.raises(ValueError, match="Field 'genie.executor\\[1\\]' must be a string"):
            ConfigValidator.validate_genie_agent(config)

    def test_invalid_background_type(self):
        """Test validation fails when background is not boolean."""
        config = {
            "name": "test",
            "description": "Test",
            "genie": {"background": "true"},  # string instead of bool
        }

        with pytest.raises(ValueError, match="Field 'genie.background' must be a boolean"):
            ConfigValidator.validate_genie_agent(config)

    def test_invalid_forge_section_type(self):
        """Test validation fails when forge section is not a dict."""
        config = {
            "name": "test",
            "description": "Test",
            "forge": "not-a-dict",
        }

        with pytest.raises(ValueError, match="Field 'forge' must be a dict"):
            ConfigValidator.validate_genie_agent(config)


# ============================================================================
# TEST 4: Agent ID Derivation Tests
# ============================================================================


class TestAgentIdDerivation:
    """Test derive_genie_agent_id function."""

    def test_base_agents_path(self):
        """Test agent ID derivation from .genie/agents/ path."""
        file_path = ".genie/agents/review.md"
        agent_id = derive_genie_agent_id(file_path)
        assert agent_id == "genie/review"

    def test_code_agents_path(self):
        """Test agent ID derivation from .genie/code/agents/ path."""
        file_path = ".genie/code/agents/fix.md"
        agent_id = derive_genie_agent_id(file_path)
        assert agent_id == "genie/code/fix"

    def test_nested_agent_path(self):
        """Test nested agent path (subdirectory)."""
        file_path = ".genie/agents/teams/analyze.md"
        agent_id = derive_genie_agent_id(file_path)
        assert agent_id == "genie/teams/analyze"

    def test_absolute_path(self):
        """Test with absolute path."""
        file_path = "/Users/test/project/.genie/agents/test.md"
        agent_id = derive_genie_agent_id(file_path)
        assert agent_id == "genie/test"

    def test_code_agents_nested(self):
        """Test nested path in code agents."""
        file_path = ".genie/code/agents/qa/hive-qa-tester.md"
        agent_id = derive_genie_agent_id(file_path)
        assert agent_id == "genie/code/qa/hive-qa-tester"

    def test_fallback_for_unknown_path(self):
        """Test fallback when path doesn't match known patterns."""
        file_path = "/some/random/path/agent.md"
        agent_id = derive_genie_agent_id(file_path)
        assert agent_id == "genie/agent"  # fallback to filename


# ============================================================================
# TEST 5: Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for full discovery pipeline."""

    def test_full_pipeline_valid_agent(self, tmp_path):
        """Test full pipeline with valid Genie agent."""
        # Create test directory structure
        agents_dir = tmp_path / ".genie" / "agents"
        agents_dir.mkdir(parents=True)

        # Write test agent
        agent_content = """---
name: test-agent
description: Test agent for integration
genie:
  executor: CLAUDE_CODE
  background: false
forge:
  CLAUDE_CODE:
    model: sonnet
---

# Test Agent
This is a test agent for integration testing.
"""
        agent_file = agents_dir / "test-agent.md"
        agent_file.write_text(agent_content)

        # Run discovery
        agents = discover_agents_with_frontmatter(tmp_path)

        # Verify
        assert len(agents) == 1
        agent = agents[0]
        assert agent.name == "test-agent"
        assert agent.id == "genie/test-agent"
        assert agent.description == "Test agent for integration"
        assert "This is a test agent" in agent.instructions

    def test_multiple_agents_discovery(self, tmp_path):
        """Test discovering multiple agents."""
        # Create test directory structure
        agents_dir = tmp_path / ".genie" / "agents"
        agents_dir.mkdir(parents=True)

        # Write multiple agents
        for i in range(3):
            agent_content = f"""---
name: agent-{i}
description: Test agent {i}
---

Agent {i} instructions.
"""
            agent_file = agents_dir / f"agent-{i}.md"
            agent_file.write_text(agent_content)

        # Run discovery
        agents = discover_agents_with_frontmatter(tmp_path)

        # Verify
        assert len(agents) == 3
        agent_names = {agent.name for agent in agents}
        assert agent_names == {"agent-0", "agent-1", "agent-2"}

    def test_skip_underscore_files(self, tmp_path):
        """Test that files starting with underscore are skipped."""
        agents_dir = tmp_path / ".genie" / "agents"
        agents_dir.mkdir(parents=True)

        # Write public agent
        public_agent = """---
name: public-agent
description: Public agent
---

Public instructions.
"""
        (agents_dir / "public.md").write_text(public_agent)

        # Write private agent (underscore prefix)
        private_agent = """---
name: private-agent
description: Private agent
---

Private instructions.
"""
        (agents_dir / "_private.md").write_text(private_agent)

        # Run discovery
        agents = discover_agents_with_frontmatter(tmp_path)

        # Verify only public agent discovered
        assert len(agents) == 1
        assert agents[0].name == "public-agent"

    def test_invalid_agent_skipped(self, tmp_path):
        """Test that invalid agents are skipped with warning."""
        agents_dir = tmp_path / ".genie" / "agents"
        agents_dir.mkdir(parents=True)

        # Write valid agent
        valid_agent = """---
name: valid-agent
description: Valid agent
---

Valid instructions.
"""
        (agents_dir / "valid.md").write_text(valid_agent)

        # Write invalid agent (missing required field)
        invalid_agent = """---
name: invalid-agent
---

Missing description.
"""
        (agents_dir / "invalid.md").write_text(invalid_agent)

        # Run discovery
        agents = discover_agents_with_frontmatter(tmp_path)

        # Verify only valid agent loaded
        assert len(agents) == 1
        assert agents[0].name == "valid-agent"

    def test_code_agents_directory(self, tmp_path):
        """Test discovery from .genie/code/agents/."""
        code_agents_dir = tmp_path / ".genie" / "code" / "agents"
        code_agents_dir.mkdir(parents=True)

        agent_content = """---
name: code-agent
description: Code agent
---

Code agent instructions.
"""
        (code_agents_dir / "code-agent.md").write_text(agent_content)

        # Run discovery
        agents = discover_agents_with_frontmatter(tmp_path)

        assert len(agents) == 1
        assert agents[0].name == "code-agent"
        assert agents[0].id == "genie/code/code-agent"


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
