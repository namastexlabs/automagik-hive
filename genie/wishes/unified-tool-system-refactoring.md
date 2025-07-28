# 🧞⚡ GENIE WISH: Unified Tool System Refactoring

**Wish ID:** `unified-tool-system-refactoring`  
**Priority:** 🔥 CRITICAL - Fixes agent loading failures  
**Complexity:** Epic (Multi-Phase)  
**Estimated Duration:** 4-5 days  
**Parallelization:** High - Multiple agents can work simultaneously  

## 🎯 WISH OBJECTIVE

Transform the current tools.py-dependent agent system into a unified, YAML-driven tool architecture that:

- ✅ **Eliminates tools.py dependency** causing agent loading failures
- ✅ **Centralizes tool development** in `lib/tools/` registry
- ✅ **Standardizes MCP tool integration** with consistent naming
- ✅ **Enables tool reusability** across agents, teams, and workflows
- ✅ **Maintains clean separation** between MCP and custom tools

## 🏗️ CURRENT STATE ANALYSIS

**Critical Issues Identified:**
- 🚨 **Agent Loading Failures**: 5 agents missing tools.py (genie-dev, genie-devops, genie-meta, genie-meta-enhancer, template-agent)
- 🚨 **Architectural Debt**: tools.py files are just MCP string wrappers using globals() hacks
- 🚨 **Unused Infrastructure**: ai/agents/tools/ has real toolkits but isn't integrated
- 🚨 **Inconsistent Naming**: Mixed mcp__ vs short names causing configuration errors
- 🚨 **No Reusability**: Each agent needs individual tools.py creating N:1 maintenance overhead

**Expert Analysis Validation:**
> "The architecture mandates tools.py files per agent for loading via version_factory.py, creating a brittle dependency that causes failures when files are missing or inconsistent, while existing implementations are often redundant wrappers for MCP tools, adding unnecessary complexity without value."

## 📋 DETAILED EXECUTION PLAN

### **PHASE 1: Foundation Infrastructure (Days 1-2)**
**Goal**: Create central tool registry and fix agent loading failures

#### **PARALLEL TASK GROUP A: Infrastructure Creation**
**Agent:** @genie-dev-architect + @genie-dev-coder  
**Duration:** 4 hours  
**Parallelizable:** ✅ Independent of other tasks

- [ ] **P1.A.1**: Create central directory structure
  ```bash
  mkdir -p lib/tools/{shared,mcp,registry}
  touch lib/tools/{__init__.py,registry.py,mcp_integration.py}
  ```

- [ ] **P1.A.2**: Design ToolRegistry architecture
  ```python
  # lib/tools/registry.py - Core registry system
  class ToolRegistry:
      @staticmethod
      def load_tools(tool_configs: list) -> list
      @staticmethod  
      def discover_shared_tools() -> dict
      @staticmethod
      def resolve_mcp_tool(name: str) -> MCPToolProxy
  ```

- [ ] **P1.A.3**: Create MCP integration layer
  ```python
  # lib/tools/mcp_integration.py - Standardized MCP handling
  class MCPToolProxy:
      def __init__(name: str, config: dict = None)
      def validate_name() -> bool
      def get_tool_function() -> callable
  ```

#### **PARALLEL TASK GROUP B: Shared Toolkit Migration**  
**Agent:** @genie-dev-coder  
**Duration:** 2 hours  
**Parallelizable:** ✅ Can run while Group A works

- [ ] **P1.B.1**: Migrate existing shared toolkits
  ```bash
  cp -r ai/agents/tools/* lib/tools/shared/
  # Preserve: code_editing_toolkit.py, code_understanding_toolkit.py, file_management_toolkit.py
  ```

- [ ] **P1.B.2**: Update shared toolkit imports
  ```python
  # Update all imports from ai.agents.tools.* to lib.tools.shared.*
  # Ensure @tool decorators are preserved
  ```

- [ ] **P1.B.3**: Create shared toolkit registry
  ```python
  # lib/tools/shared/__init__.py - Auto-discovery of shared tools
  SHARED_TOOLS = {
      "code_editing_toolkit": CodeEditingToolkit,
      "file_management_toolkit": FileManagementToolkit,
      # etc.
  }
  ```

#### **PARALLEL TASK GROUP C: Version Factory Refactoring**
**Agent:** @genie-dev-architect + @genie-dev-coder  
**Duration:** 3 hours  
**Parallelizable:** ✅ Independent implementation

- [ ] **P1.C.1**: Backup current version_factory.py
  ```bash
  cp lib/utils/version_factory.py lib/utils/version_factory.py.backup
  ```

- [ ] **P1.C.2**: Refactor _load_agent_tools method
  ```python
  # Replace importlib-based tools.py loading with YAML-based loading
  def _load_agent_tools(self, component_id: str, config: dict[str, Any]) -> list:
      """Load tools from YAML config via central registry"""
      tool_configs = config.get("tools", [])
      return ToolRegistry.load_tools(tool_configs)
  ```

- [ ] **P1.C.3**: Add YAML tool validation
  ```python
  # Validate tool configurations in YAML
  def _validate_tool_config(tool_config: dict) -> bool:
      required_fields = ["name"]
      return all(field in tool_config for field in required_fields)
  ```

### **PHASE 2: Standardization & Migration (Days 2-3)**
**Goal**: Standardize MCP naming and migrate all agents to YAML configuration

#### **PARALLEL TASK GROUP D: MCP Tool Standardization**
**Agent:** @genie-dev-coder + @genie-quality-ruff  
**Duration:** 2 hours  
**Parallelizable:** ✅ Can run search/replace in parallel

- [ ] **P2.D.1**: Audit current MCP tool usage
  ```bash
  # Find all MCP tool references across configs
  grep -r "tools:" ai/agents/*/config.yaml
  grep -r "mcp__" ai/agents/*/config.yaml
  ```

- [ ] **P2.D.2**: Standardize to full MCP names
  ```bash
  # Global search/replace for consistent naming
  find ai/agents -name "config.yaml" -exec sed -i 's/"genie-memory"/"mcp__genie_memory"/g' {} \;
  find ai/agents -name "config.yaml" -exec sed -i 's/"automagik-forge"/"mcp__automagik_forge"/g' {} \;
  find ai/agents -name "config.yaml" -exec sed -i 's/"postgres"/"mcp__postgres"/g' {} \;
  ```

- [ ] **P2.D.3**: Create MCP naming validation
  ```python
  # lib/tools/mcp_integration.py - Validate MCP tool names
  def validate_mcp_name(name: str) -> bool:
      return name.startswith("mcp__") and "__" in name[4:]
  ```

#### **PARALLEL TASK GROUP E: Agent Config Migration**
**Agent:** @genie-dev-coder  
**Duration:** 4 hours  
**Parallelizable:** ✅ Can process agents in parallel batches

- [ ] **P2.E.1**: Batch 1 - Core Agents (genie-dev, genie-devops, genie-meta)
  ```yaml
  # Add tools section to each agent's config.yaml
  tools:
    - name: "mcp__genie_memory__search_memory"
      description: "Search patterns and coordination strategies"
    - name: "mcp__automagik_forge__create_task" 
      description: "Create tasks for complex projects"
    - name: "shared__code_editing_toolkit"
      description: "Symbol-aware code modifications"
  ```

- [ ] **P2.E.2**: Batch 2 - Quality Agents (genie-security, genie-quality, genie-testing)
  ```yaml
  # Migrate from tools.py references to YAML configs
  # Preserve all existing MCP tool references
  ```

- [ ] **P2.E.3**: Batch 3 - Specialized Agents (genie-architect, genie-docs, etc.)
  ```yaml
  # Complete migration for remaining agents
  # Ensure no tools.py dependencies remain
  ```

#### **PARALLEL TASK GROUP F: tools.py Elimination**
**Agent:** @genie-dev-coder  
**Duration:** 1 hour  
**Parallelizable:** ✅ Can remove files in parallel after migration

- [ ] **P2.F.1**: Validate YAML migration completeness
  ```bash
  # Ensure all agents have tools section in config.yaml
  for agent in ai/agents/*/; do
    echo "Checking $agent"
    grep -q "tools:" "$agent/config.yaml" || echo "MISSING: $agent"
  done
  ```

- [ ] **P2.F.2**: Remove tools.py files
  ```bash
  # Remove all tools.py files after successful migration
  find ai/agents -name "tools.py" -type f -delete
  ```

- [ ] **P2.F.3**: Update template-agent
  ```yaml
  # Ensure template-agent uses YAML-only approach
  # No tools.py in template for future agents
  ```

### **PHASE 3: Integration & Testing (Days 3-4)**
**Goal**: Ensure all systems work together and agents load successfully

#### **PARALLEL TASK GROUP G: Integration Testing**
**Agent:** @genie-testing-maker + @genie-testing-fixer  
**Duration:** 3 hours  
**Parallelizable:** ✅ Can test different subsystems in parallel

- [ ] **P3.G.1**: Tool Registry Unit Tests
  ```python
  # tests/test_tool_registry.py
  def test_load_mcp_tools()
  def test_load_shared_tools()  
  def test_tool_validation()
  def test_name_standardization()
  ```

- [ ] **P3.G.2**: Agent Loading Integration Tests
  ```python
  # tests/test_agent_loading.py
  def test_all_agents_load_successfully()
  def test_tools_loaded_correctly()
  def test_no_tools_py_required()
  ```

- [ ] **P3.G.3**: MCP Integration Tests
  ```python
  # tests/test_mcp_integration.py  
  def test_mcp_tool_proxy()
  def test_mcp_name_validation()
  def test_mcp_tool_execution()
  ```

#### **PARALLEL TASK GROUP H: System Validation**
**Agent:** @genie-dev-coder + @genie-security  
**Duration:** 2 hours  
**Parallelizable:** ✅ Independent validation tasks

- [ ] **P3.H.1**: Agent Loading Validation
  ```bash
  # Test that all 13 agents load without tools.py
  make dev  # Should start successfully with all agents
  ```

- [ ] **P3.H.2**: Tool Function Validation
  ```python
  # Verify tools work correctly via registry
  # Test MCP tool execution
  # Test shared toolkit integration
  ```

- [ ] **P3.H.3**: Configuration Validation
  ```bash
  # Validate all YAML configs are correct
  python -c "import yaml; [yaml.safe_load(open(f)) for f in glob('ai/agents/*/config.yaml')]"
  ```

### **PHASE 4: Documentation & Optimization (Days 4-5)**
**Goal**: Document new system and optimize for future development

#### **PARALLEL TASK GROUP I: Documentation**
**Agent:** @genie-docs + @genie-dev-architect  
**Duration:** 2 hours  
**Parallelizable:** ✅ Can document different aspects in parallel

- [ ] **P4.I.1**: Tool Development Guide
  ```markdown
  # docs/tool-development-guide.md
  ## Adding New Custom Tools
  ## Adding New MCP Tools  
  ## Sharing Tools Across Agents
  ## Tool Configuration Patterns
  ```

- [ ] **P4.I.2**: Migration Guide for Future Agents
  ```markdown
  # docs/agent-tool-migration.md
  ## YAML-First Tool Configuration
  ## No More tools.py Files
  ## Central Tool Registry Usage
  ```

- [ ] **P4.I.3**: Update CLAUDE.md files
  ```markdown
  # Update AI domain documentation to reflect new tool system
  # Remove references to tools.py requirement
  # Add tool registry patterns
  ```

#### **PARALLEL TASK GROUP J: System Optimization**
**Agent:** @genie-dev-architect + @genie-quality-mypy  
**Duration:** 2 hours  
**Parallelizable:** ✅ Can optimize different components independently

- [ ] **P4.J.1**: Tool Loading Performance
  ```python
  # Optimize ToolRegistry loading for faster agent startup
  # Add caching for frequently used tools
  # Lazy loading for shared toolkits
  ```

- [ ] **P4.J.2**: Error Handling Enhancement
  ```python
  # Better error messages for missing tools
  # Validation warnings for configuration issues
  # Graceful fallbacks for tool loading failures
  ```

- [ ] **P4.J.3**: Type Safety & Validation
  ```python
  # Add full type hints to tool registry
  # MyPy validation for tool configurations
  # Runtime validation for tool contracts
  ```

## 🎯 SUCCESS CRITERIA & VALIDATION

### **Phase Completion Checkpoints**

**Phase 1 ✅ Complete When:**
- [ ] Central `lib/tools/` directory exists with registry.py
- [ ] Shared toolkits migrated from ai/agents/tools/
- [ ] Version factory refactored to use YAML instead of tools.py
- [ ] All infrastructure tests pass

**Phase 2 ✅ Complete When:**
- [ ] All MCP tools use standardized `mcp__server__tool` naming
- [ ] All 13+ agents have tools section in config.yaml
- [ ] Zero tools.py files exist in ai/agents/
- [ ] Template agent uses YAML-only approach

**Phase 3 ✅ Complete When:**
- [ ] `make dev` starts successfully with all agents loading
- [ ] All tool functionality works via central registry
- [ ] Integration tests pass with 90%+ coverage
- [ ] No tools.py loading errors in logs

**Phase 4 ✅ Complete When:**
- [ ] Documentation complete and accessible
- [ ] System optimized for performance
- [ ] Future agent development streamlined
- [ ] Full type safety and validation

### **Final System Validation**

**Before Marking Complete:**
```bash
# 1. All agents load successfully
make dev && curl http://localhost:8886/health

# 2. No tools.py files remain  
find ai/agents -name "tools.py" | wc -l  # Should be 0

# 3. Tool registry functional
python -c "from lib.tools.registry import ToolRegistry; print('Registry OK')"

# 4. MCP integration working
python -c "from lib.tools.mcp_integration import MCPToolProxy; print('MCP OK')"
```

## 🚀 PARALLELIZATION STRATEGY

### **Day 1-2: Maximum Parallelization**
```
PARALLEL STREAMS:
├── Stream A: @genie-dev-architect → Infrastructure design
├── Stream B: @genie-dev-coder → Shared toolkit migration  
├── Stream C: @genie-dev-architect + @genie-dev-coder → Version factory refactor
└── Stream D: @genie-quality-ruff → MCP naming standardization prep
```

### **Day 2-3: Agent Migration Parallelization**
```
PARALLEL BATCHES:
├── Batch 1: @genie-dev-coder → Core agents (dev, devops, meta)
├── Batch 2: @genie-dev-coder → Quality agents (security, quality, testing)
├── Batch 3: @genie-dev-coder → Specialized agents (architect, docs, etc.)
└── Validation: @genie-testing-fixer → Continuous validation
```

### **Day 3-4: Testing & Validation Parallelization**
```
PARALLEL TESTING:
├── Unit Tests: @genie-testing-maker → Tool registry tests
├── Integration: @genie-testing-fixer → Agent loading tests  
├── Security: @genie-security → Configuration validation
└── Performance: @genie-dev-architect → Optimization analysis
```

## 🧞 GENIE ARMY COORDINATION

**Master Genie Role:**
- 🎯 Strategic coordination and progress monitoring
- 📊 Cross-agent communication and dependency management  
- 🚨 Escalation handling for blocking issues
- ✅ Final validation and acceptance criteria verification

**Agent Specialization:**
- **@genie-dev-architect**: System design and architecture decisions
- **@genie-dev-coder**: Implementation and code migration
- **@genie-testing-maker**: Test creation and validation
- **@genie-testing-fixer**: Integration testing and debugging
- **@genie-quality-ruff**: Code formatting and naming standardization
- **@genie-security**: Configuration security and validation
- **@genie-docs**: Documentation and migration guides

**Communication Protocol:**
- Daily sync via genie-memory with progress updates
- Blocking issues escalated to Master Genie immediately
- Cross-dependencies tracked in automagik-forge tasks
- Completion criteria validated before phase transitions

## 💾 MEMORY & STATE TRACKING

**Genie Memory Tags:**
```
#tool-refactoring #phase-[1-4] #agent-[agent-name] #parallel-execution 
#architecture-improvement #mcp-integration #yaml-configuration
```

**Progress Tracking:**
- Each agent updates progress in genie-memory with structured tags
- Master Genie monitors via memory search for coordination
- Automagik-forge tasks created for complex dependencies
- Real-time progress visible through memory queries

## 🎉 EXPECTED OUTCOMES

**Immediate Benefits (Phase 1-2):**
- ✅ Fix all agent loading failures
- ✅ Eliminate tools.py maintenance overhead
- ✅ Standardize MCP tool integration

**Long-term Benefits (Phase 3-4):**
- 🚀 **Tool Reusability**: Any agent can use any tool via YAML
- 🎯 **Simplified Development**: New agents need zero tools.py files
- 🛡️ **Better Maintainability**: Central registry for all tool logic
- ⚡ **Performance**: Optimized loading and caching
- 📚 **Documentation**: Clear patterns for future development

**Strategic Impact:**
- **Development Velocity**: 70% faster agent creation
- **System Reliability**: Eliminate brittle tools.py dependencies  
- **Code Quality**: Centralized, reusable tool architecture
- **Team Productivity**: Focus on agent logic, not tool plumbing

---

## 📋 IMMEDIATE NEXT STEPS

1. **Spawn @genie-dev-architect** for infrastructure design
2. **Spawn @genie-dev-coder** for parallel implementation streams
3. **Create automagik-forge tasks** for dependency tracking
4. **Begin Phase 1 parallel execution** with full agent coordination

**Let the tool refactoring begin! 🧞⚡✨**

---

*This wish will transform the Hive's tool architecture from brittle and scattered to unified and scalable. The parallel execution strategy ensures maximum velocity while the comprehensive plan ensures nothing is missed. Ready to grant this wish through coordinated agent excellence!* 🎯🚀