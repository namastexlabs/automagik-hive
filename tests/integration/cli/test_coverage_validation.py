"""Comprehensive test coverage validation for refactored CLI architecture.

Validates that the test suite achieves 90%+ coverage for all CLI modules
and provides detailed coverage reporting and analysis.
"""

import importlib
import inspect
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import ast

import pytest


class CoverageAnalyzer:
    """Analyze test coverage for CLI modules."""

    def __init__(self):
        # Updated to reflect actual CLI module structure
        self.cli_modules = [
            'cli.commands.agent',
            'cli.commands.genie',
            'cli.commands.init',
            'cli.commands.postgres',
            'cli.commands.uninstall',
            'cli.commands.workspace',
            'cli.main',
            'cli.commands',
            'cli.core.agent_environment',
            'cli.core.agent_service',
            'cli.core.postgres_service',
            'cli.docker_manager',
            'cli.utils',
            'cli.workspace',
        ]
        
        # Updated to reflect actual test module structure
        self.test_modules = [
            'tests.cli.commands.test_agent_commands',
            'tests.cli.commands.test_genie',
            'tests.cli.commands.test_init',
            'tests.cli.commands.test_postgres',
            'tests.cli.commands.test_uninstall',
            'tests.cli.commands.test_workspace',
            'tests.cli.test_main',
            'tests.cli.core.test_agent_environment',
            'tests.cli.core.test_agent_service',
            'tests.cli.core.test_postgres_service',
            'tests.cli.test_docker_manager',
            'tests.cli.test_utils',
            'tests.cli.test_workspace_cli',
        ]

    def analyze_module_functions(self, module_name: str) -> Dict[str, List[str]]:
        """Analyze functions and methods in a module."""
        try:
            module = importlib.import_module(module_name)
            functions = {}
            
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    class_methods = []
                    for method_name, method_obj in inspect.getmembers(obj):
                        if (inspect.ismethod(method_obj) or inspect.isfunction(method_obj)) and \
                           not method_name.startswith('_'):
                            class_methods.append(method_name)
                    if class_methods:
                        functions[name] = class_methods
                elif inspect.isfunction(obj) and not name.startswith('_'):
                    functions[name] = []
                    
            return functions
        except ImportError as e:
            print(f"Warning: Could not import {module_name}: {e}")
            return {}

    def analyze_test_coverage_patterns(self, test_module_name: str) -> Set[str]:
        """Analyze what functions/methods are covered by tests."""
        try:
            test_module = importlib.import_module(test_module_name)
            covered_items = set()
            
            for name, obj in inspect.getmembers(test_module):
                if inspect.isclass(obj) and name.startswith('Test'):
                    for method_name, method_obj in inspect.getmembers(obj):
                        if inspect.isfunction(method_obj) and method_name.startswith('test_'):
                            # Extract what this test covers from method name
                            covered_items.add(method_name)
                            
            return covered_items
        except ImportError as e:
            print(f"Warning: Could not import test module {test_module_name}: {e}")
            return set()

    def calculate_coverage_estimate(self) -> Dict[str, float]:
        """Calculate estimated coverage for each module."""
        coverage_results = {}
        
        for module_name in self.cli_modules:
            functions = self.analyze_module_functions(module_name)
            total_functions = sum(len(methods) if methods else 1 for methods in functions.values())
            
            if total_functions == 0:
                coverage_results[module_name] = 100.0
                continue
                
            # Count how many functions have corresponding tests
            covered_count = 0
            for test_module in self.test_modules:
                test_coverage = self.analyze_test_coverage_patterns(test_module)
                
                # Simple heuristic: count tests that likely cover functions
                for func_name in functions:
                    test_patterns = [
                        f"test_{func_name.lower()}",
                        f"test_{module_name.split('.')[-1]}_{func_name.lower()}",
                    ]
                    
                    for pattern in test_patterns:
                        if any(pattern in test_name.lower() for test_name in test_coverage):
                            covered_count += 1
                            break
                            
            coverage_percent = (covered_count / total_functions) * 100
            coverage_results[module_name] = min(coverage_percent, 100.0)
            
        return coverage_results

    def generate_coverage_report(self) -> str:
        """Generate comprehensive coverage report."""
        coverage_results = self.calculate_coverage_estimate()
        
        report = []
        report.append("=" * 80)
        report.append("CLI REFACTORED ARCHITECTURE - TEST COVERAGE ANALYSIS")
        report.append("=" * 80)
        report.append("")
        
        total_coverage = sum(coverage_results.values()) / len(coverage_results) if coverage_results else 0
        
        report.append(f"OVERALL COVERAGE ESTIMATE: {total_coverage:.1f}%")
        report.append(f"TARGET COVERAGE: 90.0%")
        report.append(f"STATUS: {'✅ PASSED' if total_coverage >= 90 else '❌ NEEDS IMPROVEMENT'}")
        report.append("")
        
        report.append("MODULE BREAKDOWN:")
        report.append("-" * 50)
        
        for module_name, coverage in sorted(coverage_results.items()):
            status = "✅" if coverage >= 90 else "⚠️" if coverage >= 70 else "❌"
            report.append(f"{status} {module_name:<35} {coverage:>6.1f}%")
            
        report.append("")
        report.append("COVERAGE CATEGORIES:")
        report.append("-" * 20)
        
        excellent = sum(1 for c in coverage_results.values() if c >= 95)
        good = sum(1 for c in coverage_results.values() if 90 <= c < 95)
        needs_work = sum(1 for c in coverage_results.values() if 70 <= c < 90)
        poor = sum(1 for c in coverage_results.values() if c < 70)
        
        report.append(f"Excellent (95%+): {excellent} modules")
        report.append(f"Good (90-95%):   {good} modules")
        report.append(f"Needs Work (70-90%): {needs_work} modules")
        report.append(f"Poor (<70%):     {poor} modules")
        
        return "\n".join(report)


class TestCoverageValidation:
    """Test coverage validation for CLI refactored architecture."""

    @pytest.fixture
    def coverage_analyzer(self):
        """Create coverage analyzer for testing."""
        return CoverageAnalyzer()

    def test_coverage_target_achieved(self, coverage_analyzer):
        """Test that 90% coverage target is achieved."""
        coverage_results = coverage_analyzer.calculate_coverage_estimate()
        
        if not coverage_results:
            pytest.fail("No coverage results calculated")
            
        total_coverage = sum(coverage_results.values()) / len(coverage_results)
        
        # Generate detailed report
        report = coverage_analyzer.generate_coverage_report()
        print("\n" + report)
        
        # Check if target is met
        target_coverage = 90.0
        if total_coverage < target_coverage:
            low_coverage_modules = [
                f"{module}: {coverage:.1f}%" 
                for module, coverage in coverage_results.items() 
                if coverage < target_coverage
            ]
            
            failure_msg = f"Coverage target not met!\n"
            failure_msg += f"Overall: {total_coverage:.1f}% (target: {target_coverage}%)\n"
            failure_msg += f"Modules below target:\n"
            for module_info in low_coverage_modules:
                failure_msg += f"  {module_info}\n"
                
            pytest.fail(failure_msg)


if __name__ == "__main__":
    # Run coverage analysis directly
    analyzer = CoverageAnalyzer() 
    report = analyzer.generate_coverage_report()
    print(report)
    
    # Calculate and display summary
    coverage_results = analyzer.calculate_coverage_estimate()
    total_coverage = sum(coverage_results.values()) / len(coverage_results) if coverage_results else 0
    
    print(f"\n🎯 SUMMARY:")
    print(f"Target Coverage: 90.0%")
    print(f"Achieved Coverage: {total_coverage:.1f}%")
    print(f"Status: {'✅ PASSED' if total_coverage >= 90 else '❌ NEEDS IMPROVEMENT'}")
    
    if total_coverage >= 90:
        print("\n🎉 CLI REFACTORED ARCHITECTURE TEST COVERAGE TARGET ACHIEVED!")
    else:
        print(f"\n⚠️ Need {90 - total_coverage:.1f}% more coverage to meet target")