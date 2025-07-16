#!/usr/bin/env python3
"""
🚀 Genie Agents Performance Suite - Unified Entry Point
Single script to run all performance tests with mock LLM support.
"""

import asyncio
import argparse
import sys
import os
import time
import json
import platform
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Optional imports with fallbacks
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️  psutil not installed - system metrics will be limited")

try:
    from tests.performance.mock_llm import MockLLMContext, MockLLM
    HAS_MOCK_LLM = True
except ImportError:
    HAS_MOCK_LLM = False
    print("⚠️  Mock LLM not available - using simulation")
    
    # Fallback mock context
    class MockLLMContext:
        def __init__(self, enable_mock=True):
            self.enable_mock = enable_mock
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass

try:
    from agents.registry import AgentRegistry
    HAS_AGENT_REGISTRY = True
except ImportError:
    HAS_AGENT_REGISTRY = False
    print("⚠️  Agent registry not available - using simulation")


@dataclass
class PerformanceResults:
    """Unified performance results structure."""
    timestamp: datetime
    version: str
    test_mode: str
    mock_enabled: bool
    system_info: Dict[str, Any]
    total_duration: float
    tests_completed: int
    agent_tests: List[Dict[str, Any]]
    concurrency_tests: List[Dict[str, Any]]
    stress_tests: List[Dict[str, Any]]
    summary: Dict[str, Any]


class UnifiedPerformanceSuite:
    """Unified performance test suite."""
    
    def __init__(self, version: str = "current", use_mock: bool = True):
        self.version = version
        self.use_mock = use_mock
        self.start_time = datetime.now(timezone.utc)
        self.mock_llm = MockLLM(base_latency=1.0, latency_variance=0.5) if use_mock else None
        
        # Standard test agents
        self.test_agents = [
            ("pagbank-specialist", "Como fazer um PIX?"),
            ("adquirencia-specialist", "Como funciona a antecipação?"),
            ("emissao-specialist", "Qual o limite do cartão?"),
            ("human-handoff", "Preciso falar com um humano"),
            ("finalizacao", "Como finalizar meu atendimento?")
        ]
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "mock_enabled": self.use_mock
        }
        
        if HAS_PSUTIL:
            info.update({
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2)
            })
        else:
            info.update({
                "cpu_count": os.cpu_count() or 1,
                "memory_total_gb": "unknown"
            })
        
        return info
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if HAS_PSUTIL:
            return psutil.Process().memory_info().rss / (1024 * 1024)
        else:
            return 0.0  # Fallback when psutil not available
    
    def _simulate_agent_execution(self, agent_id: str, message: str) -> Dict[str, Any]:
        """Execute agent with proper simulation."""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            if self.use_mock and HAS_MOCK_LLM:
                # Use mock LLM for fast, realistic testing
                response = self.mock_llm.generate_response(message, agent_id)
                success = True
                response_length = len(response.content)
                error_message = None
            elif HAS_AGENT_REGISTRY:
                # Real agent execution
                agent = AgentRegistry.get_agent(agent_id)
                response = agent.run(message)
                success = True
                response_length = len(str(response))
                error_message = None
            else:
                # Fallback simulation
                time.sleep(1.0 + (hash(agent_id) % 1000) / 1000.0)  # Simulate realistic latency
                success = True
                response_length = 1000 + (hash(message) % 500)  # Simulate response size
                error_message = None
                
        except Exception as e:
            success = False
            response_length = 0
            error_message = str(e)
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        return {
            "agent_id": agent_id,
            "message": message,
            "success": success,
            "duration_seconds": end_time - start_time,
            "response_length": response_length,
            "memory_usage_mb": end_memory - start_memory,
            "error_message": error_message
        }
    
    async def run_agent_tests(self, verbose: bool = True) -> List[Dict[str, Any]]:
        """Run individual agent performance tests."""
        if verbose:
            print("🧪 Agent Performance Tests")
            print("=" * 40)
        
        results = []
        
        for agent_id, message in self.test_agents:
            if verbose:
                print(f"📊 Testing {agent_id}...")
            
            result = self._simulate_agent_execution(agent_id, message)
            results.append(result)
            
            if verbose:
                status = "✅" if result["success"] else "❌"
                print(f"  {status} {result['duration_seconds']:.2f}s - {result['response_length']:,} chars")
            
            # Small delay between tests
            await asyncio.sleep(0.1)
        
        return results
    
    async def run_concurrency_tests(self, levels: List[int] = None, verbose: bool = True) -> List[Dict[str, Any]]:
        """Run concurrency performance tests."""
        if verbose:
            print("\n🏁 Concurrency Performance Tests")
            print("=" * 40)
        
        if levels is None:
            levels = [3, 5, 10, 20] if self.use_mock else [3, 5]
        
        results = []
        
        for concurrent_requests in levels:
            if verbose:
                print(f"📊 Testing {concurrent_requests} concurrent requests...")
            
            start_time = time.time()
            
            # Create tasks for concurrent execution
            tasks = []
            for i in range(concurrent_requests):
                task = asyncio.create_task(
                    asyncio.to_thread(
                        self._simulate_agent_execution,
                        "pagbank-specialist",
                        f"Concurrency test {i}"
                    )
                )
                tasks.append(task)
            
            # Execute all tasks
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # Process results
            successful = 0
            failed = 0
            response_times = []
            
            for result in task_results:
                if isinstance(result, Exception):
                    failed += 1
                elif result["success"]:
                    successful += 1
                    response_times.append(result["duration_seconds"])
                else:
                    failed += 1
            
            # Calculate metrics
            success_rate = (successful / concurrent_requests) * 100
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            rps = concurrent_requests / total_duration
            
            result = {
                "concurrent_requests": concurrent_requests,
                "successful_requests": successful,
                "failed_requests": failed,
                "success_rate": success_rate,
                "total_duration": total_duration,
                "avg_response_time": avg_response_time,
                "requests_per_second": rps
            }
            
            results.append(result)
            
            if verbose:
                print(f"  ✅ {successful}/{concurrent_requests} successful ({success_rate:.1f}%)")
                print(f"  📊 RPS: {rps:.2f}, Avg: {avg_response_time:.2f}s")
        
        return results
    
    async def run_stress_tests(self, rps: float = 1.0, duration: int = 30, verbose: bool = True) -> List[Dict[str, Any]]:
        """Run stress tests."""
        if verbose:
            print("\n🔥 Stress Tests")
            print("=" * 40)
        
        results = []
        agent_id = "pagbank-specialist"
        
        # Sustained load test
        if verbose:
            print(f"📊 Sustained Load Test: {rps} RPS for {duration}s")
        
        start_time = time.time()
        request_times = []
        successful_requests = 0
        failed_requests = 0
        total_requests = 0
        
        async def send_request(request_id: int):
            """Send single request and track timing."""
            try:
                result = self._simulate_agent_execution(agent_id, f"Stress test {request_id}")
                return result["success"], result["duration_seconds"]
            except Exception as e:
                if verbose:
                    print(f"❌ Request {request_id} failed: {e}")
                return False, 0.0
        
        # Calculate request interval
        interval = 1.0 / rps
        
        # Run sustained load
        request_id = 0
        while time.time() - start_time < duration:
            request_start = time.time()
            
            # Send request
            success, req_duration = await send_request(request_id)
            request_times.append(req_duration)
            total_requests += 1
            request_id += 1
            
            if success:
                successful_requests += 1
            else:
                failed_requests += 1
            
            # Progress indicator
            if verbose and total_requests % 10 == 0:
                elapsed = time.time() - start_time
                print(f"  📈 {total_requests} requests in {elapsed:.1f}s (Success: {successful_requests}, Failed: {failed_requests})")
            
            # Wait for next interval
            elapsed = time.time() - request_start
            if elapsed < interval:
                await asyncio.sleep(interval - elapsed)
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        # Calculate metrics
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        actual_rps = total_requests / test_duration
        avg_response_time = sum(request_times) / len(request_times) if request_times else 0
        
        stress_result = {
            "test_type": "sustained_load",
            "target_rps": rps,
            "actual_rps": actual_rps,
            "duration": test_duration,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "min_response_time": min(request_times) if request_times else 0,
            "max_response_time": max(request_times) if request_times else 0
        }
        
        results.append(stress_result)
        
        if verbose:
            print(f"  ✅ Success Rate: {success_rate:.1f}%")
            print(f"  📊 Actual RPS: {actual_rps:.2f}")
            print(f"  ⏱️  Avg Response: {avg_response_time:.2f}s")
        
        # Memory pressure test
        if verbose:
            print(f"\n📊 Memory Pressure Test: 5 concurrent x 3 iterations")
        
        concurrent_requests = 5
        iterations = 3
        total_successful = 0
        total_failed = 0
        
        for iteration in range(iterations):
            # Send concurrent requests
            tasks = []
            for i in range(concurrent_requests):
                task = asyncio.create_task(
                    asyncio.to_thread(
                        self._simulate_agent_execution,
                        agent_id,
                        f"Memory test iteration {iteration} request {i}"
                    )
                )
                tasks.append(task)
            
            # Execute batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count results
            successful = sum(1 for r in batch_results if isinstance(r, dict) and r.get("success", False))
            failed = concurrent_requests - successful
            
            total_successful += successful
            total_failed += failed
            
            if verbose:
                print(f"  📈 Iteration {iteration + 1}: {successful}/{concurrent_requests} successful")
            
            # Small delay between iterations
            if iteration < iterations - 1:
                await asyncio.sleep(1)
        
        total_mem_requests = total_successful + total_failed
        mem_success_rate = (total_successful / total_mem_requests * 100) if total_mem_requests > 0 else 0
        
        memory_result = {
            "test_type": "memory_pressure",
            "concurrent_requests": concurrent_requests,
            "iterations": iterations,
            "total_requests": total_mem_requests,
            "successful_requests": total_successful,
            "failed_requests": total_failed,
            "success_rate": mem_success_rate
        }
        
        results.append(memory_result)
        
        if verbose:
            print(f"  ✅ Memory Success Rate: {mem_success_rate:.1f}%")
        
        return results
    
    def calculate_summary(self, agent_results: List[Dict], concurrency_results: List[Dict], stress_results: List[Dict]) -> Dict[str, Any]:
        """Calculate overall performance summary."""
        # Agent performance
        successful_agents = [r for r in agent_results if r["success"]]
        agent_success_rate = len(successful_agents) / len(agent_results) * 100 if agent_results else 0
        avg_agent_response = sum(r["duration_seconds"] for r in successful_agents) / len(successful_agents) if successful_agents else 0
        
        # Concurrency performance
        if concurrency_results:
            max_rps = max(r["requests_per_second"] for r in concurrency_results)
            avg_concurrency_success = sum(r["success_rate"] for r in concurrency_results) / len(concurrency_results)
            best_concurrency = max(concurrency_results, key=lambda x: x["requests_per_second"])
        else:
            max_rps = 0
            avg_concurrency_success = 0
            best_concurrency = None
        
        # Stress performance
        if stress_results:
            avg_stress_success = sum(r["success_rate"] for r in stress_results) / len(stress_results)
            sustained_load_result = next((r for r in stress_results if r["test_type"] == "sustained_load"), None)
            memory_pressure_result = next((r for r in stress_results if r["test_type"] == "memory_pressure"), None)
        else:
            avg_stress_success = 0
            sustained_load_result = None
            memory_pressure_result = None
        
        # Overall score calculation
        overall_score = (agent_success_rate + avg_concurrency_success + avg_stress_success) / 3
        
        # Performance grading
        if overall_score >= 95 and avg_agent_response < 3:
            grade = "A"
            status = "EXCELLENT"
        elif overall_score >= 90 and avg_agent_response < 5:
            grade = "B"
            status = "GOOD"
        elif overall_score >= 80 and avg_agent_response < 10:
            grade = "C"
            status = "ACCEPTABLE"
        else:
            grade = "D"
            status = "NEEDS IMPROVEMENT"
        
        return {
            "overall_score": overall_score,
            "grade": grade,
            "status": status,
            "agent_success_rate": agent_success_rate,
            "avg_agent_response_time": avg_agent_response,
            "max_rps": max_rps,
            "avg_concurrency_success": avg_concurrency_success,
            "best_concurrency_level": best_concurrency["concurrent_requests"] if best_concurrency else 0,
            "avg_stress_success": avg_stress_success,
            "sustained_load_success": sustained_load_result["success_rate"] if sustained_load_result else 0,
            "memory_pressure_success": memory_pressure_result["success_rate"] if memory_pressure_result else 0,
            "agents_tested": len(agent_results),
            "concurrency_tests": len(concurrency_results),
            "stress_tests": len(stress_results)
        }
    
    def generate_markdown_report(self, results: PerformanceResults) -> str:
        """Generate comprehensive markdown report."""
        test_type = "Mock LLM" if self.use_mock else "Real LLM"
        
        report = f"""# {test_type} Performance Test Report

## Test Overview

- **Date**: {results.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Version**: {results.version}
- **Test Mode**: {results.test_mode}
- **Mock Enabled**: {results.mock_enabled}
- **Duration**: {results.total_duration:.1f} seconds
- **Tests Completed**: {results.tests_completed}

## System Information

- **Platform**: {results.system_info['platform']}
- **Python**: {results.system_info['python_version']}
- **CPU Cores**: {results.system_info['cpu_count']}
- **Memory**: {results.system_info['memory_total_gb']} GB
- **Hostname**: {results.system_info['hostname']}

## 🎯 Overall Performance Summary

- **Overall Score**: {results.summary['overall_score']:.1f}%
- **Grade**: {results.summary['grade']}
- **Status**: {results.summary['status']}

### Key Metrics
- **Agent Success Rate**: {results.summary['agent_success_rate']:.1f}%
- **Average Response Time**: {results.summary['avg_agent_response_time']:.2f}s
- **Max RPS**: {results.summary['max_rps']:.2f}
- **Concurrency Success**: {results.summary['avg_concurrency_success']:.1f}%
- **Stress Test Success**: {results.summary['avg_stress_success']:.1f}%

## 🧪 Agent Performance Results

| Agent ID | Status | Duration | Response Size | Memory Usage | Success |
|----------|--------|----------|---------------|--------------|---------|
"""
        
        for result in results.agent_tests:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            error_info = f" ({result['error_message']})" if result.get("error_message") else ""
            memory_mb = result.get("memory_usage_mb", 0)
            
            report += f"| {result['agent_id']} | {status} | {result['duration_seconds']:.2f}s | {result['response_length']:,} chars | {memory_mb:.1f}MB | {result['success']}{error_info} |\n"
        
        if results.concurrency_tests:
            report += f"""
## 🏁 Concurrency Performance Results

| Concurrent Requests | Success Rate | RPS | Avg Response | Total Duration |
|-------------------|--------------|-----|-------------|----------------|
"""
            
            for result in results.concurrency_tests:
                report += f"| {result['concurrent_requests']} | {result['success_rate']:.1f}% | {result['requests_per_second']:.2f} | {result['avg_response_time']:.2f}s | {result['total_duration']:.2f}s |\n"
        
        if results.stress_tests:
            report += f"""
## 🔥 Stress Test Results

| Test Type | Requests | Success Rate | RPS | Avg Response | Duration |
|-----------|----------|--------------|-----|-------------|----------|
"""
            
            for result in results.stress_tests:
                if result["test_type"] == "sustained_load":
                    report += f"| Sustained Load | {result['total_requests']} | {result['success_rate']:.1f}% | {result['actual_rps']:.2f} | {result['avg_response_time']:.2f}s | {result['duration']:.1f}s |\n"
                elif result["test_type"] == "memory_pressure":
                    report += f"| Memory Pressure | {result['total_requests']} | {result['success_rate']:.1f}% | N/A | N/A | N/A |\n"
        
        report += f"""
## 📊 Performance Analysis

### Test Environment
"""
        
        if self.use_mock:
            report += """
**Mock LLM Testing** 🤖
- ✅ **Fast Execution**: Complete testing in seconds
- ✅ **Cost-Free**: No API charges
- ✅ **Consistent**: Repeatable results for CI/CD
- ✅ **Realistic**: Simulates actual response patterns
- 🎯 **Ideal For**: Development, CI/CD, frequent testing
"""
        else:
            report += """
**Real LLM Testing** 🔗
- ✅ **Production Accurate**: Real-world performance
- ⚠️ **API Costs**: Charges apply
- ⚠️ **Variable**: Network affects results
- 🎯 **Ideal For**: Production validation, baselines
"""
        
        report += f"""
### Performance Insights

**Response Time Analysis:**
- Average: {results.summary['avg_agent_response_time']:.2f}s
- Target: <3s excellent, <5s good, <10s acceptable
- Assessment: {results.summary['grade']} - {results.summary['status']}

**Concurrency Analysis:**
- Max RPS: {results.summary['max_rps']:.2f}
- Best Level: {results.summary['best_concurrency_level']} concurrent requests
- Success Rate: {results.summary['avg_concurrency_success']:.1f}%

**Stress Test Analysis:**
- Sustained Load: {results.summary['sustained_load_success']:.1f}% success
- Memory Pressure: {results.summary['memory_pressure_success']:.1f}% success
- Overall Resilience: {results.summary['avg_stress_success']:.1f}%

## 🎯 Recommendations

### Performance Optimization
"""
        
        recommendations = []
        
        if results.summary['avg_agent_response_time'] > 5:
            recommendations.append("🔧 **Optimize Response Times**: Current average is high for production")
        elif results.summary['avg_agent_response_time'] < 3:
            recommendations.append("🎉 **Excellent Response Times**: Performance is optimal")
        
        if results.summary['agent_success_rate'] < 100:
            recommendations.append("🔧 **Improve Reliability**: Address failing test scenarios")
        
        if results.summary['max_rps'] < 5:
            recommendations.append("🔧 **Enhance Throughput**: Consider performance optimizations")
        
        if results.summary['avg_stress_success'] < 85:
            recommendations.append("🔧 **Strengthen Resilience**: Improve performance under stress")
        
        if not recommendations:
            recommendations.append("🎉 **Excellent Performance**: All metrics within acceptable ranges")
        
        for rec in recommendations:
            report += f"- {rec}\n"
        
        report += f"""
### Testing Strategy
- 🚀 **Execution Time**: {results.total_duration:.1f}s total
- 🔄 **Automation Ready**: Suitable for CI/CD pipelines
- 📈 **Baseline Established**: Use these metrics as performance targets
- 🎯 **Cost**: {"Free with mock LLM" if self.use_mock else "Minimal API costs"}

### Next Steps
1. **Performance Monitoring**: Track these metrics over time
2. **Threshold Alerts**: Set alerts for degradation
3. **Regular Testing**: Integrate into development workflow
4. **Optimization**: Address any performance bottlenecks identified

---

**Generated by Genie Agents Unified Performance Suite**  
*Total Runtime: {results.total_duration:.1f} seconds*  
*Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
        
        return report
    
    def save_results(self, results: PerformanceResults, data_dir: str = "data") -> Tuple[str, str]:
        """Save results to data directory."""
        data_path = Path(data_dir)
        data_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = results.timestamp.strftime('%Y%m%d_%H%M%S')
        test_type = "unified_mock" if self.use_mock else "unified_real"
        
        # Save JSON data
        json_filename = f"performance_results_{test_type}_{timestamp}.json"
        json_filepath = data_path / json_filename
        
        with open(json_filepath, 'w') as f:
            json.dump(asdict(results), f, indent=2, default=str)
        
        # Save markdown report
        md_filename = f"performance_report_{test_type}_{timestamp}.md"
        md_filepath = data_path / md_filename
        
        markdown_report = self.generate_markdown_report(results)
        with open(md_filepath, 'w') as f:
            f.write(markdown_report)
        
        return str(json_filepath), str(md_filepath)
    
    async def run_quick_test(self) -> PerformanceResults:
        """Run quick test suite (agents + basic concurrency)."""
        print(f"⚡ Quick Performance Test Suite")
        print(f"🤖 Mode: {'Mock LLM' if self.use_mock else 'Real LLM'}")
        print("=" * 50)
        
        # Run basic tests
        agent_results = await self.run_agent_tests()
        concurrency_results = await self.run_concurrency_tests(levels=[3, 5])
        stress_results = []  # Skip stress tests for quick mode
        
        # Calculate summary
        summary = self.calculate_summary(agent_results, concurrency_results, stress_results)
        
        # Create results
        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - self.start_time).total_seconds()
        
        results = PerformanceResults(
            timestamp=self.start_time,
            version=self.version,
            test_mode="Quick Test",
            mock_enabled=self.use_mock,
            system_info=self._get_system_info(),
            total_duration=total_duration,
            tests_completed=len(agent_results) + len(concurrency_results),
            agent_tests=agent_results,
            concurrency_tests=concurrency_results,
            stress_tests=stress_results,
            summary=summary
        )
        
        return results
    
    async def run_full_test(self) -> PerformanceResults:
        """Run comprehensive test suite."""
        print(f"🏃 Full Performance Test Suite")
        print(f"🤖 Mode: {'Mock LLM' if self.use_mock else 'Real LLM'}")
        print("=" * 50)
        
        # Run all tests
        agent_results = await self.run_agent_tests()
        concurrency_results = await self.run_concurrency_tests()
        stress_results = await self.run_stress_tests()
        
        # Calculate summary
        summary = self.calculate_summary(agent_results, concurrency_results, stress_results)
        
        # Create results
        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - self.start_time).total_seconds()
        
        results = PerformanceResults(
            timestamp=self.start_time,
            version=self.version,
            test_mode="Full Test",
            mock_enabled=self.use_mock,
            system_info=self._get_system_info(),
            total_duration=total_duration,
            tests_completed=len(agent_results) + len(concurrency_results) + len(stress_results),
            agent_tests=agent_results,
            concurrency_tests=concurrency_results,
            stress_tests=stress_results,
            summary=summary
        )
        
        return results
    
    async def run_stress_only(self, rps: float = 1.0, duration: int = 30) -> PerformanceResults:
        """Run stress tests only."""
        print(f"🔥 Stress Test Suite")
        print(f"🤖 Mode: {'Mock LLM' if self.use_mock else 'Real LLM'}")
        print("=" * 50)
        
        # Run stress tests only
        agent_results = []
        concurrency_results = []
        stress_results = await self.run_stress_tests(rps=rps, duration=duration)
        
        # Calculate summary
        summary = self.calculate_summary(agent_results, concurrency_results, stress_results)
        
        # Create results
        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - self.start_time).total_seconds()
        
        results = PerformanceResults(
            timestamp=self.start_time,
            version=self.version,
            test_mode="Stress Test",
            mock_enabled=self.use_mock,
            system_info=self._get_system_info(),
            total_duration=total_duration,
            tests_completed=len(stress_results),
            agent_tests=agent_results,
            concurrency_tests=concurrency_results,
            stress_tests=stress_results,
            summary=summary
        )
        
        return results


def print_banner():
    """Print application banner."""
    print("🚀 Genie Agents Unified Performance Suite")
    print("=" * 60)


def print_help():
    """Print comprehensive help."""
    print("""
🎯 PERFORMANCE TEST MODES:

⚡ QUICK (Default - Recommended for development):
  python run_performance_suite.py quick
  • Ultra-fast testing (10-30 seconds)
  • Agent + basic concurrency tests
  • Perfect for CI/CD and development

🏃 FULL (Comprehensive testing):
  python run_performance_suite.py full
  • Complete test suite (2-10 minutes)
  • Agent + concurrency + stress tests
  • Detailed performance analysis

🔥 STRESS (Stress testing only):
  python run_performance_suite.py stress [--rps 1.0] [--duration 30]
  • Sustained load + memory pressure tests
  • System breaking point detection
  • Performance under load validation

🔧 OPTIONS:
  --mock          Use mock LLM (default, fast and free)
  --real          Use real LLM (production-accurate, API costs)
  --rps N         Requests per second for stress tests
  --duration N    Duration in seconds for stress tests
  --version V     Version identifier
  --output DIR    Output directory for reports
  --verbose       Detailed output during testing
  --help          Show this help message

🚀 EXAMPLES:
  # Quick development testing (recommended)
  python run_performance_suite.py quick
  
  # Full testing with mock LLM
  python run_performance_suite.py full --mock
  
  # Stress testing with custom parameters
  python run_performance_suite.py stress --rps 2.0 --duration 60
  
  # Real LLM testing (API costs apply)
  python run_performance_suite.py full --real

💡 RECOMMENDATIONS:
  • Use 'quick' for frequent development testing
  • Use 'full' for comprehensive validation before releases
  • Use 'stress' to find system performance limits
  • Use --mock for cost-free, fast, realistic testing
  • Use --real for production-accurate measurements
""")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Genie Agents Unified Performance Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Test mode
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["quick", "full", "stress", "help"],
        default="quick",
        help="Test mode to run"
    )
    
    # LLM mode
    parser.add_argument("--mock", action="store_true", help="Use mock LLM (default)")
    parser.add_argument("--real", action="store_true", help="Use real LLM")
    
    # Stress test options
    parser.add_argument("--rps", type=float, default=1.0, help="Requests per second")
    parser.add_argument("--duration", type=int, default=30, help="Duration in seconds")
    
    # General options
    parser.add_argument("--version", type=str, default="current", help="Version identifier")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Handle help
    if args.mode == "help" or len(sys.argv) == 1:
        print_banner()
        print_help()
        return 0
    
    # Determine test mode
    use_mock = not args.real  # Default to mock unless --real specified
    
    # Override with environment variable
    if os.getenv("USE_MOCK_LLM", "").lower() in ("true", "1"):
        use_mock = True
    
    # Print configuration
    print_banner()
    print(f"🎯 Mode: {args.mode.upper()}")
    print(f"🤖 LLM: {'Mock' if use_mock else 'Real'}")
    print(f"🏷️  Version: {args.version}")
    print(f"💰 Cost: {'FREE' if use_mock else 'API CHARGES APPLY'}")
    print()
    
    # Warning for real LLM
    if not use_mock:
        print("⚠️  WARNING: Real LLM testing will incur API charges!")
        print("⚠️  Use --mock for cost-free testing.")
        print()
        
        response = input("Continue with real LLM testing? (y/N): ").strip().lower()
        if response not in ('y', 'yes'):
            print("Aborted. Use --mock for cost-free testing.")
            return 1
    
    # Run tests
    try:
        with MockLLMContext(enable_mock=use_mock):
            suite = UnifiedPerformanceSuite(version=args.version, use_mock=use_mock)
            
            if args.mode == "quick":
                results = await suite.run_quick_test()
            elif args.mode == "full":
                results = await suite.run_full_test()
            elif args.mode == "stress":
                results = await suite.run_stress_only(rps=args.rps, duration=args.duration)
            else:
                print(f"❌ Unknown mode: {args.mode}")
                return 1
            
            # Save results
            json_path, md_path = suite.save_results(results, args.output)
            
            # Print summary
            print(f"\n" + "=" * 60)
            print("🎯 PERFORMANCE SUITE COMPLETE")
            print("=" * 60)
            print(f"Overall Score: {results.summary['overall_score']:.1f}%")
            print(f"Grade: {results.summary['grade']}")
            print(f"Status: {results.summary['status']}")
            print(f"Total Duration: {results.total_duration:.1f}s")
            print(f"Tests Completed: {results.tests_completed}")
            print(f"\n📊 Results saved to:")
            print(f"  JSON: {json_path}")
            print(f"  Markdown: {md_path}")
            
            # Exit with appropriate code
            if results.summary['grade'] in ['A', 'B']:
                return 0
            else:
                return 1
        
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user.")
        return 1
        
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))