# Forge Task Usage Cleanup Plan

## DELETIONS ✅ COMPLETED

### **Agent Files - Complete Removal:**
- ✅ `.claude/agents/genie-task-analyst.md` - DELETED

### **Forge References - Remove Entirely:**
- ✅ `genie-self-learn.md` - All 14 update_task calls and forge tool references REMOVED
- ✅ `genie-quality-ruff.md` - All update_task/get_task calls and forge tool references REMOVED  
- ✅ `genie-quality-mypy.md` - All update_task calls and forge tool references REMOVED
- ✅ `hive-release-manager.md` - Remove forge references REMOVED
- ✅ `genie-dev-planner.md` - Remove forge integration mentions REMOVED

### **Testing Agent Forge Usage - KEEP (for reporting code bugs):**
- `genie-testing-fixer.md` - Keep create_task for source code bug reporting
- `genie-testing-maker.md` - Keep task_id parameter references

## EDITS ✅ COMPLETED

### **CLAUDE.md Updates:**
- ✅ Remove `genie-task-analyst` from routing matrix - COMPLETED
- ✅ Remove `genie-task-analyst` references in zen documentation - COMPLETED
- ✅ Remove genie-task-analyst from agent lists - COMPLETED

### **Config Files - Remove Forge Tools:**
```yaml
# Remove "automagik-forge:*" from:
- ✅ ai/agents/genie-quality/config.yaml - COMPLETED
- ✅ ai/agents/genie-testing/config.yaml - COMPLETED  
- ✅ ai/agents/genie-dev/config.yaml - COMPLETED
- ✅ ai/agents/genie-debug/config.yaml - COMPLETED
- ✅ ai/workflows/template-workflow/config.yaml - COMPLETED
- ✅ ai/tools/template-tool/config.yaml - COMPLETED
- ✅ ai/teams/template-team/config.yaml - COMPLETED

# KEEP "automagik-forge:*" in:
- ✅ ai/agents/master-genie/config.yaml (user-approved task creation) - PRESERVED
- ✅ ai/teams/genie/config.yaml (orchestration) - PRESERVED
```

### **Test Files - Remove References:**
- ✅ Remove genie-task-analyst from test files in `tests/integration/` - COMPLETED

## KEEP

### **Keep Forge Tools:**
- `ai/agents/master-genie/config.yaml` - User-approved task creation
- `ai/teams/genie/config.yaml` - Orchestration
- `testing-agent-file-boundary-enforcer.py` - Boundary enforcement create_task
- `genie-testing-fixer.md` - Source code bug reporting create_task
- `genie-testing-maker.md` - Task_id parameter references
- `wish.md` - Create_task template
- `CLAUDE.md` - Parallel execution example

## FILES EDITED ✅ ALL COMPLETED

1. ✅ `.claude/agents/genie-self-learn.md` - Remove all forge content - COMPLETED
2. ✅ `.claude/agents/genie-quality-ruff.md` - Remove all forge content - COMPLETED
3. ✅ `.claude/agents/genie-quality-mypy.md` - Remove all forge content - COMPLETED  
4. ✅ `.claude/agents/hive-release-manager.md` - Remove forge references - COMPLETED
5. ✅ `.claude/agents/genie-dev-planner.md` - Remove forge mentions - COMPLETED
6. ✅ `CLAUDE.md` - Remove genie-task-analyst from routing matrix and lists - COMPLETED
7. ✅ `ai/agents/genie-quality/config.yaml` - Remove automagik-forge - COMPLETED
8. ✅ `ai/agents/genie-testing/config.yaml` - Remove automagik-forge - COMPLETED
9. ✅ `ai/agents/genie-dev/config.yaml` - Remove automagik-forge - COMPLETED
10. ✅ `ai/agents/genie-debug/config.yaml` - Remove automagik-forge - COMPLETED
11. ✅ `ai/workflows/template-workflow/config.yaml` - Remove automagik-forge - COMPLETED
12. ✅ `ai/tools/template-tool/config.yaml` - Remove automagik-forge - COMPLETED
13. ✅ `ai/teams/template-team/config.yaml` - Remove automagik-forge - COMPLETED
14. ✅ `tests/integration/workspace_protocol/test_context_ingestion.py` - Remove genie-task-analyst - COMPLETED
15. ✅ `tests/integration/workspace_protocol/test_execution_script.py` - Remove genie-task-analyst - COMPLETED
16. ✅ `tests/integration/workspace_protocol/test_artifact_lifecycle.py` - Remove genie-task-analyst - COMPLETED

## FINAL STATE

**Only forge usage:**
- Master Genie + Genie Team: create_task (user-approved orchestration)
- Testing agents: create_task (bug reporting only, no update_task)
- Testing boundary enforcer: create_task (security boundary)
- Everything else: No forge tools