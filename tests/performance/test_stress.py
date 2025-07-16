"""
Stress testing suite for Genie Agents multi-agent system.

This module provides comprehensive stress testing for:
- High concurrency scenarios
- Load testing under sustained traffic
- Memory pressure testing
- Resource exhaustion scenarios
- System stability under extreme conditions
"""

import asyncio
import time
import threading
import psutil
import json
import uuid
import gc
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest
import aiohttp
from agno.agent import Agent
from agno.team import Team

from ai.agents.registry import AgentRegistry
from ai.teams.ana.team import get_ana_team
from config.settings import settings
from utils.log import logger


@dataclass
class StressTestResult:
    """Stress test result data structure."""
    test_name: str
    timestamp: datetime
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    average_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    memory_peak_mb: float
    memory_average_mb: float
    cpu_peak_percent: float
    cpu_average_percent: float
    error_rate: float
    throughput_degradation: float
    system_stability_score: float
    metadata: Dict[str, Any] = None


@dataclass
class ResourceUsage:
    """System resource usage tracking."""
    timestamp: datetime
    memory_mb: float
    cpu_percent: float
    open_files: int
    network_connections: int
    thread_count: int


class StressTestSuite:
    """Comprehensive stress testing suite for multi-agent system."""
    
    def __init__(self, results_dir: str = "tests/performance/stress_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[StressTestResult] = []
        self.resource_usage: List[ResourceUsage] = []
        self.monitoring_active = False
        self.monitoring_thread = None
        
    def start_resource_monitoring(self):
        """Start background resource monitoring."""
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_resources)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
    def stop_resource_monitoring(self):
        """Stop background resource monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
            
    def _monitor_resources(self):
        """Background resource monitoring loop."""
        process = psutil.Process()
        
        while self.monitoring_active:
            try:
                self.resource_usage.append(ResourceUsage(
                    timestamp=datetime.now(timezone.utc),
                    memory_mb=process.memory_info().rss / 1024 / 1024,
                    cpu_percent=process.cpu_percent(),
                    open_files=process.num_fds() if hasattr(process, 'num_fds') else 0,
                    network_connections=len(process.connections()),
                    thread_count=process.num_threads()
                ))
                time.sleep(1)  # Monitor every second
            except psutil.NoSuchProcess:
                break
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                
    def _calculate_percentiles(self, values: List[float]) -> Dict[str, float]:
        """Calculate response time percentiles."""
        if not values:
            return {"p50": 0, "p95": 0, "p99": 0}
            
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        return {
            "p50": sorted_values[int(n * 0.5)],
            "p95": sorted_values[int(n * 0.95)],
            "p99": sorted_values[int(n * 0.99)]
        }
        
    def _calculate_system_stability_score(self, 
                                        success_rate: float, 
                                        response_time_variance: float,
                                        memory_stability: float) -> float:
        """
        Calculate system stability score (0-100).
        
        Args:
            success_rate: Percentage of successful requests
            response_time_variance: Variance in response times
            memory_stability: Memory usage stability
            
        Returns:
            Stability score between 0 and 100
        """
        # Normalize factors
        success_factor = success_rate / 100.0
        response_factor = max(0, 1 - (response_time_variance / 10.0))  # Assume 10s variance is bad
        memory_factor = max(0, 1 - (memory_stability / 1000.0))  # Assume 1GB variance is bad
        
        # Weighted average
        stability_score = (success_factor * 0.5 + response_factor * 0.3 + memory_factor * 0.2) * 100
        return min(100, max(0, stability_score))
    
    async def sustained_load_test(self,
                                agent_id: str,
                                requests_per_second: float,
                                duration_seconds: int,
                                test_message: str = "Sustained load test message") -> StressTestResult:
        """
        Run sustained load test with constant RPS.
        
        Args:
            agent_id: Agent to test
            requests_per_second: Target requests per second
            duration_seconds: Test duration in seconds
            test_message: Message to send
            
        Returns:
            StressTestResult with performance metrics
        """
        self.start_resource_monitoring()
        
        start_time = time.time()
        request_times = []
        successful_requests = 0
        failed_requests = 0
        
        async def send_request():
            """Send single request and track timing."""
            req_start = time.time()
            try:
                agent = AgentRegistry.get_agent(agent_id)
                await agent.run(test_message)
                req_end = time.time()
                return True, req_end - req_start
            except Exception as e:
                req_end = time.time()
                logger.error(f"Request failed: {e}")
                return False, req_end - req_start
        
        # Calculate request interval
        interval = 1.0 / requests_per_second
        
        # Run sustained load
        total_requests = 0
        while time.time() - start_time < duration_seconds:
            request_start = time.time()
            
            # Send request
            success, duration = await send_request()
            request_times.append(duration)
            total_requests += 1
            
            if success:
                successful_requests += 1
            else:
                failed_requests += 1
            
            # Wait for next interval
            elapsed = time.time() - request_start
            if elapsed < interval:
                await asyncio.sleep(interval - elapsed)
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        self.stop_resource_monitoring()
        
        # Calculate metrics
        percentiles = self._calculate_percentiles(request_times)
        avg_response_time = sum(request_times) / len(request_times) if request_times else 0
        
        # Resource usage metrics
        memory_values = [r.memory_mb for r in self.resource_usage]
        cpu_values = [r.cpu_percent for r in self.resource_usage]
        
        memory_peak = max(memory_values) if memory_values else 0
        memory_avg = sum(memory_values) / len(memory_values) if memory_values else 0
        cpu_peak = max(cpu_values) if cpu_values else 0
        cpu_avg = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        
        # Calculate stability metrics
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        response_time_variance = max(request_times) - min(request_times) if request_times else 0
        memory_stability = max(memory_values) - min(memory_values) if memory_values else 0
        
        stability_score = self._calculate_system_stability_score(
            success_rate, response_time_variance, memory_stability
        )
        
        result = StressTestResult(
            test_name=f"sustained_load_{agent_id}_{requests_per_second}rps",
            timestamp=datetime.now(timezone.utc),
            duration_seconds=test_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=total_requests / test_duration,
            average_response_time=avg_response_time,
            median_response_time=percentiles["p50"],
            p95_response_time=percentiles["p95"],
            p99_response_time=percentiles["p99"],
            min_response_time=min(request_times) if request_times else 0,
            max_response_time=max(request_times) if request_times else 0,
            memory_peak_mb=memory_peak,
            memory_average_mb=memory_avg,
            cpu_peak_percent=cpu_peak,
            cpu_average_percent=cpu_avg,
            error_rate=failed_requests / total_requests * 100 if total_requests > 0 else 0,
            throughput_degradation=max(0, (requests_per_second - (total_requests / test_duration)) / requests_per_second * 100),
            system_stability_score=stability_score,
            metadata={
                "target_rps": requests_per_second,
                "actual_rps": total_requests / test_duration,
                "resource_samples": len(self.resource_usage)
            }
        )
        
        self.results.append(result)
        return result
    
    async def spike_load_test(self,
                            agent_id: str,
                            base_rps: float,
                            spike_rps: float,
                            spike_duration: int,
                            total_duration: int,
                            test_message: str = "Spike load test message") -> StressTestResult:
        """
        Run spike load test with traffic spikes.
        
        Args:
            agent_id: Agent to test
            base_rps: Base requests per second
            spike_rps: Spike requests per second
            spike_duration: Duration of spike in seconds
            total_duration: Total test duration in seconds
            test_message: Message to send
            
        Returns:
            StressTestResult with performance metrics
        """
        self.start_resource_monitoring()
        
        start_time = time.time()
        request_times = []
        successful_requests = 0
        failed_requests = 0
        total_requests = 0
        
        async def send_request():
            """Send single request and track timing."""
            req_start = time.time()
            try:
                agent = AgentRegistry.get_agent(agent_id)
                await agent.run(test_message)
                req_end = time.time()
                return True, req_end - req_start
            except Exception as e:
                req_end = time.time()
                logger.error(f"Request failed: {e}")
                return False, req_end - req_start
        
        # Run spike test
        current_time = 0
        while current_time < total_duration:
            # Determine current RPS based on spike pattern
            if current_time % (spike_duration * 2) < spike_duration:
                current_rps = spike_rps
            else:
                current_rps = base_rps
            
            interval = 1.0 / current_rps
            request_start = time.time()
            
            # Send request
            success, duration = await send_request()
            request_times.append(duration)
            total_requests += 1
            
            if success:
                successful_requests += 1
            else:
                failed_requests += 1
            
            # Wait for next interval
            elapsed = time.time() - request_start
            if elapsed < interval:
                await asyncio.sleep(interval - elapsed)
            
            current_time = time.time() - start_time
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        self.stop_resource_monitoring()
        
        # Calculate metrics (similar to sustained load test)
        percentiles = self._calculate_percentiles(request_times)
        avg_response_time = sum(request_times) / len(request_times) if request_times else 0
        
        # Resource usage metrics
        memory_values = [r.memory_mb for r in self.resource_usage]
        cpu_values = [r.cpu_percent for r in self.resource_usage]
        
        memory_peak = max(memory_values) if memory_values else 0
        memory_avg = sum(memory_values) / len(memory_values) if memory_values else 0
        cpu_peak = max(cpu_values) if cpu_values else 0
        cpu_avg = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        
        # Calculate stability metrics
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        response_time_variance = max(request_times) - min(request_times) if request_times else 0
        memory_stability = max(memory_values) - min(memory_values) if memory_values else 0
        
        stability_score = self._calculate_system_stability_score(
            success_rate, response_time_variance, memory_stability
        )
        
        result = StressTestResult(
            test_name=f"spike_load_{agent_id}_{base_rps}to{spike_rps}rps",
            timestamp=datetime.now(timezone.utc),
            duration_seconds=test_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=total_requests / test_duration,
            average_response_time=avg_response_time,
            median_response_time=percentiles["p50"],
            p95_response_time=percentiles["p95"],
            p99_response_time=percentiles["p99"],
            min_response_time=min(request_times) if request_times else 0,
            max_response_time=max(request_times) if request_times else 0,
            memory_peak_mb=memory_peak,
            memory_average_mb=memory_avg,
            cpu_peak_percent=cpu_peak,
            cpu_average_percent=cpu_avg,
            error_rate=failed_requests / total_requests * 100 if total_requests > 0 else 0,
            throughput_degradation=0,  # Not applicable for spike tests
            system_stability_score=stability_score,
            metadata={
                "base_rps": base_rps,
                "spike_rps": spike_rps,
                "spike_duration": spike_duration,
                "actual_rps": total_requests / test_duration,
                "resource_samples": len(self.resource_usage)
            }
        )
        
        self.results.append(result)
        return result
    
    async def memory_pressure_test(self,
                                 agent_id: str,
                                 concurrent_requests: int,
                                 iterations: int,
                                 memory_limit_mb: Optional[int] = None,
                                 test_message: str = "Memory pressure test message") -> StressTestResult:
        """
        Run memory pressure test to check memory handling.
        
        Args:
            agent_id: Agent to test
            concurrent_requests: Number of concurrent requests
            iterations: Number of iterations
            memory_limit_mb: Optional memory limit to enforce
            test_message: Message to send
            
        Returns:
            StressTestResult with memory usage metrics
        """
        self.start_resource_monitoring()
        
        start_time = time.time()
        request_times = []
        successful_requests = 0
        failed_requests = 0
        total_requests = 0
        
        async def send_batch():
            """Send batch of concurrent requests."""
            async def single_request():
                req_start = time.time()
                try:
                    agent = AgentRegistry.get_agent(agent_id)
                    await agent.run(test_message)
                    req_end = time.time()
                    return True, req_end - req_start
                except Exception as e:
                    req_end = time.time()
                    logger.error(f"Request failed: {e}")
                    return False, req_end - req_start
            
            # Send concurrent requests
            tasks = [single_request() for _ in range(concurrent_requests)]
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # Run memory pressure test
        for iteration in range(iterations):
            logger.info(f"Memory pressure test iteration {iteration + 1}/{iterations}")
            
            # Check memory limit
            if memory_limit_mb:
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                if current_memory > memory_limit_mb:
                    logger.warning(f"Memory limit exceeded: {current_memory:.1f}MB > {memory_limit_mb}MB")
                    break
            
            # Send batch
            batch_results = await send_batch()
            
            # Process results
            for result in batch_results:
                total_requests += 1
                if isinstance(result, Exception):
                    failed_requests += 1
                    request_times.append(0.0)
                else:
                    success, duration = result
                    if success:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                    request_times.append(duration)
            
            # Force garbage collection
            gc.collect()
            
            # Small delay between iterations
            await asyncio.sleep(0.1)
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        self.stop_resource_monitoring()
        
        # Calculate metrics
        percentiles = self._calculate_percentiles([t for t in request_times if t > 0])
        avg_response_time = sum(t for t in request_times if t > 0) / len([t for t in request_times if t > 0]) if request_times else 0
        
        # Resource usage metrics
        memory_values = [r.memory_mb for r in self.resource_usage]
        cpu_values = [r.cpu_percent for r in self.resource_usage]
        
        memory_peak = max(memory_values) if memory_values else 0
        memory_avg = sum(memory_values) / len(memory_values) if memory_values else 0
        cpu_peak = max(cpu_values) if cpu_values else 0
        cpu_avg = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        
        # Calculate stability metrics
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        response_time_variance = max(request_times) - min(request_times) if request_times else 0
        memory_stability = max(memory_values) - min(memory_values) if memory_values else 0
        
        stability_score = self._calculate_system_stability_score(
            success_rate, response_time_variance, memory_stability
        )
        
        result = StressTestResult(
            test_name=f"memory_pressure_{agent_id}_{concurrent_requests}x{iterations}",
            timestamp=datetime.now(timezone.utc),
            duration_seconds=test_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=total_requests / test_duration,
            average_response_time=avg_response_time,
            median_response_time=percentiles["p50"],
            p95_response_time=percentiles["p95"],
            p99_response_time=percentiles["p99"],
            min_response_time=min(request_times) if request_times else 0,
            max_response_time=max(request_times) if request_times else 0,
            memory_peak_mb=memory_peak,
            memory_average_mb=memory_avg,
            cpu_peak_percent=cpu_peak,
            cpu_average_percent=cpu_avg,
            error_rate=failed_requests / total_requests * 100 if total_requests > 0 else 0,
            throughput_degradation=0,  # Not applicable for memory tests
            system_stability_score=stability_score,
            metadata={
                "concurrent_requests": concurrent_requests,
                "iterations": iterations,
                "memory_limit_mb": memory_limit_mb,
                "memory_growth": memory_peak - memory_values[0] if memory_values else 0,
                "resource_samples": len(self.resource_usage)
            }
        )
        
        self.results.append(result)
        return result
    
    def save_results(self, filename: Optional[str] = None) -> str:
        """Save stress test results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stress_test_results_{timestamp}.json"
        
        filepath = self.results_dir / filename
        
        data = {
            "stress_test_results": [asdict(r) for r in self.results],
            "resource_usage": [asdict(r) for r in self.resource_usage],
            "metadata": {
                "total_tests": len(self.results),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "system_info": {
                    "cpu_count": psutil.cpu_count(),
                    "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                    "disk_total_gb": psutil.disk_usage('/').total / (1024**3)
                }
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return str(filepath)
    
    def generate_stress_report(self) -> Dict[str, Any]:
        """Generate comprehensive stress test report."""
        if not self.results:
            return {"error": "No stress test results available"}
        
        # Overall statistics
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        total_failed = sum(r.failed_requests for r in self.results)
        
        # Performance metrics
        avg_rps = sum(r.requests_per_second for r in self.results) / len(self.results)
        avg_response_time = sum(r.average_response_time for r in self.results) / len(self.results)
        avg_error_rate = sum(r.error_rate for r in self.results) / len(self.results)
        
        # Resource usage
        peak_memory = max(r.memory_peak_mb for r in self.results)
        avg_memory = sum(r.memory_average_mb for r in self.results) / len(self.results)
        peak_cpu = max(r.cpu_peak_percent for r in self.results)
        avg_cpu = sum(r.cpu_average_percent for r in self.results) / len(self.results)
        
        # Stability metrics
        avg_stability = sum(r.system_stability_score for r in self.results) / len(self.results)
        
        # Test-specific analysis
        test_breakdown = {}
        for result in self.results:
            test_type = result.test_name.split('_')[0]
            if test_type not in test_breakdown:
                test_breakdown[test_type] = []
            test_breakdown[test_type].append(result)
        
        return {
            "summary": {
                "total_tests": len(self.results),
                "total_requests": total_requests,
                "total_successful": total_successful,
                "total_failed": total_failed,
                "overall_success_rate": total_successful / total_requests * 100 if total_requests > 0 else 0,
                "average_rps": avg_rps,
                "average_response_time": avg_response_time,
                "average_error_rate": avg_error_rate,
                "average_stability_score": avg_stability
            },
            "resource_usage": {
                "peak_memory_mb": peak_memory,
                "average_memory_mb": avg_memory,
                "peak_cpu_percent": peak_cpu,
                "average_cpu_percent": avg_cpu
            },
            "test_breakdown": {
                test_type: {
                    "count": len(results),
                    "avg_rps": sum(r.requests_per_second for r in results) / len(results),
                    "avg_stability": sum(r.system_stability_score for r in results) / len(results)
                }
                for test_type, results in test_breakdown.items()
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Test classes for pytest integration
class TestStressLoad:
    """Stress load test suite."""
    
    @pytest.fixture
    def stress_suite(self):
        """Create stress test suite instance."""
        return StressTestSuite()
    
    @pytest.mark.asyncio
    async def test_sustained_load_low(self, stress_suite):
        """Test sustained low load."""
        result = await stress_suite.sustained_load_test(
            agent_id="pagbank-specialist",
            requests_per_second=2.0,
            duration_seconds=30
        )
        
        assert result.error_rate < 10.0  # Less than 10% error rate
        assert result.system_stability_score > 70.0  # Stability score > 70
        assert result.memory_peak_mb < 1000.0  # Less than 1GB memory
        
    @pytest.mark.asyncio
    async def test_sustained_load_medium(self, stress_suite):
        """Test sustained medium load."""
        result = await stress_suite.sustained_load_test(
            agent_id="pagbank-specialist",
            requests_per_second=5.0,
            duration_seconds=60
        )
        
        assert result.error_rate < 20.0  # Less than 20% error rate
        assert result.system_stability_score > 50.0  # Stability score > 50
        assert result.throughput_degradation < 50.0  # Less than 50% degradation
        
    @pytest.mark.asyncio
    async def test_spike_load(self, stress_suite):
        """Test spike load handling."""
        result = await stress_suite.spike_load_test(
            agent_id="pagbank-specialist",
            base_rps=2.0,
            spike_rps=10.0,
            spike_duration=10,
            total_duration=60
        )
        
        assert result.error_rate < 30.0  # Less than 30% error rate under spikes
        assert result.system_stability_score > 40.0  # Stability score > 40
        assert result.memory_peak_mb < 2000.0  # Less than 2GB memory
        
    @pytest.mark.asyncio
    async def test_memory_pressure(self, stress_suite):
        """Test memory pressure handling."""
        result = await stress_suite.memory_pressure_test(
            agent_id="pagbank-specialist",
            concurrent_requests=10,
            iterations=20,
            memory_limit_mb=1500
        )
        
        assert result.error_rate < 25.0  # Less than 25% error rate
        assert result.system_stability_score > 50.0  # Stability score > 50
        assert result.memory_peak_mb < 1500.0  # Respect memory limit


class TestSystemLimits:
    """System limits and breaking point tests."""
    
    @pytest.fixture
    def stress_suite(self):
        """Create stress test suite instance."""
        return StressTestSuite()
    
    @pytest.mark.asyncio
    async def test_find_breaking_point(self, stress_suite):
        """Find system breaking point by gradually increasing load."""
        rps_levels = [1, 2, 5, 10, 20, 50]
        breaking_point = None
        
        for rps in rps_levels:
            logger.info(f"Testing RPS level: {rps}")
            
            result = await stress_suite.sustained_load_test(
                agent_id="pagbank-specialist",
                requests_per_second=rps,
                duration_seconds=30
            )
            
            # Consider breaking point if error rate > 50% or stability < 30
            if result.error_rate > 50.0 or result.system_stability_score < 30.0:
                breaking_point = rps
                break
        
        if breaking_point:
            logger.info(f"Breaking point found at {breaking_point} RPS")
        else:
            logger.info("No breaking point found within tested range")
        
        # Assert that system can handle at least 5 RPS
        assert breaking_point is None or breaking_point > 5


# CLI script for running stress tests
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Genie Agents stress tests")
    parser.add_argument("--test-type", choices=["sustained", "spike", "memory", "all"], 
                       default="all", help="Type of stress test to run")
    parser.add_argument("--agent", type=str, default="pagbank-specialist", 
                       help="Agent to test")
    parser.add_argument("--duration", type=int, default=60, 
                       help="Test duration in seconds")
    parser.add_argument("--rps", type=float, default=5.0, 
                       help="Requests per second")
    parser.add_argument("--spike-rps", type=float, default=20.0, 
                       help="Spike requests per second")
    parser.add_argument("--concurrent", type=int, default=10, 
                       help="Concurrent requests for memory test")
    parser.add_argument("--iterations", type=int, default=20, 
                       help="Iterations for memory test")
    
    args = parser.parse_args()
    
    async def main():
        stress_suite = StressTestSuite()
        
        if args.test_type in ["sustained", "all"]:
            print(f"Running sustained load test: {args.rps} RPS for {args.duration}s")
            await stress_suite.sustained_load_test(
                agent_id=args.agent,
                requests_per_second=args.rps,
                duration_seconds=args.duration
            )
        
        if args.test_type in ["spike", "all"]:
            print(f"Running spike load test: {args.rps} -> {args.spike_rps} RPS")
            await stress_suite.spike_load_test(
                agent_id=args.agent,
                base_rps=args.rps,
                spike_rps=args.spike_rps,
                spike_duration=10,
                total_duration=args.duration
            )
        
        if args.test_type in ["memory", "all"]:
            print(f"Running memory pressure test: {args.concurrent} concurrent x {args.iterations} iterations")
            await stress_suite.memory_pressure_test(
                agent_id=args.agent,
                concurrent_requests=args.concurrent,
                iterations=args.iterations
            )
        
        # Save results
        results_file = stress_suite.save_results()
        print(f"Results saved to: {results_file}")
        
        # Generate report
        report = stress_suite.generate_stress_report()
        print("\nStress Test Report:")
        print(json.dumps(report, indent=2))
    
    asyncio.run(main())