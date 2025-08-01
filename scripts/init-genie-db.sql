-- Automagik Hive Genie Database Initialization
-- PostgreSQL initialization script for genie stack
-- Database: hive_genie (port 48532)

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS agno;
CREATE SCHEMA IF NOT EXISTS hive;

-- Set default search path
ALTER DATABASE hive_genie SET search_path TO agno, hive, public;

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

-- Genie orchestration sessions
CREATE TABLE IF NOT EXISTS hive.orchestration_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_name VARCHAR(255),
    orchestrator_type VARCHAR(50) NOT NULL, -- 'genie', 'genie-clone', etc.
    parent_session_id UUID REFERENCES hive.orchestration_sessions(id),
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'paused', 'completed', 'failed', 'cancelled')),
    context_data JSONB DEFAULT '{}',
    spawned_agents JSONB DEFAULT '[]', -- Array of spawned agent information
    task_graph JSONB DEFAULT '{}', -- Task dependency graph
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Create indexes for orchestration sessions
CREATE INDEX IF NOT EXISTS idx_orchestration_sessions_orchestrator ON hive.orchestration_sessions (orchestrator_type);
CREATE INDEX IF NOT EXISTS idx_orchestration_sessions_parent ON hive.orchestration_sessions (parent_session_id);
CREATE INDEX IF NOT EXISTS idx_orchestration_sessions_status ON hive.orchestration_sessions (status);
CREATE INDEX IF NOT EXISTS idx_orchestration_sessions_started_at ON hive.orchestration_sessions (started_at DESC);

-- Agent spawn tracking for orchestration
CREATE TABLE IF NOT EXISTS hive.agent_spawns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orchestration_session_id UUID NOT NULL REFERENCES hive.orchestration_sessions(id),
    agent_type VARCHAR(100) NOT NULL, -- e.g., 'genie-dev-coder', 'genie-testing-maker'
    spawn_context JSONB NOT NULL, -- Context preserved from parent
    task_description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('spawned', 'running', 'completed', 'failed', 'timeout')),
    result_data JSONB,
    error_message TEXT,
    spawned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    execution_time_ms INTEGER,
    metadata JSONB DEFAULT '{}'
);

-- Create indexes for agent spawns
CREATE INDEX IF NOT EXISTS idx_agent_spawns_session ON hive.agent_spawns (orchestration_session_id);
CREATE INDEX IF NOT EXISTS idx_agent_spawns_agent_type ON hive.agent_spawns (agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_spawns_status ON hive.agent_spawns (status);
CREATE INDEX IF NOT EXISTS idx_agent_spawns_spawned_at ON hive.agent_spawns (spawned_at DESC);

-- Task coordination for parallel execution
CREATE TABLE IF NOT EXISTS hive.task_coordination (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orchestration_session_id UUID NOT NULL REFERENCES hive.orchestration_sessions(id),
    task_group_id UUID NOT NULL, -- Group related parallel tasks
    task_name VARCHAR(255) NOT NULL,
    agent_spawn_id UUID REFERENCES hive.agent_spawns(id),
    dependencies JSONB DEFAULT '[]', -- Array of task IDs this task depends on
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'ready', 'running', 'completed', 'failed', 'blocked')),
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Create indexes for task coordination
CREATE INDEX IF NOT EXISTS idx_task_coordination_session ON hive.task_coordination (orchestration_session_id);
CREATE INDEX IF NOT EXISTS idx_task_coordination_group ON hive.task_coordination (task_group_id);
CREATE INDEX IF NOT EXISTS idx_task_coordination_status ON hive.task_coordination (status);
CREATE INDEX IF NOT EXISTS idx_task_coordination_priority ON hive.task_coordination (priority DESC);
CREATE INDEX IF NOT EXISTS idx_task_coordination_agent_spawn ON hive.task_coordination (agent_spawn_id);

-- Agent execution logs (same as agent stack but with orchestration context)
CREATE TABLE IF NOT EXISTS hive.agent_execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(255) NOT NULL,
    execution_id UUID NOT NULL,
    session_id UUID,
    orchestration_session_id UUID REFERENCES hive.orchestration_sessions(id),
    agent_spawn_id UUID REFERENCES hive.agent_spawns(id),
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
CREATE INDEX IF NOT EXISTS idx_agent_execution_logs_orchestration ON hive.agent_execution_logs (orchestration_session_id);
CREATE INDEX IF NOT EXISTS idx_agent_execution_logs_agent_spawn ON hive.agent_execution_logs (agent_spawn_id);
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

-- Function to auto-update task status based on dependencies
CREATE OR REPLACE FUNCTION update_task_status()
RETURNS TRIGGER AS $$
BEGIN
    -- If a task completes, check if any pending tasks can now be marked as ready
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        UPDATE hive.task_coordination 
        SET status = 'ready'
        WHERE status = 'blocked' 
        AND orchestration_session_id = NEW.orchestration_session_id
        AND NOT EXISTS (
            SELECT 1 FROM hive.task_coordination dep_task
            WHERE dep_task.id = ANY(
                SELECT jsonb_array_elements_text(dependencies)::UUID 
                FROM hive.task_coordination blocked_task 
                WHERE blocked_task.id = task_coordination.id
            )
            AND dep_task.status NOT IN ('completed')
        );
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply task status trigger
CREATE TRIGGER update_dependent_task_status
    AFTER UPDATE ON hive.task_coordination
    FOR EACH ROW EXECUTE FUNCTION update_task_status();

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Insert initial component versions for genie stack
INSERT INTO hive.component_versions (component_type, name, version, status, metadata) VALUES
    ('agent', 'genie-clone', '1.0.0', 'active', '{"description": "Fractal Genie cloning for complex orchestration"}'),
    ('agent', 'genie-dev-planner', '1.0.0', 'active', '{"description": "Development planning specialist"}'),
    ('agent', 'genie-dev-designer', '1.0.0', 'active', '{"description": "System architecture design specialist"}'),
    ('agent', 'genie-dev-coder', '1.0.0', 'active', '{"description": "Code implementation specialist"}'),
    ('agent', 'genie-dev-fixer', '1.0.0', 'active', '{"description": "Debugging and issue resolution specialist"}'),
    ('agent', 'genie-testing-maker', '1.0.0', 'active', '{"description": "Test suite creation specialist"}'),
    ('agent', 'genie-testing-fixer', '1.0.0', 'active', '{"description": "Test fixing and coverage specialist"}'),
    ('agent', 'genie-quality-ruff', '1.0.0', 'active', '{"description": "Ruff formatting and linting specialist"}'),
    ('agent', 'genie-quality-mypy', '1.0.0', 'active', '{"description": "MyPy type checking specialist"}'),
    ('agent', 'genie-claudemd', '1.0.0', 'active', '{"description": "CLAUDE.md documentation management"}'),
    ('agent', 'genie-agent-creator', '1.0.0', 'active', '{"description": "Agent creation specialist"}'),
    ('agent', 'genie-agent-enhancer', '1.0.0', 'active', '{"description": "Agent enhancement specialist"}'),
    ('team', 'development-team', '1.0.0', 'active', '{"description": "Coordinated development team workflow"}'),
    ('team', 'quality-team', '1.0.0', 'active', '{"description": "Code quality assurance team"}'),
    ('workflow', 'tdd-workflow', '1.0.0', 'active', '{"description": "Test-driven development workflow"}'),
    ('workflow', 'deployment-workflow', '1.0.0', 'active', '{"description": "Application deployment workflow"}'
)
ON CONFLICT (component_type, name) DO NOTHING;

-- Insert orchestration-focused knowledge base entries
INSERT INTO agno.knowledge_base (name, content, meta_data) VALUES
    ('orchestration-patterns', 'Multi-agent orchestration patterns and coordination strategies', '{"domain": "orchestration", "type": "documentation"}'),
    ('parallel-execution', 'Parallel task execution strategies and dependency management', '{"domain": "orchestration", "type": "documentation"}'),
    ('context-preservation', 'Context preservation techniques for fractal agent spawning', '{"domain": "orchestration", "type": "documentation"}'),
    ('task-coordination', 'Task coordination and dependency resolution patterns', '{"domain": "orchestration", "type": "documentation"}'),
    ('agent-communication', 'Inter-agent communication protocols and message passing', '{"domain": "orchestration", "type": "documentation"}')
ON CONFLICT DO NOTHING;

-- =============================================================================
-- PERMISSIONS
-- =============================================================================

-- Grant permissions to application user
GRANT ALL PRIVILEGES ON SCHEMA agno TO hive_genie;
GRANT ALL PRIVILEGES ON SCHEMA hive TO hive_genie;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agno TO hive_genie;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA hive TO hive_genie;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agno TO hive_genie;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA hive TO hive_genie;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA agno GRANT ALL ON TABLES TO hive_genie;
ALTER DEFAULT PRIVILEGES IN SCHEMA hive GRANT ALL ON TABLES TO hive_genie;
ALTER DEFAULT PRIVILEGES IN SCHEMA agno GRANT ALL ON SEQUENCES TO hive_genie;
ALTER DEFAULT PRIVILEGES IN SCHEMA hive GRANT ALL ON SEQUENCES TO hive_genie;