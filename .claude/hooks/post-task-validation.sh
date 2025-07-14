#!/bin/bash

# Post-Task Validation Hook
# Automatically validates completed tasks against specs using multi-model approach
# Called after task completion to ensure compliance with requirements

TASK_JSON="$1"
TASK_NAME=$(echo "$TASK_JSON" | jq -r '.description // "Unknown Task"')
TASK_PROMPT=$(echo "$TASK_JSON" | jq -r '.prompt // ""')

# Extract task ID/type for spec matching
TASK_ID=""
if [[ "$TASK_NAME" =~ T-([0-9]+) ]]; then
    TASK_ID="T-${BASH_REMATCH[1]}"
elif [[ "$TASK_NAME" =~ (.*):.*$ ]]; then
    TASK_ID="${BASH_REMATCH[1]}"
else
    TASK_ID="$TASK_NAME"
fi

echo "🔍 Post-Task Validation: $TASK_ID ($TASK_NAME)"

# Define spec validation based on task type
case "$TASK_ID" in
    "T-004"|*"Typification"*)
        SPEC_VALIDATION="Validate 5-level typification workflow implementation:
        - Agno workflow with Pydantic validators
        - Hierarchical Business Unit → Product → Motive → Submotive → Conclusion
        - Only valid business logic combinations allowed
        - Portuguese categories from knowledge base
        - Routes to correct agents based on classification
        - Integration with Ana router working"
        MODEL="gemini-2.5-pro"
        ;;
    "T-005"|*"Versioning"*)
        SPEC_VALIDATION="Validate agent versioning system implementation:
        - Database-driven version management (v25/v26/v27)
        - Different prompts per version supported
        - 2+ variants running simultaneously
        - A/B testing capability implemented
        - Version creation/switching working
        - Hot deployment without restarts"
        MODEL="grok-4-0709"
        ;;
    "T-006"|*"Monitoring"*)
        SPEC_VALIDATION="Validate production monitoring system implementation:
        - Real-time monitoring dashboard operational
        - Agent performance analytics working
        - System health monitoring with alerts
        - Typification and versioning analytics integrated
        - Performance metrics for all components"
        MODEL="o3"
        ;;
    *"API"*|*"api"*)
        SPEC_VALIDATION="Validate API implementation against production standards:
        - FastAPI structure with proper routing
        - Health checks and error handling
        - Portuguese error messages
        - Monitoring integration
        - Production-ready configuration"
        MODEL="gemini-2.5-pro"
        ;;
    *"Database"*|*"database"*)
        SPEC_VALIDATION="Validate database implementation:
        - PostgreSQL with PgVector support
        - Alembic migrations working
        - Connection pooling configured
        - Service layer with CRUD operations
        - Performance optimizations"
        MODEL="o3"
        ;;
    *"Infrastructure"*|*"infrastructure"*)
        SPEC_VALIDATION="Validate infrastructure implementation:
        - agno-demo-app patterns copied correctly
        - Modern FastAPI structure
        - Database integration working
        - Development scripts functional"
        MODEL="grok-4-0709"
        ;;
    *)
        SPEC_VALIDATION="General task validation:
        - Requirements met as specified
        - Integration with existing system
        - Code quality and best practices
        - Documentation updated"
        MODEL="gemini-2.5-pro"
        ;;
esac

# Create validation command with full context
VALIDATION_COMMAND="/review \"$SPEC_VALIDATION

**Task Completed**: $TASK_NAME
**Context**: You have full codebase access. Validate implementation by examining:
- Relevant code files and their actual implementation
- Integration points with existing system
- Configuration and setup files
- Test coverage and functionality

**Critical**: Use your full codebase access to verify actual implementation, not just assume requirements are met. Examine the files, test the functionality, and provide specific findings.\" model=\"$MODEL\""

echo "📋 Validation Spec: $SPEC_VALIDATION"
echo "🤖 Using Model: $MODEL"
echo "⚡ Command: $VALIDATION_COMMAND"

# Return the original JSON to continue normal processing
echo "$TASK_JSON"

# Note: The actual /review command execution should be triggered by the framework
# This hook prepares the validation but doesn't execute it to avoid blocking