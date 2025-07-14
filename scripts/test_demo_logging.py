#!/usr/bin/env python3
"""
Test script for enhanced typification workflow demo logging.
Run this to see the detailed logging in action for demo purposes.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.conversation_typification.workflow import get_conversation_typification_workflow
from agno.utils.log import logger

def test_demo_logging():
    """Test the enhanced demo logging functionality"""
    
    print("🎯 Testing Enhanced Typification Workflow Demo Logging")
    print("=" * 60)
    
    # Sample conversation for testing
    sample_conversation = """
    Cliente: Olá, estou com problemas no meu cartão PagBank
    Ana: Olá! Posso te ajudar com seu cartão. Qual é o problema específico?
    Cliente: O cartão não está passando nas máquinas, diz que está bloqueado
    Ana: Vou verificar o status do seu cartão. Pode me informar os últimos 4 dígitos?
    Cliente: 1234
    Ana: Identifiquei que seu cartão está temporariamente bloqueado por segurança. 
    Vou desbloqueá-lo agora. Aguarde um momento...
    Ana: Pronto! Seu cartão já está desbloqueado. Pode tentar usar novamente.
    Cliente: Muito obrigado! Funcionou perfeitamente.
    """
    
    # Create workflow with demo logging enabled
    workflow = get_conversation_typification_workflow(debug_mode=True)
    
    print(f"🚀 Starting typification workflow test...")
    print(f"📝 Sample conversation: {len(sample_conversation)} characters")
    print(f"🔧 Debug: {os.getenv('DEBUG')}, 🎬 Demo: {os.getenv('DEMO_MODE')}")
    print()
    
    try:
        # Run the workflow
        results = list(workflow.run(
            session_id="DEMO-001",
            conversation_history=sample_conversation,
            customer_id="customer-123",
            metadata={"demo": True, "test_case": "card_unblock"}
        ))
        
        print("\n" + "=" * 60)
        print("✅ DEMO TEST COMPLETED SUCCESSFULLY")
        print(f"📊 Results: {len(results)} workflow events")
        
        if results:
            final_result = results[-1]
            if hasattr(final_result, 'content') and isinstance(final_result.content, dict):
                if 'typification' in final_result.content:
                    typification = final_result.content['typification']
                    print(f"🎯 Final Classification: {typification.get('hierarchy_path', 'N/A')}")
                    print(f"📈 Confidence Scores: {final_result.content.get('confidence_scores', {})}")
                    print(f"⏱️  Resolution Time: {final_result.content.get('resolution_time_minutes', 0):.2f} minutes")
                
    except Exception as e:
        print(f"❌ DEMO TEST FAILED: {str(e)}")
        logger.error(f"Demo test error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🎬 PagBank V2 Typification Workflow - Demo Logging Test")
    print("This script demonstrates the enhanced logging features.")
    print()
    
    success = test_demo_logging()
    
    if success:
        print("\n🎉 Demo logging test completed successfully!")
        print("💡 You can now see detailed enum selections, agent reasoning, and tool interactions")
        print("📋 Use this logging in your demos to show how the AI workflow operates under the hood")
    else:
        print("\n💥 Demo test failed - check the logs above")
        sys.exit(1)