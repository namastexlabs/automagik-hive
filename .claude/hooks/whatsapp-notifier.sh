#!/bin/bash
# WhatsApp notification hook for Genie Framework
# Sends notifications when tasks complete or important events happen

# Configuration
INSTANCE="SofIA"
NOTIFICATION_KEYWORDS=("✅ Complete" "🔄 Started" "⚠️ Error" "🎯 Epic")

# Get the input
INPUT=$(cat)

# Check if this is a notification-worthy event
should_notify=false
for keyword in "${NOTIFICATION_KEYWORDS[@]}"; do
    if echo "$INPUT" | grep -q "$keyword"; then
        should_notify=true
        break
    fi
done

# Also check for task completions in memory
if echo "$INPUT" | grep -q "TASK.*DONE"; then
    should_notify=true
fi

# Send notification if needed
if [ "$should_notify" = true ]; then
    # Extract relevant info
    task_info=$(echo "$INPUT" | grep -E "(TASK|Epic|Complete)" | head -3)
    
    # Format notification message
    message="🤖 Genie Update
    
$task_info

💡 Check memory for details:
memory.search('TASK') for status
memory.search('PATTERN') for new patterns"

    # Send WhatsApp message (async, don't block)
    {
        # Use Claude's MCP WhatsApp tool
        cat << EOF | claude --tool mcp__send_whatsapp_message__send_text_message
{
    "instance": "$INSTANCE",
    "message": "$message"
}
EOF
    } &
fi

# Pass through the original input unchanged
echo "$INPUT"