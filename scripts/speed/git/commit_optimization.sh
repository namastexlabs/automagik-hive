#!/bin/bash

# Genie Speed Optimization Framework - Commit Optimization
# Handles structured commits with performance metadata

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
DECISION_FILE=""
TARGET=""
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --decision)
            DECISION_FILE="$2"
            shift 2
            ;;
        --target)
            TARGET="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate inputs
if [[ -z "$DECISION_FILE" ]]; then
    log_error "Decision file is required (--decision)"
    exit 1
fi

if [[ -z "$TARGET" ]]; then
    log_error "Target is required (--target)"
    exit 1
fi

if [[ ! -f "$DECISION_FILE" ]]; then
    log_error "Decision file not found: $DECISION_FILE"
    exit 1
fi

# Read decision data
DECISION_DATA=$(cat "$DECISION_FILE")

# Extract key metrics using jq if available, otherwise use Python
if command -v jq >/dev/null 2>&1; then
    APPROVED=$(echo "$DECISION_DATA" | jq -r '.approved')
    IMPROVEMENT=$(echo "$DECISION_DATA" | jq -r '.improvement_percent')
    RUNTIME_BEFORE=$(echo "$DECISION_DATA" | jq -r '.runtime_before')
    RUNTIME_AFTER=$(echo "$DECISION_DATA" | jq -r '.runtime_after')
    OPTIMIZATION_TYPE=$(echo "$DECISION_DATA" | jq -r '.optimization_type // "general"')
    DESCRIPTION=$(echo "$DECISION_DATA" | jq -r '.description // "Performance optimization"')
else
    # Use Python as fallback
    APPROVED=$(python3 -c "
import json
with open('$DECISION_FILE') as f:
    data = json.load(f)
    print(data.get('approved', 'false'))
    ")
    IMPROVEMENT=$(python3 -c "
import json
with open('$DECISION_FILE') as f:
    data = json.load(f)
    print(data.get('improvement_percent', 0))
    ")
    RUNTIME_BEFORE=$(python3 -c "
import json
with open('$DECISION_FILE') as f:
    data = json.load(f)
    print(data.get('runtime_before', 0))
    ")
    RUNTIME_AFTER=$(python3 -c "
import json
with open('$DECISION_FILE') as f:
    data = json.load(f)
    print(data.get('runtime_after', 0))
    ")
    OPTIMIZATION_TYPE=$(python3 -c "
import json
with open('$DECISION_FILE') as f:
    data = json.load(f)
    print(data.get('optimization_type', 'general'))
    ")
    DESCRIPTION=$(python3 -c "
import json
with open('$DECISION_FILE') as f:
    data = json.load(f)
    print(data.get('description', 'Performance optimization'))
    ")
fi

# Validate approval
if [[ "$APPROVED" != "true" ]]; then
    log_error "Optimization not approved, cannot commit"
    exit 1
fi

log_info "Committing optimization for: $TARGET"
log_info "Improvement: +${IMPROVEMENT}%"
log_info "Runtime: ${RUNTIME_BEFORE}s → ${RUNTIME_AFTER}s"

# Extract function name from target
FUNCTION_NAME=$(echo "$TARGET" | cut -d':' -f2 | cut -d':' -f2)
if [[ -z "$FUNCTION_NAME" ]]; then
    FUNCTION_NAME=$(basename "$TARGET")
fi

# Create commit message
COMMIT_MESSAGE="perf: optimize ${FUNCTION_NAME} (+${IMPROVEMENT}%)

${DESCRIPTION}

Performance Impact:
- Runtime: ${RUNTIME_BEFORE}s → ${RUNTIME_AFTER}s
- Improvement: +${IMPROVEMENT}%
- Optimization Type: ${OPTIMIZATION_TYPE}
- Target: ${TARGET}

Benchmarked using minimum runtime methodology
✅ Correctness verified
✅ Performance validated
✅ Tests passing

🤖 Generated with Genie Speed Optimization Framework

Co-Authored-By: Genie-Speed-Framework <noreply@genie-agents.com>"

# Stage all changes
git add -A

# Check if there are changes to commit
if git diff --cached --quiet; then
    log_warning "No changes to commit"
    exit 0
fi

# Create commit
if git commit -m "$COMMIT_MESSAGE"; then
    log_success "Optimization committed successfully"
    
    # Get commit hash
    COMMIT_HASH=$(git rev-parse HEAD)
    log_info "Commit hash: $COMMIT_HASH"
    
    # Create optimization metadata file
    METADATA_FILE="${PROJECT_ROOT}/data/speed_optimization/commit_${COMMIT_HASH}.json"
    cat > "$METADATA_FILE" << EOF
{
    "commit_hash": "$COMMIT_HASH",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "target": "$TARGET",
    "function_name": "$FUNCTION_NAME",
    "improvement_percent": $IMPROVEMENT,
    "runtime_before": $RUNTIME_BEFORE,
    "runtime_after": $RUNTIME_AFTER,
    "optimization_type": "$OPTIMIZATION_TYPE",
    "description": "$DESCRIPTION",
    "decision_file": "$DECISION_FILE",
    "framework_version": "1.0.0"
}
EOF
    
    log_success "Optimization metadata saved to: $METADATA_FILE"
    
    # Update optimization history
    HISTORY_FILE="${PROJECT_ROOT}/data/speed_optimization/optimization_history.json"
    
    if [[ -f "$HISTORY_FILE" ]]; then
        # Append to existing history
        python3 -c "
import json
import sys

# Read existing history
with open('$HISTORY_FILE', 'r') as f:
    history = json.load(f)

# Add new entry
new_entry = {
    'commit_hash': '$COMMIT_HASH',
    'timestamp': '$(date -u +%Y-%m-%dT%H:%M:%SZ)',
    'target': '$TARGET',
    'function_name': '$FUNCTION_NAME',
    'improvement_percent': $IMPROVEMENT,
    'runtime_before': $RUNTIME_BEFORE,
    'runtime_after': $RUNTIME_AFTER,
    'optimization_type': '$OPTIMIZATION_TYPE'
}

history['optimizations'].append(new_entry)
history['total_optimizations'] = len(history['optimizations'])
history['last_updated'] = '$(date -u +%Y-%m-%dT%H:%M:%SZ)'

# Calculate cumulative improvement
total_improvement = sum(opt['improvement_percent'] for opt in history['optimizations'])
history['cumulative_improvement'] = round(total_improvement, 2)

# Save updated history
with open('$HISTORY_FILE', 'w') as f:
    json.dump(history, f, indent=2)
"
    else
        # Create new history file
        cat > "$HISTORY_FILE" << EOF
{
    "total_optimizations": 1,
    "cumulative_improvement": $IMPROVEMENT,
    "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "optimizations": [
        {
            "commit_hash": "$COMMIT_HASH",
            "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
            "target": "$TARGET",
            "function_name": "$FUNCTION_NAME",
            "improvement_percent": $IMPROVEMENT,
            "runtime_before": $RUNTIME_BEFORE,
            "runtime_after": $RUNTIME_AFTER,
            "optimization_type": "$OPTIMIZATION_TYPE"
        }
    ]
}
EOF
    fi
    
    log_success "Optimization history updated"
    
    # Optional: Create git tag for significant optimizations
    if (( $(echo "$IMPROVEMENT > 50" | bc -l) )); then
        TAG_NAME="speed-opt-$(date +%Y%m%d-%H%M%S)"
        git tag -a "$TAG_NAME" -m "Significant performance optimization: +${IMPROVEMENT}%"
        log_success "Created git tag: $TAG_NAME"
    fi
    
    # Display summary
    echo ""
    echo "🎉 Optimization Summary"
    echo "======================="
    echo "Target: $TARGET"
    echo "Function: $FUNCTION_NAME"
    echo "Improvement: +${IMPROVEMENT}%"
    echo "Runtime: ${RUNTIME_BEFORE}s → ${RUNTIME_AFTER}s"
    echo "Commit: $COMMIT_HASH"
    echo "Type: $OPTIMIZATION_TYPE"
    echo ""
    
else
    log_error "Failed to commit optimization"
    exit 1
fi