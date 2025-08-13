#!/usr/bin/env python3
"""
Travel Planning Example using the SkyPlanner Team.

This example demonstrates how to use the automagik-store's travel planning
agents and team to create a comprehensive travel itinerary.

Prerequisites:
- Set GOOGLE_MAPS_API_KEY environment variable
- Set APIFY_TOKEN environment variable
- Set OPENAI_API_KEY or ANTHROPIC_API_KEY
- Ensure PostgreSQL is running (for agent memory)
"""

import asyncio
import os
import sys
from pathlib import Path
from textwrap import dedent

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.teams.skyplanner_team.team import get_skyplanner_team


async def plan_trip():
    """Run the SkyPlanner team to plan a trip."""
    
    # Verify required environment variables
    required_vars = ["OPENAI_API_KEY", "GOOGLE_MAPS_API_KEY", "APIFY_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these in your .env file or environment.")
        return
    
    print("🚀 Initializing SkyPlanner Travel Team...")
    print("-" * 50)
    
    # Create the team
    team = get_skyplanner_team(
        debug_mode=True,
        user_id="travel_demo_user",
        session_id="demo_session_001"
    )
    
    # Define the travel request
    travel_request = dedent("""
        I want to travel to San Francisco from New York sometime in May.
        I am one person going for 2 weeks.
        
        Please plan my travel itinerary including:
        - Best Airbnb listings within reasonable budget
        - Must-see attractions and hidden gems
        - Restaurant recommendations
        - Weather forecast and what to pack
        - Suggested daily itinerary
        
        My interests include:
        - Technology and startups (would love to see Silicon Valley)
        - Nature and hiking (interested in nearby trails)
        - Good coffee and food scene
        - Photography spots
        
        Budget: Moderate (not luxury but comfortable)
    """)
    
    print("📋 Travel Request:")
    print(travel_request)
    print("-" * 50)
    print("\n🤖 SkyPlanner Team is working on your travel plan...\n")
    
    # Execute the team's planning
    try:
        response = await team.arun(travel_request)
        
        print("\n" + "=" * 50)
        print("✈️ YOUR COMPLETE TRAVEL PLAN")
        print("=" * 50)
        
        # Display the structured response
        if hasattr(response, 'content'):
            print(response.content)
        else:
            print(response)
            
    except Exception as e:
        print(f"\n❌ Error during planning: {e}")
        print("Please check your API keys and connections.")


async def simple_query():
    """Run a simple query for testing."""
    
    print("🚀 Running simple travel query test...")
    
    team = get_skyplanner_team(
        debug_mode=False,
        user_id="test_user"
    )
    
    query = "What are the top 3 attractions in Paris?"
    
    print(f"Query: {query}")
    response = await team.arun(query)
    print(f"Response: {response}")


if __name__ == "__main__":
    # Check if we're running a simple test or full demo
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        asyncio.run(simple_query())
    else:
        asyncio.run(plan_trip())