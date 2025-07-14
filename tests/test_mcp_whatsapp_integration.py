"""
Test MCP WhatsApp Integration
============================

Tests for the MCP WhatsApp integration to ensure proper removal of native tools
and successful integration with the dedicated WhatsApp notifier agent.
"""

import pytest
import os
from unittest.mock import patch, AsyncMock
from agents.whatsapp_notifier.agent import WhatsAppNotifierAgent, get_whatsapp_notifier
from workflows.human_handoff.workflow import HumanHandoffWorkflow
from workflows.human_handoff.models import ConversationContext


class TestMCPWhatsAppIntegration:
    """Test suite for MCP WhatsApp integration"""
    
    @pytest.fixture
    def mock_environment(self):
        """Mock environment variables for testing"""
        with patch.dict(os.environ, {
            'EVOLUTION_API_BASE_URL': 'http://192.168.112.142:8080',
            'EVOLUTION_API_API_KEY': 'BEE0266C2040-4D83-8FAA-A9A3EF89DDEF',
            'EVOLUTION_API_INSTANCE': 'SofIA',
            'EVOLUTION_API_FIXED_RECIPIENT': '5511986780008@s.whatsapp.net'
        }):
            yield
    
    @pytest.mark.asyncio
    async def test_whatsapp_notifier_initialization(self, mock_environment):
        """Test WhatsApp notifier agent initialization"""
        notifier = WhatsAppNotifierAgent("test_instance")
        result = await notifier.initialize()
        
        assert result is True
        assert notifier._mcp_available is True
        assert notifier.agent is not None
        assert notifier.instance == "test_instance"
    
    @pytest.mark.asyncio
    async def test_whatsapp_notifier_send_message(self, mock_environment):
        """Test sending WhatsApp message via MCP agent"""
        notifier = WhatsAppNotifierAgent("test_instance")
        await notifier.initialize()
        
        result = await notifier.send_message(
            message="Test escalation message",
            number="+5511999999999"
        )
        
        assert result["success"] is True
        assert result["method"] == "mcp_send_text_message"
        assert result["instance"] == "test_instance"
        assert result["number"] == "+5511999999999"
        assert result["message_length"] == len("Test escalation message")
    
    @pytest.mark.asyncio
    async def test_whatsapp_notifier_with_fixed_recipient(self, mock_environment):
        """Test sending message with fixed recipient (no number parameter)"""
        notifier = WhatsAppNotifierAgent("test_instance")
        await notifier.initialize()
        
        result = await notifier.send_message(
            message="Test message with fixed recipient"
        )
        
        assert result["success"] is True
        assert result["number"] == "5511986780008@s.whatsapp.net"
    
    @pytest.mark.asyncio
    async def test_whatsapp_notifier_environment_check(self):
        """Test environment variable validation"""
        # Test without environment variables
        notifier = WhatsAppNotifierAgent("test_instance")
        result = await notifier.initialize()
        
        assert result is False
        
        # Test with partial environment
        with patch.dict(os.environ, {'EVOLUTION_API_BASE_URL': 'test'}, clear=True):
            notifier = WhatsAppNotifierAgent("test_instance")
            result = await notifier.initialize()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_whatsapp_notifier_singleton(self, mock_environment):
        """Test singleton pattern for WhatsApp notifier"""
        notifier1 = await get_whatsapp_notifier("test_instance")
        notifier2 = await get_whatsapp_notifier("test_instance")
        
        # Should return the same instance
        assert notifier1 is notifier2
        assert notifier1._mcp_available is True
    
    @pytest.mark.asyncio
    async def test_notification_formatting(self, mock_environment):
        """Test structured notification formatting"""
        notifier = WhatsAppNotifierAgent("test_instance")
        await notifier.initialize()
        
        result = await notifier.send_notification(
            protocol_id="ESC-TEST-20250714123456",
            customer_name="João Silva",
            urgency="HIGH",
            description="Problema com PIX não funcionando",
            target_number="+5511999999999"
        )
        
        assert result["success"] is True
        assert result["number"] == "+5511999999999"
        # The message should be formatted as a structured notification
        assert "message_length" in result
        assert result["message_length"] > 0
    
    def test_native_whatsapp_tools_removed(self):
        """Test that native WhatsApp tools have been removed"""
        from agents.tools.agent_tools import AGENT_TOOLS, get_agent_tools
        
        # WhatsApp should not be in the tool registry
        assert "whatsapp" not in AGENT_TOOLS
        
        # Human handoff agent should not have native WhatsApp tools
        human_handoff_tools = get_agent_tools("human_handoff")
        
        # Should not contain the old send_whatsapp_message function
        tool_names = [getattr(tool, '__name__', str(tool)) for tool in human_handoff_tools]
        assert "send_whatsapp_message" not in tool_names
    
    @pytest.mark.asyncio
    async def test_human_handoff_workflow_mcp_integration(self, mock_environment):
        """Test human handoff workflow uses MCP WhatsApp agent"""
        workflow = HumanHandoffWorkflow(
            debug_mode=True,
            whatsapp_enabled=True,
            whatsapp_instance="test_instance"
        )
        
        # Test the MCP agent method
        result = await workflow._send_via_mcp_agent(
            message="Test escalation notification",
            target_phone="+5511999999999"
        )
        
        assert result["success"] is True
        assert "mcp" in result.get("method", "")
    
    def test_mcp_environment_detection(self, mock_environment):
        """Test MCP environment detection"""
        workflow = HumanHandoffWorkflow(
            debug_mode=True,
            whatsapp_enabled=True
        )
        
        # Test MCP availability check
        result = workflow._test_mcp_availability()
        assert result is True
        
        # Test without environment
        with patch.dict(os.environ, {}, clear=True):
            workflow = HumanHandoffWorkflow(debug_mode=True)
            result = workflow._test_mcp_availability()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_environment):
        """Test error handling in MCP integration"""
        notifier = WhatsAppNotifierAgent("test_instance")
        
        # Test without initialization
        result = await notifier.send_message("Test message")
        assert result["success"] is False
        assert "not initialized" in result["error"]
        
        # Initialize and test error in send
        await notifier.initialize()
        
        # Mock an error in the MCP call
        with patch.object(notifier, '_call_mcp_whatsapp', side_effect=Exception("MCP error")):
            result = await notifier.send_message("Test message")
            assert result["success"] is False
            assert "MCP error" in result["error"]
    
    def test_configuration_files(self):
        """Test that configuration files are properly updated"""
        import yaml
        from pathlib import Path
        
        # Test WhatsApp notifier config
        config_path = Path(__file__).parent.parent / "agents" / "whatsapp_notifier" / "config.yaml"
        assert config_path.exists()
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        assert config["agent"]["agent_id"] == "whatsapp-notifier"
        assert "WhatsApp" in config["agent"]["name"]
        
        # Test human handoff config update
        hh_config_path = Path(__file__).parent.parent / "agents" / "human_handoff" / "config.yaml"
        if hh_config_path.exists():
            with open(hh_config_path) as f:
                hh_config = yaml.safe_load(f)
            
            assert hh_config["whatsapp"]["enabled"] is True
            assert hh_config["whatsapp"]["agent"] == "whatsapp-notifier"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])