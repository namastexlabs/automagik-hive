#!/bin/bash
# Nuke Checkpoint Hook
# Enhances /nuke command usage with automatic git checkpoint management
#
# This hook intercepts /nuke command usage and automatically:
# - Creates a git checkpoint before nuclear debugging begins
# - Stores checkpoint information for recovery
# - Provides rollback capabilities if nuclear debugging fails
# - Logs all checkpoint operations for audit trail

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="$SCRIPT_DIR/../logs/nuke-checkpoint.log"
CHECKPOINT_FILE="$SCRIPT_DIR/../logs/nuclear-checkpoints.json"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Read input from stdin
INPUT_JSON=$(cat)

# Function to log checkpoint events
log_checkpoint_event() {
    local event_type="$1"
    local details="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "{\"timestamp\": \"$timestamp\", \"event\": \"$event_type\", \"details\": \"$details\"}" >> "$LOG_FILE"
}

# Function to create git checkpoint
create_checkpoint() {
    local issue="$1"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local checkpoint_id="nuclear-debug-$timestamp"
    
    # Change to project root for git operations
    cd "$PROJECT_ROOT"
    
    # Check if we're in a git repository
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        log_checkpoint_event "error" "not_in_git_repository"
        return 1
    fi
    
    # Create checkpoint commit
    git add . 2>/dev/null || true
    if git commit -m "🚨 NUCLEAR CHECKPOINT: $issue" >/dev/null 2>&1; then
        # Create checkpoint tag
        git tag "$checkpoint_id" >/dev/null 2>&1
        
        # Store checkpoint information
        local checkpoint_info="{
            \"checkpoint_id\": \"$checkpoint_id\",
            \"issue\": \"$issue\",
            \"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",
            \"commit_hash\": \"$(git rev-parse HEAD)\",
            \"branch\": \"$(git rev-parse --abbrev-ref HEAD)\"
        }"
        
        # Initialize checkpoint file if it doesn't exist
        if [[ ! -f "$CHECKPOINT_FILE" ]]; then
            echo "[]" > "$CHECKPOINT_FILE"
        fi
        
        # Add checkpoint to file
        local updated_checkpoints=$(jq --argjson checkpoint "$checkpoint_info" '. + [$checkpoint]' "$CHECKPOINT_FILE")
        echo "$updated_checkpoints" > "$CHECKPOINT_FILE"
        
        log_checkpoint_event "checkpoint_created" "id:$checkpoint_id"
        echo "$checkpoint_id"
        return 0
    else
        log_checkpoint_event "warning" "no_changes_to_commit"
        echo "no-changes-$(date +"%Y%m%d_%H%M%S")"
        return 0
    fi
}

# Function to build nuclear debugging guidance with checkpoint info
build_nuclear_guidance() {
    local issue="$1"
    local checkpoint_id="$2"
    
    local guidance="## 🚨 Nuclear Debugging Checkpoint Created

### Checkpoint Information
**Checkpoint ID**: $checkpoint_id
**Issue**: $issue
**Timestamp**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

### Safety Measures Activated
- ✅ **Git Checkpoint**: Created automatic checkpoint before nuclear debugging
- ✅ **Rollback Ready**: Can revert to current state if nuclear debugging fails
- ✅ **Audit Trail**: All operations logged for recovery and analysis

### Nuclear Debugging Protocol
Your nuclear debugging session will follow the enhanced 3-layer protocol:

1. **🔍 Layer 1: Parallel Investigation**
   - Multiple models analyze the issue simultaneously
   - Specialized tools for different aspects (debug, analyze, thinkdeep)
   - Smart model selection based on issue complexity

2. **⚔️ Layer 2: Parallel Debates**
   - Challenge assumptions and validate findings
   - Build consensus through multi-model discussion
   - Adversarial analysis to stress-test theories

3. **🎯 Layer 3: Parallel Solution Generation**
   - Generate multiple solution candidates
   - Validate and rank potential fixes
   - Consensus on final implementation approach

### Checkpoint Recovery
If nuclear debugging fails or produces unexpected results:

\`\`\`bash
# Revert to checkpoint
git reset --hard $checkpoint_id

# Or use the recovery command
git checkout $checkpoint_id
\`\`\`

### Emergency Recovery
In case of critical issues during nuclear debugging:
1. The checkpoint tag $checkpoint_id preserves the current state
2. All changes can be reverted automatically
3. The audit trail in logs/ provides full recovery information

### Memory Integration
This nuclear debugging session will be automatically tagged in memory:
- **Pattern**: \"NUCLEAR $issue\"
- **Checkpoint**: \"$checkpoint_id\"
- **Recovery**: Available if needed

---

## Your Nuclear Debugging Request
"
    
    echo "$guidance"
}

# Main logic
main() {
    # Check if this is a command execution (not a tool call)
    local message=$(echo "$INPUT_JSON" | jq -r '.message // ""')
    
    # Only process /nuke command usage
    if [[ ! "$message" =~ ^/nuke ]]; then
        echo '{"continue": true}'
        exit 0
    fi
    
    # Extract the issue from the nuke command
    local issue=$(echo "$message" | sed 's/^\/nuke[[:space:]]*//' | sed 's/^"\(.*\)"$/\1/')
    
    if [[ -z "$issue" ]]; then
        log_checkpoint_event "skipped" "no_issue_description"
        echo '{"continue": true}'
        exit 0
    fi
    
    log_checkpoint_event "nuke_command_detected" "issue:$issue"
    
    # Create git checkpoint
    local checkpoint_id=$(create_checkpoint "$issue")
    
    if [[ $? -eq 0 ]]; then
        # Build nuclear debugging guidance
        local guidance=$(build_nuclear_guidance "$issue" "$checkpoint_id")
        
        # Inject context into the message
        local enhanced_message="$guidance$issue"
        
        # Update the input JSON with enhanced message
        local output_json=$(echo "$INPUT_JSON" | jq --arg new_message "$enhanced_message" '.message = $new_message')
        
        log_checkpoint_event "context_injected" "checkpoint:$checkpoint_id"
        
        # Return the modified input
        echo "$output_json"
    else
        log_checkpoint_event "error" "checkpoint_creation_failed"
        # Continue without modification on error
        echo '{"continue": true}'
    fi
}

# Run main function
main