import os
import json
os.environ['AGNO_LOG_LEVEL'] = 'DEBUG'

# Monkey patch the Team._get_system_message to log context size
from agno.team.team import Team

original_get_system_message = Team._get_system_message

def patched_get_system_message(self, *args, **kwargs):
    # Call original
    result = original_get_system_message(self, *args, **kwargs)
    
    # Log the size
    if hasattr(result, 'content'):
        size = len(str(result.content))
        print(f"\n🔴 SYSTEM MESSAGE for {self.name}: {size:,} characters")
        
        if size > 10000:
            print("🔴 LARGE SYSTEM MESSAGE DETECTED!")
            content = str(result.content)
            
            # Check for specific patterns
            if '<team_members>' in content:
                # Count team members
                import re
                members = re.findall(r'- Agent \d+:', content)
                print(f"  ⚠️  Contains {len(members)} team members")
            
            if 'Tools:' in content:
                tools = re.findall(r'- ([^:]+):', content.split('Tools:')[1] if 'Tools:' in content else '')
                print(f"  ⚠️  Contains {len(tools)} tools listed")
                
            if '<team_session_state>' in content:
                print("  ⚠️  Contains team session state")
                
            if 'Knowledge Base Results:' in content:
                print("  ⚠️  Contains knowledge base results")
                
            # Show preview
            print(f"\n  Preview (first 1000 chars):\n{content[:1000]}...")
    
    return result

Team._get_system_message = patched_get_system_message

# Also patch the run messages to see user message size
from agno.models.base import Model

original_build_run_messages = Model._build_run_messages

def patched_build_run_messages(self, *args, **kwargs):
    # Call original
    result = original_build_run_messages(self, *args, **kwargs)
    
    # Log sizes
    if hasattr(result, 'messages') and result.messages:
        total_size = 0
        for msg in result.messages:
            if hasattr(msg, 'content'):
                total_size += len(str(msg.content))
        
        if total_size > 50000:
            print(f"\n🔴 TOTAL MESSAGES SIZE: {total_size:,} characters")
            print(f"  Number of messages: {len(result.messages)}")
            
            for i, msg in enumerate(result.messages):
                if hasattr(msg, 'content') and hasattr(msg, 'role'):
                    size = len(str(msg.content))
                    if size > 10000:
                        print(f"  Message {i} ({msg.role}): {size:,} chars")
    
    return result

Model._build_run_messages = patched_build_run_messages

# Now run the playground
from playground import app
print("\n🔍 Context debugging enabled - monitoring all message sizes\n")