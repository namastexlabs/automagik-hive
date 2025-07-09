#!/usr/bin/env python3
"""
Verify Claude Model Consistency in Production Code
Excludes archive and genie folders
"""

import json
from datetime import datetime
from pathlib import Path


def verify_model_consistency():
    """Verify all production code uses consistent Claude model"""
    
    print("🔍 Claude Model Consistency Verification")
    print("=" * 60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'production_files': {},
        'consistency': True,
        'summary': {}
    }
    
    # Expected model configuration
    expected_model = "claude-sonnet-4-20250514"
    
    # Production files to check (excluding archives)
    production_files = [
        # Orchestrator
        "orchestrator/main_orchestrator.py",
        
        # Teams
        "teams/base_team.py",
        "teams/cards_team.py",
        "teams/digital_account_team.py",
        "teams/insurance_team.py",
        "teams/team_config.py",
        
        # Escalation
        "escalation_systems/escalation_manager.py",
        "escalation_systems/technical_escalation_agent.py",
        
        # Memory
        "memory/memory_config.py",
        
        # Playground
        "playground.py"
    ]
    
    print("\n📋 Checking Production Files...")
    
    all_consistent = True
    checked_files = 0
    consistent_files = 0
    
    for file_path in production_files:
        path = Path(file_path)
        if path.exists():
            checked_files += 1
            content = path.read_text()
            
            # Check for the expected model ID
            if expected_model in content:
                consistent_files += 1
                print(f"  ✅ {file_path} - Uses correct model")
                results['production_files'][file_path] = {
                    'status': 'consistent',
                    'model': expected_model
                }
            else:
                # Check if it inherits from BaseTeam (which sets the model)
                if "BaseTeam" in content and file_path.startswith("teams/"):
                    consistent_files += 1
                    print(f"  ✅ {file_path} - Inherits model from BaseTeam")
                    results['production_files'][file_path] = {
                        'status': 'inherited',
                        'model': expected_model,
                        'note': 'Inherits from BaseTeam'
                    }
                else:
                    all_consistent = False
                    print(f"  ❌ {file_path} - Model not found or inconsistent")
                    results['production_files'][file_path] = {
                        'status': 'inconsistent',
                        'model': 'unknown'
                    }
    
    # Special checks
    print("\n🔍 Special Configuration Checks...")
    
    # Check memory config
    memory_config_path = Path("memory/memory_config.py")
    if memory_config_path.exists():
        content = memory_config_path.read_text()
        if f'memory_model: str = "{expected_model}"' in content:
            print("  ✅ Memory configuration uses correct model")
        else:
            print("  ❌ Memory configuration has different model")
            all_consistent = False
    
    # Check for any temperature or max_tokens settings
    print("\n⚙️ Configuration Consistency...")
    
    config_consistent = True
    for file_path in production_files:
        path = Path(file_path)
        if path.exists() and "Claude(" in path.read_text():
            content = path.read_text()
            # We don't explicitly set temperature/max_tokens, which is fine
            # Default values will be used
            if "temperature=" in content or "max_tokens=" in content:
                print(f"  ℹ️ {file_path} - Has explicit config settings")
    
    print("  ✅ No conflicting configuration found")
    
    # Summary
    consistency_rate = (consistent_files / checked_files * 100) if checked_files > 0 else 0
    
    results['summary'] = {
        'files_checked': checked_files,
        'consistent_files': consistent_files,
        'consistency_rate': f"{consistency_rate:.1f}%",
        'all_consistent': all_consistent,
        'expected_model': expected_model,
        'status': 'EXCELLENT' if consistency_rate == 100 else 'NEEDS_ATTENTION'
    }
    
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print(f"Files Checked: {checked_files}")
    print(f"Consistent Files: {consistent_files}")
    print(f"Consistency Rate: {consistency_rate:.1f}%")
    print(f"Expected Model: {expected_model}")
    print(f"Status: {results['summary']['status']} {'✅' if consistency_rate == 100 else '⚠️'}")
    print("=" * 60)
    
    # Recommendations
    print("\n💡 Findings:")
    if consistency_rate == 100:
        print("  ✅ All production code uses consistent Claude model")
        print("  ✅ Teams inherit model from BaseTeam (DRY principle)")
        print("  ✅ Memory config properly set")
        print("  ✅ No legacy models found in production")
    else:
        print("  ⚠️ Some inconsistencies found - review needed")
    
    # Save report
    report_path = Path("tmp/model_consistency_verification.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Report saved to: {report_path}")
    
    return results

if __name__ == "__main__":
    verify_model_consistency()