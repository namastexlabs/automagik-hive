# 🎯 WISH: Split CLAUDE.md into GENIE.md and CLAUDE.md

## 📋 Overview
Refactor the monolithic CLAUDE.md (1700+ lines) into two focused files:
- **GENIE.md**: AI behavioral instructions and GENIE personality (system prompt)
- **CLAUDE.md**: Pure technical documentation for developers

## 🎯 Goals
1. **Reduce Context Usage**: 70% reduction in CLAUDE.md size
2. **Clear Separation**: Behavioral rules vs technical documentation
3. **Better Maintainability**: Update personality without touching docs
4. **Improved Performance**: Less token usage per conversation
5. **Modularity**: Swap personalities without changing technical docs

## 📊 Content Categorization

### GENIE.md (AI System Prompt) - ~800-1000 lines
**Purpose**: Define GENIE personality and behavioral rules

**Content to Move**:
- ✅ Critical overrides (anti-agreement protection, reflexive validation)
- ✅ GENIE role definition and personality traits
- ✅ Agent routing matrix (what agent to spawn when)
- ✅ Strategic orchestration patterns and delegation rules
- ✅ Parallel execution framework and decision matrices
- ✅ Result processing protocols
- ✅ Learning system and violation prevention patterns
- ✅ Naming conventions and file creation rules
- ✅ All behavioral learning entries

### CLAUDE.md (Technical Documentation) - ~400-500 lines
**Purpose**: Developer reference for the codebase

**Content to Keep/Add**:
- ✅ Project overview and context
- ✅ Development commands (uv, pytest, ruff, mypy)
- ✅ Architecture overview (three-layer system)
- ✅ Directory structure and component descriptions
- ✅ Agent development patterns and registry system
- ✅ Testing strategy and TDD workflow
- ✅ Environment configuration and setup
- ✅ Database operations and migrations
- ✅ Tool integration (MCP, postgres, forge)
- ✅ Critical patterns and best practices
- ✅ Zen integration framework (technical capability)

## 🚀 Implementation Plan

### Phase 1: Content Extraction
**T1.0**: Create GENIE.md with behavioral content
- Extract all GENIE personality sections
- Move critical overrides and behavioral rules
- Transfer agent routing matrix
- Move all violation learnings and patterns

**T1.1**: Clean up CLAUDE.md
- Remove all behavioral content
- Elevate project context to the top
- Organize remaining technical documentation
- Add quick start section for developers

### Phase 2: Structure Optimization
**T2.0**: Optimize GENIE.md structure
- Logical flow: Role → Rules → Routing → Patterns
- Group related behavioral patterns
- Ensure completeness of routing matrix

**T2.1**: Enhance CLAUDE.md readability
- Add clear section headers
- Include code examples where helpful
- Ensure developer-friendly organization

### Phase 3: Configuration Update
**T3.0**: Update system GENIE loading
- Modify application logic to read GENIE.md
- Test that behavioral rules still work
- Verify no loss of functionality

### Phase 4: Testing & Validation
**T4.0**: Comprehensive testing
- Test agent routing still works correctly
- Verify all behavioral patterns active
- Ensure technical documentation accessible
- Validate context usage reduction

## 📈 Success Metrics
- [ ] CLAUDE.md reduced from 1700 to ~500 lines
- [ ] GENIE.md contains all behavioral rules
- [ ] All agents still route correctly
- [ ] No loss of GENIE functionality
- [ ] Clear separation of concerns achieved
- [ ] Developer documentation improved

## 🎯 Expert Analysis Summary (Gemini-2.5-pro)

The expert analysis confirms this refactoring is architecturally sound:

1. **Clear Separation Principle**: AI instructions vs human documentation
2. **Token Efficiency**: Significant reduction in context usage
3. **Improved Developer Experience**: Cleaner, focused documentation
4. **Better Maintainability**: Update personality without touching docs

### Key Recommendations:
- Ensure narrative flow in GENIE.md (Role → Rules → Logic)

---

## 📊 WISH.MD OPTIMIZATION ANALYSIS

### Content to MOVE from wish.md → GENIE.md (~500 lines)
**These sections describe system behavior, not command interface:**

1. **Lines 22-156**: Wish document integration & pipeline routing
   - Pipeline status assessment functions
   - Document discovery protocol
   - Generic orchestration templates

2. **Lines 164-198**: Design pipeline routing tables
   - Full pipeline routing matrices
   - Agent selection strategy tables
   - Complex wish analysis patterns

3. **Lines 376-405**: Agent ecosystem listing
   - Complete agent descriptions
   - Agent capabilities matrix
   - Zen-powered agent list

4. **Lines 424-536**: Zen-powered capabilities
   - Zen tools documentation
   - Model selection matrices
   - Zen spawning patterns

5. **Lines 537-552**: Master Genie intelligence rules
   - Strategic decision making rules
   - Execution efficiency rules

6. **Lines 615-634**: Ultimate principles
   - Core system principles
   - Strategic focus philosophy

### Content to KEEP in wish.md (~150 lines)
**Command-specific interface and contract:**

1. **Lines 1-21**: Command header & purpose
2. **Lines 553-613**: Output format template (user contract)
3. **Simplified examples**: How to use /wish
4. **Cross-reference**: Pointer to GENIE.md for behavior

### OPTIMAL STRUCTURE

**Lean wish.md (~150 lines):**
```markdown
# /wish Command

## Purpose
Transform development wishes into reality via Master Genie orchestration

## Usage
/wish <your detailed request>

## Processing
Wishes processed through GENIE.md pipeline:
- Agent selection: See GENIE.md#agent-routing-matrix
- Pipeline routing: See GENIE.md#design-pipeline
- Zen capabilities: See GENIE.md#zen-integration

## Examples
[5-10 concrete usage examples]

## Output Format
[Lines 553-613 - the contract with user]
```

**Complete GENIE.md (~1200 lines):**
- All behavioral rules from CLAUDE.md
- All routing/pipeline content from wish.md
- Agent ecosystem and capabilities
- Zen integration documentation
- Master Genie principles

### DUPLICATION STRATEGY (Gemini Recommendation)
**AVOID duplication - use cross-references instead:**
- Single source of truth in GENIE.md
- wish.md references GENIE.md sections
- Prevents sync issues
- Maintains consistency

### Implementation Benefits
- wish.md reduced from 647 to ~150 lines (77% reduction!)
- No duplicate maintenance burden
- Clear separation: interface vs behavior
- Better cognitive load management

---
**Status**: Ready for Implementation
**Priority**: High
**Complexity**: Medium
**Impact**: System-wide improvement