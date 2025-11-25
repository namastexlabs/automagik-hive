"""Test real Genie agent files from the project."""

from pathlib import Path

import pytest

from hive.discovery import derive_genie_agent_id, discover_agents_with_frontmatter
from hive.scaffolder.frontmatter_parser import parse_markdown_frontmatter
from hive.scaffolder.genie_mapper import map_genie_to_hive
from hive.scaffolder.validator import ConfigValidator


PROJECT_ROOT = Path("/Users/caiorod/Documents/Namastex/automagik-hive")


class TestRealGenieAgents:
    """Test with real Genie agent markdown files."""

    def test_analyze_agent(self):
        """Test parsing analyze.md agent."""
        agent_file = PROJECT_ROOT / ".genie" / "agents" / "analyze.md"

        if not agent_file.exists():
            pytest.skip(f"Agent file not found: {agent_file}")

        # Parse frontmatter
        parsed = parse_markdown_frontmatter(str(agent_file))
        frontmatter = parsed["frontmatter"]
        content = parsed["content"]

        # Validate schema
        ConfigValidator.validate_genie_agent(frontmatter)

        # Map to Hive
        hive_config = map_genie_to_hive(frontmatter, content)

        # Assertions
        assert hive_config["agent"]["name"] == "analyze"
        assert hive_config["agent"]["description"] == "System analysis and focused investigations (universal framework)"
        assert "anthropic:claude-sonnet" in hive_config["agent"]["model"]
        assert "Analyze Agent" in hive_config["instructions"]

        # Check settings
        assert "settings" in hive_config
        assert hive_config["settings"]["background"] is True

    def test_fix_agent(self):
        """Test parsing fix.md agent."""
        agent_file = PROJECT_ROOT / ".genie" / "code" / "agents" / "fix.md"

        if not agent_file.exists():
            pytest.skip(f"Agent file not found: {agent_file}")

        # Parse frontmatter
        parsed = parse_markdown_frontmatter(str(agent_file))
        frontmatter = parsed["frontmatter"]
        content = parsed["content"]

        # Validate schema
        ConfigValidator.validate_genie_agent(frontmatter)

        # Map to Hive
        hive_config = map_genie_to_hive(frontmatter, content)

        # Assertions
        assert hive_config["agent"]["name"] == "fix"
        assert hive_config["agent"]["description"] == "Apply fixes using debug spell and other code agents/spells as needed"

        # Check executor chain (multiple executors)
        assert "executor_chain" in hive_config["agent"]
        assert len(hive_config["agent"]["executor_chain"]) == 3
        assert "claude_code" in hive_config["agent"]["executor_chain"]

        # Check settings
        assert "settings" in hive_config
        assert hive_config["settings"]["background"] is True
        assert hive_config["settings"]["skip_permissions"] is True

    def test_derive_id_from_real_paths(self):
        """Test derive_genie_agent_id with real file paths."""
        test_cases = [
            (".genie/agents/analyze.md", "genie/analyze"),
            (".genie/agents/wish.md", "genie/wish"),
            (".genie/code/agents/fix.md", "genie/code/fix"),
            (".genie/code/agents/explore.md", "genie/code/explore"),
        ]

        for file_path, expected_id in test_cases:
            agent_id = derive_genie_agent_id(file_path)
            assert agent_id == expected_id, f"Path {file_path} should map to {expected_id}, got {agent_id}"

    def test_full_discovery_integration(self):
        """Test full discovery with real project structure."""
        if not PROJECT_ROOT.exists():
            pytest.skip(f"Project root not found: {PROJECT_ROOT}")

        # Run discovery
        agents = discover_agents_with_frontmatter(PROJECT_ROOT)

        # Should discover multiple agents
        assert len(agents) > 0, "Should discover at least one agent"

        # Check agent properties
        for agent in agents:
            assert hasattr(agent, "name")
            assert hasattr(agent, "id")
            assert hasattr(agent, "description")
            assert hasattr(agent, "instructions")
            assert agent.instructions, f"Agent {agent.name} has empty instructions"

        # Find specific agents
        agent_names = {agent.name for agent in agents}
        agent_ids = {agent.id for agent in agents}

        print(f"\nDiscovered {len(agents)} agents:")
        for agent in agents:
            print(f"  - {agent.name} (id: {agent.id})")

        # Should find some known agents
        assert "analyze" in agent_names or "fix" in agent_names, "Should find at least one known agent"

    def test_all_agents_parse_without_error(self):
        """Test that all .md files in .genie directories parse without errors."""
        agent_dirs = [
            PROJECT_ROOT / ".genie" / "agents",
            PROJECT_ROOT / ".genie" / "code" / "agents",
        ]

        errors = []
        successful = []

        for agent_dir in agent_dirs:
            if not agent_dir.exists():
                continue

            for md_file in agent_dir.rglob("*.md"):
                # Skip files starting with underscore and README
                if md_file.name.startswith("_") or md_file.name == "README.md":
                    continue

                try:
                    # Parse frontmatter
                    parsed = parse_markdown_frontmatter(str(md_file))
                    frontmatter = parsed["frontmatter"]
                    content = parsed["content"]

                    # Validate schema
                    ConfigValidator.validate_genie_agent(frontmatter)

                    # Map to Hive
                    hive_config = map_genie_to_hive(frontmatter, content)

                    successful.append(md_file.name)
                except Exception as e:
                    errors.append((md_file.name, str(e)))

        # Report results
        print(f"\nSuccessfully parsed {len(successful)} agents:")
        for name in successful:
            print(f"  ✓ {name}")

        if errors:
            print(f"\nErrors in {len(errors)} agents:")
            for name, error in errors:
                print(f"  ✗ {name}: {error}")

        # All should succeed
        assert len(errors) == 0, f"Failed to parse {len(errors)} agents: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
