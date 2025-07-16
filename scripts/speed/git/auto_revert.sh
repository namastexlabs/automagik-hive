#!/bin/bash

# Genie Speed Optimization Framework - Auto Revert
# Automatically reverts failed optimizations

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Default values
REASON=""
CHECKPOINT=""
VERBOSE=false
PRESERVE_LOGS=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --reason)
            REASON="$2"
            shift 2
            ;;
        --checkpoint)
            CHECKPOINT="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --no-preserve-logs)
            PRESERVE_LOGS=false
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate inputs
if [[ -z "$REASON" ]]; then
    log_error "Revert reason is required (--reason)"
    exit 1
fi

if [[ -z "$CHECKPOINT" ]]; then
    log_error "Checkpoint is required (--checkpoint)"
    exit 1
fi

log_warning "Starting auto-revert process"
log_info "Reason: $REASON"
log_info "Checkpoint: $CHECKPOINT"

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
log_info "Current branch: $CURRENT_BRANCH"

# Get checkpoint metadata
CHECKPOINT_FILE="${PROJECT_ROOT}/data/speed_optimization/${CHECKPOINT}.json"
if [[ ! -f "$CHECKPOINT_FILE" ]]; then
    log_error "Checkpoint metadata not found: $CHECKPOINT_FILE"
    exit 1
fi

# Read checkpoint data
CHECKPOINT_DATA=$(cat "$CHECKPOINT_FILE")

# Extract checkpoint information
if command -v jq >/dev/null 2>&1; then
    ORIGINAL_COMMIT=$(echo "$CHECKPOINT_DATA" | jq -r '.commit')
    ORIGINAL_BRANCH=$(echo "$CHECKPOINT_DATA" | jq -r '.branch // "main"')
    TARGET=$(echo "$CHECKPOINT_DATA" | jq -r '.target')
else
    # Use Python as fallback
    ORIGINAL_COMMIT=$(python3 -c "
import json
with open('$CHECKPOINT_FILE') as f:
    data = json.load(f)
    print(data.get('commit', ''))
    ")
    ORIGINAL_BRANCH=$(python3 -c "
import json
with open('$CHECKPOINT_FILE') as f:
    data = json.load(f)
    print(data.get('branch', 'main'))
    ")
    TARGET=$(python3 -c "
import json
with open('$CHECKPOINT_FILE') as f:
    data = json.load(f)
    print(data.get('target', ''))
    ")
fi

log_info "Original commit: $ORIGINAL_COMMIT"
log_info "Original branch: $ORIGINAL_BRANCH"
log_info "Target: $TARGET"

# Create revert metadata
REVERT_TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
REVERT_ID="revert-$(date +%s)"

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    log_warning "Uncommitted changes detected"
    
    # Stash changes if preserving logs
    if [[ "$PRESERVE_LOGS" == "true" ]]; then
        git stash push -m "Auto-revert stash: $REASON"
        log_info "Changes stashed for preservation"
    else
        log_warning "Discarding uncommitted changes"
    fi
fi

# Determine revert strategy based on reason
case "$REASON" in
    "insufficient_improvement")
        REVERT_TYPE="performance_threshold"
        ;;
    "correctness_failure")
        REVERT_TYPE="correctness_verification"
        ;;
    "timeout")
        REVERT_TYPE="timeout_exceeded"
        ;;
    "test_failure")
        REVERT_TYPE="test_failure"
        ;;
    "all_attempts_failed")
        REVERT_TYPE="exhausted_attempts"
        ;;
    *)
        REVERT_TYPE="general"
        ;;
esac

# Perform revert based on current situation
if [[ "$CURRENT_BRANCH" == "$CHECKPOINT" ]]; then
    log_info "Reverting changes in optimization branch"
    
    # Reset to original commit
    if git reset --hard "$ORIGINAL_COMMIT"; then
        log_success "Reset to original commit: $ORIGINAL_COMMIT"
    else
        log_error "Failed to reset to original commit"
        exit 1
    fi
    
    # Switch back to original branch
    if git checkout "$ORIGINAL_BRANCH"; then
        log_success "Switched back to original branch: $ORIGINAL_BRANCH"
    else
        log_error "Failed to switch to original branch"
        exit 1
    fi
    
    # Delete optimization branch
    if git branch -D "$CHECKPOINT"; then
        log_success "Deleted optimization branch: $CHECKPOINT"
    else
        log_warning "Failed to delete optimization branch"
    fi
    
else
    log_info "Reverting committed changes"
    
    # Check if we're on the correct branch
    if [[ "$CURRENT_BRANCH" != "$ORIGINAL_BRANCH" ]]; then
        log_info "Switching to original branch: $ORIGINAL_BRANCH"
        git checkout "$ORIGINAL_BRANCH"
    fi
    
    # Find commits to revert (between original and current)
    COMMITS_TO_REVERT=$(git rev-list --reverse "${ORIGINAL_COMMIT}..HEAD")
    
    if [[ -n "$COMMITS_TO_REVERT" ]]; then
        log_info "Found commits to revert:"
        echo "$COMMITS_TO_REVERT" | while read -r commit; do
            log_info "  $commit: $(git log --format='%s' -n 1 "$commit")"
        done
        
        # Revert each commit
        echo "$COMMITS_TO_REVERT" | while read -r commit; do
            if git revert --no-edit "$commit"; then
                log_success "Reverted commit: $commit"
            else
                log_error "Failed to revert commit: $commit"
                
                # Handle conflicts
                if git status --porcelain | grep -q "^UU"; then
                    log_warning "Merge conflicts detected during revert"
                    
                    # Try to resolve conflicts automatically
                    if [[ "$PRESERVE_LOGS" == "true" ]]; then
                        log_info "Attempting automatic conflict resolution"
                        
                        # For now, abort the revert and let user handle
                        git revert --abort
                        log_error "Automatic conflict resolution not implemented"
                        log_error "Please resolve conflicts manually"
                        exit 1
                    else
                        # Abort revert and force reset
                        git revert --abort
                        git reset --hard "$ORIGINAL_COMMIT"
                        log_warning "Force reset to original commit due to conflicts"
                    fi
                fi
            fi
        done
    else
        log_info "No commits to revert"
    fi
fi

# Create revert record
REVERT_RECORD="${PROJECT_ROOT}/data/speed_optimization/revert_${REVERT_ID}.json"
cat > "$REVERT_RECORD" << EOF
{
    "revert_id": "$REVERT_ID",
    "timestamp": "$REVERT_TIMESTAMP",
    "checkpoint": "$CHECKPOINT",
    "reason": "$REASON",
    "revert_type": "$REVERT_TYPE",
    "target": "$TARGET",
    "original_commit": "$ORIGINAL_COMMIT",
    "original_branch": "$ORIGINAL_BRANCH",
    "current_branch": "$CURRENT_BRANCH",
    "preserve_logs": $PRESERVE_LOGS
}
EOF

log_success "Revert record created: $REVERT_RECORD"

# Update revert history
REVERT_HISTORY="${PROJECT_ROOT}/data/speed_optimization/revert_history.json"

if [[ -f "$REVERT_HISTORY" ]]; then
    # Append to existing history
    python3 -c "
import json

# Read existing history
with open('$REVERT_HISTORY', 'r') as f:
    history = json.load(f)

# Add new entry
new_entry = {
    'revert_id': '$REVERT_ID',
    'timestamp': '$REVERT_TIMESTAMP',
    'checkpoint': '$CHECKPOINT',
    'reason': '$REASON',
    'revert_type': '$REVERT_TYPE',
    'target': '$TARGET'
}

history['reverts'].append(new_entry)
history['total_reverts'] = len(history['reverts'])
history['last_updated'] = '$REVERT_TIMESTAMP'

# Count revert types
revert_counts = {}
for revert in history['reverts']:
    revert_type = revert['revert_type']
    revert_counts[revert_type] = revert_counts.get(revert_type, 0) + 1

history['revert_counts'] = revert_counts

# Save updated history
with open('$REVERT_HISTORY', 'w') as f:
    json.dump(history, f, indent=2)
"
else
    # Create new history file
    cat > "$REVERT_HISTORY" << EOF
{
    "total_reverts": 1,
    "last_updated": "$REVERT_TIMESTAMP",
    "revert_counts": {
        "$REVERT_TYPE": 1
    },
    "reverts": [
        {
            "revert_id": "$REVERT_ID",
            "timestamp": "$REVERT_TIMESTAMP",
            "checkpoint": "$CHECKPOINT",
            "reason": "$REASON",
            "revert_type": "$REVERT_TYPE",
            "target": "$TARGET"
        }
    ]
}
EOF
fi

log_success "Revert history updated"

# Clean up temporary files if not preserving logs
if [[ "$PRESERVE_LOGS" == "false" ]]; then
    log_info "Cleaning up temporary files"
    
    # Remove checkpoint files
    rm -f "${PROJECT_ROOT}/data/speed_optimization/${CHECKPOINT}.json"
    rm -f "${PROJECT_ROOT}/data/speed_optimization/baseline_${CHECKPOINT}.json"
    rm -f "${PROJECT_ROOT}/data/speed_optimization/optimization_${CHECKPOINT}_"*.py
    rm -f "${PROJECT_ROOT}/data/speed_optimization/benchmark_${CHECKPOINT}_"*.json
    rm -f "${PROJECT_ROOT}/data/speed_optimization/decision_${CHECKPOINT}_"*.json
    
    log_success "Temporary files cleaned up"
fi

# Restore stashed changes if they exist
if [[ "$PRESERVE_LOGS" == "true" ]] && git stash list | grep -q "Auto-revert stash: $REASON"; then
    log_info "Restoring stashed changes"
    if git stash pop; then
        log_success "Stashed changes restored"
    else
        log_warning "Failed to restore stashed changes (conflicts may exist)"
    fi
fi

# Display summary
echo ""
echo "🔄 Revert Summary"
echo "================="
echo "Reason: $REASON"
echo "Type: $REVERT_TYPE"
echo "Checkpoint: $CHECKPOINT"
echo "Target: $TARGET"
echo "Original commit: $ORIGINAL_COMMIT"
echo "Current branch: $(git branch --show-current)"
echo "Revert ID: $REVERT_ID"
echo "Logs preserved: $PRESERVE_LOGS"
echo ""

log_success "Auto-revert completed successfully"

# Optional: Send notification (if configured)
if [[ -n "${SPEED_OPT_WEBHOOK:-}" ]]; then
    curl -X POST "$SPEED_OPT_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"event\": \"optimization_reverted\",
            \"reason\": \"$REASON\",
            \"target\": \"$TARGET\",
            \"checkpoint\": \"$CHECKPOINT\",
            \"timestamp\": \"$REVERT_TIMESTAMP\"
        }" 2>/dev/null || log_warning "Failed to send webhook notification"
fi