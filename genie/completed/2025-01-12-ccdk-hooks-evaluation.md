# Active Task: CCDK Hook System Evaluation & Absorption

**Epic**: ccdk-integration  
**Status**: 📋 TODO  
**Priority**: HIGH  
**Agent**: Hook System Analyst  
**Mode**: ULTRATHINK

## Overview

Deep evaluation of the CCDK hook system (4 hook types + configuration) to determine which automation patterns, context injection mechanisms, and lifecycle integrations should be absorbed into our PagBank genie framework.

## Hook System Components to Evaluate

### 1. Subagent Context Injector (`subagent-context-injector.sh`)
**Purpose**: Automatic context injection for all Task tool calls
**Trigger**: PreToolUse for `Task` tool
**Complexity**: Medium - JSON manipulation with context prepending

**Key Features**:
- Intercepts ALL Task tool calls before execution
- Prepends references to core documentation:
  - `docs/CLAUDE.md` (project overview, coding standards)
  - `docs/ai-context/project-structure.md` (file tree, tech stack)
  - `docs/ai-context/docs-overview.md` (documentation architecture)
- Preserves original task prompt by prepending
- Token-efficient through @ references
- Pass-through for non-Task tools

**PagBank Relevance**: 🎯 **CRITICAL** - Essential for our multi-agent coordination

**Adaptation Needs**:
- Change paths: `docs/` → `genie/ai-context/`
- Add business unit context injection
- Include Portuguese language standards
- Add compliance rules reference

### 2. Gemini Context Injector (`gemini-context-injector.sh`)
**Purpose**: Automatic project context for Gemini consultations
**Trigger**: PreToolUse for `mcp__gemini__consult_gemini`
**Complexity**: High - Session detection, file attachment logic

**Key Features**:
- Detects new Gemini sessions (no session_id)
- Auto-attaches project documentation:
  - `docs/ai-context/project-structure.md` (complete project context)
  - `MCP-ASSISTANT-RULES.md` (project-specific coding standards)
- Session-aware (only new sessions)
- Graceful failure handling
- Comprehensive logging
- Preserves existing file attachments

**PagBank Relevance**: 🔥 **MEDIUM** - Useful but we primarily use search-repo/ask-repo

**Adaptation Considerations**:
- Do we need this for our MCP tools?
- Should we create similar for search-repo-docs/ask-repo-agent?
- Could be valuable for external consultations

### 3. MCP Security Scanner (`mcp-security-scan.sh`)
**Purpose**: Prevent credential exposure in MCP calls
**Trigger**: PreToolUse for all MCP tools (`mcp__.*`)
**Complexity**: High - Pattern matching, file scanning, configurable rules

**Key Features**:
- Pattern-based detection for API keys, passwords, secrets
- Scans code context, problem descriptions, attached files
- File content scanning with size limits
- Configurable via `config/sensitive-patterns.json`
- Whitelisting for placeholder values
- Command injection protection
- Comprehensive security event logging
- Blocking behavior (exit code 2)

**PagBank Relevance**: 🎯 **CRITICAL** - Essential for financial services compliance

**Adaptation Needs**:
- Add PagBank-specific sensitive patterns
- Include PII detection patterns
- Add financial data exposure patterns
- Include customer data protection rules

### 4. Notification System (`notify.sh`)
**Purpose**: Audio feedback for task completion and input needs
**Trigger**: Notification events, Stop events
**Complexity**: Low - Cross-platform audio playback

**Key Features**:
- Cross-platform audio support (macOS, Linux, Windows)
- Non-blocking background playback
- Multiple audio fallbacks
- Two notification types: `input`, `complete`
- Pleasant notification sounds
- Simple audio file management

**PagBank Relevance**: 🔥 **LOW** - Nice to have but not critical

**Adaptation Considerations**:
- Could be useful for long-running epic tasks
- Optional feature for developer experience
- Low priority for initial implementation

## Hook Architecture Analysis

### Claude Code Lifecycle Integration
```
Claude Code Lifecycle
        │
        ├── PreToolUse ──────► Security Scanner
        │                      ├── Context Injector (Gemini)
        │                      └── Context Injector (Subagents)
        │
        ├── Tool Execution
        │
        ├── PostToolUse
        │
        ├── Notification ────────► Audio Feedback
        │
        └── Stop/SubagentStop ───► Completion Sound
```

**Key Insights**:
- Deterministic execution at specific lifecycle points
- JSON input/output transformation capability
- Blocking capability for security enforcement
- Comprehensive logging for debugging

### Configuration Management
**Settings Structure**: `.claude/settings.json`
```json
{
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...], 
    "Notification": [...],
    "Stop": [...]
  }
}
```

**Key Features**:
- Matcher patterns for tool targeting
- Command execution with workspace variables
- Multiple hooks per lifecycle event
- Flexible hook chaining

## Evaluation Criteria

### Critical for PagBank
- **Security Compliance**: Does it protect sensitive financial data?
- **Context Consistency**: Does it ensure consistent multi-agent knowledge?
- **Business Rule Enforcement**: Can it enforce PagBank-specific rules?
- **Compliance Logging**: Does it provide audit trails?

### Technical Integration
- **Genie Compatibility**: How does it work with our kanban framework?
- **Performance Impact**: Execution time and resource usage?
- **Maintenance Complexity**: Configuration and update requirements?
- **Error Handling**: Graceful failure and recovery?

### Development Experience
- **Automation Value**: Does it reduce manual overhead?
- **Developer Friction**: Does it interfere with workflows?
- **Debugging Support**: Can issues be easily diagnosed?
- **Customization Flexibility**: Can it be adapted for our needs?

## Decision Points for Discussion

### Priority 1: Essential Hooks (Critical)
**Hooks**: Subagent Context Injector, MCP Security Scanner

**Questions for Discussion**:
1. Should we implement subagent context injection for our multi-agent coordination?
2. How should we adapt security scanning for PagBank financial data protection?
3. What PagBank-specific patterns should we add to security scanning?
4. Should we inject business unit context automatically?

### Priority 2: Useful Hooks (Medium Value)
**Hooks**: Gemini Context Injector

**Questions for Discussion**:
1. Do we need automatic context injection for our MCP tools (search-repo, ask-repo)?
2. Should we create similar hooks for external AI consultations?
3. Is this valuable for our Agno documentation queries?

### Priority 3: Optional Hooks (Low Value)
**Hooks**: Notification System

**Questions for Discussion**:
1. Would audio feedback be useful for long-running epic tasks?
2. Should this be an optional developer experience feature?
3. Is this worth the implementation and maintenance effort?

## Adaptation Strategy

### Phase 1: Critical Security and Context
```bash
.claude/hooks/
├── genie-context-injector.sh       # Adapted subagent context injector
├── pagbank-security-scan.sh        # Adapted MCP security scanner
└── config/
    └── pagbank-sensitive-patterns.json  # PagBank-specific patterns
```

**Genie Context Injector Features**:
- Auto-inject genie/ai-context/ files for all Task calls
- Include business unit context
- Add Portuguese language standards
- Include compliance rules reference

**PagBank Security Scanner Features**:
- Financial data pattern detection
- PII exposure prevention
- Customer data protection
- Audit logging for compliance

### Phase 2: Enhanced MCP Integration
```bash
.claude/hooks/
├── agno-context-injector.sh        # For search-repo/ask-repo calls
└── external-ai-injector.sh         # For external consultations
```

### Phase 3: Developer Experience
```bash
.claude/hooks/
├── notify.sh                       # Cross-platform notifications
└── sounds/                         # Notification audio files
```

## Implementation Details

### Genie Context Injector Adaptation
```bash
# Auto-inject for every Task call:
@genie/ai-context/project-structure.md    # Complete PagBank tech stack
@genie/ai-context/business-units.md       # Business domain context
@genie/ai-context/compliance-rules.md     # Financial services compliance
@genie/ai-context/portuguese-standards.md # PT-BR language requirements
@CLAUDE.md                                # Master project context
```

### PagBank Security Patterns
```json
{
  "sensitive_patterns": [
    "cpf\\s*[:=]\\s*[0-9]{3}\\.?[0-9]{3}\\.?[0-9]{3}-?[0-9]{2}",
    "cnpj\\s*[:=]\\s*[0-9]{2}\\.?[0-9]{3}\\.?[0-9]{3}/?[0-9]{4}-?[0-9]{2}",
    "pix\\s*key\\s*[:=]",
    "account\\s*number\\s*[:=]",
    "customer\\s*id\\s*[:=]",
    "auth\\s*token\\s*[:=]",
    "api\\s*key\\s*[:=]"
  ],
  "pii_patterns": [
    "nome\\s*completo\\s*[:=]",
    "endereco\\s*[:=]",
    "telefone\\s*[:=]",
    "email\\s*[:=].*@.*\\."
  ]
}
```

### Configuration Template
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "${WORKSPACE}/.claude/hooks/genie-context-injector.sh"
          }
        ]
      },
      {
        "matcher": "mcp__.*",
        "hooks": [
          {
            "type": "command", 
            "command": "${WORKSPACE}/.claude/hooks/pagbank-security-scan.sh"
          }
        ]
      }
    ]
  }
}
```

## Testing Strategy

### Hook Functionality Testing
- Test context injection with various Task scenarios
- Validate security scanning with sensitive data patterns
- Test graceful failure with missing files
- Verify performance impact on tool execution

### PagBank-Specific Testing
- Test business unit context injection
- Validate Portuguese language standard injection
- Test compliance rule reference injection
- Verify financial data pattern detection

### Integration Testing
- Test with existing genie kanban workflow
- Validate with multi-agent coordination scenarios
- Test with actual PagBank business scenarios
- Verify compatibility with existing tooling

## Next Steps

1. **Stakeholder Review** - Discuss priorities and security requirements
2. **Security Pattern Definition** - Define PagBank-specific sensitive patterns
3. **Context Structure Design** - Design genie/ai-context/ file structure
4. **Implementation Planning** - Create detailed implementation roadmap
5. **Testing Framework** - Design comprehensive testing approach

---

**Status**: Ready for stakeholder review and security pattern discussion
**Dependencies**: Completion of genie/ai-context/ structure design
**Blockers**: Need stakeholder input on security requirements and implementation priorities