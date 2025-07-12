# Config - Models Directory

<system_context>
This directory contains model configuration and provider settings for the PagBank multi-agent system. The system supports 20+ model providers with Claude as the primary model for production use.
</system_context>

## Purpose

Centralize model configuration, provider settings, and model-specific parameters for all agents and teams in the PagBank system. This includes thinking modes, reasoning capabilities, and provider-specific optimizations.

## Model Configuration (From Reference Files)

### Supported Model Providers (20+ Verified)
```yaml
model_providers:
  # MAJOR PROVIDERS
  anthropic: "Claude models (claude-sonnet-4-20250514, etc.)"
  openai: "GPT models (gpt-4o, gpt-4o-mini, o3-mini, etc.)"
  google: "Gemini models (gemini-2.0-flash-exp, etc.)"
  mistral: "Mistral models (mistral-large-latest, etc.)"
  
  # CLOUD PROVIDERS
  aws: "AWS Bedrock models"
  azure: "Azure AI Foundry models"
  
  # SPECIALIZED PROVIDERS
  ollama: "Local models (llama3.1:8b, etc.)"
  groq: "Fast inference models (llama-3.3-70b-versatile, deepseek-r1-distill-llama-70b, etc.)"
  cerebras: "Cerebras models"
  cohere: "Cohere models (command-r-plus, etc.)"
  deepinfra: "DeepInfra models (meta-llama/Llama-2-70b-chat-hf, etc.)"
  deepseek: "DeepSeek models (deepseek-chat, etc.)"
  
  # ADDITIONAL PROVIDERS
  huggingface: "HuggingFace models"
  nvidia: "Nvidia models"
  openrouter: "OpenRouter aggregated models"
  perplexity: "Perplexity models"
  together: "Together AI models"
  vllm: "vLLM self-hosted models"
  xai: "xAI models"
```

### Universal Model Configuration Parameters
```yaml
universal_model_config:
  # REQUIRED PARAMETERS
  id: str                                       # Model identifier (e.g., "gpt-4o", "claude-sonnet-4-20250514")
  
  # CORE SETTINGS
  name: Optional[str]                           # Model instance name
  provider: Optional[str]                       # Provider name (auto-generated from class name)
  
  # GENERATION CONTROL
  temperature: Optional[float]                  # Controls randomness of output (0.0-2.0)
  max_tokens: Optional[int]                     # Maximum tokens to generate
  top_p: Optional[float]                        # Nucleus sampling parameter
  top_k: Optional[int]                          # Top-K sampling parameter
  frequency_penalty: Optional[float]            # Penalize frequent tokens (-2.0 to 2.0)
  presence_penalty: Optional[float]             # Penalize present tokens (-2.0 to 2.0)
  
  # STOPPING CONDITIONS
  stop: Optional[Union[str, List[str]]]         # Stop sequences
  stop_sequences: Optional[List[str]]           # Alternative stop sequences (Anthropic)
  
  # DETERMINISM & REPRODUCIBILITY
  seed: Optional[int]                           # Random seed for deterministic output
  
  # AUTHENTICATION & CONNECTION
  api_key: Optional[str]                        # API key for authentication
  base_url: Optional[Union[str, httpx.URL]]     # Custom API endpoint
  timeout: Optional[float]                      # Request timeout in seconds
  max_retries: Optional[int]                    # Maximum retry attempts
```

## Models Used in This Codebase (From Examples)

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

### Model Configuration Examples from Codebase
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
  
  # Standard agent without thinking (example from demos)
  standard_demo_agent:
    model: "Claude(id='claude-3-7-sonnet-latest')"
    usage: "Demo agents without thinking capability"
```

## Model-Specific Parameters

### Anthropic Claude Models
```yaml
claude_specific:
  # CORE PARAMETERS
  id: str                                       # Default: "claude-3-5-sonnet-20241022"
  max_tokens: Optional[int]                     # Default: 4096
  
  # CLAUDE-SPECIFIC FEATURES ⭐ CONFIRMED IN CODEBASE
  thinking: Optional[Dict[str, Any]]            # ⭐ THINKING MODE - Claude's internal reasoning
    # Structure: {"type": "enabled"|"disabled", "budget_tokens": int}
    # Example: thinking={"type": "enabled", "budget_tokens": 1024}
    # Used in: agents/specialists/base_agent.py:79, agents/orchestrator/main_orchestrator.py:172
  
  cache_system_prompt: Optional[bool]          # Default: False - Cache system messages
  extended_cache_time: Optional[bool]          # Default: False - Extended caching
  
  # SAMPLING CONTROL
  temperature: Optional[float]                  # Randomness control
  top_p: Optional[float]                        # Nucleus sampling
  top_k: Optional[int]                          # Top-K sampling
  stop_sequences: Optional[List[str]]           # Custom stop sequences
```

### OpenAI Models
```yaml
openai_specific:
  # CORE PARAMETERS
  id: str                                       # Default: "gpt-4o"
  
  # REASONING MODELS PARAMETERS
  reasoning_effort: Optional[str]               # ⭐ REASONING EFFORT - "low", "medium", "high" (o3-mini only)
  
  # ADVANCED FEATURES
  store: Optional[bool]                         # Store completions for training/evals
  metadata: Optional[Dict[str, Any]]           # Request metadata
  modalities: Optional[List[str]]              # ["text", "audio"] - Multimodal support
  audio: Optional[Dict[str, Any]]              # Audio config: {"voice": "alloy", "format": "wav"}
  
  # TOKEN CONTROL
  max_tokens: Optional[int]                     # Legacy parameter
  max_completion_tokens: Optional[int]          # New preferred parameter
```

### Google Gemini Models
```yaml
gemini_specific:
  # CORE PARAMETERS
  id: str                                       # Default: "gemini-2.0-flash-exp"
  
  # GEMINI-SPECIFIC FEATURES
  function_declarations: Optional[List[FunctionDeclaration]]  # Function definitions
  generation_config: Optional[Dict[str, Any]]  # Generation configuration
  safety_settings: Optional[Dict[str, Any]]    # Safety and content filtering
  
  # ADVANCED FEATURES
  grounding: bool                               # Default: False - Use grounding
  search: bool                                  # Default: False - Use search
  grounding_dynamic_threshold: Optional[float] # Grounding threshold
  
  # VERTEX AI INTEGRATION
  vertexai: bool                               # Default: False - Use Vertex AI
  project_id: Optional[str]                    # Google Cloud project ID
  location: Optional[str]                      # Google Cloud region
```

### Groq Models
```yaml
groq_specific:
  # CORE PARAMETERS
  id: str                                       # Default: "llama-3.3-70b-versatile"
  
  # DEEPSEEK REASONING SUPPORT
  # ⭐ SUPPORTS DEEPSEEK-R1 REASONING MODELS
  # Example: "deepseek-r1-distill-llama-70b"
  
  # ADVANCED SAMPLING
  logprobs: Optional[bool]                      # Return log probabilities
  top_logprobs: Optional[int]                   # Number of top logprobs
  logit_bias: Optional[Dict[int, float]]        # Token bias mapping
  
  # USER IDENTIFICATION
  user: Optional[str]                           # End-user identifier for monitoring
```

### vLLM Models
```yaml
vllm_specific:
  # CORE PARAMETERS
  id: str                                       # Required - Model path (e.g., "Qwen/Qwen2.5-7B-Instruct")
  base_url: str                                # Default: "http://localhost:8000/v1/"
  api_key: str                                 # Default: "EMPTY" (usually not needed)
  
  # VLLM-SPECIFIC FEATURES
  enable_thinking: Optional[bool]              # ⭐ THINKING MODE - vLLM thinking capability
  
  # SAMPLING CONTROL
  temperature: float                           # Default: 0.7
  top_p: float                                 # Default: 0.8
  top_k: Optional[int]                         # Top-K sampling
  presence_penalty: float                      # Default: 1.5 - Repetition penalty
```

## Reasoning & Thinking Patterns

### Key Distinctions
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

### Thinking Mode Support by Provider
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

## Model Configuration Best Practices

### Development Configuration
```python
# config/models/development.py
DEVELOPMENT_MODELS = {
    "default": Claude(
        id="claude-3-5-haiku-20241022",  # Fast, cheaper for development
        temperature=0.7,
        max_tokens=1000
    ),
    "reasoning": Claude(
        id="claude-sonnet-4-20250514",
        thinking={"type": "enabled", "budget_tokens": 512},
        max_tokens=1500
    )
}
```

### Production Configuration
```python
# config/models/production.py
PRODUCTION_MODELS = {
    "default": Claude(
        id="claude-sonnet-4-20250514",
        temperature=0.5,
        max_tokens=2000,
        thinking={"type": "enabled", "budget_tokens": 1024}
    ),
    "fast": Claude(
        id="claude-3-5-haiku-20241022",
        temperature=0.3,
        max_tokens=1000
    ),
    "fallback": OpenAI(
        id="gpt-4o",
        temperature=0.5,
        max_completion_tokens=2000
    )
}
```

### Model Selection Strategy
```python
def get_model_for_agent(agent_type: str, environment: str):
    """Select appropriate model based on agent type and environment."""
    if environment == "production":
        if agent_type in ["orchestrator", "specialist"]:
            return PRODUCTION_MODELS["default"]  # With thinking
        elif agent_type == "memory":
            return PRODUCTION_MODELS["fast"]     # No thinking needed
    else:
        return DEVELOPMENT_MODELS["default"]     # Cheaper for dev
```

## Key References

- **Main Documentation**: `CLAUDE.md` - Root system documentation
- **Config Documentation**: `config/CLAUDE.md` - Main configuration patterns
- **Agent Documentation**: `agents/CLAUDE.md` - Agent-specific model usage
- **API Documentation**: `api/CLAUDE.md` - Model configuration in API layer

## Critical Rules

- ✅ **Use Claude 4 models** as primary models for production
- ✅ **Enable thinking mode** for orchestrator and specialist agents
- ✅ **Configure fallback models** for high availability
- ✅ **Use environment variables** for API keys (${ANTHROPIC_API_KEY})
- ✅ **Set appropriate max_tokens** greater than thinking budget_tokens
- ❌ **Never hardcode API keys** in model configurations
- ❌ **Never disable thinking** for critical decision-making agents
- ❌ **Never use deprecated models** in production
- ❌ **Never exceed rate limits** by implementing proper retry logic