# Documentation Architecture - PagBank Multi-Agent System

This project uses a **3-tier documentation system** specifically designed for multi-agent orchestration that organizes knowledge by stability and scope, enabling efficient AI context loading and scalable development across specialized business units.

## How the 3-Tier System Works for Multi-Agent Development

**Tier 1 (Foundation)**: Stable, system-wide documentation that rarely changes - architectural principles, multi-agent orchestration patterns, Agno framework integration, and core development protocols for Brazilian financial services.

**Tier 2 (Component)**: Architectural charters for major system components - agent configurations, team routing logic, workflow patterns, and component-wide conventions without feature-specific details.

**Tier 3 (Feature-Specific)**: Granular documentation co-located with code - specific business unit implementations, technical details, and local architectural decisions that evolve with customer service features.

This hierarchy allows AI agents to load targeted context efficiently while maintaining a stable foundation of Brazilian financial services knowledge and multi-agent coordination patterns.

## Documentation Principles for Multi-Agent Systems
- **Business Unit Separation**: Documentation organized by PagBank, Adquirência, and Emissão domains
- **Agent-Aware Co-location**: Documentation lives near relevant agent and team code
- **Smart Extension**: New documentation files created automatically when warranted by routing changes
- **AI-First**: Optimized for efficient AI context loading and machine-readable multi-agent patterns
- **Portuguese Language**: Customer-facing documentation in PT-BR, technical docs in English

## Tier 1: Foundational Documentation (System-Wide)

- **[Master Context](/CLAUDE.md)** - *Essential for every session.* Multi-agent orchestration patterns, Brazilian financial compliance, Agno framework integration, and development protocols for specialized customer service agents
- **[Project Structure](/genie/ai-context/project-structure.md)** - *REQUIRED reading.* Complete technology stack, agent hierarchy, business unit separation, and multi-agent system architecture
- **[System Integration](/genie/ai-context/system-integration.md)** - *For cross-agent work.* Agent communication patterns, team routing logic, escalation flows, and performance optimization across business units
- **[Deployment Infrastructure](/genie/ai-context/deployment-infrastructure.md)** - *Infrastructure patterns.* Multi-agent containerization, monitoring, CI/CD workflows, and scaling strategies for customer service loads
- **[Task Management](/genie/ai-context/handoff.md)** - *Session continuity.* Current development tasks, agent coordination progress, and next session goals

## Tier 2: Component-Level Documentation

### Multi-Agent Core Components
- **[Agents Directory](/agents/CLAUDE.md)** - *Agent factory patterns.* Individual specialist definitions for PagBank, Adquirência, and Emissão business units with YAML-first configuration and dynamic versioning
- **[Teams Directory](/teams/CLAUDE.md)** - *Team orchestration.* Ana routing team implementation with mode="route" patterns, business unit detection, and member coordination strategies
- **[Workflows Directory](/workflows/CLAUDE.md)** - *Process automation.* Human handoff workflows, typification processes, and escalation sequences for customer service excellence

### System Infrastructure Components  
- **[API Directory](/api/CLAUDE.md)** - *FastAPI integration.* Agno playground integration, dynamic agent versioning, streaming responses, and Portuguese language support
- **[Configuration Management](/config/CLAUDE.md)** - *Global settings.* Environment-based configuration, model provider settings, database connections, and Brazilian compliance parameters
- **[Database Layer](/db/CLAUDE.md)** - *Data persistence.* PostgreSQL with automatic SQLite fallback, session management, and multi-agent state coordination

### Context and Knowledge Components
- **[Context Management](/context/CLAUDE.md)** - *Knowledge and memory.* CSV knowledge base with business unit filtering, session persistence, and pattern detection for Brazilian financial services
- **[Testing Framework](/tests/CLAUDE.md)** - *Quality assurance.* Multi-agent testing patterns, Portuguese language validation, routing accuracy tests, and compliance verification

## Tier 3: Feature-Specific Documentation

Granular CONTEXT.md files co-located with code for minimal cascade effects across business units:

### Agent-Specific Feature Documentation
- **[PagBank Specialist](/agents/pagbank/CONTEXT.md)** - *Digital banking agent.* PIX operations, account management, mobile top-up, and investment products expertise
- **[Adquirência Specialist](/agents/adquirencia/CONTEXT.md)** - *Merchant services agent.* Sales anticipation, machine rental, fee calculations, and multi-acquirer support
- **[Emissão Specialist](/agents/emissao/CONTEXT.md)** - *Card services agent.* Card limits, bill generation, password management, and international usage policies

### Orchestration Feature Documentation
- **[Main Orchestrator](/agents/orchestrator/CONTEXT.md)** - *Central routing.* Business unit detection, agent selection logic, frustration monitoring, and escalation triggers
- **[Human Handoff Logic](/agents/orchestrator/human_handoff_detector.py)** - *Escalation patterns.* Frustration detection algorithms, WhatsApp integration, and human agent transition protocols
- **[Routing Intelligence](/agents/orchestrator/routing_logic.py)** - *Business logic.* Keyword analysis, business unit mapping, confidence scoring, and routing decision explanations

### Knowledge and Context Documentation
- **[Knowledge Base Management](/context/knowledge/CONTEXT.md)** - *CSV knowledge system.* Business unit filtering, hot reload patterns, and RAG implementation for Brazilian financial products
- **[Memory Management](/context/memory/CONTEXT.md)** - *Session persistence.* User memory patterns, conversation state, and cross-agent context sharing
- **[Agentic Filters](/context/knowledge/agentic_filters.py)** - *Business unit isolation.* Knowledge filtering by Adquirência, Emissão, and PagBank domains

### API and Integration Documentation
- **[Playground Integration](/api/playground.py)** - *Development interface.* Agno playground setup, agent registration, and testing workflows
- **[Agent Endpoints](/api/routes/agents/CONTEXT.md)** - *Individual agent APIs.* Dynamic versioning, session management, and business unit routing
- **[Team Endpoints](/api/routes/teams/CONTEXT.md)** - *Orchestration APIs.* Ana team routing, mode="route" implementation, and response formatting

## Task Type Routing Logic

### Multi-Agent Development Tasks
**Route to**: `/agents/CLAUDE.md` + specific agent directories
**Use when**: Creating or modifying individual business unit specialists
**Key context**: Agent factory patterns, YAML configuration, Portuguese language requirements

### Team Orchestration Tasks  
**Route to**: `/teams/CLAUDE.md` + `/agents/orchestrator/`
**Use when**: Implementing routing logic, business unit detection, or escalation flows
**Key context**: Mode="route" patterns, routing confidence scoring, Ana team implementation

### Business Logic Implementation
**Route to**: Business unit specific `/agents/{unit}/` + `/context/knowledge/`
**Use when**: Adding new financial products, updating business rules, or modifying service offerings
**Key context**: Knowledge base filtering, compliance requirements, Portuguese content

### API and Integration Tasks
**Route to**: `/api/CLAUDE.md` + specific endpoint directories
**Use when**: Building external integrations, API endpoints, or client interfaces
**Key context**: Agno FastAPI patterns, streaming responses, dynamic versioning

### Database and Storage Tasks
**Route to**: `/db/CLAUDE.md` + `/config/CLAUDE.md`
**Use when**: Managing persistence, sessions, or storage configuration
**Key context**: PostgreSQL/SQLite patterns, session management, schema updates

### Testing and Quality Assurance
**Route to**: `/tests/CLAUDE.md` + component-specific test directories
**Use when**: Writing tests, validating routing accuracy, or ensuring compliance
**Key context**: Multi-agent testing patterns, Portuguese validation, business unit isolation

### Knowledge Management Tasks
**Route to**: `/context/CLAUDE.md` + knowledge-specific directories
**Use when**: Updating knowledge base, managing business unit content, or implementing RAG
**Key context**: CSV knowledge patterns, business unit filtering, hot reload mechanisms

## Intelligent Documentation Discovery

### For Agent Development
1. **Start with**: `/CLAUDE.md` (master context) + `/agents/CLAUDE.md` (agent patterns)
2. **Add business unit context**: `/agents/{pagbank|adquirencia|emissao}/`
3. **Include API integration**: `/api/CLAUDE.md` for endpoint requirements
4. **Reference knowledge**: `/context/knowledge/` for business unit data

### For Routing and Orchestration
1. **Start with**: `/CLAUDE.md` + `/teams/CLAUDE.md` + `/agents/orchestrator/`
2. **Add routing context**: `/agents/orchestrator/routing_logic.py` patterns
3. **Include escalation**: `/workflows/CLAUDE.md` for human handoff
4. **Reference detection**: Business unit keyword analysis and confidence scoring

### For Business Logic Updates
1. **Start with**: Business unit specific documentation in `/agents/{unit}/`
2. **Add knowledge context**: `/context/knowledge/` with business unit filtering
3. **Include compliance**: `/config/CLAUDE.md` for regulatory requirements
4. **Reference testing**: `/tests/CLAUDE.md` for validation patterns

### For Infrastructure and Configuration
1. **Start with**: `/config/CLAUDE.md` + `/db/CLAUDE.md`
2. **Add deployment context**: `/genie/ai-context/deployment-infrastructure.md`
3. **Include monitoring**: Performance and health check patterns
4. **Reference integration**: `/api/CLAUDE.md` for service connections

## Adding New Documentation

### New Business Unit Specialist
1. Create `/agents/new-unit/CONTEXT.md` (Tier 3)
2. Update `/agents/CLAUDE.md` with new unit patterns (Tier 2)
3. Add business unit to this routing guide
4. Create knowledge filters in `/context/knowledge/`

### New Orchestration Feature
1. Create `/agents/orchestrator/feature/CONTEXT.md` (Tier 3)
2. Update `/teams/CLAUDE.md` with routing patterns (Tier 2)
3. Add routing logic to this discovery guide
4. Create corresponding test patterns

### New API Integration
1. Create `/api/routes/integration/CONTEXT.md` (Tier 3)
2. Update `/api/CLAUDE.md` with endpoint patterns (Tier 2)
3. Add integration to routing logic
4. Create monitoring and health check patterns

### Deprecating Multi-Agent Documentation
1. Remove obsolete agent/team CONTEXT.md files
2. Update this routing guide to remove obsolete paths
3. Check for broken references in orchestration logic
4. Archive outdated business unit patterns

---

*This documentation architecture is specifically designed for the PagBank Multi-Agent System with its specialized business units (PagBank, Adquirência, Emissão), Ana routing team, Portuguese language requirements, and Brazilian financial services compliance needs. The routing logic helps AI agents efficiently discover the right documentation tier for their specific development tasks.*