"""CLI Startup Performance Profiler.

This module provides timing analysis for CLI startup performance,
measuring import times and module initialization overhead.
"""

import cProfile
import pstats
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Dict, List, Tuple


class StartupProfiler:
    """Profile CLI startup performance and module loading times."""

    def __init__(self):
        self.import_times: Dict[str, float] = {}
        self.total_time = 0.0
        self.memory_peak = 0
        
    def profile_import_timing(self) -> Dict[str, float]:
        """Profile individual module import times."""
        import_stats = {}
        
        # Time individual imports
        modules_to_time = [
            'argparse',
            'subprocess', 
            'sys',
            'pathlib',
            'cli.commands.init',
            'cli.commands.agent',
            'cli.commands.postgres',
            'cli.commands.workspace',
            'cli.commands.uninstall',
            'lib.utils.version_reader'
        ]
        
        for module in modules_to_time:
            start_time = time.perf_counter()
            try:
                __import__(module)
                end_time = time.perf_counter()
                import_stats[module] = (end_time - start_time) * 1000  # Convert to ms
            except ImportError as e:
                import_stats[module] = f"Import Error: {e}"
                
        return import_stats
    
    def profile_cli_startup(self) -> Tuple[float, Dict[str, any]]:
        """Profile complete CLI startup with memory tracking."""
        tracemalloc.start()
        start_time = time.perf_counter()
        
        # Import the main CLI module to simulate startup
        try:
            from cli.main import create_parser
            
            # Create parser to simulate full initialization
            parser = create_parser()
            
            end_time = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            startup_time = (end_time - start_time) * 1000  # Convert to ms
            
            return startup_time, {
                'memory_current': current / 1024 / 1024,  # MB
                'memory_peak': peak / 1024 / 1024,  # MB
                'parser_created': True
            }
            
        except Exception as e:
            end_time = time.perf_counter()
            tracemalloc.stop()
            startup_time = (end_time - start_time) * 1000
            
            return startup_time, {
                'error': str(e),
                'memory_current': 0,
                'memory_peak': 0,
                'parser_created': False
            }
    
    def run_detailed_profile(self) -> Dict[str, any]:
        """Run comprehensive startup profiling with cProfile."""
        profiler = cProfile.Profile()
        
        # Profile the full startup sequence
        profiler.enable()
        
        try:
            # Simulate CLI startup
            from cli.main import create_parser, main
            parser = create_parser()
            
            # Test argument parsing (simulate help command)
            import sys
            original_argv = sys.argv
            sys.argv = ['automagik-hive', '--help']
            
            try:
                # This will call parser.print_help() and return 0
                result = main()
            except SystemExit:
                # Expected behavior for --help
                pass
            finally:
                sys.argv = original_argv
                
        except Exception as e:
            print(f"Profile error: {e}")
        finally:
            profiler.disable()
        
        # Analyze profiling results
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        
        # Get top time-consuming functions
        top_functions = []
        stats_items = list(stats.stats.items())[:10]
        for func, (cc, nc, tt, ct, callers) in stats_items:
            filename, line, func_name = func
            top_functions.append({
                'function': f"{Path(filename).name}:{line}({func_name})",
                'calls': nc,
                'total_time': tt * 1000,  # Convert to ms
                'cumulative_time': ct * 1000  # Convert to ms
            })
            
        return {
            'total_calls': stats.total_calls,
            'total_time': stats.total_tt * 1000,  # Convert to ms
            'top_functions': top_functions
        }
    
    def benchmark_startup_times(self, iterations: int = 10) -> Dict[str, any]:
        """Benchmark CLI startup multiple times for statistical analysis."""
        startup_times = []
        import_times = []
        memory_peaks = []
        
        for i in range(iterations):
            # Clear module cache to simulate fresh startup
            modules_to_clear = [
                'cli.main', 'cli.commands.init', 'cli.commands.agent',
                'cli.commands.postgres', 'cli.commands.workspace', 
                'cli.commands.uninstall'
            ]
            
            for module in modules_to_clear:
                if module in sys.modules:
                    del sys.modules[module]
            
            # Profile startup
            startup_time, stats = self.profile_cli_startup()
            startup_times.append(startup_time)
            memory_peaks.append(stats.get('memory_peak', 0))
            
            # Profile imports
            import_stats = self.profile_import_timing()
            total_import_time = sum(
                time for time in import_stats.values() 
                if isinstance(time, (int, float))
            )
            import_times.append(total_import_time)
        
        # Calculate statistics
        avg_startup = sum(startup_times) / len(startup_times)
        min_startup = min(startup_times)
        max_startup = max(startup_times)
        
        avg_imports = sum(import_times) / len(import_times)
        avg_memory = sum(memory_peaks) / len(memory_peaks)
        
        return {
            'iterations': iterations,
            'startup_times_ms': {
                'average': avg_startup,
                'minimum': min_startup,
                'maximum': max_startup,
                'all_times': startup_times
            },
            'import_times_ms': {
                'average': avg_imports,
                'all_times': import_times
            },
            'memory_mb': {
                'average_peak': avg_memory,
                'all_peaks': memory_peaks
            }
        }


def run_performance_benchmark():
    """Run complete performance benchmark and display results."""
    print("🚀 CLI Startup Performance Profiler")
    print("=" * 50)
    
    profiler = StartupProfiler()
    
    # 1. Basic import timing
    print("\n📦 Module Import Analysis:")
    import_stats = profiler.profile_import_timing()
    for module, time_ms in import_stats.items():
        if isinstance(time_ms, (int, float)):
            print(f"  {module:25s}: {time_ms:6.2f}ms")
        else:
            print(f"  {module:25s}: {time_ms}")
    
    # 2. Single startup profile
    print("\n⏱️  Single Startup Profile:")
    startup_time, stats = profiler.profile_cli_startup()
    print(f"  Total startup time: {startup_time:.2f}ms")
    print(f"  Memory peak: {stats.get('memory_peak', 0):.2f}MB")
    print(f"  Parser created: {stats.get('parser_created', False)}")
    
    # 3. Statistical benchmark
    print("\n📊 Statistical Benchmark (10 iterations):")
    benchmark_results = profiler.benchmark_startup_times(10)
    startup_stats = benchmark_results['startup_times_ms']
    print(f"  Average startup: {startup_stats['average']:.2f}ms")
    print(f"  Min startup: {startup_stats['minimum']:.2f}ms")
    print(f"  Max startup: {startup_stats['maximum']:.2f}ms")
    print(f"  Average imports: {benchmark_results['import_times_ms']['average']:.2f}ms")
    print(f"  Average memory: {benchmark_results['memory_mb']['average_peak']:.2f}MB")
    
    # 4. Detailed profiling
    print("\n🔍 Detailed Function Analysis:")
    detailed_stats = profiler.run_detailed_profile()
    print(f"  Total calls: {detailed_stats['total_calls']}")
    print(f"  Total time: {detailed_stats['total_time']:.2f}ms")
    print("\n  Top 5 time-consuming functions:")
    for i, func in enumerate(detailed_stats['top_functions'][:5], 1):
        print(f"    {i}. {func['function']}")
        print(f"       Calls: {func['calls']}, Time: {func['total_time']:.2f}ms")
    
    return benchmark_results


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    run_performance_benchmark()