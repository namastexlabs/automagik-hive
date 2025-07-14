# CLAUDE.md

<state_configuration>
<!-- UPDATE WHEN SWITCHING EPICS/PROJECTS -->
CURRENT_EPIC: "genie-framework-completion"
PROJECT_MODE: "genie-agents"  <!-- automagik-v2 | genie-agents -->
</state_configuration>

<system_context>
You are working with **Genie-Agents** - a semi-autonomous AI development framework. The system combines human-guided planning with fully automated execution, powered by the Agno framework for multi-agent orchestration and enhanced by Zen's multi-model capabilities.

**Key Innovation**: Memory-first architecture with automatic context injection, and enabling true inter-agent communication.
</system_context>

<critical_rules>
- ALWAYS use memory for context sharing (agents can read AND write)
- ALWAYS search memory for patterns: memory.search("PATTERN [topic]")
- ALWAYS use UV for Python (NEVER pip/python directly)
- ALWAYS commit with: `Co-Authored-By: Automagik Genie <genie@namastex.ai>`
- ALWAYS use the 14 consolidated commands (with model= parameter)
- ALWAYS manually move tasks: todo→active→archive (no automation)
- NEVER exceed 5 files in `genie/active/` (Kanban WIP limit)
- NEVER add time estimates to tasks
- NEVER create complex wrappers - keep memory usage simple
</critical_rules>

## Command System (16 Commands)

<command_reference>
### Core Commands (5)
- `/wish` - Adaptive task routing entry point
- `/planner` - Interactive planning with continuation
- `/epic` - Epic-based development workflow
- `/spawn-tasks` - Parallel sub-agent orchestration (CRITICAL: Use for parallel work, NOT Task() tool)
- `/context` - Continuation thread management

### Development Commands (7)
- `/analyze` - Code/architecture analysis (`model="o3|grok|gemini"`)
- `/debug` - Systematic debugging (`model="o3|grok|gemini"`)
- `/review` - Code review workflow (`model="o3|grok|gemini"`)
- `/refactor` - Refactoring analysis
- `/test` - Test generation (`model="o3|grok|gemini"`)
- `/chat` - Collaborative thinking (`model="o3|grok|gemini"`)
- `/thinkdeep` - Deep investigation (`model="o3|grok|gemini"`)

### Documentation Commands (2)
- `/docs` - Create/update documentation
- `/full-context` - Comprehensive analysis

### Context Tools (2)
- `/search-docs` - Search library documentation via Context7
- `/ask-repo` - Interactive Q&A with GitHub repositories

**Example**: `/analyze "Review auth system" model="o3"`
**Agno Docs**: `/ask-repo "agno-agi/agno" "How do I create an agent?"`
</command_reference>

## Memory-First Architecture

<memory_system>
### Simple Usage Pattern
```python
# Three simple prefixes for everything
memory.add("PATTERN: Auth Flow - Use JWT with refresh tokens #auth")
memory.add("TASK T-001: Working on API endpoints - Alice") 
memory.add("FOUND: Run tests with 'uv run pytest'")

# Search is natural
results = memory.search("PATTERN auth")     # Find auth patterns
status = memory.search("TASK T-001")        # Check task status
knowledge = memory.search("FOUND tests")    # How to run tests
```

### Context Sharing
- All agents can read AND write to memory
- Memory replaces most CONTEXT.md files
- Automatic context search in task-context-injector.sh
- Files only for: structured data, large documents, version control

### Context Tools
- **Search Repo**: `/context7/agno` for Agno framework documentation
- **Ask Repo**: `agno-agi/agno` for Q&A with latest Agno repository

### Memory Patterns
1. **Project Context**: Architecture decisions, tech stack
2. **Error Solutions**: Known issues and fixes
3. **Task Progress**: What's been done, what's pending
4. **Agent Communication**: Messages between agents
5. **User Preferences**: Learned patterns and style
</memory_system>

## Automated Context Injection

<context_automation>
### Hook System
The `task-context-injector.sh` hook automatically prepends to ALL Task() calls:
1. Essential project context from CLAUDE.md
2. Technical foundation from ai-context files
3. Memory search instructions

### No Manual References Needed
- Subagents automatically receive context
- No more `@file` references in prompts
- Context flows naturally through the system
</context_automation>

## Quick Start

<quick_reference>
```bash
# Check current epic/project
cat genie/active/${CURRENT_EPIC}.md

# Start development (port 7777)
uv run python api/playground.py

# Run tests
uv run pytest tests/

# Type checking
uv run mypy agents/ --strict

# Quality checks
uv run ruff check .
uv run ruff format .
```
</quick_reference>

## Development Flow

<workflow>
1. **Check Patterns**: Review `@genie/reference/` first
2. **Use Memory**: Add discoveries as you work
3. **Simple Commands**: Use the 14 commands with model parameter
4. **Manual Task Management**: Move tasks todo→active→archive manually
5. **Test Everything**: Type checks, unit tests, integration tests
6. **Archive Complete**: Move done work to `genie/archive/`
</workflow>

## Project Structure

<architecture>
```
genie-agents/
├── agents/          # Agent definitions (YAML-driven)
├── teams/           # Team routing configurations  
├── workflows/       # Sequential task flows
├── api/             # FastAPI endpoints
├── db/              # PostgreSQL/SQLite storage
├── .claude/         
│   ├── commands/    # 14 consolidated commands
│   └── hooks/       # task-context-injector.sh
└── genie/           # Framework workspace (see genie/CLAUDE.md)
```
</architecture>

## Critical Reminders

<reminders>
✅ Memory is bidirectional - all agents read/write
✅ Commands use model= parameter (not separate files)
✅ Context injection is automatic via hooks
✅ Keep it simple - no complex wrappers
✅ Test with mypy and pytest before completing
✅ Archive to maintain 5-file active limit
✅ Manual task orchestration (no hook automation)

❌ No time estimates on tasks
❌ No backwards compatibility needed
❌ No pip - always use uv
❌ No manual context references
❌ No automatic task management (hooks don't work)
</reminders>

---

**For Genie Framework details**: See `genie/CLAUDE.md`
**For technical standards**: See `genie/ai-context/development-standards.md`
**For project structure**: See `genie/ai-context/project-structure.md`