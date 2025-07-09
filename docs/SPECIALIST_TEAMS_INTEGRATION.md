# Specialist Teams Integration Documentation

## Overview

This document provides comprehensive documentation for the PagBank Multi-Agent System's specialist teams integration, including the newly implemented Insurance Team and cross-team coordination capabilities.

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      Main Orchestrator                           │
│  - Routes queries to appropriate teams                          │
│  - Manages session state across teams                          │
│  - Handles escalations and handoffs                           │
└───────────────┬─────────────────────────────────┬──────────────┘
                │                                 │
    ┌───────────▼───────────┐         ┌──────────▼──────────┐
    │   Routing Logic       │         │   Session Manager    │
    │ - Keyword matching    │         │ - State preservation │
    │ - Context awareness   │         │ - Frustration tracking│
    │ - Confidence scoring  │         │ - Team history       │
    └───────────────────────┘         └──────────────────────┘
                │
    ┌───────────┴─────────────────────────────────────────┐
    │                  Specialist Teams                    │
    ├─────────────┬─────────────┬────────────┬───────────┤
    │   Cards     │  Digital    │ Investments│  Credit   │ Insurance
    │   Team      │  Account    │    Team    │   Team    │   Team
    └─────────────┴─────────────┴────────────┴───────────┴─────────
```

## Teams Overview

### 1. Cards Team (Cartões)
- **Purpose**: Handle all card-related queries
- **Specialties**: Credit/debit cards, limits, benefits, fraud
- **Key Features**: Instant blocking, cashback calculation, fraud detection

### 2. Digital Account Team (Conta Digital)
- **Purpose**: Manage account and transaction queries
- **Specialties**: PIX, transfers, balance, statements
- **Key Features**: Instant PIX, QR code generation, scheduled transfers

### 3. Investments Team (Investimentos)
- **Purpose**: Investment advisory and portfolio management
- **Specialties**: CDB, Treasury, funds, savings goals
- **Key Features**: Risk profiling, simulations, tax calculations
- **Compliance**: Mandatory investment disclaimers

### 4. Credit Team (Crédito)
- **Purpose**: Credit and loan services
- **Specialties**: FGTS advance, payroll loans, personal credit
- **Key Features**: Credit analysis, fraud detection, simulations
- **Security**: Enhanced fraud detection for advance fee scams

### 5. Insurance Team (Seguros) - NEW
- **Purpose**: Insurance and protection products
- **Specialties**: Life, home, card protection, health plans
- **Key Features**: 
  - R$ 20,000 monthly prize draw (always mentioned)
  - R$ 24.90/month health plan with NO waiting period
  - Claims processing and assistance
  - Premium calculations

## Cross-Team Integration Features

### 1. Session State Preservation

Teams share session context to maintain continuity:

```python
# Session context preserved across teams
{
    "session_id": "abc123",
    "user_id": "user456",
    "context": {
        "customer_name": "João Silva",
        "customer_segment": "premium",
        "previous_teams": ["cartoes", "investimentos"],
        "discovered_info": {
            "has_cdb": True,
            "cdb_amount": 50000,
            "card_limit": 5000
        },
        "interaction_count": 3,
        "frustration_level": 0
    }
}
```

### 2. Intelligent Routing

The routing logic considers multiple factors:

1. **Keyword Matching**: Direct keywords for each team
2. **Context Awareness**: Previous interactions influence routing
3. **Confidence Scoring**: Determines routing certainty
4. **Multi-Intent Detection**: Handles queries spanning multiple teams

### 3. Team Handoffs

Seamless transitions between teams:

```python
# Investment team suggests insurance
response = {
    "content": "Para proteção adicional, recomendo nosso time de seguros.",
    "suggested_actions": ["transfer_to_insurance_team"],
    "handoff_context": {
        "from_team": "investimentos",
        "reason": "patrimony_protection",
        "relevant_info": {"has_investments": True}
    }
}
```

### 4. Knowledge Sharing

Information discovered by one team is available to others:

- Investment team discovers customer has R$ 50k in CDB
- Cards team can suggest using CDB as collateral for limit increase
- Insurance team can recommend appropriate coverage levels

## Integration Patterns

### Pattern 1: Sequential Team Engagement

Customer journey through multiple teams:

```
User: "Quero abrir uma conta" → Digital Account Team
User: "E como faço para investir?" → Investment Team  
User: "Preciso de seguro para proteger?" → Insurance Team
```

### Pattern 2: Cross-Reference Queries

Queries that require knowledge from multiple teams:

```
User: "Meu investimento está protegido?"
→ Investment Team (FGC protection info)
→ Suggests Insurance Team (additional protection)
```

### Pattern 3: Bundled Products

Products that span multiple teams:

```
User: "Quero cartão com seguro viagem"
→ Cards Team (card features)
→ Insurance Team (travel insurance details)
→ Coordinated response with both products
```

## Testing Strategy

### Unit Tests

Each team has comprehensive unit tests:
- `/tests/test_insurance_team.py` - Insurance team specific
- `/tests/test_team_framework.py` - Base framework tests

### Integration Tests

Cross-team scenarios:
- `/tests/integration/test_cross_team.py` - Team coordination
- `/tests/integration/test_multi_routing.py` - Routing logic

### Test Coverage

1. **Individual Team Functions**: 95%+ coverage
2. **Cross-Team Handoffs**: Full scenario testing
3. **Session Preservation**: State consistency tests
4. **Error Handling**: Fallback mechanisms
5. **Performance**: Sub-2s response time

## Configuration Management

### Team Configuration

Each team configured in `team_config.py`:

```python
TeamConfig(
    team_id="seguros",
    team_name="Time de Seguros e Saúde",
    knowledge_filters=["seguro", "protecao", "cobertura"],
    routing_keywords=["seguro", "vida", "saúde", "proteção"],
    priority_topics=["sinistro", "cancelamento_urgente"],
    escalation_threshold=0.7
)
```

### Knowledge Filters

Teams use specific filters to access relevant knowledge:

```python
knowledge_filters = {
    "cartoes": ["cartao", "credito", "debito", "fatura"],
    "conta_digital": ["conta", "pix", "transferencia"],
    "investimentos": ["investimento", "cdb", "tesouro"],
    "credito": ["credito", "emprestimo", "fgts"],
    "seguros": ["seguro", "protecao", "cobertura"]
}
```

## Performance Optimization

### Caching Strategy

1. **Team Responses**: 5-minute cache for identical queries
2. **Knowledge Base**: 15-minute cache for search results
3. **Session State**: In-memory for active sessions

### Parallel Processing

Teams can process independently:
- Routing determination: <100ms
- Team processing: <1.5s average
- Total response time: <2s target

## Security and Compliance

### Insurance Team Specific

1. **SUSEP Disclaimers**: Automatically added to insurance responses
2. **Coverage Transparency**: Always mentions exclusions
3. **Pricing Accuracy**: Validated against current rates

### Credit Team Specific

1. **Fraud Detection**: Advance fee scam detection
2. **Rate Disclosure**: CET always displayed
3. **Eligibility Verification**: Before suggesting products

### Investment Team Specific

1. **Suitability Warnings**: Risk disclaimers
2. **Tax Information**: IR calculations included
3. **FGC Protection**: Always mentioned for eligible products

## Monitoring and Analytics

### Key Metrics

1. **Team Performance**
   - Response time per team
   - Confidence scores distribution
   - Escalation rates

2. **Cross-Team Metrics**
   - Handoff success rate
   - Session continuity score
   - Knowledge sharing effectiveness

3. **Customer Experience**
   - Frustration level trends
   - Resolution rates
   - Multi-team journey completion

## Deployment Considerations

### Environment Requirements

```bash
# Python 3.11+ required
# Use uv for dependency management
uv sync

# Environment variables
AGNO_API_KEY=your_key
ANTHROPIC_API_KEY=your_key  # For Claude Opus 4
DATABASE_URL=your_db_url
```

### Scaling Considerations

1. **Horizontal Scaling**: Each team can scale independently
2. **Database Connections**: Pool management for high load
3. **Memory Usage**: ~500MB per team instance

## Troubleshooting Guide

### Common Issues

1. **Team Not Responding**
   - Check team initialization logs
   - Verify knowledge base connection
   - Ensure memory manager is accessible

2. **Incorrect Routing**
   - Review routing keywords in team_config.py
   - Check confidence thresholds
   - Verify context is being passed

3. **Session State Loss**
   - Confirm session manager is running
   - Check session timeout settings
   - Verify database connections

### Debug Mode

Enable debug logging:

```python
# In settings.py
debug = True
log_level = "DEBUG"

# Shows:
- Routing decisions with scores
- Team selection reasoning  
- Knowledge base queries
- Session state changes
```

## Future Enhancements

### Planned Features

1. **Advanced Analytics**
   - ML-based routing optimization
   - Predictive escalation detection
   - Personalized team assignment

2. **Enhanced Integration**
   - Real-time collaboration between teams
   - Shared workspace for complex cases
   - Visual customer journey mapping

3. **New Capabilities**
   - Voice integration for all teams
   - Proactive engagement based on patterns
   - Multi-language support (EN, ES)

## Conclusion

The PagBank Multi-Agent System now features complete integration across all five specialist teams with sophisticated routing, session management, and cross-team coordination. The Insurance team adds crucial protection products with emphasis on the R$ 20,000 monthly prize and affordable health plans.

Key achievements:
- ✅ All 5 teams fully implemented and tested
- ✅ Seamless cross-team handoffs
- ✅ Session state preservation
- ✅ Intelligent routing with context awareness
- ✅ Comprehensive test coverage
- ✅ Production-ready error handling

The system is ready for deployment and can handle complex, multi-team customer journeys while maintaining context and providing specialized expertise for each domain.