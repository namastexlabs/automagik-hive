#!/bin/bash

# Speed Optimization Framework Hook
# Enhances /speed command usage with intelligent optimization context

set -euo pipefail

# Configuration
WORKSPACE="${WORKSPACE:-$(pwd)}"
CLAUDE_DIR="${WORKSPACE}/.claude"
LOGS_DIR="${CLAUDE_DIR}/logs"
SPEED_DIR="${WORKSPACE}/scripts/speed"

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"

# Logging functions
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" >> "$LOGS_DIR/speed-optimization.log"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$LOGS_DIR/speed-optimization.log"
}

log_debug() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] DEBUG: $1" >> "$LOGS_DIR/speed-optimization.log"
}

# Read the input JSON
INPUT=$(cat)

# Extract the user message from the input
MESSAGE=$(echo "$INPUT" | jq -r '.message // empty')

# Check if this is a /speed command
if [[ ! "$MESSAGE" =~ ^/speed ]]; then
    echo "$INPUT"
    exit 0
fi

log_info "Processing /speed command: $MESSAGE"

# Parse the speed command
SPEED_COMMAND=$(echo "$MESSAGE" | sed 's/^\/speed\s*//')

# Analyze the command for optimization opportunities
analyze_speed_command() {
    local command="$1"
    local analysis=""
    
    # Function optimization
    if [[ "$command" =~ optimize-function ]]; then
        analysis="FUNCTION_OPTIMIZATION"
    # Module optimization
    elif [[ "$command" =~ optimize-module ]]; then
        analysis="MODULE_OPTIMIZATION"
    # Commit optimization
    elif [[ "$command" =~ optimize-commit ]]; then
        analysis="COMMIT_OPTIMIZATION"
    # Codebase analysis
    elif [[ "$command" =~ analyze-codebase ]]; then
        analysis="CODEBASE_ANALYSIS"
    # Baseline establishment
    elif [[ "$command" =~ establish-baseline ]]; then
        analysis="BASELINE_ESTABLISHMENT"
    # Regression checking
    elif [[ "$command" =~ check-regression ]]; then
        analysis="REGRESSION_CHECK"
    # Report generation
    elif [[ "$command" =~ generate-report ]]; then
        analysis="REPORT_GENERATION"
    else
        analysis="GENERAL_OPTIMIZATION"
    fi
    
    echo "$analysis"
}

# Generate optimization context based on analysis
generate_optimization_context() {
    local analysis="$1"
    local context=""
    
    case "$analysis" in
        "FUNCTION_OPTIMIZATION")
            context="FUNCTION OPTIMIZATION CONTEXT:
- Focus on specific function performance improvements
- Use minimum runtime benchmarking methodology
- Ensure correctness through comprehensive testing
- Consider algorithm complexity, data structures, and implementation patterns
- Apply zen consensus for complex optimizations
- One commit per optimization with automatic revert on failure

OPTIMIZATION STRATEGY:
1. Analyze function complexity and bottlenecks
2. Generate optimization candidates using AI models
3. Benchmark using minimum runtime approach (best of N runs)
4. Verify correctness through test execution
5. Apply consensus validation for complex changes
6. Commit successful optimizations with performance metadata

MEMORY SEARCH PATTERNS:
- Previous function optimizations: 'function optimization +performance'
- Algorithm improvements: 'algorithm optimization +complexity'
- Performance patterns: 'performance improvement +runtime'
- Zen consensus usage: 'zen consensus +optimization'"
            ;;
        "MODULE_OPTIMIZATION")
            context="MODULE OPTIMIZATION CONTEXT:
- Optimize entire modules for comprehensive performance gains
- Identify optimization candidates across multiple functions
- Coordinate multi-function optimization workflows
- Track cumulative performance improvements
- Apply systematic optimization methodology

OPTIMIZATION STRATEGY:
1. Scan module for optimization candidates
2. Prioritize functions by impact and complexity
3. Apply sequential optimization with checkpointing
4. Track cumulative performance improvements
5. Generate module-level optimization report
6. Coordinate with CI/CD for automated optimization

MEMORY SEARCH PATTERNS:
- Module optimization patterns: 'module optimization +performance'
- Multi-function coordination: 'multi-function optimization'
- Performance tracking: 'performance tracking +cumulative'
- Automated optimization: 'automated optimization +CI/CD'"
            ;;
        "COMMIT_OPTIMIZATION")
            context="COMMIT OPTIMIZATION CONTEXT:
- Optimize changes within specific git commits
- Focus on recent modifications and their performance impact
- Apply git-based optimization workflow
- Track optimization history and impact
- Coordinate with version control for rollback safety

OPTIMIZATION STRATEGY:
1. Identify changed functions in target commit
2. Apply optimization to modified code
3. Benchmark changes against baseline
4. Use git checkpointing for safe rollback
5. Track optimization impact across commits
6. Generate commit-based optimization reports

MEMORY SEARCH PATTERNS:
- Commit optimization patterns: 'commit optimization +git'
- Git workflow integration: 'git workflow +optimization'
- Version control safety: 'git checkpoint +rollback'
- Change tracking: 'change tracking +performance'"
            ;;
        "CODEBASE_ANALYSIS")
            context="CODEBASE ANALYSIS CONTEXT:
- Comprehensive analysis of entire codebase for optimization opportunities
- Identify performance bottlenecks and optimization candidates
- Generate prioritized optimization roadmap
- Establish performance baselines across the system
- Create optimization strategy based on impact analysis

ANALYSIS STRATEGY:
1. Scan codebase for optimization candidates
2. Analyze function complexity and performance characteristics
3. Identify high-impact optimization opportunities
4. Generate prioritized optimization roadmap
5. Establish system-wide performance baselines
6. Create comprehensive analysis report

MEMORY SEARCH PATTERNS:
- Codebase analysis patterns: 'codebase analysis +performance'
- Performance profiling: 'performance profiling +bottlenecks'
- Optimization prioritization: 'optimization prioritization +impact'
- System analysis: 'system analysis +performance'"
            ;;
        "BASELINE_ESTABLISHMENT")
            context="BASELINE ESTABLISHMENT CONTEXT:
- Create performance baselines for systematic optimization
- Establish measurement methodology and benchmarking standards
- Set up performance monitoring and regression detection
- Configure optimization thresholds and success criteria
- Enable continuous performance tracking

BASELINE STRATEGY:
1. Identify critical functions and performance metrics
2. Establish baseline measurements using minimum runtime methodology
3. Configure performance monitoring and alerting
4. Set optimization thresholds and success criteria
5. Enable automated regression detection
6. Create baseline documentation and maintenance procedures

MEMORY SEARCH PATTERNS:
- Baseline establishment: 'baseline establishment +performance'
- Performance monitoring: 'performance monitoring +continuous'
- Regression detection: 'regression detection +automated'
- Measurement methodology: 'measurement methodology +benchmarking'"
            ;;
        "REGRESSION_CHECK")
            context="REGRESSION CHECK CONTEXT:
- Detect performance regressions across the codebase
- Compare current performance against established baselines
- Identify functions with degraded performance
- Generate regression reports with impact analysis
- Coordinate with CI/CD for automated regression detection

REGRESSION STRATEGY:
1. Compare current performance against baselines
2. Identify functions with significant performance degradation
3. Analyze regression causes and impact
4. Generate detailed regression reports
5. Coordinate with development workflow for fixes
6. Update baselines after regression resolution

MEMORY SEARCH PATTERNS:
- Regression detection patterns: 'regression detection +performance'
- Performance degradation: 'performance degradation +analysis'
- Baseline comparison: 'baseline comparison +regression'
- Automated monitoring: 'automated monitoring +CI/CD'"
            ;;
        "REPORT_GENERATION")
            context="REPORT GENERATION CONTEXT:
- Generate comprehensive optimization reports
- Track optimization history and cumulative impact
- Create performance visualization and trends
- Document optimization methodology and results
- Provide actionable recommendations for future optimizations

REPORT STRATEGY:
1. Aggregate optimization data and metrics
2. Generate performance trends and visualizations
3. Calculate cumulative optimization impact
4. Document optimization methodology and best practices
5. Provide actionable recommendations
6. Create shareable optimization reports

MEMORY SEARCH PATTERNS:
- Report generation patterns: 'report generation +optimization'
- Performance visualization: 'performance visualization +trends'
- Optimization tracking: 'optimization tracking +history'
- Documentation patterns: 'documentation +performance'"
            ;;
        *)
            context="GENERAL OPTIMIZATION CONTEXT:
- Apply systematic performance optimization methodology
- Use AI-assisted optimization with multi-model consensus
- Implement minimum runtime benchmarking approach
- Ensure correctness through comprehensive testing
- Track optimization impact and generate reports

OPTIMIZATION STRATEGY:
1. Analyze code for optimization opportunities
2. Generate optimization candidates using AI models
3. Apply rigorous benchmarking and correctness verification
4. Use git checkpointing for safe optimization workflow
5. Track optimization impact and generate reports
6. Coordinate with development workflow for integration

MEMORY SEARCH PATTERNS:
- Optimization methodology: 'optimization methodology +systematic'
- AI-assisted optimization: 'AI optimization +consensus'
- Performance improvement: 'performance improvement +benchmarking'
- Optimization workflow: 'optimization workflow +git'"
            ;;
    esac
    
    echo "$context"
}

# Analyze the speed command
ANALYSIS=$(analyze_speed_command "$SPEED_COMMAND")
log_debug "Speed command analysis: $ANALYSIS"

# Generate optimization context
OPTIMIZATION_CONTEXT=$(generate_optimization_context "$ANALYSIS")
log_debug "Generated optimization context for $ANALYSIS"

# Create enhanced message with optimization context
ENHANCED_MESSAGE="$MESSAGE

# Speed Optimization Framework Context

$OPTIMIZATION_CONTEXT

## Framework Integration

The Genie Speed Optimization Framework follows a \"generate and verify\" approach inspired by Codeflash:

1. **AI-Assisted Optimization**: Multiple AI models generate optimization candidates
2. **Minimum Runtime Benchmarking**: Best-of-N measurement approach reduces noise
3. **Correctness Verification**: Comprehensive testing ensures behavioral equivalence
4. **Git Checkpointing**: Safe optimization workflow with automatic rollback
5. **Zen Consensus**: Multi-model validation for complex optimizations
6. **Performance Tracking**: Continuous monitoring and regression detection

## Available Tools

- **Main CLI**: \`./scripts/speed/speedopt.sh\`
- **Benchmarking**: \`scripts/speed/benchmarks/benchmark_runner.py\`
- **AI Generation**: \`scripts/speed/ai/optimization_generator.py\`
- **Git Integration**: \`scripts/speed/git/commit_optimization.sh\`
- **Reporting**: \`scripts/speed/reports/performance_reporter.py\`

## Configuration

- **Main Config**: \`config/speed_config.yaml\`
- **Consensus Config**: \`config/consensus_config.yaml\`
- **Performance Data**: \`data/speed_optimization/\`

## Memory Integration

Use \`mcp__genie_memory__search_memory\` to find relevant optimization patterns and previous solutions that can inform your approach.

## Best Practices

1. **Start with Analysis**: Always analyze before optimizing
2. **Establish Baselines**: Create performance baselines for comparison
3. **Use Consensus**: Apply multi-model consensus for complex optimizations
4. **Track Impact**: Monitor optimization impact and maintain history
5. **Safe Workflow**: Use git checkpointing for rollback safety
6. **Continuous Integration**: Integrate with CI/CD for automated optimization

Remember: The goal is measurable performance improvement while maintaining code correctness and quality."

# Create the enhanced input JSON
ENHANCED_INPUT=$(echo "$INPUT" | jq --arg msg "$ENHANCED_MESSAGE" '.message = $msg')

log_info "Enhanced /speed command with optimization context"

# Output the enhanced input
echo "$ENHANCED_INPUT"