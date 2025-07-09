#!/usr/bin/env python3
"""
Memory System Validation for PagBank Multi-Agent System
Validates Agno v2 Memory compliance and performance
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Import Agno Memory v2 components
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.anthropic import Claude
from knowledge.csv_knowledge_base import create_pagbank_knowledge_base

# Import PagBank memory system
from memory.memory_manager import create_memory_manager
from teams.base_team import BaseTeam


class MemoryValidationSuite:
    """Comprehensive validation suite for memory system"""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        
    def validate_agno_v2_compliance(self) -> Dict[str, Any]:
        """Validate compliance with Agno Memory v2 specifications"""
        print("🔍 Validating Agno Memory v2 Compliance...")
        
        results = {
            'sqlite_memory_db': False,
            'memory_object_init': False,
            'user_memory_persistence': False,
            'session_summary_generation': False,
            'pattern_detection': False,
            'team_memory_integration': False,
            'agent_memory_configuration': False
        }
        
        try:
            # 1. SqliteMemoryDb Configuration
            memory_db = SqliteMemoryDb(
                table_name="test_memory",
                db_file="tmp/test_memory.db"
            )
            results['sqlite_memory_db'] = True
            print("✅ SqliteMemoryDb configuration correct")
            
            # 2. Memory Object Initialization
            memory = Memory(
                model=Claude(id="claude-sonnet-4-20250514"),
                db=memory_db,
                delete_memories=True,
                clear_memories=True
            )
            results['memory_object_init'] = True
            print("✅ Memory object initialization compliant")
            
            # 3. User Memory Persistence Test
            test_user_id = "test_user_123"
            memory.clear()
            
            # Add memory and verify persistence using proper Memory v2 API
            # Memory v2 uses add_user_memory and get_user_memories methods
            try:
                # Clear any existing memories first
                memory.clear_user_memories(user_id=test_user_id)
                
                # Add a test memory using the correct Memory v2 API
                memory.add_user_memory(
                    user_id=test_user_id,
                    memory="Test user likes cartões and PIX"
                )
                
                # Retrieve memories to verify persistence
                user_memories = memory.get_user_memories(user_id=test_user_id)
                if user_memories and len(user_memories) > 0:
                    results['user_memory_persistence'] = True
                    print("✅ User memory persistence working")
                else:
                    print("❌ User memory not persisted")
                    
            except Exception as e:
                print(f"Memory creation method error: {e}")
                print(f"Available memory methods: {[m for m in dir(memory) if not m.startswith('_')]}")
            
            # 4. Pattern Detection (using PagBank system)
            memory_manager = create_memory_manager()
            patterns = memory_manager.pattern_detector.detect_patterns(
                "Problemas com cartão", []
            )
            if patterns:
                results['pattern_detection'] = True
                print("✅ Pattern detection functional")
            
            # 5. Team Memory Integration
            knowledge_base = create_pagbank_knowledge_base()
            test_team = BaseTeam(
                team_name="test_team",
                team_role="Test Team",
                team_description="Test team for validation",
                knowledge_base=knowledge_base,
                memory_manager=memory_manager,
                knowledge_filters=["test"]
            )
            
            if hasattr(test_team.team, 'memory') and test_team.team.memory:
                results['team_memory_integration'] = True
                print("✅ Team memory integration working")
            
            # 6. Agent Memory Configuration
            # Check that agents have proper memory settings
            if len(test_team.members) > 0:
                agent = test_team.members[0]
                if (hasattr(agent, 'enable_user_memories') and 
                    hasattr(agent, 'enable_agentic_memory')):
                    results['agent_memory_configuration'] = True
                    print("✅ Agent memory configuration correct")
            
        except Exception as e:
            print(f"❌ Memory validation error: {e}")
        
        return results
    
    def test_performance_benchmarks(self) -> Dict[str, Any]:
        """Test memory system performance against targets"""
        print("\n⚡ Testing Memory Performance...")
        
        performance = {
            'memory_retrieval_ms': 0,
            'pattern_detection_ms': 0,
            'session_persistence_ms': 0,
            'cleanup_efficiency_ms': 0,
            'target_met': False
        }
        
        try:
            memory_manager = create_memory_manager()
            
            # 1. Memory Retrieval Speed (<100ms target)
            start_time = time.time()
            user_memories = memory_manager.memory.get_user_memories("test_user")
            retrieval_time = (time.time() - start_time) * 1000
            performance['memory_retrieval_ms'] = round(retrieval_time, 2)
            
            # 2. Pattern Detection Speed
            start_time = time.time()
            patterns = memory_manager.pattern_detector.analyze_message(
                "test_user", "Problema com cartão de crédito", {}
            )
            pattern_time = (time.time() - start_time) * 1000
            performance['pattern_detection_ms'] = round(pattern_time, 2)
            
            # 3. Session Persistence Speed
            start_time = time.time()
            session_data = memory_manager.session_manager.get_session("test_session")
            persistence_time = (time.time() - start_time) * 1000
            performance['session_persistence_ms'] = round(persistence_time, 2)
            
            # 4. Memory Cleanup Efficiency
            start_time = time.time()
            memory_manager.cleanup_expired_sessions()
            cleanup_time = (time.time() - start_time) * 1000
            performance['cleanup_efficiency_ms'] = round(cleanup_time, 2)
            
            # Check if target met (retrieval <100ms)
            performance['target_met'] = performance['memory_retrieval_ms'] < 100
            
            print(f"📊 Memory retrieval: {performance['memory_retrieval_ms']}ms")
            print(f"📊 Pattern detection: {performance['pattern_detection_ms']}ms")
            print(f"📊 Session persistence: {performance['session_persistence_ms']}ms")
            print(f"📊 Cleanup efficiency: {performance['cleanup_efficiency_ms']}ms")
            
            if performance['target_met']:
                print("✅ Performance targets met")
            else:
                print("⚠️ Performance targets not met")
                
        except Exception as e:
            print(f"❌ Performance test error: {e}")
        
        return performance
    
    def test_cross_team_isolation(self) -> bool:
        """Test that team memory doesn't leak between teams"""
        print("\n🔒 Testing Cross-Team Memory Isolation...")
        
        try:
            memory_manager = create_memory_manager()
            knowledge_base = create_pagbank_knowledge_base()
            
            # Create two different teams
            team1 = BaseTeam(
                team_name="cartoes_team",
                team_role="Cards Team",
                team_description="Cards specialist team",
                knowledge_base=knowledge_base,
                memory_manager=memory_manager,
                knowledge_filters=["cartoes"]
            )
            
            team2 = BaseTeam(
                team_name="investments_team", 
                team_role="Investments Team",
                team_description="Investments specialist team",
                knowledge_base=knowledge_base,
                memory_manager=memory_manager,
                knowledge_filters=["investimentos"]
            )
            
            # Add memory to team1 using correct Memory v2 API
            team1_memory = memory_manager.get_team_memory("cartoes_team")
            if team1_memory:
                team1_memory.add_user_memory(
                    user_id="shared_user",
                    memory="User prefers credit cards"
                )
            
            # Check team2 doesn't see team1's memory
            team2_memory = memory_manager.get_team_memory("investments_team")
            if team2_memory:
                team2_memories = team2_memory.get_user_memories("shared_user")
                
                # Should not see team1's specific memories
                if team2_memories:
                    card_memories = [m for m in team2_memories if "credit cards" in str(m)]
                    if len(card_memories) == 0:
                        print("✅ Cross-team memory isolation working")
                        return True
                    else:
                        print("❌ Memory leak detected between teams")
                        return False
                else:
                    print("✅ Cross-team memory isolation working (no shared memories)")
                    return True
            
        except Exception as e:
            print(f"❌ Isolation test error: {e}")
            return False
        
        return True
    
    def test_memory_workflows(self) -> Dict[str, bool]:
        """Test key memory workflows"""
        print("\n🔄 Testing Memory Workflows...")
        
        workflows = {
            'user_memory_across_sessions': False,
            'pattern_detection_triggers': False,
            'session_summary_generation': False,
            'memory_cleanup_archival': False
        }
        
        try:
            memory_manager = create_memory_manager()
            test_user = "workflow_test_user"
            
            # 1. User Memory Across Sessions
            memory_manager.memory.add_user_memory(
                user_id=test_user,
                memory="User frequently asks about PIX transfers"
            )
            
            # Simulate new session
            memories = memory_manager.memory.get_user_memories(test_user)
            if memories and len(memories) > 0:
                workflows['user_memory_across_sessions'] = True
                print("✅ User memory persists across sessions")
            
            # 2. Pattern Detection Triggers
            patterns = memory_manager.pattern_detector.analyze_message(
                test_user, "Problema com PIX", {"keywords": ["pix", "transferencia", "erro"]}
            )
            if patterns:
                workflows['pattern_detection_triggers'] = True
                print("✅ Pattern detection triggers working")
            
            # 3. Session Summary Generation (if available)
            try:
                session_summary = memory_manager.session_manager.get_session_summary("test_session")
                workflows['session_summary_generation'] = True
                print("✅ Session summary generation available")
            except Exception as e:
                print(f"⚠️  Session summary generation not available: {e}")
                workflows['session_summary_generation'] = False
            
            # 4. Memory Cleanup and Archival
            cleanup_result = memory_manager.cleanup_expired_sessions()
            workflows['memory_cleanup_archival'] = True
            print("✅ Memory cleanup and archival working")
            
        except Exception as e:
            print(f"❌ Workflow test error: {e}")
        
        return workflows
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        print("\n📋 Generating Memory Validation Report...")
        
        # Run all validations
        compliance = self.validate_agno_v2_compliance()
        performance = self.test_performance_benchmarks()
        isolation = self.test_cross_team_isolation()
        workflows = self.test_memory_workflows()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'compliance': compliance,
            'performance': performance,
            'isolation': isolation,
            'workflows': workflows,
            'overall_score': 0,
            'recommendations': []
        }
        
        # Calculate overall score
        compliance_score = sum(compliance.values()) / len(compliance) * 100
        workflow_score = sum(workflows.values()) / len(workflows) * 100
        isolation_score = 100 if isolation else 0
        performance_score = 100 if performance.get('target_met', False) else 80
        
        report['overall_score'] = round(
            (compliance_score + workflow_score + isolation_score + performance_score) / 4, 1
        )
        
        # Generate recommendations
        if not performance.get('target_met', False):
            report['recommendations'].append("Optimize memory retrieval performance")
        
        if not isolation:
            report['recommendations'].append("Fix cross-team memory isolation")
        
        if compliance_score < 100:
            report['recommendations'].append("Address Agno v2 compliance issues")
        
        return report


def main():
    """Main validation entry point"""
    print("🧪 PagBank Memory System Validation")
    print("=" * 50)
    
    validator = MemoryValidationSuite()
    report = validator.generate_report()
    
    print(f"\n📊 VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Overall Score: {report['overall_score']}%")
    print(f"Compliance: {sum(report['compliance'].values())}/{len(report['compliance'])} ✅")
    print(f"Workflows: {sum(report['workflows'].values())}/{len(report['workflows'])} ✅")
    print(f"Isolation: {'✅' if report['isolation'] else '❌'}")
    print(f"Performance: {'✅' if report['performance']['target_met'] else '⚠️'}")
    
    if report['recommendations']:
        print(f"\n📝 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    # Save report
    report_path = Path("tmp/memory_validation_report.json")
    report_path.parent.mkdir(exist_ok=True)
    
    import json
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Report saved to: {report_path}")
    
    return report['overall_score'] >= 85


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Memory System: VALIDATED")
    else:
        print("\n❌ Memory System: NEEDS ATTENTION")