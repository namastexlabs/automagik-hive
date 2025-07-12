# Evaluation: Full-Context Command Adaptation for PagBank Multi-Agent System

## Task Overview
Analyze the copied `/full-context` command from CCDK and evaluate how to adapt it specifically for our PagBank multi-agent financial services system, integrating with our enhanced genie/ai-context/ foundation and MCP tools.

## Current Command Analysis

### Strengths of Current Implementation
1. **Adaptive Strategy Selection**: Direct/Focused/Multi-Perspective analysis based on complexity
2. **Parallel Sub-Agent Execution**: Efficient parallel task processing
3. **Comprehensive Investigation Workflow**: 7-step standard workflow for thorough analysis
4. **Impact Assessment Focus**: Dependency mapping and cleanup planning
5. **Auto-Loaded Context**: Automatic loading of core project documentation

### PagBank-Specific Adaptations Needed

#### 1. Business Unit Awareness
**Current Issue**: Generic component analysis
**Adaptation Required**:
- Add business unit context (Adquirência, Emissão, PagBank, Human Handoff)
- Include financial compliance considerations in all analyses
- Integrate Brazilian Portuguese language requirements

```markdown
### Enhanced Sub-Agent Specialization for PagBank:
- **Business Unit Specialist Analysis**: Sub-agents focused on specific business units
- **Compliance Impact Assessment**: Financial regulation and PII handling analysis
- **Multi-Language Consideration**: PT-BR customer content vs EN technical implementation
- **Agent Orchestration Patterns**: Routing logic and specialist coordination analysis
```

#### 2. Enhanced Auto-Loaded Context
**Current**: Basic project structure and docs overview
**PagBank Enhancement**:
```markdown
## Auto-Loaded PagBank Context:
@/CLAUDE.md
@/genie/ai-context/project-structure.md
@/genie/ai-context/docs-overview.md
@/genie/ai-context/development-standards.md  # NEW
@/genie/ai-context/system-integration.md     # NEW
@/genie/reference/routing-patterns.md        # NEW
@/genie/reference/compliance-rules.md        # NEW (if exists)
```

#### 3. MCP Tools Integration
**Current**: Basic Gemini/Context7 mention
**PagBank Integration**:
- `search-repo-docs`: For library documentation lookup during development
- `ask-repo-agent`: For GitHub repository analysis and questions
- `send-whatsapp-message`: For testing human handoff workflows
- `wait`: For testing timing-sensitive agent coordination

#### 4. Financial Services Specific Workflows

```markdown
### PagBank-Specific Investigation Patterns:

**Payment Processing Analysis**:
1. Review business unit routing logic (orchestrator/routing_logic.py)
2. Analyze payment method handlers in specialist agents
3. Check compliance validations and fraud detection
4. Verify Portuguese language responses
5. Test human escalation pathways

**Agent Coordination Analysis**:
1. Examine orchestrator state synchronization
2. Analyze memory persistence across sessions
3. Check frustration detection and escalation logic
4. Verify cross-agent context sharing
5. Test multi-agent conversation flows

**Knowledge Base Analysis**:
1. Review CSV knowledge filtering by business unit
2. Analyze hot-reload and incremental loading
3. Check agentic filters for context relevance
4. Verify knowledge accuracy and completeness
5. Test RAG retrieval performance
```

#### 5. Development Workflow Integration

```markdown
### Genie Framework Integration:
- **Pattern Validation**: Check against genie/reference/ for existing patterns
- **Active Task Management**: Integrate with genie/active/ workflow (max 5 files)
- **Multi-Agent Development**: Coordinate changes across specialist agents
- **UV Environment**: Ensure all commands use UV package manager
- **Testing Requirements**: Include agent-specific and integration tests
```

## Specific Use Cases for PagBank System

### Use Case 1: Adding New Payment Method
```markdown
Command: /full-context "Add support for boleto bancário payment method"

Expected Sub-Agent Analysis:
1. **PagBank Agent Analysis**: Current payment handlers and integration points
2. **Routing Logic Analysis**: Keywords and classification updates needed
3. **Knowledge Base Analysis**: CSV entries and documentation requirements
4. **Compliance Analysis**: Financial regulations for boleto processing
5. **Testing Analysis**: Agent-specific and integration test requirements
```

### Use Case 2: Improving Agent Coordination
```markdown
Command: /full-context "Optimize agent handoff performance for complex queries"

Expected Sub-Agent Analysis:
1. **Orchestrator Analysis**: Current routing and state management
2. **Memory Analysis**: Session persistence and context sharing
3. **Performance Analysis**: Bottlenecks in agent coordination
4. **Human Handoff Analysis**: Escalation triggers and timing
5. **Integration Testing**: End-to-end flow validation
```

### Use Case 3: Enhancing Knowledge Management
```markdown
Command: /full-context "Implement real-time knowledge base updates"

Expected Sub-Agent Analysis:
1. **CSV Knowledge Analysis**: Current hot-reload and filtering mechanisms
2. **Agent Integration Analysis**: How agents consume knowledge updates
3. **Performance Analysis**: Impact of real-time updates on response times
4. **Memory Analysis**: Caching and invalidation strategies
5. **MCP Integration Analysis**: Using search-repo-docs for external updates
```

## Required Template Modifications

### 1. Business Unit Template Extension
```markdown
Task: "Analyze [BUSINESS_UNIT] specialist agent and [SPECIFIC_COMPONENT(S)] for [TASK_OBJECTIVE] related to user request '$ARGUMENTS'"

Enhanced Investigation Workflow:
1. Review auto-loaded PagBank context (CLAUDE.md, ai-context files, routing patterns)
2. Analyze business unit specific agent implementation (adquirencia/emissao/pagbank)
3. Check orchestrator routing logic for business unit classification
4. Examine knowledge base filtering for business unit context
5. Verify compliance requirements and Portuguese language handling
6. Map import/export dependencies across agent modules
7. Assess impact on tests, memory management, and human handoff
8. Identify cleanup opportunities and pattern compliance
```

### 2. MCP-Enhanced Analysis Template
```markdown
### MCP Tool Integration Strategy:
- **search-repo-docs**: When external library documentation is needed
- **ask-repo-agent**: For GitHub repository analysis and best practices
- **Evolution API**: For WhatsApp integration testing and validation
- **Context7**: For up-to-date financial services libraries and frameworks
```

### 3. Compliance-Aware Status Updates
```markdown
Example PagBank Status Updates:
"Analysis revealed the PagBank agent uses business unit filtering with CSV knowledge base entries for payment method routing. I'll implement boleto support by extending the existing payment handlers in pagbank_agent.py and updating the knowledge base with Portuguese keywords, following established patterns in PIX processing. This requires updating 4 import statements, adding new compliance validations, and ensuring Portuguese responses throughout the flow."

"Found that agent orchestration uses memory synchronization with session persistence for complex query handling. I'll optimize handoff performance by implementing connection pooling in the orchestrator and adding intelligent caching to the memory manager, following the existing agent coordination patterns. The implementation requires updates to 3 core components and comprehensive integration testing."
```

## Integration Points with Existing Genie Framework

### 1. Pattern Persistence Integration
- Auto-check `genie/reference/` for existing patterns before analysis
- Store successful analysis patterns back to reference folder
- Integrate with genie workflow for pattern reuse

### 2. Active Task Coordination
- Respect 5-file limit in `genie/active/`
- Create complementary task files for multi-agent changes
- Maintain task status and completion tracking

### 3. Development Standards Compliance
- Enforce UV usage for all Python operations
- Validate Portuguese language requirements
- Check compliance considerations automatically
- Ensure agent-specific testing requirements

## Recommendations for Implementation

### Phase 1: Basic Adaptation
1. Update auto-loaded context paths for PagBank structure
2. Add business unit awareness to sub-agent templates
3. Integrate basic MCP tool references
4. Update example use cases for financial services

### Phase 2: Enhanced Integration
1. Add automatic pattern checking against genie/reference/
2. Implement business unit specific analysis workflows
3. Integrate comprehensive MCP tool usage
4. Add compliance and language validation

### Phase 3: Advanced Optimization
1. Implement intelligent sub-agent selection based on business units
2. Add automatic testing requirement generation
3. Integrate with genie active task management
4. Add pattern learning and recommendation system

## Success Metrics

### Technical Metrics
- Reduced analysis time for multi-agent changes
- Improved accuracy in dependency mapping
- Better pattern compliance across implementations
- Enhanced test coverage for agent interactions

### Business Metrics
- Faster feature development for financial services
- Better compliance validation coverage
- Improved Portuguese language consistency
- Enhanced agent coordination reliability

## Next Steps

1. **Validate Current Implementation**: Test the copied command with simple PagBank queries
2. **Implement Phase 1 Adaptations**: Update context paths and business unit awareness
3. **Create Test Scenarios**: Develop specific test cases for the three use cases outlined
4. **Integrate with MCP Tools**: Add comprehensive MCP tool usage patterns
5. **Document Patterns**: Store successful adaptations in genie/reference/

This evaluation provides a comprehensive roadmap for adapting the full-context command to serve our specific PagBank multi-agent development needs while maintaining the powerful adaptive analysis capabilities of the original CCDK implementation.