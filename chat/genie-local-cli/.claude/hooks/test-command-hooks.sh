#!/bin/bash
# Command-Specific Hooks Test Suite
# Comprehensive testing for all new command-specific hooks
#
# This script tests the functionality of:
# - fix-context-injector.sh
# - build-planner.sh
# - nuke-checkpoint.sh
# - command-memory.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HOOKS_DIR="$SCRIPT_DIR"
TEST_LOG="$SCRIPT_DIR/../logs/hook-tests.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Initialize test log
mkdir -p "$(dirname "$TEST_LOG")"
echo "=== Command Hooks Test Session $(date) ===" > "$TEST_LOG"

# Helper functions
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
    echo "=== $1 ===" >> "$TEST_LOG"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    echo "✓ $1" >> "$TEST_LOG"
    ((TESTS_PASSED++))
}

print_failure() {
    echo -e "${RED}✗ $1${NC}"
    echo "✗ $1" >> "$TEST_LOG"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
    echo "ℹ $1" >> "$TEST_LOG"
}

# Test helper: create test JSON input
create_test_input() {
    local message="$1"
    local tool_name="${2:-}"
    local tool_input="${3:-{}}"
    
    if [[ -n "$tool_name" ]]; then
        jq -n --arg msg "$message" --arg tool "$tool_name" --argjson input "$tool_input" \
            '{message: $msg, tool_name: $tool, tool_input: $input}'
    else
        jq -n --arg msg "$message" '{message: $msg}'
    fi
}

# Test helper: run hook with input
run_hook_test() {
    local hook_script="$1"
    local test_input="$2"
    local expected_change="$3"
    
    if [[ ! -f "$hook_script" ]]; then
        print_failure "Hook script not found: $hook_script"
        return 1
    fi
    
    if [[ ! -x "$hook_script" ]]; then
        print_failure "Hook script not executable: $hook_script"
        return 1
    fi
    
    local result
    result=$(echo "$test_input" | "$hook_script" 2>&1)
    local exit_code=$?
    
    if [[ $exit_code -ne 0 ]]; then
        print_failure "Hook failed with exit code $exit_code: $result"
        return 1
    fi
    
    # Check if result is valid JSON
    if ! echo "$result" | jq . >/dev/null 2>&1; then
        print_failure "Hook returned invalid JSON: $result"
        return 1
    fi
    
    # Check if expected change occurred
    if [[ "$expected_change" == "continue" ]]; then
        local continue_flag
        continue_flag=$(echo "$result" | jq -r '.continue // false')
        if [[ "$continue_flag" == "true" ]]; then
            print_success "Hook correctly returned continue=true"
        else
            print_failure "Hook should have returned continue=true but returned: $result"
            return 1
        fi
    elif [[ "$expected_change" == "modified" ]]; then
        local original_message
        original_message=$(echo "$test_input" | jq -r '.message // ""')
        local result_message
        result_message=$(echo "$result" | jq -r '.message // ""')
        
        if [[ "$result_message" != "$original_message" ]]; then
            print_success "Hook correctly modified message content"
        else
            print_failure "Hook should have modified message but didn't"
            return 1
        fi
    fi
    
    return 0
}

# Test 1: Fix Context Injector
test_fix_context_injector() {
    print_header "Testing Fix Context Injector"
    
    local hook_script="$HOOKS_DIR/fix-context-injector.sh"
    
    # Test 1.1: Non-fix command should pass through
    print_info "Test 1.1: Non-fix command pass-through"
    local input1
    input1=$(create_test_input "/build something")
    run_hook_test "$hook_script" "$input1" "continue"
    
    # Test 1.2: Fix command should be enhanced
    print_info "Test 1.2: Fix command enhancement"
    local input2
    input2=$(create_test_input "/fix API returns 500 error")
    run_hook_test "$hook_script" "$input2" "modified"
    
    # Test 1.3: Fix command with performance keywords
    print_info "Test 1.3: Fix command with performance context"
    local input3
    input3=$(create_test_input "/fix Memory leak in agent sessions")
    run_hook_test "$hook_script" "$input3" "modified"
    
    # Test 1.4: Fix command with agent-specific keywords
    print_info "Test 1.4: Fix command with agent context"
    local input4
    input4=$(create_test_input "/fix Agent routing fails for Portuguese queries")
    run_hook_test "$hook_script" "$input4" "modified"
    
    # Test 1.5: Empty fix command should pass through
    print_info "Test 1.5: Empty fix command"
    local input5
    input5=$(create_test_input "/fix")
    run_hook_test "$hook_script" "$input5" "continue"
}

# Test 2: Build Planner
test_build_planner() {
    print_header "Testing Build Planner"
    
    local hook_script="$HOOKS_DIR/build-planner.sh"
    
    # Test 2.1: Non-build command should pass through
    print_info "Test 2.1: Non-build command pass-through"
    local input1
    input1=$(create_test_input "/debug something")
    run_hook_test "$hook_script" "$input1" "continue"
    
    # Test 2.2: Simple build command (LOW complexity)
    print_info "Test 2.2: Simple build command"
    local input2
    input2=$(create_test_input "/build Create validation function for email")
    run_hook_test "$hook_script" "$input2" "modified"
    
    # Test 2.3: API build command (MEDIUM complexity)
    print_info "Test 2.3: API build command"
    local input3
    input3=$(create_test_input "/build Create REST API for user management")
    run_hook_test "$hook_script" "$input3" "modified"
    
    # Test 2.4: System build command (HIGH complexity)
    print_info "Test 2.4: System build command"
    local input4
    input4=$(create_test_input "/build Implement distributed authentication system")
    run_hook_test "$hook_script" "$input4" "modified"
    
    # Test 2.5: Agent-specific build command
    print_info "Test 2.5: Agent-specific build command"
    local input5
    input5=$(create_test_input "/build Create new agent with team routing")
    run_hook_test "$hook_script" "$input5" "modified"
}

# Test 3: Nuke Checkpoint
test_nuke_checkpoint() {
    print_header "Testing Nuke Checkpoint"
    
    local hook_script="$HOOKS_DIR/nuke-checkpoint.sh"
    
    # Test 3.1: Non-nuke command should pass through
    print_info "Test 3.1: Non-nuke command pass-through"
    local input1
    input1=$(create_test_input "/fix something")
    run_hook_test "$hook_script" "$input1" "continue"
    
    # Test 3.2: Nuke command should be enhanced (if in git repo)
    print_info "Test 3.2: Nuke command enhancement"
    local input2
    input2=$(create_test_input "/nuke Race condition in payment processing")
    
    # Check if we're in a git repository
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        run_hook_test "$hook_script" "$input2" "modified"
    else
        print_info "Not in git repository, nuke checkpoint will pass through"
        run_hook_test "$hook_script" "$input2" "continue"
    fi
    
    # Test 3.3: Empty nuke command should pass through
    print_info "Test 3.3: Empty nuke command"
    local input3
    input3=$(create_test_input "/nuke")
    run_hook_test "$hook_script" "$input3" "continue"
}

# Test 4: Command Memory
test_command_memory() {
    print_header "Testing Command Memory"
    
    local hook_script="$HOOKS_DIR/command-memory.sh"
    
    # Test 4.1: Non-memory tool should pass through
    print_info "Test 4.1: Non-memory tool pass-through"
    local input1
    input1=$(create_test_input "" "Task" '{"prompt": "Do something"}')
    run_hook_test "$hook_script" "$input1" "continue"
    
    # Test 4.2: Memory add should be enhanced
    print_info "Test 4.2: Memory add enhancement"
    local input2
    input2=$(create_test_input "" "mcp__genie-memory__add_memories" '{"text": "FOUND solution for API timeout issue"}')
    run_hook_test "$hook_script" "$input2" "modified"
    
    # Test 4.3: Memory add with pattern content
    print_info "Test 4.3: Memory add with pattern content"
    local input3
    input3=$(create_test_input "" "mcp__genie-memory__add_memories" '{"text": "PATTERN: Agent implementation using YAML configuration"}')
    run_hook_test "$hook_script" "$input3" "modified"
    
    # Test 4.4: Memory add with empty text should pass through
    print_info "Test 4.4: Memory add with empty text"
    local input4
    input4=$(create_test_input "" "mcp__genie-memory__add_memories" '{"text": ""}')
    run_hook_test "$hook_script" "$input4" "continue"
}

# Test 5: Integration Tests
test_integration() {
    print_header "Testing Integration Scenarios"
    
    # Test 5.1: Verify log directories are created
    print_info "Test 5.1: Log directory creation"
    local log_dirs=(
        "$SCRIPT_DIR/../logs"
        "$(dirname "$SCRIPT_DIR/../logs/fix-context-injection.log")"
        "$(dirname "$SCRIPT_DIR/../logs/build-planning.log")"
        "$(dirname "$SCRIPT_DIR/../logs/nuke-checkpoint.log")"
        "$(dirname "$SCRIPT_DIR/../logs/command-memory.log")"
    )
    
    for log_dir in "${log_dirs[@]}"; do
        if [[ -d "$log_dir" ]]; then
            print_success "Log directory exists: $log_dir"
        else
            print_failure "Log directory missing: $log_dir"
        fi
    done
    
    # Test 5.2: Verify hook scripts are executable
    print_info "Test 5.2: Hook script permissions"
    local hook_scripts=(
        "$HOOKS_DIR/fix-context-injector.sh"
        "$HOOKS_DIR/build-planner.sh"
        "$HOOKS_DIR/nuke-checkpoint.sh"
        "$HOOKS_DIR/command-memory.sh"
    )
    
    for hook_script in "${hook_scripts[@]}"; do
        if [[ -x "$hook_script" ]]; then
            print_success "Hook is executable: $(basename "$hook_script")"
        else
            print_failure "Hook is not executable: $(basename "$hook_script")"
        fi
    done
    
    # Test 5.3: Verify JSON processing capabilities
    print_info "Test 5.3: JSON processing"
    local test_json='{"message": "test", "tool_name": "test", "tool_input": {"text": "test"}}'
    if echo "$test_json" | jq . >/dev/null 2>&1; then
        print_success "JSON processing available"
    else
        print_failure "JSON processing not available (jq required)"
    fi
}

# Main test execution
main() {
    print_header "Command-Specific Hooks Test Suite"
    
    # Check prerequisites
    if ! command -v jq >/dev/null 2>&1; then
        print_failure "jq is required for JSON processing"
        exit 1
    fi
    
    # Run all tests
    test_fix_context_injector
    test_build_planner
    test_nuke_checkpoint
    test_command_memory
    test_integration
    
    # Print summary
    print_header "Test Results Summary"
    echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
    
    echo "Tests Passed: $TESTS_PASSED" >> "$TEST_LOG"
    echo "Tests Failed: $TESTS_FAILED" >> "$TEST_LOG"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        print_success "All tests passed! Command-specific hooks are working correctly."
        exit 0
    else
        print_failure "Some tests failed. Check the logs for details."
        exit 1
    fi
}

# Run tests
main "$@"