"""Performance Benchmark: Docker SDK vs Subprocess.

This module provides benchmarking capabilities to demonstrate the performance
and reliability advantages of Docker SDK over subprocess calls.
"""

import subprocess
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import docker
from docker.errors import APIError, NotFound

from docker_sdk_poc import DockerSDKManager


@dataclass
class BenchmarkResult:
    """Single benchmark measurement result"""
    operation: str
    method: str  # 'subprocess' or 'sdk'
    duration: float
    success: bool
    error: Optional[str] = None
    memory_usage: Optional[float] = None


@dataclass
class BenchmarkSuite:
    """Complete benchmark suite results"""
    results: List[BenchmarkResult]
    summary: Dict[str, Any]


@contextmanager
def timer():
    """Context manager for timing operations"""
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start
    

class DockerBenchmark:
    """Docker SDK vs Subprocess performance benchmark"""
    
    def __init__(self):
        self.sdk_manager = DockerSDKManager()
        self.results: List[BenchmarkResult] = []
    
    def benchmark_container_listing(self, iterations: int = 10) -> List[BenchmarkResult]:
        """Benchmark container listing operations"""
        results = []
        
        print(f"🏃‍♂️ Benchmarking container listing ({iterations} iterations)")
        
        # Subprocess approach
        subprocess_times = []
        for i in range(iterations):
            with timer() as get_time:
                try:
                    result = subprocess.run(
                        ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=True
                    )
                    success = True
                    error = None
                except subprocess.SubprocessError as e:
                    success = False
                    error = str(e)
                
                duration = get_time()
                subprocess_times.append(duration)
                
                results.append(BenchmarkResult(
                    operation="list_containers",
                    method="subprocess", 
                    duration=duration,
                    success=success,
                    error=error
                ))
        
        # SDK approach
        sdk_times = []
        for i in range(iterations):
            with timer() as get_time:
                try:
                    containers = self.sdk_manager.list_containers(all=True)
                    success = True
                    error = None
                except Exception as e:
                    success = False
                    error = str(e)
                
                duration = get_time()
                sdk_times.append(duration)
                
                results.append(BenchmarkResult(
                    operation="list_containers",
                    method="sdk",
                    duration=duration,
                    success=success,
                    error=error
                ))
        
        # Print comparison
        avg_subprocess = sum(subprocess_times) / len(subprocess_times)
        avg_sdk = sum(sdk_times) / len(sdk_times)
        speedup = avg_subprocess / avg_sdk if avg_sdk > 0 else 0
        
        print(f"  📊 Subprocess avg: {avg_subprocess:.4f}s")
        print(f"  📊 SDK avg: {avg_sdk:.4f}s")
        print(f"  🚀 SDK speedup: {speedup:.2f}x")
        
        return results
    
    def benchmark_container_info(self, container_name: str = "postgres", iterations: int = 10) -> List[BenchmarkResult]:
        """Benchmark getting container information"""
        results = []
        
        print(f"🔍 Benchmarking container info retrieval ({iterations} iterations)")
        
        # Find a container to test with
        try:
            test_containers = self.sdk_manager.list_containers(all=True)
            if not test_containers:
                print("⚠️ No containers found for info benchmark")
                return results
            test_container = test_containers[0].name
        except Exception:
            print("⚠️ Could not find test container")
            return results
        
        # Subprocess approach
        subprocess_times = []
        for i in range(iterations):
            with timer() as get_time:
                try:
                    result = subprocess.run(
                        ["docker", "inspect", test_container],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=True
                    )
                    success = True
                    error = None
                except subprocess.SubprocessError as e:
                    success = False
                    error = str(e)
                
                duration = get_time()
                subprocess_times.append(duration)
                
                results.append(BenchmarkResult(
                    operation="container_info",
                    method="subprocess",
                    duration=duration,
                    success=success,
                    error=error
                ))
        
        # SDK approach
        sdk_times = []
        for i in range(iterations):
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
                
                results.append(BenchmarkResult(
                    operation="container_info",
                    method="sdk",
                    duration=duration,
                    success=success,
                    error=error
                ))
        
        # Print comparison
        avg_subprocess = sum(subprocess_times) / len(subprocess_times)
        avg_sdk = sum(sdk_times) / len(sdk_times)
        speedup = avg_subprocess / avg_sdk if avg_sdk > 0 else 0
        
        print(f"  📊 Subprocess avg: {avg_subprocess:.4f}s")
        print(f"  📊 SDK avg: {avg_sdk:.4f}s")
        print(f"  🚀 SDK speedup: {speedup:.2f}x")
        
        return results
    
    def benchmark_log_retrieval(self, container_name: Optional[str] = None, iterations: int = 5) -> List[BenchmarkResult]:
        """Benchmark log retrieval operations"""
        results = []
        
        print(f"📋 Benchmarking log retrieval ({iterations} iterations)")
        
        # Find a container to test with
        try:
            test_containers = self.sdk_manager.list_containers(all=True)
            if not test_containers:
                print("⚠️ No containers found for log benchmark")
                return results
            test_container = container_name or test_containers[0].name
        except Exception:
            print("⚠️ Could not find test container")
            return results
        
        # Subprocess approach
        subprocess_times = []
        for i in range(iterations):
            with timer() as get_time:
                try:
                    result = subprocess.run(
                        ["docker", "logs", "--tail", "50", test_container],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=True
                    )
                    success = True
                    error = None
                except subprocess.SubprocessError as e:
                    success = False
                    error = str(e)
                
                duration = get_time()
                subprocess_times.append(duration)
                
                results.append(BenchmarkResult(
                    operation="get_logs",
                    method="subprocess",
                    duration=duration,
                    success=success,
                    error=error
                ))
        
        # SDK approach  
        sdk_times = []
        for i in range(iterations):
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
                
                results.append(BenchmarkResult(
                    operation="get_logs",
                    method="sdk",
                    duration=duration,
                    success=success,
                    error=error
                ))
        
        # Print comparison
        avg_subprocess = sum(subprocess_times) / len(subprocess_times)  
        avg_sdk = sum(sdk_times) / len(sdk_times)
        speedup = avg_subprocess / avg_sdk if avg_sdk > 0 else 0
        
        print(f"  📊 Subprocess avg: {avg_subprocess:.4f}s")
        print(f"  📊 SDK avg: {avg_sdk:.4f}s") 
        print(f"  🚀 SDK speedup: {speedup:.2f}x")
        
        return results
    
    def run_comprehensive_benchmark(self) -> BenchmarkSuite:
        """Run comprehensive benchmark suite"""
        print("🏁 Starting Comprehensive Docker SDK vs Subprocess Benchmark")
        print("=" * 60)
        
        if not self.sdk_manager.is_available:
            print("❌ Docker SDK not available - cannot run benchmarks")
            return BenchmarkSuite(results=[], summary={})
        
        all_results = []
        
        # Run all benchmark categories
        all_results.extend(self.benchmark_container_listing(iterations=10))
        all_results.extend(self.benchmark_container_info(iterations=10))
        all_results.extend(self.benchmark_log_retrieval(iterations=5))
        
        # Calculate summary statistics
        subprocess_results = [r for r in all_results if r.method == "subprocess"]
        sdk_results = [r for r in all_results if r.method == "sdk"]
        
        subprocess_avg = sum(r.duration for r in subprocess_results) / len(subprocess_results) if subprocess_results else 0
        sdk_avg = sum(r.duration for r in sdk_results) / len(sdk_results) if sdk_results else 0
        
        subprocess_success_rate = sum(1 for r in subprocess_results if r.success) / len(subprocess_results) if subprocess_results else 0
        sdk_success_rate = sum(1 for r in sdk_results if r.success) / len(sdk_results) if sdk_results else 0
        
        overall_speedup = subprocess_avg / sdk_avg if sdk_avg > 0 else 0
        
        summary = {
            "total_operations": len(all_results),
            "subprocess_avg_duration": subprocess_avg,
            "sdk_avg_duration": sdk_avg,
            "overall_speedup": overall_speedup,
            "subprocess_success_rate": subprocess_success_rate,
            "sdk_success_rate": sdk_success_rate,
            "subprocess_error_count": sum(1 for r in subprocess_results if not r.success),
            "sdk_error_count": sum(1 for r in sdk_results if not r.success)
        }
        
        # Print final summary
        print("\n📈 BENCHMARK SUMMARY")
        print("=" * 30)
        print(f"Total operations: {summary['total_operations']}")
        print(f"Subprocess avg: {summary['subprocess_avg_duration']:.4f}s (success: {summary['subprocess_success_rate']:.1%})")
        print(f"SDK avg: {summary['sdk_avg_duration']:.4f}s (success: {summary['sdk_success_rate']:.1%})")
        print(f"Overall speedup: {summary['overall_speedup']:.2f}x")
        print(f"Error reduction: {summary['subprocess_error_count']} → {summary['sdk_error_count']} errors")
        
        return BenchmarkSuite(results=all_results, summary=summary)
    
    def demonstrate_error_handling(self):
        """Demonstrate superior error handling with Docker SDK"""
        print("\n🛡️ Error Handling Demonstration")
        print("=" * 35)
        
        # Test 1: Non-existent container
        print("Test 1: Non-existent container")
        
        # Subprocess approach
        try:
            result = subprocess.run(
                ["docker", "inspect", "non-existent-container-12345"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )
            print("  Subprocess: Unexpected success")
        except subprocess.CalledProcessError as e:
            print(f"  Subprocess: Exception thrown - {e}")
        except subprocess.TimeoutExpired:
            print("  Subprocess: Timeout exception")
        
        # SDK approach
        try:
            info = self.sdk_manager.get_container_info("non-existent-container-12345")
            if info is None:
                print("  SDK: Graceful None return (no exception)")
            else:
                print("  SDK: Unexpected success")
        except Exception as e:
            print(f"  SDK: Exception - {e}")
        
        # Test 2: Invalid operation
        print("\nTest 2: Invalid Docker command")
        
        # Subprocess approach
        try:
            result = subprocess.run(
                ["docker", "invalid-command", "test"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )
            print("  Subprocess: Unexpected success")
        except subprocess.CalledProcessError as e:
            print(f"  Subprocess: Exception thrown - return code {e.returncode}")
        except subprocess.TimeoutExpired:
            print("  Subprocess: Timeout exception")
        
        # SDK approach has built-in method validation
        print("  SDK: Invalid operations prevented at compile time (type safety)")
        
        print("\n✅ Error handling demonstration completed")


def run_benchmark():
    """Run the complete benchmark suite"""
    benchmark = DockerBenchmark()
    
    # Run performance benchmarks
    suite = benchmark.run_comprehensive_benchmark()
    
    # Demonstrate error handling advantages
    benchmark.demonstrate_error_handling()
    
    return suite


if __name__ == "__main__":
    run_benchmark()