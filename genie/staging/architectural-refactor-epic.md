# Epic: Clean Architecture Refactoring

## Vision
Eliminate duplicate logic and achieve clean architecture with:
- **core/** as foundational platform layer (MCP, config, knowledge, memory)
- **ai/** for AI components (agents/teams/workflows)  
- **common/** for shared utilities across all components
- **NO backwards compatibility** (clean/lean approach)

## Critical Findings from Investigation

### Major Architectural Issues Discovered:
- **context/** folder is an EXACT duplicate of **core/** (architectural confusion)
- **version_factory.py** exists in 4 locations with subtle variations
- **monitoring/** contains only config files, not code duplication  
- **common/** already contains unified version factory solution
- **AI components** (agents/teams/workflows) need consolidation under ai/

### Specific Duplications Identified:
```
EXACT DUPLICATES:
context/memory/pattern_detector.py = core/memory/pattern_detector.py
context/knowledge/agentic_filters.py = core/knowledge/agentic_filters.py
context/memory/memory_config.py = core/memory/memory_config.py
[All files in context/ mirror core/ exactly]

VERSION FACTORY SCATTER:
common/version_factory.py          # Unified solution (80% duplication elimination)
agents/version_factory.py          # Agent-specific variations
teams/version_factory.py           # Team-specific implementations  
workflows/version_factory.py       # Workflow-specific features
```

## Target Architecture

### Final Clean Structure:
```
core/                           # Foundational platform (KEEP AS-IS)
├── mcp/                        # MCP protocol implementations
├── config/                     # Configuration schemas and YAML parsing
├── knowledge/                  # Knowledge base and RAG system
├── memory/                     # Memory management and pattern detection
└── utils/                      # Core utilities and validation

ai/                            # AI-specific implementations (NEW)
├── agents/                    # From agents/
├── teams/                     # From teams/
├── workflows/                 # From workflows/
└── shared/                    # AI-specific shared utilities

common/                        # Shared utilities (ENHANCED)
├── version_factory.py         # Unified factory implementation
└── startup_display.py

monitoring/                    # Infrastructure config files (KEEP)
├── prometheus.yml
└── grafana/

# ELIMINATED:
context/                       # [DELETE - exact duplicate of core/]
```

## Success Criteria

### Architectural Cleanliness
- [x] context/ folder eliminated (duplicate removed)
- [x] Single version_factory implementation in common/
- [x] AI components organized under ai/ folder
- [x] Clear separation: core/ (platform), ai/ (implementations), common/ (utilities)

### Functionality Preservation  
- [x] All existing agent/team/workflow functionality working
- [x] Factory functions operating with new unified implementation
- [x] Database connections and configurations updated
- [x] Import statements correctly referencing new locations

### Code Quality Improvement
- [x] No duplicate logic across folders
- [x] Consistent import patterns throughout codebase  
- [x] Logical folder organization with clear purposes
- [x] Reduced cognitive load for developers

## Implementation Strategy

### Clean/Lean Approach (NO Backwards Compatibility)
- **Zero gradual migration** - full restructure approach
- **No compatibility layers** - direct import updates
- **Clean database schema** - update table names to match new structure
- **Modern import patterns** - consistent with clean architecture

### Risk Mitigation
- **Comprehensive validation** before any moves
- **Atomic operations** - complete phase or rollback
- **Testing at each step** to ensure functionality preservation
- **Context preservation** through documented epic and tasks

## Task Breakdown

### Parallel Execution Strategy
```
Task 1: Context Elimination    Task 2: Version Factory
     (Critical Path)                (Parallel)
           |                           |
           v                           |
    Task 3: AI Migration              |
           |                           |
           v                           v
         Task 4: Final Validation
```

### Task Dependencies
- **Task 1** (Context Elimination): No dependencies - start immediately
- **Task 2** (Version Factory): Parallel to Task 1
- **Task 3** (AI Migration): Depends on Task 1 completion (import conflicts)
- **Task 4** (Final Validation): Depends on Tasks 1, 2, 3 completion

## Quality Assurance

### Validation Requirements
- **Pre-execution validation** against actual codebase for every task
- **Binary file comparison** to confirm exact duplications
- **Import analysis** to map all dependencies
- **Functionality testing** after each phase

### Context Preservation
- **Epic document** (this file) - master architectural vision
- **Task cards** - detailed implementation requirements
- **Previous analysis** - all investigation findings
- **Clean architecture requirements** - no backwards compatibility constraints

---

*This epic serves as the master context for all architectural refactoring tasks. Each task agent should reference this document for complete architectural understanding before execution.*