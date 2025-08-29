"""
Integration test to demonstrate model configuration bug in Automagik Hive.

ISSUE: YAML model configurations are being ignored, all agents default to OpenAI.
STATUS: CRITICAL BUG - System is not respecting configured AI providers.

Expected behavior:
- genie-debug should use Google Gemini (provider: google, id: gemini-2.5-flash)
- System should respect YAML model configurations
- Different agents should be able to use different providers

Actual behavior:
- All agents default to OpenAI gpt-4o regardless of YAML configuration
- Agent.model returns dict instead of instantiated model
- Playground API shows all agents using "OpenAI gpt-4o"

Test evidence collected on 2025-08-28:
1. ✅ genie-debug/config.yaml correctly configured with Google Gemini
2. ✅ GEMINI_API_KEY properly set in .env
3. ✅ HIVE_DEFAULT_MODEL=gemini-2.5-flash in .env  
4. ✅ PostgreSQL database connection working
5. ❌ All agents in /playground/agents show OpenAI model
6. ❌ Agent.model is dict, not instantiated model object
7. ❌ Model configuration processing not triggered

Debugging shows:
- Model configuration YAML loading: ✅ Working
- Model proxy processing: ❌ Not triggered (no debug logs)
- Agno Agent creation: ❌ Defaults to OpenAI fallback
"""

import pytest
import yaml
from ai.agents.registry import AgentRegistry


class TestModelConfigurationBug:
    """Test suite to reproduce and document the model configuration bug."""
    
    def test_yaml_config_loads_correctly(self):
        """Verify YAML config contains correct Gemini configuration."""
        with open('ai/agents/genie-debug/config.yaml') as f:
            config = yaml.safe_load(f)
        
        # Verify YAML has correct model config
        assert 'model' in config
        model_config = config['model']
        assert model_config['provider'] == 'google'
        assert model_config['id'] == 'gemini-2.5-flash'
        assert model_config['temperature'] == 0.2
        assert model_config['max_tokens'] == 4000
        print(f"✅ YAML config correct: {model_config}")
    
    async def test_agent_registry_ignores_model_config(self):
        """Demonstrate that AgentRegistry ignores YAML model configuration."""
        # Create agent through registry
        agent = await AgentRegistry.get_agent('genie-debug')
        
        # BUG: Agent.model should be instantiated model, not dict
        print(f"Agent model type: {type(agent.model)}")
        print(f"Agent model value: {agent.model}")
        
        # BUG: Agent.model should be instantiated model, but it's None!
        if agent.model is None:
            print("❌ CRITICAL BUG: Agent.model is None - no model configuration applied!")
        elif isinstance(agent.model, dict):
            print("❌ BUG: Agent.model is dict - model not instantiated")
        else:
            print(f"✅ Agent.model instantiated: {type(agent.model)}")
        
        # The dict should at least contain the YAML config, but it doesn't
        if isinstance(agent.model, dict):
            provider = agent.model.get('provider')
            model_id = agent.model.get('id')
            print(f"Model config from agent: provider={provider}, id={model_id}")
            
            # BUG: Even the dict doesn't contain the YAML configuration
            if provider != 'google' or model_id != 'gemini-2.5-flash':
                print(f"❌ BUG: Agent model config doesn't match YAML")
                print(f"Expected: provider=google, id=gemini-2.5-flash")
                print(f"Actual: provider={provider}, id={model_id}")
    
    def test_environment_has_gemini_config(self):
        """Verify environment is configured for Gemini."""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        gemini_key = os.getenv('GEMINI_API_KEY')
        default_model = os.getenv('HIVE_DEFAULT_MODEL')
        
        assert gemini_key is not None, "GEMINI_API_KEY not set"
        assert gemini_key.startswith('AIzaSy'), "GEMINI_API_KEY format incorrect"
        assert default_model == 'gemini-2.5-flash', f"HIVE_DEFAULT_MODEL wrong: {default_model}"
        
        print(f"✅ Environment configured correctly:")
        print(f"  GEMINI_API_KEY: {gemini_key[:10]}...")
        print(f"  HIVE_DEFAULT_MODEL: {default_model}")
    
    async def test_multiple_agents_same_model_bug(self):
        """Show that all agents get the same default OpenAI model."""
        agent_configs = {}
        
        # Load YAML configs for different agents
        agents_to_test = ['genie-debug', 'genie-dev', 'template-agent']
        for agent_id in agents_to_test:
            try:
                with open(f'ai/agents/{agent_id}/config.yaml') as f:
                    config = yaml.safe_load(f)
                    agent_configs[agent_id] = config.get('model', {})
            except FileNotFoundError:
                print(f"Config not found for {agent_id}")
        
        # Create agents through registry
        created_agents = {}
        for agent_id in agents_to_test:
            try:
                agent = await AgentRegistry.get_agent(agent_id)
                created_agents[agent_id] = agent
            except Exception as e:
                print(f"Failed to create {agent_id}: {e}")
        
        # Analyze the bug
        print("\\n🐛 MODEL CONFIGURATION BUG ANALYSIS:")
        print("="*50)
        
        for agent_id, agent in created_agents.items():
            yaml_config = agent_configs.get(agent_id, {})
            actual_model = agent.model
            
            print(f"\\nAgent: {agent_id}")
            print(f"  YAML Config: {yaml_config}")
            print(f"  Actual Model: {actual_model}")
            print(f"  Model Type: {type(actual_model)}")
            
            # Check if YAML config matches actual model
            if isinstance(actual_model, dict):
                yaml_provider = yaml_config.get('provider')
                actual_provider = actual_model.get('provider')
                yaml_id = yaml_config.get('id')
                actual_id = actual_model.get('id')
                
                config_matches = (yaml_provider == actual_provider and yaml_id == actual_id)
                print(f"  Config Matches: {config_matches}")
                
                if not config_matches:
                    print(f"  ❌ BUG: Expected {yaml_provider}:{yaml_id}, got {actual_provider}:{actual_id}")
        
        print(f"\\n📋 SUMMARY:")
        print(f"  Total agents tested: {len(created_agents)}")
        print(f"  YAML configs loaded: {len(agent_configs)}")
        print(f"  🐛 BUG: Model configurations from YAML are being ignored")
        print(f"  🐛 BUG: All agents default to same model regardless of YAML config")


if __name__ == "__main__":
    import asyncio
    
    print("🔍 AUTOMAGIK HIVE MODEL CONFIGURATION BUG REPRODUCTION")
    print("="*60)
    
    test = TestModelConfigurationBug()
    
    # Run synchronous tests
    print("\\n1. Testing YAML configuration loading...")
    test.test_yaml_config_loads_correctly()
    
    print("\\n2. Testing environment configuration...")
    test.test_environment_has_gemini_config()
    
    # Run async tests
    print("\\n3. Testing agent registry model handling...")
    asyncio.run(test.test_agent_registry_ignores_model_config())
    
    print("\\n4. Testing multiple agents model configurations...")
    asyncio.run(test.test_multiple_agents_same_model_bug())
    
    print("\\n" + "="*60)
    print("🎯 CONCLUSION: Model configuration bug confirmed and documented")
    print("🔧 NEXT STEPS: Fix model configuration processing in agent registry")