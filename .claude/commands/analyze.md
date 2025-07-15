# /analyze

---
allowed-tools: mcp__zen__analyze(*), Read(*), Bash(*), Glob(*), Grep(*)
description: Comprehensive code and architecture analysis with optional model selection
---

Analyze code, architecture, performance, or security aspects of your project using the best AI model for the task.

## Usage

```bash
# Default (uses Claude)
/analyze "Review the authentication system architecture"

# With specific model
/analyze "Analyze database query performance" model="o3"
/analyze "Security review of API endpoints" model="grok"
/analyze "Scalability assessment" model="gemini"
```

## Model Strengths

- **Claude** (default): Comprehensive analysis with project context
- **O3**: Logical analysis, systematic evaluation
- **Grok**: Large context analysis (256K tokens)
- **Gemini**: Architectural insights and patterns

## Analysis Types

- **Architecture**: System design, patterns, scalability
- **Performance**: Bottlenecks, optimization opportunities
- **Security**: Vulnerabilities, best practices
- **Quality**: Code smells, maintainability
- **General**: Overall assessment

## Automatic Execution

/mcp__zen__analyze "$ARGUMENTS" model="${MODEL:-claude}" analysis_type="${TYPE:-general}"

---

**Unified Analysis**: One command for all analysis needs. Model selection is optional - defaults to Claude for comprehensive project-aware analysis.