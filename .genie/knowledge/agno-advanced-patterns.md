# Agno Advanced Patterns - Extended Reference

**Research Date:** 2025-10-30
**Sources:** Automagik Hive Production Code, Integration Tests, Real-World Usage
**Status:** Battle-Tested Patterns

---

## Table of Contents

1. [Agent Response Handling](#agent-response-handling)
2. [Testing Patterns](#testing-patterns)
3. [Performance Optimization](#performance-optimization)
4. [Error Recovery Strategies](#error-recovery-strategies)
5. [Multi-Agent Coordination](#multi-agent-coordination)
6. [YAML Configuration Patterns](#yaml-configuration-patterns)
7. [Model Selection Logic](#model-selection-logic)

---

## Agent Response Handling

### RunOutput Structure

```python
# Agent returns RunOutput object
response = agent.run("What is 2+2?")

# Access content
print(response.content)  # Main text response

# Check response attributes
if hasattr(response, 'content'):
    content = response.content
else:
    content = str(response)
```

### Response Content Validation

```python
def validate_agent_response(response, min_length: int = 10):
    """Validate agent response quality."""
    # Check response exists
    if not response:
        raise ValueError("No response from agent")

    # Check content attribute
    if not hasattr(response, 'content'):
        raise ValueError("Response missing content attribute")

    content = response.content

    # Validate content
    if not content or not content.strip():
        raise ValueError("Empty response content")

    if len(content) < min_length:
        raise ValueError(f"Response too short: {len(content)} chars")

    # Check for error indicators
    if "error" in content.lower() or "exception" in content.lower():
        raise ValueError("Response contains error message")

    return content
```

### Structured Response Extraction

```python
import re

def extract_structured_data(response_content: str, pattern: str):
    """Extract structured data from response."""
    # Example: Extract number from "ANSWER: 42"
    match = re.search(pattern, response_content)
    if match:
        return match.group(1)
    return None

# Usage
response = await agent.arun("What is 17 * 23?")
answer = extract_structured_data(
    response.content,
    r"ANSWER:\s*(\d+)"
)
print(f"Extracted: {answer}")  # "391"
```

---

## Testing Patterns

### Fixture-Based Agent Creation

```python
import pytest
from agno.agent import Agent
from agno.models.openai import OpenAIChat

@pytest.fixture
def openai_model():
    """Reusable OpenAI model fixture."""
    return OpenAIChat(id="gpt-4o-mini")

@pytest.fixture
def test_agent(openai_model):
    """Create test agent with standard config."""
    agent = Agent(
        name="Test Agent",
        model=openai_model,
        instructions="You are a helpful assistant.",
        markdown=True
    )
    agent.agent_id = "test-agent"
    return agent

# Use in tests
@pytest.mark.asyncio
async def test_agent_responds(test_agent):
    response = await test_agent.arun("Hello")
    assert response.content
```

### Quality Validation Fixture

```python
@pytest.fixture
def quality_validator():
    """Validate response quality."""
    class QualityValidator:
        @staticmethod
        def validate_response(response: str, criteria: dict) -> dict:
            return {
                "has_content": bool(response and response.strip()),
                "min_length": len(response) >= criteria.get("min_length", 0),
                "contains_keywords": any(
                    kw.lower() in response.lower()
                    for kw in criteria.get("should_contain", [])
                ) if criteria.get("should_contain") else True,
                "not_error": "error" not in response.lower()
            }

        @staticmethod
        def calculate_quality_score(results: dict) -> float:
            return sum(results.values()) / len(results)

    return QualityValidator()

# Usage
@pytest.mark.asyncio
async def test_response_quality(test_agent, quality_validator):
    response = await test_agent.arun("What is the capital of France?")

    criteria = {
        "min_length": 5,
        "should_contain": ["Paris"]
    }

    validation = quality_validator.validate_response(response.content, criteria)
    quality_score = quality_validator.calculate_quality_score(validation)

    assert quality_score >= 0.75, f"Quality too low: {quality_score}"
```

### Performance Measurement

```python
import time
from contextlib import contextmanager

@contextmanager
def measure_response_time():
    """Measure agent response time."""
    start = time.time()
    yield lambda: time.time() - start

# Usage
async def test_performance():
    with measure_response_time() as get_duration:
        response = await agent.arun("Quick question")

    duration = get_duration()
    assert duration < 5.0, f"Too slow: {duration}s"
```

---

## Performance Optimization

### Concurrent Agent Execution

```python
import asyncio

async def concurrent_agent_tasks(agents: list, queries: list):
    """Execute multiple agents concurrently."""
    # Create tasks for all agents
    tasks = [
        agent.arun(query)
        for agent, query in zip(agents, queries)
    ]

    # Run concurrently with asyncio.gather
    responses = await asyncio.gather(*tasks)

    return [r.content for r in responses]

# Usage
agents = [create_agent() for _ in range(3)]
queries = ["Query 1", "Query 2", "Query 3"]

results = await concurrent_agent_tasks(agents, queries)
```

### Rate Limiting

```python
import asyncio

async def rate_limited_execution(agent, queries: list, delay: float = 0.5):
    """Execute queries with rate limiting."""
    results = []

    for query in queries:
        response = await agent.arun(query)
        results.append(response.content)

        # Wait between requests
        await asyncio.sleep(delay)

    return results
```

### Batch Processing with Progress

```python
from typing import List

async def batch_process_queries(
    agent,
    queries: List[str],
    batch_size: int = 5,
    delay_between_batches: float = 1.0
):
    """Process queries in batches."""
    results = []

    for i in range(0, len(queries), batch_size):
        batch = queries[i:i + batch_size]

        print(f"Processing batch {i//batch_size + 1}...")

        # Process batch concurrently
        batch_results = await asyncio.gather(
            *[agent.arun(q) for q in batch]
        )

        results.extend([r.content for r in batch_results])

        # Delay between batches
        if i + batch_size < len(queries):
            await asyncio.sleep(delay_between_batches)

    return results
```

---

## Error Recovery Strategies

### Exponential Backoff Retry

```python
import asyncio
from typing import Optional

async def exponential_backoff_retry(
    agent,
    query: str,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0
) -> Optional[str]:
    """Retry with exponential backoff."""
    delay = initial_delay

    for attempt in range(max_attempts):
        try:
            response = await agent.arun(query)
            return response.content

        except Exception as e:
            if attempt == max_attempts - 1:
                print(f"All {max_attempts} attempts failed")
                raise

            print(f"Attempt {attempt + 1} failed: {e}")
            print(f"Retrying in {delay}s...")

            await asyncio.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)

    return None
```

### Fallback Chain

```python
async def try_agents_in_sequence(agents: list, query: str):
    """Try agents until one succeeds."""
    last_error = None

    for i, agent in enumerate(agents):
        try:
            response = await agent.arun(query)
            print(f"Agent {i} succeeded")
            return response.content

        except Exception as e:
            print(f"Agent {i} failed: {e}")
            last_error = e
            continue

    raise Exception(f"All agents failed. Last error: {last_error}")
```

### Graceful Degradation

```python
async def query_with_fallback(
    primary_agent,
    fallback_agent,
    query: str,
    timeout: float = 30.0
):
    """Use primary agent with fallback."""
    try:
        # Try primary with timeout
        response = await asyncio.wait_for(
            primary_agent.arun(query),
            timeout=timeout
        )
        return response.content, "primary"

    except asyncio.TimeoutError:
        print("Primary timed out, using fallback")
        response = await fallback_agent.arun(query)
        return response.content, "fallback"

    except Exception as e:
        print(f"Primary failed: {e}, using fallback")
        response = await fallback_agent.arun(query)
        return response.content, "fallback"
```

---

## Multi-Agent Coordination

### Agent Communication Pattern

```python
async def multi_agent_workflow(
    researcher_agent,
    writer_agent,
    reviewer_agent,
    topic: str
):
    """Coordinate multiple agents for complex task."""
    # Step 1: Research
    research_response = await researcher_agent.arun(
        f"Research information about: {topic}"
    )
    research_data = research_response.content

    # Step 2: Write based on research
    write_response = await writer_agent.arun(
        f"Write an article based on this research: {research_data}"
    )
    draft = write_response.content

    # Step 3: Review and improve
    review_response = await reviewer_agent.arun(
        f"Review and suggest improvements for: {draft}"
    )
    final_content = review_response.content

    return {
        "research": research_data,
        "draft": draft,
        "final": final_content
    }
```

### Parallel Specialist Pattern

```python
async def parallel_analysis(
    topic: str,
    specialists: dict
):
    """Get insights from multiple specialists in parallel."""
    # Create tasks for each specialist
    tasks = {
        name: agent.arun(f"Analyze {topic} from {name} perspective")
        for name, agent in specialists.items()
    }

    # Execute concurrently
    results = await asyncio.gather(*tasks.values())

    # Combine results
    return {
        name: response.content
        for name, response in zip(tasks.keys(), results)
    }

# Usage
specialists = {
    "technical": tech_agent,
    "business": business_agent,
    "security": security_agent
}

insights = await parallel_analysis("Cloud migration", specialists)
```

---

## YAML Configuration Patterns

### Complete Agent Configuration

```yaml
# config.yaml - Production pattern
agent:
  name: "Production Agent"
  agent_id: "prod-agent"
  version: 1.0.0
  description: "Production-ready agent configuration"

model:
  provider: "anthropic"
  id: "claude-3-5-haiku-20241022"
  temperature: 0.7

instructions: |
  You are a production assistant.

  ## Capabilities
  - Answer questions clearly
  - Provide structured responses
  - Follow best practices

  ## Guidelines
  - Be concise and accurate
  - Use examples when helpful
  - Maintain professional tone

tools:
  - name: "DuckDuckGoTools"
    enabled: true
  - name: "PythonTools"
    enabled: false

storage:
  table_name: "prod_agent_sessions"
  auto_upgrade_schema: true

metadata:
  created_by: "DevOps Team"
  environment: "production"
  version_date: "2025-01-30"
```

### Loading Pattern

```python
import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat

def load_agent_from_yaml(config_path: str) -> Agent:
    """Load agent from YAML configuration."""
    # Load config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Extract sections
    agent_config = config.get("agent", {})
    model_config = config.get("model", {})

    # Create model based on provider
    provider = model_config.get("provider", "openai")
    model_id = model_config.get("id")
    temperature = model_config.get("temperature", 0.7)

    if provider == "openai":
        model = OpenAIChat(id=model_id, temperature=temperature)
    elif provider == "anthropic":
        model = Claude(id=model_id, temperature=temperature)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    # Create agent
    agent = Agent(
        name=agent_config.get("name"),
        model=model,
        instructions=config.get("instructions"),
        markdown=True
    )

    # Set agent_id as instance attribute
    if agent_config.get("agent_id"):
        agent.agent_id = agent_config["agent_id"]

    return agent

# Usage
agent = load_agent_from_yaml("config.yaml")
```

---

## Model Selection Logic

### Dynamic Provider Selection

```python
from typing import Literal

ModelProvider = Literal["openai", "anthropic"]

def select_model_by_task(
    task_type: str,
    preferred_provider: ModelProvider = "openai"
):
    """Select optimal model based on task type."""
    # Task complexity mapping
    task_models = {
        "simple": {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-haiku-20241022"
        },
        "complex": {
            "openai": "gpt-4o",
            "anthropic": "claude-sonnet-4-5-20250929"
        },
        "creative": {
            "openai": "gpt-4o",
            "anthropic": "claude-3-5-haiku-20241022"
        },
        "analytical": {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-haiku-20241022"
        }
    }

    model_id = task_models.get(task_type, {}).get(
        preferred_provider,
        "gpt-4o-mini"  # Default fallback
    )

    return model_id, preferred_provider
```

### Cost-Optimized Selection

```python
def select_cost_optimized_model(
    complexity: str,
    budget_tier: str = "standard"
):
    """Select model based on complexity and budget."""
    # Budget tier mappings
    budget_models = {
        "low": {
            "simple": ("gpt-4o-mini", 0.0),
            "complex": ("gpt-4o-mini", 0.5)
        },
        "standard": {
            "simple": ("gpt-4o-mini", 0.7),
            "complex": ("claude-3-5-haiku-20241022", 0.7)
        },
        "premium": {
            "simple": ("claude-3-5-haiku-20241022", 0.7),
            "complex": ("claude-sonnet-4-5-20250929", 0.7)
        }
    }

    model_id, temperature = budget_models.get(budget_tier, {}).get(
        complexity,
        ("gpt-4o-mini", 0.7)
    )

    return model_id, temperature
```

### Temperature Selection Guide

```python
def get_optimal_temperature(task_category: str) -> float:
    """Get optimal temperature for task category."""
    temperature_guide = {
        # Deterministic tasks
        "math": 0.0,
        "logic": 0.0,
        "code_generation": 0.2,
        "factual_qa": 0.3,

        # Balanced tasks
        "general_assistance": 0.7,
        "summarization": 0.5,
        "translation": 0.3,

        # Creative tasks
        "creative_writing": 0.9,
        "brainstorming": 0.8,
        "storytelling": 0.9
    }

    return temperature_guide.get(task_category, 0.7)  # Default
```

---

## Production Deployment Patterns

### Environment-Based Configuration

```python
import os

def create_production_agent(
    environment: str = "production"
) -> Agent:
    """Create agent with environment-specific config."""
    # Environment configurations
    env_configs = {
        "development": {
            "model_id": "gpt-4o-mini",
            "temperature": 0.7,
            "timeout": 60.0
        },
        "staging": {
            "model_id": "claude-3-5-haiku-20241022",
            "temperature": 0.7,
            "timeout": 45.0
        },
        "production": {
            "model_id": "claude-sonnet-4-5-20250929",
            "temperature": 0.5,  # More deterministic
            "timeout": 30.0
        }
    }

    config = env_configs.get(environment, env_configs["development"])

    # Create model based on environment
    if config["model_id"].startswith("gpt"):
        model = OpenAIChat(
            id=config["model_id"],
            temperature=config["temperature"]
        )
    else:
        model = Claude(
            id=config["model_id"],
            temperature=config["temperature"]
        )

    return Agent(
        name=f"{environment.title()} Agent",
        model=model,
        instructions=os.getenv("AGENT_INSTRUCTIONS", "You are a helpful assistant."),
        markdown=True
    )
```

### Monitoring Integration

```python
import time
from typing import Callable

async def monitored_agent_run(
    agent,
    query: str,
    logger: Callable,
    metrics_collector: Callable
):
    """Run agent with monitoring and metrics."""
    start_time = time.time()
    success = False
    error = None

    try:
        response = await agent.arun(query)
        success = True

        # Log success
        logger.info(
            "Agent execution successful",
            agent_id=getattr(agent, 'agent_id', 'unknown'),
            duration=time.time() - start_time
        )

        return response.content

    except Exception as e:
        error = str(e)
        logger.error(
            "Agent execution failed",
            agent_id=getattr(agent, 'agent_id', 'unknown'),
            error=error
        )
        raise

    finally:
        # Collect metrics
        metrics_collector({
            "agent_id": getattr(agent, 'agent_id', 'unknown'),
            "duration": time.time() - start_time,
            "success": success,
            "error": error,
            "query_length": len(query)
        })
```

---

## Key Learnings from Production

### Critical Patterns

1. **Always set agent_id as instance attribute**, not in constructor
2. **Use factory functions** for flexible agent creation
3. **Validate responses** before processing
4. **Implement retry logic** with exponential backoff
5. **Test with real API calls** in integration tests
6. **Monitor performance** and quality metrics

### Common Pitfalls to Avoid

1. ❌ Passing `agent_id` to Agent constructor → TypeError
2. ❌ Not checking `response.content` exists → AttributeError
3. ❌ Hardcoding model IDs → Inflexible configuration
4. ❌ No timeout handling → Hanging requests
5. ❌ Ignoring response validation → Silent failures

### Production Checklist

- [ ] Factory pattern for agent creation
- [ ] YAML configuration for flexibility
- [ ] Error handling with retries
- [ ] Response validation
- [ ] Performance monitoring
- [ ] Timeout handling
- [ ] Quality metrics collection
- [ ] Environment-based configuration

---

**End of Document**
