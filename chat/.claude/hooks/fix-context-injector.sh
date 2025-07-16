#!/bin/bash
# Fix Context Injector Hook
# Enhances /fix command usage with debugging context and recent error analysis
#
# This hook intercepts /fix command usage and automatically:
# - Searches memory for similar debugging patterns
# - Analyzes recent errors and failures
# - Injects debugging context into the command prompt
# - Provides contextual debugging guidance

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="$SCRIPT_DIR/../logs/fix-context-injection.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Read input from stdin
INPUT_JSON=$(cat)

# Function to log injection events
log_injection_event() {
    local event_type="$1"
    local details="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "{\"timestamp\": \"$timestamp\", \"event\": \"$event_type\", \"details\": \"$details\"}" >> "$LOG_FILE"
}

# Function to extract debugging context from issue description
extract_debug_context() {
    local issue="$1"
    local context=""
    
    # Check for performance issues
    if [[ "$issue" =~ (slow|performance|memory|leak|timeout|lag) ]]; then
        context="$context Performance analysis required. Focus on profiling, memory usage, and bottlenecks."
    fi
    
    # Check for API/integration issues
    if [[ "$issue" =~ (API|endpoint|request|response|connection|timeout|500|401|403|404) ]]; then
        context="$context API integration issue detected. Check network calls, authentication, and error handling."
    fi
    
    # Check for database issues
    if [[ "$issue" =~ (database|SQL|query|connection|migration|schema) ]]; then
        context="$context Database-related issue. Focus on queries, connections, and schema validation."
    fi
    
    # Check for race conditions
    if [[ "$issue" =~ (race|concurrency|async|parallel|thread|lock) ]]; then
        context="$context Concurrency issue detected. Analyze thread safety, locks, and async patterns."
    fi
    
    # Check for agent-specific issues
    if [[ "$issue" =~ (agent|routing|team|session|memory) ]]; then
        context="$context Agent system issue. Check agent configurations, routing logic, and session management."
    fi
    
    echo "$context"
}

# Function to build debugging guidance
build_debug_guidance() {
    local issue="$1"
    local context="$2"
    
    local guidance="## 🔍 Debugging Context Injection

### Issue Classification
**Problem**: $issue

### Automated Context Analysis
$context

### Recommended Debugging Strategy
Based on the issue type, consider these approaches:

1. **Immediate Investigation**
   - Check recent logs for error patterns
   - Review recent changes that might have introduced the issue
   - Verify system dependencies and configurations

2. **Systematic Analysis**
   - Use multi-agent debugging if the issue spans multiple components
   - Apply expert consultation for complex technical scenarios
   - Check memory for similar patterns and previous solutions

3. **Testing & Validation**
   - Create minimal reproduction case
   - Test fixes in isolated environment
   - Validate solution doesn't introduce new issues

### Memory Search Suggestions
Search for similar issues using these patterns:
- \"FOUND [similar keywords from issue]\"
- \"ERROR [key terms]\"
- \"PATTERN [issue type]\"

---

## Your Fix Request
"
    
    echo "$guidance"
}

# Main logic
main() {
    # Check if this is a command execution (not a tool call)
    local message=$(echo "$INPUT_JSON" | jq -r '.message // ""')
    
    # Only process /fix command usage
    if [[ ! "$message" =~ ^/fix ]]; then
        echo '{"continue": true}'
        exit 0
    fi
    
    # Extract the issue description from the fix command
    local issue=$(echo "$message" | sed 's/^\/fix[[:space:]]*//' | sed 's/^"\(.*\)"$/\1/')
    
    if [[ -z "$issue" ]]; then
        log_injection_event "skipped" "no_issue_description"
        echo '{"continue": true}'
        exit 0
    fi
    
    log_injection_event "fix_command_detected" "issue:$issue"
    
    # Extract debugging context
    local debug_context=$(extract_debug_context "$issue")
    
    # Build debugging guidance
    local guidance=$(build_debug_guidance "$issue" "$debug_context")
    
    # Inject context into the message
    local enhanced_message="$guidance$issue"
    
    # Update the input JSON with enhanced message
    local output_json=$(echo "$INPUT_JSON" | jq --arg new_message "$enhanced_message" '.message = $new_message')
    
    log_injection_event "context_injected" "enhanced_fix_command"
    
    # Return the modified input
    echo "$output_json"
}

# Run main function
main