# Technical Specification Document: CLI Cleanup Strategy

## 1. OVERVIEW

**Objective**: Systematically refactor and modernize the CLI implementation to eliminate technical debt, reduce complexity, and improve maintainability through parallel execution strategy.

**Success Metrics**: 
- Reduce total lines of code by 30% (from 13,168 to ~9,200)
- Eliminate 100% of linting violations (currently 4 violations)
- Reduce cyclomatic complexity in monolithic files by 50%
- Standardize naming conventions (eliminate "unified_installer.py")
- Remove all dead code and unused imports
- Achieve 100% test coverage for refactored components

## 2. CURRENT STATE ANALYSIS

### File Size Analysis
```
MONOLITHIC FILES (>1000 lines):
- health_checker.py: 1,268 lines (CRITICAL)
- workspace_manager.py: 1,110 lines (CRITICAL)
- unified_installer.py: 922 lines (HIGH)
- workflow_orchestrator.py: 897 lines (HIGH)
- uninstall.py: 798 lines (MEDIUM)
- service_manager.py: 726 lines (MEDIUM)
- docker_service.py: 700 lines (MEDIUM)
```

### Technical Debt Inventory
```
LINTING VIOLATIONS:
- W291: Trailing whitespace (2 instances)
- SIM103: Needless boolean return (1 instance)
- SIM118: Use `key in dict` instead of `key in dict.keys()` (1 instance)

NAMING VIOLATIONS:
- unified_installer.py → installer.py (user requirement)
- workspace_manager.py → workspace.py (already exists, merge needed)

ARCHITECTURAL ISSUES:
- 47 classes across 30 files (over-engineering)
- 451 functions (excessive granularity)
- Multiple manager/service/orchestrator patterns (redundancy)
- Lazy loading complexity in LazyCommandLoader
```

## 3. FUNCTIONAL REQUIREMENTS

### Core Cleanup Features
- **File Consolidation**: Merge redundant manager/service patterns into cohesive modules
- **Size Reduction**: Break monolithic files into focused, single-responsibility modules
- **Naming Standardization**: Apply consistent naming conventions throughout CLI
- **Dead Code Elimination**: Remove unused imports, functions, and classes
- **Complexity Reduction**: Simplify over-engineered abstractions

### User Stories
- As a developer, I want simple, focused files (<350 lines) so that I can understand and maintain code easily
- As a maintainer, I want consistent naming patterns so that I can navigate the codebase intuitively  
- As a contributor, I want clean code without linting violations so that I can focus on features
- As a user, I want "installer.py" instead of "unified_installer.py" for better naming clarity

## 4. NON-FUNCTIONAL REQUIREMENTS

### Performance
- CLI startup time: <2 seconds (maintain current lazy loading benefits)
- Memory usage: Reduce by 20% through dead code elimination
- Import time: <500ms for any command execution

### Maintainability
- Maximum file size: 350 lines per file
- Maximum function complexity: 10 cyclomatic complexity
- Test coverage: 90%+ for all refactored components
- Documentation: Every public method documented

### Quality Gates
- Zero linting violations (Ruff)
- Zero type checking errors (MyPy)
- 100% backward compatibility for CLI interface
- All existing functionality preserved

## 5. TECHNICAL ARCHITECTURE

### Cleanup Phase Structure

#### Phase 1: Foundation Cleanup (Parallel Execution)
```python
# 8 Parallel Tasks - File-Level Fixes
Task("genie-quality-ruff"): Fix linting violations per file
Task("genie-dev-fixer"): Remove dead imports per file  
Task("genie-dev-coder"): Rename unified_installer.py → installer.py
Task("genie-dev-coder"): Merge duplicate workspace files
```

#### Phase 2: Monolithic File Decomposition (Parallel Execution)
```python
# 7 Parallel Tasks - One per monolithic file
Task("genie-dev-designer"): Decompose health_checker.py (1,268 lines)
Task("genie-dev-designer"): Decompose workspace_manager.py (1,110 lines)  
Task("genie-dev-designer"): Decompose installer.py (922 lines)
Task("genie-dev-designer"): Decompose workflow_orchestrator.py (897 lines)
Task("genie-dev-designer"): Decompose uninstall.py (798 lines)
Task("genie-dev-designer"): Decompose service_manager.py (726 lines)
Task("genie-dev-designer"): Decompose docker_service.py (700 lines)
```

#### Phase 3: Architecture Simplification (Sequential Dependencies)
```python
# Sequential workflow - dependencies between phases
genie-dev-planner: Analyze manager/service/orchestrator patterns
genie-dev-designer: Design unified architecture patterns
genie-dev-coder: Implement simplified abstractions
genie-testing-maker: Create comprehensive test suite
```

### Component Breakdown

#### Target File Structure (Post-Cleanup)
```
cli/
├── commands/
│   ├── installer.py          # Renamed from unified_installer
│   ├── health.py            # Split from health_checker.py  
│   ├── health_report.py     # Health reporting logic
│   ├── workspace.py         # Merged workspace functionality
│   ├── service.py          # Simplified service operations
│   ├── uninstall.py        # Streamlined uninstall logic
│   └── orchestrator.py     # Core orchestration only
├── core/
│   ├── docker.py           # Simplified Docker operations
│   ├── postgres.py         # Database operations only
│   ├── environment.py      # Environment management
│   └── security.py         # Security utilities
└── utils/                  # New - extracted utilities
    ├── validators.py       # Input validation logic
    ├── formatters.py       # Output formatting
    └── helpers.py          # Common helper functions
```

### Data Models (Simplified)

#### Cleanup Progress Tracking
```python
@dataclass
class CleanupResult:
    """Track cleanup operation results."""
    file_path: str
    original_lines: int
    final_lines: int
    violations_fixed: int
    functions_removed: int
    classes_simplified: int
    status: str  # "success", "partial", "failed"
```

#### File Decomposition Strategy
```python
@dataclass
class DecompositionPlan:
    """Plan for breaking down monolithic files."""
    source_file: str
    target_files: list[str]
    function_mapping: dict[str, str]
    dependency_order: list[str]
    validation_criteria: list[str]
```

### API Contracts (Internal CLI)

#### Cleanup Operation Interface
```python
class FileCleanupStrategy:
    """Standard interface for file cleanup operations."""
    
    def analyze_violations(self, file_path: str) -> list[str]:
        """Identify specific issues in file."""
        
    def decompose_file(self, file_path: str, target_size: int) -> list[str]:
        """Break file into smaller focused modules."""
        
    def validate_cleanup(self, original: str, targets: list[str]) -> bool:
        """Ensure functionality preservation."""
```

## 6. PARALLEL EXECUTION STRATEGY

### Multi-Agent Coordination Plan

#### Phase 1: Parallel File-Level Cleanup (8 Simultaneous Tasks)
```python
# MANDATORY PARALLEL EXECUTION - Independent file operations
Task(subagent_type="genie-quality-ruff", 
     prompt="Fix linting violations in cli/commands/__init__.py")
Task(subagent_type="genie-quality-ruff", 
     prompt="Fix linting violations in cli/commands/init.py")  
Task(subagent_type="genie-quality-ruff", 
     prompt="Fix linting violations in cli/commands/workspace.py")
Task(subagent_type="genie-quality-ruff", 
     prompt="Fix linting violations in cli/main.py")
Task(subagent_type="genie-dev-coder", 
     prompt="Rename cli/commands/unified_installer.py to installer.py")
Task(subagent_type="genie-dev-fixer", 
     prompt="Remove dead imports from cli/core/ directory")
Task(subagent_type="genie-dev-fixer", 
     prompt="Remove dead imports from cli/commands/ directory")
Task(subagent_type="genie-dev-coder", 
     prompt="Merge duplicate workspace functionality")
```

#### Phase 2: Parallel Monolithic Decomposition (7 Simultaneous Tasks)
```python
# MANDATORY PARALLEL EXECUTION - Independent file decomposition
Task(subagent_type="genie-dev-designer", 
     prompt="Decompose cli/commands/health_checker.py into health.py + health_report.py (<350 lines each)")
Task(subagent_type="genie-dev-designer", 
     prompt="Decompose cli/commands/workspace_manager.py into focused modules (<350 lines each)")
Task(subagent_type="genie-dev-designer", 
     prompt="Decompose cli/commands/installer.py into installer.py + install_utils.py (<350 lines each)")
Task(subagent_type="genie-dev-designer", 
     prompt="Decompose cli/commands/workflow_orchestrator.py into orchestrator.py + workflow_utils.py (<350 lines each)")
Task(subagent_type="genie-dev-designer", 
     prompt="Decompose cli/commands/uninstall.py into focused uninstall modules (<350 lines each)")
Task(subagent_type="genie-dev-designer", 
     prompt="Decompose cli/commands/service_manager.py into service.py + service_utils.py (<350 lines each)")
Task(subagent_type="genie-dev-designer", 
     prompt="Decompose cli/core/docker_service.py into docker.py + docker_utils.py (<350 lines each)")
```

#### Phase 3: Architecture Validation (Parallel Quality Gates)
```python
# MANDATORY PARALLEL EXECUTION - Independent validation
Task(subagent_type="genie-quality-ruff", 
     prompt="Validate all refactored files pass linting")
Task(subagent_type="genie-quality-mypy", 
     prompt="Validate all refactored files pass type checking")
Task(subagent_type="genie-testing-maker", 
     prompt="Create comprehensive test suite for refactored CLI")
Task(subagent_type="genie-dev-fixer", 
     prompt="Validate CLI functionality preservation through integration tests")
```

### Risk Mitigation Strategy

#### Backup and Rollback Plan
```python
# Pre-cleanup backup strategy
cleanup_workflow = {
    "backup_phase": "Create git branch 'cli-cleanup-backup' before any changes",
    "incremental_commits": "Commit after each parallel task completion",
    "rollback_triggers": ["Functionality loss", "Test failures", "Import errors"],
    "validation_gates": ["Ruff passes", "MyPy passes", "All tests pass", "CLI commands work"]
}
```

#### Functionality Preservation Tests
```python
# Critical CLI functionality that must be preserved
preservation_tests = [
    "uvx automagik-hive --install agent",
    "uvx automagik-hive --start agent", 
    "uvx automagik-hive --health agent",
    "uvx automagik-hive --status agent",
    "uvx automagik-hive --logs agent",
    "uvx automagik-hive --stop agent",
    "uvx automagik-hive --uninstall agent"
]
```

## 7. TEST-DRIVEN DEVELOPMENT STRATEGY

### Red-Green-Refactor Integration

#### Red Phase: Pre-Cleanup Test Creation
```python
# Create failing tests for target architecture
test_scenarios = [
    "test_installer_py_exists_not_unified_installer",
    "test_health_checker_under_350_lines", 
    "test_workspace_manager_under_350_lines",
    "test_zero_linting_violations",
    "test_all_imports_used",
    "test_consistent_naming_patterns"
]
```

#### Green Phase: Minimal Cleanup Implementation
```python
# Implement just enough cleanup to pass tests
cleanup_priorities = [
    "Fix linting violations first (quick wins)",
    "Rename unified_installer.py (user requirement)", 
    "Break largest files (health_checker.py priority)",
    "Remove obvious dead code (unused imports)"
]
```

#### Refactor Phase: Quality and Architecture
```python
# Improve design while keeping tests green
refactor_opportunities = [
    "Simplify LazyCommandLoader complexity",
    "Unify manager/service/orchestrator patterns", 
    "Extract common utilities to utils/ directory",
    "Optimize import dependencies"
]
```

### Test Categories

#### Unit Tests: Component-Level Validation
```python
# Test each refactored module independently
unit_test_strategy = {
    "installer.py": "Test installation workflow without dependencies",
    "health.py": "Test health checking logic with mocked services", 
    "workspace.py": "Test workspace operations with mocked filesystem",
    "service.py": "Test service management with mocked Docker"
}
```

#### Integration Tests: CLI Command Validation  
```python
# Test CLI commands end-to-end
integration_test_strategy = {
    "command_execution": "All 8 CLI commands execute successfully",
    "workflow_completion": "Install → start → health → stop → uninstall workflow",
    "error_handling": "Graceful failure modes and recovery suggestions",
    "cross_platform": "Linux, macOS, Windows compatibility"
}
```

#### Regression Tests: Functionality Preservation
```python
# Ensure no functionality lost during cleanup
regression_test_strategy = {
    "api_compatibility": "All existing CLI flags and options work",
    "output_format": "Help text and error messages unchanged",
    "configuration": "All configuration files and environment variables work",
    "performance": "CLI startup time not degraded"
}
```

## 8. IMPLEMENTATION PHASES

### Phase 1: Foundation Cleanup (Week 1)
**Deliverables**:
- Fix all 4 linting violations
- Rename unified_installer.py → installer.py
- Remove all unused imports across CLI
- Merge duplicate workspace functionality
- Create git backup branch

**Timeline**: 2 days (parallel execution)
**Agents**: 8 parallel tasks
**Success Criteria**: Zero linting violations, consistent naming, clean imports

### Phase 2: Monolithic File Decomposition (Week 1-2)
**Deliverables**:
- Break health_checker.py (1,268 lines) into health.py + health_report.py (<350 lines each)
- Break workspace_manager.py (1,110 lines) into focused modules (<350 lines each)
- Break installer.py (922 lines) into installer.py + install_utils.py (<350 lines each)
- Break workflow_orchestrator.py (897 lines) into orchestrator.py + workflow_utils.py (<350 lines each)
- Break remaining monolithic files following same pattern

**Timeline**: 5 days (parallel execution)
**Agents**: 7 parallel tasks (one per monolithic file)
**Success Criteria**: All files <350 lines, functionality preserved, tests passing

### Phase 3: Architecture Simplification (Week 2)
**Deliverables**:
- Analyze and simplify manager/service/orchestrator patterns
- Create unified architecture for CLI operations
- Extract common utilities to utils/ directory
- Simplify LazyCommandLoader complexity
- Comprehensive test suite for refactored components

**Timeline**: 3 days (sequential with parallel validation)
**Agents**: Sequential design + parallel validation
**Success Criteria**: Simplified architecture, comprehensive tests, performance maintained

### Phase 4: Quality Assurance & Documentation (Week 2)
**Deliverables**:
- 100% test coverage for refactored components
- Zero linting violations (Ruff)
- Zero type checking errors (MyPy)
- Updated documentation for new file structure
- Performance benchmarks vs original implementation

**Timeline**: 2 days (parallel execution)
**Agents**: Parallel quality gates
**Success Criteria**: All quality gates pass, documentation complete, benchmarks positive

## 9. EDGE CASES & ERROR HANDLING

### Boundary Conditions
- **File size edge case**: Files exactly at 350 line limit - allow up to 375 lines for natural breakpoints
- **Import dependency cycles**: Break cycles through interface extraction or dependency injection
- **Git merge conflicts**: Use feature branch workflow with incremental commits
- **Cross-platform path handling**: Ensure Path objects used consistently throughout

### Error Scenarios
- **Functionality regression**: Automated rollback to backup branch + issue identification
- **Import errors after refactoring**: Dependency analysis tool + automatic import fixing
- **Test failures during cleanup**: Parallel debugging + isolated fix deployment
- **Performance degradation**: Profiling comparison + optimization priority queue

### Recovery Strategies
```python
# Automated recovery protocols
recovery_strategies = {
    "linting_failures": "Run ruff --fix automatically before manual review",
    "type_errors": "Run mypy with --install-types flag for missing dependencies", 
    "test_failures": "Isolate failing test + run in debug mode + specific fix",
    "import_errors": "Use isort + autoflake for automatic import cleanup",
    "functionality_loss": "Git bisect to identify breaking commit + selective revert"
}
```

## 10. ACCEPTANCE CRITERIA

### Definition of Done
- [ ] All files under 350 lines (target) or 375 lines (maximum)
- [ ] Zero linting violations (Ruff clean)
- [ ] Zero type checking errors (MyPy clean)
- [ ] unified_installer.py renamed to installer.py
- [ ] All unused imports removed
- [ ] 90%+ test coverage for refactored components
- [ ] All 8 CLI commands function identically to pre-cleanup
- [ ] Performance benchmarks equal or better than original
- [ ] Documentation updated for new file structure
- [ ] Git commit history preserved with co-author attribution

### Quality Gates
- [ ] **Automated Validation**: CI pipeline passes all checks
- [ ] **Manual Testing**: All CLI workflows tested on 3 platforms
- [ ] **Performance Testing**: Startup time <2 seconds maintained
- [ ] **Code Review**: All refactored code reviewed for SOLID principles
- [ ] **Integration Testing**: End-to-end CLI workflows validated
- [ ] **Regression Testing**: No functionality lost compared to baseline

### Validation Steps

#### Step 1: Automated Quality Validation
```bash
# Must pass before considering cleanup complete
uv run ruff check cli/ --statistics  # Must show 0 errors
uv run mypy cli/                      # Must pass with no errors
uv run pytest tests/cli/ --cov=cli --cov-report=term-missing  # Must show 90%+ coverage
```

#### Step 2: CLI Command Functionality Testing
```bash
# All commands must work identically to pre-cleanup
uvx automagik-hive --install agent
uvx automagik-hive --start agent
uvx automagik-hive --health agent  
uvx automagik-hive --status agent
uvx automagik-hive --logs agent 100
uvx automagik-hive --stop agent
uvx automagik-hive --restart agent
uvx automagik-hive --uninstall agent
```

#### Step 3: Performance Validation
```bash
# Performance must equal or exceed pre-cleanup benchmarks
time uvx automagik-hive --help     # Must be <2 seconds
time uvx automagik-hive --health agent  # Must be <5 seconds
```

#### Step 4: File Structure Validation
```bash
# Validate new file structure meets requirements
find cli/ -name "*.py" -exec wc -l {} + | awk '$1 > 375 {print "VIOLATION: " $0}'  # Must show no violations
ls -la cli/commands/installer.py   # Must exist (renamed from unified_installer.py)
ls -la cli/commands/unified_installer.py && echo "ERROR: File should not exist" || echo "SUCCESS: File removed"
```

## 11. SUCCESS METRICS SUMMARY

### Quantitative Targets
- **Lines of Code**: Reduce from 13,168 to ~9,200 (30% reduction)
- **File Size**: 0 files >375 lines (currently 7 files >700 lines)  
- **Linting Violations**: Reduce from 4 to 0 (100% improvement)
- **Test Coverage**: Achieve 90%+ for all refactored components
- **Performance**: Maintain <2 second CLI startup time
- **Classes**: Reduce from 47 to ~30 (simplification)
- **Functions**: Optimize from 451 total (complexity reduction)

### Qualitative Improvements
- **Naming Consistency**: installer.py instead of unified_installer.py
- **Code Readability**: Single-responsibility modules <350 lines
- **Maintainability**: Clear separation of concerns
- **Developer Experience**: Intuitive file organization
- **Architecture Simplicity**: Reduced manager/service/orchestrator redundancy

### Parallel Execution Benefits
- **Time Efficiency**: Complete cleanup in 2 weeks instead of 4+ weeks sequential
- **Risk Distribution**: Isolated failures don't block entire cleanup
- **Quality Assurance**: Parallel validation ensures comprehensive coverage
- **Agent Specialization**: Each agent focused on specific expertise area
- **Scalability**: Pattern applicable to future cleanup operations

---

**Implementation Ready**: This TSD provides complete specification for systematic CLI cleanup with parallel execution strategy, measurable success criteria, and comprehensive risk mitigation. All components designed for immediate agent spawning and execution.