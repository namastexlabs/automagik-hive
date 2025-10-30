# Agno Best Practices & Advanced Patterns

**Research Date:** 2025-10-30
**Source:** Agno Cookbook & Documentation (https://github.com/agno-agi/agno)

## Executive Summary

This document consolidates production-ready best practices, common patterns, and gotchas from the Agno framework cookbook and documentation. It focuses on instruction engineering, error handling, storage patterns, performance optimization, and common mistakes to avoid.

---

## 1. INSTRUCTION ENGINEERING PATTERNS

### 1.1 Core Principles

**YAML-First Configuration:**
- All agent instructions should live in `config.yaml`, not hardcoded in Python
- Enables hot-reloading and version control without code changes
- Separates concerns: configuration vs. implementation

**Structured Instruction Format:**
```yaml
instructions: |
  You are [ROLE DEFINITION].

  [COORDINATION/EXECUTION FOCUS]

  Your responsibilities:
  - [Specific task 1]
  - [Specific task 2]
  - [Specific task 3]

  [BEHAVIORAL GUIDELINES]

  [OUTPUT FORMAT REQUIREMENTS]
```

### 1.2 Instruction Templates

#### Domain Orchestrator Pattern
```yaml
instructions: |
  You are the GENIE-DEV domain orchestrator.

  COORDINATION ROLE:
  - Analyze development tasks and requirements
  - Spawn appropriate .claude/agents for execution:
    * genie-dev-coder for implementation
    * genie-dev-fixer for bug resolution

  SPAWNING PATTERN:
  - Use claude-mcp tool to spawn .claude/agents
  - .claude/agents auto-load CLAUDE.md context
  - Monitor execution and coordinate results
  - Maintain strategic focus on coordination
```

#### Customer Support Specialist Pattern
```yaml
instructions:
  - "You are an expert customer support specialist."
  - "Always be empathetic, professional, and solution-oriented."
  - "Provide clear, actionable steps to resolve customer issues."
  - "Follow the established patterns for consistent, high-quality support."
```

#### Reasoning Agent Pattern
```python
instructions=dedent("""
    You are an expert problem-solving assistant with strong analytical skills! 🧠

    Your approach to problems:
    1. First, break down complex questions into component parts
    2. Clearly state your assumptions
    3. Develop a structured reasoning path
    4. Consider multiple perspectives
    5. Evaluate evidence and counter-arguments
    6. Draw well-justified conclusions

    When solving problems:
    - Use explicit step-by-step reasoning
    - Identify key variables and constraints
    - Explore alternative scenarios
    - Highlight areas of uncertainty
    - Explain your thought process clearly

    For quantitative problems:
    - Show your calculations
    - Explain the significance of numbers
    - Consider confidence intervals when appropriate

    For qualitative reasoning:
    - Assess how different factors interact
    - Consider psychological and social dynamics
    - Evaluate practical constraints
    """)
```

### 1.3 Few-Shot Learning Pattern

**Use Case:** Guide agent behavior with concrete examples

```python
support_examples = [
    # Example 1: Simple issue resolution
    Message(role="user", content="I forgot my password and can't log in"),
    Message(
        role="assistant",
        content="""
    I'll help you reset your password right away.

    **Steps to Reset Your Password:**
    1. Go to the login page and click "Forgot Password"
    2. Enter your email address
    3. Check your email for the reset link
    4. Follow the link to create a new password
    5. Use a strong password with uppercase, lowercase, numbers, and symbols
    """.strip(),
    ),
    # Additional examples...
]

agent = Agent(
    additional_input=support_examples,  # ← Few-shot learning injection
    instructions=[...],
)
```

### 1.4 Memory-Aware Instructions

**Prevent frivolous memory updates:**
```python
agent = Agent(
    db=db,
    enable_agentic_memory=True,
    instructions=[
        "Only update memories when users share significant new information.",
        "Don't create memories for casual conversation or temporary states.",
        "Batch multiple memory updates together when possible."
    ]
)
```

---

## 2. ERROR HANDLING & RELIABILITY

### 2.1 Automatic Retry Configuration

```python
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    exponential_backoff=True,  # ← Automatic retry with backoff
    retries=2,                 # ← Number of retry attempts
    retry_delay=1,             # ← Initial delay in seconds
)
```

**Best Practices:**
- Always enable `exponential_backoff` for production
- Set `retries=2` as baseline (balance resilience vs. latency)
- Use `retry_delay=1` for most use cases (adjust based on API rate limits)

### 2.2 Pre-Hooks for Input Validation

```python
from agno.exceptions import CheckTrigger, InputCheckError
from agno.run.team import RunInput

def comprehensive_input_validation(run_input: RunInput) -> None:
    """
    Pre-hook: Comprehensive input validation using an AI team.

    Validates:
    - Relevance to team's purpose
    - Sufficient detail for meaningful response
    - Safety (no harmful content, prompt injection)
    """
    validator_team = Team(
        name="Input Validator",
        model=OpenAIChat(id="gpt-5-mini"),
        instructions=[
            "Analyze user requests for:",
            "1. RELEVANCE: Appropriate for team's domain",
            "2. DETAIL: Enough information for meaningful response",
            "3. SAFETY: Not harmful or unsafe",
        ],
        output_schema=InputValidationResult,
    )

    validation_result = validator_team.run(
        input=f"Validate this user request: '{run_input.input_content}'"
    )

    result = validation_result.content

    if not result.is_safe:
        raise InputCheckError(
            f"Input is harmful or unsafe.",
            check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
        )

    if not result.is_relevant:
        raise InputCheckError(
            f"Input is not relevant.",
            check_trigger=CheckTrigger.OFF_TOPIC,
        )

# Apply to team
team = Team(
    name="Financial Advisor Team",
    pre_hooks=[comprehensive_input_validation],
    # ...
)
```

### 2.3 Post-Hooks for Output Validation

```python
from agno.exceptions import CheckTrigger, OutputCheckError
from agno.run.team import RunOutput

def validate_response_quality(run_output: RunOutput) -> None:
    """
    Post-hook: Validate team response for quality and safety.

    Checks:
    - Response completeness (not too short/vague)
    - Professional tone and language
    - Safety and appropriateness
    """

    # Skip validation for empty responses
    if not run_output.content or len(run_output.content.strip()) < 10:
        raise OutputCheckError(
            "Response is too short or empty",
            check_trigger=CheckTrigger.OUTPUT_NOT_ALLOWED,
        )

    validator_team = Team(
        name="Output Validator",
        model=OpenAIChat(id="gpt-5-mini"),
        instructions=[
            "Analyze responses for:",
            "1. COMPLETENESS: Addresses question thoroughly",
            "2. PROFESSIONALISM: Appropriate language",
            "3. SAFETY: No harmful advice",
        ],
        output_schema=OutputValidationResult,
    )

    validation_result = validator_team.run(
        input=f"Validate this response: '{run_output.content}'"
    )

    result = validation_result.content

    if not result.is_complete:
        raise OutputCheckError(
            f"Response incomplete. Concerns: {', '.join(result.concerns)}",
            check_trigger=CheckTrigger.OUTPUT_NOT_ALLOWED,
        )

    if result.confidence_score < 0.6:
        raise OutputCheckError(
            f"Quality score too low ({result.confidence_score:.2f})",
            check_trigger=CheckTrigger.OUTPUT_NOT_ALLOWED,
        )

# Apply to team
team = Team(
    name="Customer Support Team",
    post_hooks=[validate_response_quality],
    # ...
)
```

### 2.4 Tool Hooks for Observability

```python
import time
from typing import Any, Callable, Dict

def logger_hook(function_name: str, function_call: Callable, arguments: Dict[str, Any]):
    """Tool hook for logging and timing."""

    if function_name == "delegate_task_to_member":
        member_id = arguments.get("member_id")
        logger.info(f"Delegating task to member {member_id}")

    # Start timer
    start_time = time.time()
    result = function_call(**arguments)
    end_time = time.time()

    duration = end_time - start_time
    logger.info(f"Function {function_name} took {duration:.2f} seconds")

    return result

agent = Agent(
    tools=[DuckDuckGoTools()],
    tool_hooks=[logger_hook],  # ← Apply to all tools
)
```

### 2.5 Retry Logic with Pre-Hooks

```python
from agno.exceptions import RetryAgentRun

num_calls = 0

def pre_hook(fc: FunctionCall):
    global num_calls

    print(f"Pre-hook: {fc.function.name}")
    num_calls += 1

    if num_calls < 2:
        raise RetryAgentRun(
            "This wasn't interesting enough, retry with different argument"
        )

@tool(pre_hook=pre_hook)
def print_something(something: str) -> Iterator[str]:
    print(something)
    yield f"I have printed {something}"

agent = Agent(tools=[print_something])
```

---

## 3. STORAGE & MEMORY PATTERNS

### 3.1 Memory Management Decision Tree

```
├── Need real-time memory updates during conversation?
│   ├── YES → Use enable_agentic_memory=True
│   │         (8x more expensive, nested LLM calls)
│   └── NO  → Use enable_user_memories=True ✅ RECOMMENDED
│             (Processes memories once at end)
```

### 3.2 Automatic Memory (Recommended)

```python
# ✅ GOOD: Single memory processing after conversation
agent = Agent(
    db=db,
    enable_user_memories=True  # Processes once at end
)

# Use when you need:
# - Standard memory persistence
# - Cost-effective operations
# - Batch memory updates
```

### 3.3 Agentic Memory (Advanced)

```python
# Only use when you specifically need:
# - Real-time memory updates during conversation
# - User-directed memory commands ("forget my address")
# - Complex memory reasoning within conversation flow

agent = Agent(
    db=db,
    enable_agentic_memory=True,
    tool_call_limit=5,  # ← Prevent excessive operations
    instructions=[
        "Only update memories when users share significant new information.",
        "Don't create memories for casual conversation.",
        "Batch multiple memory updates together when possible."
    ]
)
```

**Cost Analysis:**
```python
# Scenario: User with 100 existing memories
# 10-message conversation, agent updates memory 7 times:
#
# Normal conversation: 10 × 500 tokens = 5,000 tokens
# With agentic memory: (10 × 500) + (7 × 5,000) = 40,000 tokens
# Cost increase: 8x more expensive!
```

### 3.4 Cost Optimization: Cheaper Model for Memory

```python
from agno.memory import MemoryManager

# ✅ GOOD: Use cheap model for memory operations
memory_manager = MemoryManager(
    db=db,
    model=OpenAIChat(id="gpt-4o-mini")  # 60x less expensive
)

# Expensive model for main conversations
agent = Agent(
    db=db,
    model=OpenAIChat(id="gpt-4o"),
    memory_manager=memory_manager,
    enable_agentic_memory=True
)
```

### 3.5 User Isolation (Critical)

```python
# ❌ BAD: Shared memory across users
agent.print_response("I love pizza")
agent.print_response("I'm allergic to dairy")

# ✅ GOOD: Isolated memories per user
agent.print_response("I love pizza", user_id="user_123")
agent.print_response("I'm allergic to dairy", user_id="user_456")
```

### 3.6 Memory Pruning

```python
from datetime import datetime, timedelta

def prune_old_memories(db, user_id, days=90):
    """Remove memories older than 90 days"""
    cutoff_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())

    memories = db.get_user_memories(user_id=user_id)
    for memory in memories:
        if memory.updated_at and memory.updated_at < cutoff_timestamp:
            db.delete_user_memory(memory_id=memory.memory_id)

# Run periodically or before high-cost operations
prune_old_memories(db, user_id="john_doe@example.com")
```

### 3.7 Selective Session Storage

```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGoTools()],
    db=SqliteDb(db_file="tmp/agents.db"),
    add_history_to_context=True,
    num_history_runs=5,
    store_media=False,              # Don't store images/videos/audio
    store_tool_messages=False,      # Don't store tool execution details
    store_history_messages=False    # Don't store history messages
)
```

### 3.8 Common Memory Pitfall

```python
# ❌ DOESN'T WORK: Both enabled
agent = Agent(
    db=db,
    enable_user_memories=True,
    enable_agentic_memory=True  # This DISABLES automatic behavior!
)

# ✅ CORRECT: Choose one
agent = Agent(db=db, enable_user_memories=True)  # Automatic
# OR
agent = Agent(db=db, enable_agentic_memory=True)  # Agentic
```

---

## 4. PERFORMANCE OPTIMIZATION

### 4.1 Workflow Event Storage

```python
# Production: Selective event storage
production_workflow = Workflow(
    name="Production Workflow",
    store_events=True,
    events_to_skip=[
        WorkflowRunEvent.step_started,
        WorkflowRunEvent.parallel_execution_started,
        # Keep step_completed and workflow_completed
    ],
    steps=[...]
)

# Performance: Disable all events
fast_workflow = Workflow(
    name="Fast Workflow",
    store_events=False,  # ← No overhead
    steps=[...]
)
```

### 4.2 Knowledge Base Chunking Strategies

```python
from agno.knowledge.chunking.fixed import FixedSizeChunking
from agno.knowledge.chunking.semantic import SemanticChunking

# ✅ FAST: Simple content (uniform structure)
fast_chunking = FixedSizeChunking(
    chunk_size=800,
    overlap=80
)

# ✅ QUALITY: Complex content (variable structure)
quality_chunking = SemanticChunking(
    chunk_size=1200,
    similarity_threshold=0.5
)
```

### 4.3 Content Filtering

```python
# ✅ GOOD: Process only what you need
knowledge.add_contents(
    paths=["large_dataset/"],
    include=["*.pdf"],       # Only PDFs
    exclude=["*backup*"],    # Skip backups
    skip_if_exists=True,     # Avoid reprocessing
    metadata={"batch": "current"}
)
```

### 4.4 Async Operations

```python
# Async content loading for better performance
await knowledge.add_content_async(path="large_dataset/")

# Async agent responses
response = await agent.arun("What's in the dataset?")
```

### 4.5 Bulk Memory Operations

```python
# ✅ GOOD: Bulk upsert for performance
memories = [
    UserMemory(memory_id="mem_1", user_id="user_abc", ...),
    UserMemory(memory_id="mem_2", user_id="user_abc", ...),
]

# POST /memories/upsert
result = db.upsert_memories(memories, deserialize=True)
```

### 4.6 Performance Benchmarks

**Agno Performance Characteristics:**
- Agent instantiation: ~3 microseconds
- Memory footprint: ~6.6KB
- **529× faster than LangGraph**
- **24× lower memory usage**
- Stateless and horizontally scalable

---

## 5. STRUCTURED OUTPUT PATTERNS

### 5.1 Input Schema Validation

```python
from pydantic import BaseModel, Field
from typing import List

class ResearchTopic(BaseModel):
    """Structured research topic with validation"""
    topic: str
    focus_areas: List[str] = Field(description="Specific areas to focus on", min_items=1)
    target_audience: str
    depth_level: str = Field(pattern="^(basic|intermediate|advanced)$")
    sources_required: int = Field(ge=3, le=20, default=5)

# Workflow with automatic validation
workflow = Workflow(
    name="Content Creation Workflow",
    input_schema=ResearchTopic,  # ← Validates input automatically
    steps=[research_step, content_planning_step],
)

# Valid input
workflow.print_response(
    input={
        "topic": "AI trends in 2024",
        "focus_areas": ["Machine Learning", "Computer Vision"],
        "target_audience": "Tech professionals",
        "sources_required": 8
    }
)
```

### 5.2 Output Schema Enforcement

```python
class StockAnalysis(BaseModel):
    symbol: str
    company_name: str
    analysis: str

class StockReport(BaseModel):
    symbol: str
    company_name: str
    analysis: str

# Agent-level output schema
stock_searcher = Agent(
    name="Stock Searcher",
    model=OpenAIChat("gpt-5-mini"),
    output_schema=StockAnalysis,  # ← Enforces structure
    tools=[DuckDuckGoTools()],
)

# Team-level output schema
team = Team(
    name="Stock Research Team",
    model=OpenAIChat("gpt-5-mini"),
    members=[stock_searcher],
    output_schema=StockReport,  # ← Final output structure
)

response = team.run("What is the current stock price of NVDA?")
assert isinstance(response.content, StockReport)  # ✅ Type-safe
```

### 5.3 Async Structured Streaming

```python
async def test_structured_streaming():
    """Stream structured output asynchronously"""
    async_stream = team.arun(
        "Give me a stock report for NVDA",
        stream=True,
        stream_events=True
    )

    # Consume async streaming events
    run_response = None
    async for event_or_response in async_stream:
        run_response = event_or_response  # Last item is final response

    assert isinstance(run_response.content, StockReport)
    print(f"✅ Symbol: {run_response.content.symbol}")
```

---

## 6. TOOL INTEGRATION PATTERNS

### 6.1 Tool Selection

```python
# ✅ GOOD: Selective tool inclusion
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[
        CalculatorTools(
            exclude_tools=["exponentiate", "factorial", "is_prime"],
        ),
        DuckDuckGoTools(
            include_tools=["duckduckgo_search"]
        ),
    ],
)
```

### 6.2 Reasoning Tools Integration

```python
from agno.tools.reasoning import ReasoningTools

# ✅ GOOD: Add reasoning to any model
reasoning_agent = Agent(
    model=Claude(id="claude-3-7-sonnet-latest"),
    tools=[
        ReasoningTools(add_instructions=True),
        DuckDuckGoTools(),
    ],
    instructions="Use tables where possible",
)

# Run with full reasoning visibility
reasoning_agent.print_response(
    "Compare NVDA to TSLA",
    stream=True,
    show_full_reasoning=True,
    stream_events=True,
)
```

### 6.3 Knowledge Tools

```python
from agno.tools.knowledge import KnowledgeTools

knowledge_tools = KnowledgeTools(
    knowledge=agno_docs,
    think=True,      # Enable thinking tool
    search=True,     # Enable search tool
    analyze=True,    # Enable analysis tool
    add_few_shot=True,  # Add few-shot examples
)

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[knowledge_tools],
)
```

---

## 7. COMMON MISTAKES TO AVOID

### 7.1 Memory Configuration

```python
# ❌ WRONG: Both memory modes enabled
agent = Agent(
    db=db,
    enable_user_memories=True,
    enable_agentic_memory=True  # Disables automatic!
)

# ✅ RIGHT: Choose one
agent = Agent(db=db, enable_user_memories=True)
```

### 7.2 User Isolation

```python
# ❌ WRONG: No user_id
agent.print_response("I love pizza")  # Shared memory!

# ✅ RIGHT: Explicit user_id
agent.print_response("I love pizza", user_id="user_123")
```

### 7.3 Tool Call Limits

```python
# ❌ WRONG: No limit on agentic memory
agent = Agent(
    db=db,
    enable_agentic_memory=True
    # Missing tool_call_limit!
)

# ✅ RIGHT: Set reasonable limit
agent = Agent(
    db=db,
    enable_agentic_memory=True,
    tool_call_limit=5  # Prevent runaway costs
)
```

### 7.4 Hardcoded Configuration

```python
# ❌ WRONG: Hardcoded in Python
agent = Agent(
    instructions="You are a helpful assistant...",
    model=OpenAIChat(id="gpt-4o"),
)

# ✅ RIGHT: YAML-driven
config = yaml.safe_load(open("config.yaml"))
agent = Agent(
    instructions=config["instructions"],
    model=resolve_model(model_id=config["model"]["id"]),
)
```

### 7.5 Missing Error Handling

```python
# ❌ WRONG: No retry logic
agent = Agent(model=OpenAIChat(id="gpt-5-mini"))

# ✅ RIGHT: Automatic retry
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    exponential_backoff=True,
    retries=2,
    retry_delay=1,
)
```

### 7.6 Inefficient Storage

```python
# ❌ WRONG: Store everything
agent = Agent(
    db=db,
    store_media=True,
    store_tool_messages=True,
    store_history_messages=True,
)

# ✅ RIGHT: Selective storage
agent = Agent(
    db=db,
    add_history_to_context=True,
    num_history_runs=5,
    store_media=False,
    store_tool_messages=False,
    store_history_messages=False,
)
```

---

## 8. RELIABILITY EVALUATION

### 8.1 Tool Call Validation

```python
from agno.eval.reliability import ReliabilityEval, ReliabilityResult

def test_tool_reliability():
    agent = Agent(
        model=OpenAIChat(id="gpt-5-mini"),
        tools=[CalculatorTools()],
    )

    response = agent.run("What is 10*5 then to the power of 2?")

    evaluation = ReliabilityEval(
        name="Tool Calls Reliability",
        agent_response=response,
        expected_tool_calls=["multiply", "exponentiate"],
    )

    result = evaluation.run(print_results=True)
    result.assert_passed()  # ✅ Ensures tools were called
```

### 8.2 Team Delegation Validation

```python
def evaluate_team_reliability():
    team = Team(
        name="Web Searcher Team",
        members=[web_searcher],
    )

    response = team.run("What is the latest news on AI?")

    evaluation = ReliabilityEval(
        name="Team Reliability Evaluation",
        team_response=response,
        expected_tool_calls=[
            "delegate_task_to_member",  # Team delegation
            "duckduckgo_news",          # Tool execution
        ],
    )

    result = evaluation.run(print_results=True)
    result.assert_passed()
```

---

## 9. PRODUCTION CHECKLIST

### Before Deployment:

- [ ] **Error Handling**
  - [ ] `exponential_backoff=True` enabled
  - [ ] `retries` configured (baseline: 2)
  - [ ] Pre/post hooks for validation
  - [ ] Tool hooks for observability

- [ ] **Memory Management**
  - [ ] Choose correct memory mode (`enable_user_memories` vs `enable_agentic_memory`)
  - [ ] Set `tool_call_limit` if using agentic memory
  - [ ] Implement memory pruning strategy
  - [ ] Ensure user isolation with `user_id`

- [ ] **Performance**
  - [ ] Selective event storage configured
  - [ ] Content filtering optimized
  - [ ] Chunking strategy matches content type
  - [ ] Storage selectively disabled where appropriate

- [ ] **Configuration**
  - [ ] YAML-driven instructions
  - [ ] No hardcoded secrets/credentials
  - [ ] Environment-based model selection
  - [ ] Version control for configs

- [ ] **Structured Output**
  - [ ] Input schema validation (Pydantic)
  - [ ] Output schema enforcement
  - [ ] Type-safe data flow

- [ ] **Testing**
  - [ ] Reliability evaluations for critical paths
  - [ ] Tool call validation
  - [ ] Performance benchmarks
  - [ ] Error path coverage

---

## 10. QUICK REFERENCE

### Model Configuration
```python
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    exponential_backoff=True,
    retries=2,
    retry_delay=1,
)
```

### Memory (Recommended)
```python
agent = Agent(
    db=db,
    enable_user_memories=True,  # Automatic, cost-effective
)
```

### Storage Optimization
```python
agent = Agent(
    db=db,
    add_history_to_context=True,
    num_history_runs=5,
    store_media=False,
    store_tool_messages=False,
    store_history_messages=False,
)
```

### Structured Output
```python
agent = Agent(
    output_schema=MyPydanticModel,  # Type-safe responses
)
```

### Validation Hooks
```python
team = Team(
    pre_hooks=[input_validation],   # Before processing
    post_hooks=[output_validation], # After generation
)
```

### Tool Hooks
```python
agent = Agent(
    tools=[DuckDuckGoTools()],
    tool_hooks=[logger_hook],  # Observability
)
```

---

## Related Documentation

- [Agno Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook)
- [Agno Documentation](https://docs.agno.com)
- [Automagik Hive CLAUDE.md](/CLAUDE.md)
- [AI Domain Guide](/ai/CLAUDE.md)
