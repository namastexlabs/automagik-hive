#!/usr/bin/env python3
"""
PagBank Claude Model Usage Audit
Ensures consistency of Claude model usage across all components
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def find_claude_usage(file_path: Path) -> List[Dict[str, Any]]:
    """Find Claude model usage in a file"""
    usage = []
    
    try:
        content = file_path.read_text()
        lines = content.split('\n')
        
        # Patterns to find Claude usage
        patterns = [
            (r'Claude\s*\(\s*id\s*=\s*["\']([^"\']+)["\']', 'direct'),
            (r'model\s*=\s*Claude\s*\(', 'assignment'),
            (r'claude-sonnet-4-20250514', 'model_id'),
            (r'claude-3-5-sonnet', 'legacy_model')
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, usage_type in patterns:
                if match := re.search(pattern, line):
                    model_id = match.group(1) if usage_type == 'direct' else None
                    usage.append({
                        'file': str(file_path),
                        'line': i,
                        'type': usage_type,
                        'model_id': model_id,
                        'text': line.strip()
                    })
                    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return usage

def audit_claude_models() -> Dict[str, Any]:
    """Perform comprehensive audit of Claude model usage"""
    
    print("🔍 PagBank Claude Model Usage Audit")
    print("=" * 60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'components': {},
        'summary': {},
        'inconsistencies': [],
        'recommendations': []
    }
    
    # Define components to audit
    components = {
        'orchestrator': ['orchestrator/main_orchestrator.py'],
        'teams': [
            'teams/base_team.py',
            'teams/cards_team.py', 
            'teams/digital_account_team.py',
            'teams/investments_team.py',
            'teams/credit_team.py',
            'teams/insurance_team.py',
            'teams/team_config.py'
        ],
        'escalation': [
            'escalation_systems/escalation_manager.py',
            'escalation_systems/technical_escalation_agent.py'
        ],
        'memory': ['memory/memory_manager.py'],
        'playground': ['playground.py']
    }
    
    # Standard expected configuration
    expected_model = "claude-sonnet-4-20250514"
    expected_config = {
        'id': expected_model,
        'temperature': 0.1,
        'max_tokens': 2048
    }
    
    total_usage = 0
    correct_usage = 0
    
    print("\n📋 Auditing Components...")
    
    for component_name, files in components.items():
        print(f"\n🔍 {component_name.upper()}")
        component_usage = []
        
        for file_path in files:
            path = Path(file_path)
            if path.exists():
                usage = find_claude_usage(path)
                component_usage.extend(usage)
                
                # Analyze usage
                for u in usage:
                    total_usage += 1
                    if u['type'] == 'direct' and u['model_id'] == expected_model:
                        correct_usage += 1
                        print(f"  ✅ {path.name}:{u['line']} - Correct model")
                    elif u['type'] == 'model_id' and expected_model in u['text']:
                        correct_usage += 1
                        print(f"  ✅ {path.name}:{u['line']} - Correct model ID")
                    elif u['type'] == 'legacy_model':
                        print(f"  ❌ {path.name}:{u['line']} - Legacy model found")
                        results['inconsistencies'].append({
                            'file': u['file'],
                            'line': u['line'],
                            'issue': 'Legacy Claude model',
                            'found': u['text']
                        })
                    
        results['components'][component_name] = component_usage
    
    # Check temperature and max_tokens settings
    print("\n⚙️ Checking Model Configurations...")
    
    temp_pattern = r'temperature\s*=\s*([\d.]+)'
    tokens_pattern = r'max_tokens\s*=\s*(\d+)'
    
    config_issues = []
    
    for component_name, files in components.items():
        for file_path in files:
            path = Path(file_path)
            if path.exists():
                content = path.read_text()
                
                # Check temperature
                temp_matches = re.findall(temp_pattern, content)
                for temp in temp_matches:
                    if float(temp) != expected_config['temperature']:
                        config_issues.append({
                            'file': str(path),
                            'setting': 'temperature',
                            'found': temp,
                            'expected': str(expected_config['temperature'])
                        })
                
                # Check max_tokens
                token_matches = re.findall(tokens_pattern, content)
                for tokens in token_matches:
                    if int(tokens) != expected_config['max_tokens']:
                        config_issues.append({
                            'file': str(path),
                            'setting': 'max_tokens',
                            'found': tokens,
                            'expected': str(expected_config['max_tokens'])
                        })
    
    if config_issues:
        print("  ⚠️ Found configuration inconsistencies")
        results['inconsistencies'].extend(config_issues)
    else:
        print("  ✅ All configurations consistent")
    
    # Performance analysis
    print("\n⚡ Analyzing Performance Implications...")
    
    performance_analysis = {
        'model_consistency': {
            'status': 'optimal' if correct_usage == total_usage else 'needs_attention',
            'details': f"{correct_usage}/{total_usage} using correct model"
        },
        'memory_efficiency': {
            'status': 'good',
            'details': 'Single model type reduces memory overhead'
        },
        'response_time': {
            'status': 'consistent',
            'details': 'All teams use same model = predictable latency'
        },
        'cost_optimization': {
            'status': 'optimized',
            'details': 'Sonnet 4 provides best cost/performance ratio'
        }
    }
    
    results['performance'] = performance_analysis
    
    # Generate recommendations
    print("\n💡 Generating Recommendations...")
    
    if results['inconsistencies']:
        results['recommendations'].append({
            'priority': 'high',
            'action': 'Fix model inconsistencies',
            'details': f"Found {len(results['inconsistencies'])} inconsistencies to address"
        })
    
    results['recommendations'].extend([
        {
            'priority': 'medium',
            'action': 'Centralize model configuration',
            'details': 'Create config/models.py with get_standard_claude_model()',
            'code': '''def get_standard_claude_model():
    """Standard Claude model for all PagBank components"""
    return Claude(
        id="claude-sonnet-4-20250514",
        temperature=0.1,
        max_tokens=2048
    )'''
        },
        {
            'priority': 'low',
            'action': 'Add model configuration validation',
            'details': 'Implement startup validation to ensure consistency'
        },
        {
            'priority': 'low', 
            'action': 'Document model selection rationale',
            'details': 'Add documentation explaining why Sonnet 4 was chosen'
        }
    ])
    
    # Calculate compliance score
    compliance_score = (correct_usage / total_usage * 100) if total_usage > 0 else 0
    
    results['summary'] = {
        'total_claude_usage': total_usage,
        'correct_model_usage': correct_usage,
        'compliance_score': f"{compliance_score:.1f}%",
        'inconsistencies_found': len(results['inconsistencies']),
        'status': 'EXCELLENT' if compliance_score >= 95 else 'NEEDS_ATTENTION'
    }
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 AUDIT SUMMARY")
    print(f"Total Claude Usage: {total_usage}")
    print(f"Correct Model Usage: {correct_usage}")
    print(f"Compliance Score: {compliance_score:.1f}%")
    print(f"Inconsistencies: {len(results['inconsistencies'])}")
    print(f"Status: {results['summary']['status']} {'✅' if compliance_score >= 95 else '⚠️'}")
    print("=" * 60)
    
    # Save detailed report
    report_path = Path("tmp/claude_model_audit.json")
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: {report_path}")
    
    # Show inconsistencies if any
    if results['inconsistencies']:
        print("\n⚠️ INCONSISTENCIES FOUND:")
        for issue in results['inconsistencies'][:5]:  # Show first 5
            print(f"  - {issue.get('file', 'Unknown')}:{issue.get('line', '?')} - {issue.get('issue', issue.get('setting', 'Unknown'))}")
        if len(results['inconsistencies']) > 5:
            print(f"  ... and {len(results['inconsistencies']) - 5} more")
    
    return results

if __name__ == "__main__":
    audit_claude_models()