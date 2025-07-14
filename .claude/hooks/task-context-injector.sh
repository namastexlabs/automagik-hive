#!/bin/bash
# Task Context Injector Hook for Genie Framework
# Automatically injects project context into all Task tool calls
#
# This hook ensures every subagent has access to essential project
# documentation without manual specification in each Task prompt.

set -euo pipefail

# Get the project root directory dynamically
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Read input from stdin
INPUT_JSON=$(cat)

# Extract tool name
TOOL_NAME=$(echo "$INPUT_JSON" | jq -r '.tool_name // ""')

# Only process Task tool calls
if [[ "$TOOL_NAME" != "Task" ]]; then
    # Pass through unchanged for other tools
    echo "$INPUT_JSON"
    exit 0
fi

# Extract the original prompt
ORIGINAL_PROMPT=$(echo "$INPUT_JSON" | jq -r '.tool_input.prompt // ""')

# Function to get recent memory context
get_memory_context() {
    local recent_patterns=""
    local recent_tasks=""
    local recent_findings=""
    
    # Check if memory command is available and get recent context
    if command -v memory >/dev/null 2>&1; then
        recent_patterns=$(memory search "PATTERN:" 2>/dev/null | head -3 || echo "")
        recent_tasks=$(memory search "TASK:" 2>/dev/null | head -2 || echo "")
        recent_findings=$(memory search "FOUND:" 2>/dev/null | head -3 || echo "")
    fi
    
    echo "🧠 RECENT MEMORY CONTEXT:"
    if [ -n "$recent_patterns" ]; then
        echo "   Recent patterns: $recent_patterns"
    fi
    if [ -n "$recent_tasks" ]; then
        echo "   Active tasks: $recent_tasks"
    fi
    if [ -n "$recent_findings" ]; then
        echo "   Recent findings: $recent_findings"
    fi
    echo ""
}

# Build context prefix with essential files and dynamic memory
MEMORY_CONTEXT=$(get_memory_context)

CONTEXT_PREFIX="=== DYNAMIC PROJECT CONTEXT ===
Project Root: $PROJECT_ROOT

📋 ESSENTIAL FILES:
   - @CLAUDE.md - Master project context and workflow rules
   - @genie/CLAUDE.md - Framework-specific instructions

$MEMORY_CONTEXT

🔍 MEMORY SEARCH COMMANDS:
   Search for patterns: memory.search('PATTERN: [topic]')
   Check current work: memory.search('TASK: Working')
   Find discoveries: memory.search('FOUND: [topic]')
   Check for blockers: memory.search('TASK: BLOCKED')

💡 QUICK CONTEXT QUERIES:
   - Project tech stack: memory.search('PROJECT: tech')
   - Authentication: memory.search('PATTERN: auth')
   - Database info: memory.search('FOUND: database')
   - API structure: memory.search('FOUND: api')

Your assigned task:
"

# Check if context is already injected (to avoid double injection)
if echo "$ORIGINAL_PROMPT" | grep -q "DYNAMIC PROJECT CONTEXT"; then
    # Already has context, pass through unchanged
    echo "$INPUT_JSON"
    exit 0
fi

# Create modified prompt with context
MODIFIED_PROMPT="${CONTEXT_PREFIX}

${ORIGINAL_PROMPT}"

# Update the JSON with modified prompt
MODIFIED_JSON=$(echo "$INPUT_JSON" | jq --arg prompt "$MODIFIED_PROMPT" '.tool_input.prompt = $prompt')

# Output the modified JSON
echo "$MODIFIED_JSON"