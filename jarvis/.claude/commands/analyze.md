# /analyze

---
allowed-tools: mcp__zen__analyze(*), mcp__zen__codereview(*), mcp__zen__secaudit(*), Task(*), Read(*), Bash(*), Glob(*), Grep(*), mcp__gemini__*, mcp__search-repo-docs__*, mcp__ask-repo-agent__*, mcp__genie_memory__*, mcp__send_whatsapp_message__*, mcp__wait__*
description: Unified analysis command supporting general analysis, multi-agent code review, and security/performance audits
---

Comprehensive analysis command that unifies general analysis, multi-agent code review, and specialized security/performance audits with intelligent mode selection.

## Auto-Loaded Project Context:
@/CLAUDE.md
@/docs/ai-context/project-structure.md
@/docs/ai-context/docs-overview.md

## Analysis Modes

### General Analysis (default)
```bash
# Default comprehensive analysis
/analyze "Review the authentication system architecture"
/analyze "Analyze database performance" model="o3"
```

### Multi-Agent Code Review
```bash
# Multi-expert code review (replaces /review)
/analyze "Latest commit for security issues" mode="review"
/analyze "agents/routing/handler.py for performance" mode="review"
/analyze "Authentication system implementation" mode="review"
```

### Security Audit
```bash
# Security-focused analysis (replaces /check security focus)
/analyze "Security audit of API endpoints" mode="security"
/analyze "User input validation" mode="security"
/analyze "Review authentication flow" mode="security"
```

### Performance Analysis
```bash
# Performance-focused analysis (replaces /check performance focus)
/analyze "Database queries" mode="performance"
/analyze "Payment processing bottlenecks" mode="performance"
/analyze "Memory usage in agent sessions" mode="performance"
```

### Quality Assessment
```bash
# Code quality analysis (replaces /check quality focus)
/analyze "Code quality in agents/" mode="quality"
/analyze "Maintainability review" mode="quality"
```

## Model Strengths

- **Claude** (default): Comprehensive analysis with project context
- **O3**: Logical analysis, systematic evaluation, code review
- **Grok**: Large context analysis (256K tokens), performance analysis
- **Gemini**: Architectural insights, security patterns, creative solutions

## Intelligent Mode Selection

The command automatically selects the optimal analysis approach:

### General Mode (default)
- Uses `mcp__zen__analyze` for architectural and code analysis
- Single-agent comprehensive assessment
- Best for: architecture review, design patterns, general insights

### Review Mode
- Uses multi-agent code review teams (from original `/review`)
- Deploys 3-6 specialized agents based on scope:
  - Security_Auditor, Performance_Analyzer, Quality_Inspector, Architecture_Reviewer
- Parallel execution for comprehensive coverage
- Best for: comprehensive code review, critical findings, production readiness

### Security Mode  
- Uses `mcp__zen__secaudit` for specialized security analysis
- OWASP Top 10 systematic analysis
- Compliance evaluation (SOC2, PCI DSS, etc.)
- Best for: vulnerability assessment, security compliance, threat modeling

### Performance Mode
- Uses `mcp__zen__analyze` with performance focus
- Bottleneck identification and optimization
- Resource utilization analysis
- Best for: performance optimization, scalability assessment

### Quality Mode
- Uses `mcp__zen__analyze` with quality focus
- Code smell detection and maintainability
- Design pattern compliance
- Best for: code quality improvement, technical debt assessment

## Enhanced Capabilities

### Expert Consultation & Notifications
```python
# Complex analysis with expert consultation
mcp__gemini__consult_gemini(
    specific_question="Analysis approach for [complex component]",
    problem_description="Need comprehensive analysis of [system]",
    code_context="System shows patterns like [examples]...",
    attached_files=["critical/files.py"],
    preferred_approach="review"
)

# Critical findings notifications
mcp__send_whatsapp_message__send_text_message(
    instance="SofIA",
    message="🚨 CRITICAL: Analysis found severe issues in [component]. Immediate attention required.",
    number="5511986780008@s.whatsapp.net"
)
```

### Memory Integration
```python
# Store analysis patterns
mcp__genie_memory__add_memory(
    content="PATTERN: Analysis [component] - Found [issues] using [approach] #analysis"
)

# Search for similar analysis patterns
mcp__genie_memory__search_memory(
    query="PATTERN analysis [similar component]"
)
```

## Migration from Previous Commands

**From `/review`**: Use `mode="review"` for multi-agent code review
**From `/check` security**: Use `mode="security"` for security audits  
**From `/check` performance**: Use `mode="performance"` for performance analysis
**From `/check` quality**: Use `mode="quality"` for code quality assessment

## Automatic Execution

```bash
# Parse mode and arguments
MODE="${MODE:-general}"
ANALYSIS_ARGS="$ARGUMENTS"

# Route to appropriate analysis based on mode
case "$MODE" in
    "review")
        # Multi-agent code review (from original /review)
        # Deploy specialized review agents in parallel
        ;;
    "security") 
        # Security audit (from original /check security)
        mcp__zen__secaudit "$ANALYSIS_ARGS" model="${MODEL:-claude}"
        ;;
    "performance"|"quality")
        # Performance or quality analysis (from original /check)
        mcp__zen__analyze "$ANALYSIS_ARGS" model="${MODEL:-claude}" analysis_type="$MODE"
        ;;
    *)
        # General analysis (original /analyze behavior)
        mcp__zen__analyze "$ANALYSIS_ARGS" model="${MODEL:-claude}" analysis_type="general"
        ;;
esac
```

---

**Unified Analysis**: One powerful command for all analysis needs - from quick assessments to comprehensive multi-agent reviews and specialized security audits.