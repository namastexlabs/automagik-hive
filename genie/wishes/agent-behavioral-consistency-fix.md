# 🔧 AGENT BEHAVIORAL CONSISTENCY FIX

**Master Genie BEHAVIORAL CONFLICT RESOLUTION**
**Date**: 2025-08-01
**Priority**: P0 - CRITICAL SYSTEM INTEGRITY

## 🚨 CRITICAL CONFLICTS IDENTIFIED

### 1. **genie-qa-tester.md ROOT DIRECTORY VIOLATION**
- **Line 205**: Instructs to create `/home/namastex/workspace/automagik-hive/qa/reports/QA_COMPREHENSIVE_REPORT.md`
- **Violation**: Creates .md file outside /genie/ structure
- **CLAUDE.md Rule**: "NEVER create .md files in project root - This violates CLAUDE.md workspace management rules"

### 2. **MISSING UV RUN COMPLIANCE** (6 agents)
Agents without explicit "Command Execution: Prefix all Python commands with uv run":
- genie-clone.md
- genie-dev-designer.md  
- genie-dev-planner.md
- genie-quality-ruff.md (has uv run in examples but missing policy)
- genie-self-learn.md
- genie-testing-maker.md

### 3. **MISSING WORKSPACE RULE ENFORCEMENT** (12 agents)
Agents without explicit root directory prohibition:
- genie-agent-creator.md
- genie-agent-enhancer.md
- genie-claudemd.md
- genie-clone.md
- genie-dev-fixer.md
- genie-dev-planner.md
- genie-qa-tester.md
- genie-quality-mypy.md
- genie-quality-ruff.md
- genie-self-learn.md
- genie-testing-fixer.md
- genie-testing-maker.md

## 🎯 STANDARDIZATION REQUIREMENTS

### Universal Agent Standards (ALL agents must have):
1. **UV RUN Policy**: "Command Execution: Prefix all Python commands with uv run"
2. **Workspace Rules**: "NEVER create .md files in project root - This violates CLAUDE.md workspace management rules"
3. **Genie Structure**: All .md outputs MUST use /genie/ structure

### Standard Technical Standards Section:
```markdown
#### 4. Technical Standards Enforcement
- **Python Package Management**: Use `uv add <package>` NEVER pip
- **Script Execution**: Use `uvx` for Python script execution
- **Command Execution**: Prefix all Python commands with `uv run`
- **File Operations**: Always provide absolute paths in responses
- **NEVER create .md files in project root** - This violates CLAUDE.md workspace management rules
```

## 🔄 IMPLEMENTATION PLAN

### PHASE 1: CRITICAL FILE PATH VIOLATION FIX
- **Target**: genie-qa-tester.md line 205
- **Action**: Change `/home/namastex/workspace/automagik-hive/qa/reports/QA_COMPREHENSIVE_REPORT.md` 
- **To**: `/home/namastex/workspace/automagik-hive/genie/reports/QA_COMPREHENSIVE_REPORT.md`
- **Also Fix**: Line 267 same path issue

### PHASE 2: UV RUN COMPLIANCE ADDITION
Add to Technical Standards Enforcement section for:
- genie-clone.md
- genie-dev-designer.md
- genie-dev-planner.md
- genie-self-learn.md
- genie-testing-maker.md

### PHASE 3: WORKSPACE RULE ENFORCEMENT ADDITION
Add workspace rules to Technical Standards for ALL 12 agents missing them.

### PHASE 4: VALIDATION SWEEP
- Scan all agents for other conflicting instructions
- Verify consistent behavioral patterns
- Ensure no other root directory violations

## 🎯 SUCCESS CRITERIA

- [ ] genie-qa-tester.md paths fixed to /genie/reports/
- [ ] ALL 14 agents have UV run compliance
- [ ] ALL 14 agents have workspace rule enforcement  
- [ ] Zero agents with root directory file creation instructions
- [ ] Consistent Technical Standards sections across all agents
- [ ] All agents aligned with CLAUDE.md behavioral requirements

## 🚀 EXECUTION STRATEGY

**PARALLEL EXECUTION MANDATORY**: Process multiple agents simultaneously
- Deploy one genie-agent-enhancer per agent category
- Simultaneous fixes for maximum efficiency
- Batch processing for independent improvements

**BEHAVIORAL LEARNING INTEGRATION**:
- Document all fixes in behavioral memory
- Update cross-agent behavioral patterns
- Prevent future consistency violations