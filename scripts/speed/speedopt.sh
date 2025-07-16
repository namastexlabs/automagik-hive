#!/bin/bash

# Genie Speed Optimization Framework - Main Entry Point
# Inspired by Codeflash's "generate and verify" approach

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG_FILE="${PROJECT_ROOT}/config/speed_config.yaml"
CONSENSUS_CONFIG="${PROJECT_ROOT}/config/consensus_config.yaml"

# Default values
MIN_IMPROVEMENT=10
MAX_ATTEMPTS=3
CONSENSUS_REQUIRED=false
MODELS="grok-4-0709,gemini-2.5-pro,o3"
BENCHMARK_RUNS=50
TIMEOUT=300
VERBOSE=false

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

# Usage information
usage() {
    cat << EOF
Genie Speed Optimization Framework

USAGE:
    $0 <command> [options]

COMMANDS:
    optimize-function <file::function>  Optimize a specific function
    optimize-module <path>              Optimize entire module
    optimize-commit <commit>            Optimize changes in commit
    analyze-codebase                    Analyze codebase for optimization candidates
    establish-baseline                  Create performance baselines
    check-regression                    Check for performance regressions
    generate-report                     Generate optimization report

OPTIONS:
    --min-improvement <percent>         Minimum improvement required (default: 10)
    --max-attempts <count>             Maximum optimization attempts (default: 3)
    --consensus                        Enable multi-model consensus
    --models <model1,model2,...>       Comma-separated list of models
    --benchmark-runs <count>           Number of benchmark runs (default: 50)
    --timeout <seconds>                Benchmark timeout (default: 300)
    --verbose                          Enable verbose output
    --help                             Show this help message

EXAMPLES:
    # Optimize a specific function
    $0 optimize-function agents/tools/agent_tools.py::search_knowledge_base

    # Optimize with consensus validation
    $0 optimize-function agents/tools/agent_tools.py::search_knowledge_base --consensus

    # Optimize entire module
    $0 optimize-module agents/adquirencia/ --min-improvement 15

    # Check for regressions
    $0 check-regression

    # Generate optimization report
    $0 generate-report --format markdown

EOF
}

# Parse command line arguments
parse_args() {
    COMMAND=""
    TARGET=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            optimize-function|optimize-module|optimize-commit|analyze-codebase|establish-baseline|check-regression|generate-report)
                COMMAND="$1"
                shift
                if [[ $# -gt 0 && ! "$1" =~ ^-- ]]; then
                    TARGET="$1"
                    shift
                fi
                ;;
            --min-improvement)
                MIN_IMPROVEMENT="$2"
                shift 2
                ;;
            --max-attempts)
                MAX_ATTEMPTS="$2"
                shift 2
                ;;
            --consensus)
                CONSENSUS_REQUIRED=true
                shift
                ;;
            --models)
                MODELS="$2"
                shift 2
                ;;
            --benchmark-runs)
                BENCHMARK_RUNS="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    if [[ -z "$COMMAND" ]]; then
        log_error "No command specified"
        usage
        exit 1
    fi
}

# Validate environment
validate_environment() {
    log_info "Validating environment..."
    
    # Check Python dependencies
    if ! python3 -c "import timeit, cProfile, statistics, yaml, git" 2>/dev/null; then
        log_error "Missing required Python dependencies"
        log_info "Run: pip install -r ${SCRIPT_DIR}/requirements.txt"
        exit 1
    fi
    
    # Check git repository
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_error "Not in a git repository"
        exit 1
    fi
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        log_warning "Uncommitted changes detected"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Create required directories
    mkdir -p "${PROJECT_ROOT}/data/speed_optimization"
    mkdir -p "${PROJECT_ROOT}/logs/speed_optimization"
    
    log_success "Environment validation complete"
}

# Create optimization checkpoint
create_checkpoint() {
    local checkpoint_name="$1"
    local description="$2"
    
    log_info "Creating checkpoint: $checkpoint_name"
    
    # Create checkpoint branch
    git checkout -b "$checkpoint_name" 2>/dev/null || {
        log_error "Failed to create checkpoint branch"
        return 1
    }
    
    # Create checkpoint metadata
    cat > "${PROJECT_ROOT}/data/speed_optimization/${checkpoint_name}.json" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "description": "$description",
    "commit": "$(git rev-parse HEAD)",
    "branch": "$checkpoint_name",
    "target": "$TARGET",
    "config": {
        "min_improvement": $MIN_IMPROVEMENT,
        "max_attempts": $MAX_ATTEMPTS,
        "consensus_required": $CONSENSUS_REQUIRED,
        "models": "$MODELS",
        "benchmark_runs": $BENCHMARK_RUNS
    }
}
EOF
    
    log_success "Checkpoint created: $checkpoint_name"
}

# Run benchmarks
run_benchmarks() {
    local target="$1"
    local output_file="$2"
    
    log_info "Running benchmarks for: $target"
    
    python3 "${SCRIPT_DIR}/benchmarks/benchmark_runner.py" \
        --target "$target" \
        --runs "$BENCHMARK_RUNS" \
        --timeout "$TIMEOUT" \
        --output "$output_file" \
        ${VERBOSE:+--verbose}
}

# Generate optimization using AI models
generate_optimization() {
    local target="$1"
    local attempt="$2"
    local output_file="$3"
    
    log_info "Generating optimization attempt $attempt for: $target"
    
    local consensus_flag=""
    if [[ "$CONSENSUS_REQUIRED" == "true" ]]; then
        consensus_flag="--consensus --models $MODELS"
    fi
    
    python3 "${SCRIPT_DIR}/ai/optimization_generator.py" \
        --target "$target" \
        --attempt "$attempt" \
        --output "$output_file" \
        $consensus_flag \
        ${VERBOSE:+--verbose}
}

# Verify optimization correctness
verify_correctness() {
    local target="$1"
    local optimized_file="$2"
    
    log_info "Verifying correctness for: $target"
    
    python3 "${SCRIPT_DIR}/ai/correctness_verifier.py" \
        --target "$target" \
        --optimized "$optimized_file" \
        ${VERBOSE:+--verbose}
}

# Make optimization decision
make_decision() {
    local benchmark_file="$1"
    local decision_file="$2"
    
    log_info "Making optimization decision..."
    
    python3 "${SCRIPT_DIR}/ai/decision_maker.py" \
        --benchmark-results "$benchmark_file" \
        --min-improvement "$MIN_IMPROVEMENT" \
        --output "$decision_file" \
        ${VERBOSE:+--verbose}
}

# Commit optimization
commit_optimization() {
    local decision_file="$1"
    local target="$2"
    
    log_info "Committing optimization..."
    
    "${SCRIPT_DIR}/git/commit_optimization.sh" \
        --decision "$decision_file" \
        --target "$target" \
        ${VERBOSE:+--verbose}
}

# Revert optimization
revert_optimization() {
    local reason="$1"
    local checkpoint="$2"
    
    log_warning "Reverting optimization: $reason"
    
    "${SCRIPT_DIR}/git/auto_revert.sh" \
        --reason "$reason" \
        --checkpoint "$checkpoint" \
        ${VERBOSE:+--verbose}
}

# Generate optimization report
generate_report() {
    local format="${1:-markdown}"
    
    log_info "Generating optimization report..."
    
    python3 "${SCRIPT_DIR}/reports/performance_reporter.py" \
        --format "$format" \
        --output "${PROJECT_ROOT}/data/speed_optimization/report.${format}" \
        ${VERBOSE:+--verbose}
}

# Main optimization workflow
optimize_target() {
    local target="$1"
    local type="$2"  # function, module, or commit
    
    log_info "Starting optimization workflow for: $target"
    
    # Create checkpoint
    local checkpoint_name="speed-opt-$(date +%s)"
    create_checkpoint "$checkpoint_name" "Optimization attempt for $target"
    
    # Establish baseline
    local baseline_file="${PROJECT_ROOT}/data/speed_optimization/baseline_${checkpoint_name}.json"
    run_benchmarks "$target" "$baseline_file"
    
    # Attempt optimizations
    local success=false
    for attempt in $(seq 1 $MAX_ATTEMPTS); do
        log_info "Optimization attempt $attempt/$MAX_ATTEMPTS"
        
        # Generate optimization
        local opt_file="${PROJECT_ROOT}/data/speed_optimization/optimization_${checkpoint_name}_${attempt}.py"
        if ! generate_optimization "$target" "$attempt" "$opt_file"; then
            log_warning "Failed to generate optimization attempt $attempt"
            continue
        fi
        
        # Verify correctness
        if ! verify_correctness "$target" "$opt_file"; then
            log_warning "Correctness verification failed for attempt $attempt"
            continue
        fi
        
        # Benchmark optimized version
        local bench_file="${PROJECT_ROOT}/data/speed_optimization/benchmark_${checkpoint_name}_${attempt}.json"
        if ! run_benchmarks "$target" "$bench_file"; then
            log_warning "Benchmarking failed for attempt $attempt"
            continue
        fi
        
        # Make decision
        local decision_file="${PROJECT_ROOT}/data/speed_optimization/decision_${checkpoint_name}_${attempt}.json"
        if ! make_decision "$bench_file" "$decision_file"; then
            log_warning "Decision making failed for attempt $attempt"
            continue
        fi
        
        # Check if optimization meets criteria
        if python3 -c "
import json
with open('$decision_file') as f:
    data = json.load(f)
    exit(0 if data.get('approved', False) else 1)
        "; then
            log_success "Optimization approved for attempt $attempt"
            commit_optimization "$decision_file" "$target"
            success=true
            break
        else
            log_warning "Optimization not approved for attempt $attempt"
        fi
    done
    
    # Handle final result
    if [[ "$success" == "true" ]]; then
        log_success "Optimization completed successfully"
        generate_report "markdown"
    else
        log_error "All optimization attempts failed"
        revert_optimization "all_attempts_failed" "$checkpoint_name"
        return 1
    fi
}

# Command implementations
cmd_optimize_function() {
    if [[ -z "$TARGET" ]]; then
        log_error "No function specified"
        usage
        exit 1
    fi
    
    optimize_target "$TARGET" "function"
}

cmd_optimize_module() {
    if [[ -z "$TARGET" ]]; then
        log_error "No module specified"
        usage
        exit 1
    fi
    
    optimize_target "$TARGET" "module"
}

cmd_optimize_commit() {
    if [[ -z "$TARGET" ]]; then
        log_error "No commit specified"
        usage
        exit 1
    fi
    
    optimize_target "$TARGET" "commit"
}

cmd_analyze_codebase() {
    log_info "Analyzing codebase for optimization opportunities..."
    
    python3 "${SCRIPT_DIR}/benchmarks/codebase_analyzer.py" \
        --project-root "$PROJECT_ROOT" \
        --output "${PROJECT_ROOT}/data/speed_optimization/analysis.json" \
        ${VERBOSE:+--verbose}
        
    log_success "Codebase analysis complete"
}

cmd_establish_baseline() {
    log_info "Establishing performance baselines..."
    
    python3 "${SCRIPT_DIR}/benchmarks/baseline_manager.py" \
        --project-root "$PROJECT_ROOT" \
        --output "${PROJECT_ROOT}/data/speed_optimization/baselines.json" \
        ${VERBOSE:+--verbose}
        
    log_success "Baseline establishment complete"
}

cmd_check_regression() {
    log_info "Checking for performance regressions..."
    
    python3 "${SCRIPT_DIR}/benchmarks/regression_checker.py" \
        --project-root "$PROJECT_ROOT" \
        --baselines "${PROJECT_ROOT}/data/speed_optimization/baselines.json" \
        ${VERBOSE:+--verbose}
        
    log_success "Regression check complete"
}

cmd_generate_report() {
    generate_report "markdown"
}

# Main execution
main() {
    parse_args "$@"
    validate_environment
    
    case "$COMMAND" in
        optimize-function)
            cmd_optimize_function
            ;;
        optimize-module)
            cmd_optimize_module
            ;;
        optimize-commit)
            cmd_optimize_commit
            ;;
        analyze-codebase)
            cmd_analyze_codebase
            ;;
        establish-baseline)
            cmd_establish_baseline
            ;;
        check-regression)
            cmd_check_regression
            ;;
        generate-report)
            cmd_generate_report
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            usage
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"