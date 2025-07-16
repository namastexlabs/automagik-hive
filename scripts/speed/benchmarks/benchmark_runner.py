#!/usr/bin/env python3
"""
Genie Speed Optimization Framework - Benchmark Runner
Implements minimum runtime benchmarking inspired by Codeflash
"""

import argparse
import importlib.util
import json
import statistics
import sys
import time
import timeit
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import traceback
import ast
import inspect
import cProfile
import pstats
from io import StringIO

# Add project root to path
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))


class BenchmarkRunner:
    """
    Core benchmarking engine implementing minimum runtime measurement
    following Codeflash methodology
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[{level}] {message}")
    
    def parse_target(self, target: str) -> Tuple[str, str]:
        """Parse target into file path and function name"""
        if "::" in target:
            file_path, function_name = target.split("::", 1)
            return file_path, function_name
        else:
            # If no function specified, benchmark the entire module
            return target, None
    
    def load_module(self, file_path: str) -> Any:
        """Dynamically load module from file path"""
        try:
            # Convert relative path to absolute
            abs_path = Path(project_root) / file_path
            if not abs_path.exists():
                raise FileNotFoundError(f"File not found: {abs_path}")
            
            # Load module
            spec = importlib.util.spec_from_file_location("target_module", abs_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return module
        except Exception as e:
            self.log(f"Error loading module {file_path}: {e}", "ERROR")
            raise
    
    def get_function(self, module: Any, function_name: str) -> Any:
        """Get function from module"""
        try:
            return getattr(module, function_name)
        except AttributeError:
            self.log(f"Function {function_name} not found in module", "ERROR")
            raise
    
    def generate_test_inputs(self, func: Any) -> List[Tuple[Any, ...]]]:
        """Generate test inputs for function based on signature"""
        try:
            sig = inspect.signature(func)
            test_inputs = []
            
            # Generate basic test cases
            args = []
            for param_name, param in sig.parameters.items():
                if param.annotation == str:
                    args.append("test_string")
                elif param.annotation == int:
                    args.append(42)
                elif param.annotation == float:
                    args.append(3.14)
                elif param.annotation == bool:
                    args.append(True)
                elif param.annotation == list:
                    args.append([1, 2, 3])
                elif param.annotation == dict:
                    args.append({"key": "value"})
                else:
                    # Default to string for unknown types
                    args.append("default_value")
            
            # Add multiple test cases with different input sizes
            test_inputs.append(tuple(args))
            
            # Generate edge cases
            if len(args) > 0:
                # Empty/minimal inputs
                edge_args = []
                for arg in args:
                    if isinstance(arg, str):
                        edge_args.append("")
                    elif isinstance(arg, (int, float)):
                        edge_args.append(0)
                    elif isinstance(arg, list):
                        edge_args.append([])
                    elif isinstance(arg, dict):
                        edge_args.append({})
                    else:
                        edge_args.append(arg)
                test_inputs.append(tuple(edge_args))
                
                # Large inputs
                large_args = []
                for arg in args:
                    if isinstance(arg, str):
                        large_args.append("x" * 1000)
                    elif isinstance(arg, int):
                        large_args.append(10000)
                    elif isinstance(arg, float):
                        large_args.append(9999.99)
                    elif isinstance(arg, list):
                        large_args.append(list(range(100)))
                    elif isinstance(arg, dict):
                        large_args.append({f"key_{i}": f"value_{i}" for i in range(50)})
                    else:
                        large_args.append(arg)
                test_inputs.append(tuple(large_args))
            
            return test_inputs if test_inputs else [()]
            
        except Exception as e:
            self.log(f"Error generating test inputs: {e}", "WARNING")
            return [()]  # Return empty tuple as fallback
    
    def profile_function(self, func: Any, test_inputs: List[Tuple[Any, ...]]) -> Dict[str, Any]:
        """Profile function to identify bottlenecks"""
        profiler = cProfile.Profile()
        
        try:
            # Run function with profiling
            profiler.enable()
            for inputs in test_inputs:
                func(*inputs)
            profiler.disable()
            
            # Analyze results
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            
            # Capture profile output
            output = StringIO()
            stats.print_stats(20)  # Top 20 functions
            profile_output = output.getvalue()
            
            return {
                "total_calls": stats.total_calls,
                "total_time": stats.total_tt,
                "profile_output": profile_output
            }
            
        except Exception as e:
            self.log(f"Error profiling function: {e}", "WARNING")
            return {}
    
    def measure_minimum_runtime(self, func: Any, test_inputs: List[Tuple[Any, ...]], 
                               runs: int = 50, timeout: int = 300) -> Dict[str, Any]:
        """
        Measure minimum runtime using Codeflash methodology
        
        For each input, run multiple times and take minimum.
        Sum minimums across all inputs for total runtime.
        """
        self.log(f"Measuring minimum runtime with {runs} runs, timeout {timeout}s")
        
        min_input_runtimes = []
        individual_results = []
        
        start_time = time.time()
        
        for input_idx, inputs in enumerate(test_inputs):
            self.log(f"Testing input {input_idx + 1}/{len(test_inputs)}: {inputs}")
            
            min_runtime = float('inf')
            runtimes = []
            
            for run in range(runs):
                # Check timeout
                if time.time() - start_time > timeout:
                    self.log(f"Timeout reached, stopping at run {run}", "WARNING")
                    break
                
                try:
                    # Measure single execution
                    runtime = timeit.timeit(
                        lambda: func(*inputs),
                        number=1
                    )
                    
                    runtimes.append(runtime)
                    
                    # Update minimum
                    if runtime < min_runtime:
                        min_runtime = runtime
                        
                except Exception as e:
                    self.log(f"Error in run {run} for input {input_idx}: {e}", "WARNING")
                    continue
            
            if runtimes:
                min_input_runtimes.append(min_runtime)
                individual_results.append({
                    "input_index": input_idx,
                    "input": str(inputs),
                    "min_runtime": min_runtime,
                    "avg_runtime": statistics.mean(runtimes),
                    "median_runtime": statistics.median(runtimes),
                    "std_runtime": statistics.stdev(runtimes) if len(runtimes) > 1 else 0,
                    "runs_completed": len(runtimes)
                })
            else:
                self.log(f"No successful runs for input {input_idx}", "WARNING")
        
        # Calculate total runtime as sum of minimums
        total_runtime = sum(min_input_runtimes) if min_input_runtimes else 0
        
        return {
            "total_runtime": total_runtime,
            "total_runs": len(test_inputs) * runs,
            "successful_inputs": len(min_input_runtimes),
            "individual_results": individual_results,
            "measurement_time": time.time() - start_time
        }
    
    def benchmark_function(self, file_path: str, function_name: str, 
                          runs: int = 50, timeout: int = 300) -> Dict[str, Any]:
        """Benchmark a specific function"""
        self.log(f"Benchmarking function: {file_path}::{function_name}")
        
        try:
            # Load module and function
            module = self.load_module(file_path)
            func = self.get_function(module, function_name)
            
            # Generate test inputs
            test_inputs = self.generate_test_inputs(func)
            self.log(f"Generated {len(test_inputs)} test input sets")
            
            # Profile function
            profile_data = self.profile_function(func, test_inputs)
            
            # Measure runtime
            runtime_data = self.measure_minimum_runtime(func, test_inputs, runs, timeout)
            
            return {
                "target": f"{file_path}::{function_name}",
                "type": "function",
                "timestamp": time.time(),
                "runtime_data": runtime_data,
                "profile_data": profile_data,
                "test_inputs_count": len(test_inputs),
                "function_signature": str(inspect.signature(func))
            }
            
        except Exception as e:
            self.log(f"Error benchmarking function: {e}", "ERROR")
            traceback.print_exc()
            return {
                "target": f"{file_path}::{function_name}",
                "type": "function",
                "timestamp": time.time(),
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def find_functions_in_module(self, module: Any) -> List[str]:
        """Find all functions in a module"""
        functions = []
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and obj.__module__ == module.__name__:
                functions.append(name)
        return functions
    
    def benchmark_module(self, file_path: str, runs: int = 50, timeout: int = 300) -> Dict[str, Any]:
        """Benchmark all functions in a module"""
        self.log(f"Benchmarking module: {file_path}")
        
        try:
            # Load module
            module = self.load_module(file_path)
            
            # Find all functions
            functions = self.find_functions_in_module(module)
            self.log(f"Found {len(functions)} functions in module")
            
            # Benchmark each function
            function_results = {}
            for func_name in functions:
                try:
                    func_result = self.benchmark_function(file_path, func_name, runs, timeout)
                    function_results[func_name] = func_result
                except Exception as e:
                    self.log(f"Error benchmarking function {func_name}: {e}", "WARNING")
                    function_results[func_name] = {
                        "error": str(e),
                        "timestamp": time.time()
                    }
            
            return {
                "target": file_path,
                "type": "module",
                "timestamp": time.time(),
                "functions_benchmarked": len(functions),
                "function_results": function_results
            }
            
        except Exception as e:
            self.log(f"Error benchmarking module: {e}", "ERROR")
            traceback.print_exc()
            return {
                "target": file_path,
                "type": "module",
                "timestamp": time.time(),
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def benchmark_target(self, target: str, runs: int = 50, timeout: int = 300) -> Dict[str, Any]:
        """Benchmark a target (function or module)"""
        file_path, function_name = self.parse_target(target)
        
        if function_name:
            return self.benchmark_function(file_path, function_name, runs, timeout)
        else:
            return self.benchmark_module(file_path, runs, timeout)
    
    def save_results(self, results: Dict[str, Any], output_file: str):
        """Save benchmark results to file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.log(f"Results saved to: {output_file}")
        except Exception as e:
            self.log(f"Error saving results: {e}", "ERROR")
            raise


def main():
    parser = argparse.ArgumentParser(description="Genie Speed Optimization - Benchmark Runner")
    parser.add_argument("--target", required=True, help="Target to benchmark (file::function or file)")
    parser.add_argument("--runs", type=int, default=50, help="Number of benchmark runs")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--output", required=True, help="Output file for results")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Create benchmark runner
    runner = BenchmarkRunner(verbose=args.verbose)
    
    # Run benchmarks
    results = runner.benchmark_target(args.target, args.runs, args.timeout)
    
    # Save results
    runner.save_results(results, args.output)
    
    # Print summary
    if "error" in results:
        print(f"❌ Benchmarking failed: {results['error']}")
        sys.exit(1)
    else:
        if results["type"] == "function":
            runtime_data = results.get("runtime_data", {})
            total_runtime = runtime_data.get("total_runtime", 0)
            successful_inputs = runtime_data.get("successful_inputs", 0)
            
            print(f"✅ Benchmarking completed successfully")
            print(f"📊 Total runtime: {total_runtime:.6f} seconds")
            print(f"🔍 Successful inputs: {successful_inputs}")
            print(f"📁 Results saved to: {args.output}")
        else:
            functions_benchmarked = results.get("functions_benchmarked", 0)
            print(f"✅ Module benchmarking completed")
            print(f"🔍 Functions benchmarked: {functions_benchmarked}")
            print(f"📁 Results saved to: {args.output}")


if __name__ == "__main__":
    main()