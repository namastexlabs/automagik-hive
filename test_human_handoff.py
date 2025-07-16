#!/usr/bin/env python3
"""
Test script for Human Handoff Agent
Tests the complete human handoff workflow including WhatsApp integration
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents.human_handoff.agent import get_human_handoff_agent
from workflows.human_handoff.workflow import get_human_handoff_workflow


async def test_human_handoff_agent():
    """Test the human handoff agent functionality"""
    print("🧪 Testing Human Handoff Agent...")
    
    # Test 1: Agent Creation
    print("\n1. Creating Human Handoff Agent...")
    try:
        agent = get_human_handoff_agent(
            session_id="test-session-001",
            debug_mode=True,
            user_name="João Silva",
            phone_number="11987654321",
            cpf="12345678901"
        )
        print("✅ Agent created successfully")
        print(f"   - Agent ID: {agent.agent_id}")
        print(f"   - Agent Name: {agent.name}")
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return False
    
    # Test 2: Agent Response
    print("\n2. Testing Agent Response...")
    try:
        test_message = "Estou muito frustrado! Quero falar com uma pessoa real agora!"
        print(f"   - Sending message: {test_message}")
        
        response = agent.run(test_message)
        print("✅ Agent responded successfully")
        print(f"   - Response: {response.content[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Agent response failed: {e}")
        return False


async def test_human_handoff_workflow():
    """Test the human handoff workflow directly"""
    print("\n🧪 Testing Human Handoff Workflow...")
    
    # Test 1: Workflow Creation
    print("\n1. Creating Human Handoff Workflow...")
    try:
        workflow = get_human_handoff_workflow(
            whatsapp_enabled=True,
            whatsapp_instance="SofIA"
        )
        print("✅ Workflow created successfully")
        print(f"   - WhatsApp enabled: {workflow.whatsapp_enabled}")
        print(f"   - WhatsApp instance: {workflow.whatsapp_instance}")
    except Exception as e:
        print(f"❌ Workflow creation failed: {e}")
        return False
    
    # Test 2: Workflow Execution
    print("\n2. Testing Workflow Execution...")
    try:
        # Test parameters
        test_params = {
            "customer_message": "Preciso de ajuda humana urgente!",
            "escalation_reason": "frustration_detected",
            "conversation_history": "Cliente tentou resolver o problema sozinho várias vezes",
            "urgency_level": "high",
            "business_unit": "pagbank",
            "session_id": "test-session-workflow-001",
            "user_name": "Maria Santos",
            "phone_number": "11999887766",
            "cpf": "98765432100"
        }
        
        print(f"   - Testing parameters: {test_params}")
        
        # Execute workflow async
        results = []
        async for result in workflow.arun(**test_params):
            results.append(result)
        
        print("✅ Workflow executed successfully")
        print(f"   - Results count: {len(results)}")
        
        if results:
            final_result = results[-1]
            print(f"   - Final result type: {type(final_result)}")
            if hasattr(final_result, 'content'):
                print(f"   - Final content: {str(final_result.content)[:200]}...")
        
        return True
    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_whatsapp_integration():
    """Test WhatsApp integration directly"""
    print("\n🧪 Testing WhatsApp Integration...")
    
    try:
        from workflows.shared.whatsapp_notification import get_whatsapp_notification_service
        
        # Test notification service
        whatsapp_service = get_whatsapp_notification_service(debug_mode=True)
        
        # Test handoff notification
        handoff_data = {
            "protocol_id": "TEST-PROTOCOL-001",
            "escalation_analysis": {
                "urgency_level": "high",
                "customer_emotion": "frustrated",
                "escalation_reason": "explicit_request"
            }
        }
        
        result = await whatsapp_service.send_human_handoff_notification(handoff_data)
        
        if result["success"]:
            print("✅ WhatsApp notification sent successfully")
            print(f"   - Result: {result}")
        else:
            print("❌ WhatsApp notification failed")
            print(f"   - Error: {result.get('error', 'Unknown error')}")
        
        return result["success"]
    
    except Exception as e:
        print(f"❌ WhatsApp integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting Human Handoff Agent Tests")
    print("=" * 50)
    
    # Test results
    results = []
    
    # Test 1: Agent functionality
    agent_result = await test_human_handoff_agent()
    results.append(("Human Handoff Agent", agent_result))
    
    # Test 2: Workflow functionality
    workflow_result = await test_human_handoff_workflow()
    results.append(("Human Handoff Workflow", workflow_result))
    
    # Test 3: WhatsApp integration
    whatsapp_result = await test_whatsapp_integration()
    results.append(("WhatsApp Integration", whatsapp_result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<25} {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("🎉 All tests passed! Human handoff system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the logs above.")


if __name__ == "__main__":
    asyncio.run(main())