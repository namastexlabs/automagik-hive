# Epic: PagBank V2 Multi-Agent System

**Epic ID**: `epic-pagbank-v2`  
**Status**: 🔄 IN PROGRESS  
**Branch**: `epic-pagbank-v2`  
**Lead**: Platform Team  

## Epic Overview

Complete V2 rewrite of PagBank multi-agent system using Agno framework patterns. Transform POC into production-ready "agent factory" platform supporting ALL PagBank business units through YAML configuration.

## Key Objectives

- ✅ Database-driven configuration with hot reload
- ✅ Team mode=config["team"]["mode"] pattern from agno-demo-app  
- ✅ 5-level hierarchical typification workflow
- ✅ Support for Adquirência, Emissão, PagBank, Human Handoff units

## Task Cards Status (Multi-Agent Coordination)

### Phase 1: Foundation Tasks
- [ ] 📋 `pagbank-v2_phase1-refactor-ana-team.md` - Extract routing logic, implement Team patterns
- [ ] 📋 `pagbank-v2_phase1-database-infrastructure.md` - PostgreSQL setup with PgVector  
- [ ] 📋 `pagbank-v2_phase1-base-api-structure.md` - FastAPI with playground
- [ ] 📋 `pagbank-v2_phase1-migrate-agents.md` - Move specialists to new structure

### Phase 2: Platform Core
- [ ] 📋 `pagbank-v2_phase2-agent-versioning.md` - Version management system
- [ ] 📋 `pagbank-v2_phase2-typification-workflow.md` - 5-level hierarchical categorization

### Phase 3: Production Features  
- [ ] 📋 `pagbank-v2_phase3-enhanced-monitoring.md` - Advanced monitoring and analytics

### Support Tasks
- [ ] 📋 `pagbank-v2_review-epic-v2-transformation.md` - Complete epic review guide
- [ ] 🔄 `pagbank-v2_project-status.md` - Central status tracking
- [ ] 🔄 `pagbank-v2_phase1-review-and-refinement.md` - Phase 1 refinement
- [ ] 🔄 `pagbank-v2_versioning-architecture.md` - Version architecture design

### Status Icons for Agent Coordination
- [ ] 📋 **TODO** - Available to pick up (in `genie/todo/`)
- [ ] 🔄 **IN PROGRESS** - Agent working on it (in `genie/active/`)
- [ ] ⏳ **BLOCKED** - Waiting for dependency
- [ ] 🔍 **REVIEW** - Ready for review/testing
- [ ] ✅ **DONE** - Completed and archived

### Multi-Agent Workflow
1. **Pick Task**: Agent changes `[ ] 📋` to `[🔄] 🔄` and moves file to active/
2. **Block Others**: Other agents see task is in progress, pick available `[ ] 📋` tasks  
3. **Dependencies**: Use `[⏳] ⏳` when blocked by another task
4. **Complete**: Change to `[✅] ✅` and move file to archive/
5. **Unblock**: Other agents see completion, can now pick dependent tasks

### Example Status Updates
```markdown
# Agent 1 starts ana team refactor
- [🔄] 🔄 `pagbank-v2_phase1-refactor-ana-team.md` - Extract routing logic, implement Team patterns

# Agent 2 sees it's taken, picks database task  
- [🔄] 🔄 `pagbank-v2_phase1-database-infrastructure.md` - PostgreSQL setup with PgVector

# Agent 3 blocked by database dependency
- [⏳] ⏳ `pagbank-v2_phase1-migrate-agents.md` - Move specialists to new structure

# Agent 1 completes, unblocks migration
- [✅] ✅ `pagbank-v2_phase1-refactor-ana-team.md` - Extract routing logic, implement Team patterns
- [🔄] 🔄 `pagbank-v2_phase1-migrate-agents.md` - Move specialists to new structure (Agent 3)
```

## Epic Rules

1. **Single Branch**: All work happens in existing `v2` branch
2. **Task Card Movement**: Tasks move through todo → active → archive
3. **WIP Limit**: Max 5 task cards in active at any time
4. **Checkpoint Commits**: Commit frequently after each task card completion
5. **Revert Strategy**: Individual task cards can be reverted via git commits
6. **Pattern Extraction**: Save reusable patterns to `genie/reference/`

## Dependencies & Blockers

### Phase 1 Dependencies
- `pagbank-v2_phase1-database-infrastructure.md` → Required for agent migration
- `pagbank-v2_phase1-base-api-structure.md` → Required for versioning system
- `pagbank-v2_phase1-refactor-ana-team.md` → Can start immediately (no blockers)
- `pagbank-v2_phase1-migrate-agents.md` → Depends on database + ana team refactor

### Phase 2 Dependencies  
- `pagbank-v2_phase2-agent-versioning.md` → Depends on base API structure
- `pagbank-v2_phase2-typification-workflow.md` → Depends on migrated agents

### Phase 3 Dependencies
- `pagbank-v2_phase3-enhanced-monitoring.md` → Depends on all previous phases

### Agent Assignment Strategy
- **5 Agents Max**: Respect WIP limit in active/
- **Parallel Work**: Phase 1 tasks can run in parallel
- **Sequential Phases**: Phase 2 starts after Phase 1 complete
- **Real-time Updates**: All agents watch epic file for status changes

## Dependencies

- Agno framework patterns from `genie/reference/agno-*.md`
- Database schema from `genie/reference/database-schema.md`  
- YAML configuration patterns from `genie/reference/yaml-configuration.md`

## V2 Branch Workflow

```bash
# Work directly in v2 branch
git checkout v2

# Start task card
mv genie/todo/pagbank-v2/phase1-refactor-ana-team.md \
   genie/active/pagbank-v2/

# Work on task card...
# Make incremental commits during development
git add .
git commit -m "feat(ana-team): implement Team routing pattern

Co-Authored-By: Automagik Genie <genie@namastex.ai>"

# Complete task card - checkpoint commit
git add .
git commit -m "✅ Complete phase1-refactor-ana-team

- Ana team now uses Team mode=config pattern
- Routing logic extracted from orchestrator  
- All specialists defined and tested
- Ready for phase1-database-infrastructure

Co-Authored-By: Automagik Genie <genie@namastex.ai>"

# Archive completed task
mv genie/active/pagbank-v2/phase1-refactor-ana-team.md genie/archive/
```

## Success Criteria

- [ ] All PagBank business units supported
- [ ] YAML-driven configuration working
- [ ] 5-level typification implemented
- [ ] Production-ready monitoring
- [ ] Zero backwards compatibility (clean V2)

---

**Navigation**: 
- Task Cards: `genie/todo/${CURRENT_EPIC}_*.md` and `genie/active/${CURRENT_EPIC}_*.md`
- Patterns: `genie/reference/`
- Central Status: `genie/active/epic-status.md`