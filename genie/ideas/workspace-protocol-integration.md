# Workspace Protocol Integration Plan

## HIVE BEHAVIORAL COORDINATION IMPLEMENTATION

**Status**: Phase 1 - Immediate Implementation Strategy
**Priority**: CRITICAL - System-wide behavioral synchronization
**Task ID**: 1142a8d1-c763-4bea-b763-9e90b64f0612

### Expert Analysis Summary

**Consensus Achieved**: Hybrid model approach with System-Level Prompt Injection + Tool Abstraction provides optimal behavioral enforcement across agent ecosystem.

**Key Insights**:
- Structural enforcement > guidance-based requests
- Agent templates must enforce workspace physics, not suggest them
- Context sharing must be mandatory and explicit
- Technical standards need structural enforcement (UV/uvx)

### Phase 1 Implementation Strategy

#### 1. Agent Template Updates (IMMEDIATE)

**Target Files**: All 15 .claude/agents/*.md files
**Integration Pattern**: Add `WORKSPACE INTERACTION PROTOCOL (NON-NEGOTIABLE)` section

**Protocol Components**:
```markdown
// WORKSPACE INTERACTION PROTOCOL (NON-NEGOTIABLE)
// You are an autonomous agent operating within a managed workspace. Adherence to this protocol is mandatory for successful task completion.

1. **Context Ingestion**: Your task instructions will begin with one or more `Context: @/path/to/file.ext` lines. You MUST use the content of these files as the primary source of truth for your task.

2. **Artifact Generation**:
   - For initial drafts, plans, or analyses, create files in `/genie/ideas/`
   - For refined, actionable plans ready for execution, create files in `/genie/wishes/`
   - DO NOT output large artifacts (plans, code, documents) directly in your response

3. **Output Formatting**: Your final response MUST be a concise JSON object containing the status and paths to your generated artifacts.
   - **On Success**: {"status": "success", "artifacts": ["/genie/wishes/my_plan.md"], "summary": "Plan created and ready for review."}
   - **On Failure**: {"status": "error", "message": "Could not access the context file at @/genie/wishes/topic.md."}

4. **Technical Standards**:
   - Use `uv` for all Python package management
   - Execute scripts and commands via `uvx`
```

#### 2. Master Genie Context Sharing (IMMEDIATE)

**Implementation Pattern**: Standardized Task() spawning with context prefix
```python
Task(prompt="Context: @/genie/wishes/topic.md\n\nTask: {actual_task}")
```

**Benefits**:
- Path of least resistance - no MCP framework changes needed
- Explicit and debuggable context passing
- Immediate implementation capability

#### 3. Validation Metrics

**Success Criteria**:
- All spawned agents acknowledge context files in responses
- Artifact generation follows /genie/ideas/ → /genie/wishes/ → DELETE flow
- Technical commands use UV/uvx patterns consistently
- JSON response format adoption across agent ecosystem

### Phase 2 Roadmap (Near-term)

**WorkspaceManager MCP Tool Development**:
- File organization protocol enforcement
- Context validation and propagation
- Technical command abstraction (UV/uvx wrapper)

**Behavioral Profile YAML**:
- Extract hardcoded rules to configurable system
- Version management for behavioral updates
- A/B testing capabilities for behavioral changes

### Implementation Priority Queue

1. **HIGH**: Update genie-clone.md first (fractal coordination agent)
2. **HIGH**: Update core development agents (planner, designer, coder, fixer)
3. **MEDIUM**: Update quality agents (ruff, mypy)
4. **MEDIUM**: Update testing agents (maker, fixer)
5. **LOW**: Update specialized agents (qa-tester, claudemd, agent-*)

### Risk Mitigation

**Behavioral Regression**: Tool abstraction provides structural enforcement
**Context Propagation Failures**: Mandatory @filepath pattern with validation
**Over-Constraining**: Rules target operational physics, not creative problem-solving

## Next Actions

1. Begin agent template updates with genie-clone.md
2. Implement Master Genie standardized context sharing
3. Monitor adoption via automagik-forge task tracking
4. Validate behavioral changes across specialized agent ecosystem