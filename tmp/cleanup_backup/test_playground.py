#!/usr/bin/env python3
"""
Test PagBank Playground Integration
Quick validation before full deployment
"""

def test_playground_components():
    """Test all playground components work"""
    print("🧪 Testing PagBank Playground Components...")
    
    try:
        # Test orchestrator creation
        from orchestrator.main_orchestrator import create_main_orchestrator
        orchestrator = create_main_orchestrator()
        print("✅ Main orchestrator created successfully")
        
        # Test orchestrator response
        response = orchestrator.process_message(
            message="Olá, preciso de ajuda com meu cartão",
            user_id="test_user",
            session_id="test_session"
        )
        print(f"✅ Orchestrator responded: {str(response)[:100]}...")
        
        # Test playground creation
        from playground import create_pagbank_playground
        playground_app = create_pagbank_playground()
        print("✅ Playground app created successfully")
        
        # Test agent wrapper
        agents = playground_app.agents
        if agents and len(agents) > 0:
            agent = agents[0]
            print(f"✅ Agent wrapper: {agent.name}")
        
        print("\n🎯 All components working - Ready for demo!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_playground_components()
    if success:
        print("\n✅ PagBank Playground: READY FOR DEPLOYMENT")
    else:
        print("\n❌ PagBank Playground: NEEDS FIXES")