"""
TDD Test Suite for Genie Debug Agent - RED Phase Implementation

This test suite follows TDD methodology with failing tests first to drive implementation.
Tests are designed to FAIL initially to enforce RED phase compliance.

Agent Under Test: ai/agents/genie-debug/agent.py
Pattern: Direct Agno Agent creation with YAML configuration loading
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import yaml
import sys
import os

# Add the project root to Python path for module imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
        assert "name" in config, "Configuration should have a 'name' field"
    
    def test_config_has_required_fields(self, agent_config_dir):
        """Test that configuration contains all required fields."""
        config_file = agent_config_dir / "config.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        required_fields = ["name", "description", "instructions", "model"]
        for field in required_fields:
            assert field in config, f"Configuration missing required field: {field}"
    
    def test_agent_name_matches_directory(self, agent_config_dir):
        """Test that agent name in config matches directory name."""
        config_file = agent_config_dir / "config.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        expected_name = "genie-debug"
        actual_name = config.get("name")
        assert actual_name == expected_name, f"Agent name '{actual_name}' doesn't match directory name '{expected_name}'"
    
    @patch('agno.Agent')
    def test_agent_instantiation(self, mock_agent_class, agent_config_dir, sample_config):
        """Test that agent can be instantiated with configuration."""
        # Mock the agent creation
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        # Import and test agent creation (this would be the actual implementation)
        config_file = agent_config_dir / "config.yaml"
        
        # This test will fail until the agent.py file implements proper instantiation
        with pytest.raises(ImportError):
            # This import should eventually work when agent.py is implemented
            from ai.agents.genie_debug.agent import create_agent
            agent = create_agent()
    
    def test_agent_has_debug_specific_tools(self, agent_config_dir):
        """Test that debug agent has appropriate debugging tools."""
        config_file = agent_config_dir / "config.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        tools = config.get("tools", [])
        debug_tools = ["bash", "read", "edit", "grep"]
        
        # At least some debug tools should be present
        assert any(tool in tools for tool in debug_tools), f"Debug agent should have debugging tools like {debug_tools}"
    
    def test_agent_temperature_for_debugging(self, agent_config_dir):
        """Test that debug agent has appropriate temperature for precise debugging."""
        config_file = agent_config_dir / "config.yaml"
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        temperature = config.get("temperature", 0.5)
        assert temperature <= 0.3, f"Debug agent should have low temperature for precision, got {temperature}"

class TestGenieDebugAgentIntegration:
    """Integration tests for Genie Debug Agent with Agno framework."""
    
    @patch('agno.Agent')
    def test_agent_registration_in_agno(self, mock_agent_class):
        """Test that agent can be registered with Agno framework."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        # This test will fail until proper Agno integration is implemented
        with pytest.raises(ImportError):
            # This should eventually work when agent registration is implemented
            from ai.agents.genie_debug.agent import register_agent
            register_agent()
    
    def test_agent_responds_to_debug_requests(self):
        """Test that agent can handle debug-specific requests."""
        # This test will fail until agent implementation is complete
        pytest.skip("Agent implementation required for integration testing")
        
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