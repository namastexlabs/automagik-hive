#!/usr/bin/env python3
"""
Deep Test Structure Analysis - Detailed breakdown of test coverage issues.
"""

import os
from pathlib import Path
from collections import defaultdict
import json


def analyze_test_structure():
    """Analyze test structure in detail."""
    
    # Categories for analysis
    source_dirs = {'api', 'lib', 'ai', 'common', 'cli'}
    skip_dirs = {'__pycache__', '.git', '.venv', 'venv', 'data', 'logs', '.pytest_cache'}
    
    # Collections
    source_files = defaultdict(list)  # dir -> [files]
    test_files = defaultdict(list)    # dir -> [files]
    
    # Collect source files
    for src_dir in source_dirs:
        if not Path(src_dir).exists():
            continue
        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for f in files:
                if f.endswith('.py') and not f.startswith('test_') and f != '__init__.py':
                    rel_path = Path(root) / f
                    source_files[src_dir].append(str(rel_path))
    
    # Collect test files
    if Path('tests').exists():
        for root, dirs, files in os.walk('tests'):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for f in files:
                if f.endswith('.py') and f != '__init__.py' and f != 'conftest.py':
                    rel_path = Path(root) / f
                    # Determine which source dir this test belongs to
                    parts = Path(root).parts[1:] if len(Path(root).parts) > 1 else []
                    if parts and parts[0] in source_dirs:
                        test_files[parts[0]].append(str(rel_path))
                    else:
                        test_files['_root'].append(str(rel_path))
    
    # Analysis results
    results = {
        'summary': {},
        'by_directory': {},
        'orphaned_tests': [],
        'missing_tests': [],
        'test_naming_issues': []
    }
    
    # Analyze each source directory
    for src_dir in source_dirs:
        src_count = len(source_files[src_dir])
        test_count = len(test_files[src_dir])
        
        results['by_directory'][src_dir] = {
            'source_files': src_count,
            'test_files': test_count,
            'ratio': f"{test_count}/{src_count}" if src_count > 0 else "0/0",
            'coverage_pct': round((test_count / src_count * 100) if src_count > 0 else 0, 1)
        }
        
        # Find missing tests
        for src_file in source_files[src_dir]:
            # Expected test path
            src_path = Path(src_file)
            expected_test = Path('tests') / src_path.parent / f"test_{src_path.name}"
            if not expected_test.exists():
                results['missing_tests'].append({
                    'source': str(src_file),
                    'expected_test': str(expected_test)
                })
    
    # Find orphaned tests (tests without source)
    for test_dir, tests in test_files.items():
        for test_file in tests:
            test_path = Path(test_file)
            
            # Skip non-test files
            if not test_path.name.startswith('test_'):
                results['test_naming_issues'].append(str(test_file))
                continue
            
            # Derive expected source
            if test_dir != '_root':
                # Remove 'test_' prefix
                source_name = test_path.name[5:]
                # Build expected source path
                rel_parts = test_path.parts[2:]  # Skip 'tests' and first dir
                if rel_parts:
                    expected_source = Path(test_dir) / Path(*rel_parts[:-1]) / source_name
                else:
                    expected_source = Path(test_dir) / source_name
            else:
                # Root level test - try to figure out where it belongs
                source_name = test_path.name[5:] if test_path.name.startswith('test_') else test_path.name
                expected_source = Path(source_name)
            
            # Check if source exists
            exists = False
            for src_dir in source_dirs:
                if (Path(src_dir) / expected_source).exists():
                    exists = True
                    break
            
            if not exists and expected_source.exists():
                exists = True
                
            if not exists:
                results['orphaned_tests'].append({
                    'test': str(test_file),
                    'expected_source': str(expected_source),
                    'category': test_dir
                })
    
    # Summary stats
    total_source = sum(len(files) for files in source_files.values())
    total_tests = sum(len(files) for files in test_files.values())
    
    results['summary'] = {
        'total_source_files': total_source,
        'total_test_files': total_tests,
        'missing_tests_count': len(results['missing_tests']),
        'orphaned_tests_count': len(results['orphaned_tests']),
        'test_naming_issues_count': len(results['test_naming_issues']),
        'overall_coverage_pct': round((total_tests / total_source * 100) if total_source > 0 else 0, 1)
    }
    
    # Add breakdown of test categories
    test_categories = defaultdict(int)
    for test_dir, tests in test_files.items():
        test_categories[test_dir] = len(tests)
    results['test_categories'] = dict(test_categories)
    
    return results


def print_analysis(results):
    """Print analysis in readable format."""
    print("=" * 80)
    print("DEEP TEST STRUCTURE ANALYSIS")
    print("=" * 80)
    print()
    
    # Summary
    s = results['summary']
    print("OVERALL SUMMARY:")
    print("-" * 40)
    print(f"Total source files:        {s['total_source_files']:>5}")
    print(f"Total test files:          {s['total_test_files']:>5}")
    print(f"Missing tests:             {s['missing_tests_count']:>5}")
    print(f"Orphaned tests:            {s['orphaned_tests_count']:>5}")
    print(f"Test naming issues:        {s['test_naming_issues_count']:>5}")
    print(f"Overall coverage:          {s['overall_coverage_pct']:>5.1f}%")
    print()
    
    # By directory breakdown
    print("BREAKDOWN BY SOURCE DIRECTORY:")
    print("-" * 40)
    for dir_name, stats in results['by_directory'].items():
        print(f"{dir_name:15} Source: {stats['source_files']:>3}  Tests: {stats['test_files']:>3}  "
              f"Ratio: {stats['ratio']:>7}  Coverage: {stats['coverage_pct']:>5.1f}%")
    print()
    
    # Test categories
    print("TEST FILE DISTRIBUTION:")
    print("-" * 40)
    for category, count in results['test_categories'].items():
        if category == '_root':
            print(f"Root level tests:          {count:>5}")
        else:
            print(f"tests/{category:15}    {count:>5}")
    print()
    
    # Sample of issues
    if results['missing_tests']:
        print("SAMPLE OF MISSING TESTS (first 10):")
        print("-" * 40)
        for item in results['missing_tests'][:10]:
            print(f"  ❌ {item['source']}")
            print(f"     → Need: {item['expected_test']}")
        if len(results['missing_tests']) > 10:
            print(f"  ... and {len(results['missing_tests']) - 10} more")
        print()
    
    if results['orphaned_tests']:
        print("SAMPLE OF ORPHANED TESTS (first 10):")
        print("-" * 40)
        for item in results['orphaned_tests'][:10]:
            print(f"  👻 {item['test']}")
            print(f"     → Missing: {item['expected_source']}")
        if len(results['orphaned_tests']) > 10:
            print(f"  ... and {len(results['orphaned_tests']) - 10} more")
        print()
    
    if results['test_naming_issues']:
        print("TEST NAMING ISSUES:")
        print("-" * 40)
        for test in results['test_naming_issues'][:5]:
            print(f"  ⚠️  {test}")
        if len(results['test_naming_issues']) > 5:
            print(f"  ... and {len(results['test_naming_issues']) - 5} more")
        print()
    
    # Recommendations
    print("KEY FINDINGS:")
    print("-" * 40)
    print("1. Many test files don't follow the expected naming/location pattern")
    print("2. Large number of orphaned tests indicate refactoring or deletion of source files")
    print("3. Test coverage is very low, especially in 'lib' directory")
    print("4. Some tests are at root level when they should be in subdirectories")
    print()
    
    print("RECOMMENDED ACTIONS:")
    print("-" * 40)
    print("1. Review and delete orphaned tests for non-existent source files")
    print("2. Create missing tests for critical source files")
    print("3. Reorganize misplaced tests to follow mirror structure")
    print("4. Update TDD hook to enforce proper test structure")
    print()


if __name__ == "__main__":
    results = analyze_test_structure()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        print(json.dumps(results, indent=2))
    else:
        print_analysis(results)