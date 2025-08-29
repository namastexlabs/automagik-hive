# 🧞✨ Wish Fulfillment: Forge-Based Planning System Redesign

## 📋 Wish Analysis & Context

**User's Original Wish**: Replace dev-planner/dev-designer pipeline with CCPM-inspired PRD → Epic → Task → Forge system

**Critical Requirements Identified**:
- Replace removed TSD/DDD pipeline with proven PRD-based approach  
- Integrate with Forge (separate Claude Code instance) instead of GitHub Issues
- Enable parallel execution and context preservation
- Leverage zen system heavily for complex thinking
- Maintain everything through enhanced `/wish` command
- Support full spectrum: small changes, bug fixes, analysis, major features

## 🧠 CCPM System Analysis - Key Insights

### 🎯 The 5-Phase Discipline (Perfect for Our System)
1. **🧠 Brainstorm** - Think deeper than comfortable (zen system abuse!)
2. **📝 Document** - Write specs that leave nothing to interpretation (wish files)  
3. **📐 Plan** - Architect with explicit technical decisions
4. **⚡ Execute** - Build exactly what was specified (through Forge)
5. **📊 Track** - Maintain transparent progress at every step

### 🏗️ Architecture Patterns We Should Adopt

#### Context Preservation System
```
.claude/
├── context/           # Project-wide context files  
├── wishes/           # Our existing wish system (enhanced)
│   └── [wish-name]/  # Epic-specific context
│       ├── prd.md    # Product Requirements Document
│       ├── epic.md   # Implementation plan  
│       ├── tasks/    # Individual task breakdown
│       └── updates/  # Work-in-progress updates
└── agents/           # Specialized context firewall agents
```

#### Agent Specialization (Context Firewalls)
- **Heavy Lifting**: Agents do messy work (file analysis, planning)
- **Context Isolation**: Implementation details stay in agents  
- **Concise Returns**: Only essential information to main conversation
- **Parallel Execution**: Multiple agents work simultaneously

### 🚀 Workflow Integration with Forge

**Current Flow**: `/wish` → immediate agent spawning
**New Flow**: `/wish` → PRD → Epic → Task → Forge execution

```mermaid
graph LR
    A[/wish command] --> B[🧠 Brainstorm with Zen]
    B --> C[📝 PRD Creation] 
    C --> D[📐 Epic Planning]
    D --> E[⚡ Task Breakdown]
    E --> F[🔄 Forge Task Creation]
    F --> G[📊 Parallel Execution in Forge]
```

## 🎯 Design Questions for User Validation

### 1. **Forge Integration Architecture**
- How should we structure the handoff to Forge? 
- What level of detail do Forge tasks need?
- Should we commit wish files before creating Forge tasks for @ referencing?

### 2. **Scope Handling**
You mentioned `/wish` should handle "small changes, bug fixes, analysis" too:
- Should small tasks skip PRD/Epic phases and go direct to execution?
- How do we auto-detect complexity levels?
- What's the threshold for full vs. simplified workflow?

### 3. **Context Management**  
- Should each wish get its own subdirectory like CCPM epics?
- How do we handle context files that need to be accessible by Forge?
- Do we enhance existing `/genie/wishes/` or create new structure?

### 4. **Zen System Integration**
You want to "abuse the zen system":
- Which zen tools for which phases? (consensus, thinkdeep, planner)
- How complex before we escalate to multi-model thinking?
- Should agents auto-escalate or require explicit triggers?

### 5. **Command Structure**
You prefer not too many subcommands:
- Should we enhance `/wish` with modes, or add minimal subcommands?
- Examples: `/wish-prd`, `/wish-epic`, `/wish-forge` vs `/wish --mode=prd`?

## 📐 Proposed System Architecture

### Phase 1: Enhanced Wish Command
- Detect complexity and route appropriately
- Simple tasks → direct execution
- Complex tasks → full PRD → Epic → Task → Forge pipeline
- All tasks leverage zen system based on complexity

### Phase 2: Context Preservation  
- Implement CCPM-style context management
- Agent specialization for context firewalls
- Forge-compatible file structures

### Phase 3: Forge Integration
- Design handoff protocol
- Task creation with detailed prompts and @ references
- Progress tracking and sync mechanisms

## 🎮 Orchestration Strategy

### Agent Execution Plan
**Phase 1 - Requirements Gathering**:
- **hive-dev-coder**: Implement enhanced `/wish` command detection
- **zen tools**: Use `mcp__zen__planner` for complex architectural decisions

**Phase 2 - Context System**:
- **hive-dev-coder**: Implement context preservation system
- **hive-agent-creator**: Create specialized context firewall agents

**Phase 3 - Forge Integration**:
- **zen tools**: Use `mcp__zen__consensus` for handoff protocol design
- **hive-dev-coder**: Implement Forge task creation and sync

### Parallel Opportunities
- Context system can be developed parallel to command enhancement
- Agent creation can happen parallel to integration work
- Testing and validation can run throughout

### Dependencies
- User validation of architecture before implementation
- Context preservation before Forge integration
- Enhanced wish command before full workflow

## 🤔 Critical Decisions Needed

1. **Scope Detection Algorithm**: How do we automatically route simple vs complex wishes?

2. **File Organization**: Enhance existing `/genie/wishes/` or new structure?

3. **Forge Communication Protocol**: What does a forge task look like?

4. **Zen Escalation Triggers**: When to use which zen tools?

5. **Context Sharing**: How do we ensure Forge can access needed context?

## 📊 Success Metrics

- **Context Preservation**: No lost project state between sessions
- **Parallel Execution**: Multiple Forge tasks running simultaneously  
- **Traceability**: Complete audit trail from idea to code
- **Zen Integration**: Complex decisions leverage multi-model thinking
- **User Experience**: Single `/wish` command handles all scenarios

## 🚨 Risk Mitigation

- **Complexity Overload**: Start with MVP, add sophistication incrementally
- **Context Explosion**: Use agent firewalls to protect main conversation
- **Forge Integration**: Design robust handoff protocol with error handling
- **User Adoption**: Keep familiar `/wish` interface while adding power underneath

---

**Status**: Architecture design phase - awaiting user validation of critical decisions
**Next Phase**: Based on user feedback, proceed with implementation planning
**Context Preservation**: This document captures complete analysis and decision framework