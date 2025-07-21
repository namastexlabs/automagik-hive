#!/usr/bin/env python3
"""
Performance Benchmark for YAML Templating System

Tests template rendering performance against direct agent instantiation
to ensure templating overhead stays within acceptable limits.
"""

import json
import statistics
import time
from typing import Any

try:
    from lib.logging import logger
except ImportError:
    try:
        from agno.utils.log import logger
    except ImportError:
        from lib.logging import logger

from .context import ContextProvider
from .processor import TemplateProcessorFactory


class TemplatingBenchmark:
    """
    Performance benchmark suite for template processing.
    
    Measures template rendering performance across different scenarios
    and compares against baseline direct instantiation performance.
    """

    def __init__(self):
        self.logger = logger
        self.results: dict[str, Any] = {}

    def run_full_benchmark(self) -> dict[str, Any]:
        """Run complete benchmark suite."""
        self.logger.info("🏁 Starting template processing benchmark")

        # Test scenarios
        scenarios = [
            ("simple_template", self._benchmark_simple_template),
            ("complex_template", self._benchmark_complex_template),
            ("context_building", self._benchmark_context_building),
            ("security_validation", self._benchmark_security_validation)
        ]

        results = {}

        for scenario_name, benchmark_func in scenarios:
            self.logger.info(f"🧪 Running benchmark: {scenario_name}")
            try:
                scenario_results = benchmark_func()
                results[scenario_name] = scenario_results
                self.logger.info(f"✅ {scenario_name}: {scenario_results['avg_time_ms']:.2f}ms avg")
            except Exception as e:
                self.logger.error(f"❌ {scenario_name} failed: {e!s}")
                results[scenario_name] = {"error": str(e)}

        # Calculate summary statistics
        results["summary"] = self._calculate_summary(results)

        self.logger.info("🏁 Benchmark completed")
        return results

    def _benchmark_simple_template(self) -> dict[str, Any]:
        """Benchmark simple template rendering."""
        processor = TemplateProcessorFactory.create_development()

        simple_config = {
            "agent": {
                "name": "Hello {{ user_context.user_name }}!",
                "version": "{{ system_context.environment }}"
            },
            "model": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }

        context = {
            "user_context": {"user_name": "João"},
            "system_context": {"environment": "production"}
        }

        return self._time_operations(
            lambda: processor.render_config(simple_config, context),
            iterations=1000,
            name="simple_template"
        )

    def _benchmark_complex_template(self) -> dict[str, Any]:
        """Benchmark complex template with conditionals and loops."""
        processor = TemplateProcessorFactory.create_development()

        complex_config = {
            "agent": {
                "name": "{% if user_context.is_vip %}VIP {% endif %}{{ user_context.user_name }}",
                "max_tokens": "{% if user_context.is_vip %}4000{% else %}2000{% endif %}"
            },
            "instructions": """
            Hello {{ user_context.user_name }}!
            
            {% if user_context.permissions %}
            Your permissions:
            {% for permission in user_context.permissions %}
            - {{ permission }}
            {% endfor %}
            {% endif %}
            
            Environment: {{ system_context.environment | upper }}
            """,
            "features": "{{ tenant_context.enabled_features | length }} features enabled"
        }

        context = {
            "user_context": {
                "user_name": "Maria",
                "is_vip": True,
                "permissions": ["read", "write", "admin", "delete"]
            },
            "system_context": {"environment": "production"},
            "tenant_context": {
                "enabled_features": ["chat", "classification", "analytics", "reporting"]
            }
        }

        return self._time_operations(
            lambda: processor.render_config(complex_config, context),
            iterations=500,
            name="complex_template"
        )

    def _benchmark_context_building(self) -> dict[str, Any]:
        """Benchmark context building performance."""
        provider = ContextProvider()

        context_kwargs = {
            "user_id": "user_123",
            "user_name": "João Silva",
            "email": "joao@example.com",
            "phone_number": "5511999887766",
            "permissions": ["read", "write"],
            "subscription_type": "enterprise",
            "session_id": "sess_456",
            "channel": "whatsapp",
            "debug_mode": True,
            "tenant_id": "company_xyz"
        }

        return self._time_operations(
            lambda: provider.build_context(**context_kwargs),
            iterations=2000,
            name="context_building"
        )


    def _benchmark_security_validation(self) -> dict[str, Any]:
        """Benchmark security validation performance."""
        processor = TemplateProcessorFactory.create_development()

        safe_config = {
            "agent": {"name": "Safe {{ user_context.user_name }}"},
            "instructions": "You are {{ user_context.user_name }}'s assistant."
        }

        context = {"user_context": {"user_name": "Security Test"}}

        return self._time_operations(
            lambda: processor.render_config(safe_config, context),
            iterations=500,
            name="security_validation"
        )

    def _time_operations(self, operation, iterations: int, name: str) -> dict[str, Any]:
        """Time multiple operations and return statistics."""
        times = []
        errors = 0

        for _ in range(iterations):
            start_time = time.perf_counter()
            try:
                result = operation()
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)  # Convert to ms
            except Exception as e:
                errors += 1
                self.logger.warning(f"⚠️ Operation failed in {name}: {e!s}")

        if not times:
            return {"error": "All operations failed"}

        return {
            "name": name,
            "iterations": len(times),
            "errors": errors,
            "avg_time_ms": statistics.mean(times),
            "median_time_ms": statistics.median(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0,
            "p95_time_ms": sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max(times),
            "p99_time_ms": sorted(times)[int(len(times) * 0.99)] if len(times) > 100 else max(times)
        }

    def _calculate_summary(self, results: dict[str, Any]) -> dict[str, Any]:
        """Calculate summary statistics across all benchmarks."""
        valid_results = [r for r in results.values() if isinstance(r, dict) and "avg_time_ms" in r]

        if not valid_results:
            return {"error": "No valid benchmark results"}

        flat_results = valid_results

        avg_times = [r["avg_time_ms"] for r in flat_results if "avg_time_ms" in r]

        return {
            "total_benchmarks": len(valid_results),
            "overall_avg_ms": statistics.mean(avg_times) if avg_times else 0,
            "overall_median_ms": statistics.median(avg_times) if avg_times else 0,
            "fastest_benchmark": min(flat_results, key=lambda x: x.get("avg_time_ms", float("inf"))),
            "slowest_benchmark": max(flat_results, key=lambda x: x.get("avg_time_ms", 0)),
            "performance_grade": self._calculate_grade(avg_times)
        }

    def _calculate_grade(self, avg_times: list[float]) -> str:
        """Calculate performance grade based on average times."""
        if not avg_times:
            return "N/A"

        overall_avg = statistics.mean(avg_times)

        if overall_avg < 5:
            return "A+ (Excellent)"
        if overall_avg < 10:
            return "A (Very Good)"
        if overall_avg < 20:
            return "B (Good)"
        if overall_avg < 50:
            return "C (Acceptable)"
        return "D (Needs Improvement)"


def run_benchmark() -> dict[str, Any]:
    """Run complete templating benchmark suite."""
    benchmark = TemplatingBenchmark()
    return benchmark.run_full_benchmark()


def print_benchmark_results(results: dict[str, Any]):
    """Print formatted benchmark results to console and log structured data."""
    # Console output for human readability
    logger.info("⚡ YAML TEMPLATING PERFORMANCE BENCHMARK RESULTS")

    summary = results.get("summary", {})
    if "error" in summary:
        logger.error(f"⚡ Benchmark failed: {summary['error']}")
        return

    # Log structured summary first
    logger.info("⚡ Overall Performance Results",
               grade=summary.get("performance_grade", "N/A"),
               avg_time_ms=summary.get("overall_avg_ms", 0),
               median_time_ms=summary.get("overall_median_ms", 0))

    # Individual benchmark results
    for name, result in results.items():
        if name == "summary":
            continue

        if isinstance(result, dict) and "error" in result:
            logger.error(f"⚡ {name} benchmark failed", error=result["error"])
            continue

        if "avg_time_ms" in result:
            logger.info(f"⚡ {name} benchmark results",
                       avg_time_ms=result["avg_time_ms"],
                       median_time_ms=result["median_time_ms"],
                       p95_time_ms=result["p95_time_ms"],
                       errors=result.get("errors", 0),
                       iterations=result.get("iterations", 0))

    # Performance recommendations
    fastest = summary.get("fastest_benchmark", {})
    slowest = summary.get("slowest_benchmark", {})

    if fastest and slowest:
        ratio = slowest.get("avg_time_ms", 0) / fastest.get("avg_time_ms", 1)
        logger.info("⚡ Performance insights",
                   fastest_name=fastest.get("name", "Unknown"),
                   fastest_time_ms=fastest.get("avg_time_ms", 0),
                   slowest_name=slowest.get("name", "Unknown"),
                   slowest_time_ms=slowest.get("avg_time_ms", 0),
                   performance_ratio=ratio)

        if ratio > 5:
            logger.warning("⚡ Performance optimization recommended",
                         slow_operation=slowest.get("name", "slower operations"),
                         ratio=ratio)


if __name__ == "__main__":
    results = run_benchmark()
    print_benchmark_results(results)

    # Save results to file
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
