# /speed

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Glob(*), Grep(*), Bash(*), LS(*), TodoWrite(*), WebSearch(*), mcp__zen__*, mcp__search-repo-docs__*, mcp__ask-repo-agent__*, mcp__genie_memory__*, mcp__send_whatsapp_message__*, mcp__wait__*
description: Genie Speed Optimization Framework - AI-assisted performance optimization with generate-and-verify approach
---

# Genie Speed Optimization Framework

## Overview

The Genie Speed Optimization Framework is an AI-assisted performance optimization system inspired by Codeflash that follows a "generate and verify" approach. It uses multi-model consensus to generate optimizations, rigorously verifies performance improvements, and maintains code correctness through complete testing.

## Core Philosophy

- **Generate and Verify**: AI models propose optimizations, empirical benchmarking validates improvements
- **One Commit Per Optimization**: Each optimization attempt gets its own commit for traceability
- **Automatic Revert**: Failed optimizations are automatically reverted to prevent regressions
- **Multi-Model Consensus**: Complex optimizations require agreement from multiple AI models
- **Minimum Runtime Principle**: Performance measured using best-of-N runs to minimize noise

## Framework Components

### 1. Benchmarking Infrastructure (`scripts/speed/`)
- **benchmark_runner.py**: Core benchmarking engine with minimum runtime measurement
- **performance_profiler.py**: Code profiling and bottleneck identification
- **noise_reduction.py**: Statistical techniques for stable performance measurement
- **baseline_manager.py**: Manages performance baselines and regression detection

### 2. Git Automation (`scripts/speed/git/`)
- **checkpoint_manager.sh**: Creates optimization checkpoints and manages branches
- **auto_revert.sh**: Automatically reverts failed optimizations
- **commit_automation.py**: Handles structured commits with performance metadata
- **conflict_resolver.py**: Manages git conflicts during optimization workflows

### 3. AI Optimization Engine (`scripts/speed/ai/`)
- **optimization_generator.py**: Multi-model optimization proposal system
- **consensus_validator.py**: Zen consensus integration for complex optimizations
- **correctness_verifier.py**: Validates optimization correctness through testing
- **candidate_ranker.py**: Ranks optimization candidates by impact and safety

### 4. Reporting System (`scripts/speed/reports/`)
- **performance_reporter.py**: Generates complete optimization reports
- **visualization_engine.py**: Creates performance charts and trends
- **summary_generator.py**: Produces optimization summaries and recommendations
- **history_tracker.py**: Maintains optimization history and metrics

## Quick Start Guide

### Prerequisites
```bash
# Install dependencies
pip install -r scripts/speed/requirements.txt

# Verify test suite coverage
python scripts/speed/verify_test_coverage.py

# Setup benchmarking environment
python scripts/speed/setup_environment.py
```

### Basic Usage

#### 1. Single Function Optimization
```bash
# Optimize a specific function
./scripts/speed/speedopt.sh optimize-function agents/tools/agent_tools.py::search_knowledge_base

# With custom thresholds
./scripts/speed/speedopt.sh optimize-function agents/tools/agent_tools.py::search_knowledge_base --min-improvement 15 --max-attempts 3
```

#### 2. Module-Wide Optimization
```bash
# Optimize entire module
./scripts/speed/speedopt.sh optimize-module agents/adquirencia/

# With consensus validation
./scripts/speed/speedopt.sh optimize-module agents/adquirencia/ --consensus --models "grok-4-0709,gemini-2.5-pro,o3"
```

#### 3. Commit-Level Optimization
```bash
# Optimize changes since last commit
./scripts/speed/speedopt.sh optimize-commit HEAD~1

# Optimize specific commit
./scripts/speed/speedopt.sh optimize-commit a1b2c3d4
```

## Detailed Workflow

### Phase 1: Analysis and Candidate Identification

1. **Codebase Analysis**
   ```bash
   python scripts/speed/analyze_codebase.py --target agents/ --output analysis.json
   ```
   - Identifies optimization candidates using static analysis
   - Maps function call graphs and dependencies
   - Estimates optimization impact potential

2. **Baseline Establishment**
   ```bash
   python scripts/speed/establish_baseline.py --config baseline_config.yaml
   ```
   - Creates performance baselines for all identified functions
   - Establishes noise thresholds for benchmarking
   - Validates test coverage requirements

### Phase 2: Optimization Generation

1. **AI Model Preparation**
   ```bash
   python scripts/speed/prepare_models.py --consensus-config consensus.yaml
   ```
   - Configures multi-model consensus system
   - Sets up model-specific optimization prompts
   - Validates API keys and rate limits

2. **Optimization Generation**
   ```bash
   python scripts/speed/generate_optimizations.py --target function_name --attempts 5
   ```
   - Generates multiple optimization candidates
   - Applies code context and project patterns
   - Ranks candidates by estimated impact

### Phase 3: Verification and Benchmarking

1. **Correctness Verification**
   ```bash
   python scripts/speed/verify_correctness.py --candidate optimization_candidate.py
   ```
   - Runs complete test suite
   - Validates behavioral equivalence
   - Checks edge case handling

2. **Performance Benchmarking**
   ```bash
   python scripts/speed/run_benchmarks.py --original original.py --powered powered.py
   ```
   - Applies minimum runtime measurement
   - Handles multiple input scenarios
   - Generates statistical confidence intervals

### Phase 4: Decision and Commit

1. **Optimization Decision**
   ```bash
   python scripts/speed/make_decision.py --benchmark-results results.json --threshold 10
   ```
   - Evaluates performance improvement significance
   - Applies consensus validation for complex changes
   - Generates decision rationale

2. **Commit or Revert**
   ```bash
   # Automatic commit if optimization succeeds
   ./scripts/speed/commit_optimization.sh --results results.json

   # Automatic revert if optimization fails
   ./scripts/speed/revert_optimization.sh --reason "insufficient_improvement"
   ```

## Configuration Files

### `config/speed_config.yaml`
```yaml
# Performance thresholds
thresholds:
  minimum_improvement: 10  # Minimum % improvement required
  noise_floor: 5          # Measurement noise tolerance
  timeout_seconds: 300    # Maximum benchmark runtime

# Benchmarking settings
benchmarking:
  warmup_runs: 3
  measurement_runs: 50
  statistical_method: "minimum"  # minimum, median, mean
  confidence_level: 0.95

# AI model configuration
models:
  consensus_required: true
  models:
    - name: "grok-4-0709"
      provider: "xai"
      weight: 1.0
    - name: "gemini-2.5-pro"
      provider: "google"
      weight: 1.0
    - name: "o3"
      provider: "openai"
      weight: 1.0

# Git automation
git:
  auto_commit: true
  auto_revert: true
  branch_prefix: "speed-opt"
  commit_message_template: "Speed optimization: {function_name} (+{improvement}%)"
```

### `config/consensus_config.yaml`
```yaml
# Zen consensus integration
consensus:
  required_for:
    - complex_functions: true     # Functions > 50 LOC
    - critical_paths: true       # Functions in performance-critical modules
    - external_apis: true        # Functions with external dependencies
    - async_functions: false     # Currently not supported

  voting_weights:
    correctness: 0.4
    performance: 0.3
    maintainability: 0.2
    security: 0.1

  minimum_agreement: 0.7         # 70% consensus required
  tie_breaking: "conservative"   # conservative, aggressive, manual
```

## Advanced Features

### Custom Optimization Strategies

1. **Algorithm Optimization**
   ```bash
   python scripts/speed/optimize_algorithms.py --strategy "complexity_reduction"
   ```
   - Identifies O(n²) → O(n log n) opportunities
   - Suggests better data structures
   - Optimizes loop structures

2. **Memory Optimization**
   ```bash
   python scripts/speed/optimize_memory.py --strategy "allocation_reduction"
   ```
   - Reduces memory allocations
   - Optimizes data structure usage
   - Identifies memory leaks

3. **I/O Optimization**
   ```bash
   python scripts/speed/optimize_io.py --strategy "batch_operations"
   ```
   - Batches database operations
   - Optimizes file I/O patterns
   - Reduces network calls

### Continuous Optimization

1. **CI/CD Integration**
   ```yaml
   # .github/workflows/speed_optimization.yml
   name: Speed Optimization
   on:
     pull_request:
       branches: [main, master]
   
   jobs:
     speed_check:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Run Speed Analysis
           run: |
             python scripts/speed/ci_analysis.py --pr-number ${{ github.event.number }}
             python scripts/speed/suggest_optimizations.py --output suggestions.md
   ```

2. **Scheduled Optimization**
   ```bash
   # Daily optimization cron job
   0 2 * * * cd /path/to/genie-agents && ./scripts/speed/daily_optimization.sh
   ```

### Performance Monitoring

1. **Real-time Metrics**
   ```bash
   python scripts/speed/monitor_performance.py --dashboard --port 8080
   ```
   - Live performance dashboard
   - Regression detection alerts
   - Optimization opportunity notifications

2. **Historical Analysis**
   ```bash
   python scripts/speed/analyze_history.py --since "2024-01-01" --format html
   ```
   - Performance trend analysis
   - Optimization effectiveness reports
   - Regression root cause analysis

## Troubleshooting

### Common Issues

1. **Flaky Benchmarks**
   ```bash
   # Increase measurement runs
   python scripts/speed/diagnose_noise.py --function target_function
   
   # Use containerized benchmarking
   docker run --rm -v $(pwd):/code genie-speed-bench python scripts/speed/run_benchmarks.py
   ```

2. **Git Conflicts**
   ```bash
   # Manual conflict resolution
   python scripts/speed/resolve_conflicts.py --branch speed-opt-branch
   
   # Reset optimization state
   ./scripts/speed/reset_optimization.sh --preserve-baseline
   ```

3. **Test Failures**
   ```bash
   # Detailed test analysis
   python scripts/speed/analyze_test_failures.py --optimization-candidate candidate.py
   
   # Generate additional test cases
   python scripts/speed/generate_tests.py --function target_function --coverage 95
   ```

### Performance Debugging

1. **Profiling Analysis**
   ```bash
   python scripts/speed/profile_function.py --function target_function --detailed
   ```

2. **Bottleneck Identification**
   ```bash
   python scripts/speed/identify_bottlenecks.py --module target_module --threshold 1.0
   ```

## Best Practices

### 1. Optimization Targets
- **High-Impact Functions**: Focus on functions called frequently or in critical paths
- **Self-Contained Logic**: Prioritize functions with minimal external dependencies
- **Well-Tested Code**: Ensure complete test coverage before optimization
- **Stable Interfaces**: Avoid optimizing frequently changing APIs

### 2. Benchmarking Guidelines
- **Warm-up Runs**: Always include warm-up runs before measurement
- **Multiple Inputs**: Test with various input sizes and patterns
- **Statistical Validation**: Use proper statistical methods for result validation
- **Environment Consistency**: Maintain consistent benchmarking environment

### 3. Safety Measures
- **Incremental Changes**: Make small, focused optimizations
- **Rollback Readiness**: Always have a clear rollback plan
- **Monitoring**: Monitor performance after optimization deployment
- **Documentation**: Document optimization rationale and impact

## Integration with Genie Agents

### Agent-Specific Optimizations

1. **Agent Response Time**
   ```bash
   ./scripts/speed/optimize_agent_response.sh --agent adquirencia --target-latency 500ms
   ```

2. **Memory Usage**
   ```bash
   ./scripts/speed/optimize_agent_memory.sh --agent pagbank --max-memory 512MB
   ```

3. **Throughput Optimization**
   ```bash
   ./scripts/speed/optimize_throughput.sh --team ana --target-rps 100
   ```

### Monitoring Integration

1. **Grafana Dashboard**
   - Performance metrics visualization
   - Optimization impact tracking
   - Regression detection alerts

2. **Prometheus Metrics**
   - Function execution time histograms
   - Memory usage metrics
   - Optimization success rates

## Reporting and Analytics

### Optimization Reports

Each optimization generates a complete report:

```markdown
# Optimization Report: search_knowledge_base()

## Summary
- **Function**: `agents/tools/agent_tools.py::search_knowledge_base`
- **Optimization Type**: Algorithm improvement
- **Performance Gain**: +23.5%
- **Memory Impact**: -15% allocation
- **Status**: ✅ Committed

## Benchmarking Results
- **Original Runtime**: 45.2ms (best of 50 runs)
- **Optimized Runtime**: 34.6ms (best of 50 runs)
- **Improvement**: 23.5% faster
- **Statistical Confidence**: 99.5%

## Changes Made
- Replaced linear search with binary search for sorted knowledge base
- Implemented result caching for repeated queries
- Optimized string comparison operations

## Verification
- ✅ All 47 existing tests pass
- ✅ 15 new edge case tests generated and pass
- ✅ Memory leak detection: No issues found
- ✅ Type safety: All type hints valid

## AI Model Consensus
- **Grok-4-0709**: ✅ Approved (confidence: 0.92)
- **Gemini-2.5-Pro**: ✅ Approved (confidence: 0.88)
- **O3**: ✅ Approved (confidence: 0.85)
- **Overall Consensus**: 0.88 (above 0.7 threshold)

## Impact Analysis
- **Affected Functions**: 12 callers analyzed
- **System Impact**: Improved overall agent response time by 3.2%
- **Resource Savings**: $15/month in compute costs
```

### Historical Analysis

```bash
# Generate monthly optimization report
python scripts/speed/generate_monthly_report.py --month 2024-01

# Analyze optimization trends
python scripts/speed/analyze_trends.py --since "2024-01-01" --format pdf
```

## Future Enhancements

### Planned Features

1. **Machine Learning Integration**
   - Predictive optimization candidate identification
   - Automated parameter tuning
   - Performance regression prediction

2. **Multi-Language Support**
   - TypeScript optimization for chat CLI
   - Shell script optimization
   - YAML configuration optimization

3. **Advanced Analytics**
   - A/B testing for optimizations
   - Performance correlation analysis
   - Resource usage optimization

### Research Areas

1. **Semantic Optimization**
   - Code meaning preservation during optimization
   - Intent-aware refactoring
   - Domain-specific optimization patterns

2. **Distributed Optimization**
   - Multi-service optimization coordination
   - Cross-service performance impact analysis
   - Distributed system bottleneck identification

---

## Quick Reference

### Common Commands
```bash
# Quick function optimization
./scripts/speed/quick_optimize.sh function_name

# Bulk module optimization
./scripts/speed/bulk_optimize.sh module_path/

# Performance regression check
./scripts/speed/check_regression.sh

# Generate optimization report
./scripts/speed/generate_report.sh --format markdown
```

### Key Configuration Files
- `config/speed_config.yaml` - Main configuration
- `config/consensus_config.yaml` - AI model consensus settings
- `config/benchmarking_config.yaml` - Benchmarking parameters
- `.github/workflows/speed_optimization.yml` - CI/CD integration

### Support and Documentation
- **Issues**: Report bugs and feature requests in GitHub Issues
- **Documentation**: Full documentation in `docs/speed-framework/`
- **Examples**: Real-world examples in `examples/speed-optimizations/`
- **Community**: Join discussions in the #speed-optimization channel

For detailed implementation guides, see the `docs/speed-framework/` directory.