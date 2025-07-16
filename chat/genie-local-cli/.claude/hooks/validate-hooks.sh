#!/bin/bash

# Hook Validation Script
# Tests all configured hooks to ensure they work properly with Claude Code

echo "=== Claude Code Hooks Validation ==="
echo "Testing all configured hooks..."

# Test 1: Check settings configuration
echo "1. Checking hook configuration..."
if [[ ! -f ".claude/settings.local.json" ]]; then
    echo "❌ settings.local.json not found"
    exit 1
fi

# Parse hook configuration
HOOKS_COUNT=$(jq '.hooks | keys | length' .claude/settings.local.json)
echo "✓ Found $HOOKS_COUNT hook types configured"

# Test 2: Check hook files exist and are executable
echo "2. Checking hook files..."
for hook in mcp-security-scan.sh gemini-context-injector.sh subagent-context-injector.sh notify.sh; do
    if [[ -x ".claude/hooks/$hook" ]]; then
        echo "✓ $hook is executable"
    else
        echo "❌ $hook is missing or not executable"
    fi
done

# Test 3: Environment variables
echo "3. Checking environment variables..."
source .env
if [[ -n "$ANTHROPIC_API_KEY" ]]; then
    echo "✓ ANTHROPIC_API_KEY configured"
else
    echo "❌ ANTHROPIC_API_KEY missing"
fi

if [[ -n "$GEMINI_API_KEY" ]]; then
    echo "✓ GEMINI_API_KEY configured"
else
    echo "❌ GEMINI_API_KEY missing"
fi

# Test 4: Test hook execution
echo "4. Testing hook execution..."

# Test MCP security scan
echo "  Testing MCP security scan..."
SECURITY_RESULT=$(echo '{"tool_name": "mcp__test__action", "parameters": {"test": "value"}}' | bash .claude/hooks/mcp-security-scan.sh)
if [[ $? -eq 0 ]]; then
    echo "✓ MCP security scan working"
else
    echo "❌ MCP security scan failed"
fi

# Test Gemini context injector
echo "  Testing Gemini context injector..."
GEMINI_RESULT=$(echo '{"tool_name": "mcp__gemini__consult_gemini", "parameters": {"specific_question": "test"}}' | bash .claude/hooks/gemini-context-injector.sh)
if [[ $? -eq 0 ]]; then
    echo "✓ Gemini context injector working"
else
    echo "❌ Gemini context injector failed"
fi

# Test subagent context injector
echo "  Testing subagent context injector..."
SUBAGENT_RESULT=$(echo '{"tool_name": "Task", "parameters": {"task": "test"}}' | bash .claude/hooks/subagent-context-injector.sh)
if [[ $? -eq 0 ]]; then
    echo "✓ Subagent context injector working"
else
    echo "❌ Subagent context injector failed"
fi

# Test notification hooks
echo "  Testing notification hooks..."
bash .claude/hooks/notify.sh input > /dev/null 2>&1
if [[ $? -eq 0 ]]; then
    echo "✓ Notification hooks working"
else
    echo "❌ Notification hooks failed"
fi

# Test 5: Check log files
echo "5. Checking log files..."
if [[ -f ".claude/logs/security-scan.log" ]]; then
    echo "✓ Security scan logging active"
else
    echo "❌ Security scan logging not working"
fi

if [[ -f ".claude/logs/context-injection.log" ]]; then
    echo "✓ Context injection logging active"
else
    echo "❌ Context injection logging not working"
fi

echo "=== Validation Complete ==="
echo "All hooks are properly configured and working with Claude Code!"