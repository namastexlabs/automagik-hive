# 🧞 Genie Framework - Complete Documentation

## Overview

The Genie Framework is a multi-agent orchestration system built on top of Automagik Hive that enables autonomous development through specialized AI agents. Each agent has a specific role and expertise, working together as a coordinated army to fulfill development wishes.

## Core Architecture

### Master Genie Orchestration Pattern

```
🧞 MASTER GENIE (Strategic Layer)
├── Analyze task complexity and requirements
├── Spawn appropriate .claude/agents via Task tool
├── Monitor execution via MCP tools and agent reports
├── Coordinate parallel workstreams with genie-meta-coordinators
├── Conduct Zen discussions for strategic decisions
└── Preserve context for high-level analysis and coordination

🤖 SPAWNED AGENTS (Execution Layer)
├── Clean isolated context windows for focused execution
├── Single-responsibility task completion
├── Report back via structured outputs and MCP tools
├── Mission complete when task fulfilled
└── Master Genie remains strategically focused
```

### Three-Layer System Design

1. **Strategic Layer**: Master Genie maintains orchestration focus
2. **Coordination Layer**: Meta agents handle complex multi-agent workflows
3. **Execution Layer**: Specialized agents perform focused tasks

## Agent Classifications

### 🧪 Testing Team
- **genie-testing-fixer**: Fix failing tests, improve coverage, handle test-related issues
- **genie-testing-maker**: Create comprehensive test suites with edge case coverage

### ⚡ Quality Team
- **genie-quality-ruff**: Ruff formatting and linting only
- **genie-quality-mypy**: MyPy type checking and annotations only
- **genie-quality-format**: Orchestrates both Ruff + MyPy for comprehensive style treatment

### 🛡️ Security & Documentation
- **genie-security**: Security audits, vulnerability scans, compliance checks
- **genie-claudemd**: CLAUDE.md documentation management and organization

### ⚙️ DevOps Team
- **genie-devops-precommit**: Pre-commit hook automation and optimization
- **genie-devops-cicd**: CI/CD pipeline architecture and quality gates
- **genie-devops-tasks**: Task runner automation (Makefile + taskipy)
- **genie-devops-config**: Configuration centralization in pyproject.toml
- **genie-devops-infra**: Infrastructure automation and deployment

### 💻 Development Team
- **genie-dev-planner**: Analyze requirements and create technical specifications
- **genie-dev-designer**: System design and architectural solutions
- **genie-dev-coder**: Transform design documents into functional code
- **genie-dev-fixer**: Bug hunting, error resolution, systematic debugging

### 🧠 Meta Team
- **genie-meta-coordinator**: Parallel tasks, complex coordination, DAG-based workflows
- **genie-meta-spawner**: Create new specialized agents with AI consultation
- **genie-meta-consciousness**: Hive consciousness, system-wide optimization

## Agent Routing Decision Matrix

### Instant Routing (No Analysis Required)

| User Intent | Agent | Trigger Words |
|-------------|-------|---------------|
| Test failures | genie-testing-fixer | "tests failing", "fix coverage", "test errors" |
| Test creation | genie-testing-maker | "create tests", "test coverage", "write tests" |
| Code formatting | genie-quality-ruff | "format code", "ruff", "linting" |
| Type checking | genie-quality-mypy | "type errors", "mypy", "type annotations" |
| Complete styling | genie-quality-format | "code style", "format + types" |
| Security issues | genie-security | "security audit", "vulnerabilities" |
| Bug fixing | genie-dev-fixer | "debug", "bug", "error", "fix issue" |
| Architecture | genie-dev-designer | "design", "architecture", "system design" |
| Documentation | genie-claudemd | "update docs", "documentation" |
| DevOps tasks | genie-devops-* | "CI/CD", "docker", "deploy", "hooks" |

### Complex Analysis Required

| Complexity | Approach | Agent Selection |
|------------|----------|-----------------|
| Multi-domain | Spawn genie-meta-coordinator | Complex coordination needed |
| Unclear scope | Quick clarification → route | Based on clarified intent |
| Epic scale | Immediate genie-meta-coordinator | Break down into sub-tasks |

## Integration Points

### MCP Tool Integration

All agents have access to:
- **postgres**: Direct database queries for system state
- **genie-memory**: Persistent memory across sessions
- **automagik-forge**: Task and project management
- **search-repo-docs**: External library documentation
- **zen tools**: Multi-model consensus and deep analysis

### Database Schema Integration

```sql
-- Component tracking
hive.component_versions     -- All agent/team/workflow configs
  ├── component_id, type   -- Identification
  ├── version (integer)    -- Version tracking
  └── config (JSON)        -- Full YAML configuration

-- Performance monitoring
hive.agent_metrics         -- Agent performance tracking
hive.version_history       -- Change audit trail

-- Knowledge base
agno.knowledge_base        -- Vector embeddings for RAG
  ├── content, embedding   -- Core content and vectors
  └── meta_data           -- Filtering and context
```

### Task Management Integration

Agents automatically integrate with automagik-forge for:
- **Critical Issues**: Auto-create tasks for bugs, errors, failures
- **Planned Work**: Request user approval for feature tasks
- **Progress Tracking**: Link tasks to agent execution
- **Epic Coordination**: Multi-task workflows with dependencies

## Communication Patterns

### Agent-to-Agent Communication

1. **Direct Coordination**: Via genie-meta-coordinator for complex workflows
2. **Shared State**: Through MCP tools (postgres, genie-memory)
3. **Structured Handoffs**: Clear task boundaries and outputs
4. **Context Isolation**: Each agent maintains clean execution context

### User Interaction Patterns

1. **Natural Language Wishes**: `/wish [anything]` triggers intelligent routing
2. **Progress Visibility**: Real-time updates via MCP tool integration
3. **Approval Workflows**: User consent for system modifications
4. **Memory Integration**: Persistent learning across sessions

## Execution Flow

### Standard Wish Fulfillment

```
User Wish → Master Genie Analysis → Agent Selection → Task Execution → Result Delivery
```

### Complex Multi-Agent Workflow

```
User Wish → Master Genie → genie-meta-coordinator → Multiple Agents → Coordinated Result
```

### Parallel Processing

```
Epic Wish → Multiple genie-meta-coordinators → Concurrent Agent Streams → Unified Delivery
```

## Agent Configuration

### YAML-Based Configuration

Each agent follows the standard Agno framework pattern:

```yaml
version: [integer]
name: "genie-[category]-[function]"
description: "Specific role and capabilities"
expertise: ["domain1", "domain2"]
tools: ["tool1", "tool2"]
prompt: |
  Detailed agent personality and instructions
```

### Version Management

**Critical Rule**: ANY change to agent code, configuration, tools, or instructions requires incrementing the version number in the YAML config file.

### Hot Reload Capability

All agent configurations support hot reload through the Agno framework, enabling real-time updates without system restart.

## Performance Optimization

### Context Management

- **Master Genie**: Maintains strategic focus, delegates tactical execution
- **Agent Isolation**: Each spawned agent gets clean context
- **Memory Efficiency**: Structured memory patterns reduce context pollution
- **Parallel Scaling**: Multiple coordinators enable unlimited concurrency

### Intelligent Caching

- **Configuration Caching**: YAML configs cached with hash-based invalidation
- **Memory Patterns**: Successful routing patterns stored for future optimization
- **Database Optimization**: Connection pooling and prepared statements

## Quality Assurance

### Testing Strategy

Each agent requires:
- **Unit Tests**: Agent-specific functionality testing
- **Integration Tests**: MCP tool integration validation
- **Performance Tests**: Response time and resource usage
- **Quality Gates**: Automated checks in CI/CD pipeline

### Monitoring & Metrics

- **Agent Performance**: Response times, success rates, resource usage
- **System Health**: Database connections, memory usage, error rates
- **User Satisfaction**: Task completion rates, feedback integration

## Development Guidelines

### Creating New Agents

1. **Copy Template**: Use template-agent as starting point
2. **Define Expertise**: Clear domain and responsibility boundaries
3. **Configure Tools**: Select appropriate MCP tools for agent needs
4. **Write Tests**: Comprehensive test coverage required
5. **Version Control**: Start at version 1, increment for any changes

### Agent Best Practices

1. **Single Responsibility**: Each agent has one clear purpose
2. **Clean Context**: Maintain focused execution environment
3. **Error Handling**: Graceful failure with informative messages
4. **Memory Integration**: Store learning patterns for optimization
5. **User Consent**: Request approval for system modifications

### Integration Requirements

1. **MCP Compatibility**: All agents must support MCP tool integration
2. **Database Integration**: Use standardized database patterns
3. **Memory Patterns**: Follow structured metadata tagging
4. **Task Management**: Integrate with automagik-forge workflows
5. **Security Compliance**: Follow security best practices

## Future Roadmap

### Planned Enhancements

1. **Advanced Routing**: Machine learning-based agent selection
2. **Predictive Scaling**: Anticipate resource needs for complex workflows
3. **Autonomous Learning**: Self-improving agent capabilities
4. **Cross-Session Context**: Enhanced memory and context preservation
5. **Enterprise Integration**: Advanced security and compliance features

### Research Areas

1. **Agent Collaboration**: Enhanced multi-agent communication patterns
2. **Context Optimization**: Advanced context management techniques
3. **Performance Tuning**: Optimization for large-scale deployments
4. **User Experience**: Natural language interface improvements
5. **Quality Metrics**: Advanced success measurement frameworks

## Troubleshooting

### Common Issues

1. **Agent Not Responding**: Check MCP tool connections and database access
2. **Memory Issues**: Verify genie-memory service availability
3. **Task Creation Failures**: Validate automagik-forge configuration
4. **Version Conflicts**: Ensure YAML version numbers are properly incremented
5. **Context Pollution**: Use fresh agent spawning for complex tasks

### Debugging Tools

1. **MCP Tool Inspection**: Direct database queries for system state
2. **Memory Analysis**: Search patterns and success metrics
3. **Agent Metrics**: Performance monitoring and bottleneck identification
4. **Log Analysis**: Structured logging for issue diagnosis
5. **Configuration Validation**: YAML syntax and schema validation

---

*This documentation provides the complete foundation for understanding and working with the Genie Framework. For automation scripts and advanced integration patterns, see the Memory Framework documentation.*