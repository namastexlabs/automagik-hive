# Agno Codebase Examples

**Status**: ✅ VERIFIED AGAINST AGNO SOURCE ✅  
**Library**: `/context7/agno` (2552 code snippets)  
**Description**: Examples and patterns from this codebase  
**Parent**: [Agno Patterns Index](@genie/reference/agno-patterns-index.md)

---

## Models Used in This Codebase ✅ IDENTIFIED

> **Note**: For complete model configuration parameters and all supported providers, see [Agno Model Configuration](@genie/reference/agno-model-configuration.md)

### Primary Models in Production
```yaml
production_models:
  anthropic:
    - "claude-sonnet-4-20250514"              # Main model (agents, memory, API)
    - "claude-3-5-haiku-20241022"             # Fast model (tests, memory)
    - "claude-3-7-sonnet-latest"              # Demo agents
    - "claude-3-7-sonnet-20250219"            # Demo reasoning
  
  openai:
    - "gpt-4o"                                # Demo agents, teams
    - "gpt-4o-mini"                           # Demo workflows, basic agents
    - "o3-mini"                               # Reasoning examples
    - "text-embedding-3-small"                # Embeddings
```

### Model Configuration Examples from Codebase ✅ VERIFIED
```yaml
example_configurations:
  # Main orchestrator with thinking (agents/orchestrator/main_orchestrator.py:169-172)
  main_orchestrator_with_thinking:
    model: |
      Claude(
          id="claude-sonnet-4-20250514",
          max_tokens=1500,  # Must be greater than thinking budget
          thinking={"type": "enabled", "budget_tokens": 1024}
      )
    usage: "Routing decisions with internal reasoning"
    
  # Specialist agents with thinking (agents/specialists/base_agent.py:76-79)
  specialist_agent_with_thinking:
    model: |
      Claude(
          id="claude-sonnet-4-20250514",
          max_tokens=1500,  # Must be greater than thinking budget
          thinking={"type": "enabled", "budget_tokens": 1024}
      )
    usage: "All business unit specialists (Adquirência, Emissão, PagBank)"
  
  # Memory manager (context/memory/memory_manager.py:50)
  memory_manager:
    model: "Claude(id=self.config.memory_model)"  # Default: "claude-sonnet-4-20250514"
    usage: "Memory operations and session management"
  
  # Reasoning agent with tools (genie/agno-demo-app/agents/reasoning.py:22-39)
  reasoning_agent_with_tools:
    agent_config: |
      Agent(
          model=Claude(id=agent_settings.claude_4_sonnet),
          tools=[ReasoningTools(add_instructions=True)],
          name="Reasoning Agent",
          role="Reasoning agent",
          storage=reasoning_agent_storage,
          add_history_to_messages=True,
          num_history_responses=5
      )
    usage: "Demo reasoning capabilities via tools"
  
  # Standard agent without thinking (example from demos)
  standard_demo_agent:
    model: "Claude(id='claude-3-7-sonnet-latest')"
    usage: "Demo agents without thinking capability"
  
  # Combined reasoning and response models (from Agno docs)
  hybrid_reasoning_pattern:
    model: "Claude(id='claude-3-7-sonnet-20250219')"           # Response
    reasoning_model: "Groq(id='deepseek-r1-distill-llama-70b')"  # Reasoning
    parameters:
      temperature: 0.6
      max_tokens: 1024
      top_p: 0.95
    usage: "Pattern from Agno documentation (not used in this codebase)"
```


---

**Navigation**: [Index](@genie/reference/agno-patterns-index.md)
