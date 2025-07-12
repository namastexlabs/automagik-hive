# Evaluation: Code Review Command Adaptation for PagBank Multi-Agent System

## Objective
Analyze and adapt the CCDK `/code-review` command for our PagBank multi-agent system, considering our Python/FastAPI/Agno stack, Brazilian financial services compliance, and specialized agent architecture.

## Context Analysis

### Current Stack Compatibility
The CCDK code-review command is designed for general-purpose codebases, but our system has specific requirements:

**Technology Stack:**
- **Python/FastAPI**: Async code patterns, dependency injection, Pydantic models
- **Agno Framework**: Specialized agent patterns, YAML configuration, team orchestration
- **PostgreSQL + PgVector**: Database schema integrity, migration safety
- **Multi-Agent Architecture**: Inter-agent communication, routing logic, context sharing

**Business Context:**
- **Brazilian Financial Services**: LGPD compliance, fraud detection, regulatory requirements
- **Customer Support Focus**: Query routing, escalation patterns, Portuguese language accuracy
- **Production Criticality**: 24/7 availability, transaction safety, audit trails

## Required Review Agent Specializations

### 1. Financial Compliance Auditor
**Focus Areas:**
- LGPD (Lei Geral de Proteção de Dados) compliance in data handling
- PII detection and masking in logs and responses
- Fraud detection keyword validation
- Audit trail completeness
- Transaction integrity checks

**Critical Patterns to Review:**
```python
# LGPD compliance in agent responses
response_data = {"user_data": masked_pii(user_info)}

# Fraud detection in routing logic
if contains_fraud_keywords(query):
    escalate_to_human()

# Audit trail requirements
log_transaction(user_id, action, timestamp, compliance_metadata)
```

### 2. Agent Architecture Validator
**Focus Areas:**
- Agent inheritance patterns from `BaseSpecialistAgent`
- Business unit routing accuracy (Adquirência, Emissão, PagBank, Human)
- Context persistence between agent interactions
- Team orchestration using Agno patterns

**Critical Patterns to Review:**
```python
# Proper agent inheritance
class PagBankAgent(BaseSpecialistAgent):
    def __init__(self):
        super().__init__(business_unit=BusinessUnit.PAGBANK)

# Routing logic integrity
def route_query(query: str) -> BusinessUnit:
    # Must handle all business units
    # Must escalate on frustration detection

# Context sharing between agents
shared_context = AgentContext(
    user_session=session,
    business_context=context,
    escalation_history=history
)
```

### 3. Portuguese Language Accuracy Validator
**Focus Areas:**
- Customer-facing responses in correct PT-BR
- Technical documentation bilingual consistency
- Knowledge base Portuguese accuracy
- Error message localization

**Critical Patterns to Review:**
```python
# Customer responses must be in Portuguese
customer_response = generate_response(query, language="pt-BR")

# Technical logs can be in English
logger.info("Agent routing completed successfully")

# Error messages should be bilingual
error_msg = {
    "pt": "Erro na validação do cartão",
    "en": "Card validation error"
}
```

### 4. Database Schema & Migration Safety Auditor
**Focus Areas:**
- Alembic migration safety
- PgVector embedding integrity
- Agent configuration schema validation
- Knowledge base data consistency

**Critical Patterns to Review:**
```python
# Migration safety
def upgrade():
    # Must be reversible
    # Must preserve existing data
    # Must handle large datasets

# Agent config validation
@validator('business_unit')
def validate_business_unit(cls, v):
    if v not in BusinessUnit:
        raise ValueError(f"Invalid business unit: {v}")
```

### 5. Performance & Scalability Analyst
**Focus Areas:**
- Agent response time optimization
- Database query efficiency
- Memory usage in multi-agent scenarios
- Async/await pattern correctness

**Critical Patterns to Review:**
```python
# Async agent operations
async def process_query(self, query: str) -> AgentResponse:
    # Must handle timeouts
    # Must release resources
    # Must maintain session state

# Database efficiency
@lru_cache(maxsize=1000)
def get_agent_config(agent_id: str):
    # Cache frequently accessed configs
```

### 6. Security & API Safety Validator
**Focus Areas:**
- FastAPI endpoint security
- Input validation and sanitization
- Rate limiting implementation
- API key and token management

**Critical Patterns to Review:**
```python
# Secure endpoint patterns
@app.post("/api/v1/query")
async def process_query(
    request: QueryRequest,
    user: User = Depends(get_current_user),
    rate_limit: None = Depends(rate_limiter)
):
    # Input validation via Pydantic
    # User authentication required
    # Rate limiting applied
```

## Integration with Quality Standards

### Type Checking Integration
- **mypy**: Strict typing for agent interfaces
- **Pydantic**: Runtime validation for agent configs
- **Protocol compliance**: Agent interface adherence

### Linting Standards
- **ruff**: Code style and complexity
- **black**: Consistent formatting
- **isort**: Import organization

### Testing Coverage
- **Unit tests**: Individual agent behavior
- **Integration tests**: Multi-agent flows
- **End-to-end tests**: Complete customer journeys

## Specific Review Patterns for Our System

### 1. Agent Communication Flow Review
```python
# Verify routing logic integrity
def test_routing_patterns():
    assert route_query("problemas com PIX") == BusinessUnit.PAGBANK
    assert route_query("limite do cartão") == BusinessUnit.EMISSAO
    assert route_query("máquina não funciona") == BusinessUnit.ADQUIRENCIA
```

### 2. Frustration Escalation Review
```python
# Ensure human handoff triggers correctly
def validate_escalation_logic():
    session.frustration_level += 1
    if session.frustration_level >= 3:
        assert route_to_human_agent()
```

### 3. Knowledge Base Consistency Review
```python
# Verify CSV knowledge integrity
def validate_knowledge_base():
    for entry in knowledge_csv:
        assert entry.business_unit in BusinessUnit
        assert entry.content_pt is not None
        assert entry.embedding_vector is not None
```

### 4. Configuration Hot Reload Safety
```python
# Ensure config changes don't break active sessions
def test_hot_reload_safety():
    active_sessions = get_active_sessions()
    reload_agent_config("pagbank_agent.yaml")
    assert all(session.is_valid() for session in active_sessions)
```

## Brazilian Financial Services Compliance Considerations

### 1. LGPD Compliance Checklist
- [ ] PII data is properly masked in logs
- [ ] User consent is tracked and respected
- [ ] Data retention policies are enforced
- [ ] Right to deletion is implemented

### 2. Financial Regulation Compliance
- [ ] Transaction data integrity is maintained
- [ ] Audit trails are complete and immutable
- [ ] Fraud detection patterns are comprehensive
- [ ] Regulatory reporting data is accurate

### 3. Operational Security
- [ ] API endpoints require proper authentication
- [ ] Rate limiting prevents abuse
- [ ] Sensitive data is encrypted at rest and in transit
- [ ] Access controls follow principle of least privilege

## Adaptation Recommendations

### 1. Enhanced Agent Allocation Strategy
Modify the dynamic agent allocation to include:
- **Financial Compliance Agent**: Always allocated for production code
- **Portuguese Language Agent**: Always allocated for customer-facing code
- **Agent Architecture Agent**: Always allocated for agent-related changes

### 2. Specialized Coverage Areas
Add to mandatory coverage areas:
- **Business Unit Routing**: Verify all queries route correctly
- **Compliance Validation**: Check LGPD and financial regulations
- **Language Accuracy**: Ensure Portuguese correctness
- **Agent Communication**: Validate inter-agent protocols

### 3. Context-Aware Review Focus
Enhanced context loading for our system:
- Load `CLAUDE.md` for system understanding
- Read business unit documentation
- Analyze agent YAML configurations
- Review knowledge base structure

### 4. Production Risk Assessment
Specialized risk categories for financial services:
- **Transaction Integrity**: Could cause financial losses
- **Compliance Violations**: Could trigger regulatory action
- **Customer Experience**: Could damage brand reputation
- **System Availability**: Could affect 24/7 service requirements

## Implementation Priority

### Phase 1: Core Adaptation
1. Copy CCDK command to `.claude/commands/`
2. Modify agent allocation for our tech stack
3. Add financial compliance review patterns
4. Test with sample agent code

### Phase 2: Specialization
1. Implement Portuguese language validation
2. Add business unit routing verification
3. Integrate with our testing framework
4. Create compliance checklists

### Phase 3: Production Integration
1. Add to CI/CD pipeline
2. Configure for different review scopes
3. Integrate with monitoring systems
4. Train team on usage patterns

## Success Metrics

### Code Quality Improvements
- Reduced production incidents from code defects
- Improved agent routing accuracy
- Faster Portuguese language issue detection
- Better compliance violation prevention

### Developer Productivity
- Faster code review cycles
- More consistent code quality
- Reduced back-and-forth in reviews
- Better architectural decision guidance

### Compliance Assurance
- Zero LGPD violations in production
- Complete audit trail coverage
- Proper PII handling in all components
- Regulatory requirement adherence

## Next Steps

1. **Test Current Command**: Run `/code-review` on existing agent code
2. **Identify Gaps**: Document areas where current command misses our needs
3. **Create Adaptations**: Modify command for our specific requirements
4. **Pilot Testing**: Use adapted command on recent changes
5. **Team Training**: Educate developers on new review process
6. **Integration**: Add to standard development workflow

## Notes

- This evaluation focuses on adapting existing functionality rather than building from scratch
- All adaptations must maintain the core philosophy of high-impact findings only
- Portuguese language accuracy is critical for customer-facing components
- Financial compliance cannot be compromised for any performance gains
- Agent architecture patterns must be preserved to maintain system integrity