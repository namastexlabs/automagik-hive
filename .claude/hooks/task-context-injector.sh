#!/bin/bash
# Task Context Injector Hook for Genie Framework
# Automatically injects project context into all Task tool calls
#
# This hook ensures every subagent has access to essential project
# documentation without manual specification in each Task prompt.

set -euo pipefail

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

# Build context prefix with essential files
CONTEXT_PREFIX="ESSENTIAL PROJECT CONTEXT - Read these files first:

1. Project Overview and Rules:
   - @/CLAUDE.md - Master project context and workflow rules
   
2. Technical Foundation:
   - @/genie/ai-context/project-structure.md - Complete tech stack and architecture
   - @/genie/ai-context/development-standards.md - Coding standards and patterns

3. Memory Context:
   Search genie-memory for any relevant context using: memory.search('your topic')
   
After reading the above context, proceed with your assigned task:
"

# Check if context is already injected (to avoid double injection)
if echo "$ORIGINAL_PROMPT" | grep -q "ESSENTIAL PROJECT CONTEXT"; then
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