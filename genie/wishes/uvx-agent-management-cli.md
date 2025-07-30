# WISH 2: UVX Agent Management CLI

## 🎯 Wish Summary
Replace current make-based agent commands with UVX-native CLI commands that provide seamless agent lifecycle management in UV environments.

## 🧞‍♂️ User's Original Request  
"as we will start using uvx for starting instances, the agent could start their own instance using uvx automagik-hive --agent-serve and uvx automagik-hive --agent-logs to replace current make agent and make logs behavior, for uvx environment"

## ✨ Detailed Wish Specification

### Command Mapping Transformation
```bash
# OLD MAKE COMMANDS → NEW UVX COMMANDS
make agent         → uvx automagik-hive --agent-serve
make agent-logs    → uvx automagik-hive --agent-logs  
make agent-status  → uvx automagik-hive --agent-status
make agent-stop    → uvx automagik-hive --agent-stop
make agent-restart → uvx automagik-hive --agent-restart
```

### Technical Requirements

#### 1. UVX Agent Serve (`--agent-serve`)
**Purpose**: Start agent development server (replaces `make agent`)
```bash
uvx automagik-hive --agent-serve

# Features:
- Starts on port 38886 (agent development port)
- Background process with PID tracking
- Progress indicators during startup
- Environment detection and validation
- Clean error messages for issues
```

#### 2. UVX Agent Logs (`--agent-logs`)  
**Purpose**: Real-time log streaming (replaces `make agent-logs`)
```bash
uvx automagik-hive --agent-logs

# Features:
- Non-blocking terminal return
- Real-time log streaming
- Historical log access
- Log filtering options
- Clean formatting and colors
```

#### 3. UVX Agent Status (`--agent-status`)
**Purpose**: Health check and status reporting
```bash
uvx automagik-hive --agent-status

# Output:
✅ Agent server running (PID: 12345)
🌐 Accessible at: http://localhost:38886
📊 Database: Connected (postgresql://localhost:35532)
🧞‍♂️ Genie: Ready for wishes
```

#### 4. UVX Agent Stop (`--agent-stop`)
**Purpose**: Graceful shutdown with cleanup
```bash
uvx automagik-hive --agent-stop

# Features:
- Graceful server shutdown
- PID file cleanup
- Connection draining
- Status confirmation
```

#### 5. UVX Agent Restart (`--agent-restart`)
**Purpose**: Clean restart sequence
```bash
uvx automagik-hive --agent-restart

# Features:
- Stop existing server
- Clean environment reset
- Fresh server start
- Status verification
```

## 🔧 Implementation Architecture

### CLI Argument Structure
```python
# Main entry point parsing
def main():
    if args.agent_serve:
        return agent_serve()
    elif args.agent_logs:
        return agent_logs()
    elif args.agent_status:
        return agent_status()
    # ... etc
```

### Process Management Strategy
```python
# PID file management
PID_FILE = ".hive/agent.pid"

def agent_serve():
    # Check if already running
    # Start server in background
    # Write PID file
    # Show startup progress
    
def agent_stop():
    # Read PID file
    # Send graceful shutdown signal
    # Clean up PID file
    # Confirm shutdown
```

### Environment Integration
```python
# UV environment detection
def detect_uv_environment():
    # Check for UV installation
    # Validate Python version
    # Verify dependencies
    # Configure environment variables
```

## 🎯 Success Criteria
- [ ] All 5 commands work seamlessly in UV environments
- [ ] `--agent-serve` starts development server on 38886
- [ ] `--agent-logs` shows real-time, formatted logs
- [ ] `--agent-status` reports accurate health information
- [ ] `--agent-stop` performs clean shutdown
- [ ] `--agent-restart` does clean restart cycle
- [ ] Cross-platform compatibility (Linux, macOS, Windows/WSL)
- [ ] Proper error handling with helpful messages
- [ ] Background processes don't block terminal

## 🚨 Critical Design Decisions Needed

### 1. Process Management Approach
**Question**: How should we handle background processes?
**Options**:
- A) Use subprocess with daemon mode
- B) Use systemd/launchd integration
- C) Custom process manager with PID files

### 2. Log Management Strategy
**Question**: How should logs be handled?
**Current thinking**:
- Real-time streaming via file watching
- Structured logging with JSON format
- Configurable log levels and filtering
- Automatic log rotation

### 3. Environment Configuration
**Question**: How should UV environments be detected?
**Options**:
- A) Automatic detection with fallbacks
- B) Explicit environment specification
- C) Configuration file approach

### 4. Error Recovery Patterns
**Question**: How should we handle common issues?
**Scenarios**:
- Port already in use
- Database connection failures  
- Permission issues
- UV environment problems

## 🔄 Integration with Current System

### Database Connectivity
- Maintain connection to PostgreSQL on port 35532
- Preserve existing agent environment variables
- Support both development and production modes

### Agent Framework Integration
- Load existing .claude/agents/* structure
- Maintain compatibility with current agent patterns
- Support hot reload and dynamic loading

### MCP Tools Integration
- Preserve all current MCP tool connections
- Maintain automagik-forge integration
- Support external tool ecosystem

## 🤔 Questions for User Enhancement

1. **Command Naming**: Do you prefer the proposed `--agent-*` pattern or different naming?

2. **Process Management**: Should we support multiple concurrent agent servers or enforce single instance?

3. **Log Output**: What level of log detail do you want by default?
   - Minimal (errors + status)
   - Standard (info + warnings) 
   - Verbose (debug + trace)

4. **Configuration**: Should agent server settings be:
   - Command line arguments?
   - Configuration file?
   - Environment variables?
   - All of the above?

5. **Development Workflow**: Should `--agent-serve` automatically:
   - Watch for code changes and restart?
   - Show startup logs then return terminal?
   - Stay attached until manual stop?

## 🎮 Developer Experience Goals

### Seamless Transition
- Developers can switch from `make` to `uvx` commands
- All functionality preserved and enhanced
- Improved error messages and feedback

### UV Environment Native
- Works perfectly in UV-managed Python environments
- Automatic dependency resolution
- No conflicts with system Python

### Enhanced Productivity
- Faster startup times
- Better process management
- Cleaner development workflow

**Ready for your enhancement and validation!** 🧞‍♂️✨