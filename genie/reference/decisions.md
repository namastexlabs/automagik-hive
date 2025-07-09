# Key Decisions Log

## Database Architecture
**Decision**: Use single `pagbank.db` file with multiple tables
**Rationale**: Agno supports table_name parameter, simpler for POC
**Date**: Current session

## Directory Structure
**Decision**: Consolidate all data in `data/` directory
**Rationale**: Clean separation, easy backup, follows best practices
**Date**: Current session

## Genie Workspace
**Decision**: Implement structured framework with active/completed/reference
**Rationale**: Prevent file accumulation, maintain clean workspace
**Date**: Current session

## Priority Features
**Decision**: Move "antecipação" keywords from Credit to Digital Account team
**Rationale**: Client requirement - antecipação is account feature not credit
**Date**: Previous session

## Python Environment
**Decision**: Always use `uv run` instead of direct Python
**Rationale**: Project requirement, ensures correct environment
**Date**: Throughout project