#!/usr/bin/env python3
"""
Test script to verify user data parameter passing from CLI to workflow execution
"""

import asyncio
import sys
import os
sys.path.append(os.path.abspath('.'))

from workflows.human_handoff.workflow import get_human_handoff_workflow
from agents.tools.workflow_tools import trigger_human_handoff_workflow


async def test_workflow_direct():
    """Test workflow execution with user data parameters - direct call"""
    print("=== Testing Workflow Direct Call ===")
    
    # Test data
    user_data = {
        "user_id": "test_user_123",
        "user_name": "João Silva",
        "phone_number": "11999999999",
        "cpf": "12345678901"
    }
    
    # Create workflow instance
    workflow = get_human_handoff_workflow(
        whatsapp_enabled=False,  # Disable WhatsApp for testing
        whatsapp_instance="test"
    )
    
    print(f"🧪 Testing with user data: {user_data}")
    
    # Execute workflow with user data
    results = []
    async for result in workflow.arun(
        customer_message="Preciso de ajuda com minha conta",
        escalation_reason="test_escalation",
        conversation_history="Cliente relatou problema com PIX",
        urgency_level="high",
        business_unit="pagbank",
        session_id="test_session_123",
        customer_id="test_customer_456",
        **user_data  # Pass user data parameters
    ):
        results.append(result)
        print(f"✅ Result: {result.content[:100]}...")
    
    # Verify user data was processed
    final_result = results[-1] if results else None
    if final_result and final_result.content:
        content = final_result.content
        if "João Silva" in content or "11999999999" in content:
            print("✅ SUCCESS: User data was properly passed to workflow!")
            return True
        else:
            print("❌ FAILED: User data not found in workflow output")
            print(f"Content: {content}")
            return False
    else:
        print("❌ FAILED: No workflow result received")
        return False


def test_workflow_tool():
    """Test workflow tool with user data parameters"""
    print("\n=== Testing Workflow Tool Call ===")
    
    # Test data
    user_data = {
        "user_id": "test_user_456",
        "user_name": "Maria Santos",
        "phone_number": "11888888888",
        "cpf": "98765432100"
    }
    
    print(f"🧪 Testing tool with user data: {user_data}")
    
    # Call workflow tool with user data
    result = trigger_human_handoff_workflow(
        customer_message="Estou com problema no cartão",
        escalation_reason="test_tool_escalation",
        conversation_history="Cliente mencionou problema com limite",
        urgency_level="medium",
        business_unit="emissao",
        session_id="test_session_456",
        customer_id="test_customer_789",
        **user_data  # Pass user data parameters
    )
    
    print(f"✅ Tool result: {result[:100]}...")
    
    # Verify user data was processed
    if "Maria Santos" in result or "11888888888" in result:
        print("✅ SUCCESS: User data was properly passed to workflow tool!")
        return True
    else:
        print("❌ FAILED: User data not found in tool output")
        print(f"Result: {result}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Testing User Data Parameter Passing - End-to-End")
    print("=" * 60)
    
    # Test 1: Direct workflow call
    test1_passed = await test_workflow_direct()
    
    # Test 2: Workflow tool call
    test2_passed = test_workflow_tool()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY:")
    print(f"✅ Direct workflow call: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Workflow tool call: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! User data parameter passing is working correctly.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)