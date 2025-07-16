#!/usr/bin/env python3
"""
Test script for enhanced Ana team demo logging.
Run this to see the detailed agent activity logging in action.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.teams.ana.team import get_ana_team
from agno.utils.log import logger

def test_ana_demo_logging():
    """Test the enhanced demo logging functionality for Ana team"""
    
    print("🎬 Testing Enhanced Ana Team Demo Logging")
    print("=" * 60)
    
    # Sample fraud PIX conversation for testing
    fraud_pix_query = "tive um problema de fraude, meu dinheiro sumiu no pix"
    
    print(f"🚀 Starting Ana team test...")
    print(f"📝 Sample query: {fraud_pix_query}")
    print(f"🔧 Debug: {os.getenv('DEBUG')}, 🎬 Demo: {os.getenv('DEMO_MODE')}")
    print()
    
    try:
        # Create enhanced Ana team
        ana_team = get_ana_team(
            debug_mode=True,
            session_id="DEMO-FRAUD-001",
            user_id="demo-user"
        )
        
        print(f"\n🎯 Running query through Ana team...")
        print(f"This should show the agent routing process step by step:")
        print()
        
        # Run the query - this should trigger all the demo logging
        result = ana_team.run(fraud_pix_query)
        
        print("\n" + "=" * 60)
        print("✅ DEMO TEST COMPLETED SUCCESSFULLY")
        print(f"📊 Response generated: {len(str(result.content)) if hasattr(result, 'content') else 'N/A'} characters")
        
        if hasattr(result, 'content'):
            print(f"🎯 Response preview: {str(result.content)[:100]}...")
        
        print("\n🎉 Demo logging shows:")
        print("  • Team initialization with specialist list")
        print("  • Query processing with routing analysis")
        print("  • Behind-the-scenes agent selection")
        print("  • Tool usage and knowledge base searches")
        print("  • Final result with success metrics")
        
    except Exception as e:
        print(f"❌ DEMO TEST FAILED: {str(e)}")
        logger.error(f"Demo test error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🎬 PagBank V2 Ana Team - Enhanced Demo Logging Test")
    print("This script demonstrates the behind-the-scenes agent activity for management demos.")
    print()
    
    success = test_ana_demo_logging()
    
    if success:
        print("\n🎉 Enhanced demo logging test completed successfully!")
        print("💡 You can now show management exactly what the agents do under the hood")
        print("📋 This includes routing decisions, tool usage, and specialist selection")
    else:
        print("\n💥 Demo test failed - check the logs above")
        sys.exit(1)