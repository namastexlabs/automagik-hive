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
CONTEXT_PREFIX="=== DYNAMIC PROJECT CONTEXT ===

📋 ESSENTIAL FILES:
   - @/CLAUDE.md - Master project context and workflow rules
   - @/genie/ai-context/project-structure.md - Complete tech stack and architecture
   - @/genie/ai-context/development-standards.md - Coding standards and patterns

🧠 MEMORY CONTEXT:
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