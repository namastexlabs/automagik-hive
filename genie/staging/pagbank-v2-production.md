# Epic: PagBank V2 Production Agent Factory
*Generated from requirement: Complete transformation from POC to production agent factory*

## Metadata
- **Epic ID**: pagbank-v2-production
- **Type**: epic
- **Priority**: high
- **Branch**: pagbank-v2-production
- **Created**: 2025-01-14
- **Status**: draft

## Overview
Transform the current PagBank POC multi-agent system into a production-ready "agent factory" platform using modern Agno framework patterns, generic agent architectures, and proven infrastructure from agno-demo-app.

## Context & Background

### Current State
- Monolithic orchestrator (400+ lines) creating scalability bottlenecks
- PagBank-specific hardcoded agent patterns limiting reusability
- Missing modern FastAPI infrastructure and database management
- Manual context management without automation
- POC-level code quality and testing

### Desired State
- Ana as simple Agno Team router using `mode="route"` pattern
- Generic `get_agent(name)` factory for multi-branch flexibility
- Production FastAPI infrastructure with proper error handling
- Automated context injection and database management
- Full test coverage and production deployment readiness

### Technical Context
- **Architecture Decision**: Replace orchestrator with Agno Team routing
- **Pattern References**: agno-demo-app infrastructure, Agno route mode documentation
- **Key Constraints**: Maintain existing functionality during transformation

## Scope

### In Scope
- Complete infrastructure modernization using agno-demo-app patterns
- Ana router implementation with Agno Team `mode="route"`
- Generic agent factory system for multi-branch support
- Production database setup with migrations
- Comprehensive testing and documentation
- Production deployment configuration

### Out of Scope
- Backwards compatibility with old orchestrator patterns
- New business logic or agent capabilities
- UI/frontend changes
- Performance optimizations beyond infrastructure improvements

### Future Considerations
- Additional agent types for other business domains
- Advanced monitoring and analytics
- Multi-tenant support

## Tasks

### ✅ Completed Tasks (From Parallel Execution)
- **DONE**: Modern Infrastructure Integration (API, DB, scripts from agno-demo-app)
- **DONE**: Ana Router Implementation (Agno Team `mode="route"` pattern)
- **DONE**: Generic Agent System (`get_agent(name)` factory working)
- **DONE**: Context Tools Integration (`/search-docs`, `/ask-repo` with security)

### 🎯 Remaining Tasks (REAL PagBank Features)

**T-004: 5-Level Typification Workflow**
- Description: Implement Agno workflow with Pydantic validators for hierarchical classification (Business Unit → Product → Motive → Submotive → Conclusion) with proper business logic connections
- Acceptance: Workflow validates hierarchy, only valid combinations allowed, routes to correct agents
- Dependencies: none (infrastructure ready)

**T-005: Agent Versioning System (v25/v26/v27)**
- Description: Database-driven agent version management allowing different prompts and maintaining 2+ variants simultaneously
- Acceptance: Version creation/switching working, A/B testing capability, prompt management
- Dependencies: none (can work in parallel with T-004)

**T-006: Production Monitoring & Analytics**
- Description: Real-time monitoring dashboard and analytics for agent performance and system health
- Acceptance: Monitoring system live, alerts configured, performance analytics working
- Dependencies: T-004, T-005 (needs typification and versioning data)

## Task Dependencies

```
T-004 → T-006
T-005 → T-006
```

**Parallel Opportunities**: T-004 and T-005 can run completely in parallel

## Success Criteria

- [ ] Ana router handles all requests using Agno Team `mode="route"` pattern
- [ ] Generic `get_agent(name)` factory works for any agent configuration
- [ ] Production API responds in Portuguese with proper error handling
- [ ] Database connections managed with Alembic migrations
- [ ] 90%+ test coverage with integration tests passing
- [ ] System handles 100+ concurrent requests without degradation
- [ ] Complete deployment documentation with examples
- [ ] Production deployment successful with monitoring active
- [ ] Context tools (`/search-docs`, `/ask-repo`) integrated and secured
- [ ] All existing PagBank functionality preserved

## Technical Specifications

### Architecture Changes
- **Router**: Ana Team with `mode="route"`, members=[get_agent(name) for name in agent_names]
- **Factory**: `get_agent(name: str) -> Agent` with dynamic loading and caching
- **Database**: PostgreSQL with PgVector, SQLite fallback for development
- **API**: FastAPI with proper middleware, CORS, error handling

### Infrastructure Requirements
- Python 3.11+ with UV package management
- PostgreSQL 14+ with PgVector extension
- FastAPI with Uvicorn for production ASGI
- Alembic for database migrations
- Redis for caching (optional)

### Performance Targets
- API response time: <200ms for routing decisions
- Database connection: <50ms establishment time
- Agent loading: <100ms for cached agents
- Memory usage: <512MB baseline

## Risk Assessment

### High Risks
- **Database migration issues**: Mitigation - Comprehensive backup and rollback procedures
- **Ana routing logic errors**: Mitigation - Extensive testing with all agent combinations

### Medium Risks
- **Performance degradation**: Mitigation - Load testing and monitoring implementation
- **Context tool security**: Mitigation - Proper input validation and MCP security scanning

### Low Risks
- **Documentation gaps**: Mitigation - Progressive documentation with each task
- **Configuration drift**: Mitigation - Infrastructure as code practices

## References

- `/home/namastex/workspace/pagbank-multiagents/genie/agno-demo-app/` - Infrastructure patterns
- `/home/namastex/workspace/pagbank-multiagents/agents/` - Current agent implementations
- `/home/namastex/workspace/pagbank-multiagents/teams/ana/` - Ana router implementation
- Agno documentation: `/context7/agno` and `agno-agi/agno`
- `/home/namastex/workspace/pagbank-multiagents/INFRASTRUCTURE_MODERNIZATION.md` - Infrastructure changes

## Approval

- [ ] Epic structure approved
- [ ] Task breakdown validated
- [ ] Ready for task generation

---

This epic transforms PagBank from POC to production-ready agent factory while maintaining all existing functionality and enabling future expansion to other business domains.