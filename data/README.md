# PagBank Data Directory

This directory contains the persistent database for the PagBank Multi-Agent System POC.

## Single Database Architecture: `pagbank.db`

The entire system uses a single SQLite database with multiple tables that are automatically created on first run:

### Memory Tables
- `pagbank_memories` - Production agent memories, user context, and patterns
- `pagbank_memories_dev` - Development environment memories (same DB)
- `pagbank_memories_test` - Test environment memories (same DB)

### Core Tables
- `sessions` - User session tracking and interaction history
- `tickets` - Support ticket system for escalations
- `escalation_records` - Escalation event tracking
- `learned_patterns` - ML patterns for escalation decisions
- `escalation_outcomes` - Escalation resolution tracking

### Feedback System Tables
- `feedback_memories` - Feedback collection memories
- `feedback_storage` - Feedback entry storage
- `feedback_analysis_memories` - Analysis memories
- `human_agent_memories` - Human agent simulation memories
- `human_agent_storage` - Human agent session storage
- `conversation_memories` - Conversation context memories
- `conversation_storage` - Conversation history storage

### Demo/Playground
- `pagbank_demo_sessions` - Playground demo sessions

## Why Single Database?

For this POC:
- **Simplicity**: One file to manage, backup, and deploy
- **Efficiency**: All components share the same database connection
- **Consistency**: All data in one place, easier transactions
- **Auto-creation**: Tables are created automatically when components initialize
- **No setup required**: Just run the application and everything is created

## Data Privacy

This database contains sensitive customer interaction data and should be handled according to PagBank's data privacy policies.

## Important Notes

1. **Auto-generated**: The database and all tables are created automatically on first run
2. **Git ignored**: Database files (*.db) are not committed to version control
3. **Fresh start**: Delete `pagbank.db` to reset all data and start fresh
4. **Backup**: Simply backup the single `pagbank.db` file regularly

## Database Structure

When the application runs, it creates tables across different components:
- **Agno Memory V2**: Creates memory tables with `_memories` suffix
- **Session Manager**: Creates `sessions` table
- **Ticket System**: Creates `tickets` table
- **Pattern Learner**: Creates escalation pattern tables
- **Feedback System**: Creates feedback-related tables