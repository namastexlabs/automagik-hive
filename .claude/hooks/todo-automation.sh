#!/bin/bash
# TODO Automation Hook for Genie Framework
# Automatically creates, updates, and manages TODO items based on epic progress and memory state

set -euo pipefail

# Configuration
EPIC_ID="genie-framework-completion"
TODO_MEMORY_PREFIX="TODO_AUTO:"

# Function to extract current TODO state from TodoWrite tool calls
extract_todo_updates() {
    local input="$1"
    
    if echo "$input" | jq -e '.tool_name == "TodoWrite"' >/dev/null 2>&1; then
        echo "$input" | jq -r '.tool_input.todos[]? | "\(.id):\(.status):\(.content)"'
    fi
}

# Function to auto-generate TODOs from epic status
auto_generate_todos() {
    # Get current epic status from memory
    local completed_tasks=$(memory.search "TASK.*DONE" | wc -l)
    local epic_status_file="genie/staging/${EPIC_ID}.md"
    
    if [ -f "$epic_status_file" ]; then
        # Parse epic file for remaining tasks
        while IFS= read -r line; do
            if echo "$line" | grep -q "^#### .*T-[0-9][0-9]*:"; then
                local task_id=$(echo "$line" | grep -o "T-[0-9][0-9]*")
                local task_desc=$(echo "$line" | sed 's/^#### .*T-[0-9][0-9]*: //')
                
                # Check if task is already done in memory
                if ! memory.search "TASK $task_id.*DONE" >/dev/null 2>&1; then
                    # Check if task is in progress
                    if memory.search "TASK $task_id.*Working" >/dev/null 2>&1; then
                        echo "$task_id:in_progress:$task_desc"
                    else
                        echo "$task_id:pending:$task_desc"
                    fi
                else
                    echo "$task_id:completed:$task_desc"
                fi
            fi
        done < "$epic_status_file"
    fi
}

# Function to update TODO based on memory state
update_todo_from_memory() {
    local task_id="$1"
    
    # Check memory for task status
    if memory.search "TASK $task_id.*DONE" >/dev/null 2>&1; then
        echo "completed"
    elif memory.search "TASK $task_id.*Working\|TASK $task_id.*IN_PROGRESS" >/dev/null 2>&1; then
        echo "in_progress"
    else
        echo "pending"
    fi
}

# Function to generate TodoWrite JSON
generate_todo_json() {
    local todos="$1"
    
    echo '{"tool_name": "TodoWrite", "tool_input": {"todos": ['
    
    local first=true
    while IFS=':' read -r id status content; do
        if [ "$first" = true ]; then
            first=false
        else
            echo ","
        fi
        
        local priority="medium"
        # Set priority based on task dependencies and importance
        case "$id" in
            T-005) priority="high" ;;  # Interactive tasks need user
            T-0*) priority="high" ;;   # Early foundation tasks
            *) priority="medium" ;;
        esac
        
        echo -n "{\"id\": \"$id\", \"content\": \"$content\", \"status\": \"$status\", \"priority\": \"$priority\"}"
    done <<< "$todos"
    
    echo ']}}'
}

# Function to detect task state changes
detect_task_changes() {
    local input="$1"
    
    # Look for task completion patterns in memory updates
    if echo "$input" | grep -q "TASK.*DONE\|TASK.*Working\|TASK.*STARTED"; then
        local task_mentions=$(echo "$input" | grep -o "T-[0-9][0-9]*" | sort -u)
        
        if [ -n "$task_mentions" ]; then
            echo "TASK_CHANGE_DETECTED: $task_mentions"
            return 0
        fi
    fi
    
    return 1
}

# Function to auto-update TODOs
auto_update_todos() {
    echo "Auto-updating TODOs based on current epic state..." >&2
    
    # Generate current TODO state from epic and memory
    local current_todos=$(auto_generate_todos)
    
    if [ -n "$current_todos" ]; then
        # Generate and execute TodoWrite command
        local todo_json=$(generate_todo_json "$current_todos")
        
        # Store the auto-update in memory for tracking
        memory.add "$TODO_MEMORY_PREFIX Auto-updated TODOs at $(date -Iseconds)"
        
        # Output the TodoWrite command JSON
        echo "$todo_json" >&2
        
        # Note: In a real implementation, this would trigger the TodoWrite tool
        # For now, we log that an update should happen
        echo "TODO auto-update triggered" >&2
    fi
}

# Main function
main() {
    local input=$(cat)
    
    # Check if this input indicates task state changes
    if detect_task_changes "$input"; then
        echo "Task state change detected, triggering TODO update..." >&2
        auto_update_todos
    fi
    
    # Check if this is already a TodoWrite call (avoid recursion)
    if echo "$input" | jq -e '.tool_name == "TodoWrite"' >/dev/null 2>&1; then
        # Log manual TODO update
        memory.add "$TODO_MEMORY_PREFIX Manual TODO update detected at $(date -Iseconds)"
    fi
    
    # Pass through input unchanged
    echo "$input"
}

# Helper function for epic monitoring
monitor_epic_progress() {
    local epic_file="genie/staging/${EPIC_ID}.md"
    
    if [ -f "$epic_file" ]; then
        # Watch for changes to epic file and trigger TODO updates
        # This would be called by a file watcher in a complete implementation
        auto_update_todos
    fi
}

# Helper function to sync memory with TODOs
sync_memory_todos() {
    echo "Syncing memory state with TODO system..." >&2
    
    # Get all task-related memories
    local memory_tasks=$(memory.search "TASK T-")
    
    # Parse and update TODO state accordingly
    while IFS= read -r memory_entry; do
        if [[ "$memory_entry" =~ T-([0-9]+) ]]; then
            local task_id="T-${BASH_REMATCH[1]}"
            local status=$(update_todo_from_memory "$task_id")
            echo "Task $task_id should be: $status" >&2
        fi
    done <<< "$memory_tasks"
}

# Export functions for use by other scripts
export -f auto_generate_todos
export -f update_todo_from_memory
export -f auto_update_todos
export -f sync_memory_todos

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi