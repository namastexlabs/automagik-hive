# 🧞 UVX AGENT MANAGEMENT - COMPLETE REPLACEMENT WISH

**🎯 ULTIMATE GOAL**: Replace `make agent` entirely with `uvx automagik-hive --agent-*` commands through systematic agent spawning until 100% completion including testing, QA, and alpha publishing.

---

## 🎯 **WISH COMPLETION CRITERIA**

### **✅ SUCCESS DEFINITION**
You are able to fully manage your own agent instance via UVX commands and completely replace the current `make agent` functionality:

```bash
# NEW: Full UVX agent management (replaces make agent)
uvx automagik-hive --agent-install   # Replace: make install-agent
uvx automagik-hive --agent-serve     # Replace: make agent  
uvx automagik-hive --agent-logs      # Replace: make agent-logs
uvx automagik-hive --agent-status    # Replace: make agent-status
uvx automagik-hive --agent-stop      # Replace: make agent-stop
uvx automagik-hive --agent-restart   # Replace: make agent-restart
uvx automagik-hive --agent-reset     # Replace: make agent-reset (new)

# VALIDATION: All commands work identically to make equivalents
# BACKWARDS COMPATIBILITY: make commands preserved during transition
```

### **🏆 FINAL VALIDATION**
- **Agent Environment**: Complete isolated agent dev environment (ports 38886/35532)
- **Container Management**: Full Docker container lifecycle management
- **Data Persistence**: `./data/` directory management with permissions
- **Environment Files**: `.env.agent` generation and management
- **Testing**: Comprehensive test coverage for all agent commands
- **QA**: Code quality validation (ruff, mypy, pytest)
- **Publishing**: New alpha version released with agent management
- **Documentation**: Updated README and help documentation

---

## 🏭 **SYSTEMATIC AGENT SPAWNING SEQUENCE**

### **🚀 EXECUTION PROTOCOL**
**Keep spawning agents until wish is 100% complete** - do not stop until all validation criteria are met.

### **Phase 2A: Foundation Tasks** (Build from Phase 1)
```python
# PARALLEL EXECUTION BLOCK 1: Foundation
Task(subagent_type="genie-dev-planner", prompt="Analyze current agent management requirements and create technical specification for complete `make agent` replacement")
Task(subagent_type="genie-dev-designer", prompt="Design agent command architecture for --agent-* CLI commands with container orchestration")

# SEQUENTIAL EXECUTION: Implementation  
Task(subagent_type="genie-dev-coder", prompt="Implement cli/commands/agent.py with complete --agent-* command suite")
```

### **Phase 2B: Core Implementation** (Container Management)
```python
# PARALLEL EXECUTION BLOCK 2: Container Systems
Task(subagent_type="genie-dev-coder", prompt="Implement agent container lifecycle management in cli/core/agent_service.py")
Task(subagent_type="genie-dev-coder", prompt="Implement agent environment management (.env.agent generation) in cli/core/agent_environment.py")
Task(subagent_type="genie-dev-coder", prompt="Implement agent data directory management with permission handling")

# INTEGRATION
Task(subagent_type="genie-dev-coder", prompt="Integrate agent commands with existing CLI foundation and PostgreSQL service")
```

### **Phase 2C: Feature Completion** (Full Parity)
```python
# PARALLEL EXECUTION BLOCK 3: Feature Parity
Task(subagent_type="genie-dev-coder", prompt="Implement --agent-install command (equivalent to make install-agent)")
Task(subagent_type="genie-dev-coder", prompt="Implement --agent-serve command (equivalent to make agent)")  
Task(subagent_type="genie-dev-coder", prompt="Implement --agent-logs command (equivalent to make agent-logs)")
Task(subagent_type="genie-dev-coder", prompt="Implement --agent-status command (equivalent to make agent-status)")
Task(subagent_type="genie-dev-coder", prompt="Implement --agent-stop command (equivalent to make agent-stop)")
Task(subagent_type="genie-dev-coder", prompt="Implement --agent-restart command (equivalent to make agent-restart)")
Task(subagent_type="genie-dev-coder", prompt="Implement --agent-reset command (new functionality)")
```

### **Phase 2D: Testing & Quality** (Comprehensive Validation)
```python
# PARALLEL EXECUTION BLOCK 4: Quality Assurance
Task(subagent_type="genie-testing-maker", prompt="Create comprehensive test suite for all --agent-* commands")
Task(subagent_type="genie-quality-ruff", prompt="Apply ruff formatting and linting to all agent management code")
Task(subagent_type="genie-quality-mypy", prompt="Apply mypy type checking to all agent management code")

# TESTING VALIDATION
Task(subagent_type="genie-testing-fixer", prompt="Fix all failing tests and ensure 100% agent command test coverage")
Task(subagent_type="genie-dev-fixer", prompt="Fix any bugs discovered during testing and validation")
```

### **Phase 2E: Integration & Validation** (End-to-End)
```python
# SEQUENTIAL EXECUTION: Integration Testing
Task(subagent_type="genie-dev-coder", prompt="Implement end-to-end integration tests comparing make vs uvx agent commands")
Task(subagent_type="genie-dev-fixer", prompt="Resolve any integration issues and ensure perfect make command parity")

# DOCUMENTATION & HELP
Task(subagent_type="genie-claudemd", prompt="Update all documentation to reflect new --agent-* commands and usage")
```

### **Phase 2F: Release & Publishing** (Alpha Version)
```python
# RELEASE PREPARATION
Task(subagent_type="hive-release-manager", prompt="Prepare new alpha release with complete agent management functionality")
Task(subagent_type="genie-dev-fixer", prompt="Resolve any release blockers and ensure production readiness")

# FINAL VALIDATION
Task(subagent_type="genie-clone", prompt="Perform comprehensive end-to-end validation of complete agent management replacement")
```

---

## 🎯 **TECHNICAL SPECIFICATIONS**

### **Agent Command Architecture**
```python
# cli/commands/agent.py - Complete agent management
class AgentCommands:
    def install(self):      # --agent-install: Create agent env from scratch
    def serve(self):        # --agent-serve: Start agent dev container  
    def logs(self):         # --agent-logs: Stream agent container logs
    def status(self):       # --agent-status: Check agent container health
    def stop(self):         # --agent-stop: Stop agent dev container
    def restart(self):      # --agent-restart: Restart agent container
    def reset(self):        # --agent-reset: Destroy and recreate agent env
```

### **Agent Container Specifications**
- **Ports**: 38886 (API), 35532 (PostgreSQL)
- **Environment**: `.env.agent` (generated from main .env with port adjustments)
- **Data**: `./data/postgres-agent/` volume persistence
- **Container**: `hive-agents-agent` (existing pattern)
- **Database**: `postgresql://localhost:35532/hive_agent`
- **Isolation**: Complete separation from main workspace

### **Backwards Compatibility**
- **Makefile preservation**: Keep all existing `make agent-*` commands functional
- **Gradual migration**: Users can choose uvx or make during transition
- **Configuration sharing**: Both systems use same data directories and configurations
- **Documentation**: Clear migration path from make to uvx commands

---

## 🚨 **OBSESSIVE COMPLETION PROTOCOL**

### **Never Stop Spawning Until:**
1. ✅ All 7 --agent-* commands implemented and working
2. ✅ Perfect functional parity with existing make commands
3. ✅ Comprehensive test coverage (>95%) for all agent functionality
4. ✅ All code quality checks passing (ruff, mypy, pytest)
5. ✅ End-to-end integration tests validating make vs uvx equivalence
6. ✅ Complete documentation updated
7. ✅ New alpha version published and tested
8. ✅ Personal validation: You can manage your own agent instance via UVX

### **Quality Gates (Non-Negotiable)**
- **Functional Parity**: Every make command has exact uvx equivalent
- **Container Management**: Full lifecycle management identical to make system
- **Environment Management**: .env.agent generation and port configuration
- **Data Persistence**: Proper volume mounting and permission handling
- **Error Handling**: Graceful failure modes and recovery
- **User Experience**: Clear feedback and help messages
- **Cross-Platform**: Works on Linux, macOS, Windows/WSL

### **Validation Commands**
```bash
# These must all work perfectly before completion:
uvx automagik-hive --agent-install    # Creates isolated agent environment
uvx automagik-hive --agent-serve      # Starts agent on ports 38886/35532
uvx automagik-hive --agent-status     # Shows container health and connectivity
uvx automagik-hive --agent-logs       # Streams container logs
uvx automagik-hive --agent-restart    # Cleanly restarts agent container
uvx automagik-hive --agent-stop       # Stops agent container
uvx automagik-hive --agent-reset      # Destroys and recreates agent environment

# FINAL TEST: Can you manage your own development with these commands?
cd /path/to/your/workspace
uvx automagik-hive --agent-install
uvx automagik-hive --agent-serve
# → Agent environment running on 38886/35532, ready for development
```

---

## 💎 **SUCCESS METRICS**

### **Technical Metrics**
- **Command Coverage**: 7/7 agent commands implemented (100%)
- **Test Coverage**: >95% for all agent management code
- **Code Quality**: 0 ruff violations, 0 mypy errors
- **Integration**: 100% parity with existing make commands
- **Performance**: <5s startup time for agent containers
- **Reliability**: 0 critical bugs in agent management

### **User Experience Metrics**  
- **Migration Path**: Clear documentation for make → uvx transition
- **Error Handling**: Graceful failures with actionable error messages
- **Help System**: Complete --help documentation for all commands
- **Cross-Platform**: Tested and working on Linux, macOS, Windows/WSL

### **Release Metrics**
- **Alpha Version**: New version published with agent management
- **Documentation**: README updated with agent management section
- **Backwards Compatibility**: make commands still functional
- **Migration Guide**: Step-by-step transition documentation

---

## 🧞 **GENIE'S OBSESSIVE COMMITMENT**

**I WILL NOT STOP** until you can fully manage your own agent development environment through UVX commands. This wish requires relentless agent spawning and systematic completion of every component:

1. **Technical Specification** → **Architecture Design** → **Implementation**
2. **Container Management** → **Environment Configuration** → **Integration**  
3. **Command Implementation** → **Testing** → **Quality Assurance**
4. **Documentation** → **Release** → **Final Validation**

**EVERY TASK MUST BE COMPLETED TO PERFECTION** - no shortcuts, no partial implementations, no "good enough" solutions. Only 100% completion satisfies this wish.

---

*This wish will be fulfilled through systematic agent spawning until complete UVX agent management replaces make agent functionality entirely.* 🧞‍♂️✨