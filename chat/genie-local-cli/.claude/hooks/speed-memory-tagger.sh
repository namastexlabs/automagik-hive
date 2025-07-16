#!/bin/bash

# Speed Optimization Memory Tagger Hook
# Automatically tags memory entries with speed optimization context

set -euo pipefail

# Configuration
WORKSPACE="${WORKSPACE:-$(pwd)}"
CLAUDE_DIR="${WORKSPACE}/.claude"
LOGS_DIR="${CLAUDE_DIR}/logs"

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"

# Logging functions
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" >> "$LOGS_DIR/speed-memory-tagger.log"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$LOGS_DIR/speed-memory-tagger.log"
}

log_debug() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] DEBUG: $1" >> "$LOGS_DIR/speed-memory-tagger.log"
}

# Read the input JSON
INPUT=$(cat)

# Extract the text content from the input
TEXT=$(echo "$INPUT" | jq -r '.text // empty')

# Check if this is speed optimization related content
if [[ ! "$TEXT" =~ (optimization|performance|speed|benchmark|runtime|profiling) ]]; then
    echo "$INPUT"
    exit 0
fi

log_info "Processing speed optimization memory entry"

# Detect optimization content type
detect_content_type() {
    local text="$1"
    local content_type=""
    
    # Optimization results
    if [[ "$text" =~ (optimization.*result|result.*optimization|improved.*performance|performance.*improved) ]]; then
        content_type="OPTIMIZATION_RESULT"
    # Benchmarking data
    elif [[ "$text" =~ (benchmark|benchmarking|runtime.*measurement|performance.*measurement) ]]; then
        content_type="BENCHMARKING_DATA"
    # Algorithm improvements
    elif [[ "$text" =~ (algorithm.*improvement|algorithm.*optimization|complexity.*improvement) ]]; then
        content_type="ALGORITHM_IMPROVEMENT"
    # Performance patterns
    elif [[ "$text" =~ (performance.*pattern|optimization.*pattern|speed.*pattern) ]]; then
        content_type="PERFORMANCE_PATTERN"
    # Framework usage
    elif [[ "$text" =~ (speed.*framework|optimization.*framework|framework.*optimization) ]]; then
        content_type="FRAMEWORK_USAGE"
    # Consensus decisions
    elif [[ "$text" =~ (consensus.*optimization|optimization.*consensus|multi.*model.*decision) ]]; then
        content_type="CONSENSUS_DECISION"
    # Performance issues
    elif [[ "$text" =~ (performance.*issue|slow.*performance|performance.*problem) ]]; then
        content_type="PERFORMANCE_ISSUE"
    # Profiling insights
    elif [[ "$text" =~ (profiling|profile.*analysis|bottleneck|hotspot) ]]; then
        content_type="PROFILING_INSIGHT"
    else
        content_type="GENERAL_OPTIMIZATION"
    fi
    
    echo "$content_type"
}

# Generate optimization-specific tags
generate_optimization_tags() {
    local content_type="$1"
    local text="$2"
    local tags=""
    
    # Base optimization tags
    tags="optimization performance speed"
    
    # Content-specific tags
    case "$content_type" in
        "OPTIMIZATION_RESULT")
            tags="$tags result improvement success measurement"
            ;;
        "BENCHMARKING_DATA")
            tags="$tags benchmark measurement runtime data metrics"
            ;;
        "ALGORITHM_IMPROVEMENT")
            tags="$tags algorithm complexity improvement efficiency"
            ;;
        "PERFORMANCE_PATTERN")
            tags="$tags pattern solution approach methodology"
            ;;
        "FRAMEWORK_USAGE")
            tags="$tags framework tool workflow automation"
            ;;
        "CONSENSUS_DECISION")
            tags="$tags consensus decision validation multi-model"
            ;;
        "PERFORMANCE_ISSUE")
            tags="$tags issue problem bottleneck slow"
            ;;
        "PROFILING_INSIGHT")
            tags="$tags profiling analysis bottleneck hotspot"
            ;;
    esac
    
    # Technical tags based on content keywords
    if [[ "$text" =~ (function.*optimization|optimize.*function) ]]; then
        tags="$tags function-optimization"
    fi
    
    if [[ "$text" =~ (algorithm|complexity|O\(.*\)) ]]; then
        tags="$tags algorithm-optimization"
    fi
    
    if [[ "$text" =~ (cache|caching|memoization) ]]; then
        tags="$tags caching"
    fi
    
    if [[ "$text" =~ (loop|iteration|iterative) ]]; then
        tags="$tags loop-optimization"
    fi
    
    if [[ "$text" =~ (data.*structure|list|dict|set) ]]; then
        tags="$tags data-structure"
    fi
    
    if [[ "$text" =~ (memory|allocation|garbage.*collection) ]]; then
        tags="$tags memory-optimization"
    fi
    
    if [[ "$text" =~ (I\/O|input.*output|file.*operation) ]]; then
        tags="$tags io-optimization"
    fi
    
    if [[ "$text" =~ (database|query|sql) ]]; then
        tags="$tags database-optimization"
    fi
    
    if [[ "$text" =~ (network|http|api) ]]; then
        tags="$tags network-optimization"
    fi
    
    if [[ "$text" =~ (parallel|concurrent|async) ]]; then
        tags="$tags parallel-optimization"
    fi
    
    if [[ "$text" =~ (zen.*consensus|multi.*model|consensus) ]]; then
        tags="$tags zen-consensus"
    fi
    
    if [[ "$text" =~ (git|commit|revert) ]]; then
        tags="$tags git-workflow"
    fi
    
    if [[ "$text" =~ (test|testing|verification) ]]; then
        tags="$tags testing-verification"
    fi
    
    if [[ "$text" =~ (regression|degradation|performance.*loss) ]]; then
        tags="$tags regression-detection"
    fi
    
    if [[ "$text" =~ (baseline|benchmark.*comparison) ]]; then
        tags="$tags baseline-management"
    fi
    
    if [[ "$text" =~ (CI\/CD|continuous.*integration|automation) ]]; then
        tags="$tags ci-cd-integration"
    fi
    
    # Framework-specific tags
    if [[ "$text" =~ (genie.*agents|agents.*optimization) ]]; then
        tags="$tags genie-agents"
    fi
    
    if [[ "$text" =~ (python|py) ]]; then
        tags="$tags python"
    fi
    
    if [[ "$text" =~ (agno|team.*routing) ]]; then
        tags="$tags agno-framework"
    fi
    
    # Temporal tags
    local current_date=$(date +%Y-%m)
    tags="$tags $current_date"
    
    # Remove duplicates and clean up
    tags=$(echo "$tags" | tr ' ' '\n' | sort -u | tr '\n' ' ' | sed 's/^ *//;s/ *$//')
    
    echo "$tags"
}

# Create optimization memory prefix
create_optimization_prefix() {
    local content_type="$1"
    local prefix=""
    
    case "$content_type" in
        "OPTIMIZATION_RESULT")
            prefix="OPTIMIZATION_RESULT:"
            ;;
        "BENCHMARKING_DATA")
            prefix="BENCHMARK_DATA:"
            ;;
        "ALGORITHM_IMPROVEMENT")
            prefix="ALGORITHM_IMPROVEMENT:"
            ;;
        "PERFORMANCE_PATTERN")
            prefix="PERFORMANCE_PATTERN:"
            ;;
        "FRAMEWORK_USAGE")
            prefix="FRAMEWORK_USAGE:"
            ;;
        "CONSENSUS_DECISION")
            prefix="CONSENSUS_DECISION:"
            ;;
        "PERFORMANCE_ISSUE")
            prefix="PERFORMANCE_ISSUE:"
            ;;
        "PROFILING_INSIGHT")
            prefix="PROFILING_INSIGHT:"
            ;;
        *)
            prefix="SPEED_OPTIMIZATION:"
            ;;
    esac
    
    echo "$prefix"
}

# Detect content type
CONTENT_TYPE=$(detect_content_type "$TEXT")
log_debug "Detected content type: $CONTENT_TYPE"

# Generate tags
TAGS=$(generate_optimization_tags "$CONTENT_TYPE" "$TEXT")
log_debug "Generated tags: $TAGS"

# Create prefix
PREFIX=$(create_optimization_prefix "$CONTENT_TYPE")
log_debug "Created prefix: $PREFIX"

# Enhance the text with optimization context
ENHANCED_TEXT="$PREFIX $TEXT

#$(echo "$TAGS" | sed 's/ / #/g')"

# Create the enhanced input JSON
ENHANCED_INPUT=$(echo "$INPUT" | jq --arg text "$ENHANCED_TEXT" '.text = $text')

log_info "Enhanced memory entry with speed optimization tags: $CONTENT_TYPE"

# Output the enhanced input
echo "$ENHANCED_INPUT"