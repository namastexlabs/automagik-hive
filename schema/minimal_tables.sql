-- PagBank Multi-Agent System - Minimal PostgreSQL Schema
-- Only creates custom tables. Agno will auto-create its own tables.

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User Sessions (Custom session management)
-- This is the only table we need to create manually
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    team_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    interaction_count INTEGER DEFAULT 0,
    session_context JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active, last_activity DESC);
CREATE INDEX IF NOT EXISTS idx_user_sessions_team ON user_sessions(team_id);

-- Update trigger for last_activity
CREATE OR REPLACE FUNCTION update_last_activity()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_activity = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_sessions_last_activity 
BEFORE UPDATE ON user_sessions
FOR EACH ROW 
WHEN (OLD.* IS DISTINCT FROM NEW.*)
EXECUTE FUNCTION update_last_activity();

-- Grant permissions
GRANT ALL ON user_sessions TO ai;

-- Note: The following tables will be auto-created by Agno:
-- - team_sessions (by PostgresStorage)
-- - agent_sessions (by PostgresStorage)  
-- - user_memories (by PostgresMemoryDb)
-- - ana_user_memories (by PostgresMemoryDb)