# /wish

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Glob(*), Grep(*), Bash(*), LS(*), NotebookRead(*), NotebookEdit(*), WebFetch(*), TodoWrite(*), WebSearch(*), ListMcpResourcesTool(*), ReadMcpResourceTool(*), mcp__zen__chat(*), mcp__zen__thinkdeep(*), mcp__zen__planner(*), mcp__zen__consensus(*), mcp__zen__codereview(*), mcp__zen__precommit(*), mcp__zen__debug(*), mcp__zen__secaudit(*), mcp__zen__docgen(*), mcp__zen__analyze(*), mcp__zen__refactor(*), mcp__zen__tracer(*), mcp__zen__testgen(*), mcp__zen__challenge(*), mcp__zen__listmodels(*), mcp__zen__version(*), mcp__search-repo-docs__*, mcp__ask-repo-agent__*, mcp__wait__*, mcp__send_whatsapp_message__*
description: Transform user wishes into structured epics through intelligent analysis, multi-model consultation, and automated orchestration
---

🚧 **DEVELOPMENT MODE** 🚧
Testing the complete wish → epic → tasks workflow with context injection and automation.

Transform any development wish into a fully orchestrated epic with automatic task generation and context flow.

## Enhanced Workflow (Learning from CCDK)

```mermaid
graph TD
    A[User: /wish "I want..."] --> B[Claude: Analyzes wish]
    B --> C{Complex enough for Gemini?}
    C -->|Yes| D[/gemini-consult for architecture advice]
    C -->|No| E[Direct analysis]
    D --> F[Claude: Intelligent Q&A with user]
    E --> F
    F --> G[Claude: /epic to structure]
    G --> H[Claude: /spawn-tasks to create files]
    H --> I[Hooks: Automate everything]
    I --> J[Ready for multi-agent work]
```

## How It Works

### Phase 1: Wish Analysis & Consultation

When you express a wish, Claude:

1. **Analyzes the request** to understand scope and complexity
2. **Checks existing context**:
   - Current epic state
   - Available patterns in reference/
   - Recently modified files
   - Open issues or blockers

3. **Decides if external consultation needed**:
   ```python
   # Complex architectural decisions → Gemini
   # Framework questions → search-repo-docs
   # Pattern questions → reference/ files
   # Simple tasks → direct processing
   ```

4. **Consults intelligently** (if needed):
   ```python
   # Example: Architecture consultation
   /gemini-consult "User wants: [wish]. Given our epic-based Genie Framework 
                   with @genie/active/genie-framework-analysis-report.md context,
                   what's the best approach for automatic context flow?"
   ```

### Phase 2: Intelligent Dialogue

Claude engages with you to gather context, asking questions based on:
- Wish complexity
- Detected patterns
- Gemini's insights (if consulted)
- Existing framework constraints

Questions are dynamic and contextual, not a rigid form.

### Phase 3: Epic Structuring (Internal)

Claude internally uses `/epic` to:
- Synthesize all gathered information
- Structure tasks with dependencies
- Define success criteria
- Generate comprehensive epic document

### Phase 4: Task Generation (Internal)

Claude uses `/spawn-tasks` to:
- Parse the epic structure
- Create individual task files
- Set up automation triggers
- Initialize reference patterns

### Phase 5: Automation Magic

Hooks handle everything automatically:
- Update CURRENT_EPIC in CLAUDE.md
- Move files to correct folders
- Set up task dependencies
- Inject context for all agents

## Usage Examples

### Simple Wish
```bash
/wish "Fix the routing bug in Ana team"
```
Claude: Direct analysis → targeted questions → bug fix epic

### Complex Wish
```bash
/wish "I wish to finish the creation of my AI development agent team and framework system. My desired output is to create a truly bulletproof framework where context flows automatically to every agent at every level."
```
Claude: Gemini consultation → deep architecture discussion → comprehensive epic

### Feature Wish
```bash
/wish "Add support for #epic: and #task: references in all commands"
```
Claude: Pattern analysis → implementation questions → feature epic

## Intelligent Context Gathering

### What Claude Considers
1. **Existing Patterns**: Checks @genie/reference/* for similar work
2. **Current State**: Reads epic status, active tasks, blockers
3. **Technical Context**: Reviews recent commits, modified files
4. **External Knowledge**: Consults documentation via MCP tools

### Dynamic Question Categories

Based on wish analysis, Claude selects from:

```yaml
architecture_questions:
  - "What's the desired end-state architecture?"
  - "Should we follow patterns from @genie/reference/*?"
  - "Are there external libraries to consider?"

implementation_questions:
  - "Which files are the main touchpoints?"
  - "What's the preferred technical approach?"
  - "Any existing code to preserve?"

validation_questions:
  - "How will we test this?"
  - "What are the success metrics?"
  - "Any compliance requirements?"

scope_questions:
  - "What's explicitly in/out of scope?"
  - "Should this affect all agents or subset?"
  - "Any timeline constraints?"
```

## Multi-Command Orchestration

The `/wish` command orchestrates multiple tools:

1. **Analysis Phase**:
   - `/zen-analyze` - Deep pattern analysis
   - `/full-context` - Comprehensive understanding
   - `/gemini-consult` - Architecture advice

2. **Planning Phase**:
   - `/zen-plan` - Sequential planning
   - `/zen-consensus` - Multi-model validation

3. **Execution Phase**:
   - `/epic` - Structure generation (internal)
   - `/spawn-tasks` - Task creation (internal)

## Context Injection (Coming Soon)

All commands will benefit from automatic context:
- Epic context via #epic:current
- Task context via #task:id
- Pattern context via #pattern:name
- Agent context via #context:agent

## Development Testing Flow

Since we're building this together:

1. **Test Wish Analysis**: Try different wishes, see how it routes
2. **Test Consultations**: When does it consult Gemini/docs?
3. **Test Dialogue**: Are questions extracting good context?
4. **Test Epic Generation**: Quality of structured output
5. **Test Automation**: Do hooks work correctly?

## Next Commands to Build

1. **`/epic`** (internal use): Structures epic from gathered context
2. **`/spawn-tasks`** (internal use): Creates task files from epic
3. **Hooks**: Automate file movements and state updates

---

🚧 **Note**: This is our vision being built live. Each test refines the intelligence.