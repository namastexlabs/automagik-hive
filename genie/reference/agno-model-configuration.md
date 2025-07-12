# Agno Model Configuration

**Status**: ✅ CONSOLIDATED REFERENCE ✅  
**Library**: `/context7/agno` (2552 code snippets)  
**Description**: Model providers and their specific configuration parameters  
**Parent**: [Agno Patterns Index](@genie/reference/agno-patterns-index.md)  
**Consolidated from**:
- agno-model-providers.md
- agno-model-specific-parameters.md

---

## Model Configuration Patterns ✅ VERIFIED

### Supported Model Providers (20+ Confirmed)
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
  ibm: "IBM WatsonX models (granite-20b-code-instruct, etc.)"
  litellm: "LiteLLM proxy models"
  lmstudio: "LM Studio local models"
  meta: "Meta Llama models"
  nvidia: "Nvidia models (nvidia/llama-3.1-nemotron-70b-instruct, etc.)"
  openrouter: "OpenRouter aggregated models"
  perplexity: "Perplexity models (sonar-pro, etc.)"
  sambanova: "SambaNova models"
  together: "Together AI models (mistralai/Mixtral-8x7B-Instruct-v0.1, etc.)"
  vercel: "Vercel AI models"
  vllm: "vLLM self-hosted models"
  xai: "xAI models"
  huggingface: "HuggingFace models (meta-llama/Meta-Llama-3-8B-Instruct, etc.)"
  aimlapi: "AI/ML API models"
```

### Universal Model Configuration Parameters ✅ VERIFIED
```yaml
universal_model_config:
  # REQUIRED PARAMETERS
  id: str                                       # Model identifier (e.g., "gpt-4o", "claude-sonnet-4-20250514")
  
  # CORE SETTINGS
  name: Optional[str]                           # Model instance name (default varies by provider)
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
  
  # HTTP CONFIGURATION
  default_headers: Optional[Dict[str, Any]]     # Default headers for requests
  default_query: Optional[Dict[str, Any]]       # Default query parameters
  http_client: Optional[httpx.Client]           # Custom HTTP client
  client_params: Optional[Dict[str, Any]]       # Additional client parameters
  
  # REQUEST CUSTOMIZATION
  request_params: Optional[Dict[str, Any]]      # Additional request parameters
  extra_headers: Optional[Dict[str, Any]]       # Extra headers per request
  extra_query: Optional[Dict[str, Any]]         # Extra query parameters per request
```

## Model-Specific Parameters ✅ COMPREHENSIVE

### Anthropic Claude Models ✅ VERIFIED
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
  
  # MCP INTEGRATION
  mcp_servers: Optional[List[MCPServerConfiguration]]  # Model Context Protocol servers
  
  # STRUCTURED OUTPUT
  structured_outputs: bool                      # Default: False
  add_images_to_message_content: bool          # Default: True
  override_system_role: bool                   # Default: True
  system_message_role: str                     # Default: "assistant"
```

### OpenAI Models ✅ VERIFIED
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
  
  # ADVANCED SAMPLING
  logprobs: Optional[bool]                      # Return log probabilities
  top_logprobs: Optional[int]                   # Number of top logprobs to return
  logit_bias: Optional[Dict[int, float]]        # Bias specific tokens
  
  # STRUCTURED OUTPUT
  supports_native_structured_outputs: bool     # Default: True
  
  # CLIENT SETTINGS
  organization: Optional[str]                   # OpenAI organization ID
  role_map: Optional[Dict[str, str]]           # Custom role mapping
  default_role_map:                            # Default role mapping
    system: "developer"
    user: "user" 
    assistant: "assistant"
    tool: "tool"
    model: "assistant"
```

### Google Gemini Models ✅ VERIFIED
```yaml
gemini_specific:
  # CORE PARAMETERS
  id: str                                       # Default: "gemini-2.0-flash-exp"
  
  # GEMINI-SPECIFIC FEATURES
  function_declarations: Optional[List[FunctionDeclaration]]  # Function definitions
  generation_config: Optional[Dict[str, Any]]  # Generation configuration
  safety_settings: Optional[Dict[str, Any]]    # Safety and content filtering
  generative_model_kwargs: Optional[Dict[str, Any]]  # Additional model kwargs
  
  # ADVANCED FEATURES
  grounding: bool                               # Default: False - Use grounding
  search: bool                                  # Default: False - Use search
  grounding_dynamic_threshold: Optional[float] # Grounding threshold
  
  # VERTEX AI INTEGRATION
  vertexai: bool                               # Default: False - Use Vertex AI
  project_id: Optional[str]                    # Google Cloud project ID
  location: Optional[str]                      # Google Cloud region
  
  # GENERATION CONTROL
  max_output_tokens: Optional[int]             # Maximum output tokens
  logprobs: Optional[bool]                     # Return log probabilities
```

### Groq Models ✅ VERIFIED  
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

### vLLM Models ✅ VERIFIED
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

### Provider-Specific Advanced Parameters ✅ VERIFIED

#### Mistral Models
```yaml
mistral_specific:
  safe_mode: bool                              # Default: False - Content filtering
  safe_prompt: bool                            # Default: False - Prompt filtering
  random_seed: Optional[int]                   # Random seed
  response_format: Optional[Union[Dict, ChatCompletionResponse]]  # Response format
```

#### Cohere Models
```yaml
cohere_specific:
  add_chat_history: bool                       # Default: False - Add chat history
  structured_outputs: bool                     # Default: False
  supports_structured_outputs: bool           # Default: True
```

#### AWS Bedrock Models
```yaml
aws_bedrock_specific:
  max_tokens: int                              # Default: 4096
  stop_sequences: Optional[List[str]]          # Stop sequences
```

#### HuggingFace Models
```yaml
huggingface_specific:
  store: Optional[bool]                        # Store for distillation/evals
  response_format: Optional[Any]               # Response format specification
  client: Optional[InferenceClient]            # HF client instance
  async_client: Optional[AsyncInferenceClient] # Async HF client
```

---

**Navigation**: [Index](@genie/reference/agno-patterns-index.md)
