#!/usr/bin/env python3
"""
Debug script to test conversation history in routing teams.
Reproduces the issue where conversation history is not maintained across routing operations.
"""

import os
import tempfile
from agno.storage.sqlite import SqliteStorage
from agents.orchestrator.main_orchestrator import create_main_orchestrator

def test_conversation_history():
    """Test conversation history persistence in routing team"""
    
    # Create temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        print("🧪 Testing conversation history in routing team...")
        print(f"📁 Using temporary database: {db_path}")
        
        # Create orchestrator
        orchestrator = create_main_orchestrator()
        
        # Configure storage for the routing team
        team_storage = SqliteStorage(
            table_name="team_sessions", 
            db_file=db_path,
            auto_upgrade_schema=True
        )
        orchestrator.routing_team.storage = team_storage
        
        # Configure shared storage for individual agents
        agent_storage = SqliteStorage(
            table_name="agent_sessions", 
            db_file=db_path,
            auto_upgrade_schema=True
        )
        
        # Configure individual agents with storage
        for agent_name, agent_instance in orchestrator.specialist_agents.items():
            agent_instance.storage = agent_storage
            print(f"   ✓ Configured storage for {agent_name}")
        
        # Configure team with history settings
        orchestrator.routing_team.add_history_to_messages = True
        orchestrator.routing_team.num_history_runs = 5
        
        print("\n📋 Current routing team configuration:")
        print(f"   • Storage: {orchestrator.routing_team.storage is not None}")
        print(f"   • add_history_to_messages: {orchestrator.routing_team.add_history_to_messages}")
        print(f"   • num_history_runs: {orchestrator.routing_team.num_history_runs}")
        print(f"   • Mode: {orchestrator.routing_team.mode}")
        print(f"   • Members: {len(orchestrator.routing_team.members)}")
        
        user_id = "test_user_debug"
        session_id = "test_session_debug"
        
        print("\n🔄 Starting conversation test...")
        
        # Message 1: Investment question (should route to investments agent)
        print("\n1️⃣ First message - Investment question:")
        message1 = "Quero informações sobre CDB"
        print(f"   User: {message1}")
        
        result1 = orchestrator.process_message(
            message=message1,
            user_id=user_id,
            session_id=session_id
        )
        
        print(f"   Response: {result1['response'].content[:100]}...")
        print(f"   Session ID: {result1['session_id']}")
        team_state1 = result1.get('team_session_state')
        if team_state1:
            print(f"   Interaction count: {team_state1.get('interaction_count', 0)}")
        else:
            print("   ❌ team_session_state is None")
        
        # Message 2: Human handoff request (should route to human handoff agent) 
        print("\n2️⃣ Second message - Human handoff:")
        message2 = "Quero falar com um atendente humano"
        print(f"   User: {message2}")
        
        result2 = orchestrator.process_message(
            message=message2,
            user_id=user_id,
            session_id=result1['session_id']  # Use same session
        )
        
        print(f"   Response: {result2['response'].content[:100]}...")
        print(f"   Session ID: {result2['session_id']}")
        team_state2 = result2.get('team_session_state')
        if team_state2:
            print(f"   Interaction count: {team_state2.get('interaction_count', 0)}")
        else:
            print("   ❌ team_session_state is None")
        
        # Message 3: Reference to first message (should show conversation history)
        print("\n3️⃣ Third message - Reference to conversation history:")
        message3 = "Qual foi minha primeira pergunta?"
        print(f"   User: {message3}")
        
        result3 = orchestrator.process_message(
            message=message3,
            user_id=user_id,
            session_id=result2['session_id']  # Use same session
        )
        
        print(f"   Response: {result3['response'].content[:200]}...")
        print(f"   Session ID: {result3['session_id']}")
        team_state3 = result3.get('team_session_state')
        if team_state3:
            print(f"   Interaction count: {team_state3.get('interaction_count', 0)}")
        else:
            print("   ❌ team_session_state is None")
        
        # Check if the routing team has access to conversation history
        print("\n📊 Team session analysis:")
        team_session_state = team_state3 if team_state3 else {}
        print(f"   • Total interactions: {team_session_state.get('interaction_count', 0)}")
        print(f"   • Message history length: {len(team_session_state.get('message_history', []))}")
        print(f"   • Routing history length: {len(team_session_state.get('routing_history', []))}")
        
        # Try to get team history directly
        print("\n🔍 Checking team run history:")
        try:
            team_history = orchestrator.routing_team.get_team_history()
            print(f"   • Team history runs: {len(team_history) if team_history else 0}")
            if team_history:
                for i, run in enumerate(team_history[-3:], 1):  # Show last 3 runs
                    content = getattr(run, 'content', str(run))[:50]
                    print(f"     Run {i}: {content}...")
        except Exception as e:
            print(f"   ❌ Error getting team history: {e}")
        
        # Test: Check if the response actually shows awareness of previous messages
        print("\n🎯 Testing history awareness:")
        if "cdb" in result3['response'].content.lower():
            print("   ✅ Response shows awareness of CDB question")
        else:
            print("   ❌ Response does NOT show awareness of CDB question")
        
        # Check storage directly
        print("\n💾 Direct storage inspection:")
        try:
            # Get all sessions from storage
            all_sessions = team_storage.get_all_sessions()
            print(f"   • Total sessions in storage: {len(all_sessions)}")
            
            # Find our session
            our_session = None
            for session in all_sessions:
                if session.session_id == result3['session_id']:
                    our_session = session
                    break
            
            if our_session:
                messages = our_session.memory.get('messages', [])
                print(f"   • Messages in our session: {len(messages)}")
                for i, msg in enumerate(messages[-5:], 1):  # Show last 5 messages
                    role = getattr(msg, 'role', 'unknown')
                    content = getattr(msg, 'content', str(msg))[:50]
                    print(f"     Message {i} ({role}): {content}...")
            else:
                print("   ❌ Could not find our session in storage")
                
        except Exception as e:
            print(f"   ❌ Error inspecting storage: {e}")
        
        print("\n📋 Analysis Summary:")
        print("=" * 50)
        
        # Check each potential issue
        issues_found = []
        
        if team_state3 is None:
            issues_found.append("❌ team_session_state is None - orchestrator not returning session state")
        elif team_state3.get('interaction_count', 0) < 3:
            issues_found.append("❌ Interaction count not incrementing properly")
        else:
            print("✅ Interaction count is incrementing")
        
        if team_state3 is None or len(team_session_state.get('message_history', [])) == 0:
            issues_found.append("❌ Team session state message_history is empty or unavailable")
        else:
            print("✅ Team session state has message history")
        
        if "cdb" not in result3['response'].content.lower():
            issues_found.append("❌ Final response shows no awareness of first CDB question")
        else:
            print("✅ Final response shows awareness of conversation history")
        
        if not issues_found:
            print("\n🎉 All checks passed! Conversation history is working correctly.")
        else:
            print(f"\n⚠️  Found {len(issues_found)} issues:")
            for issue in issues_found:
                print(f"   {issue}")
        
        return len(issues_found) == 0
        
    finally:
        # Clean up temporary database
        try:
            os.unlink(db_path)
            print(f"\n🧹 Cleaned up temporary database: {db_path}")
        except Exception as e:
            print(f"⚠️  Could not clean up database: {e}")

if __name__ == "__main__":
    success = test_conversation_history()
    exit(0 if success else 1)