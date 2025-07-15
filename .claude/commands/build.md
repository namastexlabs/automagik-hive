# /build

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Bash(*), Glob(*), Grep(*), mcp__gemini__*, mcp__search-repo-docs__*, mcp__ask-repo-agent__*, mcp__genie_memory__*, mcp__send_whatsapp_message__*, mcp__wait__*
description: Implement features, write code, and build functionality
---

Build and implement features, write code, and create functionality from requirements.

## Auto-Loaded Project Context:
@/CLAUDE.md
@/docs/ai-context/project-structure.md
@/docs/ai-context/docs-overview.md

## Usage

```bash
# Implement new features
/build "Add user authentication system"
/build "Create payment processing API"
/build "Implement real-time notifications"

# Code specific functionality
/build "Write function to validate email addresses"
/build "Create database migration for user table"
/build "Build REST endpoints for product catalog"
```

## Intelligent Implementation Strategy

### Step 1: Requirement Analysis
Parse user request: "$ARGUMENTS"

**Implementation Categories:**
- **Simple Function/Util** → Direct implementation
- **API/Endpoint** → Pattern-based implementation  
- **Feature/Component** → Multi-agent analysis
- **System Integration** → Comprehensive analysis

### Step 2: Progressive Enhancement Strategy

**Level 1: Direct Implementation** (Simple tasks)
- Single file implementations
- Follow existing patterns
- Minimal dependencies

**Level 2: Pattern Analysis** (Moderate complexity)
- Analyze existing similar implementations
- Use 1-2 sub-agents for guidance
- Follow established conventions

**Level 3: Multi-Agent Design** (Complex features)
- Deploy 2-4 specialized sub-agents:
  - **Architecture_Analyst**: Design approach using project patterns
  - **Implementation_Specialist**: Code structure and organization
  - **Integration_Expert**: Dependencies and connections
  - **Quality_Validator**: Security, performance, testing

**Level 4: Expert Consultation** (High complexity)
- Use Gemini consultation for complex technical decisions
- Repository pattern research via search-repo-docs
- Cross-reference best practices

### Step 3: Implementation Execution

**For Sub-Agent Approach:**
```
Task: "Analyze [COMPONENT] for implementing [FEATURE] related to user request '$ARGUMENTS'"

Standard Implementation Workflow:
1. Review auto-loaded project context (CLAUDE.md, project-structure.md, docs-overview.md)
2. Analyze existing similar implementations for patterns
3. Design approach following project conventions
4. Consider dependencies, security, and performance
5. Plan integration with existing systems
6. Return actionable implementation strategy
```

**CRITICAL: Launch all sub-agents in parallel using single message with multiple Task invocations.**

### Step 4: Code Generation

Based on analysis:
1. **Follow project patterns** - Use existing conventions
2. **Implement incrementally** - Build in logical steps
3. **Add proper typing** - Include type hints and validation
4. **Include error handling** - Robust error management
5. **Add documentation** - Docstrings and comments
6. **Consider testing** - Make code testable

### Step 5: Integration & Validation

- **Test functionality** - Verify implementation works
- **Check dependencies** - Ensure imports resolve
- **Validate patterns** - Follows project conventions
- **Security review** - Check for vulnerabilities
- **Performance check** - No obvious bottlenecks

## Expert Consultation & Advanced Tools

For complex implementations, leverage the full toolkit:

```python
# Complex architectural decisions with Gemini
mcp__gemini__consult_gemini(
    specific_question="How should I implement [complex feature]?",
    problem_description="Need to build [requirement] following [constraints]",
    code_context="Current system uses [patterns]...",
    attached_files=["relevant/files.py"],
    preferred_approach="implement"
)

# Research Agno framework patterns
mcp__search-repo-docs__resolve-library-id(libraryName="agno")
mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/context7/agno",
    topic="Implementation patterns for [feature]",
    tokens=10000
)

# Ask specific implementation questions
mcp__ask-repo-agent__ask_question(
    repoName="agno-agi/agno",
    question="How to implement [specific pattern] with Team routing?"
)

# Coordinate complex multi-step implementations
mcp__wait__wait_minutes(
    minutes=1,
    message="Waiting for test suite to complete before proceeding..."
)

# Notify on critical implementation milestones
mcp__send_whatsapp_message__send_text_message(
    instance="SofIA",
    message="🚀 DEPLOYED: [Feature] implementation complete and tested. Ready for review.",
    number="5511986780008@s.whatsapp.net"
)
```

## Automatic Memory Integration

Every implementation automatically updates memory with findings:

```python
# Store implementation patterns
mcp__genie_memory__add_memory(
    content="PATTERN: [Feature] Implementation - Used [approach] with [technologies] #implementation"
)

# Store solutions and discoveries  
mcp__genie_memory__add_memory(
    content="FOUND: [Problem] solved with [solution] in [file] #solution"
)

# Store task progress
mcp__genie_memory__add_memory(
    content="TASK: Completed [feature] implementation - [status] #task"
)

# Search for existing patterns before starting
mcp__genie_memory__search_memory(
    query="PATTERN [similar feature]"
)
```

## Output Format

```markdown
# Implementation: [Feature Name]

## Analysis Summary
- **Complexity**: [Low/Medium/High]
- **Pattern**: [Following existing pattern X]
- **Integration**: [Dependencies and connections]

## Implementation Plan
1. [Step 1 with file locations]
2. [Step 2 with code structure]  
3. [Step 3 with integration]

## Files Created/Modified
- `file1.py`: [Purpose and changes]
- `file2.py`: [Purpose and changes]

## Memory Updates
- [Patterns stored in memory]
- [Solutions discovered and saved]

## Testing & Validation
- [How to test the implementation]
- [Expected behavior]

## Notifications Sent
- [WhatsApp notifications for major completions]
```

## Automatic Execution

```bash
# Search memory for similar patterns
mcp__genie_memory__search_memory query="PATTERN implementation $ARGUMENTS"

# For complex features, consult Gemini
if [[ "$ARGUMENTS" =~ complex|architecture|system ]]; then
    mcp__gemini__consult_gemini \
        specific_question="How to implement: $ARGUMENTS" \
        problem_description="Building new functionality in genie-agents system" \
        preferred_approach="implement"
fi

# Notify on completion
mcp__send_whatsapp_message__send_text_message \
    instance="SofIA" \
    message="🚀 BUILD: Starting implementation of: $ARGUMENTS" \
    number="5511986780008@s.whatsapp.net"
```

---

**Smart Implementation**: From requirements to working code following your project's architecture and patterns.