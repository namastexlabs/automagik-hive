# Genie Agents Performance Testing Suite

A comprehensive, unified performance testing system for the Genie Agents multi-agent platform.

## 🚀 Quick Start

```bash
# Quick development testing (recommended)
python run_performance_suite.py quick

# Full comprehensive testing
python run_performance_suite.py full

# Stress testing
python run_performance_suite.py stress --rps 2.0 --duration 60
```

## 📁 File Structure

```
tests/performance/
├── run_performance_suite.py     # 🎯 MAIN ENTRY POINT - Run all tests
├── mock_llm.py                  # 🤖 Mock LLM for fast, cost-free testing
├── metrics_collector.py         # 📊 Comprehensive metrics collection
├── version_comparison.py        # 📈 Version comparison & regression detection
├── test_benchmark.py           # 🧪 Pytest-compatible benchmark tests
├── test_stress.py              # 🔥 Pytest-compatible stress tests
├── data/                       # 📄 Test results and reports
└── README.md                   # 📖 This file
```

## 🎯 Test Modes

### ⚡ Quick Mode (Default)
- **Purpose**: Fast development testing
- **Duration**: 10-30 seconds
- **Tests**: Agent performance + basic concurrency
- **Use Case**: Daily development, CI/CD pipelines

```bash
python run_performance_suite.py quick
```

### 🏃 Full Mode
- **Purpose**: Comprehensive validation
- **Duration**: 2-10 minutes
- **Tests**: All tests (agents, concurrency, stress)
- **Use Case**: Pre-release validation, performance baselines

```bash
python run_performance_suite.py full
```

### 🔥 Stress Mode
- **Purpose**: Load testing and breaking points
- **Duration**: Configurable (30s-5min)
- **Tests**: Sustained load + memory pressure
- **Use Case**: Capacity planning, system limits

```bash
python run_performance_suite.py stress --rps 1.0 --duration 30
```

## 🔧 Configuration Options

### LLM Testing Mode
```bash
# Mock LLM (default) - Fast, free, realistic
python run_performance_suite.py quick --mock

# Real LLM - Production-accurate, API costs apply
python run_performance_suite.py full --real
```

### Stress Test Parameters
```bash
# Custom RPS and duration
python run_performance_suite.py stress --rps 2.0 --duration 60

# Different output directory
python run_performance_suite.py full --output results/
```

### Environment Variables
```bash
# Enable mock LLM by default
export USE_MOCK_LLM=true

# Custom output directory
export PERFORMANCE_OUTPUT_DIR=results/
```

## 📊 Understanding Results

### Performance Grades
- **A**: Excellent (>95% success, <3s response)
- **B**: Good (>90% success, <5s response)
- **C**: Acceptable (>80% success, <10s response)
- **D**: Needs Improvement (below thresholds)

### Key Metrics
- **Agent Response Time**: Average time for agent execution
- **Success Rate**: Percentage of successful requests
- **RPS**: Requests per second (concurrency capability)
- **Memory Usage**: Peak memory consumption
- **CPU Usage**: Peak CPU utilization

### Report Formats
- **JSON**: Machine-readable results (`data/performance_results_*.json`)
- **Markdown**: Human-readable reports (`data/performance_report_*.md`)

## 🧪 Integration with Pytest

Run performance tests as part of your test suite:

```bash
# Run all performance tests
pytest tests/performance/test_benchmark.py
pytest tests/performance/test_stress.py

# Run specific test categories
pytest tests/performance/test_benchmark.py::test_agent_performance
pytest tests/performance/test_stress.py::test_sustained_load
```

## 📈 Version Comparison & Regression Detection

### Create Performance Baselines
```python
from tests.performance.version_comparison import VersionComparisonEngine

engine = VersionComparisonEngine()
baseline = await engine.create_baseline("v1.0", run_full_benchmark=True)
```

### Compare Versions
```python
comparison = engine.compare_versions("v1.0", "v1.1")
print(f"Overall Score: {comparison.overall_score}")
print(f"Recommendation: {comparison.recommendation}")
```

### Regression Detection
- **Automatic**: Compares current version against baseline
- **Threshold**: 5% change considered significant
- **Alerts**: Critical regressions trigger rollback recommendations
- **Trends**: Track performance changes over time

## 📊 Metrics Collection

### Real-time Monitoring
```python
from tests.performance.metrics_collector import metrics_collector

# Start background monitoring
metrics_collector.start_monitoring(interval_seconds=5)

# Record custom metrics
metrics_collector.record_agent_metric(
    agent_id="pagbank-specialist",
    operation="run",
    duration_seconds=2.5,
    success=True
)
```

### Performance Reports
```python
# Agent performance report
report = metrics_collector.get_agent_performance_report(hours=24)

# System health report
health = metrics_collector.get_system_health_report(hours=24)

# Export metrics
filepath = metrics_collector.export_metrics(format="json")
```

## 🤖 Mock LLM Testing

### Benefits
- **Fast**: Tests complete in seconds
- **Cost-Free**: No API charges
- **Consistent**: Repeatable results
- **Realistic**: Simulates actual response patterns

### Configuration
```python
from tests.performance.mock_llm import MockLLMContext, MockLLM

# Use mock LLM in context
with MockLLMContext(enable_mock=True):
    # All LLM calls are mocked
    suite = UnifiedPerformanceSuite(use_mock=True)
    results = await suite.run_quick_test()
```

### Mock Response Patterns
- **Latency**: Simulates realistic API response times
- **Success Rate**: Configurable failure rate (default 2%)
- **Response Size**: Realistic token counts
- **Agent-Specific**: Different patterns per agent type

## 🎯 Best Practices

### Development Workflow
1. **Daily**: Run quick tests during development
2. **CI/CD**: Include quick tests in build pipelines
3. **Pre-Release**: Run full tests before deployment
4. **Monitoring**: Set up continuous performance monitoring

### Performance Optimization
1. **Baseline**: Establish performance baselines
2. **Monitor**: Track key metrics over time
3. **Alert**: Set up alerts for performance degradation
4. **Iterate**: Use results to guide optimization efforts

### Cost Management
- **Default Mock**: Use mock LLM for most testing
- **Selective Real**: Use real LLM for production validation
- **Batch Testing**: Run comprehensive tests less frequently
- **Monitor Usage**: Track API costs and optimize

## 🔧 Troubleshooting

### Common Issues

**Tests Failing**
```bash
# Check dependencies
pip install -r requirements.txt

# Verify agent configuration
python -c "from agents.registry import AgentRegistry; print(AgentRegistry.list_agents())"
```

**Slow Performance**
```bash
# Use mock LLM for faster testing
python run_performance_suite.py quick --mock

# Reduce test scope
python run_performance_suite.py stress --duration 10
```

**Memory Issues**
```bash
# Monitor memory usage
python -c "from tests.performance.metrics_collector import metrics_collector; print(metrics_collector.get_system_health_report())"
```

### Debug Mode
```bash
# Enable verbose output
python run_performance_suite.py full --verbose

# Check system resources
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%, CPU: {psutil.cpu_percent()}%')"
```

## 📞 Support

For issues or questions:
1. Check this README for common solutions
2. Review test logs in `data/` directory
3. Examine metrics in `metrics.db`
4. Contact the development team

## 🎉 Contributing

When adding new performance tests:
1. Add to the unified suite in `run_performance_suite.py`
2. Include both mock and real LLM testing
3. Add comprehensive metrics collection
4. Document new test modes in this README
5. Include pytest-compatible test variants

---

**Generated by Genie Agents Performance Testing Suite**