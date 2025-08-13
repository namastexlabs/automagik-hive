# File Management Rules - Complete Extraction from CLAUDE.md

## 📍 All File Management Rules Found

### Location 1: Lines 37-40 (Critical Constraints)
```
- **NEVER create files unless they're absolutely necessary** for achieving your goal
- **ALWAYS prefer editing an existing file** to creating a new one  
- **NEVER proactively create documentation files** (*.md) or README files unless explicitly requested
- **Do what has been asked; nothing more, nothing less**
```

### Location 2: Lines 923-926 (Critical Reminders)
```
- Do what has been asked; nothing more, nothing less
- NEVER create files unless they're absolutely necessary for achieving your goal
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files (*.md) or README files unless explicitly requested
```

### Location 3: Line 438 (Development Standards)
```
- **🎯 KISS Principle**: Simplify over-engineered components, eliminate redundant layers
```

### Location 4: Line 439 (Development Standards)
```
- **No Mocking/Placeholders**: Never mock, use placeholders, hardcode, or omit code
```

### Location 5: Lines 449-454 (File Organization & Modularity)
```
- **Small Focused Files**: Default to multiple small files (<350 lines) rather than monolithic ones
- **Single Responsibility**: Each file should have one clear purpose
- **Separation of Concerns**: Separate utilities, constants, types, components, and business logic
- **Composition Over Inheritance**: Use inheritance only for true 'is-a' relationships
- **Clear Structure**: Follow existing project structure, create new directories when appropriate
- **Proper Imports/Exports**: Design for reusability and maintainability
```

### Location 6: Lines 879-886 (Genie Workspace Management)
```
- **GENIE WORKSPACE MANAGEMENT**: `/genie/` is Genie's autonomous thinking space with KISS organization
  - **File Organization Pattern**: misplaced folders must move to proper `/genie/` structure
  - **Anti-Proliferation Rule**: ONE wish = ONE document in `/genie/wishes/`, refine in place
  - **Proper Structure**: reports/ (findings), experiments/ (prototypes), ideas/ (brainstorms), knowledge/ (wisdom), wishes/ (plans)
  - **🚨 ROOT-LEVEL .md PROHIBITION**: NEVER create .md files in project root - ALL documentation MUST use /genie/ structure
  - **MANDATORY PRE-CREATION VALIDATION**: ALL agents must validate workspace rules before creating any .md file
  - **BEHAVIORAL LEARNING INTEGRATION**: Violations trigger immediate cross-agent behavioral updates
  - **PERSONAL VIOLATION MEMORY**: I violated this rule by creating modular-deployment-plan.md in root - MOVED to /genie/wishes/ - NEVER REPEAT
```

### Location 7: Lines 887-892 (Naming Convention Rules)
```
- **🚨 CRITICAL NAMING CONVENTION VIOLATION LEARNED**: ABSOLUTE PROHIBITION on "fixed", "improved", "updated", etc. in file/function names
- **USER FEEDBACK**: "its completly forbidden, across all codebase, to write files and functionsm etc, with fixed, etc"
- **BEHAVIORAL ENFORCEMENT**: ALL agents MUST validate naming conventions before ANY file/function creation
- **NAMING PRINCIPLE**: Clean, descriptive names that reflect PURPOSE, not modification status
- **FORBIDDEN PATTERNS**: fixed, improved, updated, better, new, v2, _fix, _v
- **VALIDATION REQUIREMENT**: Pre-creation naming validation MANDATORY across all agents
```

---

## 🎯 UNIFIED FILE MANAGEMENT INSTRUCTION

### **MANDATORY FILE MANAGEMENT RULES - ABSOLUTE OVERRIDE**

#### Core Principles
1. **DO EXACTLY WHAT IS ASKED - NOTHING MORE, NOTHING LESS**
2. **NEVER CREATE FILES** unless absolutely necessary for achieving the goal
3. **ALWAYS PREFER EDITING** existing files over creating new ones

#### File Creation Restrictions
- **NEVER proactively create documentation files** (*.md) or README files unless explicitly requested
- **NEVER create .md files in project root** - ALL documentation MUST use `/genie/` structure
- **MANDATORY PRE-CREATION VALIDATION**: Validate workspace rules before ANY file creation

#### File Organization Standards
- **Small Focused Files**: Default to multiple small files (<350 lines) rather than monolithic ones
- **Single Responsibility**: Each file should have one clear purpose
- **Separation of Concerns**: Separate utilities, constants, types, components, and business logic
- **Clear Structure**: Follow existing project structure, create new directories when appropriate
- **Proper Imports/Exports**: Design for reusability and maintainability
- **Composition Over Inheritance**: Use inheritance only for true 'is-a' relationships

#### Genie Workspace Structure (`/genie/`)
- **Organization Pattern**: `/genie/` is the autonomous thinking space with KISS organization
- **Anti-Proliferation Rule**: ONE wish = ONE document in `/genie/wishes/`, refine in place
- **Directory Structure**:
  - `reports/` - findings and analysis
  - `experiments/` - prototypes and tests
  - `ideas/` - brainstorms and concepts
  - `knowledge/` - wisdom and learnings
  - `wishes/` - plans and specifications
- **Misplaced Content**: Move any misplaced folders to proper `/genie/` structure

#### Naming Conventions (ABSOLUTE PROHIBITION)
- **FORBIDDEN PATTERNS**: `fixed`, `improved`, `updated`, `better`, `new`, `v2`, `_fix`, `_v`, or any variation
- **NAMING PRINCIPLE**: Clean, descriptive names that reflect PURPOSE, not modification status
- **VALIDATION REQUIREMENT**: Pre-creation naming validation MANDATORY across all operations

#### Code Quality Standards
- **KISS Principle**: Simplify over-engineered components, eliminate redundant layers
- **No Mocking/Placeholders**: Never mock, use placeholders, hardcode, or omit code
- **Complete Implementation**: Always provide full, working code

#### Behavioral Enforcement
- **Violations trigger immediate cross-agent behavioral updates**
- **Personal violation memory maintained to prevent repetition**
- **All agents must validate against these rules before file operations**

---

## 📊 Summary

**Total Unique Rules Found**: 23 distinct file management instructions
**Redundancy Level**: High (4x repetition of core rules)
**Recommendation**: Replace all instances with single unified instruction above