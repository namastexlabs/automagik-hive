# /thinkdeep

---
allowed-tools: mcp__zen__thinkdeep(*), Read(*), Bash(*), Glob(*), Grep(*), Task(*), WebSearch(*)
description: Deep investigation and reasoning for complex problems with optional model selection
---

Comprehensive investigation and reasoning workflow for complex problems requiring systematic analysis, hypothesis testing, and expert validation.

## Usage

```bash
# Default (uses Claude)
/thinkdeep "Why is our agent routing failing intermittently?"

# With specific model
/thinkdeep "Analyze system architecture for bottlenecks" model="o3"
/thinkdeep "Debug memory leak in production" model="grok"
/thinkdeep "Investigate security vulnerabilities" model="gemini"
```

## Model Strengths

- **Claude** (default): Holistic analysis with full project context
- **O3**: Systematic investigation, logical deduction
- **Grok**: Large context analysis for complex systems
- **Gemini**: Pattern recognition, architectural insights

## Investigation Modes

- **low**: Quick investigation (8% thinking depth)
- **medium**: Standard problems (33% thinking depth)
- **high**: Complex issues (67% thinking depth) - DEFAULT
- **max**: Extremely complex challenges (100% thinking depth)

## Problem Types

Perfect for:
- Architecture decisions
- Complex bugs and race conditions
- Performance challenges
- Security analysis
- Integration problems
- System design questions

## Examples

```bash
# Complex debugging
/thinkdeep "Users report data inconsistency after deployments"

# Architecture analysis
/thinkdeep "Evaluate microservices migration strategy" model="gemini"

# Performance investigation
/thinkdeep "Database queries slow down after 1M records" model="o3"

# Security assessment
/thinkdeep "Analyze authentication flow for vulnerabilities" thinking_mode="max"
```

## Automatic Execution

/mcp__zen__thinkdeep "$ARGUMENTS" model="${MODEL:-claude}" thinking_mode="${MODE:-high}" use_websearch=true

---

**Deep Investigation**: Multi-stage analysis for your most complex technical challenges.