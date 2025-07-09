import sys
import os

# Patch the message creation to log sizes
from anthropic import AsyncAnthropic
original_create = AsyncAnthropic.messages.create

async def debug_create(self, *args, **kwargs):
    # Check message sizes
    if 'messages' in kwargs:
        print("\n" + "="*60)
        print("🔴 ANTHROPIC API CALL")
        print("="*60)
        
        total_chars = 0
        for i, msg in enumerate(kwargs['messages']):
            content_size = len(str(msg.get('content', '')))
            total_chars += content_size
            role = msg.get('role', 'unknown')
            
            print(f"\nMessage {i} ({role}): {content_size:,} chars")
            
            if content_size > 10000:
                content = str(msg.get('content', ''))
                # Show first 500 chars
                print(f"Preview: {content[:500]}...")
                
                # Check patterns
                if 'team_members>' in content:
                    import re
                    members = re.findall(r'Agent \d+:', content)
                    print(f"  ⚠️ Contains {len(members)} team members")
                
                if '<member interactions>' in content:
                    print(f"  ⚠️ Contains member interactions")
                    
                if 'team_session_state>' in content:
                    print(f"  ⚠️ Contains team session state")
                    
        print(f"\n🔴 TOTAL SIZE: {total_chars:,} characters")
        
        if total_chars > 100000:
            print("\n⚠️⚠️⚠️ CONTEXT OVER 100K - THIS WILL CAUSE OVERLOAD! ⚠️⚠️⚠️")
            
            # Save to file for analysis
            with open('debug_large_context.json', 'w') as f:
                import json
                json.dump(kwargs['messages'], f, indent=2)
                print("Saved full context to debug_large_context.json")
                
    return await original_create(self, *args, **kwargs)

AsyncAnthropic.messages.create = debug_create

# Now run a simple test
from playground import app
print("Debug monitoring enabled...")