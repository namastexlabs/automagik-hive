# /clean

---
allowed-tools: Task(*), Read(*), Bash(*), Glob(*), Grep(*), mcp__zen__*, mcp__search-repo-docs__*, mcp__ask-repo-agent__*, mcp__genie_memory__*, mcp__send_whatsapp_message__*, mcp__wait__*
description: Safely identify and remove dead code, unused files, and obsolete artifacts
---

Comprehensive dead code detection with triple-verification safety system using multiple expert agents and LLM consultation.


## ⚠️ CRITICAL SAFETY NOTICE

This command can permanently delete files. It employs:
- **Triple-verification system** with independent agents
- **Multi-LLM consensus** via Gemini consultation
- **Memory-based pattern validation**
- **WhatsApp notifications** before any deletion
- **Mandatory user confirmation** for all deletions

## Intelligent Cleanup Strategy

### Step 1: Scope Analysis
Parse user request: "$ARGUMENTS"

**Cleanup Categories:**
- **Unused Code** → Functions, classes, variables never referenced
- **Orphan Files** → Files not imported/required anywhere
- **Old Artifacts** → Backups, migrations, temporary files
- **Dead Dependencies** → Unused npm packages, imports
- **Obsolete Tests** → Tests for deleted code
- **Stale Documentation** → Docs for removed features

### Step 2: Parallel Detection Phase

Deploy 8-10 specialized detection agents in parallel:

**Wave 1: Discovery Agents (Parallel)**
```
Task: "As [Agent_Role], identify potential dead code in [assigned_area] for request '$ARGUMENTS'"

Agent 1: Import_Analyzer
- Trace all import/export relationships
- Build dependency graph
- Identify orphan files with no imports
- Find circular dependencies

Agent 2: Reference_Hunter  
- Search for function/class/variable usage
- Track method calls across codebase
- Identify unreferenced exports
- Find dead event handlers

Agent 3: Pattern_Detective
- Identify naming patterns (*.old, *.backup, *.tmp)
- Find commented-out code blocks
- Detect TODO/FIXME markers for removed features
- Locate deprecated API usage

Agent 4: Test_Validator
- Map tests to implementation files
- Find tests for non-existent code
- Identify outdated test fixtures
- Check test coverage gaps

Agent 5: Documentation_Auditor
- Cross-reference docs with code
- Find documentation for deleted features
- Identify broken links and references
- Check API doc accuracy

Agent 6: Build_Artifact_Scanner
- Check build outputs and dist folders
- Find generated files without sources
- Identify stale build configurations
- Detect unused webpack chunks

Agent 7: Git_History_Analyst
- Analyze file modification patterns
- Find files unchanged for >6 months
- Identify abandoned feature branches
- Track file deletion patterns

Agent 8: Configuration_Inspector
- Check for unused config files
- Find environment variables never read
- Identify obsolete feature flags
- Detect dead deployment configs

CRITICAL: Each agent must return:
1. List of deletion candidates with confidence scores
2. Evidence for why each file/code is dead
3. Potential risks if deleted
4. Dependencies that might break
```

### Step 3: Verification Phase

**Wave 2: Verification Agents (Parallel)**
```
After discovery agents complete, deploy verification agents:

Agent 9: Safety_Validator
- Re-check each deletion candidate
- Verify no hidden dependencies
- Check for dynamic imports/requires
- Validate against production logs

Agent 10: Business_Logic_Guardian  
- Ensure no critical business logic affected
- Check for feature flags that might activate code
- Verify no scheduled jobs depend on code
- Validate no external API contracts broken
```

### Step 4: Multi-LLM Consensus Challenge

For ALL deletions, use zen challenge for triple-verification:

```python
# CRITICAL: Use zen challenge for multi-LLM consensus on deletion safety
# This is MANDATORY for all deletion decisions due to high risk
mcp__zen__challenge(
    prompt="""CRITICAL SAFETY CHECK: Dead code analysis identified these candidates for deletion.

    Deletion Candidates:
    [List of files/code blocks with evidence]
    
    Risk Assessment:
    [Risk levels and rationale from agents]
    
    QUESTION: Is it absolutely safe to delete these files/code blocks? 
    Consider:
    1. Hidden dependencies (dynamic imports, reflection, runtime requires)
    2. External contracts (APIs, webhooks, scheduled jobs)
    3. Feature flags that might activate code
    4. Business logic that appears unused but is critical
    5. Test dependencies and build processes
    
    Respond with:
    - SAFE TO DELETE: [list] with confidence %
    - UNSAFE TO DELETE: [list] with specific reasons
    - NEEDS MANUAL REVIEW: [list] with investigation steps
    
    Be extremely conservative - when in doubt, mark as UNSAFE."""
)

# Store deletion patterns in memory
mcp__genie_memory__add_memory(
    content="PATTERN: Dead code - [Type] identified by [method] #cleanup"
)

# Search memory for previous cleanup issues
mcp__genie_memory__search_memory(
    query="FOUND cleanup deletion problems"
)

# Additional safety: Use zen consensus for critical decisions
mcp__zen__consensus(
    models=[
        {"model": "o3", "stance": "against"},     # Devil's advocate - find reasons NOT to delete
        {"model": "grok", "stance": "for"},       # Advocate for deletion
        {"model": "gemini", "stance": "neutral"}  # Neutral arbiter
    ],
    step="Evaluate deletion safety for identified dead code",
    findings="[Detailed list of candidates with all evidence]"
)
```

### Step 5: Risk Assessment Matrix

Build complete risk matrix:

```markdown
## Deletion Risk Assessment

### 🟢 Low Risk (Safe to Delete)
- No imports/exports found
- No references in codebase
- Matches known obsolete patterns
- Confirmed by all agents
- Memory shows safe deletion history

### 🟡 Medium Risk (Needs Review)
- Few or indirect references
- Might be used conditionally
- Part of deprecated feature
- Some agents disagree
- Similar deletions had issues before

### 🔴 High Risk (DO NOT DELETE)
- Any production dependency
- Dynamic imports possible
- External API contracts
- Business logic involved
- Memory shows previous problems
```

### Step 6: Staged Deletion Plan

Create careful deletion strategy:

1. **Group by risk level**
2. **Start with lowest risk**
3. **Delete in small batches**
4. **Test after each batch**
5. **Keep deletion log**
6. **Enable quick rollback**

## Critical Safety Features

### Triple-Check System
1. **Initial Detection** - Multiple agents identify candidates
2. **Verification Pass** - Safety agents re-validate
3. **Zen Challenge** - Multi-LLM debate with stance-based consensus
4. **Human Approval** - Mandatory confirmation before deletion

### Memory Integration
```python
# Before deletion - check history
mcp__genie_memory__search_memory(
    query="FOUND deletion problems [similar files]"
)

# After deletion - store outcome
mcp__genie_memory__add_memory(
    content="FOUND: Safe deletion - [files] removed without issues #cleanup"
)
```

### Real-Time Notifications
```python
# Notify before any deletion
mcp__send_whatsapp_message__send_text_message(
    instance="SofIA",
    message="⚠️ CLEANUP: Ready to delete [X] files. Review required!",
    number="5511986780008@s.whatsapp.net"
)

# Alert on high-risk findings
mcp__send_whatsapp_message__send_text_message(
    instance="SofIA",
    message="🚨 DANGER: High-risk deletion candidates found. Manual review critical!",
    number="5511986780008@s.whatsapp.net"
)
```

## Output Format

```markdown
# 🧹 Dead Code Analysis Report

## Executive Summary
- **Files Scanned**: [total]
- **Deletion Candidates**: [count]
- **Total Size**: [MB to be freed]
- **Risk Distribution**: 🟢 [X] 🟡 [Y] 🔴 [Z]

## 🟢 Safe to Delete (Low Risk)
### Orphan Files (No imports)
- `old/backup/file.js` - Last modified: 2023-01-01
  - Evidence: No imports found, matches *.backup pattern
  - Size: 15KB
  
### Unused Functions
- `utils/helpers.js::oldHelper()` - Lines 45-67
  - Evidence: No calls found, marked @deprecated
  
## 🟡 Review Recommended (Medium Risk)
### Potentially Unused Features
- `features/abandoned-feature/` - 25 files
  - Evidence: No recent commits, but config flag exists
  - Recommendation: Check if feature flag still needed

## 🔴 DO NOT DELETE (High Risk)
### Critical Dependencies
- `legacy/api-adapter.js` - Still used by external service
  - Evidence: Production logs show active usage
  
## Verification Summary
- ✅ All agents completed analysis
- ✅ Cross-validation performed
- ✅ Memory checked for patterns
- ✅ Zen challenge consensus reached
- ✅ Multi-LLM debate completed (for/against/neutral)

## Recommended Action Plan
1. Delete all green items (low risk)
2. Manual review for yellow items
3. Keep all red items
4. Run test suite after each deletion batch

## Commands to Execute
```bash
# Stage 1: Safe deletions
rm old/backup/file.js
rm tests/obsolete-test.spec.js

# Stage 2: After review
# rm features/abandoned-feature/
```
```

## Automatic Execution

```bash
# Check memory for previous cleanup patterns
mcp__genie_memory__search_memory query="PATTERN cleanup deletion $ARGUMENTS"

# Notify about cleanup start
mcp__send_whatsapp_message__send_text_message \
    instance="SofIA" \
    message="🧹 CLEANUP: Starting dead code analysis for: $ARGUMENTS" \
    number="5511986780008@s.whatsapp.net"

# For ALL cleanups, use zen challenge for safety verification
# This triggers automatic critical thinking to prevent reflexive agreement
mcp__zen__challenge \
    prompt="User wants to clean: $ARGUMENTS. Critically evaluate if this is safe and what precautions are needed."

# For major cleanups, additional consensus check
if [[ "$ARGUMENTS" =~ full|entire|all|codebase ]]; then
    mcp__zen__consensus \
        models='[{"model": "o3", "stance": "against"}, {"model": "grok", "stance": "for"}]' \
        step="Evaluate safety of large-scale dead code cleanup" \
        findings="User requested: $ARGUMENTS"
fi

# Wait for user confirmation before ANY deletion
mcp__wait__wait_minutes \
    minutes=0.1 \
    message="⏸️ Waiting for deletion approval..."
```

## Safety Protocols

1. **NEVER auto-delete** - Always require confirmation
2. **Backup everything** - Create .cleanup-backup/ before deletions
3. **Test continuously** - Run tests after each batch
4. **Log all actions** - Keep detailed deletion log
5. **Enable rollback** - Git commit before starting
6. **Monitor afterwards** - Watch for issues post-cleanup

---

**Safe Cleanup**: Triple-verified dead code removal with zero risk to your production system.