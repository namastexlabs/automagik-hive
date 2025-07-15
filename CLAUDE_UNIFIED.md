# Genie Agents - Multi-Agent System with Zen Framework

## Quick Start
```bash
make dev    # Start on port 9888
make test   # Run all tests
```

## 1. Core Architecture
- **Agents**: YAML-configured specialists (`agents/{name}/config.yaml`)
- **Teams**: Intelligent routing via `Team(mode="route")`
- **Workflows**: Sequential automation (`workflows/`)
- **Memory**: Automated capture via hooks (no manual calls!)
- **Zen Framework**: Multi-model AI access (O3, Grok, Gemini Pro)

## 2. Command System with Zen Integration

### Essential Commands
```bash
/wish "Add WhatsApp notifications to human handoff"   # Smart routing
/analyze "Review team routing logic" model="o3"       # Code analysis
/debug "Ana team not selecting correct agent" model="grok"  # Debugging
/plan "Multi-tenant support architecture" model="pro"       # Planning
/test "Generate tests for human handoff" model="o3"         # Testing
/review "Check PR #123" model="grok"                        # Code review
```

### Zen Model Selection
Available models via zen framework:
- **o3**: Strong reasoning, logical problems (200K context)
- **grok**: Large context analysis (256K context) 
- **pro**: Gemini 2.5 Pro with thinking mode (1M context)
- **mini**: O4 Mini for quick tasks (200K context)

### Command Integration with Zen
Each command automatically uses zen tools:

#### /analyze → mcp__zen__analyze
```python
mcp__zen__analyze(
    model="o3",  # or grok, pro
    step="Analyze system architecture",
    relevant_files=["path/to/code"],
    analysis_type="architecture"
)
```

#### /debug → mcp__zen__debug  
```python
mcp__zen__debug(
    model="grok",  # Large context for complex traces
    step="Debug routing issue",
    hypothesis="Ana team routing logic error",
    thinking_mode="high"
)
```

#### /plan → mcp__zen__planner + mcp__zen__consensus
```python
# Multi-model consensus for architecture
mcp__zen__consensus(
    models=[
        {"model": "o3", "stance": "for"},
        {"model": "grok", "stance": "against"}, 
        {"model": "pro", "stance": "neutral"}
    ],
    step="Evaluate architecture approach"
)
```

## 3. Automated Memory System

### Hook-Based Capture
All tool outputs automatically captured:
```bash
.claude/hooks/
├── task-output-capture.sh      # Captures all Task() results  
├── tool-usage-logger.sh        # Logs successful patterns
├── error-memory-capture.sh     # Stores errors + fixes
└── zen-consultation-logger.sh  # Captures zen insights
```

### Memory Categories (Auto-Generated)
- **ERROR**: Exceptions, failures, issues
- **FIX**: Solutions that resolved errors  
- **PATTERN**: Repeated successful approaches
- **FOUND**: Discoveries, configurations, insights
- **ZEN**: Multi-model consultation insights

### Searching Memory
```python
# Just search - no manual adding needed!
mcp__genie-memory__search_memory(query="database setup")
mcp__genie-memory__search_memory(query="ERROR routing")
mcp__genie-memory__search_memory(query="ZEN architecture")
```

## 4. Zen-Enhanced Development Workflow

### Simple Task Flow
```bash
1. /wish "Your request"          # Smart routing with zen consultation
2. Zen tools provide multi-model insights  
3. Memory auto-captures all outputs
4. Next time: memory + zen patterns available!
```

### Complex Architecture Flow
```bash
1. /plan "Complex feature" model="pro"    # Gemini architectural planning
2. /analyze "Current system" model="grok" # Large context analysis
3. Zen consensus on approach
4. Implementation with learned patterns
```

### Multi-Model Debugging
```bash
1. /debug "Complex issue" model="o3"      # Logical reasoning
2. If unsolved → /debug same issue model="grok"  # Different perspective
3. Zen consensus on root cause
4. Fix implementation
```

## 5. Configuration

### Environment (.env)
```bash
# Core (Required)
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...

# Zen Framework
GOOGLE_API_KEY=...              # For Gemini Pro
XAI_API_KEY=...                 # For Grok

# Features  
CSV_HOT_RELOAD=true             # Live knowledge updates
DEMO_MODE=true                  # Rich console output
MEMORY_AUTO_CAPTURE=true        # Hook-based memory

# Optional Services
EVOLUTION_API_BASE_URL=...      # WhatsApp
```

### Agent Configuration (YAML)
```yaml
agent:
  agent_id: "specialist"
  name: "Domain Expert"

model:
  provider: "anthropic"
  id: "claude-3-5-sonnet-20241022"

tools:
  - "search_knowledge_base"

knowledge_filter:
  business_unit: "Domain"
  csv_file_path: "context/knowledge/knowledge_rag.csv"
```

## 6. Zen Framework Tools

### Multi-Model Consultation
```python
# Get consensus from multiple models
mcp__zen__consensus(
    models=[
        {"model": "o3", "stance": "for"},
        {"model": "grok", "stance": "against"},
        {"model": "pro", "stance": "neutral"}
    ],
    step="Architecture decision",
    findings="Current analysis..."
)

# Deep investigation with thinking mode
mcp__zen__thinkdeep(
    model="pro",
    step="Complex problem analysis", 
    thinking_mode="high",
    problem_context="Detailed context..."
)

# Collaborative discussion
mcp__zen__chat(
    model="grok",
    prompt="Discuss implementation approaches",
    use_websearch=true
)
```

### Specialized Analysis
```python
# Code review with zen
mcp__zen__codereview(
    model="o3",
    step="Review authentication system",
    relevant_files=["auth/", "security/"]
)

# Test generation
mcp__zen__testgen(
    model="o3", 
    step="Generate comprehensive tests",
    relevant_files=["agents/human_handoff/"]
)

# Security audit
mcp__zen__secaudit(
    model="grok",
    step="Security assessment",
    audit_focus="owasp"
)
```

## 7. Other MCP Tools

### Memory (Automated)
- `mcp__genie-memory__search_memory()` - Search captured knowledge
- `mcp__genie-memory__add_memories()` - Store insights (automated via hooks)

### Documentation Search
- `mcp__search-repo-docs__*` - Agno framework docs
- `mcp__ask-repo-agent__*` - Repository Q&A

### Notifications
- `mcp__send_whatsapp_message__*` - Customer notifications

## 8. Automated Hook System

### Tool Output Capture
```bash
# Every zen consultation automatically stored
mcp__zen__analyze → "ZEN: [o3] Architecture analysis found X patterns"
mcp__zen__debug → "ZEN: [grok] Debug trace revealed Y root cause"  
mcp__zen__consensus → "ZEN: [multi] Consensus: approach Z recommended"
```

### Pattern Detection
After multiple zen consultations:
- "PATTERN: [ZEN] o3 best for logical debugging"
- "PATTERN: [ZEN] grok excels at large context analysis"
- "PATTERN: [ZEN] consensus needed for architecture decisions"

### Error Learning  
```bash
# Zen tools help debug → automatic capture
Error: "Import cycle in agents/"
/debug with zen → Fix discovered
Auto-stored: "FIX: [ZEN] Import cycles resolved by restructuring"
```

## 9. Testing & Quality

```bash
# Type checking
mypy agents/ --strict

# Run tests with zen-generated tests
pytest tests/zen_generated/  # Tests from mcp__zen__testgen
make test                    # All tests

# Linting
ruff check .
ruff format .

# Zen-powered code review
/review "current changes" model="o3"
```

## 10. Common Zen-Enhanced Patterns

### Adding New Agent
1. `/plan "New agent for domain X" model="pro"`
2. Zen provides architecture guidance
3. Copy existing agent YAML with zen recommendations
4. `/test "Generate tests for new agent" model="o3"`

### Debugging Complex Issues
```bash
1. /debug "Issue description" model="grok"    # Large context
2. If unresolved → /debug same issue model="o3"  # Different approach
3. Zen consensus on root cause
4. Memory auto-captures the solution pattern
```

### Architecture Decisions
```bash
1. /analyze "Current system" model="grok"     # Full context analysis
2. /plan "Proposed changes" model="pro"       # Creative solutions  
3. Zen consensus with multiple models
4. Implementation guided by zen insights
```

## 11. Zen Model Characteristics

### When to Use O3
- Logical debugging problems
- Systematic code analysis
- Step-by-step reasoning tasks
- Complex algorithm design

### When to Use Grok  
- Large codebase analysis (256K context)
- Multi-file architectural review
- Complex trace analysis
- Performance optimization

### When to Use Pro (Gemini)
- Creative architecture solutions
- Thinking mode for complex problems
- Multi-modal analysis (if images)
- Extended reasoning chains

### When to Use Consensus
- Major architectural decisions
- Conflicting implementation approaches  
- Risk assessment for critical changes
- Validation of complex solutions

## Quick Reference

### Zen Commands
- `/analyze model="o3"` - Systematic analysis
- `/debug model="grok"` - Large context debugging
- `/plan model="pro"` - Creative architecture  
- Consensus: Multiple models for decisions

### Memory Search
- `search_memory("ZEN architecture")` - Zen insights
- `search_memory("ERROR routing")` - Past problems
- `search_memory("PATTERN zen")` - Usage patterns

### Key Paths
- Agents: `agents/{name}/config.yaml`
- Teams: `teams/{name}/config.yaml`
- Knowledge: `context/knowledge/knowledge_rag.csv`
- Hooks: `.claude/hooks/`
- Commands: `.claude/commands/`

### Debugging
- API Docs: http://localhost:9888/docs
- Health: http://localhost:9888/api/v1/health
- Demo Mode: `DEMO_MODE=true`
- Zen Models: `/listmodels` command

## Zen Integration Benefits

✅ **Multi-Model Intelligence**: Different models for different problems
✅ **Automated Capture**: All zen insights stored automatically  
✅ **Pattern Learning**: System learns which models work best
✅ **Consensus Decisions**: Multiple perspectives on complex issues
✅ **Context Preservation**: Large context models for full analysis
✅ **Specialized Tools**: Code review, testing, security audits

Remember: The zen framework provides the right AI model for each task. Commands handle complexity, hooks capture knowledge, and zen provides multi-model intelligence. Focus on building - the system learns your patterns!