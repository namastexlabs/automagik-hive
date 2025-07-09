#!/usr/bin/env python3
"""
Analyze test coverage for PagBank Multi-Agent System
Identifies critical untested paths and provides recommendations
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set

def find_test_files() -> List[Path]:
    """Find all test files in the project"""
    test_files = []
    for pattern in ['**/test_*.py', '**/*_test.py', '**/tests.py']:
        test_files.extend(Path('.').glob(pattern))
    
    # Filter out venv and archive
    return [f for f in test_files if not any(p in str(f) for p in ['.venv', 'genie/archive'])]

def find_source_files() -> List[Path]:
    """Find all source files (non-test Python files)"""
    all_py = list(Path('.').glob('**/*.py'))
    test_files = set(find_test_files())
    
    source_files = []
    for f in all_py:
        if f not in test_files and not any(p in str(f) for p in ['.venv', 'genie', 'test', '__pycache__']):
            source_files.append(f)
    
    return source_files

def analyze_test_coverage() -> Dict[str, Any]:
    """Analyze test coverage across the codebase"""
    
    print("🧪 PagBank Test Coverage Analysis")
    print("=" * 60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_files': {},
        'source_coverage': {},
        'critical_paths': {},
        'recommendations': []
    }
    
    # Find files
    test_files = find_test_files()
    source_files = find_source_files()
    
    print(f"\n📋 Found {len(test_files)} test files and {len(source_files)} source files")
    
    # Map test files to source files
    tested_modules = set()
    for test_file in test_files:
        test_name = test_file.stem
        if test_name.startswith('test_'):
            module_name = test_name[5:]  # Remove 'test_' prefix
            tested_modules.add(module_name)
            results['test_files'][str(test_file)] = {
                'module': module_name,
                'path': str(test_file)
            }
    
    # Analyze source file coverage
    covered_files = 0
    uncovered_critical = []
    
    critical_modules = {
        'main_orchestrator': 'Core routing logic',
        'routing_logic': 'Team selection algorithms',
        'frustration_detector': 'Customer frustration detection',
        'clarification_handler': 'Query clarification logic',
        'csv_knowledge_base': 'Knowledge retrieval',
        'memory_manager': 'Memory persistence',
        'pattern_detector': 'Pattern recognition',
        'base_team': 'Team coordination framework',
        'escalation_manager': 'Escalation workflows',
        'technical_escalation_agent': 'Technical issue handling'
    }
    
    for source_file in source_files:
        module_name = source_file.stem
        is_covered = module_name in tested_modules or any(test in str(source_file) for test in ['conftest'])
        
        if is_covered:
            covered_files += 1
            
        results['source_coverage'][str(source_file)] = {
            'module': module_name,
            'covered': is_covered,
            'critical': module_name in critical_modules
        }
        
        if module_name in critical_modules and not is_covered:
            uncovered_critical.append({
                'module': module_name,
                'description': critical_modules[module_name],
                'path': str(source_file)
            })
    
    # Calculate coverage metrics
    coverage_rate = (covered_files / len(source_files) * 100) if source_files else 0
    
    # Analyze critical paths
    print("\n🎯 Critical Path Analysis...")
    
    critical_paths = {
        'orchestration': {
            'description': 'Customer query routing and team selection',
            'components': ['main_orchestrator', 'routing_logic', 'clarification_handler'],
            'coverage': 0,
            'priority': 'CRITICAL'
        },
        'knowledge_retrieval': {
            'description': 'Knowledge base search and filtering',
            'components': ['csv_knowledge_base', 'knowledge_parser', 'agentic_filters'],
            'coverage': 0,
            'priority': 'HIGH'
        },
        'memory_system': {
            'description': 'User memory and pattern detection',
            'components': ['memory_manager', 'pattern_detector', 'session_manager'],
            'coverage': 0,
            'priority': 'HIGH'
        },
        'team_coordination': {
            'description': 'Multi-agent team collaboration',
            'components': ['base_team', 'team_tools', 'shared_state_tools'],
            'coverage': 0,
            'priority': 'HIGH'
        },
        'fraud_detection': {
            'description': 'Fraud and scam detection in teams',
            'components': ['credit_team', 'cards_team'],
            'coverage': 0,
            'priority': 'CRITICAL'
        },
        'escalation': {
            'description': 'Human handoff and technical escalation',
            'components': ['escalation_manager', 'technical_escalation_agent', 'ticket_system'],
            'coverage': 0,
            'priority': 'MEDIUM'
        }
    }
    
    # Calculate critical path coverage
    for path_name, path_info in critical_paths.items():
        covered_components = 0
        for component in path_info['components']:
            if any(component in str(f) for f in test_files):
                covered_components += 1
        
        path_info['coverage'] = (covered_components / len(path_info['components']) * 100) if path_info['components'] else 0
        path_info['covered_components'] = covered_components
        path_info['total_components'] = len(path_info['components'])
    
    results['critical_paths'] = critical_paths
    
    # Generate recommendations
    print("\n💡 Generating Test Recommendations...")
    
    # Priority 1: Critical untested modules
    if uncovered_critical:
        results['recommendations'].append({
            'priority': 1,
            'category': 'Critical Modules',
            'action': 'Create unit tests for critical untested modules',
            'modules': [m['module'] for m in uncovered_critical[:5]],
            'impact': 'Essential for system reliability'
        })
    
    # Priority 2: Integration tests
    results['recommendations'].append({
        'priority': 2,
        'category': 'Integration Tests',
        'action': 'Create integration tests for key workflows',
        'tests': [
            'test_orchestrator_to_team_routing',
            'test_knowledge_filtering_per_team',
            'test_memory_persistence_across_sessions',
            'test_escalation_workflow_complete'
        ],
        'impact': 'Validates system component interactions'
    })
    
    # Priority 3: Portuguese language tests
    results['recommendations'].append({
        'priority': 3,
        'category': 'Language Tests',
        'action': 'Add Portuguese language edge case tests',
        'tests': [
            'test_portuguese_text_normalization',
            'test_accent_handling',
            'test_informal_language_detection',
            'test_typo_correction'
        ],
        'impact': 'Critical for Brazilian market'
    })
    
    # Priority 4: Performance tests
    results['recommendations'].append({
        'priority': 4,
        'category': 'Performance Tests',
        'action': 'Create performance benchmarks',
        'tests': [
            'test_response_time_under_2s',
            'test_knowledge_search_performance',
            'test_concurrent_user_handling',
            'test_memory_retrieval_speed'
        ],
        'impact': 'Ensures demo readiness'
    })
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST COVERAGE SUMMARY")
    print(f"Overall Coverage: {coverage_rate:.1f}%")
    print(f"Test Files: {len(test_files)}")
    print(f"Source Files: {len(source_files)}")
    print(f"Covered Files: {covered_files}")
    print(f"Critical Untested: {len(uncovered_critical)}")
    
    print("\n🎯 Critical Path Coverage:")
    for path_name, path_info in critical_paths.items():
        status = "✅" if path_info['coverage'] > 50 else "❌"
        print(f"  {status} {path_name}: {path_info['coverage']:.0f}% ({path_info['covered_components']}/{path_info['total_components']})")
    
    print("\n⚠️ Top Untested Critical Modules:")
    for module in uncovered_critical[:5]:
        print(f"  - {module['module']}: {module['description']}")
    
    # Save detailed report
    report_path = Path("tmp/test_coverage_analysis.json")
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: {report_path}")
    
    # Create test implementation plan
    create_test_implementation_plan(results)
    
    return results

def create_test_implementation_plan(analysis: Dict[str, Any]):
    """Create a test implementation plan based on analysis"""
    
    plan_path = Path("tmp/test_implementation_plan.md")
    
    with open(plan_path, 'w') as f:
        f.write("# PagBank Test Implementation Plan\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Priority 1: Critical Unit Tests (Week 1)\n\n")
        f.write("### Core Orchestration\n")
        f.write("- [ ] `tests/unit/test_main_orchestrator.py`\n")
        f.write("  - Test routing decisions\n")
        f.write("  - Test frustration detection integration\n")
        f.write("  - Test clarification handling\n\n")
        
        f.write("### Knowledge System\n")
        f.write("- [ ] `tests/unit/test_csv_knowledge_base.py`\n")
        f.write("  - Test team-specific filtering\n")
        f.write("  - Test search accuracy\n")
        f.write("  - Test Portuguese query handling\n\n")
        
        f.write("### Memory System\n")
        f.write("- [ ] `tests/unit/test_memory_manager.py`\n")
        f.write("  - Test user memory persistence\n")
        f.write("  - Test pattern detection\n")
        f.write("  - Test session management\n\n")
        
        f.write("## Priority 2: Integration Tests (Week 2)\n\n")
        f.write("- [ ] `tests/integration/test_orchestrator_routing.py`\n")
        f.write("- [ ] `tests/integration/test_team_coordination.py`\n")
        f.write("- [ ] `tests/integration/test_escalation_flow.py`\n")
        f.write("- [ ] `tests/integration/test_customer_journey.py`\n\n")
        
        f.write("## Priority 3: System Tests (Week 3)\n\n")
        f.write("- [ ] `tests/system/test_complete_flows.py`\n")
        f.write("- [ ] `tests/system/test_portuguese_support.py`\n")
        f.write("- [ ] `tests/performance/test_benchmarks.py`\n\n")
        
        f.write("## Test Infrastructure Setup\n\n")
        f.write("```python\n")
        f.write("# conftest.py additions needed:\n")
        f.write("- Mock knowledge base fixture\n")
        f.write("- Test memory manager fixture\n")
        f.write("- Mock team fixtures\n")
        f.write("- Portuguese test data fixture\n")
        f.write("```\n\n")
        
        f.write("## Success Criteria\n\n")
        f.write("- Critical path coverage: >80%\n")
        f.write("- Overall test coverage: >70%\n")
        f.write("- All fraud detection tested\n")
        f.write("- Portuguese edge cases covered\n")
        f.write("- Performance benchmarks met (<2s response)\n")
    
    print(f"\n📝 Test implementation plan created: {plan_path}")

if __name__ == "__main__":
    analyze_test_coverage()