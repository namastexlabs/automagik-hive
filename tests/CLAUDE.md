# Tests Directory - Multi-Agent Testing Architecture

<system_context>
This directory contains comprehensive testing components for the PagBank multi-agent system. The testing architecture ensures 90%+ coverage across agents, routing logic, knowledge retrieval, memory management, and end-to-end customer scenarios with Portuguese language validation.
</system_context>

## Core Testing Principles

### Quality Gates & Coverage Targets
- **Unit Tests**: 95%+ coverage for individual components
- **Integration Tests**: 90%+ coverage for agent interactions
- **End-to-End Tests**: 85%+ coverage for customer scenarios
- **Performance Tests**: Response times under 5000ms, throughput > 20 queries/sec
- **Language Tests**: All customer responses validated in Portuguese (pt-BR)

### Testing Philosophy
Each test category follows the multi-agent architecture patterns:
- **Isolated Testing**: Agents tested independently with mocked dependencies
- **Interaction Testing**: Agent communication and routing validation
- **Scenario Testing**: Complete customer journey validation
- **Compliance Testing**: Financial services regulations and security

## Directory Structure

```
tests/
├── CLAUDE.md                    # This file - Testing guidelines
├── conftest.py                  # Pytest configuration and fixtures
├── unit/                        # Unit tests for individual components
│   ├── test_routing_logic.py    # Routing engine and business unit logic
│   ├── test_knowledge_base.py   # Knowledge retrieval and filtering
│   ├── test_business_unit_agents.py # Individual agent behavior
│   └── domain/                  # Domain-specific unit tests
├── integration/                 # Integration tests for agent interactions
│   ├── test_end_to_end_flow.py  # Complete query processing pipeline
│   ├── test_knowledge_retrieval.py # Knowledge integration scenarios
│   ├── test_hybrid_unit_routing.py # Business unit routing accuracy
│   └── test_infrastructure.py   # Database and system integration
├── performance/                 # Performance and load testing
│   └── test_baseline_metrics.py # Response time and throughput tests
└── test_*.py                    # System-level tests (orchestrator, memory, etc.)
```

## Key References

- **Agno Testing Patterns**: `genie/reference/agno-patterns.md` - Agent testing frameworks
- **Demo App Tests**: `genie/archive/agno-demo-app/tests/` - Reference test patterns
- **Performance Benchmarks**: `tests/performance/` - Baseline metrics and scalability
- **Integration Examples**: `tests/integration/` - Multi-agent interaction patterns

## Critical Testing Rules

### Must Do ✅
- **ALWAYS use Portuguese test queries** for customer-facing scenarios
- **ALWAYS test all business units** (Adquirência, Emissão, PagBank, Human Handoff)
- **ALWAYS validate routing accuracy** with confidence scores and reasoning
- **ALWAYS test frustration detection** and escalation paths
- **ALWAYS test knowledge filtering** by business unit
- **ALWAYS test memory persistence** and session management
- **ALWAYS test concurrent performance** under load
- **ALWAYS validate compliance** requirements (PII, audit trails)
- **ALWAYS test error scenarios** and graceful degradation
- **ALWAYS run performance baselines** before deployment
- **ALWAYS test with realistic Portuguese customer queries**
- **ALWAYS validate response time thresholds** (under 5 seconds)

### Never Do ❌
- **NEVER test with English customer queries** (use Portuguese pt-BR)
- **NEVER skip routing accuracy validation** for any business unit
- **NEVER ignore performance degradation** warnings
- **NEVER test with fake/unrealistic customer data**
- **NEVER skip compliance validation** tests
- **NEVER test without proper database cleanup**
- **NEVER ignore memory leak indicators**
- **NEVER skip frustration escalation testing**
- **NEVER test agents in isolation** without routing context
- **NEVER skip knowledge base consistency** validation

## Testing Architecture Patterns

### Agent Testing Pattern (From Agno Reference)
```python
# From genie/reference/agno-patterns.md - Testing Pattern
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

### Multi-Agent Integration Testing
```python
# From tests/integration/test_end_to_end_flow.py
class TestEndToEndQueryFlow:
    def test_adquirencia_query_flow(self):
        """Test complete flow for Adquirência queries"""
        queries = [
            "Como antecipar vendas da minha máquina?",
            "Preciso fazer antecipação de recebíveis"
        ]
        
        for query in queries:
            # Step 1: Query analysis
            filters = extract_filters_from_query(query)
            assert filters.get('business_unit') == 'Adquirência Web'
            
            # Step 2: Routing decision
            routing_decision = self.routing_engine.route_query(query)
            assert routing_decision.primary_unit == BusinessUnit.ADQUIRENCIA
            assert routing_decision.confidence > 0.0
```

### Performance Testing Pattern
```python
# From tests/performance/test_baseline_metrics.py
class TestBaselineMetrics:
    def test_routing_speed_baseline(self):
        """Test baseline routing speed"""
        routing_times = []
        
        for query in self.all_queries:
            start_time = time.perf_counter()
            decision = self.routing_engine.route_query(query)
            end_time = time.perf_counter()
            
            routing_time = end_time - start_time
            routing_times.append(routing_time)
        
        avg_time = mean(routing_times)
        
        # Performance assertions
        assert avg_time < 0.1, "Average routing time should be under 100ms"
        assert max(routing_times) < 0.5, "Max routing time should be under 500ms"
```

### Portuguese Language Testing Pattern
```python
# From tests/conftest.py - Sample fixtures
@pytest.fixture
def sample_user_message():
    """Sample user message for testing."""
    return {
        "content": "Olá, gostaria de saber sobre meu saldo",
        "user_id": "test_user_123",
        "session_id": "test_session_456",
        "timestamp": "2024-01-01T10:00:00Z",
        "language": "pt-BR"
    }

@pytest.fixture
def sample_knowledge_entries():
    """Sample knowledge entries for testing."""
    return [
        {
            "question": "Como consultar saldo?",
            "answer": "Para consultar seu saldo, acesse o app PagBank...",
            "keywords": ["saldo", "consultar", "conta"],
            "team_filter": "digital_account"
        }
    ]
```

## Test Configuration (From conftest.py)

### Essential Fixtures
- **`test_db`**: PostgreSQL test database initialization
- **`claude_client`**: Anthropic client for agent testing
- **`sample_user_message`**: Portuguese customer queries
- **`sample_knowledge_entries`**: Business unit knowledge samples
- **`performance_thresholds`**: Response time and memory limits
- **`integration_test_flow`**: End-to-end scenario data

### Performance Thresholds (From conftest.py)
```python
performance_thresholds = {
    "response_time_ms": 5000,      # 5 seconds max response
    "memory_usage_mb": 512,        # 512 MB memory limit
    "db_query_time_ms": 1000,      # 1 second database queries
    "knowledge_search_ms": 2000,   # 2 seconds knowledge retrieval
}
```

### Mock Configurations
- **`mock_anthropic_response`**: Claude model response simulation
- **`mock_embedding_response`**: Vector embeddings for knowledge search
- **`cleanup_test_data`**: Automatic test data cleanup

## Testing Categories

### Unit Tests (/unit/)
**Purpose**: Test individual components in isolation
- **Routing Logic**: Business unit classification accuracy
- **Knowledge Base**: CSV filtering and search efficiency
- **Business Unit Agents**: Individual agent response quality
- **Domain Logic**: Financial calculations and validations

**Coverage Target**: 95%+

### Integration Tests (/integration/)
**Purpose**: Test component interactions and workflows
- **End-to-End Flow**: Complete customer query processing
- **Knowledge Retrieval**: Cross-system knowledge integration
- **Hybrid Unit Routing**: Multi-business unit scenarios
- **Infrastructure**: Database and system integrations

**Coverage Target**: 90%+

### Performance Tests (/performance/)
**Purpose**: Validate system performance under load
- **Baseline Metrics**: Response time and throughput baselines
- **Scalability**: Performance with high query volumes
- **Concurrent Load**: Multi-user scenario testing
- **Memory Efficiency**: Resource usage optimization

**Performance Targets**: 
- Response time < 5000ms
- Throughput > 20 queries/sec
- Memory usage < 512MB

### System Tests (Root Level)
**Purpose**: Test high-level system functionality
- **Orchestrator**: Main routing and coordination logic
- **Memory Manager**: Session persistence and context management
- **Session Manager**: User session lifecycle
- **MCP Integration**: External system integrations

## Portuguese Testing Requirements

### Language Validation Rules
- All customer-facing responses MUST be in Portuguese (pt-BR)
- Test queries MUST use realistic Portuguese customer language
- Error messages MUST be bilingual (Portuguese for customers, English for system)
- Knowledge base content MUST be in Portuguese

### Sample Portuguese Test Queries by Business Unit
```python
# From tests/unit/test_routing_logic.py
adquirencia_queries = [
    "Como antecipar vendas da minha máquina?",
    "Preciso fazer antecipação de recebíveis",
    "Antecipação agendada não está funcionando"
]

emissao_queries = [
    "Meu cartão não chegou",
    "Problemas com cartão de crédito",
    "Limite do cartão múltiplo"
]

pagbank_queries = [
    "Como fazer PIX?",
    "Problemas no aplicativo PagBank",
    "Folha de pagamento não funciona"
]
```

## Compliance Testing Requirements

### Financial Services Compliance
- **PII Data Protection**: Encryption and secure handling tests
- **Audit Trail**: Transaction logging and traceability tests
- **Fraud Detection**: Suspicious activity pattern tests
- **Regulatory Compliance**: Financial regulation adherence tests

### Security Testing
- **Data Encryption**: In-memory and database encryption tests
- **Access Control**: User authorization and authentication tests
- **Input Validation**: SQL injection and XSS prevention tests
- **Session Security**: Secure session management tests

## Essential Testing Commands

### Run Full Test Suite
```bash
# Complete test suite with coverage
uv run pytest --cov=agents --cov=context --cov=config -v

# Specific test categories
uv run pytest tests/unit/ -v                    # Unit tests only
uv run pytest tests/integration/ -v             # Integration tests only
uv run pytest tests/performance/ -v             # Performance tests only
```

### Portuguese Language Tests
```bash
# Test Portuguese routing accuracy
uv run pytest tests/unit/test_routing_logic.py::TestRoutingEngine::test_route_query_pagbank -v

# Test end-to-end Portuguese scenarios
uv run pytest tests/integration/test_end_to_end_flow.py -v
```

### Performance and Load Tests
```bash
# Baseline performance metrics
uv run pytest tests/performance/test_baseline_metrics.py -v

# Concurrent load testing
uv run pytest tests/performance/test_baseline_metrics.py::TestBaselineMetrics::test_concurrent_routing_performance -v
```

### Agent-Specific Tests
```bash
# Test individual business unit agents
uv run pytest tests/unit/test_business_unit_agents.py -v

# Test routing logic accuracy
uv run pytest tests/integration/test_hybrid_unit_routing.py -v
```

## Quality Gates Before Deployment

### Pre-Deployment Checklist
1. **Unit Test Coverage**: Minimum 95% for all components
2. **Integration Coverage**: Minimum 90% for agent interactions
3. **Performance Benchmarks**: All thresholds met or improved
4. **Portuguese Validation**: All customer scenarios tested in Portuguese
5. **Routing Accuracy**: 100% accuracy for known query patterns
6. **Memory Leak Detection**: No memory growth over extended testing
7. **Compliance Validation**: All financial regulations verified
8. **Error Handling**: Graceful degradation for all failure scenarios

### Continuous Integration Requirements
- All tests MUST pass before merge
- Performance regressions MUST be investigated
- New features MUST include corresponding tests
- Portuguese language tests MUST be maintained
- Knowledge base changes MUST include test updates

## Review Task for Context Transfer ✅ COMPREHENSIVE VALIDATION

### Content Verification Checklist - Testing Architecture Domain
**Final validation before completing context transfer across all CLAUDE.md files:**

#### ✅ Core Testing Patterns Documented
1. ✅ **Multi-agent testing architecture** ensuring 90%+ coverage across agents, routing, and scenarios
2. ✅ **Quality gates and coverage targets** with specific thresholds for each testing category
3. ✅ **Portuguese language testing** requirements for all customer-facing scenarios
4. ✅ **Compliance testing framework** for financial services regulations and security
5. ✅ **Performance testing patterns** with baseline metrics and scalability validation
6. ✅ **Integration testing strategy** covering agent interactions and end-to-end flows
7. ✅ **Essential testing commands** for comprehensive test suite execution

#### ✅ Cross-Reference Validation with Other CLAUDE.md Files
- **agents/CLAUDE.md**: Agent testing should cover all documented factory patterns and business units
- **teams/CLAUDE.md**: Team routing testing should validate all documented modes and routing accuracy
- **workflows/CLAUDE.md**: Workflow testing should verify step execution and context preservation
- **config/CLAUDE.md**: Configuration testing should validate all environment setups and security
- **db/CLAUDE.md**: Database testing should cover all schema operations and performance patterns
- **api/CLAUDE.md**: API testing should validate all endpoints, security features, and streaming

#### ✅ Missing Content Identification
**Content that should be transferred TO other CLAUDE.md files:**
- ❌ All testing-specific content properly contained in this file
- Testing command references already distributed to relevant files

**Content that should be transferred FROM other CLAUDE.md files:**
- Agent testing requirements FROM `agents/CLAUDE.md` ✅ Already integrated
- Team routing validation FROM `teams/CLAUDE.md` ✅ Already integrated
- Workflow testing patterns FROM `workflows/CLAUDE.md` ✅ Already integrated
- Configuration testing FROM `config/CLAUDE.md` ✅ Already integrated
- Database testing FROM `db/CLAUDE.md` ✅ Already integrated
- API testing patterns FROM `api/CLAUDE.md` ✅ Already integrated

#### ✅ Duplication Prevention
**Content properly separated to avoid overlap:**
- ✅ Testing strategies documented here, NOT scattered across component files
- ✅ Quality gates and coverage targets centralized here
- ✅ Portuguese testing requirements consolidated here
- ✅ Compliance testing framework unified here

#### ✅ Context Transfer Requirements for Future Development
**Essential testing context that must be preserved:**
1. **90%+ Coverage Target**: Unit (95%), Integration (90%), End-to-End (85%) across all components
2. **Portuguese Language Validation**: All customer scenarios must be tested in pt-BR
3. **Multi-Agent Testing**: Isolated and interaction testing for parallel agent development
4. **Performance Thresholds**: Response time <5s, throughput >20 queries/sec, memory <512MB
5. **Compliance Requirements**: Financial services regulations, PII protection, audit trails
6. **Quality Gates**: All tests must pass before deployment with no performance regressions

#### ✅ Integration Validation Requirements
**Validate these integration points when implementing:**
- **Testing → Agent Integration**: Verify all documented agent patterns are testable
- **Testing → Team Integration**: Confirm team routing accuracy meets documented targets
- **Testing → Workflow Integration**: Test step-by-step execution and context preservation
- **Testing → Database Integration**: Validate all schema operations and health checks
- **Testing → API Integration**: Ensure all endpoints and security features are tested
- **Testing → Config Integration**: Test all environment configurations and validation

### ✅ Content Successfully Organized in tests/CLAUDE.md
- ✅ **Testing Architecture**: Multi-agent testing with quality gates and coverage targets
- ✅ **Quality Standards**: Specific coverage percentages and performance thresholds
- ✅ **Portuguese Requirements**: Language validation for all customer-facing scenarios
- ✅ **Compliance Framework**: Financial services regulations and security testing
- ✅ **Performance Baselines**: Response time, throughput, and memory usage targets
- ✅ **Integration Patterns**: Agent interaction and end-to-end scenario validation

### ✅ Current Testing State Analysis
1. **Coverage Assessment**: Framework established for analyzing coverage across all components
2. **Performance Baseline**: Thresholds documented for establishing current benchmarks
3. **Portuguese Content**: Requirements validated for all Portuguese test scenarios
4. **Integration Gaps**: Patterns provided for identifying missing integration scenarios
5. **Compliance Coverage**: Framework established for financial services compliance testing

### ✅ Testing Enhancement Priorities
1. **Agent Version Testing**: Patterns for testing dynamic agent versioning
2. **Knowledge Sync Testing**: Framework for knowledge base hot reload scenarios
3. **Escalation Path Testing**: Patterns for validating human handoff scenarios
4. **Cross-Business Unit**: Framework for queries spanning multiple business units
5. **Performance Optimization**: Patterns for identifying and optimizing bottlenecks

### ✅ Final Context Transfer Validation - ALL CLAUDE.md FILES COMPLETE

**✅ Complete Set of Enhanced CLAUDE.md Files:**
1. **agents/CLAUDE.md**: Agent development with factory patterns and business unit specifications
2. **teams/CLAUDE.md**: Team orchestration with Ana routing and mode="route" implementation
3. **workflows/CLAUDE.md**: Multi-step workflow orchestration with human handoff evolution
4. **config/CLAUDE.md**: Global configuration management with environment scaling
5. **db/CLAUDE.md**: Database schema and management with PostgreSQL/SQLite patterns
6. **api/CLAUDE.md**: FastAPI integration with Agno-first architecture and streaming
7. **tests/CLAUDE.md**: Comprehensive testing architecture with quality gates

**✅ Context Transfer Success Criteria Met:**
- ✅ No important context lost during organization
- ✅ Each CLAUDE.md file covers its domain completely
- ✅ No overlap or duplication between files
- ✅ All reference material properly absorbed and organized
- ✅ Contextual documentation supports multi-agent development workflow
- ✅ Cross-reference validation ensures integration points are clear
- ✅ Missing content identification prevents gaps in implementation
- ✅ Duplication prevention maintains clean separation of concerns
- ✅ Future development context preserved for long-term maintainability

### ✅ VALIDATION COMPLETED - CONTEXT TRANSFER SUCCESSFUL

All CLAUDE.md files now contain comprehensive review task sections that ensure proper context transfer without duplication or missing content. The documentation supports the multi-agent development workflow with clear integration points and validation requirements.
