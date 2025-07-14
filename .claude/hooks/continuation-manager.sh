#!/bin/bash
# Continuation Manager for Genie Framework
# Manages hybrid memory + Zen continuation system for long-running tasks

set -euo pipefail

# Configuration
CONTINUATION_MEMORY_PREFIX="CONTINUATION:"
MAX_CONTINUATION_AGE_HOURS=3

# Function to store continuation ID in memory
store_continuation() {
    local continuation_id="$1"
    local task_context="$2"
    local timestamp=$(date -Iseconds)
    
    memory.add "$CONTINUATION_MEMORY_PREFIX ID: $continuation_id TASK: $task_context CREATED: $timestamp"
}

# Function to retrieve active continuations
get_active_continuations() {
    local task_pattern="$1"
    memory.search "$CONTINUATION_MEMORY_PREFIX.*$task_pattern"
}

# Function to check continuation expiry
check_continuation_expiry() {
    local continuation_id="$1"
    local created_time="$2"
    local current_time=$(date +%s)
    local created_timestamp=$(date -d "$created_time" +%s)
    local age_hours=$(( (current_time - created_timestamp) / 3600 ))
    
    if [ $age_hours -gt $MAX_CONTINUATION_AGE_HOURS ]; then
        echo "EXPIRED"
    else
        echo "ACTIVE"
    fi
}

# Function to create checkpoint in memory
create_checkpoint() {
    local task_id="$1"
    local state="$2"
    local continuation_id="$3"
    
    memory.add "CHECKPOINT: $task_id STATE: $state CONTINUATION: $continuation_id"
}

# Function to restore from checkpoint
restore_checkpoint() {
    local task_id="$1"
    memory.search "CHECKPOINT: $task_id"
}

# Function to handle continuation workflows
manage_continuation() {
    local input="$1"
    
    # Check if this involves a continuation
    if echo "$input" | grep -q "continuation_id"; then
        local continuation_id=$(echo "$input" | jq -r '.continuation_id // ""')
        
        if [ -n "$continuation_id" ]; then
            # Store or update continuation in memory
            local task_context=$(echo "$input" | jq -r '.task_context // "general"')
            store_continuation "$continuation_id" "$task_context"
            
            # Create checkpoint
            create_checkpoint "$task_context" "active" "$continuation_id"
            
            echo "Continuation $continuation_id stored for task: $task_context" >&2
        fi
    fi
    
    # Check for expired continuations (cleanup)
    local continuations=$(memory.search "$CONTINUATION_MEMORY_PREFIX")
    while IFS= read -r continuation; do
        if [ -n "$continuation" ]; then
            local id=$(echo "$continuation" | grep -o 'ID: [^ ]*' | cut -d' ' -f2)
            local created=$(echo "$continuation" | grep -o 'CREATED: [^ ]*' | cut -d' ' -f2)
            
            if [ -n "$id" ] && [ -n "$created" ]; then
                local status=$(check_continuation_expiry "$id" "$created")
                if [ "$status" = "EXPIRED" ]; then
                    memory.add "CONTINUATION: $id EXPIRED at $(date -Iseconds)"
                    echo "Continuation $id expired and marked" >&2
                fi
            fi
        fi
    done <<< "$continuations"
}

# Function to get continuation context for task
get_continuation_context() {
    local task_pattern="$1"
    
    echo "=== CONTINUATION CONTEXT ==="
    echo "Active continuations for $task_pattern:"
    get_active_continuations "$task_pattern"
    echo ""
    echo "Recent checkpoints:"
    memory.search "CHECKPOINT:.*$task_pattern"
    echo "=========================="
}

# Main function
main() {
    local input=$(cat)
    
    # Manage continuations
    manage_continuation "$input"
    
    # Pass through input unchanged
    echo "$input"
}

# Helper functions for integration

# Function to start a continued task
start_continued_task() {
    local task_id="$1"
    local continuation_id="$2"
    
    echo "Starting task $task_id with continuation $continuation_id"
    store_continuation "$continuation_id" "$task_id"
    create_checkpoint "$task_id" "started" "$continuation_id"
}

# Function to resume from continuation
resume_from_continuation() {
    local task_id="$1"
    
    local checkpoint=$(restore_checkpoint "$task_id")
    if [ -n "$checkpoint" ]; then
        echo "Resuming $task_id from checkpoint: $checkpoint"
        return 0
    else
        echo "No checkpoint found for $task_id"
        return 1
    fi
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi