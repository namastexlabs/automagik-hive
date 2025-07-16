"""
Performance benchmark tests for Genie Agents multi-agent system.

This module provides comprehensive performance testing for:
- Agent execution timing
- Concurrency handling
- Memory usage monitoring
- Version comparison baselines
"""

import asyncio
import time
import threading
import psutil
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest
import aiohttp
from agno.agent import Agent
from agno.team import Team

from agents.registry import AgentRegistry
from teams.ana.team import get_ana_team
from config.settings import settings
from utils.log import logger


@dataclass
class BenchmarkResult:
    """Performance benchmark result data structure."""
    test_name: str
    timestamp: datetime
    duration_seconds: float
    success: bool
    memory_usage_mb: float
    cpu_percent: float
    agent_id: Optional[str] = None
    version: Optional[str] = None
    request_count: int = 1
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ConcurrencyResult:
    """Concurrency test result data structure."""
    test_name: str
    timestamp: datetime
    concurrent_requests: int
    total_duration_seconds: float
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    memory_peak_mb: float
    cpu_peak_percent: float


class PerformanceBenchmark:
    """Performance benchmark suite for Genie Agents."""
    
    def __init__(self, results_dir: str = "tests/performance/results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []
        self.concurrency_results: List[ConcurrencyResult] = []
        
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        return psutil.cpu_percent(interval=0.1)
    
    async def benchmark_agent_execution(
        self, 
        agent_id: str, 
        test_message: str = "Test message for performance benchmark",
        version: Optional[str] = None
    ) -> BenchmarkResult:
        """
        Benchmark single agent execution time.
        
        Args:
            agent_id: Agent identifier
            test_message: Message to send to agent
            version: Agent version (if applicable)
            
        Returns:
            BenchmarkResult with timing and resource usage
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            # Get agent from registry
            from agents.registry import AgentRegistry
            agent = AgentRegistry.get_agent(agent_id, version=version)
            
            # Execute agent
            response = await agent.run(test_message)
            
            end_time = time.time()
            end_memory = self._get_memory_usage()
            cpu_usage = self._get_cpu_usage()
            
            result = BenchmarkResult(
                test_name=f"agent_execution_{agent_id}",
                timestamp=datetime.now(timezone.utc),
                duration_seconds=end_time - start_time,
                success=True,
                memory_usage_mb=end_memory - start_memory,
                cpu_percent=cpu_usage,
                agent_id=agent_id,
                version=version,
                metadata={"response_length": len(str(response))}
            )
            
        except Exception as e:
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            result = BenchmarkResult(
                test_name=f"agent_execution_{agent_id}",
                timestamp=datetime.now(timezone.utc),
                duration_seconds=end_time - start_time,
                success=False,
                memory_usage_mb=end_memory - start_memory,
                cpu_percent=0.0,
                agent_id=agent_id,
                version=version,
                error_message=str(e)
            )
            
        self.results.append(result)
        return result
    
    async def benchmark_team_routing(
        self, 
        test_message: str = "Test routing performance",
        iterations: int = 10
    ) -> List[BenchmarkResult]:
        """
        Benchmark team routing performance.
        
        Args:
            test_message: Message to send to team
            iterations: Number of iterations to run
            
        Returns:
            List of BenchmarkResult for each iteration
        """
        results = []
        team = get_ana_team()
        
        for i in range(iterations):
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            try:
                response = await team.run(f"{test_message} - iteration {i+1}")
                
                end_time = time.time()
                end_memory = self._get_memory_usage()
                cpu_usage = self._get_cpu_usage()
                
                result = BenchmarkResult(
                    test_name=f"team_routing_iteration_{i+1}",
                    timestamp=datetime.now(timezone.utc),
                    duration_seconds=end_time - start_time,
                    success=True,
                    memory_usage_mb=end_memory - start_memory,
                    cpu_percent=cpu_usage,
                    metadata={"iteration": i+1, "total_iterations": iterations}
                )
                
            except Exception as e:
                end_time = time.time()
                end_memory = self._get_memory_usage()
                
                result = BenchmarkResult(
                    test_name=f"team_routing_iteration_{i+1}",
                    timestamp=datetime.now(timezone.utc),
                    duration_seconds=end_time - start_time,
                    success=False,
                    memory_usage_mb=end_memory - start_memory,
                    cpu_percent=0.0,
                    error_message=str(e),
                    metadata={"iteration": i+1, "total_iterations": iterations}
                )
            
            results.append(result)
            self.results.append(result)
        
        return results
    
    async def benchmark_concurrency(
        self, 
        agent_id: str,
        concurrent_requests: int = 10,
        test_message: str = "Concurrent test message"
    ) -> ConcurrencyResult:
        """
        Benchmark concurrent request handling.
        
        Args:
            agent_id: Agent to test
            concurrent_requests: Number of concurrent requests
            test_message: Message to send
            
        Returns:
            ConcurrencyResult with performance metrics
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        # Track individual request times
        request_times = []
        successful_requests = 0
        failed_requests = 0
        
        async def single_request() -> Tuple[bool, float]:
            """Execute single request and return success status and duration."""
            req_start = time.time()
            try:
                agent = AgentRegistry.get_agent(agent_id)
                await agent.run(test_message)
                req_end = time.time()
                return True, req_end - req_start
            except Exception:
                req_end = time.time()
                return False, req_end - req_start
        
        # Execute concurrent requests
        tasks = [single_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
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
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        total_duration = end_time - start_time
        
        # Calculate metrics
        valid_times = [t for t in request_times if t > 0]
        avg_response_time = sum(valid_times) / len(valid_times) if valid_times else 0
        min_response_time = min(valid_times) if valid_times else 0
        max_response_time = max(valid_times) if valid_times else 0
        requests_per_second = concurrent_requests / total_duration if total_duration > 0 else 0
        
        result = ConcurrencyResult(
            test_name=f"concurrency_{agent_id}_{concurrent_requests}",
            timestamp=datetime.now(timezone.utc),
            concurrent_requests=concurrent_requests,
            total_duration_seconds=total_duration,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            requests_per_second=requests_per_second,
            memory_peak_mb=end_memory - start_memory,
            cpu_peak_percent=self._get_cpu_usage()
        )
        
        self.concurrency_results.append(result)
        return result
    
    def save_results(self, filename: Optional[str] = None) -> str:
        """
        Save benchmark results to JSON file.
        
        Args:
            filename: Optional filename, defaults to timestamp-based name
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"
        
        filepath = self.results_dir / filename
        
        data = {
            "benchmark_results": [asdict(r) for r in self.results],
            "concurrency_results": [asdict(r) for r in self.concurrency_results],
            "metadata": {
                "total_tests": len(self.results) + len(self.concurrency_results),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "system_info": {
                    "cpu_count": psutil.cpu_count(),
                    "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                    "python_version": psutil.version_info if hasattr(psutil, 'version_info') else None
                }
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return str(filepath)
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate performance report summary.
        
        Returns:
            Dictionary with performance metrics and analysis
        """
        if not self.results and not self.concurrency_results:
            return {"error": "No benchmark results available"}
        
        # Analyze benchmark results
        successful_benchmarks = [r for r in self.results if r.success]
        failed_benchmarks = [r for r in self.results if not r.success]
        
        benchmark_stats = {
            "total_tests": len(self.results),
            "successful_tests": len(successful_benchmarks),
            "failed_tests": len(failed_benchmarks),
            "success_rate": len(successful_benchmarks) / len(self.results) * 100 if self.results else 0,
            "average_duration": sum(r.duration_seconds for r in successful_benchmarks) / len(successful_benchmarks) if successful_benchmarks else 0,
            "min_duration": min(r.duration_seconds for r in successful_benchmarks) if successful_benchmarks else 0,
            "max_duration": max(r.duration_seconds for r in successful_benchmarks) if successful_benchmarks else 0,
            "average_memory_usage": sum(r.memory_usage_mb for r in successful_benchmarks) / len(successful_benchmarks) if successful_benchmarks else 0
        }
        
        # Analyze concurrency results
        concurrency_stats = {}
        if self.concurrency_results:
            concurrency_stats = {
                "total_concurrency_tests": len(self.concurrency_results),
                "average_rps": sum(r.requests_per_second for r in self.concurrency_results) / len(self.concurrency_results),
                "max_rps": max(r.requests_per_second for r in self.concurrency_results),
                "average_success_rate": sum(r.successful_requests / r.concurrent_requests * 100 for r in self.concurrency_results) / len(self.concurrency_results)
            }
        
        return {
            "benchmark_stats": benchmark_stats,
            "concurrency_stats": concurrency_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Test classes for pytest integration
class TestAgentPerformance:
    """Agent performance test suite."""
    
    @pytest.fixture
    def benchmark(self):
        """Create benchmark instance."""
        return PerformanceBenchmark()
    
    @pytest.mark.asyncio
    async def test_pagbank_agent_performance(self, benchmark):
        """Test PagBank agent performance."""
        result = await benchmark.benchmark_agent_execution(
            agent_id="pagbank-specialist",
            test_message="Preciso de ajuda com meu cartão de crédito"
        )
        
        assert result.success
        assert result.duration_seconds < 10.0  # Should respond within 10 seconds
        assert result.memory_usage_mb < 500.0  # Should use less than 500MB
        
    @pytest.mark.asyncio
    async def test_adquirencia_agent_performance(self, benchmark):
        """Test Adquirencia agent performance."""
        result = await benchmark.benchmark_agent_execution(
            agent_id="adquirencia-specialist",
            test_message="Como configurar minha máquina de cartão?"
        )
        
        assert result.success
        assert result.duration_seconds < 10.0
        assert result.memory_usage_mb < 500.0
        
    @pytest.mark.asyncio
    async def test_team_routing_performance(self, benchmark):
        """Test team routing performance."""
        results = await benchmark.benchmark_team_routing(
            test_message="Teste de performance do roteamento",
            iterations=5
        )
        
        successful_results = [r for r in results if r.success]
        assert len(successful_results) >= 4  # At least 80% success rate
        
        avg_duration = sum(r.duration_seconds for r in successful_results) / len(successful_results)
        assert avg_duration < 15.0  # Average routing should be under 15 seconds


class TestConcurrencyPerformance:
    """Concurrency performance test suite."""
    
    @pytest.fixture
    def benchmark(self):
        """Create benchmark instance."""
        return PerformanceBenchmark()
    
    @pytest.mark.asyncio
    async def test_low_concurrency(self, benchmark):
        """Test low concurrency (5 concurrent requests)."""
        result = await benchmark.benchmark_concurrency(
            agent_id="pagbank-specialist",
            concurrent_requests=5,
            test_message="Concurrency test - low load"
        )
        
        assert result.successful_requests >= 4  # At least 80% success rate
        assert result.requests_per_second > 0.5  # At least 0.5 RPS
        assert result.average_response_time < 20.0  # Average response under 20s
        
    @pytest.mark.asyncio
    async def test_medium_concurrency(self, benchmark):
        """Test medium concurrency (20 concurrent requests)."""
        result = await benchmark.benchmark_concurrency(
            agent_id="pagbank-specialist",
            concurrent_requests=20,
            test_message="Concurrency test - medium load"
        )
        
        assert result.successful_requests >= 16  # At least 80% success rate
        assert result.requests_per_second > 0.8  # At least 0.8 RPS
        assert result.average_response_time < 30.0  # Average response under 30s
        
    @pytest.mark.asyncio
    async def test_high_concurrency(self, benchmark):
        """Test high concurrency (50 concurrent requests)."""
        result = await benchmark.benchmark_concurrency(
            agent_id="pagbank-specialist",
            concurrent_requests=50,
            test_message="Concurrency test - high load"
        )
        
        # More relaxed requirements for high concurrency
        assert result.successful_requests >= 35  # At least 70% success rate
        assert result.requests_per_second > 1.0  # At least 1 RPS
        assert result.average_response_time < 45.0  # Average response under 45s


class TestVersionComparison:
    """Version comparison and baseline tracking."""
    
    @pytest.fixture
    def benchmark(self):
        """Create benchmark instance."""
        return PerformanceBenchmark()
    
    def save_baseline(self, benchmark_results: List[BenchmarkResult], version: str):
        """Save performance baseline for version comparison."""
        baseline_file = Path("tests/performance/baselines") / f"baseline_{version}.json"
        baseline_file.parent.mkdir(parents=True, exist_ok=True)
        
        baseline_data = {
            "version": version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": [asdict(r) for r in benchmark_results],
            "summary": {
                "avg_duration": sum(r.duration_seconds for r in benchmark_results if r.success) / len([r for r in benchmark_results if r.success]),
                "success_rate": len([r for r in benchmark_results if r.success]) / len(benchmark_results) * 100,
                "avg_memory": sum(r.memory_usage_mb for r in benchmark_results if r.success) / len([r for r in benchmark_results if r.success])
            }
        }
        
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2, default=str)
    
    @pytest.mark.asyncio
    async def test_create_version_baseline(self, benchmark):
        """Create baseline for current version."""
        # Test all main agents
        agents_to_test = ["pagbank-specialist", "adquirencia-specialist", "emissao-specialist"]
        
        for agent_id in agents_to_test:
            await benchmark.benchmark_agent_execution(
                agent_id=agent_id,
                test_message=f"Baseline test for {agent_id}"
            )
        
        # Test team routing
        await benchmark.benchmark_team_routing(iterations=3)
        
        # Save baseline
        version = "v1.0"  # This should be read from version control or environment
        self.save_baseline(benchmark.results, version)
        
        # Generate report
        report = benchmark.generate_report()
        assert report["benchmark_stats"]["success_rate"] > 80  # At least 80% success rate


# CLI script for running benchmarks
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Genie Agents performance benchmarks")
    parser.add_argument("--agent", type=str, help="Specific agent to benchmark")
    parser.add_argument("--concurrency", type=int, default=10, help="Number of concurrent requests")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations")
    parser.add_argument("--save-baseline", action="store_true", help="Save results as baseline")
    parser.add_argument("--version", type=str, help="Version identifier for baseline")
    
    args = parser.parse_args()
    
    async def main():
        benchmark = PerformanceBenchmark()
        
        if args.agent:
            # Test specific agent
            print(f"Benchmarking agent: {args.agent}")
            result = await benchmark.benchmark_agent_execution(args.agent)
            print(f"Duration: {result.duration_seconds:.2f}s, Success: {result.success}")
            
            # Test concurrency
            print(f"Testing concurrency with {args.concurrency} requests...")
            concurrency_result = await benchmark.benchmark_concurrency(
                args.agent, 
                concurrent_requests=args.concurrency
            )
            print(f"RPS: {concurrency_result.requests_per_second:.2f}, Success Rate: {concurrency_result.successful_requests/concurrency_result.concurrent_requests*100:.1f}%")
            
        else:
            # Test all agents
            agents = ["pagbank-specialist", "adquirencia-specialist", "emissao-specialist"]
            for agent_id in agents:
                print(f"Benchmarking {agent_id}...")
                await benchmark.benchmark_agent_execution(agent_id)
            
            # Test team routing
            print("Testing team routing...")
            await benchmark.benchmark_team_routing(iterations=args.iterations)
        
        # Save results
        results_file = benchmark.save_results()
        print(f"Results saved to: {results_file}")
        
        # Generate report
        report = benchmark.generate_report()
        print("\nPerformance Report:")
        print(json.dumps(report, indent=2))
        
        # Save baseline if requested
        if args.save_baseline and args.version:
            test_instance = TestVersionComparison()
            test_instance.save_baseline(benchmark.results, args.version)
            print(f"Baseline saved for version: {args.version}")
    
    asyncio.run(main())