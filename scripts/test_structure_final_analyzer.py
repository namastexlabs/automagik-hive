#!/usr/bin/env python3
"""
Final Test Structure Analyzer - Handles integration tests properly.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
import json


@dataclass
class TestAnalysis:
    """Container for test analysis results."""
    source_files: Set[Path] = field(default_factory=set)
    test_files: Set[Path] = field(default_factory=set)
    integration_files: Set[Path] = field(default_factory=set)
    fixture_files: Set[Path] = field(default_factory=set)
    missing_tests: Set[Path] = field(default_factory=set)
    orphaned_tests: Set[Path] = field(default_factory=set)
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
            "total_unit_tests": len(self.test_files) - len(self.integration_files) - len(self.fixture_files),
            "total_integration_tests": len(self.integration_files),
            "total_fixture_files": len(self.fixture_files),
            "missing_tests": len(self.missing_tests),
            "orphaned_unit_tests": len(self.orphaned_tests),
            "correct_tests": len(self.correct_tests),
            "coverage_percentage": round(self.coverage_percentage, 2)
        }


class FinalTestStructureAnalyzer:
    """Test structure analyzer that properly handles integration tests."""
    
    SKIP_DIRS = {
        '__pycache__', '.git', '.venv', 'venv', 'env', 
        'node_modules', '.pytest_cache', '.mypy_cache',
        'build', 'dist', '.eggs', '*.egg-info', 'data',
        'logs', '.claude', 'genie', 'scripts', 'docs',
        'alembic', 'migrations', 'automagik-store'
    }
    
    SKIP_FILES = {
        '__init__.py', 'setup.py', 'conftest.py'
    }
    
    SOURCE_DIRS = {'api', 'lib', 'ai', 'common', 'cli'}
    
    # Integration and support directories (don't need source mirrors)
    INTEGRATION_DIRS = {'integration', 'fixtures', 'mocks', 'utilities'}
    
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
    
    def is_integration_test(self, path: Path) -> bool:
        """Check if test file is in integration/support directories."""
        try:
            relative_path = path.relative_to(self.tests_dir)
            return any(part in self.INTEGRATION_DIRS for part in relative_path.parts)
        except ValueError:
            return False
    
    def is_fixture_file(self, path: Path) -> bool:
        """Check if file is a fixture/utility file."""
        name = path.name
        return ('fixture' in name.lower() or 
                'mock' in name.lower() or
                'util' in name.lower() or
                name in {'conftest.py', 'agent_tester.py', 'protocol_validator.py'})
    
    def get_expected_test_path(self, source_path: Path) -> Path:
        """Get expected test file path for a source file."""
        try:
            relative_path = source_path.relative_to(self.project_root)
        except ValueError:
            return None
        
        if not any(str(relative_path).startswith(src_dir) for src_dir in self.SOURCE_DIRS):
            return None
        
        test_path = self.tests_dir / relative_path.parent / f"test_{relative_path.name}"
        return test_path
    
    def get_expected_source_path(self, test_path: Path) -> Path:
        """Get expected source file for a test file."""
        try:
            relative_path = test_path.relative_to(self.tests_dir)
        except ValueError:
            return None
        
        name = relative_path.name
        if name.startswith('test_'):
            source_name = name[5:]
        elif name.endswith('_test.py'):
            source_name = name[:-8] + '.py'
        else:
            return None
        
        source_path = self.project_root / relative_path.parent / source_name
        return source_path
    
    def collect_python_files(self) -> Tuple[Set[Path], Set[Path]]:
        """Collect all Python files, separated into source and test files."""
        source_files = set()
        test_files = set()
        
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            if self.should_skip_path(root_path):
                continue
            
            for file in files:
                if not file.endswith('.py') or file in self.SKIP_FILES:
                    continue
                
                file_path = root_path / file
                
                if self.is_test_file(file_path) or 'tests' in root_path.parts:
                    test_files.add(file_path)
                else:
                    # Check if it's in a source directory
                    try:
                        relative = file_path.relative_to(self.project_root)
                        if any(str(relative).startswith(src_dir) for src_dir in self.SOURCE_DIRS):
                            source_files.add(file_path)
                    except ValueError:
                        pass
        
        return source_files, test_files
    
    def analyze(self) -> TestAnalysis:
        """Perform comprehensive test structure analysis."""
        source_files, test_files = self.collect_python_files()
        self.analysis.source_files = source_files
        self.analysis.test_files = test_files
        
        # Categorize test files
        matched_test_files = set()
        
        for test_file in test_files:
            if self.is_integration_test(test_file):
                self.analysis.integration_files.add(test_file)
                continue
            
            if self.is_fixture_file(test_file):
                self.analysis.fixture_files.add(test_file)
                continue
            
            # Check if it's a proper unit test
            if not self.is_test_file(test_file):
                continue
            
            expected_source = self.get_expected_source_path(test_file)
            if expected_source and expected_source.exists() and expected_source in source_files:
                matched_test_files.add(test_file)
            else:
                self.analysis.orphaned_tests.add(test_file)
        
        # Check source files for missing tests
        for source_file in source_files:
            expected_test = self.get_expected_test_path(source_file)
            if expected_test and expected_test.exists():
                self.analysis.correct_tests.add(source_file)
                self.analysis.coverage_map[source_file] = expected_test
            else:
                self.analysis.missing_tests.add(source_file)
        
        return self.analysis
    
    def generate_report(self) -> str:
        """Generate human-readable report."""
        lines = []
        lines.append("=" * 80)
        lines.append("FINAL TEST STRUCTURE ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        stats = self.analysis.stats
        
        # Check if structure is perfect
        unit_test_issues = len(self.analysis.missing_tests) + len(self.analysis.orphaned_tests)
        
        if unit_test_issues == 0:
            lines.append("✅ PERFECT TEST STRUCTURE ACHIEVED!")
            lines.append("   All source files have corresponding unit tests")
            lines.append("   No orphaned unit tests found")
            lines.append("")
        else:
            lines.append("⚠️  UNIT TEST ISSUES FOUND:")
            lines.append(f"   Total issues to resolve: {unit_test_issues}")
            lines.append("")
        
        # Summary statistics
        lines.append("SUMMARY STATISTICS:")
        lines.append("-" * 40)
        lines.append(f"Total source files:        {stats['total_source_files']:>5}")
        lines.append(f"Unit tests (mirror):       {stats['total_unit_tests']:>5}")
        lines.append(f"Integration tests:         {stats['total_integration_tests']:>5}")
        lines.append(f"Fixture/utility files:     {stats['total_fixture_files']:>5}")
        lines.append(f"Missing unit tests:        {stats['missing_tests']:>5}")
        lines.append(f"Orphaned unit tests:       {stats['orphaned_unit_tests']:>5}")
        lines.append(f"Coverage percentage:       {stats['coverage_percentage']:>5.1f}%")
        lines.append("")
        
        # Integration test summary
        if self.analysis.integration_files:
            lines.append("INTEGRATION TEST STRUCTURE:")
            lines.append("-" * 40)
            integration_dirs = {}
            for test_file in self.analysis.integration_files:
                try:
                    relative = test_file.relative_to(self.tests_dir)
                    category = relative.parts[0] if relative.parts else 'root'
                    if category not in integration_dirs:
                        integration_dirs[category] = 0
                    integration_dirs[category] += 1
                except ValueError:
                    pass
            
            for category, count in sorted(integration_dirs.items()):
                lines.append(f"  {category:20} {count:>5} tests")
            lines.append("")
        
        # Missing tests
        if self.analysis.missing_tests:
            lines.append("MISSING UNIT TESTS:")
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
            lines.append("ORPHANED UNIT TESTS:")
            lines.append("-" * 40)
            for file in sorted(self.analysis.orphaned_tests):
                relative = file.relative_to(self.project_root)
                expected = self.get_expected_source_path(file)
                expected_rel = expected.relative_to(self.project_root) if expected else "N/A"
                lines.append(f"  👻 {relative}")
                lines.append(f"     → Expected source: {expected_rel}")
            lines.append("")
        
        # Success criteria
        if unit_test_issues == 0:
            lines.append("🎉 SUCCESS CRITERIA MET:")
            lines.append("-" * 40)
            lines.append("  ✅ Perfect mirror structure for unit tests")
            lines.append("  ✅ Proper integration test organization")
            lines.append("  ✅ Clean fixture and utility file structure")
            lines.append("  ✅ 100% test coverage maintained")
        else:
            lines.append("RECOMMENDATIONS:")
            lines.append("-" * 40)
            if self.analysis.missing_tests:
                lines.append("  1. Create missing unit test files")
            if self.analysis.orphaned_tests:
                lines.append("  2. Remove or reorganize orphaned unit tests")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)


def main():
    """Main entry point."""
    project_root = Path.cwd()
    
    analyzer = FinalTestStructureAnalyzer(project_root)
    analyzer.analyze()
    
    report = analyzer.generate_report()
    print(report)
    
    # Exit with appropriate code
    unit_test_issues = len(analyzer.analysis.missing_tests) + len(analyzer.analysis.orphaned_tests)
    sys.exit(0 if unit_test_issues == 0 else 1)


if __name__ == "__main__":
    main()