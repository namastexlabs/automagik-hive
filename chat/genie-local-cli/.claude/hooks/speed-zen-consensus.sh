#!/bin/bash

# Speed Optimization Zen Consensus Hook
# Enhances zen consensus calls with optimization-specific context

set -euo pipefail

# Configuration
WORKSPACE="${WORKSPACE:-$(pwd)}"
CLAUDE_DIR="${WORKSPACE}/.claude"
LOGS_DIR="${CLAUDE_DIR}/logs"

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"

# Logging functions
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" >> "$LOGS_DIR/speed-zen-consensus.log"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$LOGS_DIR/speed-zen-consensus.log"
}

log_debug() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] DEBUG: $1" >> "$LOGS_DIR/speed-zen-consensus.log"
}

# Read the input JSON
INPUT=$(cat)

# Extract the step content from the input
STEP=$(echo "$INPUT" | jq -r '.step // empty')

# Check if this is a speed optimization related consensus
if [[ ! "$STEP" =~ (optimization|performance|speed|benchmark|runtime) ]]; then
    echo "$INPUT"
    exit 0
fi

log_info "Processing speed optimization zen consensus"

# Detect optimization context
detect_optimization_context() {
    local step="$1"
    local context=""
    
    if [[ "$step" =~ (function.*optimization|optimize.*function) ]]; then
        context="FUNCTION_OPTIMIZATION"
    elif [[ "$step" =~ (algorithm.*optimization|optimize.*algorithm) ]]; then
        context="ALGORITHM_OPTIMIZATION"
    elif [[ "$step" =~ (performance.*improvement|improve.*performance) ]]; then
        context="PERFORMANCE_IMPROVEMENT"
    elif [[ "$step" =~ (benchmark|benchmarking|runtime|measurement) ]]; then
        context="BENCHMARKING"
    elif [[ "$step" =~ (speed.*framework|framework.*speed) ]]; then
        context="FRAMEWORK_DESIGN"
    elif [[ "$step" =~ (consensus.*optimization|optimization.*consensus) ]]; then
        context="CONSENSUS_OPTIMIZATION"
    else
        context="GENERAL_OPTIMIZATION"
    fi
    
    echo "$context"
}

# Generate optimization-specific guidance
generate_optimization_guidance() {
    local context="$1"
    local guidance=""
    
    case "$context" in
        "FUNCTION_OPTIMIZATION")
            guidance="FUNCTION OPTIMIZATION CONSENSUS GUIDANCE:

Key Evaluation Criteria:
1. **Performance Impact**: Measure actual runtime improvement using minimum-of-N methodology
2. **Correctness Preservation**: Ensure behavioral equivalence through comprehensive testing
3. **Code Quality**: Maintain readability, maintainability, and Python best practices
4. **Safety**: Validate that optimization doesn't introduce subtle bugs or edge cases

Technical Considerations:
- Algorithm complexity improvements (O(n²) → O(n log n))
- Data structure optimization (lists → sets for lookups)
- Built-in function utilization (map, filter, itertools)
- Memory allocation reduction
- Cache-friendly access patterns

Consensus Questions:
- Does the optimization provide measurable performance improvement (≥10%)?
- Are all function behaviors preserved across different input types?
- Is the optimized code maintainable and follows project standards?
- Are there any edge cases or error conditions that could be affected?

Risk Assessment:
- High Impact, Low Risk: Algorithm improvements with preserved behavior
- Medium Impact, Medium Risk: Data structure changes requiring validation
- Low Impact, High Risk: Micro-optimizations that reduce readability"
            ;;
        "ALGORITHM_OPTIMIZATION")
            guidance="ALGORITHM OPTIMIZATION CONSENSUS GUIDANCE:

Key Evaluation Criteria:
1. **Complexity Analysis**: Validate time and space complexity improvements
2. **Correctness Proof**: Ensure algorithm correctness through mathematical reasoning
3. **Input Robustness**: Test with various input sizes and edge cases
4. **Implementation Quality**: Assess code clarity and maintainability

Technical Considerations:
- Time complexity reduction (quadratic to linear, exponential to polynomial)
- Space complexity optimization (in-place operations, memory reuse)
- Divide-and-conquer strategies (sorting, searching, dynamic programming)
- Caching and memoization opportunities
- Parallel processing potential

Consensus Questions:
- Is the algorithmic approach mathematically sound and provably correct?
- Does the complexity analysis support the claimed performance improvements?
- Are all algorithmic invariants preserved throughout the optimization?
- Is the implementation robust against edge cases and unusual inputs?

Risk Assessment:
- High Impact, Low Risk: Well-established algorithms with proven complexity
- Medium Impact, Medium Risk: Custom algorithms requiring validation
- Low Impact, High Risk: Premature optimization without clear benefits"
            ;;
        "PERFORMANCE_IMPROVEMENT")
            guidance="PERFORMANCE IMPROVEMENT CONSENSUS GUIDANCE:

Key Evaluation Criteria:
1. **Measurement Accuracy**: Validate benchmarking methodology and statistical significance
2. **Realistic Workloads**: Ensure improvements apply to actual usage patterns
3. **Resource Utilization**: Consider CPU, memory, and I/O impact
4. **Scalability**: Assess performance across different input sizes

Technical Considerations:
- Profiling-guided optimization (hotspot identification)
- I/O optimization (batching, caching, async operations)
- Memory management (allocation patterns, garbage collection)
- CPU optimization (vectorization, branch prediction)
- Network optimization (connection pooling, compression)

Consensus Questions:
- Are the performance improvements statistically significant and reproducible?
- Do the improvements apply to realistic usage patterns and workloads?
- Are there any performance regressions in other areas of the system?
- Is the optimization sustainable across different deployment environments?

Risk Assessment:
- High Impact, Low Risk: Profiling-guided optimizations with clear bottlenecks
- Medium Impact, Medium Risk: Architectural changes requiring system-wide validation
- Low Impact, High Risk: Speculative optimizations without clear measurement"
            ;;
        "BENCHMARKING")
            guidance="BENCHMARKING CONSENSUS GUIDANCE:

Key Evaluation Criteria:
1. **Measurement Methodology**: Validate minimum runtime approach and statistical rigor
2. **Noise Reduction**: Ensure measurements are stable and repeatable
3. **Test Coverage**: Verify comprehensive input scenarios and edge cases
4. **Environment Consistency**: Control for system variability and external factors

Technical Considerations:
- Minimum runtime methodology (best-of-N runs)
- Statistical significance testing
- Warm-up runs for JIT compilation
- System noise control (CPU frequency, background processes)
- Input scenario diversity (small, large, edge cases)

Consensus Questions:
- Is the benchmarking methodology scientifically sound and reproducible?
- Are the measurements stable across different system conditions?
- Do the test inputs represent realistic usage patterns?
- Are statistical methods appropriate for the measurement data?

Risk Assessment:
- High Impact, Low Risk: Comprehensive benchmarking with statistical validation
- Medium Impact, Medium Risk: Limited benchmarking requiring expansion
- Low Impact, High Risk: Flaky measurements leading to incorrect conclusions"
            ;;
        "FRAMEWORK_DESIGN")
            guidance="FRAMEWORK DESIGN CONSENSUS GUIDANCE:

Key Evaluation Criteria:
1. **Architecture Soundness**: Evaluate framework design principles and patterns
2. **Extensibility**: Assess ability to handle diverse optimization scenarios
3. **Usability**: Consider developer experience and adoption barriers
4. **Safety**: Validate error handling and rollback mechanisms

Technical Considerations:
- Modular design with clear separation of concerns
- Plugin architecture for different optimization strategies
- Configuration management and customization options
- Integration with existing development workflows
- Error handling and recovery mechanisms

Consensus Questions:
- Does the framework architecture support the intended use cases effectively?
- Is the framework extensible for future optimization strategies?
- Are the interfaces intuitive and well-documented for users?
- Are safety mechanisms adequate for production use?

Risk Assessment:
- High Impact, Low Risk: Well-designed framework with proven patterns
- Medium Impact, Medium Risk: Novel approaches requiring validation
- Low Impact, High Risk: Over-engineered solutions with unclear benefits"
            ;;
        "CONSENSUS_OPTIMIZATION")
            guidance="CONSENSUS OPTIMIZATION CONSENSUS GUIDANCE:

Key Evaluation Criteria:
1. **Model Diversity**: Ensure complementary perspectives from different AI models
2. **Voting Strategy**: Validate consensus mechanisms and conflict resolution
3. **Quality Metrics**: Assess optimization quality scoring and ranking
4. **Convergence**: Evaluate consensus reliability and stability

Technical Considerations:
- Multi-model optimization generation
- Weighted voting based on model strengths
- Conflict resolution strategies
- Quality scoring algorithms
- Consensus threshold determination

Consensus Questions:
- Do the models provide sufficiently diverse and complementary perspectives?
- Is the voting strategy fair and resistant to bias?
- Are the quality metrics meaningful and predictive of success?
- Does the consensus mechanism produce stable and reliable results?

Risk Assessment:
- High Impact, Low Risk: Diverse models with proven consensus mechanisms
- Medium Impact, Medium Risk: Limited model diversity requiring expansion
- Low Impact, High Risk: Biased consensus leading to poor optimization choices"
            ;;
        *)
            guidance="GENERAL OPTIMIZATION CONSENSUS GUIDANCE:

Key Evaluation Criteria:
1. **Cost-Benefit Analysis**: Weigh optimization benefits against implementation costs
2. **Technical Soundness**: Validate technical approach and implementation quality
3. **Risk Assessment**: Identify potential issues and mitigation strategies
4. **Strategic Alignment**: Ensure optimization aligns with project goals

Technical Considerations:
- Performance measurement and validation
- Code quality and maintainability
- Testing and verification strategies
- Deployment and rollback procedures
- Long-term maintenance implications

Consensus Questions:
- Is the optimization approach technically sound and well-reasoned?
- Are the expected benefits realistic and measurable?
- Are the risks acceptable and properly mitigated?
- Does the optimization align with broader project objectives?

Risk Assessment:
- High Impact, Low Risk: Well-validated optimizations with clear benefits
- Medium Impact, Medium Risk: Moderate changes requiring careful validation
- Low Impact, High Risk: Speculative optimizations without clear justification"
            ;;
    esac
    
    echo "$guidance"
}

# Detect optimization context
CONTEXT=$(detect_optimization_context "$STEP")
log_debug "Detected optimization context: $CONTEXT"

# Generate optimization guidance
GUIDANCE=$(generate_optimization_guidance "$CONTEXT")
log_debug "Generated optimization guidance for $CONTEXT"

# Enhance the step with optimization-specific guidance
ENHANCED_STEP="$STEP

# Speed Optimization Framework Consensus Context

$GUIDANCE

## Framework Integration

When evaluating this optimization proposal, consider the Genie Speed Optimization Framework principles:

1. **Generate and Verify**: All optimizations must be generated algorithmically and verified empirically
2. **Minimum Runtime Principle**: Performance measured using best-of-N runs to minimize noise
3. **Correctness First**: No optimization is valid without behavioral equivalence guarantee
4. **One Commit Per Optimization**: Each optimization attempt gets its own commit for traceability
5. **Automatic Revert**: Failed optimizations are automatically reverted to prevent regressions
6. **Consensus Validation**: Complex optimizations require multi-model agreement

## Consensus Evaluation Framework

For this optimization proposal, please evaluate:

**Technical Merit (40%)**:
- Algorithm correctness and complexity analysis
- Implementation quality and maintainability
- Performance measurement methodology
- Edge case handling and robustness

**Performance Impact (30%)**:
- Measurable performance improvement (≥10% threshold)
- Statistical significance of benchmarking results
- Scalability across different input sizes
- Resource utilization efficiency

**Safety and Correctness (20%)**:
- Behavioral equivalence preservation
- Test coverage and verification
- Error handling and edge cases
- Rollback safety and recovery

**Strategic Value (10%)**:
- Alignment with project performance goals
- Long-term maintainability implications
- Development workflow integration
- Knowledge transfer and documentation

## Decision Criteria

**APPROVE** if:
- Technical approach is sound and well-reasoned
- Performance improvements are measurable and significant
- Correctness is verified through comprehensive testing
- Risk assessment shows acceptable safety margins

**REJECT** if:
- Technical approach is flawed or unproven
- Performance improvements are marginal or unverified
- Correctness cannot be guaranteed
- Risk assessment shows unacceptable safety concerns

**REQUEST CLARIFICATION** if:
- Technical details are insufficient for evaluation
- Performance measurement methodology needs validation
- Testing strategy requires enhancement
- Risk mitigation strategies need development

Remember: The goal is sustainable performance improvement through rigorous engineering practices."

# Create the enhanced input JSON
ENHANCED_INPUT=$(echo "$INPUT" | jq --arg step "$ENHANCED_STEP" '.step = $step')

log_info "Enhanced zen consensus with speed optimization context"

# Output the enhanced input
echo "$ENHANCED_INPUT"