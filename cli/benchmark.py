#!/usr/bin/env python3
"""CLI Performance Benchmark Suite.

A permanent benchmarking tool for monitoring CLI startup performance
and ensuring optimization improvements are maintained over time.
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from cli.profiler import StartupProfiler


class BenchmarkSuite:
    """Comprehensive CLI performance benchmark suite."""

    def __init__(self, results_dir: Optional[Path] = None):
        self.results_dir = results_dir or Path("cli/benchmark_results")
        self.results_dir.mkdir(exist_ok=True)
        self.profiler = StartupProfiler()
        
    def run_benchmark(self, iterations: int = 10, save_results: bool = True) -> Dict:
        """Run comprehensive performance benchmark."""
        timestamp = datetime.now().isoformat()
        
        print(f"🚀 CLI Performance Benchmark Suite")
        print(f"⏰ Started: {timestamp}")
        print(f"🔄 Iterations: {iterations}")
        print("=" * 60)
        
        # Run benchmark suite
        results = self.profiler.benchmark_startup_times(iterations)
        
        # Add metadata
        results.update({
            'timestamp': timestamp,
            'benchmark_version': '1.0.0',
            'python_version': sys.version,
            'iterations': iterations
        })
        
        # Display results
        self._display_results(results)
        
        # Save results if requested
        if save_results:
            self._save_results(results, timestamp)
            
        return results
    
    def _display_results(self, results: Dict):
        """Display benchmark results in a formatted way."""
        startup_stats = results['startup_times_ms']
        import_stats = results['import_times_ms']
        memory_stats = results['memory_mb']
        
        print(f"\n📊 PERFORMANCE BENCHMARK RESULTS")
        print("=" * 60)
        
        print(f"\n⚡ STARTUP PERFORMANCE:")
        print(f"  Average: {startup_stats['average']:.2f}ms")
        print(f"  Minimum: {startup_stats['minimum']:.2f}ms") 
        print(f"  Maximum: {startup_stats['maximum']:.2f}ms")
        print(f"  Range:   {startup_stats['maximum'] - startup_stats['minimum']:.2f}ms")
        
        print(f"\n📦 IMPORT PERFORMANCE:")
        print(f"  Average: {import_stats['average']:.2f}ms")
        
        print(f"\n💾 MEMORY USAGE:")
        print(f"  Peak Average: {memory_stats['average_peak']:.2f}MB")
        
        print(f"\n🎯 PERFORMANCE CLASSIFICATION:")
        avg_startup = startup_stats['average']
        if avg_startup < 5.0:
            grade = "🟢 EXCELLENT"
        elif avg_startup < 10.0:
            grade = "🟡 GOOD"
        elif avg_startup < 20.0:
            grade = "🟠 ACCEPTABLE"
        else:
            grade = "🔴 NEEDS IMPROVEMENT"
            
        print(f"  Startup Grade: {grade} ({avg_startup:.2f}ms)")
        
    def _save_results(self, results: Dict, timestamp: str):
        """Save benchmark results to JSON file."""
        safe_timestamp = timestamp.replace(":", "-").replace(".", "-")
        filename = f"benchmark_{safe_timestamp}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"\n💾 Results saved to: {filepath}")
        
    def compare_with_baseline(self, baseline_file: Optional[Path] = None) -> Dict:
        """Compare current performance with baseline."""
        if baseline_file is None:
            # Find most recent baseline
            baseline_files = list(self.results_dir.glob("benchmark_*.json"))
            if not baseline_files:
                print("❌ No baseline found. Run benchmark first to establish baseline.")
                return {}
            baseline_file = max(baseline_files, key=lambda p: p.stat().st_mtime)
        
        print(f"📈 Comparing with baseline: {baseline_file.name}")
        
        # Load baseline
        with open(baseline_file) as f:
            baseline = json.load(f)
            
        # Run current benchmark
        current = self.run_benchmark(save_results=False)
        
        # Compare results
        comparison = self._calculate_comparison(baseline, current)
        self._display_comparison(comparison)
        
        return comparison
    
    def _calculate_comparison(self, baseline: Dict, current: Dict) -> Dict:
        """Calculate performance comparison metrics."""
        baseline_startup = baseline['startup_times_ms']['average']
        current_startup = current['startup_times_ms']['average']
        
        baseline_memory = baseline['memory_mb']['average_peak']
        current_memory = current['memory_mb']['average_peak']
        
        startup_change = ((current_startup - baseline_startup) / baseline_startup) * 100
        memory_change = ((current_memory - baseline_memory) / baseline_memory) * 100
        
        return {
            'baseline_startup_ms': baseline_startup,
            'current_startup_ms': current_startup,
            'startup_change_percent': startup_change,
            'baseline_memory_mb': baseline_memory,
            'current_memory_mb': current_memory,
            'memory_change_percent': memory_change,
            'baseline_timestamp': baseline['timestamp'],
            'current_timestamp': current['timestamp']
        }
    
    def _display_comparison(self, comparison: Dict):
        """Display performance comparison results."""
        print(f"\n📊 PERFORMANCE COMPARISON")
        print("=" * 60)
        
        startup_change = comparison['startup_change_percent']
        memory_change = comparison['memory_change_percent']
        
        # Startup comparison
        if startup_change < -5:
            startup_status = f"🟢 IMPROVED by {abs(startup_change):.1f}%"
        elif startup_change > 5:
            startup_status = f"🔴 REGRESSED by {startup_change:.1f}%"
        else:
            startup_status = f"🟡 STABLE ({startup_change:+.1f}%)"
            
        # Memory comparison
        if memory_change < -5:
            memory_status = f"🟢 IMPROVED by {abs(memory_change):.1f}%"
        elif memory_change > 5:
            memory_status = f"🔴 REGRESSED by {memory_change:.1f}%"
        else:
            memory_status = f"🟡 STABLE ({memory_change:+.1f}%)"
        
        print(f"\n⚡ STARTUP PERFORMANCE:")
        print(f"  Baseline: {comparison['baseline_startup_ms']:.2f}ms")
        print(f"  Current:  {comparison['current_startup_ms']:.2f}ms")
        print(f"  Status:   {startup_status}")
        
        print(f"\n💾 MEMORY USAGE:")
        print(f"  Baseline: {comparison['baseline_memory_mb']:.2f}MB")
        print(f"  Current:  {comparison['current_memory_mb']:.2f}MB")
        print(f"  Status:   {memory_status}")
        
    def regression_test(self, threshold_ms: float = 10.0) -> bool:
        """Test for performance regression."""
        print(f"🧪 Running Performance Regression Test")
        print(f"⚠️  Failure Threshold: {threshold_ms}ms average startup")
        print("=" * 60)
        
        results = self.run_benchmark(iterations=5, save_results=False)
        avg_startup = results['startup_times_ms']['average']
        
        if avg_startup <= threshold_ms:
            print(f"✅ REGRESSION TEST PASSED: {avg_startup:.2f}ms ≤ {threshold_ms}ms")
            return True
        else:
            print(f"❌ REGRESSION TEST FAILED: {avg_startup:.2f}ms > {threshold_ms}ms")
            return False


def main():
    """Main CLI interface for benchmark suite."""
    parser = argparse.ArgumentParser(
        description="CLI Performance Benchmark Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli/benchmark.py                    # Run standard benchmark
  python cli/benchmark.py --iterations 20   # Run with more iterations
  python cli/benchmark.py --compare          # Compare with baseline
  python cli/benchmark.py --regression      # Run regression test
        """
    )
    
    parser.add_argument(
        '--iterations', '-i', 
        type=int, 
        default=10,
        help='Number of benchmark iterations (default: 10)'
    )
    
    parser.add_argument(
        '--compare', '-c',
        action='store_true',
        help='Compare current performance with baseline'
    )
    
    parser.add_argument(
        '--regression', '-r',
        action='store_true',
        help='Run performance regression test'
    )
    
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=10.0,
        help='Regression test threshold in milliseconds (default: 10.0)'
    )
    
    args = parser.parse_args()
    
    benchmark = BenchmarkSuite()
    
    try:
        if args.regression:
            success = benchmark.regression_test(args.threshold)
            sys.exit(0 if success else 1)
        elif args.compare:
            benchmark.compare_with_baseline()
        else:
            benchmark.run_benchmark(args.iterations)
            
    except KeyboardInterrupt:
        print("\n⏹️  Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()