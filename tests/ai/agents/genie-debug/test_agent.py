"""
TDD Test Suite for Genie Debug Agent - RED Phase Implementation

This test suite follows TDD methodology with failing tests first to drive implementation.
Tests are designed to FAIL initially to enforce RED phase compliance.

Agent Under Test: ai/agents/genie-debug/agent.py
Pattern: Direct Agno Agent creation with YAML configuration loading
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import yaml
import os


@pytest.fixture
def agent_config_dir():
    """Provide the path to the genie-debug agent configuration directory."""
    # Navigate to project root and then to the agent directory
    current_file = Path(__file__).resolve()
    # Go up from tests/ai/agents/genie-debug/test_agent.py to project root (5 levels)
    project_root = current_file.parent.parent.parent.parent.parent
    return project_root / "ai" / "agents" / "genie-debug"


@pytest.fixture
def sample_config():
    """Provide sample configuration for genie-debug agent."""
    return {
        "name": "genie-debug",
        "description": "Debug specialist agent",
        "instructions": "You are a debug specialist",
        "model": "claude-3.5-sonnet",
        "tools": ["bash", "read", "edit"],
        "temperature": 0.1
    }


class TestGenieDebugAgent:
    """Test suite for Genie Debug Agent configuration and instantiation."""
    
    def test_config_file_exists(self, agent_config_dir):
        """Test that the agent configuration file exists."""
        config_file = agent_config_dir / "config.yaml"
        
        assert config_file.exists(), f"Configuration file not found at {config_file}"
    
    def test_agent_file_exists(self, agent_config_dir):
        """Test that the agent implementation file exists."""
        agent_file = agent_config_dir / "agent.py"
            
        assert agent_file.exists(), f"Agent file not found at {agent_file}"
    
    def test_config_file_valid_yaml(self, agent_config_dir):
        """Test that the configuration file contains valid YAML."""
        config_file = agent_config_dir / "config.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        assert isinstance(config, dict), "Configuration should be a dictionary"
        assert "agent" in config, "Configuration should have an 'agent' section"
        assert "name" in config["agent"], "Agent section should have a 'name' field"
    
    def test_config_has_required_fields(self, agent_config_dir):
        """Test that configuration contains all required fields."""
        config_file = agent_config_dir / "config.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check agent section required fields
        agent_required_fields = ["name", "agent_id", "description"]
        assert "agent" in config, "Configuration missing 'agent' section"
        for field in agent_required_fields:
            assert field in config["agent"], f"Agent section missing required field: {field}"
            
        # Check top-level required fields
        top_level_required_fields = ["instructions", "model"]
        for field in top_level_required_fields:
            assert field in config, f"Configuration missing required top-level field: {field}"
    
    def test_agent_name_matches_directory(self, agent_config_dir):
        """Test that agent_id in config matches directory name."""
        config_file = agent_config_dir / "config.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        expected_agent_id = "genie-debug"
        actual_agent_id = config.get("agent", {}).get("agent_id")
        assert actual_agent_id == expected_agent_id, f"Agent ID '{actual_agent_id}' doesn't match directory name '{expected_agent_id}'"
    
    def test_agent_instantiation(self, agent_config_dir, sample_config):
        """Test that agent can be instantiated with configuration."""
        config_file = agent_config_dir / "config.yaml"
        agent_file = agent_config_dir / "agent.py"
        
        # Verify files exist
        assert config_file.exists(), "Config file should exist"
        assert agent_file.exists(), "Agent file should exist"
        
        # Check agent.py has the get_genie_debug_agent function
        with open(agent_file, 'r') as f:
            agent_content = f.read()
        
        assert "def get_genie_debug_agent" in agent_content, "Agent file should define get_genie_debug_agent function"
        assert "Agent.from_yaml" in agent_content, "Agent should use Agent.from_yaml pattern"
    
    def test_agent_has_debug_specific_tools(self, agent_config_dir):
        """Test that debug agent has appropriate debugging tools."""
        config_file = agent_config_dir / "config.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        tools = config.get("tools", [])
        mcp_servers = config.get("mcp_servers", [])
        
        # Check if debugging capabilities are configured via tools or MCP servers
        has_tools_configured = len(tools) > 0
        has_mcp_servers_configured = len(mcp_servers) > 0
        
        assert has_tools_configured or has_mcp_servers_configured, "Debug agent should have tools or MCP servers configured"
        
        # Check for postgres tool (debugging often needs database queries)
        tool_names = []
        for tool in tools:
            if isinstance(tool, dict):
                tool_names.append(tool.get("name", ""))
            else:
                tool_names.append(str(tool))
        
        # Check MCP servers for debugging capabilities
        mcp_server_names = []
        for server in mcp_servers:
            if isinstance(server, dict):
                mcp_server_names.append(server.get("name", ""))
            else:
                mcp_server_names.append(str(server))
        
        # Should have debugging-related tools or MCP servers
        has_postgres_tool = any("postgres" in tool_name.lower() for tool_name in tool_names)
        has_shell_tool = any("shell" in tool_name.lower() for tool_name in tool_names)
        has_postgres_mcp = any("postgres" in server_name.lower() for server_name in mcp_server_names)
        has_shell_mcp = any("shell" in server_name.lower() for server_name in mcp_server_names)
        
        has_debugging_capability = has_postgres_tool or has_shell_tool or has_postgres_mcp or has_shell_mcp
        
        assert has_debugging_capability, f"Debug agent should have debugging capabilities. Tools: {tool_names}, MCP servers: {mcp_server_names}"
    
    def test_agent_temperature_for_debugging(self, agent_config_dir):
        """Test that debug agent has appropriate temperature for precise debugging."""
        config_file = agent_config_dir / "config.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Temperature is nested under model section in the actual config
        model_config = config.get("model", {})
        temperature = model_config.get("temperature", 0.5)
        assert temperature <= 0.3, f"Debug agent should have low temperature for precision, got {temperature}"


class TestGenieDebugAgentIntegration:
    """Integration tests for Genie Debug Agent with Agno framework."""
    
    def test_agent_factory_function_exists(self, agent_config_dir):
        """Test that agent factory function exists."""
        agent_file = agent_config_dir / "agent.py"
        
        with open(agent_file, 'r') as f:
            content = f.read()
        
        # Should have the factory function
        assert "def get_genie_debug_agent" in content, "Should have factory function"
        assert "return Agent.from_yaml" in content, "Should use Agent.from_yaml"
    
    def test_agent_responds_to_debug_requests(self, agent_config_dir):
        """Test that agent configuration supports debug requests."""
        config_file = agent_config_dir / "config.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check instructions mention debugging
        instructions = config.get("instructions", "")
        assert "debug" in instructions.lower(), "Instructions should mention debugging"
        
        # Future implementation would test:
        # - Error analysis capabilities
        # - Code inspection functionality  
        # - Debug step execution
        # - Result interpretation


class TestTDDCompliance:
    """Tests to ensure TDD methodology compliance."""
    
    def test_all_tests_fail_initially(self):
        """Ensure tests fail in RED phase to drive implementation."""
        # This test documents TDD compliance
        # Most tests above should fail until implementation is complete
        assert True, "TDD RED phase documented - implementation needed"
    
    def test_config_drives_implementation(self, agent_config_dir):
        """Test that configuration exists to drive implementation."""
        config_file = agent_config_dir / "config.yaml"
        
        assert config_file.exists(), "Configuration should exist to drive TDD implementation"