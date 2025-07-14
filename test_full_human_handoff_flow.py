#!/usr/bin/env python3
"""
Test Full Human Handoff Flow
=============================

Test the complete flow: Ana Team → Human Handoff Agent → WhatsApp MCP
"""

import asyncio
from datetime import datetime
from teams.ana.team import get_ana_team_development


async def test_human_handoff_flow():
    """Test the complete human handoff flow"""
    
    print("🔄 Testing Human Handoff Flow")
    print("=" * 50)
    
    # Initialize Ana team
    ana_team = get_ana_team_development(
        user_id="test_user",
        session_id="test_session_handoff"
    )
    
    # Test human handoff request
    test_message = "quero falar com humano, transfere direto"
    
    print(f"📝 Testing message: {test_message}")
    print("-" * 40)
    
    try:
        # Send to Ana team
        response = ana_team.run(
            message=test_message,
            user_id="test_user",
            session_id="test_session_handoff"
        )
        
        print(f"✅ Ana Response: {response.content}")
        
        # Check if human handoff was detected
        if any(keyword in response.content.lower() for keyword in [
            "transferindo", "atendente", "humano", "protocolo", "transferência"
        ]):
            print("🎯 Human handoff detected!")
            
            # Now test WhatsApp MCP integration
            print("\n📱 Testing WhatsApp MCP Integration...")
            await test_whatsapp_mcp()
            
        else:
            print("❌ Human handoff not detected")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def test_whatsapp_mcp():
    """Test WhatsApp MCP integration"""
    
    # Test the MCP WhatsApp function directly
    try:
        # Test MCP function call
        result = await mcp__send_whatsapp_message__send_text_message(
            instance="pagbank_support",
            message=f"""🚨 TRANSFERÊNCIA PARA ATENDIMENTO HUMANO

📋 Protocolo: PAG{datetime.now().strftime('%Y%m%d%H%M%S')}
👤 Cliente: test_user
🕐 Horário: {datetime.now().strftime('%d/%m/%Y %H:%M')}

❗ Motivo: Solicitação explícita de atendimento humano
💬 Mensagem: quero falar com humano, transfere direto

🎯 Ação: Contatar cliente imediatamente
""",
            delay=1200
        )
        
        print(f"📱 WhatsApp MCP Result: {result}")
        
        if result and result.get('success'):
            print("✅ WhatsApp MCP integration working!")
        else:
            print("❌ WhatsApp MCP integration issue")
            
    except Exception as e:
        print(f"❌ WhatsApp MCP Error: {str(e)}")


# Check if MCP function is available
try:
    from mcp__send_whatsapp_message__send_text_message import mcp__send_whatsapp_message__send_text_message
except ImportError:
    print("⚠️ MCP WhatsApp function not available in this environment")
    
    # Create a mock function for testing
    async def mcp__send_whatsapp_message__send_text_message(instance, message, delay=None):
        """Mock MCP function for testing"""
        return {
            "success": True,
            "message": "Message sent successfully (mock)",
            "instance": instance,
            "delay": delay
        }


if __name__ == "__main__":
    asyncio.run(test_human_handoff_flow())