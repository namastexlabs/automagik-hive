#!/usr/bin/env python3
"""
Unified Test Structure Analyzer - Comprehensive test coverage and structure validation.

This script provides a complete analysis of test structure and coverage, combining:
- Comprehensive test coverage analysis 
- Detailed breakdown by directory and component
- Missing test identification with exact expected paths
- Orphaned test detection (tests without corresponding source files)
- Misplaced test identification with reorganization recommendations
- Actionable file operation commands for autonomous reorganization
- Multiple output formats (text, JSON, file operations)
- Perfect mirror structure validation with zero-issue success criteria

Usage:
    python test_structure_unified_analyzer.py [--json|-j] [--ops|-o] [--help|-h]
    
    --json, -j: Output analysis in JSON format
    --ops, -o:  Output file operation commands for reorganization
    --help, -h: Show this help message
    
Success Criteria:
    Zero issues reported = Perfect mirror structure achieved
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json


@dataclass
class TestIssue:
    """Container for a specific test structure issue."""
    issue_type: str  # 'missing', 'orphaned', 'misplaced', 'naming'
    current_path: Optional[Path] = None
    expected_path: Optional[Path] = None
    source_path: Optional[Path] = None
    severity: str = 'medium'  # 'low', 'medium', 'high', 'critical'
    description: str = ''
    recommendation: str = ''
    file_operation: str = ''  # Specific command to fix the issue


@dataclass
class TestAnalysis:
    """Container for comprehensive test analysis results."""
    source_files: Set[Path] = field(default_factory=set)
    test_files: Set[Path] = field(default_factory=set)
    issues: List[TestIssue] = field(default_factory=list)
    coverage_map: Dict[Path, Path] = field(default_factory=dict)
    directory_stats: Dict[str, Dict] = field(default_factory=dict)
    
    @property
    def missing_tests(self) -> List[TestIssue]:
        return [issue for issue in self.issues if issue.issue_type == 'missing']
    
    @property
    def orphaned_tests(self) -> List[TestIssue]:
        return [issue for issue in self.issues if issue.issue_type == 'orphaned']
    
    @property
    def integration_tests(self) -> List[TestIssue]:
        """Integration tests that don't need source mirrors (severity='info')."""
        return [issue for issue in self.orphaned_tests if issue.severity == 'info']
    
    @property
    def true_orphaned_tests(self) -> List[TestIssue]:
        """Actually orphaned tests that might need removal (severity='low')."""
        return [issue for issue in self.orphaned_tests if issue.severity == 'low']
    
    @property
    def misplaced_tests(self) -> List[TestIssue]:
        return [issue for issue in self.issues if issue.issue_type == 'misplaced']
    
    @property
    def naming_issues(self) -> List[TestIssue]:
        return [issue for issue in self.issues if issue.issue_type == 'naming']
    
    @property
    def coverage_percentage(self) -> float:
        if not self.source_files:
            return 100.0
        covered_files = len(self.coverage_map)
        return (covered_files / len(self.source_files)) * 100
    
    @property
    def total_issues(self) -> int:
        return len(self.issues)
    
    @property
    def is_perfect_structure(self) -> bool:
        """True if zero issues found - perfect mirror structure achieved."""
        return self.total_issues == 0
    
    @property
    def stats(self) -> Dict:
        return {
            "total_source_files": len(self.source_files),
            "total_test_files": len(self.test_files),
            "covered_source_files": len(self.coverage_map),
            "missing_tests": len(self.missing_tests),
            "orphaned_tests": len(self.orphaned_tests),
            "integration_tests": len(self.integration_tests),
            "true_orphaned_tests": len(self.true_orphaned_tests),
            "misplaced_tests": len(self.misplaced_tests),
            "naming_issues": len(self.naming_issues),
            "total_issues": self.total_issues,
            "coverage_percentage": round(self.coverage_percentage, 2),
            "is_perfect_structure": self.is_perfect_structure
        }


class UnifiedTestStructureAnalyzer:
    """Comprehensive test structure analyzer with autonomous reorganization capabilities."""
    
    # Directories to skip during analysis
    SKIP_DIRS = {
        '__pycache__', '.git', '.venv', 'venv', 'env', 
        'node_modules', '.pytest_cache', '.mypy_cache',
        'build', 'dist', '.eggs', '*.egg-info', 'data',
        'logs', '.claude', 'genie', 'scripts', 'docs',
        'alembic', 'migrations', 'automagik-store'
    }
    
    # Files to skip during analysis
    SKIP_FILES = {
        '__init__.py', 'setup.py', 'conftest.py'
    }
    
    # Source directories that should have mirror test structure
    SOURCE_DIRS = {'api', 'lib', 'ai', 'common', 'cli'}
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / 'tests'
        self.analysis = TestAnalysis()
    
    def should_skip_path(self, path: Path) -> bool:
        """Check if path should be skipped during analysis."""
        parts = path.parts
        return any(
            skip_dir in parts or 
            any(part.endswith(skip_dir.replace('*', '')) for part in parts)
            for skip_dir in self.SKIP_DIRS
        )
    
    def is_test_file(self, path: Path) -> bool:
        """Check if file follows test naming conventions."""
        name = path.name
        return name.startswith('test_') or name.endswith('_test.py')
    
    def get_expected_test_path(self, source_path: Path) -> Optional[Path]:
        """Get expected test file path for a source file using mirror structure."""
        try:
            relative_path = source_path.relative_to(self.project_root)
        except ValueError:
            return None
        
        # Skip if not in a source directory we care about
        if not any(str(relative_path).startswith(src_dir) for src_dir in self.SOURCE_DIRS):
            return None
        
        # Build expected test path with test_ prefix
        test_path = self.tests_dir / relative_path.parent / f"test_{relative_path.name}"
        return test_path
    
    def get_expected_source_path(self, test_path: Path) -> Optional[Path]:
        """Get expected source file for a test file using mirror structure."""
        try:
            relative_path = test_path.relative_to(self.tests_dir)
        except ValueError:
            return None
        
        # Remove test_ prefix or _test suffix
        name = relative_path.name
        if name.startswith('test_'):
            source_name = name[5:]  # Remove 'test_' prefix
        elif name.endswith('_test.py'):
            source_name = name[:-8] + '.py'  # Remove '_test.py' and add '.py'
        else:
            return None
        
        # Build expected source path
        source_path = self.project_root / relative_path.parent / source_name
        return source_path
    
    def collect_python_files(self) -> Tuple[Set[Path], Set[Path]]:
        """Collect all Python files, categorized as source or test files."""
        source_files = set()
        test_files = set()
        
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            if self.should_skip_path(root_path):
                continue
            
            for file in files:
                if not file.endswith('.py') or file in self.SKIP_FILES:
                    continue
                
                file_path = root_path / file
                
                # Categorize as test or source
                if 'tests' in root_path.parts:
                    test_files.add(file_path)
                else:
                    # Check if it's in a source directory we track
                    try:
                        relative = file_path.relative_to(self.project_root)
                        if any(str(relative).startswith(src_dir) for src_dir in self.SOURCE_DIRS):
                            source_files.add(file_path)
                    except ValueError:
                        continue
        
        return source_files, test_files
    
    def calculate_directory_stats(self) -> Dict[str, Dict]:
        """Calculate detailed statistics by directory."""
        stats = {}
        
        # Initialize stats for each source directory
        for src_dir in self.SOURCE_DIRS:
            src_files = [f for f in self.analysis.source_files 
                        if str(f.relative_to(self.project_root)).startswith(src_dir)]
            test_files = [f for f in self.analysis.test_files 
                         if f.parts[-1] != '__init__.py' and 
                         len(f.parts) > 1 and f.parts[1] == src_dir]
            
            covered_files = len([f for f in src_files if f in self.analysis.coverage_map])
            
            stats[src_dir] = {
                'source_files': len(src_files),
                'test_files': len(test_files),
                'covered_files': covered_files,
                'coverage_percentage': round(
                    (covered_files / len(src_files) * 100) if src_files else 100, 2
                ),
                'missing_tests': len([i for i in self.analysis.missing_tests 
                                    if str(i.source_path.relative_to(self.project_root)).startswith(src_dir)]),
                'orphaned_tests': len([i for i in self.analysis.orphaned_tests 
                                     if i.current_path and len(i.current_path.parts) > 1 and 
                                     i.current_path.parts[1] == src_dir])
            }
        
        return stats
    
    def analyze(self) -> TestAnalysis:
        """Perform comprehensive test structure analysis."""
        # Collect all Python files
        source_files, test_files = self.collect_python_files()
        self.analysis.source_files = source_files
        self.analysis.test_files = test_files
        
        # Track which test files are properly matched
        matched_test_files = set()
        
        # Analyze source files for missing tests
        for source_file in source_files:
            expected_test = self.get_expected_test_path(source_file)
            if expected_test:
                if expected_test.exists():
                    # Perfect match - source has proper test
                    self.analysis.coverage_map[source_file] = expected_test
                    matched_test_files.add(expected_test)
                else:
                    # Missing test file
                    issue = TestIssue(
                        issue_type='missing',
                        source_path=source_file,
                        expected_path=expected_test,
                        severity='high',
                        description=f"Source file {source_file.relative_to(self.project_root)} lacks corresponding test",
                        recommendation=f"Create test file at {expected_test.relative_to(self.project_root)}",
                        file_operation=f"mkdir -p {expected_test.parent} && touch {expected_test}"
                    )
                    self.analysis.issues.append(issue)
        
        # Integration and support directories that don't need source mirrors
        INTEGRATION_PATTERNS = {'integration', 'fixtures', 'mocks', 'utilities', 'e2e', 'scenarios'}
        
        # Analyze test files for orphans, misplaced, and naming issues
        for test_file in test_files:
            # Skip __init__.py files
            if test_file.name == '__init__.py':
                continue
                
            # Check naming conventions
            if not self.is_test_file(test_file):
                issue = TestIssue(
                    issue_type='naming',
                    current_path=test_file,
                    severity='medium',
                    description=f"Test file {test_file.relative_to(self.project_root)} doesn't follow naming convention",
                    recommendation="Rename to follow test_*.py or *_test.py convention",
                    file_operation=f"# Manual review needed for {test_file}"
                )
                self.analysis.issues.append(issue)
                continue
            
            # If already matched to a source file, it's correctly placed
            if test_file in matched_test_files:
                continue
            
            # Check if this is an integration or support test
            path_parts = test_file.parts
            is_integration = any(part in INTEGRATION_PATTERNS for part in path_parts)
            
            # Check if this test has an expected source file
            expected_source = self.get_expected_source_path(test_file)
            if expected_source:
                if expected_source.exists():
                    # Source exists but test is misplaced or misnamed
                    correct_test_path = self.get_expected_test_path(expected_source)
                    if correct_test_path and correct_test_path != test_file:
                        issue = TestIssue(
                            issue_type='misplaced',
                            current_path=test_file,
                            expected_path=correct_test_path,
                            source_path=expected_source,
                            severity='medium',
                            description=f"Test file {test_file.relative_to(self.project_root)} is misplaced",
                            recommendation=f"Move to {correct_test_path.relative_to(self.project_root)}",
                            file_operation=f"mkdir -p {correct_test_path.parent} && mv {test_file} {correct_test_path}"
                        )
                        self.analysis.issues.append(issue)
                else:
                    # Test exists but source doesn't - check if it's integration
                    if is_integration:
                        # This is expected - integration tests don't mirror source files
                        severity = 'info'
                        description = f"Integration test {test_file.relative_to(self.project_root)} (no source mirror needed)"
                        recommendation = "Integration/support test - no action needed"
                        file_operation = f"# Integration test - no action needed for {test_file}"
                    else:
                        # Regular orphaned test
                        severity = 'low'
                        description = f"Orphaned test {test_file.relative_to(self.project_root)} has no corresponding source"
                        recommendation = f"Remove orphaned test or create source file at {expected_source.relative_to(self.project_root)}"
                        file_operation = f"rm {test_file}  # Or create {expected_source}"
                    
                    issue = TestIssue(
                        issue_type='orphaned',
                        current_path=test_file,
                        expected_path=expected_source,
                        severity=severity,
                        description=description,
                        recommendation=recommendation,
                        file_operation=file_operation
                    )
                    self.analysis.issues.append(issue)
            else:
                # Can't determine expected source - check if it's integration
                if is_integration:
                    severity = 'info'
                    description = f"Integration test {test_file.relative_to(self.project_root)} (expected - no source mirror needed)"
                    recommendation = "Integration/support test - no action needed"
                    file_operation = f"# Integration test - no action needed for {test_file}"
                else:
                    severity = 'low'
                    description = f"Test file {test_file.relative_to(self.project_root)} can't be mapped to source"
                    recommendation = "Review test file purpose and location"
                    file_operation = f"# Manual review needed for {test_file}"
                
                issue = TestIssue(
                    issue_type='orphaned',
                    current_path=test_file,
                    severity=severity,
                    description=description,
                    recommendation=recommendation,
                    file_operation=file_operation
                )
                self.analysis.issues.append(issue)
        
        # Calculate directory statistics
        self.analysis.directory_stats = self.calculate_directory_stats()
        
        return self.analysis
    
    def generate_file_operations(self) -> List[str]:
        """Generate precise file operation commands for autonomous reorganization."""
        operations = []
        
        # Header
        operations.append("#!/bin/bash")
        operations.append("# Automated test structure reorganization commands")
        operations.append("# Generated by Unified Test Structure Analyzer")
        operations.append("set -e  # Exit on any error")
        operations.append("")
        
        # Group operations by type for logical execution order
        missing_ops = []
        move_ops = []
        remove_ops = []
        manual_ops = []
        
        for issue in self.analysis.issues:
            if issue.file_operation:
                if issue.issue_type == 'missing':
                    missing_ops.append(f"# Missing: {issue.description}")
                    missing_ops.append(issue.file_operation)
                    missing_ops.append("")
                elif issue.issue_type == 'misplaced':
                    move_ops.append(f"# Misplaced: {issue.description}")
                    move_ops.append(issue.file_operation)
                    move_ops.append("")
                elif issue.issue_type == 'orphaned':
                    if issue.file_operation.startswith('rm'):
                        remove_ops.append(f"# Orphaned: {issue.description}")
                        remove_ops.append(issue.file_operation)
                        remove_ops.append("")
                    else:
                        manual_ops.append(f"# Manual review: {issue.description}")
                        manual_ops.append(issue.file_operation)
                        manual_ops.append("")
                else:
                    manual_ops.append(f"# Manual review: {issue.description}")
                    manual_ops.append(issue.file_operation)
                    manual_ops.append("")
        
        # Add operations in logical order
        if missing_ops:
            operations.append("# === CREATE MISSING TEST FILES ===")
            operations.extend(missing_ops)
        
        if move_ops:
            operations.append("# === MOVE MISPLACED TEST FILES ===")
            operations.extend(move_ops)
        
        if remove_ops:
            operations.append("# === REMOVE ORPHANED TEST FILES ===")
            operations.append("# Review these carefully before executing!")
            operations.extend(remove_ops)
        
        if manual_ops:
            operations.append("# === MANUAL REVIEW REQUIRED ===")
            operations.extend(manual_ops)
        
        operations.append("echo 'Test structure reorganization complete!'")
        operations.append("echo 'Run the analyzer again to verify zero issues.'")
        
        return operations
    
    def generate_report(self, format: str = 'text') -> str:
        """Generate comprehensive analysis report."""
        if format == 'json':
            return self._generate_json_report()
        elif format == 'ops':
            return '\n'.join(self.generate_file_operations())
        else:
            return self._generate_text_report()
    
    def _generate_text_report(self) -> str:
        """Generate detailed human-readable text report."""
        lines = []
        lines.append("=" * 80)
        lines.append("UNIFIED TEST STRUCTURE ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Success criteria check
        if self.analysis.is_perfect_structure:
            lines.append("🎉 SUCCESS: PERFECT MIRROR STRUCTURE ACHIEVED!")
            lines.append("   Zero issues found - test structure is perfectly organized")
            lines.append("")
        else:
            lines.append("⚠️  ISSUES FOUND: Mirror structure needs improvement")
            lines.append(f"   Total issues to resolve: {self.analysis.total_issues}")
            lines.append("")
        
        # Summary statistics
        stats = self.analysis.stats
        lines.append("SUMMARY STATISTICS:")
        lines.append("-" * 40)
        lines.append(f"Total source files:     {stats['total_source_files']:>5}")
        lines.append(f"Total test files:       {stats['total_test_files']:>5}")
        lines.append(f"Covered source files:   {stats['covered_source_files']:>5}")
        lines.append(f"Missing tests:          {stats['missing_tests']:>5}")
        lines.append(f"Orphaned tests:         {stats['orphaned_tests']:>5}")
        lines.append(f"Misplaced tests:        {stats['misplaced_tests']:>5}")
        lines.append(f"Naming issues:          {stats['naming_issues']:>5}")
        lines.append(f"Total issues:           {stats['total_issues']:>5}")
        lines.append(f"Coverage percentage:    {stats['coverage_percentage']:>5.1f}%")
        lines.append("")
        
        # Directory breakdown
        if self.analysis.directory_stats:
            lines.append("BREAKDOWN BY SOURCE DIRECTORY:")
            lines.append("-" * 40)
            lines.append(f"{'Directory':<12} {'Source':<6} {'Tests':<6} {'Covered':<7} {'Coverage':<8} {'Missing':<7} {'Orphaned':<8}")
            lines.append("-" * 70)
            for dir_name, stats in self.analysis.directory_stats.items():
                lines.append(
                    f"{dir_name:<12} {stats['source_files']:<6} {stats['test_files']:<6} "
                    f"{stats['covered_files']:<7} {stats['coverage_percentage']:<8.1f}% "
                    f"{stats['missing_tests']:<7} {stats['orphaned_tests']:<8}"
                )
            lines.append("")
        
        # Detailed issue breakdown
        if self.analysis.missing_tests:
            lines.append("MISSING TESTS (source files without tests):")
            lines.append("-" * 40)
            for issue in sorted(self.analysis.missing_tests, key=lambda x: str(x.source_path)):
                rel_source = issue.source_path.relative_to(self.project_root)
                rel_expected = issue.expected_path.relative_to(self.project_root)
                lines.append(f"  ❌ {rel_source}")
                lines.append(f"     → Expected: {rel_expected}")
            lines.append("")
        
        if self.analysis.orphaned_tests:
            lines.append("ORPHANED TESTS (tests without source files):")
            lines.append("-" * 40)
            for issue in sorted(self.analysis.orphaned_tests, key=lambda x: str(x.current_path)):
                rel_test = issue.current_path.relative_to(self.project_root)
                lines.append(f"  👻 {rel_test}")
                if issue.expected_path:
                    rel_expected = issue.expected_path.relative_to(self.project_root)
                    lines.append(f"     → Expected source: {rel_expected}")
            lines.append("")
        
        if self.analysis.misplaced_tests:
            lines.append("MISPLACED TESTS (tests in wrong location):")
            lines.append("-" * 40)
            for issue in sorted(self.analysis.misplaced_tests, key=lambda x: str(x.current_path)):
                rel_current = issue.current_path.relative_to(self.project_root)
                rel_expected = issue.expected_path.relative_to(self.project_root)
                lines.append(f"  📍 {rel_current}")
                lines.append(f"     → Should be: {rel_expected}")
            lines.append("")
        
        if self.analysis.naming_issues:
            lines.append("NAMING ISSUES (incorrect test file naming):")
            lines.append("-" * 40)
            for issue in sorted(self.analysis.naming_issues, key=lambda x: str(x.current_path)):
                rel_test = issue.current_path.relative_to(self.project_root)
                lines.append(f"  ⚠️  {rel_test}")
                lines.append(f"     → {issue.recommendation}")
            lines.append("")
        
        # Recommendations
        lines.append("ACTIONABLE RECOMMENDATIONS:")
        lines.append("-" * 40)
        if self.analysis.is_perfect_structure:
            lines.append("  ✅ Structure is perfect! No actions needed.")
        else:
            lines.append("  1. Run with --ops flag to get file operation commands")
            lines.append("  2. Execute generated commands to fix structure automatically")
            lines.append("  3. Re-run analyzer to verify zero issues (success criteria)")
            
            if self.analysis.missing_tests:
                lines.append(f"  4. Priority: Create {len(self.analysis.missing_tests)} missing test files")
            if self.analysis.orphaned_tests:
                lines.append(f"  5. Review {len(self.analysis.orphaned_tests)} orphaned tests for deletion")
            if self.analysis.misplaced_tests:
                lines.append(f"  6. Relocate {len(self.analysis.misplaced_tests)} misplaced test files")
        
        lines.append("")
        lines.append("SUCCESS CRITERIA: Zero issues reported = Perfect mirror structure")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _generate_json_report(self) -> str:
        """Generate comprehensive JSON report."""
        def path_to_str(path: Optional[Path]) -> Optional[str]:
            return str(path.relative_to(self.project_root)) if path else None
        
        issues_data = []
        for issue in self.analysis.issues:
            issue_data = {
                "type": issue.issue_type,
                "severity": issue.severity,
                "description": issue.description,
                "recommendation": issue.recommendation,
                "file_operation": issue.file_operation,
                "current_path": path_to_str(issue.current_path),
                "expected_path": path_to_str(issue.expected_path),
                "source_path": path_to_str(issue.source_path)
            }
            issues_data.append(issue_data)
        
        report = {
            "summary": self.analysis.stats,
            "directory_stats": self.analysis.directory_stats,
            "issues": issues_data,
            "coverage_map": {
                path_to_str(k): path_to_str(v)
                for k, v in self.analysis.coverage_map.items()
            },
            "file_operations_count": len([i for i in self.analysis.issues if i.file_operation]),
            "success_criteria_met": self.analysis.is_perfect_structure
        }
        
        return json.dumps(report, indent=2)


def main():
    """Main entry point with enhanced command-line interface."""
    # Parse arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            print(__doc__)
            sys.exit(0)
    
    # Determine output format
    format = 'text'
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--json', '-j']:
            format = 'json'
        elif sys.argv[1] in ['--ops', '-o']:
            format = 'ops'
    
    # Determine project root
    project_root = Path.cwd()
    
    # Create analyzer and run analysis
    analyzer = UnifiedTestStructureAnalyzer(project_root)
    analyzer.analyze()
    
    # Generate and print report
    report = analyzer.generate_report(format=format)
    print(report)
    
    # Exit codes for automation
    if format == 'ops':
        # For ops mode, exit 0 (operations generated successfully)
        sys.exit(0)
    elif analyzer.analysis.is_perfect_structure:
        # Perfect structure achieved - success!
        sys.exit(0)
    elif analyzer.analysis.stats['coverage_percentage'] < 30:
        # Very poor coverage - critical
        sys.exit(2)
    else:
        # Issues found but manageable
        sys.exit(1)


if __name__ == "__main__":
    main()