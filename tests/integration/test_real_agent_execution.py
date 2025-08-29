"""
REAL INTEGRATION TESTS - No Mocking Bullshit

Tests that actually spawn agents, execute workflows, and validate real system behavior.
This is what should have been done from the start.
"""

import asyncio
import time
import pytest
from pathlib import Path

from ai.agents.registry import AgentRegistry
# from ai.teams.registry import TeamRegistry  # Check if this exists
from lib.config.settings import get_settings


class TestRealAgentExecution:
    """Test actual agent execution without mocks."""
    
    def test_system_configuration_is_valid(self):
        """Verify the system can load without configuration errors."""
        try:
            settings = get_settings()
            assert settings.hive_api_key.startswith("hive_")
            assert settings.hive_environment in ["development", "staging", "production"]
        except Exception as e:
            pytest.fail(f"System configuration failed: {e}")
    
    def test_agent_discovery_finds_real_agents(self):
        """Test agent discovery finds actual agent configs."""
        agents_dir = Path("ai/agents")
        assert agents_dir.exists(), "Agents directory missing"
        
        # Find real agent configs
        config_files = list(agents_dir.glob("*/config.yaml"))
        assert len(config_files) > 0, "No agent configs found"
        
        # Test registry can discover them
        try:
            available_agents = AgentRegistry.list_available_agents()
            assert len(available_agents) > 0, "Registry found no agents"
            print(f"✅ Discovered {len(available_agents)} agents: {available_agents}")
        except Exception as e:
            pytest.fail(f"Agent discovery failed: {e}")
    
    @pytest.mark.asyncio
    async def test_can_create_real_agent(self):
        """Test creating an actual agent instance."""
        try:
            available_agents = AgentRegistry.list_available_agents()
            if not available_agents:
                pytest.skip("No agents available for testing")
            
            # Try to create the first available agent
            agent_id = available_agents[0]
            print(f"🧪 Testing agent creation: {agent_id}")
            
            start_time = time.time()
            agent = await AgentRegistry.get_agent(agent_id)
            creation_time = time.time() - start_time
            
            assert agent is not None, f"Failed to create agent {agent_id}"
            assert hasattr(agent, 'agent_id'), "Agent missing agent_id attribute"
            assert creation_time < 5.0, f"Agent creation too slow: {creation_time}s"
            
            print(f"✅ Created agent {agent_id} in {creation_time:.2f}s")
            
        except Exception as e:
            pytest.fail(f"Real agent creation failed: {e}")
    
    @pytest.mark.asyncio
    async def test_agent_can_process_simple_message(self):
        """Test agent can actually process a message (not mocked)."""
        try:
            available_agents = AgentRegistry.list_available_agents()
            if not available_agents:
                pytest.skip("No agents available for testing")
            
            agent_id = available_agents[0]
            agent = await AgentRegistry.get_agent(agent_id)
            
            # Try to send a simple message
            test_message = "Hello, can you respond to this test message?"
            print(f"🧪 Testing message processing with {agent_id}")
            
            start_time = time.time()
            
            # Different agents might have different interfaces
            if hasattr(agent, 'arun'):
                response = await agent.arun(test_message)
            elif hasattr(agent, 'run'):
                response = agent.run(test_message)  
            elif hasattr(agent, 'process'):
                response = await agent.process(test_message)
            else:
                pytest.fail(f"Agent {agent_id} has no known execution method")
            
            processing_time = time.time() - start_time
            
            assert response is not None, "Agent returned None response"
            assert processing_time < 30.0, f"Response too slow: {processing_time}s"
            
            print(f"✅ Agent responded in {processing_time:.2f}s")
            print(f"   Response type: {type(response)}")
            
            # Try to extract actual response content
            if hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'text'):
                content = response.text
            elif isinstance(response, str):
                content = response
            else:
                content = str(response)
            
            assert len(content) > 0, "Agent returned empty response"
            print(f"   Response preview: {content[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Real message processing failed: {e}")
    
    @pytest.mark.asyncio
    async def test_multiple_agents_concurrent_creation(self):
        """Test creating multiple agents concurrently."""
        try:
            available_agents = AgentRegistry.list_available_agents()
            if len(available_agents) < 2:
                pytest.skip("Need at least 2 agents for concurrency test")
            
            # Test concurrent creation of first 3 agents (or all if fewer)
            test_agents = available_agents[:min(3, len(available_agents))]
            print(f"🧪 Testing concurrent creation of {len(test_agents)} agents")
            
            start_time = time.time()
            
            # Create all agents concurrently
            tasks = [AgentRegistry.get_agent(agent_id) for agent_id in test_agents]
            agents = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = time.time() - start_time
            
            # Check results
            successful_agents = [a for a in agents if not isinstance(a, Exception)]
            failed_agents = [a for a in agents if isinstance(a, Exception)]
            
            assert len(successful_agents) > 0, "No agents created successfully"
            assert total_time < 15.0, f"Concurrent creation too slow: {total_time}s"
            
            print(f"✅ Created {len(successful_agents)}/{len(test_agents)} agents in {total_time:.2f}s")
            
            if failed_agents:
                print(f"⚠️  {len(failed_agents)} agents failed:")
                for i, error in enumerate(failed_agents):
                    print(f"   {test_agents[i]}: {error}")
            
        except Exception as e:
            pytest.fail(f"Concurrent agent creation failed: {e}")
    
    def test_team_configs_exist(self):
        """Test team configs exist (registry interface TBD)."""
        teams_dir = Path("ai/teams")
        if not teams_dir.exists():
            pytest.skip("Teams directory missing")
        
        # Find real team configs
        config_files = list(teams_dir.glob("*/config.yaml"))
        if len(config_files) == 0:
            pytest.skip("No team configs found")
        
        print(f"✅ Found {len(config_files)} team configs")
        for config_file in config_files[:3]:  # Show first 3
            print(f"   - {config_file.parent.name}")


class TestRealPerformanceLimits:
    """Test actual performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_agent_creation_performance(self):
        """Test agent creation meets performance requirements."""
        try:
            available_agents = AgentRegistry.list_available_agents()
            if not available_agents:
                pytest.skip("No agents available")
            
            agent_id = available_agents[0]
            
            # Test multiple creations for average
            times = []
            for i in range(3):
                start = time.time()
                agent = await AgentRegistry.get_agent(agent_id)
                creation_time = time.time() - start
                times.append(creation_time)
                assert agent is not None
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            
            print(f"✅ Agent creation times: avg={avg_time:.2f}s, max={max_time:.2f}s")
            
            # Performance requirements
            assert avg_time < 3.0, f"Average creation time too slow: {avg_time}s"
            assert max_time < 5.0, f"Worst case creation time too slow: {max_time}s"
            
        except Exception as e:
            pytest.fail(f"Performance testing failed: {e}")
    
    @pytest.mark.asyncio 
    async def test_system_handles_rapid_requests(self):
        """Test system can handle rapid successive requests."""
        try:
            available_agents = AgentRegistry.list_available_agents()
            if not available_agents:
                pytest.skip("No agents available")
            
            agent_id = available_agents[0]
            agent = await AgentRegistry.get_agent(agent_id)
            
            # Send 5 rapid requests
            requests = []
            start_time = time.time()
            
            for i in range(5):
                if hasattr(agent, 'arun'):
                    request = agent.arun(f"Request {i+1}")
                elif hasattr(agent, 'run'):
                    request = asyncio.create_task(asyncio.to_thread(agent.run, f"Request {i+1}"))
                else:
                    pytest.skip(f"Agent {agent_id} has no testable execution method")
                requests.append(request)
            
            # Wait for all requests
            responses = await asyncio.gather(*requests, return_exceptions=True)
            total_time = time.time() - start_time
            
            successful = [r for r in responses if not isinstance(r, Exception)]
            failed = [r for r in responses if isinstance(r, Exception)]
            
            print(f"✅ Rapid requests: {len(successful)}/5 successful in {total_time:.2f}s")
            
            assert len(successful) >= 3, f"Too many failed requests: {len(failed)}/5"
            assert total_time < 60.0, f"Rapid requests took too long: {total_time}s"
            
        except Exception as e:
            pytest.fail(f"Rapid request testing failed: {e}")


class TestRealSystemHealth:
    """Test actual system health and reliability."""
    
    def test_database_connection_works(self):
        """Test database connection is functional."""
        try:
            from lib.utils.db_migration import check_database_connection
            
            # Attempt database connection
            is_connected = check_database_connection()
            
            if not is_connected:
                pytest.skip("Database not available - expected in some environments")
            
            print("✅ Database connection successful")
            
        except Exception as e:
            pytest.skip(f"Database test skipped: {e}")
    
    def test_critical_directories_exist(self):
        """Verify critical system directories exist."""
        critical_dirs = [
            Path("ai/agents"),
            Path("ai/teams"), 
            Path("api"),
            Path("lib"),
            Path("tests")
        ]
        
        for dir_path in critical_dirs:
            assert dir_path.exists(), f"Critical directory missing: {dir_path}"
            assert dir_path.is_dir(), f"Path exists but is not directory: {dir_path}"
        
        print("✅ All critical directories present")
    
    def test_required_config_files_exist(self):
        """Verify required configuration files exist."""
        required_files = [
            Path(".env"),
            Path("pyproject.toml")
            # docker-compose.yml is optional for non-Docker deployments
        ]
        
        for file_path in required_files:
            assert file_path.exists(), f"Required file missing: {file_path}"
            assert file_path.is_file(), f"Path exists but is not file: {file_path}"
        
        # Check if docker-compose.yml exists (optional)
        docker_compose = Path("docker-compose.yml")
        if docker_compose.exists():
            print("✅ Docker compose file present (optional)")
        else:
            print("ℹ️ Docker compose file not present (optional)")
        
        print("✅ All required config files present")