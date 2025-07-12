#!/usr/bin/env python3
"""
Aggressive cleanup of genie folder for V2 refactor.
Removes all POC-era files, keeping only V2-relevant content.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Base genie directory
GENIE_DIR = Path("/home/namastex/workspace/pagbank-multiagents/genie")

# Files to DELETE (POC-era, no longer needed)
FILES_TO_DELETE = [
    # Old completed files from POC implementation
    "completed/knowledge_system_fix_plan.md",
    "completed/refined-gap-analysis.md",
    "completed/refactor_plan.md",
    "completed/pagbank-final-action-items.md",
    "completed/pagbank-integration-plan.md",
    "completed/postgres-migration-plan.md",
    "completed/postgres-tables-analysis.md",
    "completed/task1_folder_structure_standardization.md",
    "completed/task2_prompt_separation.md",
    "completed/task3_simplify_to_single_agents.md",
    "completed/task4_remove_text_normalization.md",
    "completed/task5_simplify_frustration_detection.md",
    "completed/task6_human_handoff_agent.md",
    "completed/task7_update_documentation.md",
    "completed/CLAUDE.md",  # Old version
    "completed/README.md",   # Old version
    
    # All POC phase completions
    "completed/completed/PHASE_1_COMPLETE.md",
    "completed/completed/PHASE_2_COMPLETE.md",
    "completed/completed/PHASE_3_COMPLETE.md",
    "completed/completed/TEAM_FRAMEWORK_COMPLETE.md",
    "completed/completed/ORCHESTRATOR_IMPLEMENTATION.md",
    "completed/completed/ESCALATION_SYSTEMS_COMPLETE.md",
    "completed/completed/agent_g_specialist_teams_complete.md",
    "completed/completed/task-specialist-teams-complete.md",
    "completed/completed/task-memory-validation.md",
    "completed/completed/task-model-usage-audit.md",
    "completed/completed/task-orchestration-improvements.md",
    "completed/completed/task-playground-deployment.md",
    "completed/completed/task-team-coordination-review.md",
    "completed/completed/task-test-coverage-analysis.md",
    "completed/completed/task-imports-dependencies-review.md",
    "completed/completed/todo-review-agno-compliance.md",
    "completed/completed/todo-review-dead-code.md",
    "completed/completed/todo-review-imports-dependencies.md",
    "completed/completed/todo-review-knowledge-base.md",
    "completed/completed/todo-review-memory-integration.md",
    "completed/completed/todo-review-model-usage.md",
    "completed/completed/todo-review-team-coordination.md",
    "completed/completed/todo-review-test-coverage.md",
    
    # Old phase reviews
    "completed/phases/PHASE_1_REVIEW.md",
    
    # Old reports from POC
    "completed/reports/FINAL_ORGANIZATION_COMPLETE.md",
    "completed/reports/INFRASTRUCTURE_REPORT.md",
    "completed/reports/ORGANIZATION_PLAN.md",
    "completed/reports/agno-compliance-fixes-applied.md",
    "completed/reports/agno-compliance-report.md",
    "completed/reports/dead-code-analysis-report.md",
    "completed/reports/orchestration-failure-analysis.md",
    "completed/reports/team-session-state-fixes-applied.md",
    "completed/reports/test_coverage_summary.md",
    
    # Old archive files (POC planning)
    "completed/archive/knowledge.md",
    "completed/archive/orchestration-plan.md",
    "completed/archive/pagbank_agents_detailed.md",
    "completed/archive/pagbank_demo_interaction.md",
    "completed/archive/pagbank_knowledge_structure.md",
    "completed/archive/pagbank_session_state.md",
    "completed/archive/pagbank_strategic_recommendations.md",
    "completed/archive/plan-pagbank-multiagent.md",
    "completed/archive/project.md",
    "completed/archive/team-session-state-fix-plan.md",
    "completed/archive/todo_action_agents.md",
    "completed/archive/todo_demo_environment.md",
    "completed/archive/todo_knowledge_base.md",
    "completed/archive/todo_main_orchestrator.md",
    "completed/archive/todo_memory_system.md",
    "completed/archive/todo_specialist_teams.md",
    
    # Old reference files not needed for V2
    "reference/agno-app-modes.md",  # Generic, not specific to our V2
    "reference/compliance-rules.md",  # Old POC rules
    "reference/context.md",  # Vague old file
    "reference/decisions.md",  # Old POC decisions
    "reference/demo-ready.md",  # POC demo prep
    "reference/integration-examples.md",  # Old POC examples
    "reference/pagbank_processing_instructions.md",  # POC instructions
    "reference/priorities.md",  # Old POC priorities
]

# Directories to remove entirely
DIRS_TO_DELETE = [
    "completed/completed",  # Nested duplicate
    "completed/phases",     # Old phase tracking
    "completed/reports",    # Old POC reports
    "completed/archive",    # Old POC archives
]

# Files to KEEP (V2 relevant)
FILES_TO_KEEP = [
    # Active V2 work
    "active/project-status.md",
    "active/agent-coordination.md",
    
    # V2 platform strategy (already moved)
    "completed/2025-01-12-platform-strategy.md",
    
    # Reference files for V2
    "reference/agno-patterns.md",
    "reference/routing-patterns.md",
    "reference/database-schema.md",
    "reference/context-search-tools.md",
    "reference/csv_typification_analysis.md",
    "reference/typification_hierarchy_analysis.md",
    
    # Scripts
    "scripts/split_strategy_to_tasks.py",
    "scripts/clean_task_cards.py",
    "scripts/organize_genie_files.py",
    
    # Task cards (all of them)
    # Listed pattern: task-cards/**/*.md
    
    # Genie framework docs
    "CLAUDE.md",
]

def cleanup():
    """Execute aggressive cleanup"""
    deleted_files = []
    deleted_dirs = []
    errors = []
    
    # Delete directories first
    for dir_path in DIRS_TO_DELETE:
        full_path = GENIE_DIR / dir_path
        if full_path.exists() and full_path.is_dir():
            try:
                shutil.rmtree(full_path)
                deleted_dirs.append(dir_path)
                print(f"✓ Deleted directory: {dir_path}")
            except Exception as e:
                errors.append(f"Failed to delete {dir_path}: {e}")
    
    # Delete individual files
    for file_path in FILES_TO_DELETE:
        full_path = GENIE_DIR / file_path
        if full_path.exists():
            try:
                full_path.unlink()
                deleted_files.append(file_path)
                print(f"✓ Deleted: {file_path}")
            except Exception as e:
                errors.append(f"Failed to delete {file_path}: {e}")
    
    # Remove empty directories
    for root, dirs, files in os.walk(GENIE_DIR, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    print(f"✓ Removed empty directory: {dir_path.relative_to(GENIE_DIR)}")
            except:
                pass
    
    # Create summary
    summary = f"""
# V2 Cleanup Summary

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Deleted Directories ({len(deleted_dirs)})
{chr(10).join(f'- {d}' for d in deleted_dirs)}

## Deleted Files ({len(deleted_files)})
{chr(10).join(f'- {f}' for f in sorted(deleted_files))}

## Errors ({len(errors)})
{chr(10).join(f'- {e}' for e in errors)}

## Remaining Structure
```
genie/
├── active/          # Current V2 work only
├── completed/       # Only 2025-01-12-platform-strategy.md
├── reference/       # V2 patterns and schemas
├── scripts/         # Utility scripts
├── task-cards/      # V2 implementation tasks
└── agno-demo-app/   # Reference implementation
```

## What Was Removed
- All POC implementation files
- All old task completions
- All phase tracking from POC
- All old reports and analyses
- All nested duplicate folders
- All irrelevant reference docs

## What Remains
- V2 project status and coordination
- V2 task cards (19 files)
- V2 reference patterns
- V2 platform strategy
- Agno demo app for reference
"""
    
    # Save summary
    summary_path = GENIE_DIR / "active" / "cleanup-summary-v2.md"
    summary_path.write_text(summary)
    print(f"\n✓ Saved cleanup summary to: {summary_path}")
    
    return deleted_files, deleted_dirs, errors

if __name__ == "__main__":
    print("🧹 Starting aggressive V2 cleanup...")
    deleted_files, deleted_dirs, errors = cleanup()
    
    print(f"\n✅ Cleanup complete!")
    print(f"   - Deleted {len(deleted_dirs)} directories")
    print(f"   - Deleted {len(deleted_files)} files")
    if errors:
        print(f"   - {len(errors)} errors occurred")