-- Automagik Hive Agent Database Initialization
-- PostgreSQL initialization script for agent stack
-- Database: hive_agent (port 35532)

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS agno;
CREATE SCHEMA IF NOT EXISTS hive;

-- Set default search path
ALTER DATABASE hive_agent SET search_path TO agno, hive, public;

-- =============================================================================
-- AGNO SCHEMA - Core Agno Framework Tables
-- =============================================================================

-- Knowledge base for RAG system (Agno framework)
CREATE TABLE IF NOT EXISTS agno.knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI ada-002 dimensions
    meta_data JSONB DEFAULT '{}',
    filters JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for vector similarity search
CREATE INDEX IF NOT EXISTS idx_knowledge_base_embedding ON agno.knowledge_base 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create indexes for metadata filtering
CREATE INDEX IF NOT EXISTS idx_knowledge_base_meta_data ON agno.knowledge_base 
    USING GIN (meta_data);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_filters ON agno.knowledge_base 
    USING GIN (filters);

-- Create index for name searches
CREATE INDEX IF NOT EXISTS idx_knowledge_base_name ON agno.knowledge_base (name);

-- =============================================================================
-- HIVE SCHEMA - Automagik Hive Component Management
-- =============================================================================

-- Component version tracking
CREATE TABLE IF NOT EXISTS hive.component_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_type VARCHAR(50) NOT NULL CHECK (component_type IN ('agent', 'team', 'workflow')),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    config_hash VARCHAR(64), -- SHA-256 hash of configuration
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'disabled')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint on component_type + name combination
    UNIQUE(component_type, name)
);

-- Create indexes for component queries
CREATE INDEX IF NOT EXISTS idx_component_versions_type ON hive.component_versions (component_type);
CREATE INDEX IF NOT EXISTS idx_component_versions_name ON hive.component_versions (name);
CREATE INDEX IF NOT EXISTS idx_component_versions_status ON hive.component_versions (status);
CREATE INDEX IF NOT EXISTS idx_component_versions_updated_at ON hive.component_versions (updated_at DESC);

-- Agent execution logs
CREATE TABLE IF NOT EXISTS hive.agent_execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(255) NOT NULL,
    execution_id UUID NOT NULL,
    session_id UUID,
    status VARCHAR(20) NOT NULL CHECK (status IN ('started', 'running', 'completed', 'failed', 'timeout')),
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    execution_time_ms INTEGER,
    memory_usage_mb INTEGER,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Create indexes for execution log queries
CREATE INDEX IF NOT EXISTS idx_agent_execution_logs_agent ON hive.agent_execution_logs (agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_execution_logs_execution_id ON hive.agent_execution_logs (execution_id);
CREATE INDEX IF NOT EXISTS idx_agent_execution_logs_session_id ON hive.agent_execution_logs (session_id);
CREATE INDEX IF NOT EXISTS idx_agent_execution_logs_status ON hive.agent_execution_logs (status);
CREATE INDEX IF NOT EXISTS idx_agent_execution_logs_started_at ON hive.agent_execution_logs (started_at DESC);

-- =============================================================================
-- FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to component_versions
CREATE TRIGGER update_component_versions_updated_at 
    BEFORE UPDATE ON hive.component_versions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Insert initial component versions for agent stack
INSERT INTO hive.component_versions (component_type, name, version, status, metadata) VALUES
    ('agent', 'template-agent', '1.0.0', 'active', '{"description": "Base template for creating new agents"}'),
    ('team', 'template-team', '1.0.0', 'active', '{"description": "Base template for creating new teams"}'),
    ('workflow', 'template-workflow', '1.0.0', 'active', '{"description": "Base template for creating new workflows"}')
ON CONFLICT (component_type, name) DO NOTHING;

-- Insert sample knowledge base entries
INSERT INTO agno.knowledge_base (name, content, meta_data) VALUES
    ('agent-development', 'Agent development patterns and best practices for Automagik Hive', '{"domain": "development", "type": "documentation"}'),
    ('testing-strategies', 'Testing approaches for multi-agent systems', '{"domain": "testing", "type": "documentation"}'),
    ('deployment-patterns', 'Deployment strategies for agent services', '{"domain": "deployment", "type": "documentation"}')
ON CONFLICT DO NOTHING;

-- =============================================================================
-- PERMISSIONS
-- =============================================================================

-- Grant permissions to application user
GRANT ALL PRIVILEGES ON SCHEMA agno TO hive_agent;
GRANT ALL PRIVILEGES ON SCHEMA hive TO hive_agent;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agno TO hive_agent;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA hive TO hive_agent;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agno TO hive_agent;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA hive TO hive_agent;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA agno GRANT ALL ON TABLES TO hive_agent;
ALTER DEFAULT PRIVILEGES IN SCHEMA hive GRANT ALL ON TABLES TO hive_agent;
ALTER DEFAULT PRIVILEGES IN SCHEMA agno GRANT ALL ON SEQUENCES TO hive_agent;
ALTER DEFAULT PRIVILEGES IN SCHEMA hive GRANT ALL ON SEQUENCES TO hive_agent;