#!/bin/bash
# Command Memory Hook
# Automatically tags memory entries based on command type and context
#
# This hook intercepts memory operations and automatically:
# - Adds command-specific tags to memory entries
# - Categorizes memory by command type (fix, build, debug, etc.)
# - Enhances memory searchability with structured tagging
# - Provides command-specific memory context

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="$SCRIPT_DIR/../logs/command-memory.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Read input from stdin
INPUT_JSON=$(cat)

# Function to log memory events
log_memory_event() {
    local event_type="$1"
    local details="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "{\"timestamp\": \"$timestamp\", \"event\": \"$event_type\", \"details\": \"$details\"}" >> "$LOG_FILE"
}

# Function to detect current command context
detect_command_context() {
    # Check environment variables that might indicate command context
    local context=""
    
    # Check for recent command usage (simplified detection)
    if [[ "${CLAUDE_COMMAND:-}" == "fix" ]] || [[ "${RECENT_COMMAND:-}" == "fix" ]]; then
        context="fix"
    elif [[ "${CLAUDE_COMMAND:-}" == "build" ]] || [[ "${RECENT_COMMAND:-}" == "build" ]]; then
        context="build"
    elif [[ "${CLAUDE_COMMAND:-}" == "nuke" ]] || [[ "${RECENT_COMMAND:-}" == "nuke" ]]; then
        context="nuke"
    elif [[ "${CLAUDE_COMMAND:-}" == "debug" ]] || [[ "${RECENT_COMMAND:-}" == "debug" ]]; then
        context="debug"
    elif [[ "${CLAUDE_COMMAND:-}" == "analyze" ]] || [[ "${RECENT_COMMAND:-}" == "analyze" ]]; then
        context="analyze"
    fi
    
    echo "$context"
}

# Function to extract content type from memory text
extract_content_type() {
    local text="$1"
    local type=""
    
    if [[ "$text" =~ (FOUND|SOLUTION|DISCOVERED) ]]; then
        type="solution"
    elif [[ "$text" =~ (PATTERN|IMPLEMENTATION|APPROACH) ]]; then
        type="pattern"
    elif [[ "$text" =~ (ERROR|BUG|ISSUE|PROBLEM) ]]; then
        type="issue"
    elif [[ "$text" =~ (TASK|TODO|PROGRESS) ]]; then
        type="task"
    elif [[ "$text" =~ (NUCLEAR|CHECKPOINT|RECOVERY) ]]; then
        type="nuclear"
    elif [[ "$text" =~ (API|ENDPOINT|SERVICE) ]]; then
        type="api"
    elif [[ "$text" =~ (AGENT|TEAM|ROUTING) ]]; then
        type="agent"
    elif [[ "$text" =~ (DATABASE|SCHEMA|MIGRATION) ]]; then
        type="database"
    else
        type="general"
    fi
    
    echo "$type"
}

# Function to generate command-specific tags
generate_tags() {
    local command="$1"
    local content_type="$2"
    local text="$3"
    local tags=""
    
    # Add command tag
    if [[ -n "$command" ]]; then
        tags="$tags #$command"
    fi
    
    # Add content type tag
    if [[ -n "$content_type" ]]; then
        tags="$tags #$content_type"
    fi
    
    # Add specific tags based on content
    if [[ "$text" =~ (performance|memory|slow|optimization) ]]; then
        tags="$tags #performance"
    fi
    
    if [[ "$text" =~ (security|vulnerability|attack|exploit) ]]; then
        tags="$tags #security"
    fi
    
    if [[ "$text" =~ (integration|external|API|service) ]]; then
        tags="$tags #integration"
    fi
    
    if [[ "$text" =~ (testing|test|validation|verify) ]]; then
        tags="$tags #testing"
    fi
    
    if [[ "$text" =~ (deployment|production|staging) ]]; then
        tags="$tags #deployment"
    fi
    
    # Add timestamp tag
    local date_tag=$(date +"%Y-%m")
    tags="$tags #$date_tag"
    
    echo "$tags"
}

# Function to enhance memory content
enhance_memory_content() {
    local text="$1"
    local command="$2"
    local content_type="$3"
    local tags="$4"
    
    # Add command context prefix if not already present
    local prefix=""
    if [[ -n "$command" ]] && [[ ! "$text" =~ ^(FOUND|PATTERN|ERROR|TASK|NUCLEAR) ]]; then
        case "$command" in
            "fix") prefix="FIX: " ;;
            "build") prefix="BUILD: " ;;
            "nuke") prefix="NUCLEAR: " ;;
            "debug") prefix="DEBUG: " ;;
            "analyze") prefix="ANALYZE: " ;;
        esac
    fi
    
    # Enhance the text with prefix and tags
    local enhanced_text="${prefix}${text} $tags"
    
    echo "$enhanced_text"
}

# Main logic
main() {
    # Extract tool information from stdin
    local tool_name=$(echo "$INPUT_JSON" | jq -r '.tool_name // ""')
    
    # Only process genie memory add operations
    if [[ "$tool_name" != "mcp__genie-memory__add_memories" ]]; then
        echo '{"continue": true}'
        exit 0
    fi
    
    # Extract tool arguments
    local tool_args=$(echo "$INPUT_JSON" | jq -r '.tool_input // "{}"')
    local text=$(echo "$tool_args" | jq -r '.text // ""')
    
    if [[ -z "$text" ]]; then
        log_memory_event "skipped" "no_text_content"
        echo '{"continue": true}'
        exit 0
    fi
    
    log_memory_event "memory_add_detected" "processing_content"
    
    # Detect command context
    local command=$(detect_command_context)
    
    # Extract content type
    local content_type=$(extract_content_type "$text")
    
    # Generate tags
    local tags=$(generate_tags "$command" "$content_type" "$text")
    
    # Enhance memory content
    local enhanced_text=$(enhance_memory_content "$text" "$command" "$content_type" "$tags")
    
    # Update the tool arguments with enhanced text
    local modified_args=$(echo "$tool_args" | jq --arg new_text "$enhanced_text" '.text = $new_text')
    
    # Update the input JSON with modified arguments
    local output_json=$(echo "$INPUT_JSON" | jq --argjson new_args "$modified_args" '.tool_input = $new_args')
    
    log_memory_event "memory_enhanced" "command:$command,type:$content_type,tags:$tags"
    
    # Return the modified input
    echo "$output_json"
}

# Run main function
main