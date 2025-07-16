"""
Performance benchmarking and testing suite for Genie Agents.

This package provides comprehensive performance testing capabilities including:
- Agent execution timing benchmarks
- Concurrency and stress testing
- System resource monitoring
- Version comparison and regression detection
- Automated reporting and alerting
"""

from .test_benchmark import PerformanceBenchmark, BenchmarkResult
from .test_stress import StressTestSuite, StressTestResult
from .metrics_collector import MetricsCollector, TimedOperation, metrics_collector
from .version_comparison import VersionComparisonEngine, VersionBaseline, VersionComparison

__all__ = [
    'PerformanceBenchmark',
    'BenchmarkResult', 
    'StressTestSuite',
    'StressTestResult',
    'MetricsCollector',
    'TimedOperation',
    'metrics_collector',
    'VersionComparisonEngine',
    'VersionBaseline',
    'VersionComparison'
]

__version__ = '1.0.0'