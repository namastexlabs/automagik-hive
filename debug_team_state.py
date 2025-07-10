#!/usr/bin/env python3
"""
Debug script to investigate team_session_state issue
"""

import os
import tempfile
from agno.storage.sqlite import SqliteStorage
from agents.orchestrator.main_orchestrator import create_main_orchestrator

def debug_team_state():
    """Debug team session state initialization and handling"""
    
    # Create temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        print("🔍 Debugging team session state...")
        
        # Create orchestrator
        orchestrator = create_main_orchestrator()
        
        # Configure storage
        team_storage = SqliteStorage(
            table_name="team_sessions", 
            db_file=db_path,
            auto_upgrade_schema=True
        )
        orchestrator.routing_team.storage = team_storage
        
        print(f"\n📋 Team initialization state:")
        print(f"   • initial_session_state type: {type(orchestrator.initial_session_state)}")
        print(f"   • initial_session_state content: {list(orchestrator.initial_session_state.keys())}")
        print(f"   • routing_team.team_session_state type: {type(orchestrator.routing_team.team_session_state)}")
        
        if orchestrator.routing_team.team_session_state:
            print(f"   • routing_team.team_session_state keys: {list(orchestrator.routing_team.team_session_state.keys())}")
            print(f"   • interaction_count: {orchestrator.routing_team.team_session_state.get('interaction_count', 'NOT_FOUND')}")
        else:
            print("   ❌ routing_team.team_session_state is None!")
        
        # Test a message
        print(f"\n🧪 Testing message processing...")
        
        # Before processing
        print(f"Before processing:")
        print(f"   • team_session_state: {orchestrator.routing_team.team_session_state is not None}")
        
        result = orchestrator.process_message(
            message="Test message",
            user_id="debug_user",
            session_id="debug_session"
        )
        
        # After processing
        print(f"\nAfter processing:")
        print(f"   • team_session_state in result: {result.get('team_session_state') is not None}")
        print(f"   • team_session_state on team: {orchestrator.routing_team.team_session_state is not None}")
        
        if result.get('team_session_state'):
            state = result['team_session_state']
            print(f"   • returned state keys: {list(state.keys())}")
            print(f"   • interaction_count: {state.get('interaction_count', 'NOT_FOUND')}")
        
        if orchestrator.routing_team.team_session_state:
            state = orchestrator.routing_team.team_session_state
            print(f"   • team state keys: {list(state.keys())}")
            print(f"   • interaction_count: {state.get('interaction_count', 'NOT_FOUND')}")
        
        # Let's also check the memory manager result
        print(f"\n💾 Memory manager details:")
        print(f"   • session_id: {result.get('session_id')}")
        print(f"   • insights: {result.get('insights', 'None')}")
        
        # Check if update_session is being called
        print(f"\n🔄 Testing update_session method:")
        try:
            update_result = orchestrator.update_session({'current_topic': 'test'})
            print(f"   • update_session result: {update_result}")
            print(f"   • team_session_state after update: {orchestrator.routing_team.team_session_state is not None}")
        except Exception as e:
            print(f"   ❌ Error in update_session: {e}")
        
        return True
        
    finally:
        # Clean up
        try:
            os.unlink(db_path)
        except:
            pass

if __name__ == "__main__":
    debug_team_state()