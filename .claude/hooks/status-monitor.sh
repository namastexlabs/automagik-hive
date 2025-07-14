#!/bin/bash
# Status Monitor Hook for Genie Framework
# Monitors epic progress and sends notifications for milestones

set -euo pipefail

# Configuration
NOTIFICATION_INSTANCE="SofIA"
EPIC_ID="genie-framework-completion"

# Function to send WhatsApp notification
send_notification() {
    local message="$1"
    local context="${2:-""}"
    
    local full_message="🤖 Epic Progress Update

$message"
    
    if [ -n "$context" ]; then
        full_message="$full_message

💡 $context"
    fi
    
    # Send via Claude's MCP WhatsApp tool (async)
    {
        cat << EOF | claude --tool mcp__send_whatsapp_message__send_text_message 2>/dev/null || true
{
    "instance": "$NOTIFICATION_INSTANCE",
    "message": "$full_message"
}
EOF
    } &
}

# Function to get task completion count
get_task_stats() {
    # Query memory for task completion statistics
    local completed_count=0
    local in_progress_count=0
    local total_tasks=14  # Based on epic definition
    
    # Count completed tasks (this would use memory.search in real implementation)
    # For now, simulate based on known completions
    local completed_tasks=("T-001" "T-003" "T-004" "T-006" "T-002")
    completed_count=${#completed_tasks[@]}
    
    # Calculate progress percentage
    local progress=$((completed_count * 100 / total_tasks))
    
    echo "$completed_count/$total_tasks ($progress%)"
}

# Function to check for epic milestones
check_milestones() {
    local stats=$(get_task_stats)
    local completed=$(echo "$stats" | cut -d'/' -f1)
    
    case $completed in
        5)
            send_notification "🎯 Milestone: Foundation Phase Complete
            
✅ Completed Tasks: $stats
🔄 Next Phase: Planning Enhancement" "Major framework components ready"
            ;;
        7)
            send_notification "🎯 Milestone: 50% Complete
            
✅ Progress: $stats
🚀 Framework taking shape!" "Check memory: search('TASK DONE')"
            ;;
        10)
            send_notification "🎯 Milestone: Core Framework Ready
            
✅ Progress: $stats
🎉 Ready for advanced features" "Memory system fully integrated"
            ;;
        14)
            send_notification "🎉 EPIC COMPLETE: Genie Framework Done!
            
✅ All Tasks: $stats
🌟 Framework ready for self-enhancement" "The future of AI development is here!"
            ;;
    esac
}

# Function to check for blockers resolved
check_blockers_resolved() {
    # This would query memory for recently resolved blockers
    # For now, just log that we're monitoring
    echo "Monitoring for resolved blockers..." >&2
}

# Function to check for new discoveries
check_discoveries() {
    # This would query memory for recent FOUND: entries
    # For now, just log that we're monitoring
    echo "Monitoring for new discoveries..." >&2
}

# Main monitoring logic
main() {
    local input=$(cat)
    
    # Check if this is a task completion
    if echo "$input" | grep -q "TASK.*DONE"; then
        echo "Task completion detected, checking milestones..." >&2
        check_milestones
    fi
    
    # Check if this is a blocker resolution
    if echo "$input" | grep -q "BLOCKER.*RESOLVED"; then
        check_blockers_resolved
    fi
    
    # Check if this is a significant discovery
    if echo "$input" | grep -q "FOUND:.*BREAKTHROUGH\|PATTERN:.*MAJOR"; then
        check_discoveries
    fi
    
    # Pass through input unchanged
    echo "$input"
}

# Run main function
main