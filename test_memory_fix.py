#!/usr/bin/env python3
"""
NUCLEAR VALIDATION TEST - MemoryDb Fix Testing Script

This script validates the nuclear fix for the "WARNING MemoryDb not provided" issue.
Tests both the version factory path and fallback factory path to ensure memory
parameters are properly passed through all agent creation paths.
"""

import os
import sys
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Environment setup
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"
os.environ["CSV_HOT_RELOAD"] = "true"

# Required imports
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ dotenv not available, using existing environment variables")
    pass

# Import the components to test
from teams.ana.team import get_ana_team
from agents.registry import get_agent, AgentRegistry
from agents.version_factory import create_versioned_agent, agent_factory
from context.memory.memory_manager import create_memory_manager
from db.session import get_db


class MemoryFixTester:
    """Comprehensive tester for memory fix validation"""
    
    def __init__(self):
        self.test_results = []
        self.memory_manager = None
        self.session_id = "test_session_001"
        self.user_id = "test_user_001"
        
    def log_test(self, test_name: str, status: str, details: str = "", error: str = ""):
        """Log test results"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "error": error
        }
        self.test_results.append(result)
        
        # Console output
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def setup_memory_system(self) -> bool:
        """Setup shared memory system for testing"""
        try:
            print("🔧 Setting up memory system...")
            self.memory_manager = create_memory_manager()
            
            # Verify memory system components
            if not self.memory_manager.memory:
                raise ValueError("Memory object not created")
            
            if not self.memory_manager.memory_db:
                raise ValueError("Memory database not created")
            
            print(f"✅ Memory system initialized successfully")
            print(f"   - Memory object: {type(self.memory_manager.memory)}")
            print(f"   - Memory DB: {type(self.memory_manager.memory_db)}")
            print()
            
            return True
            
        except Exception as e:
            print(f"❌ Memory system setup failed: {e}")
            return False
    
    def test_version_factory_direct(self) -> bool:
        """Test version factory direct creation with memory"""
        try:
            print("🧪 Testing version factory direct creation...")
            
            # Create agent through version factory directly
            agent = agent_factory.create_agent(
                agent_id="pagbank-specialist",
                session_id=self.session_id,
                memory=self.memory_manager.memory,
                memory_db=self.memory_manager.memory_db
            )
            
            # Check if agent was created successfully
            if not agent:
                self.log_test("Version Factory Direct", "FAIL", "Agent creation returned None")
                return False
            
            # Check agent properties
            agent_memory = getattr(agent, 'memory', None)
            if not agent_memory:
                self.log_test("Version Factory Direct", "FAIL", "Agent has no memory attribute")
                return False
            
            # Check if memory has database
            memory_db = getattr(agent_memory, 'db', None)
            if not memory_db:
                self.log_test("Version Factory Direct", "FAIL", "Agent memory has no database")
                return False
            
            self.log_test("Version Factory Direct", "PASS", 
                         f"Agent created with memory: {type(agent_memory)}, db: {type(memory_db)}")
            return True
            
        except Exception as e:
            self.log_test("Version Factory Direct", "FAIL", error=str(e))
            return False
    
    def test_create_versioned_agent_function(self) -> bool:
        """Test create_versioned_agent function with memory"""
        try:
            print("🧪 Testing create_versioned_agent function...")
            
            # Create agent through convenience function
            agent = create_versioned_agent(
                agent_id="pagbank-specialist",
                session_id=self.session_id,
                memory=self.memory_manager.memory,
                memory_db=self.memory_manager.memory_db
            )
            
            # Check if agent was created successfully
            if not agent:
                self.log_test("Create Versioned Agent Function", "FAIL", "Agent creation returned None")
                return False
            
            # Check agent properties
            agent_memory = getattr(agent, 'memory', None)
            if not agent_memory:
                self.log_test("Create Versioned Agent Function", "FAIL", "Agent has no memory attribute")
                return False
            
            # Check if memory has database
            memory_db = getattr(agent_memory, 'db', None)
            if not memory_db:
                self.log_test("Create Versioned Agent Function", "FAIL", "Agent memory has no database")
                return False
            
            self.log_test("Create Versioned Agent Function", "PASS", 
                         f"Agent created with memory: {type(agent_memory)}, db: {type(memory_db)}")
            return True
            
        except Exception as e:
            self.log_test("Create Versioned Agent Function", "FAIL", error=str(e))
            return False
    
    def test_agent_registry_get_agent(self) -> bool:
        """Test AgentRegistry.get_agent with memory"""
        try:
            print("🧪 Testing AgentRegistry.get_agent...")
            
            # Create agent through registry
            agent = AgentRegistry.get_agent(
                agent_id="pagbank",
                session_id=self.session_id,
                memory=self.memory_manager.memory,
                memory_db=self.memory_manager.memory_db
            )
            
            # Check if agent was created successfully
            if not agent:
                self.log_test("Agent Registry Get Agent", "FAIL", "Agent creation returned None")
                return False
            
            # Check agent properties
            agent_memory = getattr(agent, 'memory', None)
            if not agent_memory:
                self.log_test("Agent Registry Get Agent", "FAIL", "Agent has no memory attribute")
                return False
            
            # Check if memory has database
            memory_db = getattr(agent_memory, 'db', None)
            if not memory_db:
                self.log_test("Agent Registry Get Agent", "FAIL", "Agent memory has no database")
                return False
            
            self.log_test("Agent Registry Get Agent", "PASS", 
                         f"Agent created with memory: {type(agent_memory)}, db: {type(memory_db)}")
            return True
            
        except Exception as e:
            self.log_test("Agent Registry Get Agent", "FAIL", error=str(e))
            return False
    
    def test_registry_get_agent_function(self) -> bool:
        """Test registry get_agent function with memory"""
        try:
            print("🧪 Testing registry get_agent function...")
            
            # Create agent through registry function
            agent = get_agent(
                name="pagbank",
                session_id=self.session_id,
                memory=self.memory_manager.memory,
                memory_db=self.memory_manager.memory_db
            )
            
            # Check if agent was created successfully
            if not agent:
                self.log_test("Registry Get Agent Function", "FAIL", "Agent creation returned None")
                return False
            
            # Check agent properties
            agent_memory = getattr(agent, 'memory', None)
            if not agent_memory:
                self.log_test("Registry Get Agent Function", "FAIL", "Agent has no memory attribute")
                return False
            
            # Check if memory has database
            memory_db = getattr(agent_memory, 'db', None)
            if not memory_db:
                self.log_test("Registry Get Agent Function", "FAIL", "Agent memory has no database")
                return False
            
            self.log_test("Registry Get Agent Function", "PASS", 
                         f"Agent created with memory: {type(agent_memory)}, db: {type(memory_db)}")
            return True
            
        except Exception as e:
            self.log_test("Registry Get Agent Function", "FAIL", error=str(e))
            return False
    
    def test_ana_team_agent_creation(self) -> bool:
        """Test Ana team agent creation with memory"""
        try:
            print("🧪 Testing Ana team agent creation...")
            
            # Create Ana team (this should create agents with memory)
            team = get_ana_team(
                session_id=self.session_id,
                user_id=self.user_id,
                debug_mode=True,
                agent_names=["pagbank"]  # Test with just one agent
            )
            
            # Check if team was created successfully
            if not team:
                self.log_test("Ana Team Agent Creation", "FAIL", "Team creation returned None")
                return False
            
            # Check team members
            if not team.members:
                self.log_test("Ana Team Agent Creation", "FAIL", "Team has no members")
                return False
            
            # Check first member agent
            agent = team.members[0]
            agent_memory = getattr(agent, 'memory', None)
            if not agent_memory:
                self.log_test("Ana Team Agent Creation", "FAIL", "Team member has no memory attribute")
                return False
            
            # Check if memory has database
            memory_db = getattr(agent_memory, 'db', None)
            if not memory_db:
                self.log_test("Ana Team Agent Creation", "FAIL", "Team member memory has no database")
                return False
            
            self.log_test("Ana Team Agent Creation", "PASS", 
                         f"Team created with {len(team.members)} members, first member has memory: {type(agent_memory)}, db: {type(memory_db)}")
            return True
            
        except Exception as e:
            self.log_test("Ana Team Agent Creation", "FAIL", error=str(e))
            return False
    
    def test_multiple_agents_consistency(self) -> bool:
        """Test multiple agents for memory consistency"""
        try:
            print("🧪 Testing multiple agents for memory consistency...")
            
            agent_names = ["pagbank", "adquirencia", "emissao"]
            agents = []
            
            for name in agent_names:
                try:
                    agent = get_agent(
                        name=name,
                        session_id=self.session_id,
                        memory=self.memory_manager.memory,
                        memory_db=self.memory_manager.memory_db
                    )
                    agents.append((name, agent))
                except Exception as e:
                    print(f"⚠️ Could not create {name} agent: {e}")
                    continue
            
            if not agents:
                self.log_test("Multiple Agents Consistency", "FAIL", "No agents could be created")
                return False
            
            # Check each agent has proper memory
            memory_issues = []
            for name, agent in agents:
                agent_memory = getattr(agent, 'memory', None)
                if not agent_memory:
                    memory_issues.append(f"{name}: no memory attribute")
                    continue
                
                memory_db = getattr(agent_memory, 'db', None)
                if not memory_db:
                    memory_issues.append(f"{name}: memory has no database")
                    continue
            
            if memory_issues:
                self.log_test("Multiple Agents Consistency", "FAIL", 
                             f"Memory issues found: {', '.join(memory_issues)}")
                return False
            
            self.log_test("Multiple Agents Consistency", "PASS", 
                         f"All {len(agents)} agents created with proper memory: {[name for name, _ in agents]}")
            return True
            
        except Exception as e:
            self.log_test("Multiple Agents Consistency", "FAIL", error=str(e))
            return False
    
    def test_warning_absence(self) -> bool:
        """Test for absence of MemoryDb warnings"""
        try:
            print("🧪 Testing for absence of MemoryDb warnings...")
            
            # Capture stderr to check for warnings
            import io
            import contextlib
            
            # Create a string buffer to capture output
            stderr_capture = io.StringIO()
            
            # Create agents and check for warnings
            with contextlib.redirect_stderr(stderr_capture):
                # Test version factory path
                agent1 = create_versioned_agent(
                    agent_id="pagbank-specialist",
                    session_id=self.session_id,
                    memory=self.memory_manager.memory,
                    memory_db=self.memory_manager.memory_db
                )
                
                # Test registry path
                agent2 = get_agent(
                    name="pagbank",
                    session_id=self.session_id,
                    memory=self.memory_manager.memory,
                    memory_db=self.memory_manager.memory_db
                )
            
            # Check captured output for warnings
            captured_output = stderr_capture.getvalue()
            
            if "WARNING MemoryDb not provided" in captured_output:
                self.log_test("Warning Absence", "FAIL", 
                             f"MemoryDb warning still present: {captured_output}")
                return False
            
            if "MemoryDb not provided" in captured_output:
                self.log_test("Warning Absence", "FAIL", 
                             f"MemoryDb warning detected: {captured_output}")
                return False
            
            self.log_test("Warning Absence", "PASS", 
                         "No MemoryDb warnings detected during agent creation")
            return True
            
        except Exception as e:
            self.log_test("Warning Absence", "FAIL", error=str(e))
            return False
    
    def test_memory_functionality(self) -> bool:
        """Test actual memory functionality"""
        try:
            print("🧪 Testing memory functionality...")
            
            # Create agent with memory
            agent = create_versioned_agent(
                agent_id="pagbank-specialist",
                session_id=self.session_id,
                memory=self.memory_manager.memory,
                memory_db=self.memory_manager.memory_db
            )
            
            # Test memory operations
            test_user_id = "test_user_memory"
            
            # Try to retrieve memories (this tests the database connection)
            try:
                memories = agent.memory.get_user_memories(user_id=test_user_id)
                
                # Check if memory object has database connection
                if not hasattr(agent.memory, 'db'):
                    self.log_test("Memory Functionality", "FAIL", "Agent memory has no database attribute")
                    return False
                
                if agent.memory.db is None:
                    self.log_test("Memory Functionality", "FAIL", "Agent memory database is None")
                    return False
                
                # Check if we can access the database
                try:
                    # Try to access the database through the memory object
                    # This is a basic connectivity test
                    table_name = getattr(agent.memory.db, 'table_name', 'memories')
                    if not table_name:
                        self.log_test("Memory Functionality", "FAIL", "Memory database has no table_name")
                        return False
                    
                    self.log_test("Memory Functionality", "PASS", 
                                 f"Memory database accessible: table={table_name}, memories_count={len(memories) if memories else 0}")
                    return True
                    
                except Exception as e:
                    self.log_test("Memory Functionality", "FAIL", f"Memory database access failed: {e}")
                    return False
                
            except Exception as e:
                self.log_test("Memory Functionality", "FAIL", f"Memory operation failed: {e}")
                return False
            
        except Exception as e:
            self.log_test("Memory Functionality", "FAIL", error=str(e))
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        print("=" * 80)
        print("🚀 NUCLEAR VALIDATION - Testing MemoryDb Fix")
        print("=" * 80)
        print()
        
        # Setup memory system
        if not self.setup_memory_system():
            print("❌ Memory system setup failed. Cannot run tests.")
            return {"status": "FAILED", "error": "Memory system setup failed"}
        
        # Run all tests
        tests = [
            self.test_version_factory_direct,
            self.test_create_versioned_agent_function,
            self.test_agent_registry_get_agent,
            self.test_registry_get_agent_function,
            self.test_ana_team_agent_creation,
            self.test_multiple_agents_consistency,
            self.test_warning_absence,
            self.test_memory_functionality
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            if test():
                passed += 1
            else:
                failed += 1
        
        # Print summary
        print("=" * 80)
        print("🎯 TEST SUMMARY")
        print("=" * 80)
        print(f"Total tests: {len(tests)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {(passed/len(tests)*100):.1f}%")
        print()
        
        # Print detailed results
        print("📊 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            status_emoji = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_emoji} {result['test_name']}: {result['status']}")
            if result["details"]:
                print(f"   {result['details']}")
            if result["error"]:
                print(f"   Error: {result['error']}")
        print()
        
        # Final assessment
        if failed == 0:
            print("🎉 NUCLEAR FIX VALIDATION: SUCCESS!")
            print("✅ All tests passed. The MemoryDb fix is working correctly.")
            print("✅ Memory parameters are properly flowing through all agent creation paths.")
            print("✅ No MemoryDb warnings should appear during normal operation.")
        else:
            print("⚠️ NUCLEAR FIX VALIDATION: ISSUES FOUND!")
            print(f"❌ {failed} tests failed. Memory fix may need additional work.")
        
        return {
            "status": "SUCCESS" if failed == 0 else "FAILED",
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "success_rate": passed/len(tests)*100,
            "detailed_results": self.test_results
        }


async def main():
    """Main test runner"""
    tester = MemoryFixTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["status"] == "SUCCESS":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())