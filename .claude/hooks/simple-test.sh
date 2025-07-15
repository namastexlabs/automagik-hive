#!/bin/bash
# Simple test script to verify hook functionality

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

print_failure() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Test 1: Fix Context Injector
print_info "Testing Fix Context Injector"

# Test 1.1: Non-fix command should pass through
input1='{"message": "/build something"}'
result1=$(echo "$input1" | ./fix-context-injector.sh)
continue_flag=$(echo "$result1" | jq -r '.continue // false')
if [[ "$continue_flag" == "true" ]]; then
    print_success "Fix hook correctly passes through non-fix commands"
else
    print_failure "Fix hook should pass through non-fix commands"
fi

# Test 1.2: Fix command should be enhanced
input2='{"message": "/fix API returns 500 error"}'
result2=$(echo "$input2" | ./fix-context-injector.sh)
original_message=$(echo "$input2" | jq -r '.message')
result_message=$(echo "$result2" | jq -r '.message')
if [[ "$result_message" != "$original_message" ]]; then
    print_success "Fix hook correctly enhances fix commands"
else
    print_failure "Fix hook should enhance fix commands"
fi

# Test 2: Build Planner
print_info "Testing Build Planner"

# Test 2.1: Build command should be enhanced
input3='{"message": "/build Create validation function"}'
result3=$(echo "$input3" | ./build-planner.sh)
original_message=$(echo "$input3" | jq -r '.message')
result_message=$(echo "$result3" | jq -r '.message')
if [[ "$result_message" != "$original_message" ]]; then
    print_success "Build hook correctly enhances build commands"
else
    print_failure "Build hook should enhance build commands"
fi

# Test 3: Nuke Checkpoint
print_info "Testing Nuke Checkpoint"

# Test 3.1: Nuke command should be enhanced (if in git repo)
input4='{"message": "/nuke Race condition in payment processing"}'
result4=$(echo "$input4" | ./nuke-checkpoint.sh)
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    original_message=$(echo "$input4" | jq -r '.message')
    result_message=$(echo "$result4" | jq -r '.message')
    if [[ "$result_message" != "$original_message" ]]; then
        print_success "Nuke hook correctly enhances nuke commands (git repo)"
    else
        print_failure "Nuke hook should enhance nuke commands in git repo"
    fi
else
    print_success "Nuke hook skipped (not in git repo)"
fi

# Test 4: Command Memory
print_info "Testing Command Memory"

# Test 4.1: Memory add should be enhanced
input5='{"tool_name": "mcp__genie-memory__add_memories", "tool_input": {"text": "FOUND solution for API timeout issue"}}'
result5=$(echo "$input5" | ./command-memory.sh)
original_text=$(echo "$input5" | jq -r '.tool_input.text')
result_text=$(echo "$result5" | jq -r '.tool_input.text')
if [[ "$result_text" != "$original_text" ]]; then
    print_success "Memory hook correctly enhances memory entries"
else
    print_failure "Memory hook should enhance memory entries"
fi

# Test 5: Integration checks
print_info "Testing Integration"

# Test 5.1: All scripts are executable
hooks=("fix-context-injector.sh" "build-planner.sh" "nuke-checkpoint.sh" "command-memory.sh")
for hook in "${hooks[@]}"; do
    if [[ -x "$hook" ]]; then
        print_success "Hook is executable: $hook"
    else
        print_failure "Hook is not executable: $hook"
    fi
done

# Test 5.2: JSON processing works
test_json='{"message": "test", "tool_name": "test", "tool_input": {"text": "test"}}'
if echo "$test_json" | jq . >/dev/null 2>&1; then
    print_success "JSON processing available"
else
    print_failure "JSON processing not available (jq required)"
fi

# Summary
echo ""
echo "=== Test Results Summary ==="
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"

if [[ $TESTS_FAILED -eq 0 ]]; then
    print_success "All tests passed! Command-specific hooks are working correctly."
    exit 0
else
    print_failure "Some tests failed. Check the output above for details."
    exit 1
fi