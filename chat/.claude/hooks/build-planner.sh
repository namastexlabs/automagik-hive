#!/bin/bash
# Build Planner Hook
# Enhances /build command usage with implementation planning and architecture guidance
#
# This hook intercepts /build command usage and automatically:
# - Analyzes implementation complexity and suggests appropriate strategy
# - Searches memory for similar implementation patterns
# - Provides architectural guidance based on project structure
# - Injects implementation planning context into the command prompt

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="$SCRIPT_DIR/../logs/build-planning.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Read input from stdin
INPUT_JSON=$(cat)

# Function to log planning events
log_planning_event() {
    local event_type="$1"
    local details="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "{\"timestamp\": \"$timestamp\", \"event\": \"$event_type\", \"details\": \"$details\"}" >> "$LOG_FILE"
}

# Function to analyze implementation complexity
analyze_complexity() {
    local requirement="$1"
    local complexity="LOW"
    local strategy="direct"
    
    # Check for high complexity indicators
    if [[ "$requirement" =~ (system|architecture|integration|complex|multi|scale|distributed|microservice) ]]; then
        complexity="HIGH"
        strategy="multi-agent"
    elif [[ "$requirement" =~ (API|endpoint|service|database|authentication|payment|workflow|pipeline) ]]; then
        complexity="MEDIUM"
        strategy="pattern-analysis"
    elif [[ "$requirement" =~ (function|util|helper|validation|format|parse|calculate) ]]; then
        complexity="LOW"
        strategy="direct"
    fi
    
    echo "$complexity:$strategy"
}

# Function to identify project patterns
identify_patterns() {
    local requirement="$1"
    local patterns=""
    
    # Check for agent-related patterns
    if [[ "$requirement" =~ (agent|team|routing|session|memory|knowledge) ]]; then
        patterns="$patterns Agent V2 Architecture (YAML-configured agents/teams)"
    fi
    
    # Check for API patterns
    if [[ "$requirement" =~ (API|endpoint|REST|route|handler) ]]; then
        patterns="$patterns FastAPI endpoint pattern with Pydantic validation"
    fi
    
    # Check for database patterns
    if [[ "$requirement" =~ (database|model|schema|migration|query) ]]; then
        patterns="$patterns SQLAlchemy ORM with auto-migration support"
    fi
    
    # Check for monitoring patterns
    if [[ "$requirement" =~ (monitoring|metrics|logging|analytics|alert) ]]; then
        patterns="$patterns Prometheus metrics with Grafana dashboards"
    fi
    
    # Check for integration patterns
    if [[ "$requirement" =~ (WhatsApp|notification|email|external|MCP) ]]; then
        patterns="$patterns MCP server integration pattern"
    fi
    
    echo "$patterns"
}

# Function to build implementation guidance
build_implementation_guidance() {
    local requirement="$1"
    local complexity_info="$2"
    local patterns="$3"
    
    local complexity=$(echo "$complexity_info" | cut -d':' -f1)
    local strategy=$(echo "$complexity_info" | cut -d':' -f2)
    
    local guidance="## 🚀 Implementation Planning Context

### Requirement Analysis
**Feature**: $requirement
**Complexity**: $complexity
**Strategy**: $strategy

### Project Pattern Analysis
$patterns

### Implementation Strategy Recommendation

"

    case "$strategy" in
        "direct")
            guidance="$guidance**Direct Implementation Approach**
- Single file implementation following existing patterns
- Minimal dependencies and straightforward logic
- Focus on code quality and type safety
- Follow KISS principle for simple, maintainable code"
            ;;
        "pattern-analysis")
            guidance="$guidance**Pattern-Based Implementation Approach**
- Analyze existing similar implementations in the codebase
- Use 1-2 sub-agents for guidance and validation
- Follow established project conventions and patterns
- Consider dependencies and integration points"
            ;;
        "multi-agent")
            guidance="$guidance**Multi-Agent Design Approach**
- Deploy 2-4 specialized sub-agents for comprehensive analysis
- Consider architectural implications and scalability
- Expert consultation recommended for complex decisions
- Plan for proper testing and validation"
            ;;
    esac

    guidance="$guidance

### Architecture Considerations
Based on your Genie Agents V2 architecture:

1. **Configuration**: Use YAML files for agent/team configurations
2. **Database**: Leverage PostgreSQL with auto-migrations
3. **Monitoring**: Include metrics collection for new endpoints
4. **Security**: Sanitize responses and validate inputs
5. **Testing**: Create unit and integration tests
6. **Documentation**: Add proper docstrings and type hints

### Memory Search Suggestions
Search for similar implementations using these patterns:
- \"PATTERN implementation [feature type]\"
- \"FOUND [similar functionality]\"
- \"TASK [related work]\"

### Expert Consultation Triggers
Consider using mcp__gemini__consult_gemini if:
- Architecture decisions are complex
- Performance implications are significant
- Security considerations are critical
- Integration patterns are unclear

---

## Your Build Request
"
    
    echo "$guidance"
}

# Main logic
main() {
    # Check if this is a command execution (not a tool call)
    local message=$(echo "$INPUT_JSON" | jq -r '.message // ""')
    
    # Only process /build command usage
    if [[ ! "$message" =~ ^/build ]]; then
        echo '{"continue": true}'
        exit 0
    fi
    
    # Extract the requirement from the build command
    local requirement=$(echo "$message" | sed 's/^\/build[[:space:]]*//' | sed 's/^"\(.*\)"$/\1/')
    
    if [[ -z "$requirement" ]]; then
        log_planning_event "skipped" "no_requirement_description"
        echo '{"continue": true}'
        exit 0
    fi
    
    log_planning_event "build_command_detected" "requirement:$requirement"
    
    # Analyze complexity and suggest strategy
    local complexity_info=$(analyze_complexity "$requirement")
    
    # Identify relevant project patterns
    local patterns=$(identify_patterns "$requirement")
    
    # Build implementation guidance
    local guidance=$(build_implementation_guidance "$requirement" "$complexity_info" "$patterns")
    
    # Inject context into the message
    local enhanced_message="$guidance$requirement"
    
    # Update the input JSON with enhanced message
    local output_json=$(echo "$INPUT_JSON" | jq --arg new_message "$enhanced_message" '.message = $new_message')
    
    log_planning_event "context_injected" "enhanced_build_command"
    
    # Return the modified input
    echo "$output_json"
}

# Run main function
main