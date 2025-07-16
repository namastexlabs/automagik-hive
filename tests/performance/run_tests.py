#!/usr/bin/env python3
"""
🚀 Simple Test Runner for Genie Agents Performance Suite
Quick access to all performance testing functionality.
"""

import subprocess
import sys
import os
from pathlib import Path

def print_banner():
    """Print banner."""
    print("🚀 Genie Agents Performance Test Runner")
    print("=" * 50)

def run_quick_test():
    """Run quick performance test."""
    print("⚡ Running Quick Performance Test...")
    result = subprocess.run([
        sys.executable, "run_performance_suite.py", "quick"
    ], cwd=Path(__file__).parent)
    return result.returncode

def run_full_test():
    """Run full performance test."""
    print("🏃 Running Full Performance Test...")
    result = subprocess.run([
        sys.executable, "run_performance_suite.py", "full"
    ], cwd=Path(__file__).parent)
    return result.returncode

def run_stress_test():
    """Run stress test."""
    print("🔥 Running Stress Test...")
    result = subprocess.run([
        sys.executable, "run_performance_suite.py", "stress"
    ], cwd=Path(__file__).parent)
    return result.returncode

def run_pytest_tests():
    """Run pytest performance tests."""
    print("🧪 Running Pytest Performance Tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", "-v", 
        "test_benchmark.py", "test_stress.py"
    ], cwd=Path(__file__).parent)
    return result.returncode

def show_help():
    """Show help information."""
    print("""
🎯 USAGE:
  python run_tests.py [COMMAND]

📋 COMMANDS:
  quick      ⚡ Quick performance test (default, ~30s)
  full       🏃 Full performance test (~5min)
  stress     🔥 Stress test (~2min)
  pytest     🧪 Run pytest performance tests
  help       ❓ Show this help message

🚀 EXAMPLES:
  python run_tests.py quick      # Fast development testing
  python run_tests.py full       # Comprehensive validation
  python run_tests.py stress     # Load testing
  python run_tests.py pytest     # Integration with pytest

💡 TIPS:
  • Use 'quick' for daily development testing
  • Use 'full' before releases
  • Use 'stress' to find system limits
  • All tests use mock LLM by default (fast & free)
  • Results are saved in data/ directory
""")

def main():
    """Main entry point."""
    print_banner()
    
    # Get command from arguments
    command = sys.argv[1] if len(sys.argv) > 1 else "quick"
    
    # Execute command
    if command == "quick":
        return run_quick_test()
    elif command == "full":
        return run_full_test()
    elif command == "stress":
        return run_stress_test()
    elif command == "pytest":
        return run_pytest_tests()
    elif command == "help":
        show_help()
        return 0
    else:
        print(f"❌ Unknown command: {command}")
        print("💡 Use 'python run_tests.py help' for available commands")
        return 1

if __name__ == "__main__":
    sys.exit(main())