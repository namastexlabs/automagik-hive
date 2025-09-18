#!/usr/bin/env python3
"""
Test to verify MCP tools parsing from YAML configs is working.
This verifies the fix for PR #16 - enabling MCP tools in YAML configs.
"""

import pytest
from pathlib import Path
from lib.config.yaml_parser import YAMLConfigParser


class TestMCPYAMLParsing:
    """Test MCP server parsing from YAML configurations."""

    def test_parse_mcp_servers_from_yaml(self):
        """Test that mcp_servers field is properly parsed from YAML."""
        parser = YAMLConfigParser()

        # Test template agent config which has mcp_servers defined
        config_path = "ai/agents/template-agent/config.yaml"
        if not Path(config_path).exists():
            pytest.skip(f"Config file not found: {config_path}")

        config = parser.parse_agent_config(config_path)

        # Verify MCP servers were detected
        assert config.mcp_tools, "MCP tools should be detected from mcp_servers field"

        # Check specific servers
        server_names = [t.server_name for t in config.mcp_tools]
        assert "postgres" in server_names, "postgres should be in MCP servers"
        assert "ask-repo-agent" in server_names, "ask-repo-agent should be in MCP servers"
        assert "search-repo-docs" in server_names, "search-repo-docs should be in MCP servers"

    def test_mcp_server_patterns(self):
        """Test parsing of MCP server patterns like 'server:tool'."""
        parser = YAMLConfigParser()

        # Test genie-debug config which uses patterns
        config_path = "ai/agents/genie-debug/config.yaml"
        if not Path(config_path).exists():
            pytest.skip(f"Config file not found: {config_path}")

        config = parser.parse_agent_config(config_path)

        # Should extract server names from patterns
        server_names = [t.server_name for t in config.mcp_tools]
        assert "postgres" in server_names, "Should extract 'postgres' from 'postgres:*'"
        assert "ask-repo-agent" in server_names, "Should extract 'ask-repo-agent' from pattern"

    def test_backward_compatibility_mcp_dot_format(self):
        """Test that the old 'mcp.servername' format in tools list still works."""
        import tempfile
        import yaml

        # Create a test config with old format
        test_config = {
            "agent": {
                "name": "Test Agent",
                "agent_id": "test-agent",
                "version": 1
            },
            "model": {
                "provider": "openai",
                "id": "gpt-5"
            },
            "storage": {
                "type": "postgres",
                "table_name": "test_agent"
            },
            "tools": [
                "mcp.postgres",
                "mcp.search-repo-docs",
                "regular_tool"
            ],
            "instructions": "Test instructions"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = f.name

        try:
            parser = YAMLConfigParser()
            config = parser.parse_agent_config(temp_path)

            # Check tools were properly separated
            assert "regular_tool" in config.regular_tools
            assert len(config.mcp_tools) == 2

            server_names = [t.server_name for t in config.mcp_tools]
            assert "postgres" in server_names
            assert "search-repo-docs" in server_names

        finally:
            Path(temp_path).unlink()

    def test_combined_mcp_formats(self):
        """Test that both mcp.servername and mcp_servers can work together."""
        import tempfile
        import yaml

        # Create a test config with both formats
        test_config = {
            "agent": {
                "name": "Test Agent",
                "agent_id": "test-agent",
                "version": 1
            },
            "model": {
                "provider": "openai",
                "id": "gpt-5"
            },
            "storage": {
                "type": "postgres",
                "table_name": "test_agent"
            },
            "tools": [
                "mcp.tool-from-tools-list",
                "regular_tool"
            ],
            "mcp_servers": [
                "server-from-mcp-servers:*",
                "another-server"
            ],
            "instructions": "Test instructions"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = f.name

        try:
            parser = YAMLConfigParser()
            config = parser.parse_agent_config(temp_path)

            # Check all MCP servers were detected
            server_names = [t.server_name for t in config.mcp_tools]
            assert "tool-from-tools-list" in server_names, "Should parse from tools list"
            assert "server-from-mcp-servers" in server_names, "Should parse from mcp_servers"
            assert "another-server" in server_names, "Should parse simple server names"

            # Regular tools should still work
            assert "regular_tool" in config.regular_tools

        finally:
            Path(temp_path).unlink()


@pytest.mark.asyncio
async def test_agent_creation_with_mcp():
    """Test that agents can be created with MCP servers configured."""
    from ai.agents.registry import get_agent

    # Test template agent
    agent = await get_agent("template-agent")
    assert agent is not None, "Template agent should be created"
    assert agent.agent_id == "template-agent"

    # Test genie-debug agent
    agent = await get_agent("genie-debug")
    assert agent is not None, "Genie debug agent should be created"
    assert agent.agent_id == "genie-debug"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])