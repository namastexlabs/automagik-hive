# Agno Framework Implementation Patterns

**Purpose**: Code examples and best practices for implementing Agno components  
**Complement**: For parameter documentation, see [Agno Parameters](@genie/reference/agno-patterns-index.md)  
**Navigation**: [THIS FILE] | [Parameter Reference →](@genie/reference/agno-patterns-index.md)

## Team Routing Pattern

### Basic Team with mode=config["team"]["mode"]
```python
from agno import Team, Agent

def get_routing_team():
    return Team(
        name="Customer Support Team",
        team_id="support-team",
        mode=config["team"]["mode"],  # From YAML
        members=[
            billing_agent,
            technical_agent,
            sales_agent
        ],
        model=config["model"]  # From YAML
    )
```

### Team Routing Logic
The `mode=config["team"]["mode"]` automatically:
1. Analyzes user query
2. Selects most appropriate agent
3. Routes request to that agent
4. Returns agent response

No manual orchestration needed!

## Agent Definition Pattern

### Specialist Agent
```python
from agno import Agent, ModelConfig

billing_agent = Agent(
    name="Billing Specialist",
    agent_id="billing-agent", 
    model=config["model"]  # From YAML,
    instructions=[
        "You are a billing specialist",
        "Help with invoices, payments, and account issues",
        "Always be polite and professional"
    ],
    tools=[search_knowledge_base, check_account_status],
    markdown=True,
    debug_mode=True
)
```

### Agent with System Prompt
```python
pagbank_agent = Agent(
    name="PagBank Digital Banking",
    agent_id="pagbank-specialist",
    system_prompt="""You are a PagBank digital banking specialist.
    
    Your expertise includes:
    - PIX transfers and QR codes
    - Account management
    - Mobile top-ups
    - Investment products
    
    Always respond in Portuguese (pt-BR).
    """,
    model=config["model"]  # From YAML
)
```

## Tool Integration Pattern

### Custom Tool Definition
```python
from agno import tool
from typing import Optional

@tool
def search_knowledge_base(
    query: str,
    business_unit: Optional[str] = None
) -> str:
    """Search the knowledge base for relevant information."""
    # Implementation
    return results

# Attach to agent
agent = Agent(
    name="Support Agent",
    tools=[search_knowledge_base]
)
```

## Workflow Pattern

### Sequential Workflow
```python
from agno import Workflow

categorization_workflow = Workflow(
    name="Typification Workflow",
    workflow_id="typification-v1",
    steps=[
        level1_categorizer,
        level2_categorizer,
        level3_categorizer,
        level4_categorizer,
        level5_finalizer
    ]
)
```

### Workflow Step Agent
```python
level1_agent = Agent(
    name="Level 1 Categorizer",
    agent_id="typification-level1",
    instructions=[
        "Categorize the query into main business unit",
        "Options: Adquirência, Emissão, PagBank, Outros"
    ],
    response_model=Level1Category  # Pydantic model
)
```

## Session Management Pattern

### With PostgreSQL
```python
from agno import Agent
from agno.models import Session

agent = Agent(
    name="Stateful Agent",
    storage=Storage(
        provider="postgresql",
        config=PostgresqlConfig(
            db_url=os.getenv("DATABASE_URL")
        )
    ),
    # Session automatically managed
)

# Usage preserves context
response = agent.run(
    messages=[{"role": "user", "content": "Hello"}],
    session_id="user-123"  # Automatic session tracking
)
```

## Streaming Response Pattern

### Enable Streaming
```python
from agno import Agent

agent = Agent(
    name="Streaming Agent",
    markdown=True,
    # Streaming enabled by default
)

# In FastAPI
from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    async def generate():
        stream = agent.run_stream(
            messages=request.messages,
            stream=True
        )
        async for chunk in stream:
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

## Playground Integration Pattern

### Unified Playground Endpoint
```python
from agno.playground import get_playground_router
from agno.models import ModelConfig

# Create playground with all components
playground_router = get_playground_router(
    agents=[ana_agent, support_agent],
    teams=[ana_team],
    workflows=[typification_workflow],
    default_model=config["model"]  # From YAML,
    storage_path="./storage"
)

app.include_router(playground_router, prefix="/playground")
```

## Model Configuration Pattern

### Claude Models
```python
# Opus 4 - Most capable
opus_config = ModelConfig(
    provider="anthropic",
    name="claude-opus-4-20250514",
    temperature=0.7
)

# Sonnet - Balanced
sonnet_config = ModelConfig(
    provider="anthropic",
    name="claude-sonnet-4-20250514",
    temperature=0.5
)

# Haiku - Fast and efficient
haiku_config = ModelConfig(
    provider="anthropic",
    name="claude-haiku-4-20250514",
    temperature=0.3
)
```

## Error Handling Pattern

### Graceful Fallbacks
```python
try:
    response = agent.run(messages=messages)
except AgentError as e:
    # Fall back to human handoff
    return human_handoff_agent.run(
        messages=messages + [{
            "role": "system",
            "content": f"Previous agent failed: {e}"
        }]
    )
```

## Testing Pattern

### Agent Testing
```python
import pytest
from agno.testing import AgentTestCase

class TestPagBankAgent(AgentTestCase):
    def test_pix_query(self):
        response = self.run_agent(
            agent=pagbank_agent,
            message="Como faço um PIX?"
        )
        
        assert "PIX" in response.content
        assert response.metadata["language"] == "pt-BR"
```

## Configuration Loading Pattern

### YAML to Agent
```python
import yaml
from agno import Agent

def load_agent_from_yaml(yaml_path: str) -> Agent:
    with open(yaml_path) as f:
        config = yaml.safe_load(f)
    
    return Agent(
        name=config["name"],
        agent_id=config["agent_id"],
        model=config["model"]  # From YAML,
        instructions=config["instructions"],
        tools=load_tools(config.get("tools", [])),
        debug_mode=config.get("debug_mode", True)
    )
```

## Database Integration Pattern

### With Alembic
```python
# alembic/env.py
from agno.storage.postgresql import Base
from your_app.models import CustomModels

target_metadata = Base.metadata

# Migrations handle Agno tables + your custom tables
```

## Performance Pattern

### Connection Pooling
```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

## Monitoring Pattern

### Agent Metrics
```python
from agno.monitoring import AgentMonitor

monitor = AgentMonitor(
    agent=ana_agent,
    metrics_backend="prometheus"
)

# Automatic tracking of:
# - Response times
# - Token usage  
# - Error rates
# - Session duration
```
