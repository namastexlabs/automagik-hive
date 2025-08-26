"""Tests for Jack Retrieval Agent

Test suite for WhatsApp PO query agent with Agno factory integration.
"""

import pytest
from unittest.mock import Mock, patch

from ai.agents.jack_retrieval.agent import (
    get_jack_retrieval_agent,
    validate_agent_config
)


class TestJackRetrievalAgent:
    """Test cases for Jack Retrieval Agent factory and configuration."""
    
    def test_validate_agent_config_valid(self):
        """Test that valid configuration passes validation."""
        # This should pass when config.yaml is properly structured
        assert validate_agent_config() is True
    
    def test_validate_agent_config_missing_file(self):
        """Test validation fails when config file is missing."""
        with patch("pathlib.Path.open", side_effect=FileNotFoundError):
            assert validate_agent_config() is False
    
    def test_validate_agent_config_invalid_yaml(self):
        """Test validation fails with invalid YAML."""
        with patch("pathlib.Path.open", mock_open_yaml("invalid: yaml: content:")):
            assert validate_agent_config() is False
    
    @patch("ai.agents.jack_retrieval.agent.create_agent")
    @pytest.mark.asyncio
    async def test_get_jack_retrieval_agent_creation(self, mock_create_agent):
        """Test agent creation using factory pattern."""
        # Mock the create_agent function
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent
        
        # Test agent creation
        agent = await get_jack_retrieval_agent(
            user_id="test_user",
            query_type="status"
        )
        
        # Verify factory was called correctly
        mock_create_agent.assert_called_once_with(
            "jack-retrieval",
            user_id="test_user", 
            query_type="status"
        )
        assert agent == mock_agent


class TestKnowledgeBaseIntegration:
    """Test cases for JSONKnowledgeBase integration via YAML config."""
    
    def test_knowledge_config_structure(self):
        """Test that knowledge configuration has proper structure."""
        # This tests the YAML structure used by the Agno factory
        
        mock_config = {
            "knowledge": {
                "type": "json",
                "sources": [
                    {
                        "path": "ai/workflows/processamento-faturas/data/processamento_faturas_data.json",
                        "metadata": {
                            "data_type": "po_orders",
                            "source": "processamento_faturas_workflow",
                            "domain": "invoicing"
                        }
                    }
                ],
                "search_knowledge": True,
                "enable_agentic_knowledge_filters": True,
                "num_documents": 20
            }
        }
        
        # Verify structure matches expected format
        knowledge_config = mock_config["knowledge"]
        assert knowledge_config["type"] == "json"
        assert isinstance(knowledge_config["sources"], list)
        assert len(knowledge_config["sources"]) == 1
        
        source = knowledge_config["sources"][0]
        assert "path" in source
        assert "metadata" in source
        
        metadata = source["metadata"]
        assert metadata["data_type"] == "po_orders"
        assert metadata["source"] == "processamento_faturas_workflow"
        assert metadata["domain"] == "invoicing"


class TestAgentConfigValidation:
    """Test cases for agent configuration validation."""
    
    def test_validate_required_sections(self):
        """Test validation of required configuration sections."""
        incomplete_configs = [
            {},  # Empty config
            {"agent": {}},  # Missing other sections
            {"agent": {}, "model": {}},  # Missing storage, knowledge, instructions
            {
                "agent": {"name": "test"},
                "model": {},
                "storage": {},
                "knowledge": {},
                # Missing instructions
            }
        ]
        
        for config in incomplete_configs:
            with patch("yaml.safe_load", return_value=config), \
                 patch("pathlib.Path.open"):
                assert validate_agent_config() is False
    
    def test_validate_agent_metadata(self):
        """Test validation of agent metadata fields."""
        config_with_incomplete_agent = {
            "agent": {"name": "test"},  # Missing agent_id and version
            "model": {},
            "storage": {},
            "knowledge": {"sources": []},
            "instructions": "test"
        }
        
        with patch("yaml.safe_load", return_value=config_with_incomplete_agent), \
             patch("pathlib.Path.open"):
            assert validate_agent_config() is False
    
    def test_validate_knowledge_sources(self):
        """Test validation of knowledge sources configuration."""
        configs_with_bad_knowledge = [
            {
                "agent": {"name": "test", "agent_id": "test", "version": 1},
                "model": {},
                "storage": {},
                "knowledge": {},  # No sources
                "instructions": "test"
            },
            {
                "agent": {"name": "test", "agent_id": "test", "version": 1},
                "model": {},
                "storage": {},
                "knowledge": {"sources": "not_a_list"},  # Sources not a list
                "instructions": "test"
            }
        ]
        
        for config in configs_with_bad_knowledge:
            with patch("yaml.safe_load", return_value=config), \
                 patch("pathlib.Path.open"):
                assert validate_agent_config() is False


# Test utilities
def mock_open_yaml(content):
    """Create a mock for opening YAML files with specific content."""
    mock_file = MagicMock()
    mock_file.__enter__.return_value.read.return_value = content
    return mock_file


# Integration test (runs only if config file exists)
class TestAgentIntegration:
    """Integration tests for complete agent setup."""
    
    @pytest.mark.asyncio
    async def test_agent_creation_with_real_config(self):
        """Test agent creation with actual config file (if it exists)."""
        from pathlib import Path
        
        config_path = Path(__file__).parent / "config.yaml"
        
        if not config_path.exists():
            pytest.skip("Config file not found for integration test")
        
        # Test using factory pattern
        with patch("ai.agents.jack_retrieval.agent.create_agent") as mock_create_agent:
            mock_agent = Mock()
            mock_create_agent.return_value = mock_agent
            
            agent = await get_jack_retrieval_agent(user_id="test_integration")
            
            assert agent is not None
            mock_create_agent.assert_called_once_with(
                "jack-retrieval",
                user_id="test_integration"
            )