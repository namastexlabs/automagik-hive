#!/usr/bin/env python3
"""
Test Structure Analyzer - Intelligent False Positive Reduction

This analyzer includes:
- Smart content analysis to determine if files actually need tests
- Context-aware test classification (integration vs unit vs support)
- Flexible pattern recognition for related tests
- Confidence-based issue filtering to reduce false positives
- Adaptive reporting with high-confidence vs suggestions

Usage:
    python test_analyzer.py [--json|-j] [--ops|-o] [--confidence|-c 0.7] [--help|-h]
    
    --json, -j: Output analysis in JSON format
    --ops, -o:  Output file operation commands for reorganization
    --confidence, -c: Minimum confidence threshold (0.0-1.0, default 0.7)
    --help, -h: Show this help message
"""

import os
import sys
import shutil
import fnmatch
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json
import re


@dataclass
class TestIssue:
    """Container for a specific test structure issue with confidence scoring."""
    issue_type: str  # 'missing', 'orphaned', 'misplaced', 'naming'
    current_path: Optional[Path] = None
    expected_path: Optional[Path] = None
    source_path: Optional[Path] = None
    severity: str = 'medium'  # 'low', 'medium', 'high', 'critical', 'suggestion'
    description: str = ''
    recommendation: str = ''
    file_operation: str = ''  # Specific command to fix the issue
    confidence: float = 1.0  # 0.0 to 1.0 confidence level
    reasoning: str = ''  # Explanation for flagging this issue


@dataclass
class TestAnalysis:
    """Container for comprehensive test analysis results."""
    source_files: Set[Path] = field(default_factory=set)
    test_files: Set[Path] = field(default_factory=set)
    issues: List[TestIssue] = field(default_factory=list)
    coverage_map: Dict[Path, Path] = field(default_factory=dict)
    directory_stats: Dict[str, Dict] = field(default_factory=dict)
    confidence_threshold: float = 0.7
    
    @property
    def high_confidence_issues(self) -> List[TestIssue]:
        return [issue for issue in self.issues if issue.confidence >= self.confidence_threshold]
    
    @property
    def suggestions(self) -> List[TestIssue]:
        return [issue for issue in self.issues if issue.confidence < self.confidence_threshold]
    
    @property
    def missing_tests(self) -> List[TestIssue]:
        return [issue for issue in self.high_confidence_issues if issue.issue_type == 'missing']
    
    @property
    def orphaned_tests(self) -> List[TestIssue]:
        return [issue for issue in self.high_confidence_issues if issue.issue_type == 'orphaned']
    
    @property
    def integration_tests(self) -> List[TestIssue]:
        """Integration tests that don't need source mirrors (low confidence orphans)."""
        return [issue for issue in self.suggestions if issue.issue_type == 'orphaned']
    
    @property
    def misplaced_tests(self) -> List[TestIssue]:
        return [issue for issue in self.high_confidence_issues if issue.issue_type == 'misplaced']
    
    @property
    def naming_issues(self) -> List[TestIssue]:
        return [issue for issue in self.high_confidence_issues if issue.issue_type == 'naming']
    
    @property
    def coverage_percentage(self) -> float:
        if not self.source_files:
            return 100.0
        covered_files = len(self.coverage_map)
        return (covered_files / len(self.source_files)) * 100
    
    @property
    def total_issues(self) -> int:
        return len(self.high_confidence_issues)
    
    @property
    def is_perfect_structure(self) -> bool:
        """True if zero high-confidence issues found."""
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
            "misplaced_tests": len(self.misplaced_tests),
            "naming_issues": len(self.naming_issues),
            "high_confidence_issues": len(self.high_confidence_issues),
            "suggestions": len(self.suggestions),
            "confidence_threshold": self.confidence_threshold,
            "coverage_percentage": round(self.coverage_percentage, 2),
            "is_perfect_structure": self.is_perfect_structure
        }


class TestStructureAnalyzer:
    """Test structure analyzer with intelligent false positive reduction."""
    
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
    
    def __init__(self, project_root: Path, confidence_threshold: float = 0.7):
        self.project_root = project_root
        self.tests_dir = project_root / 'tests'
        self.analysis = TestAnalysis(confidence_threshold=confidence_threshold)
        self.ignored_tests = self._load_ignored_tests()
    
    def should_skip_path(self, path: Path) -> bool:
        """Check if path should be skipped during analysis."""
        parts = path.parts
        return any(
            skip_dir in parts or 
            any(part.endswith(skip_dir.replace('*', '')) for part in parts)
            for skip_dir in self.SKIP_DIRS
        )
    
    def should_require_test(self, source_path: Path) -> bool:
        """Intelligent analysis of whether a file actually needs tests."""
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return True  # Default to requiring tests if we can't read
        
        # Skip empty or very small files
        if len(content.strip()) < 50:
            return False
            
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        total_lines = len(lines)
        
        if total_lines == 0:
            return False
        
        # Count different types of content
        import_lines = sum(1 for line in lines if line.startswith(('import ', 'from ')))
        comment_lines = sum(1 for line in lines if line.startswith('#'))
        constant_lines = sum(1 for line in lines if '=' in line and re.match(r'^[A-Z_][A-Z0-9_]*\s*=', line))
        function_defs = content.count('def ')
        class_defs = content.count('class ')
        
        # Heuristics for files that likely don't need tests
        mostly_imports = import_lines > total_lines * 0.5
        mostly_constants = constant_lines > total_lines * 0.3
        config_file = any(pattern in source_path.name.lower() for pattern in ['config', 'settings', 'constants'])
        no_executable_code = function_defs == 0 and class_defs == 0
        simple_dataclass = '@dataclass' in content and function_defs <= 2
        only_type_hints = 'typing' in content and function_defs == 0 and class_defs <= 1
        
        # Check for obvious test-exempt patterns
        if any([
            mostly_imports, mostly_constants, config_file,
            no_executable_code, simple_dataclass, only_type_hints
        ]):
            return False
        
        return True
    
    def classify_test_file(self, test_path: Path) -> str:
        """Intelligently classify test files based on location and content."""
        parts = [part.lower() for part in test_path.parts]
        name = test_path.name.lower()
        
        # Check directory context patterns
        if any(part in {'integration', 'e2e', 'end_to_end', 'scenarios'} for part in parts):
            return 'integration'
        elif any(part in {'fixtures', 'fixture', 'data', 'mocks', 'mock'} for part in parts):
            return 'support'
        elif 'conftest.py' in name or 'fixture' in name:
            return 'fixture'
        elif any(word in name for word in ['helper', 'util', 'base', 'common', 'support']):
            return 'utility'
        
        # Analyze content for additional context
        try:
            with open(test_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for integration test indicators
            integration_indicators = [
                'requests.', 'httpx.', 'curl', 'endpoint', 'api_client',
                'subprocess.', 'docker', 'database', 'redis', 'postgres'
            ]
            if any(indicator in content for indicator in integration_indicators):
                return 'integration'
            
            # Look for fixture definitions
            if 'pytest.fixture' in content or '@fixture' in content:
                return 'fixture'
            
            # Look for mock-heavy tests
            mock_indicators = ['mock.', 'patch', 'MagicMock', 'Mock()']
            mock_count = sum(content.count(indicator) for indicator in mock_indicators)
            if mock_count > 3:
                return 'unit'  # Heavy mocking usually means unit tests
                
        except Exception:
            pass
        
        return 'unit'  # Default assumption
    
    def find_related_tests(self, source_path: Path) -> List[Path]:
        """Find tests related to a source file using flexible patterns."""
        source_name = source_path.stem
        base_patterns = [
            f"test_{source_name}.py",
            f"{source_name}_test.py",
            f"test_{source_name}_*.py",
            f"*test*{source_name}*.py",
            f"test{source_name.title().replace('_', '')}.py"
        ]
        
        # Add variations for common naming patterns
        name_variations = [
            source_name.replace('_', ''),
            source_name.replace('_', '-'),
            ''.join(word.capitalize() for word in source_name.split('_'))
        ]
        
        all_patterns = base_patterns[:]
        for variation in name_variations:
            all_patterns.extend([
                f"test_{variation.lower()}.py",
                f"{variation.lower()}_test.py"
            ])
        
        related_tests = []
        for test_file in self.analysis.test_files:
            test_name = test_file.name
            if any(fnmatch.fnmatch(test_name, pattern) for pattern in all_patterns):
                related_tests.append(test_file)
        
        return related_tests
    
    def calculate_issue_confidence(self, issue: TestIssue) -> Tuple[float, str]:
        """Calculate confidence level for this issue being a real problem."""
        confidence = 1.0
        reasoning_parts = []
        
        if issue.issue_type == 'missing':
            # Check if file actually needs tests
            if not self.should_require_test(issue.source_path):
                confidence *= 0.2
                reasoning_parts.append("File appears to be config/constants - may not need tests")
            
            # Check for related tests with different naming
            related_tests = self.find_related_tests(issue.source_path)
            if related_tests:
                confidence *= 0.4
                test_names = [t.name for t in related_tests[:3]]
                reasoning_parts.append(f"Found related tests: {', '.join(test_names)}")
        
        elif issue.issue_type == 'orphaned':
            # Integration/support tests shouldn't be flagged as high confidence orphans
            test_type = self.classify_test_file(issue.current_path)
            if test_type in ['integration', 'fixture', 'utility', 'support']:
                confidence *= 0.1
                reasoning_parts.append(f"Classified as {test_type} test - expected to have no direct source mirror")
            
            # Check if it's in a clearly integration directory
            path_parts = [part.lower() for part in issue.current_path.parts]
            integration_dirs = {'integration', 'e2e', 'scenarios', 'fixtures'}
            if any(part in integration_dirs for part in path_parts):
                confidence *= 0.05
                reasoning_parts.append("Located in integration/support directory structure")
        
        elif issue.issue_type == 'misplaced':
            # Lower confidence if the current location makes sense contextually
            current_dir = issue.current_path.parent.name.lower()
            if any(keyword in current_dir for keyword in ['integration', 'e2e', 'functional']):
                confidence *= 0.3
                reasoning_parts.append("Current location suggests intentional placement for integration testing")
        
        reasoning = " | ".join(reasoning_parts) if reasoning_parts else "Standard detection criteria met"
        return confidence, reasoning
    
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
        """Get expected source file for a test file using intelligent layered strategies."""
        try:
            relative_path = test_path.relative_to(self.tests_dir)
        except ValueError:
            return None
        
        # Strategy 1: Direct Name Match (Original Logic)
        name = relative_path.name
        if name.startswith('test_'):
            source_name = name[5:]  # Remove 'test_' prefix
        elif name.endswith('_test.py'):
            source_name = name[:-8] + '.py'  # Remove '_test.py' and add '.py'
        else:
            return None
        
        direct_match = self.project_root / relative_path.parent / source_name
        if direct_match.exists():
            return direct_match
        
        # Strategy 2: Convention-Aware Search (agent.py pattern)
        if self._is_agent_test(test_path):
            agent_file = self._find_agent_file(relative_path)
            if agent_file and agent_file.exists():
                return agent_file
        
        # Strategy 3: Single-Module Directory Search
        source_dir = self.project_root / relative_path.parent
        if source_dir.exists() and source_dir.is_dir():
            single_module = self._find_single_module_in_dir(source_dir)
            if single_module:
                return single_module
        
        # Return direct match attempt (even if doesn't exist) for traditional handling
        return direct_match
    
    def _is_agent_test(self, test_path: Path) -> bool:
        """Check if this is an agent test following the agent.py convention."""
        path_str = str(test_path)
        return ('ai/agents/' in path_str and 
                test_path.name.endswith('_agent.py'))
    
    def _find_agent_file(self, test_relative_path: Path) -> Optional[Path]:
        """Find agent.py file in corresponding agent directory."""
        # For tests/ai/agents/genie-quality/test_genie_quality_agent.py
        # Look for ai/agents/genie-quality/agent.py
        if len(test_relative_path.parts) >= 3 and test_relative_path.parts[:2] == ('ai', 'agents'):
            agent_name = test_relative_path.parts[2]
            agent_file = self.project_root / 'ai' / 'agents' / agent_name / 'agent.py'
            return agent_file
        return None
    
    def _find_single_module_in_dir(self, source_dir: Path) -> Optional[Path]:
        """Find single Python module in directory (excluding __init__.py)."""
        try:
            python_files = [f for f in source_dir.glob('*.py') 
                          if f.name != '__init__.py' and not f.name.startswith('test_')]
            
            # If exactly one module found, it's likely the intended target
            if len(python_files) == 1:
                return python_files[0]
        except Exception:
            pass
        return None
    
    def _load_ignored_tests(self) -> Set[str]:
        """Load ignored test files from .test_analyzer_ignore file."""
        ignored = set()
        ignore_file = self.project_root / '.test_analyzer_ignore'
        
        if ignore_file.exists():
            try:
                with open(ignore_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            ignored.add(line)
            except Exception:
                pass
        
        return ignored
    
    def _is_test_ignored(self, test_path: Path) -> bool:
        """Check if test is in the ignore list."""
        try:
            relative_path = str(test_path.relative_to(self.project_root))
            return relative_path in self.ignored_tests
        except ValueError:
            return False
    
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
    
    def analyze(self) -> TestAnalysis:
        """Perform comprehensive test structure analysis with intelligent filtering."""
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
                    # Missing test file - calculate confidence
                    issue = TestIssue(
                        issue_type='missing',
                        source_path=source_file,
                        expected_path=expected_test,
                        severity='high',
                        description=f"Source file {source_file.relative_to(self.project_root)} lacks corresponding test",
                        recommendation=f"Create test file at {expected_test.relative_to(self.project_root)}",
                        file_operation=f"mkdir -p {expected_test.parent} && touch {expected_test}"
                    )
                    
                    # Calculate confidence and reasoning
                    confidence, reasoning = self.calculate_issue_confidence(issue)
                    issue.confidence = confidence
                    issue.reasoning = reasoning
                    
                    # Adjust severity based on confidence
                    if confidence < 0.3:
                        issue.severity = 'suggestion'
                    elif confidence < 0.7:
                        issue.severity = 'low'
                    
                    self.analysis.issues.append(issue)
        
        # Integration and support directories that don't need source mirrors
        INTEGRATION_PATTERNS = {'integration', 'fixtures', 'mocks', 'utilities', 'e2e', 'scenarios'}
        
        # Analyze test files for orphans, misplaced, and naming issues
        for test_file in test_files:
            # Skip __init__.py files
            if test_file.name == '__init__.py':
                continue
            
            # Skip ignored test files
            if self._is_test_ignored(test_file):
                continue
                
            # Check naming conventions
            if not self.is_test_file(test_file):
                issue = TestIssue(
                    issue_type='naming',
                    current_path=test_file,
                    severity='medium',
                    description=f"Test file {test_file.relative_to(self.project_root)} doesn't follow naming convention",
                    recommendation="Rename to follow test_*.py or *_test.py convention",
                    file_operation=f"# Manual review needed for {test_file}",
                    confidence=0.9,
                    reasoning="File in tests/ directory but doesn't follow naming convention"
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
                        
                        # Calculate confidence for misplacement
                        confidence, reasoning = self.calculate_issue_confidence(issue)
                        issue.confidence = confidence
                        issue.reasoning = reasoning
                        
                        self.analysis.issues.append(issue)
                else:
                    # Test exists but source doesn't - calculate confidence for orphan status
                    issue = TestIssue(
                        issue_type='orphaned',
                        current_path=test_file,
                        expected_path=expected_source,
                        severity='low',
                        description=f"Test {test_file.relative_to(self.project_root)} has no corresponding source",
                        recommendation=f"Remove test or create source file at {expected_source.relative_to(self.project_root)}",
                        file_operation=f"rm {test_file}  # Or create {expected_source}"
                    )
                    
                    # Calculate confidence - integration tests get very low confidence
                    confidence, reasoning = self.calculate_issue_confidence(issue)
                    issue.confidence = confidence
                    issue.reasoning = reasoning
                    
                    if confidence < 0.3:
                        issue.severity = 'suggestion'
                        issue.description = f"Integration test {test_file.relative_to(self.project_root)} (no source mirror needed)"
                        issue.recommendation = "Integration/support test - no action needed"
                        issue.file_operation = f"# Integration test - no action needed for {test_file}"
                    
                    self.analysis.issues.append(issue)
            else:
                # Can't determine expected source - likely integration test
                issue = TestIssue(
                    issue_type='orphaned',
                    current_path=test_file,
                    severity='suggestion',
                    confidence=0.1,
                    description=f"Integration test {test_file.relative_to(self.project_root)} (expected - no source mirror needed)",
                    recommendation="Integration/support test - no action needed",
                    file_operation=f"# Integration test - no action needed for {test_file}",
                    reasoning="Cannot map to source - likely integration/support test"
                )
                self.analysis.issues.append(issue)
        
        return self.analysis
    
    def generate_report(self, format: str = 'text') -> str:
        """Generate comprehensive analysis report with confidence-based filtering."""
        if format == 'json':
            return self._generate_json_report()
        elif format == 'ops':
            return self._generate_ops_report()
        else:
            return self._generate_text_report()
    
    def _generate_text_report(self) -> str:
        """Generate human-readable text report."""
        lines = []
        lines.append("=" * 80)
        lines.append("TEST STRUCTURE ANALYSIS - INTELLIGENT FALSE POSITIVE REDUCTION")
        lines.append("=" * 80)
        lines.append("")
        
        # Success criteria check
        if self.analysis.is_perfect_structure:
            lines.append("🎉 SUCCESS: PERFECT MIRROR STRUCTURE ACHIEVED!")
            lines.append("   Zero high-confidence issues found - test structure is well organized")
            lines.append("")
        else:
            lines.append("⚠️  HIGH-CONFIDENCE ISSUES FOUND: Mirror structure needs attention")
            lines.append(f"   Issues requiring action: {self.analysis.total_issues}")
            lines.append(f"   Suggestions (filtered): {len(self.analysis.suggestions)}")
            lines.append("")
        
        # Summary statistics
        stats = self.analysis.stats
        lines.append("SUMMARY STATISTICS:")
        lines.append("-" * 40)
        lines.append(f"Confidence threshold:       {stats['confidence_threshold']:.1f}")
        lines.append(f"Total source files:         {stats['total_source_files']:>5}")
        lines.append(f"Total test files:           {stats['total_test_files']:>5}")
        lines.append(f"Covered source files:       {stats['covered_source_files']:>5}")
        lines.append(f"High-confidence issues:     {stats['high_confidence_issues']:>5}")
        lines.append(f"Filtered suggestions:       {stats['suggestions']:>5}")
        lines.append(f"Coverage percentage:        {stats['coverage_percentage']:>5.1f}%")
        lines.append("")
        
        # High-confidence issues breakdown
        if self.analysis.missing_tests:
            lines.append("HIGH-CONFIDENCE MISSING TESTS:")
            lines.append("-" * 40)
            for issue in sorted(self.analysis.missing_tests, key=lambda x: x.confidence, reverse=True):
                rel_source = issue.source_path.relative_to(self.project_root)
                rel_expected = issue.expected_path.relative_to(self.project_root)
                lines.append(f"  ❌ {rel_source} (confidence: {issue.confidence:.2f})")
                lines.append(f"     → Expected: {rel_expected}")
                if issue.reasoning:
                    lines.append(f"     → Reason: {issue.reasoning}")
            lines.append("")
        
        if self.analysis.orphaned_tests:
            lines.append("HIGH-CONFIDENCE ORPHANED TESTS:")
            lines.append("-" * 40)
            for issue in sorted(self.analysis.orphaned_tests, key=lambda x: x.confidence, reverse=True):
                rel_test = issue.current_path.relative_to(self.project_root)
                lines.append(f"  👻 {rel_test} (confidence: {issue.confidence:.2f})")
                if issue.expected_path:
                    rel_expected = issue.expected_path.relative_to(self.project_root)
                    lines.append(f"     → Expected source: {rel_expected}")
                if issue.reasoning:
                    lines.append(f"     → Reason: {issue.reasoning}")
            lines.append("")
        
        # Show filtered suggestions summary
        if self.analysis.suggestions:
            lines.append("FILTERED SUGGESTIONS (Low Confidence):")
            lines.append("-" * 40)
            suggestion_types = {}
            for issue in self.analysis.suggestions:
                issue_type = issue.issue_type
                if issue_type not in suggestion_types:
                    suggestion_types[issue_type] = []
                suggestion_types[issue_type].append(issue)
            
            for issue_type, issues in suggestion_types.items():
                lines.append(f"  💡 {len(issues)} {issue_type} suggestions (avg confidence: {sum(i.confidence for i in issues)/len(issues):.2f})")
            lines.append("     → Most likely false positives - integration tests, config files, etc.")
            lines.append("")
        
        # Actionable recommendations
        lines.append("INTELLIGENT RECOMMENDATIONS:")
        lines.append("-" * 40)
        if self.analysis.is_perfect_structure:
            lines.append("  ✅ Structure is excellent! Only low-confidence suggestions filtered out.")
        else:
            lines.append("  1. Focus on high-confidence issues only (reduces false positive noise)")
            lines.append(f"  2. Address {len(self.analysis.missing_tests)} missing tests for core functionality")
            lines.append(f"  3. Review {len(self.analysis.orphaned_tests)} truly orphaned tests")
            lines.append(f"  4. Consider suggestions only if they align with your testing strategy")
            lines.append("  5. Adjust --confidence threshold (0.0-1.0) to tune sensitivity")
        
        lines.append("")
        lines.append(f"CONFIDENCE-BASED FILTERING: Threshold {self.analysis.confidence_threshold:.1f} filtered out {len(self.analysis.suggestions)} likely false positives")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _generate_json_report(self) -> str:
        """Generate comprehensive JSON report with confidence data."""
        def path_to_str(path: Optional[Path]) -> Optional[str]:
            return str(path.relative_to(self.project_root)) if path else None
        
        issues_data = []
        for issue in self.analysis.issues:
            issue_data = {
                "type": issue.issue_type,
                "severity": issue.severity,
                "confidence": round(issue.confidence, 3),
                "reasoning": issue.reasoning,
                "description": issue.description,
                "recommendation": issue.recommendation,
                "file_operation": issue.file_operation,
                "current_path": path_to_str(issue.current_path),
                "expected_path": path_to_str(issue.expected_path),
                "source_path": path_to_str(issue.source_path)
            }
            issues_data.append(issue_data)
        
        # Separate high-confidence from suggestions
        high_confidence = [i for i in issues_data if i['confidence'] >= self.analysis.confidence_threshold]
        suggestions = [i for i in issues_data if i['confidence'] < self.analysis.confidence_threshold]
        
        report = {
            "summary": self.analysis.stats,
            "high_confidence_issues": high_confidence,
            "suggestions": suggestions,
            "coverage_map": {
                path_to_str(k): path_to_str(v)
                for k, v in self.analysis.coverage_map.items()
            },
            "confidence_filtering": {
                "threshold": self.analysis.confidence_threshold,
                "total_detected": len(self.analysis.issues),
                "high_confidence": len(high_confidence),
                "filtered_suggestions": len(suggestions)
            },
            "success_criteria_met": self.analysis.is_perfect_structure
        }
        
        return json.dumps(report, indent=2)
    
    def _generate_ops_report(self) -> str:
        """Generate file operations only for high-confidence issues."""
        operations = []
        operations.append("#!/bin/bash")
        operations.append("# Test structure reorganization - HIGH CONFIDENCE ISSUES ONLY")
        operations.append("# Intelligent filtering applied - false positives removed")
        operations.append("set -e")
        operations.append("")
        
        high_confidence_ops = []
        for issue in self.analysis.high_confidence_issues:
            if issue.file_operation and not issue.file_operation.startswith('#'):
                high_confidence_ops.append(f"# {issue.description} (confidence: {issue.confidence:.2f})")
                high_confidence_ops.append(issue.file_operation)
                high_confidence_ops.append("")
        
        if high_confidence_ops:
            operations.append("# === HIGH CONFIDENCE OPERATIONS ===")
            operations.extend(high_confidence_ops)
        else:
            operations.append("# No high-confidence operations needed!")
            operations.append("# Intelligent filtering prevented false positive actions")
        
        operations.append("echo 'Test structure analysis complete!'")
        operations.append(f"echo 'Confidence threshold: {self.analysis.confidence_threshold}'")
        operations.append(f"echo 'Filtered out {len(self.analysis.suggestions)} likely false positives'")
        
        return '\n'.join(operations)


def main():
    """Main entry point with confidence threshold support."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test Structure Analyzer with Intelligent False Positive Reduction"
    )
    parser.add_argument('--json', '-j', action='store_true',
                       help='Output analysis in JSON format')
    parser.add_argument('--ops', '-o', action='store_true',
                       help='Output file operation commands for reorganization')
    parser.add_argument('--confidence', '-c', type=float, default=0.7,
                       help='Minimum confidence threshold (0.0-1.0, default: 0.7)')
    
    args = parser.parse_args()
    
    # Validate confidence threshold
    if not 0.0 <= args.confidence <= 1.0:
        print("Error: Confidence threshold must be between 0.0 and 1.0")
        sys.exit(1)
    
    # Determine output format
    if args.json:
        format = 'json'
    elif args.ops:
        format = 'ops'
    else:
        format = 'text'
    
    # Create analyzer with confidence threshold
    project_root = Path.cwd()
    analyzer = TestStructureAnalyzer(project_root, confidence_threshold=args.confidence)
    analyzer.analyze()
    
    # Generate and print report
    report = analyzer.generate_report(format=format)
    print(report)
    
    # Exit codes
    if format == 'ops':
        sys.exit(0)
    elif analyzer.analysis.is_perfect_structure:
        sys.exit(0)  # Perfect structure
    elif analyzer.analysis.stats['coverage_percentage'] < 30:
        sys.exit(2)  # Critical coverage issues
    else:
        sys.exit(1)  # Issues found but manageable


if __name__ == "__main__":
    main()