# /docs

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Glob(*), Grep(*), mcp__gemini__*, mcp__search-repo-docs__*, mcp__genie_memory__*, mcp__send_whatsapp_message__*
description: Generate and update documentation
---

Create complete documentation for code, APIs, and systems with expert guidance.

## Auto-Loaded Project Context:
@/CLAUDE.md
@/docs/ai-context/project-structure.md
@/docs/ai-context/docs-overview.md

## Usage

```bash
# Generate docs for specific code
/docs "Create API documentation for auth endpoints"
/docs "Document the agent routing system"
/docs "Generate README for payment module"

# Update existing docs
/docs "Update architecture docs with new caching"
/docs "Add examples to authentication guide"

# With specific style
/docs "Technical specification for database schema" style="technical"
/docs "User guide for API integration" style="user-friendly"
```

## Documentation Types

- **API**: Endpoint documentation with examples
- **Code**: Function and class documentation
- **Architecture**: System design and structure
- **User Guides**: How-to and tutorials
- **Technical Specs**: Detailed specifications
- **README**: Project overviews and setup

## Features

- Code-aware documentation
- Auto-generated examples
- Consistent formatting
- Integration with existing docs
- Multi-format output (Markdown, HTML, etc.)

## Model Selection

- **Claude** (default): Context-aware, follows project style
- **Gemini**: Creative explanations and examples
- **O3**: Systematic, complete documentation

## Expert Consultation & Notifications

For complex documentation:

```python
# Expert documentation guidance
mcp__gemini__consult_gemini(
    specific_question="How to document [complex system]?",
    problem_description="Need complete docs for [component]",
    code_context="System has [architecture and patterns]...",
    attached_files=["relevant/files.py"],
    preferred_approach="explain"
)

# Notify when documentation is completed
mcp__send_whatsapp_message__send_text_message(
    instance="SofIA",
    message="📝 DOCS: Documentation updated for [component]. New guides and API docs available.",
    number="5511986780008@s.whatsapp.net"
)
```

## Automatic Memory Integration

Every documentation task automatically updates memory:

```python
# Store documentation patterns
mcp__genie_memory__add_memory(
    content="PATTERN: Documentation - [Component] documented with [style] approach #docs"
)

# Store documentation locations
mcp__genie_memory__add_memory(
    content="FOUND: [Component] docs at [location] - Covers [topics] #documentation"
)

# Search for existing documentation patterns
mcp__genie_memory__search_memory(
    query="PATTERN documentation [similar component]"
)
```

## Automatic Execution

```bash
# Search for documentation patterns
mcp__genie_memory__search_memory query="PATTERN documentation $ARGUMENTS"

# Research documentation best practices
mcp__search-repo-docs__get-library-docs \
    context7CompatibleLibraryID="/context7/agno" \
    topic="Documentation standards and examples" \
    tokens=5000

# Notify when docs are complete
mcp__send_whatsapp_message__send_text_message \
    instance="SofIA" \
    message="📝 DOCS: Starting documentation for: $ARGUMENTS" \
    number="5511986780008@s.whatsapp.net"
```

---

**Smart Documentation**: Generate docs that match your project's style and needs.
