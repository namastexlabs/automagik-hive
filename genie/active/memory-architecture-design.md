# Memory-Based Context System Architecture

## Current State Assessment

### What We Have ✅
- Simple 3-prefix system: PATTERN/TASK/FOUND
- All agents can read/write to memory
- Basic memory integration working
- Context injection via task-context-injector.sh
- WhatsApp notifications for updates

### What We Need 🎯
- Systematic memory architecture
- Migration from file-based to memory-based context
- Scalable memory patterns
- Integration with existing workflows

## Memory Architecture Design

### 1. Memory Schema Layers

```
📚 KNOWLEDGE LAYER (Persistent)
├── PATTERN: [name] - [solution] #tags
├── FOUND: [discovery] - [context]
└── DECISION: [choice] - [rationale]

🔄 ACTIVITY LAYER (Dynamic)
├── TASK: [id] - [status] - [agent]
├── PROGRESS: [epic] - [phase] - [metrics]
└── HANDOFF: [from] to [to] - [message]

💬 COMMUNICATION LAYER (Real-time)
├── STATUS: [component] - [current_state]
├── BLOCKER: [task] needs [requirement]
└── DISCOVERY: [agent] found [insight]
```

### 2. Context Replacement Strategy

#### Phase 1: Hybrid (Current) ✅
```python
# Files for structure, memory for discoveries
memory.add("FOUND: API structure at api/main.py")
memory.add("FOUND: Tests run with 'uv run pytest'")
memory.add("PATTERN: FastAPI routing - Use APIRouter for modules")
```

#### Phase 2: Memory-First (Next)
```python
# Replace CONTEXT.md with memory queries
def get_project_context():
    return {
        "architecture": memory.search("FOUND: architecture"),
        "patterns": memory.search("PATTERN:"),
        "current_work": memory.search("TASK: status:"),
        "recent_decisions": memory.search("DECISION:")
    }
```

#### Phase 3: Pure Memory (Future)
```python
# No CONTEXT.md files, everything in memory
memory.add("PROJECT: Tech stack - FastAPI, PostgreSQL, Agno framework")
memory.add("PROJECT: Authentication - JWT with refresh tokens")
memory.add("PROJECT: Database - PostgreSQL with Alembic migrations")
```

### 3. Memory Query Patterns

#### Context Building Queries
```python
# Get full context for a feature
def build_context(topic):
    return {
        "patterns": memory.search(f"PATTERN: {topic}"),
        "current_status": memory.search(f"TASK: {topic}"),
        "discoveries": memory.search(f"FOUND: {topic}"),
        "decisions": memory.search(f"DECISION: {topic}"),
        "blockers": memory.search(f"BLOCKER: {topic}")
    }

# Examples
auth_context = build_context("authentication")
api_context = build_context("api")
database_context = build_context("database")
```

#### Real-Time Awareness Queries
```python
# What's happening right now?
current_work = memory.search("TASK: Working")
recent_discoveries = memory.search("FOUND:")
active_blockers = memory.search("BLOCKER:")

# Who's doing what?
agent_status = memory.search("TASK: - Alice")
handoffs = memory.search("HANDOFF: TO: Bob")
```

### 4. Integration Points

#### A. Task Context Injector Enhancement
```bash
# Current: Static file references
# Enhanced: Dynamic memory queries

get_memory_context() {
    echo "=== CURRENT PROJECT STATE ==="
    memory.search("TASK: Working" | head -3)
    echo "=== RECENT DISCOVERIES ==="
    memory.search("FOUND:" | head -5)
    echo "=== RELEVANT PATTERNS ==="
    memory.search("PATTERN: $TASK_TOPIC" | head -3)
}
```

#### B. Epic Progress Tracking
```python
# Epic status from memory
def epic_status(epic_id):
    return {
        "completed": memory.search(f"TASK: {epic_id} DONE"),
        "in_progress": memory.search(f"TASK: {epic_id} Working"),
        "blockers": memory.search(f"TASK: {epic_id} BLOCKED"),
        "discoveries": memory.search(f"FOUND: epic {epic_id}"),
        "patterns": memory.search(f"PATTERN: epic {epic_id}")
    }
```

#### C. Agent Handoff System
```python
# Structured handoffs
def handoff_task(from_agent, to_agent, task_id, message):
    memory.add(f"HANDOFF: FROM: {from_agent} TO: {to_agent} TASK: {task_id} MESSAGE: {message}")
    memory.add(f"TASK: {task_id} STATUS: HANDED_OFF NEXT_AGENT: {to_agent}")

# Check for handoffs
def check_handoffs(agent_name):
    return memory.search(f"HANDOFF: TO: {agent_name}")
```

## Migration Plan

### Week 1: Foundation
- ✅ Simple prefixes working
- ✅ Memory integration basic patterns
- 🔄 Enhanced context injection (T-002)

### Week 2: Context Migration
- Replace most CONTEXT.md usage with memory queries
- Update task-context-injector.sh for dynamic context
- Implement epic progress tracking

### Week 3: Advanced Patterns
- Agent handoff system
- Cross-epic pattern sharing
- Memory-based project onboarding

### Week 4: Pure Memory
- Eliminate remaining CONTEXT.md files
- Full memory-based context system
- Self-documenting project state

## Implementation Strategy

### 1. Enhanced Memory Prefixes

```python
# Current: Basic 3 prefixes
PATTERN: [name] - [solution]
TASK: [id] - [status] 
FOUND: [discovery]

# Enhanced: Structured context
PROJECT: [component] - [details]          # Permanent project info
EPIC: [id] - [status] - [progress]        # Epic tracking
AGENT: [name] - [current_task] - [status] # Agent coordination
ERROR: [issue] - [solution] - [verified]  # Error library
DECISION: [choice] - [rationale] - [date] # Decision log
```

### 2. Context Query System

```python
class ContextBuilder:
    def __init__(self):
        self.memory = memory
    
    def project_overview(self):
        """Get high-level project context"""
        return {
            "tech_stack": self.memory.search("PROJECT: tech"),
            "architecture": self.memory.search("PROJECT: architecture"),
            "patterns": self.memory.search("PATTERN:")[:10]
        }
    
    def current_activity(self):
        """Get what's happening now"""
        return {
            "active_tasks": self.memory.search("TASK: Working"),
            "recent_discoveries": self.memory.search("FOUND:")[:5],
            "blockers": self.memory.search("TASK: BLOCKED")
        }
    
    def topic_context(self, topic):
        """Get everything related to a topic"""
        return {
            "patterns": self.memory.search(f"PATTERN: {topic}"),
            "decisions": self.memory.search(f"DECISION: {topic}"),
            "discoveries": self.memory.search(f"FOUND: {topic}"),
            "current_work": self.memory.search(f"TASK: {topic}"),
            "errors": self.memory.search(f"ERROR: {topic}")
        }
```

### 3. Automated Context Injection

```bash
# Enhanced task-context-injector.sh
#!/bin/bash

# Get dynamic context from memory
PROJECT_CONTEXT=$(memory.search "PROJECT:" | head -5)
CURRENT_WORK=$(memory.search "TASK: Working" | head -3)
RECENT_PATTERNS=$(memory.search "PATTERN:" | head -5)

CONTEXT_PREFIX="=== DYNAMIC PROJECT CONTEXT ===
Current Project State:
$PROJECT_CONTEXT

Active Work:
$CURRENT_WORK

Recent Patterns:
$RECENT_PATTERNS

=== MEMORY QUERIES ===
- Current work: memory.search('TASK: Working')
- Find patterns: memory.search('PATTERN: [topic]')
- Check discoveries: memory.search('FOUND: [topic]')
- See decisions: memory.search('DECISION: [topic]')

Your assigned task:"
```

## Success Metrics

### Immediate (T-002 Complete)
- [ ] Memory architecture documented
- [ ] Enhanced context injection working
- [ ] Project context queries defined
- [ ] Migration plan approved

### Short-term (1 week)
- [ ] 80% of context queries use memory
- [ ] CONTEXT.md usage reduced by 50%
- [ ] Agent handoff system working

### Long-term (1 month)
- [ ] Zero CONTEXT.md files
- [ ] Pure memory-based context
- [ ] Self-documenting project state
- [ ] New agent onboarding via memory

## Next Steps

1. **Complete T-002**: Finalize this architecture design
2. **Implement Enhanced Context Injection**: Update hooks
3. **Start T-007**: Status monitoring system
4. **Begin Migration**: Replace file context with memory
5. **Test Cross-Agent**: Verify memory sharing works

This architecture enables the vision of omnipresent project intelligence!