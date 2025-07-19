#!/usr/bin/env python3
"""
Extract all parameters for Agent, Team, and Workflow classes
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def get_all_parameters():
    """Get all parameters for each Agno component type."""
    
    try:
        from lib.utils.agno_proxy import get_agno_proxy, get_agno_team_proxy, get_agno_workflow_proxy
        
        print("🔍 Extracting ALL Agno Parameters...")
        print("=" * 60)
        
        # Agent Parameters
        agent_proxy = get_agno_proxy()
        agent_params = sorted(list(agent_proxy.get_supported_parameters()))
        
        print(f"\n🤖 AGENT PARAMETERS ({len(agent_params)} total):")
        print("-" * 40)
        for i, param in enumerate(agent_params, 1):
            print(f"{i:2d}. {param}")
        
        # Team Parameters
        team_proxy = get_agno_team_proxy()
        team_params = sorted(list(team_proxy.get_supported_parameters()))
        
        print(f"\n👥 TEAM PARAMETERS ({len(team_params)} total):")
        print("-" * 40)
        for i, param in enumerate(team_params, 1):
            print(f"{i:2d}. {param}")
        
        # Workflow Parameters
        workflow_proxy = get_agno_workflow_proxy()
        workflow_params = sorted(list(workflow_proxy.get_supported_parameters()))
        
        print(f"\n🔄 WORKFLOW PARAMETERS ({len(workflow_params)} total):")
        print("-" * 40)
        for i, param in enumerate(workflow_params, 1):
            print(f"{i:2d}. {param}")
        
        # Summary
        print(f"\n📊 SUMMARY:")
        print(f"   Agent:    {len(agent_params)} parameters")
        print(f"   Team:     {len(team_params)} parameters")
        print(f"   Workflow: {len(workflow_params)} parameters")
        print(f"   Total:    {len(agent_params) + len(team_params) + len(workflow_params)} parameters")
        
        # Return for template generation
        return {
            "agent": agent_params,
            "team": team_params,
            "workflow": workflow_params
        }
        
    except Exception as e:
        print(f"❌ Error getting parameters: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    get_all_parameters()