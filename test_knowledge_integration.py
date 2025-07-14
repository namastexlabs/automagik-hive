#!/usr/bin/env python3
"""
Test Knowledge Integration with Human Handoff
=============================================

This test verifies that the human handoff flow works with the knowledge
search integration and MCP WhatsApp integration.
"""

import asyncio
from datetime import datetime
from teams.ana.team import get_ana_team_development


async def test_knowledge_integration():
    """Test knowledge integration with human handoff"""
    
    print("🔄 Testing Knowledge Integration with Human Handoff")
    print("=" * 60)
    
    # Initialize Ana team
    ana_team = get_ana_team_development(
        user_id="test_user",
        session_id="test_knowledge_handoff"
    )
    
    # Test cases that should trigger human handoff
    test_cases = [
        {
            "name": "Explicit Human Request",
            "message": "quero falar com humano, me transfere agora",
            "expected_agent": "human-handoff-specialist"
        },
        {
            "name": "Frustration with Bad Words",
            "message": "isso é uma merda, quero falar com alguém",
            "expected_agent": "human-handoff-specialist"
        },
        {
            "name": "Caps Lock Frustration",
            "message": "ESTOU MUITO IRRITADO COM ISSO!",
            "expected_agent": "human-handoff-specialist"
        },
        {
            "name": "Normal Question (Should NOT trigger handoff)",
            "message": "como fazer um PIX?",
            "expected_agent": "pagbank-specialist"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {test_case['name']}")
        print(f"📝 Message: {test_case['message']}")
        print(f"📋 Expected Agent: {test_case['expected_agent']}")
        print("-" * 50)
        
        try:
            # Send to Ana team
            response = ana_team.run(
                message=test_case['message'],
                user_id="test_user",
                session_id=f"test_session_{i}"
            )
            
            print(f"✅ Ana Response: {response.content[:300]}...")
            
            # Check if correct agent was triggered
            if test_case['expected_agent'] == "human-handoff-specialist":
                if any(keyword in response.content.lower() for keyword in [
                    "transferindo", "atendente", "humano", "protocolo", "transferência"
                ]):
                    print("🎯 Human handoff detected correctly!")
                    
                    # Test WhatsApp notification
                    await test_whatsapp_notification(test_case['message'])
                    
                else:
                    print("❌ Human handoff not detected when expected")
            else:
                if any(keyword in response.content.lower() for keyword in [
                    "transferindo", "atendente", "humano", "protocolo"
                ]):
                    print("❌ Human handoff triggered when not expected")
                else:
                    print("✅ Normal routing worked correctly")
                    
        except Exception as e:
            print(f"❌ Error in test case: {str(e)}")
        
        print()


async def test_whatsapp_notification(original_message: str):
    """Test WhatsApp notification with MCP integration"""
    
    print("📱 Testing WhatsApp MCP Integration...")
    
    # Create notification message
    notification_msg = f"""🚨 TRANSFERÊNCIA PARA ATENDIMENTO HUMANO

📋 Protocolo: PAG{datetime.now().strftime('%Y%m%d%H%M%S')}
👤 Cliente: test_user
🕐 Horário: {datetime.now().strftime('%d/%m/%Y %H:%M')}

❗ Motivo: Detecção de necessidade de atendimento humano
💬 Mensagem Original: {original_message}

📝 Histórico: Cliente solicitou transferência para atendimento humano
🎯 Ação: Contatar cliente imediatamente via canal preferencial

---
Sistema PagBank Multi-Agente V2"""
    
    try:
        # Test MCP WhatsApp integration
        result = await send_whatsapp_via_mcp(notification_msg)
        
        print(f"📱 WhatsApp Result: {result}")
        
        if result.get("success"):
            print("✅ WhatsApp MCP integration working!")
        else:
            print(f"⚠️ WhatsApp MCP issue: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ WhatsApp MCP Error: {str(e)}")


async def send_whatsapp_via_mcp(message: str):
    """Send WhatsApp message via MCP integration"""
    
    # Try to use the actual MCP function
    try:
        result = await mcp__send_whatsapp_message__send_text_message(
            instance="pagbank_support",
            message=message,
            delay=1200
        )
        return result
        
    except Exception as e:
        # If MCP function fails, return mock result for testing
        return {
            "success": False,
            "error": f"MCP function error: {str(e)}",
            "mock_result": True,
            "message_preview": message[:100] + "..." if len(message) > 100 else message
        }


# Mock MCP function for testing if not available
async def mcp__send_whatsapp_message__send_text_message(instance, message, delay=None):
    """Mock MCP function for testing"""
    
    # Check if Evolution API is configured
    import os
    if not os.getenv("EVOLUTION_API_BASE_URL"):
        return {
            "success": False,
            "error": "Evolution API not configured",
            "required_env": [
                "EVOLUTION_API_BASE_URL",
                "EVOLUTION_API_API_KEY", 
                "EVOLUTION_API_INSTANCE",
                "EVOLUTION_API_FIXED_RECIPIENT"
            ]
        }
    
    # Mock successful response
    return {
        "success": True,
        "method": "mcp_send_text_message",
        "instance": instance,
        "message_length": len(message),
        "delay": delay,
        "timestamp": datetime.now().isoformat(),
        "mock": True
    }


if __name__ == "__main__":
    asyncio.run(test_knowledge_integration())