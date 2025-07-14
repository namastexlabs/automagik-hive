# PagBank V2 Epic Review Guide

**Purpose**: Complete review of the entire V2 transformation plan in logical order

## 📋 Review Sequence

### Phase 1: Understanding the Context
**Start here to understand WHY we're doing this transformation**

1. **`genie/active/epic-status.md`** 
   - **Purpose**: Central overview and current status
   - **Review for**: Overall goals, progress tracking, dependency understanding
   - **Key questions**: Are the objectives clear? Do the phases make sense?

2. **`genie/archive/2025-01-12-platform-strategy.md`** (archived)
   - **Purpose**: The complete epic strategy (1994 lines split into tasks)
   - **Review for**: Business rationale, technical approach, architecture decisions
   - **Key questions**: Does the V2 approach solve current problems? Is the scope appropriate?

### Phase 2: Architecture Understanding
**Deep dive into the technical architecture**

3. **`CLAUDE.md`** (root level)
   - **Purpose**: Updated development guidelines and V2 coordination rules
   - **Review for**: Multi-agent coordination protocol, critical rules, workflow
   - **Key questions**: Are the coordination rules clear? Will multiple agents work well together?

4. **`@genie/reference/agno-patterns.md`**
   - **Purpose**: How we use the Agno framework
   - **Review for**: Framework integration approach, patterns consistency
   - **Key questions**: Are we using Agno correctly? Do patterns align with demo app?

5. **`@genie/reference/agno-patterns-index.md`**
   - **Purpose**: Organized parameter reference - see agno-patterns-index.md for all Agno components
   - **Review for**: Parameter completeness, YAML structure, configuration approach
   - **Key questions**: Are all needed parameters covered? Is the YAML approach consistent?

6. **`@genie/reference/database-schema.md`**
   - **Purpose**: V2 database design with PostgreSQL and pgvector
   - **Review for**: Schema completeness, relationships, scalability
   - **Key questions**: Does the schema support all V2 features? Are migrations planned?

7. **`@genie/reference/yaml-configuration.md`**
   - **Purpose**: YAML-first configuration approach
   - **Review for**: Configuration philosophy, examples, API update strategy
   - **Key questions**: Is the YAML → DB → API approach clear? No hardcoding anywhere?

### Phase 3: Implementation Tasks Review
**Review the actual work breakdown**

8. **`genie/task-cards/00-task-overview.md`**
   - **Purpose**: Parallel execution plan and task dependencies
   - **Review for**: Task organization, dependency mapping, agent assignment
   - **Key questions**: Can tasks really run in parallel? Are dependencies correct?

9. **`genie/task-cards/shared/00-platform-context.md`**
   - **Purpose**: Shared context for all implementation tasks
   - **Review for**: Consistent understanding across all tasks
   - **Key questions**: Is context sufficient for any agent to start work?

10. **Phase 1 Tasks** (Foundation - can run in parallel):
    - `genie/task-cards/phase1/01-refactor-ana-team.md`
    - `genie/task-cards/phase1/02-database-infrastructure.md`  
    - `genie/task-cards/phase1/03-base-api-structure.md`
    - `genie/task-cards/phase1/04-migrate-agents.md`
    - **Review for**: Task clarity, implementation steps, validation methods
    - **Key questions**: Can each task be executed independently? Are validation steps sufficient?

11. **Phase 2 Tasks** (Platform Core):
    - `genie/task-cards/phase2/01-agent-versioning.md`
    - `genie/task-cards/phase2/02-typification-workflow.md`
    - `genie/task-cards/phase2/03-configuration-hotreload.md`
    - **Review for**: Platform feature completeness, integration points
    - **Key questions**: Do these create a working platform? How do they integrate?

12. **Phase 3 Tasks** (Production Features):
    - `genie/task-cards/phase3/01-enhanced-monitoring.md`
    - `genie/task-cards/phase3/02-advanced-playground.md`
    - `genie/task-cards/phase3/03-security-compliance.md`
    - **Review for**: Production readiness, scalability, security
    - **Key questions**: Is this production-ready? What's missing for enterprise use?

### Phase 4: Supporting Documentation
**Review supporting materials and coordination**

13. **`genie/task-cards/shared/` files** (in any order):
    - `01-api-endpoints.md`
    - `02-folder-structure.md`
    - `03-yaml-configurations.md`
    - `04-database-schema.md`
    - `05-config-migration.md`
    - `06-database-api.md`
    - `07-dependencies.md`
    - `08-implementation-timeline.md`
    - **Review for**: Consistency across shared resources, completeness
    - **Key questions**: Do shared resources support all tasks? Any conflicts?

14. **`genie/active/agent-coordination.md`**
    - **Purpose**: Multi-agent coordination protocol for parallel execution
    - **Review for**: Coordination effectiveness, conflict resolution, status tracking
    - **Key questions**: Will 6 agents coordinate well? Is the wait/dependency system robust?

15. **`@genie/reference/context-search-tools.md`**
    - **Purpose**: How agents should use MCP tools for Agno questions
    - **Review for**: Tool usage patterns, question strategies
    - **Key questions**: Will agents get good answers from Agno docs? Are patterns clear?

### Phase 5: Investigation Tasks
**Review pending research and unknowns**

16. **`genie/active/agno-parameter-investigation.md`**
    - **Purpose**: Task for separate agent to investigate Agno parameters deeply
    - **Review for**: Investigation strategy, completeness of questions
    - **Key questions**: Will this investigation fill all knowledge gaps? Are instructions clear?

## 🔍 Review Checklist

For each file, ask yourself:

### Content Quality
- [ ] Is the information accurate and up-to-date?
- [ ] Are examples realistic and helpful?
- [ ] Is the writing clear and actionable?

### Consistency
- [ ] Does this align with other documents?
- [ ] Are naming conventions consistent?
- [ ] Do references point to correct files?

### Completeness  
- [ ] Are there any gaps in this area?
- [ ] What questions does this raise?
- [ ] What additional information is needed?

### Feasibility
- [ ] Can this actually be implemented as described?
- [ ] Are the timelines realistic?
- [ ] Are dependencies correctly identified?

## 🚨 Red Flags to Watch For

- **Conflicting information** between documents
- **Missing dependencies** that aren't captured
- **Unrealistic timelines** or complexity estimates
- **Hardcoded values** that should be in YAML
- **References to old patterns** (orchestrator, routing logic)
- **Assumptions about Agno** that need verification

## 📝 Review Notes Template

For each document, capture:

```markdown
## File: [filename]
**Overall Rating**: ⭐⭐⭐⭐⭐ (1-5 stars)

### Strengths:
- 

### Issues Found:
- 

### Questions/Concerns:
- 

### Recommendations:
- 

### Dependencies on Other Files:
- 
```

## 🎯 Final Review Questions

After reviewing everything:

1. **Coherence**: Does the entire plan hang together logically?
2. **Feasibility**: Can this actually be built by 6 parallel agents?
3. **Completeness**: What's missing that would prevent success?
4. **Risk**: What are the biggest risks and how are they mitigated?
5. **Value**: Will this deliver the promised transformation benefits?

---

**Estimated Review Time**: 4-6 hours for thorough review
**Recommendation**: Take breaks between phases to absorb the information