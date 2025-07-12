# Agno Reasoning Thinking

**Status**: ✅ VERIFIED AGAINST AGNO SOURCE ✅  
**Library**: `/context7/agno` (2552 code snippets)  
**Description**: Reasoning and thinking patterns across models  
**Parent**: [Agno Patterns Index](@genie/reference/agno-patterns-index.md)

---

### Reasoning & Thinking Parameters ✅ COMPREHENSIVE

> **Related Documentation**:
> - Model-specific thinking parameters: [Agno Model Configuration](@genie/reference/agno-model-configuration.md)
> - Production examples with thinking: [Agno Codebase Examples](@genie/reference/agno-codebase-examples.md)

#### 📋 Key Distinctions ✅ VERIFIED AGAINST CODEBASE & AGNO DOCS
```yaml
parameter_types:
  model_level_thinking:
    location: "Inside Model() configuration"
    purpose: "Internal scratchpad/reasoning before final response"
    example: "thinking={'type': 'enabled', 'budget_tokens': 1024}"
    providers: ["anthropic_claude", "vllm", "openai_o3"]
    codebase_usage: "✅ ACTIVE - Used in production agents"
    
  agent_level_reasoning:
    location: "Agent() or Team() configuration"
    purpose: "Multi-step reasoning workflow with separate reasoning model/agent"
    example: "reasoning=True, reasoning_model=Groq(...)"
    providers: ["universal - works with any model"]
    codebase_usage: "❌ NOT USED - Available but not implemented"
    
  tools_based_reasoning:
    location: "tools parameter in Agent() configuration"
    purpose: "Add reasoning capabilities via external tools"
    example: "tools=[ReasoningTools(add_instructions=True)]"
    providers: ["universal - works with any model"]
    codebase_usage: "✅ DEMO - Used in demo reasoning agent"
```

#### 🧠 Thinking Mode Support by Provider ✅ CODEBASE VERIFIED
```yaml
thinking_support:
  anthropic_claude:
    parameter: "thinking"
    type: "Optional[Dict[str, Any]]"
    description: "Claude's internal scratchpad/reasoning mode"
    structure: '{"type": "enabled"|"disabled", "budget_tokens": int}'
    production_usage: |
      # FROM CODEBASE - agents/specialists/base_agent.py:79
      thinking={"type": "enabled", "budget_tokens": 1024}
      
      # FROM CODEBASE - agents/orchestrator/main_orchestrator.py:172
      thinking={"type": "enabled", "budget_tokens": 1024}
    requirements: "max_tokens must be greater than budget_tokens"
  
  vllm:
    parameter: "enable_thinking"
    type: "Optional[bool]"
    description: "Enables vLLM thinking mode via chat_template_kwargs"
    example: "enable_thinking: true"
  
  openai_o3:
    parameter: "reasoning_effort"
    type: "Optional[str]"
    values: ["low", "medium", "high"]
    description: "Reasoning effort level for o3-mini model"
    example: "reasoning_effort: 'high'"
```

#### 🔧 Agent/Team Level Reasoning Parameters ✅ AGNO ABSTRACTION
```yaml
agent_team_reasoning:
  # MULTI-STEP REASONING (separate from model thinking)
  reasoning: bool                               # Default: False - Enable reasoning process
  reasoning_model: Optional[Model]              # Separate model for reasoning
  reasoning_agent: Optional[Agent]              # Dedicated reasoning agent
  reasoning_min_steps: int                      # Default: 1 - Minimum reasoning steps
  reasoning_max_steps: int                      # Default: 10 - Maximum reasoning steps
  
  # REASONING TOOLS APPROACH (from codebase)
  tools_based_reasoning:
    # FROM CODEBASE - genie/agno-demo-app/agents/reasoning.py
    tools: ["ReasoningTools(add_instructions=True)"]
    description: "Add reasoning capabilities via tools rather than model parameters"
    example: |
      Agent(
          model=Claude(id=agent_settings.claude_4_sonnet),
          tools=[ReasoningTools(add_instructions=True)],
          name="Reasoning Agent"
      )
```

#### 🔄 Reasoning Model Separation ✅ VERIFIED
```yaml
reasoning_model_patterns:
  # Pattern 1: Dedicated Reasoning Model
  agent_with_reasoning_model:
    model: "Claude(id='claude-3-7-sonnet-20250219')"     # Response model
    reasoning_model: "Groq(id='deepseek-r1-distill-llama-70b')"  # Reasoning model
    description: "Use separate models for reasoning and response generation"
  
  # Pattern 2: Single Reasoning-Capable Model
  single_reasoning_model:
    model: "OpenAIChat(id='o3-mini', reasoning_effort='high')"
    description: "Use single model with built-in reasoning capabilities"
  
  # Pattern 3: Reasoning Tools Integration
  reasoning_tools:
    model: "Claude(id='claude-3-7-sonnet-latest')"
    tools: ["ThinkingTools(add_instructions=True)", "ReasoningTools(add_instructions=True)"]
    description: "Add reasoning capabilities via tools"
```


---

**Navigation**: [Index](@genie/reference/agno-patterns-index.md)
