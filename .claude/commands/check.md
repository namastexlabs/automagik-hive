# /check

---
allowed-tools: Task(*), Read(*), Bash(*), Glob(*), Grep(*), mcp__gemini__*, mcp__search-repo-docs__*, mcp__ask-repo-agent__*, mcp__genie_memory__*, mcp__send_whatsapp_message__*, mcp__wait__*
description: Analyze code quality, security, and performance
---

Comprehensive analysis of code quality, security vulnerabilities, and performance issues with expert consultation.

## Auto-Loaded Project Context:
@/CLAUDE.md
@/docs/ai-context/project-structure.md
@/docs/ai-context/docs-overview.md

## Usage

```bash
# Quick health check
/check "Review authentication system"
/check "Security audit of API endpoints"
/check "Performance analysis of payment flow"

# With specific focus
/check "Database queries" type="performance"
/check "User input validation" type="security"
/check "Code quality in agents/" type="quality"
```

## Intelligent Analysis Strategy

### Step 1: Analysis Classification
Parse user request: "$ARGUMENTS"

**Analysis Categories:**
- **Security Focus** → Vulnerability scanning and security review
- **Performance Focus** → Bottleneck identification and optimization
- **Quality Focus** → Code smells, maintainability, patterns
- **Comprehensive** → Multi-perspective analysis

### Step 2: Progressive Analysis Strategy

**Level 1: Direct Analysis** (Simple, focused checks)
- Single-area analysis (security OR performance OR quality)
- Clear scope and obvious patterns
- Quick automated checks

**Level 2: Focused Investigation** (Moderate complexity)
- Deploy 1-2 specialized analysis agents
- Deep dive into specific concerns
- Pattern and anti-pattern detection

**Level 3: Multi-Perspective Analysis** (Complex systems)
- Deploy 3-4 specialized analysis agents:
  - **Security_Auditor**: Vulnerability assessment and threat analysis
  - **Performance_Analyzer**: Bottleneck identification and optimization
  - **Quality_Inspector**: Code maintainability and patterns
  - **Architecture_Reviewer**: System design and scalability

**Level 4: Expert Consultation** (Critical/complex analysis)
- Use Gemini for complex security or architectural assessment
- Research latest security practices and performance patterns
- Cross-reference with industry standards

### Step 3: Analysis Execution

**For Sub-Agent Approach:**
```
Task: "Analyze [COMPONENT] for [FOCUS_AREA] issues related to user request '$ARGUMENTS'"

Standard Analysis Workflow:
1. Review auto-loaded project context (CLAUDE.md, project-structure.md, docs-overview.md)
2. Examine code for [FOCUS_AREA] concerns (security/performance/quality)
3. Identify patterns, anti-patterns, and potential issues
4. Assess impact and severity of findings
5. Research best practices and solutions
6. Return actionable analysis findings with severity ratings
```

**CRITICAL: Launch all analysis agents in parallel using single message with multiple Task invocations.**

### Step 4: Analysis Areas

**Security Analysis:**
- Input validation and sanitization
- Authentication and authorization flows
- Data exposure and privacy concerns
- Injection vulnerabilities (SQL, XSS, etc.)
- Secrets management and exposure
- API security and rate limiting

**Performance Analysis:**
- Algorithmic complexity and bottlenecks
- Database query optimization
- Memory usage and leak detection
- Network I/O and caching opportunities
- Async/await patterns and concurrency
- Resource utilization and scaling

**Quality Analysis:**
- Code duplication and reusability
- Function and class complexity
- Naming conventions and clarity
- Error handling patterns
- Documentation and type hints
- Test coverage and testability

### Step 5: Expert Consultation & Notifications

For complex findings, leverage expert consultation:

```python
# Complex security assessment
mcp__gemini__consult_gemini(
    specific_question="Security analysis of [complex component]",
    problem_description="Found potential vulnerabilities in [area]",
    code_context="Code shows patterns like [examples]...",
    attached_files=["security/critical/files.py"],
    preferred_approach="review"
)

# Performance optimization research
mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/context7/agno",
    topic="Performance best practices",
    tokens=10000
)

# Repository-specific patterns
mcp__ask-repo-agent__ask_question(
    repoName="agno-agi/agno",
    question="What are the recommended patterns for [specific concern]?"
)
```

**WhatsApp Notifications for Critical Findings:**
```python
# Notify about critical security issues
mcp__send_whatsapp_message__send_text_message(
    instance="SofIA",
    message="🚨 CRITICAL: Security vulnerability found in [component]. Immediate attention required.",
    number="5511986780008@s.whatsapp.net"
)

# Notify about significant performance issues
mcp__send_whatsapp_message__send_text_message(
    instance="SofIA", 
    message="⚠️ PERFORMANCE: Major bottleneck detected in [component]. Could impact user experience.",
    number="5511986780008@s.whatsapp.net"
)
```

## Analysis Methodology

### 1. Automated Scanning
- **Pattern detection** - Find known anti-patterns
- **Static analysis** - Code quality metrics
- **Dependency check** - Vulnerable packages
- **Configuration review** - Security settings

### 2. Manual Review
- **Logic flow analysis** - Business logic flaws
- **Integration points** - Cross-system vulnerabilities
- **Error handling** - Failure mode analysis
- **Data flow** - Privacy and security implications

### 3. Performance Profiling
- **Execution paths** - Hot spots and bottlenecks
- **Resource usage** - Memory, CPU, I/O patterns
- **Concurrency** - Race conditions and deadlocks
- **Scalability** - Load handling and limits

### 4. Quality Assessment
- **Maintainability** - Code complexity and clarity
- **Extensibility** - Design patterns and flexibility
- **Testability** - Unit test coverage and design
- **Documentation** - Code clarity and comments

## Output Format

```markdown
# Code Analysis Report: [Component/System]

## Executive Summary
- **Overall Risk Level**: [Critical/High/Medium/Low]
- **Key Findings**: [2-3 most important issues]
- **Recommended Actions**: [Priority fixes]

## Security Assessment
### 🚨 Critical Issues
- [Issue with immediate security impact]

### ⚠️ Security Concerns  
- [Issues requiring attention]

### ✅ Security Strengths
- [Well-implemented security measures]

## Performance Analysis
### ⚡ Performance Issues
- [Bottlenecks and optimization opportunities]

### 📈 Performance Metrics
- [Current performance characteristics]

## Quality Review
### 🔧 Code Quality Issues
- [Maintainability and design concerns]

### 💡 Improvement Opportunities
- [Refactoring and enhancement suggestions]

## Recommendations
1. **Immediate Actions** (Fix within 24 hours)
2. **Short-term Improvements** (Fix within 1 week)  
3. **Long-term Enhancements** (Plan for next sprint)

## Memory Updates
- [Security patterns stored]
- [Performance insights saved]
- [Quality improvements documented]

## Expert Consultation Summary
[Key insights from Gemini/documentation research]
```

## Automatic Memory Integration

Every analysis automatically updates memory:

```python
# Store security findings
mcp__genie_memory__add_memory(
    content="FOUND: Security issue [type] in [component] - Fixed with [solution] #security"
)

# Store performance patterns
mcp__genie_memory__add_memory(
    content="PATTERN: Performance - [bottleneck] optimized with [approach] #performance"
)

# Search for known issues before analysis
mcp__genie_memory__search_memory(
    query="FOUND security [component]"
)

# Progressive analysis workflow
mcp__wait__wait_minutes(
    minutes=0.25,
    message="Analyzing dependencies for security vulnerabilities..."
)

# Send security report summary
mcp__send_whatsapp_message__send_media(
    instance="SofIA",
    media="[base64_security_report_image]",
    mediatype="image",
    mimetype="image/png",
    caption="🛡️ Security Analysis Complete: [Component] - [Risk Level]"
)
```

## Automatic Execution

```bash
# Search memory for known issues
mcp__genie_memory__search_memory query="FOUND security performance $ARGUMENTS"

# For security-focused checks
if [[ "$ARGUMENTS" =~ security|auth|input|validation|vulnerability ]]; then
    mcp__gemini__consult_gemini \
        specific_question="Security analysis of: $ARGUMENTS" \
        problem_description="Need security assessment in genie-agents" \
        preferred_approach="review"
    
    # Immediate notification for security concerns
    mcp__send_whatsapp_message__send_text_message \
        instance="SofIA" \
        message="🔒 SECURITY CHECK: Analyzing $ARGUMENTS" \
        number="5511986780008@s.whatsapp.net"
fi

# Research best practices
mcp__search-repo-docs__get-library-docs \
    context7CompatibleLibraryID="/context7/agno" \
    topic="Security and performance best practices" \
    tokens=8000
```

---

**Comprehensive Analysis**: Multi-expert assessment with real-time notifications for critical findings.