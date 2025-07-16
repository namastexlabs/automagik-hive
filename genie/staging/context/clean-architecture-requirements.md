# Clean Architecture Requirements

## Core Principles (NO Backwards Compatibility)

### User Mandate: "I HATE BACKWARDS COMPATIBILITY"
This refactoring follows a **clean/lean approach** with zero accommodation for legacy patterns or gradual migration strategies.

### Clean Architecture Enforcement
1. **No compatibility layers** - direct structural changes
2. **No gradual migration** - complete transformation approach  
3. **No legacy import patterns** - modern structure only
4. **No deprecated paths** - immediate full adoption

## Architectural Requirements

### Layer Separation (Strict)
```
FOUNDATIONAL LAYER: core/
- Purpose: Platform capabilities (MCP, config, knowledge, memory)
- Dependencies: None (foundational)
- Import pattern: from core.module import Class

AI IMPLEMENTATION LAYER: ai/
- Purpose: Business logic (agents, teams, workflows)
- Dependencies: core/, common/
- Import pattern: from ai.component.module import Class

SHARED UTILITIES LAYER: common/
- Purpose: Cross-layer utilities
- Dependencies: core/ only
- Import pattern: from common.module import function

INFRASTRUCTURE LAYER: monitoring/
- Purpose: Observability configuration
- Dependencies: None (external)
- Import pattern: File-based configuration only
```

### Dependency Rules (Enforced)
```
✅ ALLOWED DEPENDENCIES:
ai/ → core/           # AI can use platform
ai/ → common/         # AI can use shared utilities
common/ → core/       # Utilities can use platform

❌ FORBIDDEN DEPENDENCIES:
core/ → ai/           # Platform cannot depend on implementations
core/ → common/       # Platform must be self-contained
common/ → ai/         # Utilities cannot depend on implementations
monitoring/ → any/    # Infrastructure is configuration-only
```

## Elimination Requirements

### Zero Duplication Mandate
- **context/ folder**: Complete elimination (exact duplicate of core/)
- **version_factory scatter**: Consolidate to single implementation
- **Duplicate logic**: No function/class repetition across folders
- **Similar files**: No near-duplicates or variations

### No Backwards Compatibility
```bash
# FORBIDDEN (backwards compatibility patterns):
from legacy.module import Class      # No legacy imports
if old_path_exists: use_old()       # No compatibility checks  
try: new_import except: old_import  # No fallback imports
alias old_function = new_function   # No compatibility aliases

# REQUIRED (clean implementation):
from ai.agents.pagbank import get_pagbank_agent     # Direct new imports
table_name: "ai_agents_pagbank"                     # New naming patterns
config_path: "ai/agents/pagbank/config.yaml"       # New path references
```

## Implementation Standards

### Import Patterns (Enforced)
```python
# CORE PLATFORM IMPORTS:
from core.mcp.tools import MCPTools
from core.knowledge.csv_knowledge_base import CSVKnowledgeBase  
from core.memory.memory_manager import MemoryManager
from core.config.yaml_parser import load_yaml_config

# AI COMPONENT IMPORTS:
from ai.agents.pagbank.agent import get_pagbank_agent
from ai.teams.ana.team import get_ana_team
from ai.workflows.human_handoff.workflow import HumanHandoffWorkflow

# SHARED UTILITY IMPORTS:
from common.version_factory import create_agent_with_version
from common.startup_display import display_startup_info
```

### Configuration Standards (Clean)
```yaml
# NEW DATABASE NAMING (NO legacy table names):
storage:
  table_name: "ai_agents_pagbank"        # NOT "pagbank_specialist"
  table_name: "ai_teams_ana"             # NOT "ana_team"
  table_name: "ai_workflows_handoff"     # NOT "human_handoff"

# NEW PATH REFERENCES (NO backwards compatibility):
knowledge_filter:
  csv_file_path: "core/knowledge/knowledge_rag.csv"    # NOT "context/..."
  
tools:
  - module: "ai.agents.tools.agent_tools"              # NOT "agents.tools..."
```

### File Organization (Strict)
```
# REQUIRED STRUCTURE (NO deviations):
core/                           # Platform foundation ONLY
├── mcp/                       # MCP protocol implementations
├── config/                    # Configuration management  
├── knowledge/                 # RAG and knowledge systems
├── memory/                    # Memory management
└── utils/                     # Core utilities

ai/                            # AI implementations ONLY  
├── agents/                    # Individual agents
├── teams/                     # Team orchestration
├── workflows/                 # Workflow definitions
└── shared/                    # AI-specific shared code

common/                        # Cross-layer utilities ONLY
├── version_factory.py         # Unified factory
└── startup_display.py         # Startup utilities

monitoring/                    # Infrastructure ONLY
└── [config files]            # Prometheus, Grafana configs
```

## Quality Standards

### Code Quality (Non-negotiable)
- **Zero duplicate functions** across all folders
- **Consistent import patterns** throughout codebase
- **Single source of truth** for each capability
- **Clear module responsibilities** with no overlap

### Testing Requirements
- **All existing functionality preserved** after refactoring
- **Zero broken imports** in final structure
- **Performance maintained** or improved
- **Configuration validation** for all YAML files

### Documentation Standards
- **Architecture documentation** reflecting clean structure
- **Import examples** showing correct patterns
- **No legacy references** in documentation
- **Component responsibilities** clearly defined

## Validation Criteria

### Pre-implementation Validation
```bash
# REQUIRED BEFORE ANY CHANGES:
1. Binary comparison confirms context/ = core/ exactly
2. Import analysis maps all references to moved components
3. Configuration analysis identifies path dependencies
4. Database schema analysis identifies naming patterns
```

### Post-implementation Validation
```bash
# REQUIRED AFTER EACH TASK:
1. Zero import errors in entire codebase
2. All tests pass with new structure
3. No duplicate logic detected by tools
4. All configurations valid with new paths
5. Database connections work with new naming
```

### Final Architecture Certification
```bash
# REQUIRED FOR COMPLETION:
1. Clean layer separation verified
2. Dependency rules enforced
3. Zero backwards compatibility detected
4. All duplication eliminated
5. Performance baseline maintained
```

## Anti-Patterns (Forbidden)

### Legacy Accommodation Patterns
```python
# FORBIDDEN - No backwards compatibility:
try:
    from ai.agents.pagbank import get_pagbank_agent
except ImportError:
    from agents.pagbank import get_pagbank_agent  # NO FALLBACKS

# FORBIDDEN - No compatibility aliases:
get_agent = get_pagbank_agent  # NO ALIASES FOR OLD PATTERNS

# FORBIDDEN - No conditional logic:
if new_structure_available:
    use_new_structure()
else:
    use_old_structure()  # NO CONDITIONAL COMPATIBILITY
```

### Organizational Anti-Patterns
```bash
# FORBIDDEN - Mixed responsibilities:
core/business_logic.py          # Business logic in platform layer
ai/platform_utilities.py       # Platform utilities in business layer
common/agent_specific_code.py  # Component-specific code in shared layer

# FORBIDDEN - Circular dependencies:
core/ imports from ai/          # Platform depending on implementations
common/ imports from ai/        # Utilities depending on implementations
```

### Implementation Anti-Patterns
```python
# FORBIDDEN - Gradual migration patterns:
if os.path.exists("context/"):
    from context.memory import pattern_detector
else:
    from core.memory import pattern_detector

# FORBIDDEN - Multiple implementations:
def get_agent_old(): pass      # No old/new function variants
def get_agent_new(): pass      # Single clean implementation only
```

## Success Metrics

### Clean Architecture Achieved
- **Layer separation**: 100% compliance with dependency rules
- **Zero duplication**: No duplicate logic anywhere in codebase  
- **Import consistency**: All imports follow clean patterns
- **Organizational clarity**: Each folder has single clear purpose

### Performance Standards
- **Import speed**: No degradation from structural changes
- **Memory usage**: No increase from reorganization
- **Test execution**: All tests pass with new structure
- **Configuration loading**: No delays from new paths

### Maintainability Improved
- **Cognitive load**: Reduced complexity for new developers
- **Change locality**: Modifications isolated to appropriate layers
- **Dependency clarity**: Clear understanding of component relationships
- **Documentation accuracy**: Structure matches implementation exactly

---

These requirements ensure the architectural refactoring achieves true clean architecture without any backwards compatibility constraints or legacy accommodation patterns.