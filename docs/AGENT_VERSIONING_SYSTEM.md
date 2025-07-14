# Agent Versioning System Documentation

## Overview

The Agent Versioning System provides database-driven version management for AI agents, enabling:

- **Dynamic Configuration**: Hot-swap agent configurations without deployment
- **A/B Testing**: Test different agent versions simultaneously
- **Rollback Capabilities**: Instantly revert to previous versions
- **Performance Tracking**: Monitor metrics across versions
- **Audit Trail**: Complete history of agent changes

## Architecture

### Core Components

1. **Database Layer** (`db/tables/agent_versions.py`)
   - `AgentVersion`: Store agent configurations and metadata
   - `AgentVersionHistory`: Track changes and audit trail
   - `AgentVersionMetrics`: Performance metrics for A/B testing

2. **Service Layer** (`db/services/agent_version_service.py`)
   - `AgentVersionService`: CRUD operations for versions
   - Version lifecycle management
   - Metrics tracking and aggregation

3. **Factory Layer** (`agents/version_factory.py`)
   - `AgentVersionFactory`: Create agents from database configurations
   - File-to-database migration support
   - Fallback to file-based configuration

4. **API Layer** (`api/routes/agent_versions.py`)
   - RESTful endpoints for version management
   - Agent execution with specific versions
   - Version switching and configuration updates

5. **A/B Testing** (`agents/ab_testing.py`)
   - `ABTestManager`: Manage A/B tests between versions
   - Traffic distribution and user routing
   - Statistical analysis and recommendations

6. **CLI Tools** (`scripts/agent_version_manager.py`)
   - Command-line interface for version management
   - Migration utilities
   - Testing and debugging tools

## Database Schema

### Agent Versions Table

```sql
CREATE TABLE agent_versions (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,        -- "pagbank-specialist"
    version INTEGER NOT NULL,              -- 27, 28, 29...
    config JSONB NOT NULL,                 -- Full configuration
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    is_active BOOLEAN DEFAULT FALSE,
    is_deprecated BOOLEAN DEFAULT FALSE,
    description TEXT,
    UNIQUE(agent_id, version)
);
```

### Version History Table

```sql
CREATE TABLE agent_version_history (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,           -- created, activated, deprecated
    previous_state JSONB,
    new_state JSONB,
    changed_by VARCHAR(255),
    changed_at TIMESTAMP DEFAULT NOW(),
    reason TEXT
);
```

### Metrics Table

```sql
CREATE TABLE agent_version_metrics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL,
    metric_date TIMESTAMP DEFAULT NOW(),
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    average_response_time INTEGER,
    escalation_rate INTEGER,
    user_satisfaction INTEGER
);
```

## Quick Start

### 1. Database Setup

```bash
# Run database migrations
alembic upgrade head

# Or initialize manually
python -c "from db.session import init_database; init_database()"
```

### 2. Migrate Existing Agent

```bash
# Migrate file-based agent to database
python scripts/agent_version_manager.py migrate \
    --agent-id pagbank-specialist \
    --version 27 \
    --created-by admin \
    --description "Initial migration"
```

### 3. Create New Version

```bash
# Create from file
python scripts/agent_version_manager.py create \
    --agent-id pagbank-specialist \
    --version 28 \
    --config-file agents/pagbank/config.yaml \
    --created-by developer \
    --description "Enhanced fraud detection"

# Create from JSON
python scripts/agent_version_manager.py create \
    --agent-id pagbank-specialist \
    --version 29 \
    --config-json '{"agent": {"name": "Enhanced Agent"}, ...}' \
    --activate
```

### 4. Activate Version

```bash
python scripts/agent_version_manager.py activate \
    --agent-id pagbank-specialist \
    --version 28 \
    --changed-by admin \
    --reason "Performance improvements"
```

### 5. Test Agent

```bash
python scripts/agent_version_manager.py test \
    --agent-id pagbank-specialist \
    --version 28 \
    --message "Test message" \
    --debug
```

## API Usage

### Create Version

```bash
curl -X POST http://localhost:7777/v1/agents/ \
    -H "Content-Type: application/json" \
    -d '{
        "agent_id": "pagbank-specialist",
        "version": 28,
        "config": {
            "agent": {"name": "Enhanced Agent"},
            "instructions": "You are an enhanced agent..."
        },
        "description": "Enhanced version with better prompts",
        "created_by": "api_user"
    }'
```

### List Versions

```bash
curl http://localhost:7777/v1/agents/pagbank-specialist/versions
```

### Get Active Version

```bash
curl http://localhost:7777/v1/agents/pagbank-specialist/versions/active
```

### Activate Version

```bash
curl -X PUT http://localhost:7777/v1/agents/pagbank-specialist/versions/28/activate \
    -H "Content-Type: application/json" \
    -d '{
        "reason": "Performance improvements",
        "changed_by": "api_user"
    }'
```

### Run Agent

```bash
curl -X POST http://localhost:7777/v1/agents/pagbank-specialist/run \
    -H "Content-Type: application/json" \
    -d '{
        "message": "Hello, how can you help me?",
        "session_id": "user-123"
    }'
```

### Run Specific Version

```bash
curl -X POST http://localhost:7777/v1/agents/pagbank-specialist/versions/28/run \
    -H "Content-Type: application/json" \
    -d '{
        "message": "Test message",
        "session_id": "test-session"
    }'
```

## A/B Testing

### Create A/B Test

```python
from agents.ab_testing import create_ab_test, ab_test_manager

# Create test configuration
test_config = create_ab_test(
    test_id="pagbank-v27-vs-v28",
    name="Enhanced Prompts Test",
    description="Testing improved prompts in v28",
    agent_id="pagbank-specialist",
    control_version=27,
    test_versions=[28],
    traffic_distribution={27: 70, 28: 30},  # 70% control, 30% test
    duration_days=14,
    min_sample_size=100,
    primary_metric="success_rate"
)

# Start test
ab_test_manager.start_test(test_config)
```

### Get Agent for User

```python
from agents.ab_testing import get_agent_for_user

# Get agent for specific user (consistent version assignment)
agent = get_agent_for_user(
    test_id="pagbank-v27-vs-v28",
    user_id="user-12345",
    session_id="session-abc"
)

# Agent will have A/B test metadata
print(agent.metadata["ab_test_version"])  # 27 or 28
print(agent.metadata["ab_test_variant"])  # "control" or "test"
```

### Record Interaction

```python
from agents.ab_testing import record_test_interaction

# Record interaction results
record_test_interaction(
    test_id="pagbank-v27-vs-v28",
    user_id="user-12345",
    version=28,
    success=True,
    response_time_ms=1500,
    satisfaction_score=8,
    escalated=False
)
```

### Analyze Results

```python
# Analyze test results
analysis = ab_test_manager.analyze_test_results("pagbank-v27-vs-v28")

print(f"Test: {analysis['test_name']}")
print(f"Status: {analysis['status']}")
print(f"Sufficient data: {analysis['sufficient_data']}")

# Results by version
for version, results in analysis['results_by_version'].items():
    print(f"Version {version}:")
    print(f"  Success rate: {results['success_rate']:.1%}")
    print(f"  Avg response time: {results['avg_response_time']:.0f}ms")
    print(f"  Sample size: {results['sample_size']}")

# Recommendations
for rec in analysis['recommendations']:
    print(f"Recommendation: {rec['recommendation']}")
    print(f"Improvement: {rec['improvement_percent']:.1f}%")
```

## Configuration Format

### Agent Configuration Structure

```yaml
# agents/pagbank/config.yaml
agent:
  agent_id: "pagbank-specialist"
  version: 28
  name: "PagBank Digital Banking Expert"
  role: "Digital Banking Specialist"
  description: "Specialist in PIX, transfers, and digital services"

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"
  temperature: 0.7
  max_tokens: 2000

instructions: |
  You are a specialist in PagBank digital banking services.
  Your areas of expertise include:
  - PIX transfers and keys
  - Account management
  - Digital services
  
  Always respond in Portuguese and prioritize security.

tools:
  - "search_knowledge_base"
  - "check_account_status"
  - "verify_transaction_limits"

storage:
  type: "postgres"
  table_name: "pagbank_specialist"
  auto_upgrade_schema: true

memory:
  add_history_to_messages: true
  num_history_runs: 5

escalation_triggers:
  high_value_threshold: 5000
  security_keywords:
    - "bloqueio por segurança"
    - "transação bloqueada"
    - "suspeita de fraude"

markdown: false
show_tool_calls: true
```

## Version Management Workflow

### 1. Development Workflow

```bash
# 1. Create new version from existing
python scripts/agent_version_manager.py clone \
    --agent-id pagbank-specialist \
    --source-version 27 \
    --target-version 28

# 2. Update configuration
python scripts/agent_version_manager.py show \
    --agent-id pagbank-specialist \
    --version 28 \
    --format yaml > temp_config.yaml

# Edit temp_config.yaml

python scripts/agent_version_manager.py create \
    --agent-id pagbank-specialist \
    --version 28 \
    --config-file temp_config.yaml \
    --description "Updated prompts and tools"

# 3. Test new version
python scripts/agent_version_manager.py test \
    --agent-id pagbank-specialist \
    --version 28 \
    --message "Test message"

# 4. Activate when ready
python scripts/agent_version_manager.py activate \
    --agent-id pagbank-specialist \
    --version 28
```

### 2. A/B Testing Workflow

```python
# 1. Create test
test_config = create_ab_test(
    test_id="enhancement-test",
    name="Enhanced Agent Test",
    description="Testing new features",
    agent_id="pagbank-specialist",
    control_version=27,
    test_versions=[28],
    traffic_distribution={27: 80, 28: 20}
)

# 2. Start test
ab_test_manager.start_test(test_config)

# 3. Monitor results (daily)
analysis = ab_test_manager.analyze_test_results("enhancement-test")

# 4. Make decision
if analysis['recommendations'][0]['is_significant']:
    if analysis['recommendations'][0]['improvement_percent'] > 5:
        # Activate new version
        version_service.activate_version("pagbank-specialist", 28)
    else:
        # Revert to control
        pass
```

### 3. Production Deployment

```bash
# 1. Validate version
python scripts/agent_version_manager.py show \
    --agent-id pagbank-specialist \
    --version 28

# 2. Run comprehensive tests
python scripts/agent_version_manager.py test \
    --agent-id pagbank-specialist \
    --version 28 \
    --message "Production test message"

# 3. Gradual rollout via A/B test
# Start with 5% traffic, increase gradually

# 4. Full activation
python scripts/agent_version_manager.py activate \
    --agent-id pagbank-specialist \
    --version 28 \
    --reason "Production deployment after successful A/B test"

# 5. Monitor metrics
python scripts/agent_version_manager.py history \
    --agent-id pagbank-specialist \
    --days 1
```

## Best Practices

### Version Numbering

- Use sequential integers: 27, 28, 29, ...
- No gaps or special numbering schemes
- Higher numbers = newer versions

### Configuration Management

- Always include version number in config
- Use descriptive commit messages
- Test configurations before activation
- Keep rollback plan ready

### A/B Testing

- Run tests for sufficient duration (1-2 weeks)
- Ensure adequate sample sizes (100+ per variant)
- Monitor multiple metrics, not just primary
- Have clear success criteria

### Performance Monitoring

- Track key metrics for each version
- Set up alerts for significant changes
- Regular performance reviews
- Archive old metrics data

### Security

- Validate all configuration changes
- Audit trail for all modifications
- Secure API endpoints
- Regular security reviews

## Troubleshooting

### Common Issues

1. **Version Not Found**
   ```bash
   # Check available versions
   python scripts/agent_version_manager.py list --agent-id pagbank-specialist
   
   # Check if agent exists
   python scripts/agent_version_manager.py list-agents
   ```

2. **Configuration Errors**
   ```bash
   # Validate configuration
   python scripts/agent_version_manager.py show \
       --agent-id pagbank-specialist \
       --version 28 \
       --format yaml
   ```

3. **Database Connection Issues**
   ```bash
   # Test database connection
   python -c "from db.session import test_connection; print(test_connection())"
   
   # Check migration status
   alembic current
   ```

4. **A/B Test Issues**
   ```python
   # Check active tests
   from agents.ab_testing import ab_test_manager
   print(ab_test_manager.list_active_tests())
   
   # Get test details
   summary = ab_test_manager.get_test_summary("test-id")
   ```

### Debug Mode

```bash
# Enable debug mode for detailed logging
python scripts/agent_version_manager.py test \
    --agent-id pagbank-specialist \
    --version 28 \
    --message "Debug test" \
    --debug \
    --verbose
```

## Performance Considerations

### Database Optimization

- Use connection pooling
- Index frequently queried columns
- Regular maintenance and cleanup
- Monitor query performance

### Caching

- Cache active version configurations
- Implement configuration refresh mechanism
- Use Redis for distributed caching
- Cache A/B test assignments

### Scalability

- Horizontal scaling for API endpoints
- Database read replicas
- Async processing for metrics
- Load balancing for agent creation

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from agents.version_factory import create_versioned_agent

app = FastAPI()

@app.post("/chat")
async def chat(
    message: str,
    agent_id: str = "pagbank-specialist",
    version: int = None,
    session_id: str = None
):
    agent = create_versioned_agent(
        agent_id=agent_id,
        version=version,
        session_id=session_id
    )
    
    response = agent.run(message)
    return {
        "response": response.content,
        "version": agent.metadata.get("version"),
        "agent_id": agent_id
    }
```

### A/B Testing Integration

```python
from agents.ab_testing import get_agent_for_user, record_test_interaction

@app.post("/chat-ab")
async def chat_with_ab_test(
    message: str,
    user_id: str,
    test_id: str,
    session_id: str = None
):
    # Get agent for user (consistent version assignment)
    agent = get_agent_for_user(
        test_id=test_id,
        user_id=user_id,
        session_id=session_id
    )
    
    # Process message
    start_time = time.time()
    response = agent.run(message)
    response_time = int((time.time() - start_time) * 1000)
    
    # Record interaction
    record_test_interaction(
        test_id=test_id,
        user_id=user_id,
        version=agent.metadata["ab_test_version"],
        success=True,  # Determine based on response
        response_time_ms=response_time
    )
    
    return {
        "response": response.content,
        "version": agent.metadata["ab_test_version"],
        "variant": agent.metadata["ab_test_variant"]
    }
```

## Conclusion

The Agent Versioning System provides a robust foundation for managing AI agent configurations in production environments. It enables:

- **Rapid iteration** through database-driven configurations
- **Risk mitigation** through A/B testing and rollback capabilities
- **Performance optimization** through metrics tracking and analysis
- **Operational excellence** through comprehensive audit trails

For more information, see the example implementation in `examples/agent_versioning_demo.py` and the CLI documentation in `scripts/agent_version_manager.py --help`.