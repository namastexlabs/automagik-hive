#!/usr/bin/env python3
"""
Test User Context Forwarding Flow
=================================

This script tests the end-to-end user context forwarding from API to Team to Agent.
Tests the fixed bug where team wasn't passing user context to member agents.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")


async def test_user_context_forwarding():
    """Test that user context flows from Team to Member Agents correctly."""
    
    print("🧪 Testing User Context Forwarding Flow")
    print("=" * 50)
    
    try:
        # Import necessary components
        from teams.ana.team import get_ana_team
        from context.user_context_helper import create_user_context_state
        
        print("✅ Imports successful")
        
        # Create test user context data
        test_user_data = {
            "user_id": "test_user_123",
            "user_name": "João da Silva",
            "phone_number": "5511999999999",
            "cpf": "12345678901"
        }
        
        print(f"📝 Test user data: {test_user_data}")
        
        # Create user context state
        user_context_state = create_user_context_state(**test_user_data)
        print(f"✅ User context state created: {user_context_state}")
        
        # Create Ana team with user context
        print("🏗️ Creating Ana team with user context...")
        ana_team = get_ana_team(
            session_id="test_session_123",
            debug_mode=True,
            **test_user_data  # Pass user context parameters
        )
        
        print(f"✅ Ana team created: {ana_team.name}")
        print(f"📋 Team ID: {ana_team.team_id}")
        print(f"👥 Team members: {len(ana_team.members)}")
        
        # Check if team has user context in session_state
        if hasattr(ana_team, 'session_state') and ana_team.session_state:
            team_user_context = ana_team.session_state.get('user_context', {})
            print(f"🔍 Team session_state user_context: {team_user_context}")
            
            if team_user_context:
                print("✅ Team has user context in session_state")
            else:
                print("❌ Team missing user context in session_state")
        else:
            print("❌ Team has no session_state")
        
        # Check member agents for user context
        print("\n🔍 Checking member agents for user context...")
        for i, member in enumerate(ana_team.members):
            member_name = getattr(member, 'name', f'Member {i}')
            member_agent_id = getattr(member, 'agent_id', 'unknown')
            
            print(f"  👤 Agent: {member_name} (ID: {member_agent_id})")
            
            # Check if member has session_state with user context
            if hasattr(member, 'session_state') and member.session_state:
                member_user_context = member.session_state.get('user_context', {})
                if member_user_context:
                    print(f"    ✅ Has user context: {list(member_user_context.keys())}")
                    
                    # Verify specific fields
                    for field in ['user_id', 'user_name', 'phone_number', 'cpf']:
                        if field in member_user_context:
                            print(f"      ✓ {field}: {member_user_context[field]}")
                        else:
                            print(f"      ❌ Missing {field}")
                else:
                    print(f"    ❌ No user context in session_state")
            else:
                print(f"    ❌ No session_state")
        
        print("\n🎯 Testing team routing with user context...")
        
        # Test a simple query that should route to an agent
        test_query = "Olá, preciso de ajuda com minha conta PagBank"
        
        try:
            # Run the team with the test query
            result = await ana_team.arun(test_query)
            
            if result:
                print("✅ Team routing successful")
                print(f"📄 Response content preview: {str(result.content)[:200]}...")
                
                # Check if the response mentions user context
                if any(field in str(result.content) for field in test_user_data.values()):
                    print("✅ Response includes user context data")
                else:
                    print("⚠️ Response doesn't seem to include user context data")
                    
            else:
                print("❌ Team routing failed - no result")
                
        except Exception as e:
            print(f"❌ Team routing error: {str(e)}")
            
        print("\n" + "=" * 50)
        print("🏁 User Context Flow Test Complete")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_user_context_forwarding())