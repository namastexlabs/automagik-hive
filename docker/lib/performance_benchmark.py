"""Performance Benchmark: Docker SDK vs Subprocess.

This module provides benchmarking capabilities to demonstrate the performance
and reliability advantages of Docker SDK over subprocess calls.
"""

import subprocess
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from docker_sdk_poc import DockerSDKManager


@dataclass
class BenchmarkResult:
    """Single benchmark measurement result."""

    operation: str
    method: str  # 'subprocess' or 'sdk'
    duration: float
    success: bool
    error: str | None = None
    memory_usage: float | None = None


@dataclass
class BenchmarkSuite:
    """Complete benchmark suite results."""

    results: list[BenchmarkResult]
    summary: dict[str, Any]


@contextmanager
def timer():
    """Context manager for timing operations."""
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start


class DockerBenchmark:
    """Docker SDK vs Subprocess performance benchmark."""

    def __init__(self):
        self.sdk_manager = DockerSDKManager()
        self.results: list[BenchmarkResult] = []

    def benchmark_container_listing(
        self, iterations: int = 10
    ) -> list[BenchmarkResult]:
        """Benchmark container listing operations."""
        results = []

        # Subprocess approach
        subprocess_times = []
        for _i in range(iterations):
            with timer() as get_time:
                try:
                    subprocess.run(
                        [
                            "docker",
                            "ps",
                            "-a",
                            "--format",
                            "{{.Names}}\t{{.Status}}\t{{.Image}}",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=True,
                    )
                    success = True
                    error = None
                except subprocess.SubprocessError as e:
                    success = False
                    error = str(e)

                duration = get_time()
                subprocess_times.append(duration)

                results.append(
                    BenchmarkResult(
                        operation="list_containers",
                        method="subprocess",
                        duration=duration,
                        success=success,
                        error=error,
                    )
                )

        # SDK approach
        sdk_times = []
        for _i in range(iterations):
            with timer() as get_time:
                try:
                    self.sdk_manager.list_containers(all=True)
                    success = True
                    error = None
                except Exception as e:
                    success = False
                    error = str(e)

                duration = get_time()
                sdk_times.append(duration)

                results.append(
                    BenchmarkResult(
                        operation="list_containers",
                        method="sdk",
                        duration=duration,
                        success=success,
                        error=error,
                    )
                )

        # Print comparison
        avg_subprocess = sum(subprocess_times) / len(subprocess_times)
        avg_sdk = sum(sdk_times) / len(sdk_times)
        avg_subprocess / avg_sdk if avg_sdk > 0 else 0

        return results

    def benchmark_container_info(
        self, container_name: str = "postgres", iterations: int = 10
    ) -> list[BenchmarkResult]:
        """Benchmark getting container information."""
        results = []

        # Find a container to test with
        try:
            test_containers = self.sdk_manager.list_containers(all=True)
            if not test_containers:
                return results
            test_container = test_containers[0].name
        except Exception:
            return results

        # Subprocess approach
        subprocess_times = []
        for _i in range(iterations):
            with timer() as get_time:
                try:
                    subprocess.run(
                        ["docker", "inspect", test_container],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=True,
                    )
                    success = True
                    error = None
                except subprocess.SubprocessError as e:
                    success = False
                    error = str(e)

                duration = get_time()
                subprocess_times.append(duration)

                results.append(
                    BenchmarkResult(
                        operation="container_info",
                        method="subprocess",
                        duration=duration,
                        success=success,
                        error=error,
                    )
                )

        # SDK approach
        sdk_times = []
        for _i in range(iterations):
            with timer() as get_time:
                try:
                    info = self.sdk_manager.get_container_info(test_container)
                    success = info is not None
                    error = None if success else "Container not found"
                except Exception as e:
                    success = False
                    error = str(e)

                duration = get_time()
                sdk_times.append(duration)

                results.append(
                    BenchmarkResult(
                        operation="container_info",
                        method="sdk",
                        duration=duration,
                        success=success,
                        error=error,
                    )
                )

        # Print comparison
        avg_subprocess = sum(subprocess_times) / len(subprocess_times)
        avg_sdk = sum(sdk_times) / len(sdk_times)
        avg_subprocess / avg_sdk if avg_sdk > 0 else 0

        return results

    def benchmark_log_retrieval(
        self, container_name: str | None = None, iterations: int = 5
    ) -> list[BenchmarkResult]:
        """Benchmark log retrieval operations."""
        results = []

        # Find a container to test with
        try:
            test_containers = self.sdk_manager.list_containers(all=True)
            if not test_containers:
                return results
            test_container = container_name or test_containers[0].name
        except Exception:
            return results

        # Subprocess approach
        subprocess_times = []
        for _i in range(iterations):
            with timer() as get_time:
                try:
                    subprocess.run(
                        ["docker", "logs", "--tail", "50", test_container],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=True,
                    )
                    success = True
                    error = None
                except subprocess.SubprocessError as e:
                    success = False
                    error = str(e)

                duration = get_time()
                subprocess_times.append(duration)

                results.append(
                    BenchmarkResult(
                        operation="get_logs",
                        method="subprocess",
                        duration=duration,
                        success=success,
                        error=error,
                    )
                )

        # SDK approach
        sdk_times = []
        for _i in range(iterations):
            with timer() as get_time:
                try:
                    logs = self.sdk_manager.get_container_logs(test_container, tail=50)
                    success = logs is not None
                    error = None if success else "Could not retrieve logs"
                except Exception as e:
                    success = False
                    error = str(e)

                duration = get_time()
                sdk_times.append(duration)

                results.append(
                    BenchmarkResult(
                        operation="get_logs",
                        method="sdk",
                        duration=duration,
                        success=success,
                        error=error,
                    )
                )

        # Print comparison
        avg_subprocess = sum(subprocess_times) / len(subprocess_times)
        avg_sdk = sum(sdk_times) / len(sdk_times)
        avg_subprocess / avg_sdk if avg_sdk > 0 else 0

        return results

    def run_comprehensive_benchmark(self) -> BenchmarkSuite:
        """Run comprehensive benchmark suite."""
        if not self.sdk_manager.is_available:
            return BenchmarkSuite(results=[], summary={})

        all_results = []

        # Run all benchmark categories
        all_results.extend(self.benchmark_container_listing(iterations=10))
        all_results.extend(self.benchmark_container_info(iterations=10))
        all_results.extend(self.benchmark_log_retrieval(iterations=5))

        # Calculate summary statistics
        subprocess_results = [r for r in all_results if r.method == "subprocess"]
        sdk_results = [r for r in all_results if r.method == "sdk"]

        subprocess_avg = (
            sum(r.duration for r in subprocess_results) / len(subprocess_results)
            if subprocess_results
            else 0
        )
        sdk_avg = (
            sum(r.duration for r in sdk_results) / len(sdk_results)
            if sdk_results
            else 0
        )

        subprocess_success_rate = (
            sum(1 for r in subprocess_results if r.success) / len(subprocess_results)
            if subprocess_results
            else 0
        )
        sdk_success_rate = (
            sum(1 for r in sdk_results if r.success) / len(sdk_results)
            if sdk_results
            else 0
        )

        overall_speedup = subprocess_avg / sdk_avg if sdk_avg > 0 else 0

        summary = {
            "total_operations": len(all_results),
            "subprocess_avg_duration": subprocess_avg,
            "sdk_avg_duration": sdk_avg,
            "overall_speedup": overall_speedup,
            "subprocess_success_rate": subprocess_success_rate,
            "sdk_success_rate": sdk_success_rate,
            "subprocess_error_count": sum(
                1 for r in subprocess_results if not r.success
            ),
            "sdk_error_count": sum(1 for r in sdk_results if not r.success),
        }

        # Print final summary

        return BenchmarkSuite(results=all_results, summary=summary)

    def demonstrate_error_handling(self):
        """Demonstrate superior error handling with Docker SDK."""
        # Test 1: Non-existent container

        # Subprocess approach
        try:
            subprocess.run(
                ["docker", "inspect", "non-existent-container-12345"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
        except subprocess.CalledProcessError:
            pass
        except subprocess.TimeoutExpired:
            pass

        # SDK approach
        try:
            info = self.sdk_manager.get_container_info("non-existent-container-12345")
            if info is None:
                pass
            else:
                pass
        except Exception:
            pass

        # Test 2: Invalid operation

        # Subprocess approach
        try:
            subprocess.run(
                ["docker", "invalid-command", "test"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
        except subprocess.CalledProcessError:
            pass
        except subprocess.TimeoutExpired:
            pass

        # SDK approach has built-in method validation


def run_benchmark():
    """Run the complete benchmark suite."""
    benchmark = DockerBenchmark()

    # Run performance benchmarks
    suite = benchmark.run_comprehensive_benchmark()

    # Demonstrate error handling advantages
    benchmark.demonstrate_error_handling()

    return suite


if __name__ == "__main__":
    run_benchmark()
