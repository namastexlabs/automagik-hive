# Context Search Tools for Agno Development

**Navigation**: [← YAML Configuration](./yaml-configuration.md) | [THIS FILE] | [Task Cards →](../task-cards/00-task-overview.md)

## Available MCP Tools

### 1. Resolve Library ID
```python
# First step - find the Agno library ID
library_info = mcp__search-repo-docs__resolve-library-id(
    libraryName="agno"  # or "agnolabs/agno"
)

# Returns list of matches with:
# - library_id: "/agnolabs/agno" 
# - description: Framework info
# - trust_score: 7-10 range
# - code_snippets: Available examples
```

### 2. Get Library Documentation
```python
# Second step - retrieve specific docs
docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/agnolabs/agno",  # From step 1
    topic="teams",      # Optional: focus area
    tokens=10000        # Optional: max tokens (default 10000)
)

# Topics available:
# - "agents" - Agent creation and configuration
# - "teams" - Team composition and routing
# - "workflows" - Sequential/parallel workflows
# - "memory" - Session and storage management
# - "tools" - Tool creation and integration
# - "models" - Model configuration
# - "streaming" - Streaming responses
# - "playground" - Agno playground setup
```

### 3. Ask Specific Questions
```python
# Alternative - ask direct questions
answer = mcp__ask-repo-agent__ask_question(
    repoName="agnolabs/agno",
    question="How do I implement Team with mode='route'?"
)

# Good for:
# - Specific implementation questions
# - Code examples
# - Best practices
# - Troubleshooting
```

## Common Usage Patterns

### Pattern 1: Learning About Teams
```python
# When implementing Ana Team refactor
library_id = mcp__search-repo-docs__resolve-library-id(
    libraryName="agno"
)

team_docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID=library_id,
    topic="teams",
    tokens=15000  # Get comprehensive docs
)

# Extract routing patterns from documentation
routing_examples = extract_code_blocks(team_docs, "mode=\"route\"")
```

### Pattern 2: Understanding Workflows
```python
# For typification workflow implementation
workflow_answer = mcp__ask-repo-agent__ask_question(
    repoName="agnolabs/agno",
    question="Show me an example of a sequential workflow with 5 steps that processes data through multiple agents"
)

# Follow up with specific docs
workflow_docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/agnolabs/agno",
    topic="workflows"
)
```

### Pattern 3: Storage Configuration
```python
# When setting up PostgreSQL
storage_question = mcp__ask-repo-agent__ask_question(
    repoName="agnolabs/agno",
    question="How do I configure PostgreSQL storage with Agno including session management?"
)

# Get memory management details
memory_docs = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/agnolabs/agno",
    topic="memory"
)
```

## Integration with Task Cards

### In Task Implementation
```python
# Example from phase1/01-refactor-ana-team.md
def implement_ana_team():
    # 1. Get Agno team patterns
    team_examples = mcp__search-repo-docs__get-library-docs(
        context7CompatibleLibraryID="/agnolabs/agno",
        topic="teams"
    )
    
    # 2. Find mode=config["team"]["mode"] pattern
    route_pattern = extract_pattern(team_examples, "mode=\"route\"")
    
    # 3. Apply to Ana implementation
    ana_team = Team(
        name="Ana - PagBank Assistant",
        team_id="ana-team-v2",
        mode=config["team"]["mode"],  # From YAML
        members=[...]
    )
```

### For Debugging Issues
```python
# When something doesn't work as expected
debug_answer = mcp__ask-repo-agent__ask_question(
    repoName="agnolabs/agno",
    question="Why would Team mode='route' not be routing to the correct agent? Debug tips?"
)
```

## Best Practices

### 1. Start with Library ID
```python
# Always resolve ID first (unless you know it)
library_id = mcp__search-repo-docs__resolve-library-id(
    libraryName="agno"
)
# Usually returns: "/agnolabs/agno"
```

### 2. Use Topics for Focused Search
```python
# Don't retrieve everything - use topics
AGNO_TOPICS = [
    "agents",      # Individual agent setup
    "teams",       # Team composition
    "workflows",   # Multi-step processes
    "memory",      # State management
    "tools",       # Custom tools
    "models",      # LLM configuration
    "streaming",   # Response streaming
    "playground"   # UI setup
]
```

### 3. Combine Tools Effectively
```python
# 1. Get overview with docs
overview = mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/agnolabs/agno",
    topic="teams"
)

# 2. Ask specific implementation question
details = mcp__ask-repo-agent__ask_question(
    repoName="agnolabs/agno", 
    question=f"Based on this pattern: {pattern}, how do I add custom routing logic?"
)
```

## Common Agno Questions

### Agent Creation
```python
q1 = "How do I create an Agent with system prompt and tools?"
q2 = "What's the difference between instructions and system_prompt?"
q3 = "How do I add custom tools to an Agent?"
```

### Team Routing
```python
q1 = "How does Team mode='route' decide which agent to use?"
q2 = "Can I customize the routing logic in Team?"
q3 = "How to handle routing failures?"
```

### Workflow Steps
```python
q1 = "How do I pass data between workflow steps?"
q2 = "Can workflow steps be conditional?"
q3 = "How to handle errors in workflows?"
```

### Session Management
```python
q1 = "How does Agno handle session persistence?"
q2 = "Can I share sessions between agents?"
q3 = "How to implement custom memory storage?"
```

## Troubleshooting

### If Documentation Seems Outdated
```python
# Ask about version
version_info = mcp__ask-repo-agent__ask_question(
    repoName="agnolabs/agno",
    question="What's the latest version of Agno and what changed recently?"
)
```

### If Examples Don't Work
```python
# Get working example
working_example = mcp__ask-repo-agent__ask_question(
    repoName="agnolabs/agno",
    question="Show me a complete working example of [specific feature] that I can copy"
)
```

### If Concept Unclear
```python
# Get explanation
explanation = mcp__ask-repo-agent__ask_question(
    repoName="agnolabs/agno",
    question="Explain [concept] in simple terms with an analogy"
)
```

## Integration with Multi-Agent Development

### For Parallel Agents
Each agent working on task cards should:

1. **Check if Agno knowledge needed**:
   ```python
   if "Team" in task_title or "Agent" in task_title:
       docs = get_agno_documentation()
   ```

2. **Cache responses locally**:
   ```python
   # Save to reference for other agents
   with open("genie/reference/agno-team-examples.md", "w") as f:
       f.write(docs)
   ```

3. **Share patterns discovered**:
   ```python
   # Document in task completion
   pattern_found = {
       "feature": "Team routing",
       "pattern": "mode='route'",
       "example": code_snippet
   }
   ```

**Navigation**: [← YAML Configuration](./yaml-configuration.md) | [THIS FILE] | [Task Cards →](../task-cards/00-task-overview.md)