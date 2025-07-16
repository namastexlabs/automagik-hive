# Claude Code Hooks

This directory contains battle-tested hooks that enhance your Claude Code development experience with automated security scanning, intelligent context injection, and pleasant audio feedback.

## Architecture

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

These hooks execute at specific points in Claude Code's lifecycle, providing deterministic control over AI behavior.

## Available Hooks

### 1. Gemini Context Injector (`gemini-context-injector.sh`)

**Purpose**: Automatically includes your project documentation and assistant rules when starting new Gemini consultation sessions, ensuring the AI has complete context about your codebase and project standards.

**Trigger**: `PreToolUse` for `mcp__gemini__consult_gemini`

**Features**:
- Detects new Gemini consultation sessions (no session_id)
- Automatically attaches two key files:
  - `docs/ai-context/project-structure.md` - Complete project structure and tech stack
  - `MCP-ASSISTANT-RULES.md` - Project-specific coding standards and guidelines
- Preserves existing file attachments
- Session-aware (only injects on new sessions)
- Logs all injection events for debugging
- Fails gracefully if either file is missing
- Handles partial availability (will attach whichever files exist)

**Customization**: 
- Copy `docs/MCP-ASSISTANT-RULES.md` template to your project root
- Customize it with your project-specific standards, principles, and constraints
- The hook will automatically include it in Gemini consultations

### 2. MCP Security Scanner (`mcp-security-scan.sh`)

**Purpose**: Prevents accidental exposure of secrets, API keys, and sensitive data when using MCP servers like Gemini or Context7.

**Trigger**: `PreToolUse` for all MCP tools (`mcp__.*`)

**Features**:
- Pattern-based detection for API keys, passwords, and secrets
- Scans code context, problem descriptions, and attached files
- File content scanning with size limits
- Configurable pattern matching via `config/sensitive-patterns.json`
- Whitelisting for placeholder values
- Command injection protection for Context7
- Comprehensive logging of security events to `.claude/logs/`

**Customization**: Edit `config/sensitive-patterns.json` to:
- Add custom API key patterns
- Modify credential detection rules
- Update sensitive file patterns
- Extend the whitelist for your placeholders

### 3. Subagent Context Injector (`subagent-context-injector.sh`)

**Purpose**: Automatically includes core project documentation in all sub-agent Task prompts, ensuring consistent context across multi-agent workflows.

**Trigger**: `PreToolUse` for `Task` tool

**Features**:
- Intercepts all Task tool calls before execution
- Prepends references to three core documentation files:
  - `docs/CLAUDE.md` - Project overview, coding standards, AI instructions
  - `docs/ai-context/project-structure.md` - Complete file tree and tech stack
  - `docs/ai-context/docs-overview.md` - Documentation architecture
- Passes through non-Task tools unchanged
- Preserves original task prompt by prepending context
- Enables consistent knowledge across all sub-agents
- Eliminates need for manual context inclusion in Task prompts

**Benefits**:
- Every sub-agent starts with the same foundational knowledge
- No manual context specification needed in each Task prompt
- Token-efficient through @ references instead of content duplication
- Update context in one place, affects all sub-agents
- Clean operation with simple pass-through for non-Task tools

### 4. Notification System (`notify.sh`)

**Purpose**: Provides pleasant audio feedback when Claude Code needs your attention or completes tasks.

**Triggers**: 
- `Notification` events (all notifications including input needed)
- `Stop` events (main task completion)

**Features**:
- Cross-platform audio support (macOS, Linux, Windows)
- Non-blocking audio playback (runs in background)
- Multiple audio playback fallbacks
- Pleasant notification sounds
- Two notification types:
  - `input`: When Claude needs user input
  - `complete`: When Claude completes tasks

## Command-Specific Hooks

### 5. Fix Context Injector (`fix-context-injector.sh`)

**Purpose**: Enhances `/fix` command usage with intelligent debugging context and guidance.

**Trigger**: `PreCommand` for `/fix.*` commands

**Features**:
- Automatic issue classification (performance, API, database, concurrency, agent-specific)
- Context-aware debugging strategy recommendations
- Intelligent keyword analysis for targeted guidance
- Memory search suggestions based on issue type
- Expert consultation triggers for complex scenarios
- Structured debugging methodology injection

**Example Enhancement**:
```bash
# Input: /fix "API returns 500 error"
# Enhanced with: API integration context, error handling guidance, debugging strategy
```

### 6. Build Planner (`build-planner.sh`)

**Purpose**: Enhances `/build` command usage with implementation planning and architecture guidance.

**Trigger**: `PreCommand` for `/build.*` commands

**Features**:
- Complexity analysis (LOW/MEDIUM/HIGH) with strategy recommendations
- Project pattern identification (Agent V2, FastAPI, SQLAlchemy, etc.)
- Implementation strategy guidance (direct, pattern-analysis, multi-agent)
- Architecture considerations specific to Genie Agents V2
- Memory search patterns for similar implementations
- Expert consultation triggers for complex features

**Strategy Levels**:
- **Direct Implementation**: Simple functions and utilities
- **Pattern Analysis**: API endpoints and moderate complexity features
- **Multi-Agent Design**: Complex systems and architecture decisions

### 7. Nuke Checkpoint (`nuke-checkpoint.sh`)

**Purpose**: Enhances `/nuke` command usage with automatic git checkpoint management and recovery.

**Trigger**: `PreCommand` for `/nuke.*` commands

**Features**:
- Automatic git checkpoint creation before nuclear debugging
- Timestamp-based checkpoint IDs for easy tracking
- Checkpoint metadata storage (issue, timestamp, commit hash, branch)
- Recovery instructions and rollback guidance
- Audit trail logging for all checkpoint operations
- Emergency recovery procedures for critical issues

**Safety Features**:
- Git tag creation for stable rollback points
- JSON-based checkpoint tracking
- Detailed recovery instructions
- Audit logging for debugging sessions

### 8. Command Memory (`command-memory.sh`)

**Purpose**: Automatically tags memory entries with command context for better organization and searchability.

**Trigger**: `PreToolUse` for `mcp__genie-memory__add_memories`

**Features**:
- Command context detection (fix, build, nuke, debug, analyze)
- Content type classification (solution, pattern, issue, task, nuclear, etc.)
- Automatic tag generation based on content keywords
- Structured memory enhancement with prefixes
- Temporal tagging for time-based organization
- Context-aware memory categorization

**Tag Categories**:
- **Command Tags**: `#fix`, `#build`, `#nuke`, `#debug`, `#analyze`
- **Content Tags**: `#solution`, `#pattern`, `#issue`, `#nuclear`, `#api`, `#agent`
- **Context Tags**: `#performance`, `#security`, `#integration`, `#testing`
- **Temporal Tags**: `#2025-07` (year-month format)

## Installation

1. **Copy the hooks to your project**:
   ```bash
   cp -r hooks your-project/.claude/
   ```

2. **Configure hooks in your project**:
   ```bash
   cp hooks/setup/settings.json.template your-project/.claude/settings.json
   ```
   Then edit the WORKSPACE path in the settings file.

3. **Test the hooks**:
   ```bash
   # Test notification
   .claude/hooks/notify.sh input
   .claude/hooks/notify.sh complete
   
   # Test command-specific hooks
   .claude/hooks/test-command-hooks.sh
   
   # Test individual hooks
   echo '{"message": "/fix test issue"}' | .claude/hooks/fix-context-injector.sh
   echo '{"message": "/build test feature"}' | .claude/hooks/build-planner.sh
   echo '{"message": "/nuke test bug"}' | .claude/hooks/nuke-checkpoint.sh
   
   # View logs
   tail -f .claude/logs/context-injection.log
   tail -f .claude/logs/security-scan.log
   tail -f .claude/logs/fix-context-injection.log
   tail -f .claude/logs/build-planning.log
   tail -f .claude/logs/nuke-checkpoint.log
   tail -f .claude/logs/command-memory.log
   ```

## Hook Configuration

Add to your Claude Code `settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__gemini__consult_gemini",
        "hooks": [
          {
            "type": "command",
            "command": "${WORKSPACE}/.claude/hooks/gemini-context-injector.sh"
          }
        ]
      },
      {
        "matcher": "mcp__.*",
        "hooks": [
          {
            "type": "command",
            "command": "${WORKSPACE}/.claude/hooks/mcp-security-scan.sh"
          }
        ]
      },
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "${WORKSPACE}/.claude/hooks/subagent-context-injector.sh"
          }
        ]
      },
      {
        "matcher": "mcp__genie-memory__add_memories",
        "hooks": [
          {
            "type": "command",
            "command": "${WORKSPACE}/.claude/hooks/command-memory.sh"
          }
        ]
      }
    ],
    "PreCommand": [
      {
        "matcher": "/fix.*",
        "hooks": [
          {
            "type": "command",
            "command": "${WORKSPACE}/.claude/hooks/fix-context-injector.sh"
          }
        ]
      },
      {
        "matcher": "/build.*",
        "hooks": [
          {
            "type": "command",
            "command": "${WORKSPACE}/.claude/hooks/build-planner.sh"
          }
        ]
      },
      {
        "matcher": "/nuke.*",
        "hooks": [
          {
            "type": "command",
            "command": "${WORKSPACE}/.claude/hooks/nuke-checkpoint.sh"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "${WORKSPACE}/.claude/hooks/notify.sh input"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "${WORKSPACE}/.claude/hooks/notify.sh complete"
          }
        ]
      }
    ]
  }
}
```

See `hooks/setup/settings.json.template` for the complete configuration including all hooks and MCP servers.

## Security Model

1. **Execution Context**: Hooks run with full user permissions
2. **Blocking Behavior**: Exit code 2 blocks tool execution
3. **Data Flow**: Hooks can modify tool inputs via JSON transformation
4. **Isolation**: Each hook runs in its own process
5. **Logging**: All security events logged to `.claude/logs/`

## Integration with MCP Servers

The hooks system complements MCP server integrations:

- **Gemini Consultation**: Context injector ensures both project structure and MCP assistant rules are included
- **Context7 Documentation**: Security scanner protects library ID inputs
- **All MCP Tools**: Universal security scanning before external calls

## Best Practices

1. **Hook Design**:
   - Fail gracefully - never break the main workflow
   - Log important events for debugging
   - Use exit codes appropriately (0=success, 2=block)
   - Keep execution time minimal

2. **Security**:
   - Regularly update sensitive patterns
   - Review security logs periodically
   - Test hooks in safe environments first
   - Never log sensitive data in hooks

3. **Configuration**:
   - Use `${WORKSPACE}` variable for portability
   - Keep hooks executable (`chmod +x`)
   - Version control hook configurations
   - Document custom modifications

## Troubleshooting

### Hooks not executing
- Check file permissions: `chmod +x *.sh`
- Verify paths in settings.json
- Check Claude Code logs for errors

### Security scanner too restrictive
- Review patterns in `config/sensitive-patterns.json`
- Add legitimate patterns to the whitelist
- Check logs for what triggered the block

### No sound playing
- Verify sound files exist in `sounds/` directory
- Test audio playback: `.claude/hooks/notify.sh input`
- Check system audio settings
- Ensure you have an audio player installed (afplay, paplay, aplay, pw-play, play, ffplay, or PowerShell on Windows)

## Hook Setup Command

For comprehensive setup verification and testing, use:

```
/hook-setup
```

This command uses multi-agent orchestration to verify installation, check configuration, and run comprehensive tests. See [hook-setup.md](setup/hook-setup.md) for details.

## Extension Points

The kit is designed for extensibility:

1. **Custom Hooks**: Add new scripts following the existing patterns
2. **Event Handlers**: Configure hooks for any Claude Code event
3. **Pattern Updates**: Modify security patterns for your needs
4. **Sound Customization**: Replace audio files with your preferences