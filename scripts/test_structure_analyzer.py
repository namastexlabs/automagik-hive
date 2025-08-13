#!/usr/bin/env python3
"""
Test Structure Analyzer - Comprehensive test coverage and structure validation.

This script analyzes the codebase to ensure proper test coverage following the mirror structure:
- Each .py file should have a corresponding test file in tests/ directory
- Test files should mirror the source structure
- Identifies missing tests, misplaced tests, and orphaned tests
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import json


@dataclass
class TestAnalysis:
    """Container for test analysis results."""
    source_files: Set[Path] = field(default_factory=set)
    test_files: Set[Path] = field(default_factory=set)
    missing_tests: Set[Path] = field(default_factory=set)
    orphaned_tests: Set[Path] = field(default_factory=set)
    misplaced_tests: Set[Path] = field(default_factory=set)
    correct_tests: Set[Path] = field(default_factory=set)
    coverage_map: Dict[Path, Path] = field(default_factory=dict)
    
    @property
    def coverage_percentage(self) -> float:
        if not self.source_files:
            return 100.0
        return (len(self.correct_tests) / len(self.source_files)) * 100
    
    @property
    def stats(self) -> Dict:
        return {
            "total_source_files": len(self.source_files),
            "total_test_files": len(self.test_files),
            "missing_tests": len(self.missing_tests),
            "orphaned_tests": len(self.orphaned_tests),
            "misplaced_tests": len(self.misplaced_tests),
            "correct_tests": len(self.correct_tests),
            "coverage_percentage": round(self.coverage_percentage, 2)
        }


class TestStructureAnalyzer:
    """Analyzes test structure and coverage."""
    
    # Directories to skip
    SKIP_DIRS = {
        '__pycache__', '.git', '.venv', 'venv', 'env', 
        'node_modules', '.pytest_cache', '.mypy_cache',
        'build', 'dist', '.eggs', '*.egg-info', 'data',
        'logs', '.claude', 'genie', 'scripts', 'docs',
        'alembic', 'migrations', 'automagik-store'
    }
    
    # Files to skip
    SKIP_FILES = {
        '__init__.py', 'setup.py', 'conftest.py',
        'test_*.py', '*_test.py'  # Skip test files when looking at source
    }
    
    # Source directories that should have tests
    SOURCE_DIRS = {'api', 'lib', 'ai', 'common', 'cli'}
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / 'tests'
        self.analysis = TestAnalysis()
    
    def should_skip_path(self, path: Path) -> bool:
        """Check if path should be skipped."""
        parts = path.parts
        return any(
            skip_dir in parts or 
            any(part.endswith(skip_dir.replace('*', '')) for part in parts)
            for skip_dir in self.SKIP_DIRS
        )
    
    def is_test_file(self, path: Path) -> bool:
        """Check if file is a test file."""
        name = path.name
        return name.startswith('test_') or name.endswith('_test.py')
    
    def get_expected_test_path(self, source_path: Path) -> Path:
        """Get expected test file path for a source file."""
        # Get relative path from project root
        try:
            relative_path = source_path.relative_to(self.project_root)
        except ValueError:
            return None
        
        # Skip if not in a source directory we care about
        if not any(str(relative_path).startswith(src_dir) for src_dir in self.SOURCE_DIRS):
            return None
        
        # Build expected test path
        test_path = self.tests_dir / relative_path.parent / f"test_{relative_path.name}"
        return test_path
    
    def get_expected_source_path(self, test_path: Path) -> Path:
        """Get expected source file for a test file."""
        # Get relative path from tests directory
        try:
            relative_path = test_path.relative_to(self.tests_dir)
        except ValueError:
            return None
        
        # Remove test_ prefix or _test suffix
        name = relative_path.name
        if name.startswith('test_'):
            source_name = name[5:]
        elif name.endswith('_test.py'):
            source_name = name[:-8] + '.py'
        else:
            return None
        
        # Build expected source path
        source_path = self.project_root / relative_path.parent / source_name
        return source_path
    
    def collect_python_files(self) -> Tuple[Set[Path], Set[Path]]:
        """Collect all Python files, separated into source and test files."""
        source_files = set()
        test_files = set()
        
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            
            # Skip directories
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            if self.should_skip_path(root_path):
                continue
            
            for file in files:
                if not file.endswith('.py'):
                    continue
                
                file_path = root_path / file
                
                # Skip __init__.py and setup files
                if file in {'__init__.py', 'setup.py', 'conftest.py'}:
                    continue
                
                # Categorize as test or source
                if self.is_test_file(file_path):
                    test_files.add(file_path)
                elif 'tests' in root_path.parts:
                    # File in tests directory but not a test file
                    test_files.add(file_path)
                else:
                    # Check if it's in a source directory we care about
                    relative = file_path.relative_to(self.project_root)
                    if any(str(relative).startswith(src_dir) for src_dir in self.SOURCE_DIRS):
                        source_files.add(file_path)
        
        return source_files, test_files
    
    def analyze(self) -> TestAnalysis:
        """Perform comprehensive test structure analysis."""
        # Collect files
        source_files, test_files = self.collect_python_files()
        self.analysis.source_files = source_files
        self.analysis.test_files = test_files
        
        # Track which test files are matched
        matched_test_files = set()
        
        # Analyze source files for missing tests
        for source_file in source_files:
            expected_test = self.get_expected_test_path(source_file)
            if expected_test:
                if expected_test.exists():
                    self.analysis.correct_tests.add(source_file)
                    self.analysis.coverage_map[source_file] = expected_test
                    matched_test_files.add(expected_test)
                else:
                    self.analysis.missing_tests.add(source_file)
        
        # Analyze test files for orphans and misplaced
        for test_file in test_files:
            if not self.is_test_file(test_file):
                continue
            
            # If this test was already matched to a source file, skip it
            if test_file in matched_test_files:
                continue
            
            # Skip integration tests, fixtures, and utilities from orphaned analysis
            test_rel_path = test_file.relative_to(self.project_root)
            if any(skip_dir in test_rel_path.parts for skip_dir in ['integration', 'fixtures']):
                continue
            
            # Skip utility files that aren't actually tests
            if any(skip_name in test_file.name for skip_name in ['conftest.py', 'fixture', 'util', '_helper']):
                continue
                
            expected_source = self.get_expected_source_path(test_file)
            if expected_source:
                if not expected_source.exists():
                    # Test file exists but source doesn't
                    self.analysis.orphaned_tests.add(test_file)
                elif expected_source not in source_files:
                    # Source exists but not in tracked directories
                    # This could mean the test is for a file we're not tracking
                    self.analysis.misplaced_tests.add(test_file)
            else:
                # Can't determine expected source - likely a misnamed or special test
                self.analysis.orphaned_tests.add(test_file)
        
        return self.analysis
    
    def generate_report(self, format: str = 'text') -> str:
        """Generate analysis report."""
        if format == 'json':
            return self._generate_json_report()
        else:
            return self._generate_text_report()
    
    def _generate_text_report(self) -> str:
        """Generate human-readable text report."""
        lines = []
        lines.append("=" * 80)
        lines.append("TEST STRUCTURE ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary statistics
        stats = self.analysis.stats
        lines.append("SUMMARY STATISTICS:")
        lines.append("-" * 40)
        lines.append(f"Total source files:     {stats['total_source_files']:>5}")
        lines.append(f"Total test files:       {stats['total_test_files']:>5}")
        lines.append(f"Files with tests:       {stats['correct_tests']:>5}")
        lines.append(f"Missing tests:          {stats['missing_tests']:>5}")
        lines.append(f"Orphaned tests:         {stats['orphaned_tests']:>5}")
        lines.append(f"Misplaced tests:        {stats['misplaced_tests']:>5}")
        lines.append(f"Coverage:               {stats['coverage_percentage']:>5.1f}%")
        lines.append("")
        
        # Missing tests
        if self.analysis.missing_tests:
            lines.append("MISSING TESTS (source files without tests):")
            lines.append("-" * 40)
            for file in sorted(self.analysis.missing_tests):
                relative = file.relative_to(self.project_root)
                expected = self.get_expected_test_path(file)
                expected_rel = expected.relative_to(self.project_root) if expected else "N/A"
                lines.append(f"  ❌ {relative}")
                lines.append(f"     → Expected: {expected_rel}")
            lines.append("")
        
        # Orphaned tests
        if self.analysis.orphaned_tests:
            lines.append("ORPHANED TESTS (tests without source files):")
            lines.append("-" * 40)
            for file in sorted(self.analysis.orphaned_tests):
                relative = file.relative_to(self.project_root)
                expected = self.get_expected_source_path(file)
                expected_rel = expected.relative_to(self.project_root) if expected else "N/A"
                lines.append(f"  👻 {relative}")
                lines.append(f"     → Expected source: {expected_rel}")
            lines.append("")
        
        # Misplaced tests
        if self.analysis.misplaced_tests:
            lines.append("MISPLACED TESTS (tests in wrong location):")
            lines.append("-" * 40)
            for file in sorted(self.analysis.misplaced_tests):
                relative = file.relative_to(self.project_root)
                lines.append(f"  📍 {relative}")
            lines.append("")
        
        # Correct tests (brief summary)
        if self.analysis.correct_tests:
            lines.append("CORRECTLY STRUCTURED TESTS:")
            lines.append("-" * 40)
            lines.append(f"  ✅ {len(self.analysis.correct_tests)} source files have proper test coverage")
            lines.append("")
        
        # Recommendations
        lines.append("RECOMMENDATIONS:")
        lines.append("-" * 40)
        if self.analysis.missing_tests:
            lines.append("  1. Create missing test files following the mirror structure")
            lines.append("     Example: ai/agents/registry.py → tests/ai/agents/test_registry.py")
        if self.analysis.orphaned_tests:
            lines.append("  2. Review and remove orphaned test files or restore their source files")
        if self.analysis.misplaced_tests:
            lines.append("  3. Move misplaced test files to proper locations")
        if stats['coverage_percentage'] < 80:
            lines.append(f"  4. Improve test coverage to at least 80% (currently {stats['coverage_percentage']}%)")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _generate_json_report(self) -> str:
        """Generate JSON report."""
        report = {
            "stats": self.analysis.stats,
            "missing_tests": [str(f.relative_to(self.project_root)) for f in self.analysis.missing_tests],
            "orphaned_tests": [str(f.relative_to(self.project_root)) for f in self.analysis.orphaned_tests],
            "misplaced_tests": [str(f.relative_to(self.project_root)) for f in self.analysis.misplaced_tests],
            "correct_tests": [str(f.relative_to(self.project_root)) for f in self.analysis.correct_tests],
            "coverage_map": {
                str(k.relative_to(self.project_root)): str(v.relative_to(self.project_root))
                for k, v in self.analysis.coverage_map.items()
            }
        }
        return json.dumps(report, indent=2)


def main():
    """Main entry point."""
    # Determine project root
    project_root = Path.cwd()
    
    # Parse arguments
    format = 'text'
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--json', '-j']:
            format = 'json'
        elif sys.argv[1] in ['--help', '-h']:
            print("Usage: python test_structure_analyzer.py [--json|-j]")
            print("  Analyzes test structure and coverage")
            print("  --json, -j: Output in JSON format")
            sys.exit(0)
    
    # Create analyzer and run analysis
    analyzer = TestStructureAnalyzer(project_root)
    analyzer.analyze()
    
    # Generate and print report
    report = analyzer.generate_report(format=format)
    print(report)
    
    # Exit with error code if coverage is poor
    if analyzer.analysis.stats['coverage_percentage'] < 50:
        sys.exit(1)


if __name__ == "__main__":
    main()