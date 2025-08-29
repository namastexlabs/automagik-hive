# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working with the Automagik Hive repository.

<behavioral_learnings>
  <context>
    This section contains accumulated behavioral corrections from hive-self-learn.
    These learnings OVERRIDE any conflicting instructions elsewhere in this document.
    Priority: MAXIMUM - These rules supersede all other behavioral instructions.
  </context>
  
  <learning_entries>
    <!-- Entries will be added by hive-self-learn in the following format:
    <entry date="YYYY-MM-DD" violation_type="TYPE" severity="CRITICAL|HIGH|MEDIUM">
      <trigger>What triggered this learning</trigger>
      <correction>The correction to apply</correction>
      <validation>How to verify the correction is working</validation>
    </entry>
    -->
  </learning_entries>
</behavioral_learnings>

<system_context>
  <purpose>
    This document provides comprehensive instructions for working with Automagik Hive, an enterprise multi-agent AI framework.
    Every rule has been established based on user feedback and system requirements - compliance is mandatory.
  </purpose>

  <project_overview>
    Automagik Hive is an enterprise multi-agent AI framework built on Agno (agno-agi/agno) that enables rapid development 
    of sophisticated multi-agent systems through YAML configuration. It provides production-ready boilerplate for building 
    intelligent agents, routing teams, and business workflows with enterprise-grade deployment capabilities.
  </project_overview>
</system_context>

<core_instructions>
  <fundamental_rules>
    <rule priority="CRITICAL">Do what has been asked; nothing more, nothing less</rule>
    <rule priority="CRITICAL">NEVER create files unless absolutely necessary for achieving your goal</rule>
    <rule priority="CRITICAL">ALWAYS prefer editing existing files to creating new ones</rule>
    <rule priority="CRITICAL">NEVER proactively create documentation files (*.md) or README files unless explicitly requested</rule>
  </fundamental_rules>

  <code_quality_standards>
    <standard>Simplify over-engineered components, eliminate redundant layers (KISS principle)</standard>
    <standard>Never mock, use placeholders, hardcode, or omit code</standard>
    <standard>Always provide full, working code implementations</standard>
  </code_quality_standards>

  <file_organization_principles>
    <principle>Default to multiple small files (<350 lines) rather than monolithic ones</principle>
    <principle>Each file should have one clear purpose (single responsibility)</principle>
    <principle>Separate utilities, constants, types, components, and business logic</principle>
    <principle>Follow existing project structure, create new directories when appropriate</principle>
    <principle>Design for reusability and maintainability with proper imports/exports</principle>
    <principle>Use inheritance only for true 'is-a' relationships (composition over inheritance)</principle>
  </file_organization_principles>
</core_instructions>

<workspace_structure>
  <genie_workspace>
    <context>
      The /genie/ directory is the autonomous thinking space with streamlined WISHES-CENTRIC architecture.
      This structure ensures organized planning and prevents document proliferation.
    </context>
    
    <strict_rules>
      <rule>wishes/ = CENTRAL HUB for all active planning, agent coordination, and implementation workflows</rule>
      <rule>ONE wish = ONE document in /genie/wishes/, refine in place with DEATH TESTAMENT completion</rule>
      <rule>reports/ folder ELIMINATED - replaced by DEATH TESTAMENT structured final reports embedded in wishes/</rule>
      <rule>Move any misplaced folders to proper /genie/ structure with wishes/ as primary focus</rule>
    </strict_rules>
    
    <directory_structure>
      <dir name="wishes">PRIMARY - all active planning & execution with /wish command integration</dir>
      <dir name="ideas">brainstorms and concepts</dir>
      <dir name="experiments">prototypes and tests</dir>
      <dir name="knowledge">wisdom and learnings</dir>
    </directory_structure>
  </genie_workspace>
</workspace_structure>

<critical_behavioral_rules>
  <enforcement_context>
    These rules prevent critical system violations based on user feedback.
    Violations trigger immediate cross-agent behavioral updates and are maintained in personal violation memory.
    All agents must validate against these rules before file operations.
  </enforcement_context>

  <time_estimation_prohibition severity="CRITICAL">
    <context>
      USER FEEDBACK VIOLATION: Master Genie and agents creating 6-week plans, Week 1 timelines, etc.
      We are execution engines working in minutes/seconds, NOT project managers.
    </context>
    
    <absolute_rules>
      <rule>ALL agents MUST NEVER estimate human implementation time</rule>
      <rule>NO agent will estimate weeks, days, hours, or any human temporal predictions</rule>
    </absolute_rules>
    
    <forbidden_patterns>
      <pattern>"Week 1", "6-week plan", "over 2 weeks" estimations</pattern>
      <pattern>"3 days", "within a week", "daily" timeline predictions</pattern>
      <pattern>"8 hours", "full day", temporal work estimates</pattern>
      <pattern>Any timeline or schedule creation for human implementation</pattern>
    </forbidden_patterns>
    
    <acceptable_alternatives>
      <alternative>Use "Phase 1", "Phase 2", "Initial Implementation", "Core Development"</alternative>
      <alternative>We execute in minutes/seconds through agent orchestration</alternative>
      <alternative>All wish documents MUST include explicit subagent execution strategies</alternative>
      <alternative>Define which agents handle each implementation phase</alternative>
      <alternative>Planning documents MUST include mandatory "Orchestration Strategy" section</alternative>
    </acceptable_alternatives>
    
    <enforcement>
      <action>Any time estimation triggers automatic hive-self-learn deployment</action>
      <action>Time estimation = CRITICAL VIOLATION requiring immediate behavioral update</action>
      <action>Time estimation prohibition must propagate to ALL hive agents</action>
    </enforcement>
  </time_estimation_prohibition>

  <uv_compliance_requirement severity="CRITICAL">
    <context>
      USER FEEDBACK VIOLATION: "violation, the testing maker isnt uving uv run"
      UV is the mandated package manager for ALL Python operations.
    </context>
    
    <absolute_rules>
      <rule>ALL testing agents MUST use `uv run` for Python commands</rule>
      <rule>NEVER use python directly - Always use `uv run` for ALL Python commands</rule>
      <rule>NO testing agent will use direct `pytest`, `python`, or `coverage` commands</rule>
    </absolute_rules>
    
    <required_usage>
      <command>Testing agents MUST use `uv run pytest` for ALL test execution</command>
      <command>Testing agents MUST use `uv run coverage` for ALL coverage reporting</command>
      <command>Testing agents MUST use `uv run python` for ALL Python execution</command>
    </required_usage>
    
    <enforcement>
      <action>Update ALL testing agents with UV compliance requirements</action>
      <action>Any direct command usage = CRITICAL VIOLATION requiring immediate behavioral update</action>
      <action>UV compliance requirements must propagate to ALL new testing agents</action>
    </enforcement>
  </uv_compliance_requirement>

  <pyproject_protection severity="CRITICAL">
    <context>
      USER FEEDBACK VIOLATION: "hive-testing-fixer bypassed protection hooks and destroyed project dependencies"
      pyproject.toml is SACRED - Only UV commands can modify dependencies.
    </context>
    
    <absolute_rules>
      <rule>ALL agents MUST NEVER modify pyproject.toml file</rule>
      <rule>NO agent will directly edit, write, or modify pyproject.toml under ANY circumstances</rule>
      <rule>pyproject.toml file is READ-ONLY for all agents</rule>
    </absolute_rules>
    
    <forbidden_actions>
      <action>Direct editing of pyproject.toml file</action>
      <action>Replacing dependencies with "automagik-hive>=0.1.0"</action>
      <action>Any attempt to circumvent pyproject.toml protection</action>
      <action>Removing or replacing legitimate project dependencies</action>
    </forbidden_actions>
    
    <proper_approach>
      <approach>ALL agents MUST use UV commands ONLY for dependency changes</approach>
      <approach>ALL agents MUST respect protection mechanisms without exception</approach>
      <approach>Configuration files are PROTECTED from direct agent modification</approach>
    </proper_approach>
    
    <enforcement>
      <action>Any pyproject.toml modification triggers CRITICAL hive-self-learn deployment</action>
      <action>pyproject.toml modification = SYSTEM INTEGRITY VIOLATION requiring immediate termination</action>
      <action>pyproject.toml protection must propagate to ALL hive agents with EMERGENCY protocols</action>
    </enforcement>
  </pyproject_protection>
</critical_behavioral_rules>

<configuration_management>
  <install_command_design>
    <context>
      The --install command manages .env files intelligently to handle deployment automation.
    </context>
    
    <workflow>
      <step>If .env exists with credentials: use existing credentials</step>
      <step>If .env exists but missing/placeholder credentials: generate and update .env</step>
      <step>If .env doesn't exist: generate from .env.example as base with real credentials</step>
    </workflow>
    
    <principles>
      <principle>Environment file management is part of installation/setup process</principle>
      <principle>Runtime application code reads environment variables, installation code manages them</principle>
      <principle>Installation commands handle environment setup for deployment automation</principle>
      <principle>Clear separation between setup-time and runtime configuration management</principle>
    </principles>
  </install_command_design>

  <configuration_architecture>
    <context>
      STRICT separation between application-level (.env) and infrastructure-level (docker-compose.yml) configuration.
    </context>
    
    <env_file_rules>
      <rule>Application runtime configuration ONLY - database URLs, API keys, app settings</rule>
      <rule>NEVER include in .env/.env.example files: POSTGRES_UID, POSTGRES_GID, port mappings for Docker</rule>
    </env_file_rules>
    
    <docker_compose_rules>
      <rule>Container orchestration configuration ONLY - user permissions, port mappings, volume mounts</rule>
      <rule>Infrastructure variables belong ONLY in docker-compose.yml with ${VAR:-default} pattern</rule>
      <rule>Use shell environment or docker-compose.override.yml for infrastructure overrides</rule>
    </docker_compose_rules>
  </configuration_architecture>
</configuration_management>

<project_architecture>
  <exploration_command>
    ```bash
    # Use this tree command to explore the entire codebase structure
    tree -I '__pycache__|.git|*.pyc|.venv|data|logs|.pytest_cache|*.egg-info|node_modules|.github|genie|scripts|common|docs|alembic' -P '*.py|*.yaml|*.yml|*.toml|*.md|Makefile|Dockerfile|*.ini|*.sh|*.csv|*.json' --prune -L 4
    ```
  </exploration_command>

  <architecture_map>
    ```
    🧭 NAVIGATION ESSENTIALS
    ├── pyproject.toml              # Project dependencies (managed via UV)
    
    🤖 MULTI-AGENT CORE (Start Here for Agent Development)
    ├── ai/
    │   ├── agents/registry.py      # 🏭 Agent factory - loads all agents
    │   │   └── template-agent/     # 📋 Copy this to create new agents
    │   ├── teams/registry.py       # 🏭 Team factory - routing logic
    │   │   └── template-team/      # 📋 Copy this to create new teams  
    │   └── workflows/registry.py   # 🏭 Workflow factory - orchestration
    │       └── template-workflow/  # 📋 Copy this to create new workflows
    
    🌐 API LAYER (Where HTTP Meets Agents)
    ├── api/
    │   ├── serve.py                # 🚀 Production server (Agno FastAPIApp)
    │   ├── main.py                 # 🛝 Dev playground (Agno Playground)
    │   └── routes/v1_router.py     # 🛣️ Main API endpoints
    
    📚 SHARED SERVICES (The Foundation)
    ├── lib/
    │   ├── config/settings.py      # 🎛️ Global configuration hub
    │   ├── knowledge/              # 🧠 CSV-based RAG system
    │   │   ├── knowledge_rag.csv   # 📊 Data goes here
    │   │   └── csv_hot_reload.py   # 🔄 Hot reload magic
    │   ├── auth/service.py         # 🔐 API authentication
    │   ├── utils/agno_proxy.py     # 🔌 Agno framework integration
    │   └── versioning/             # 📦 Component version management
    
    🧪 TESTING (TODO: Not implemented yet - create tests/scenarios/ for new features)
    ```
  </architecture_map>

  <component_guides>
    For detailed implementation guidance, see component-specific CLAUDE.md files:
    - ai/CLAUDE.md - Multi-agent system orchestration
    - api/CLAUDE.md - FastAPI integration patterns  
    - lib/config/CLAUDE.md - Configuration management
    - lib/knowledge/CLAUDE.md - Knowledge base management
    - tests/CLAUDE.md - Testing patterns
  </component_guides>
</project_architecture>

<development_methodology>
  <test_driven_development>
    <context>
      Follow the red-green-refactor cycle for all feature development to ensure quality and test coverage.
    </context>
    
    <workflow>
      <step order="1" phase="RED">Spawn testing-maker for failing tests</step>
      <step order="2" phase="GREEN">Spawn dev-coder to implement minimal code to make tests pass</step>
      <step order="3" phase="REFACTOR">Coordinate quality improvements while keeping tests green</step>
    </workflow>
    
    <commands>
      ```bash
      # 1. RED: Create failing tests first
      Task(subagent_type="hive-testing-maker", prompt="Create failing test suite for [feature]")
      
      # 2. GREEN: Implement minimal code to pass tests
      Task(subagent_type="hive-dev-coder", prompt="Implement [feature] to make tests pass")
      
      # 3. REFACTOR: Improve code quality while maintaining green tests
      ```
    </commands>
    
    <strict_rule>Never spawn dev-coder without prior failing tests from testing-maker</strict_rule>
  </test_driven_development>
</development_methodology>

<development_workflow>
  <context>
    Claude Code's background CLI capabilities enable real-time development and testing.
    Follow this workflow for efficient development cycles.
  </context>

  <server_management>
    <startup_commands>
      ```bash
      # Start development server in background
      # Use Bash tool with run_in_background=True parameter:
      Bash(command="make dev", run_in_background=True)
      ```
    </startup_commands>
    
    <monitoring_commands>
      ```bash
      # Monitor server activity
      tail -f logs/server.log          # Watch server logs in real-time
      curl http://localhost:8886/api/v1/health  # Health check
      ```
    </monitoring_commands>
    
    <testing_endpoints>
      ```bash
      # Live API testing and exploration
      curl http://localhost:8886/docs                    # Swagger UI documentation  
      curl http://localhost:8886/playground/status       # Playground availability
      curl http://localhost:8886/playground/agents       # Available agents
      curl http://localhost:8886/playground/teams        # Available teams
      curl http://localhost:8886/playground/workflows    # Available workflows
      
      # Test agent functionality
      curl -X POST http://localhost:8886/playground/teams/genie/runs \
        -H "Content-Type: application/json" \
        -d '{"task_description": "Test system functionality"}'
      ```
    </testing_endpoints>
    
    <shutdown_commands>
      ```bash
      # Stop development server
      make stop                        # Graceful shutdown
      pkill -f "uvicorn"              # Force stop if needed
      ```
    </shutdown_commands>
  </server_management>

  <uv_package_management>
    <context>
      UV is the mandated package manager for ALL Python operations.
      NEVER use pip install - always use UV commands.
    </context>
    
    <dependency_commands>
      ```bash
      uv sync                          # Install/sync all dependencies from pyproject.toml
      uv add <package>                 # Add new dependency (NEVER use pip install)
      uv add --dev <package>           # Add development dependency
      ```
    </dependency_commands>
    
    <quality_commands>
      ```bash
      uv run ruff check --fix          # Lint and auto-fix code issues
      uv run mypy .                    # Type checking for quality assurance
      ```
    </quality_commands>
    
    <testing_commands>
      ```bash
      uv run pytest                    # Run all tests
      uv run pytest tests/agents/      # Test agent functionality
      uv run pytest tests/workflows/   # Test workflow orchestration  
      uv run pytest tests/api/         # Test API endpoints
      uv run pytest --cov=ai --cov=api --cov=lib  # With coverage report
      ```
    </testing_commands>
  </uv_package_management>
</development_workflow>

<development_standards>
  <core_principles>
    <principle>Write simple, focused code that solves current needs without unnecessary complexity (KISS/YAGNI/DRY)</principle>
    <principle>Apply SOLID principles where relevant, favor composition over inheritance</principle>
    <principle>Use industry standard libraries over custom implementations</principle>
    <principle>Always break compatibility for clean, modern implementations</principle>
    <principle>Remove backward compatibility code immediately - clean implementations only</principle>
    <principle>Make side effects explicit and minimal</principle>
    <principle>Be brutally honest about whether ideas are good or bad</principle>
  </core_principles>

  <quality_requirements>
    <requirement>Every new agent must have corresponding unit and integration tests</requirement>
    <requirement>Use CSV-based RAG system with hot reload for context-aware responses</requirement>
    <requirement>Never hardcode values - always use .env files and YAML configs</requirement>
  </quality_requirements>
</development_standards>

<mcp_tool_integration>
  <context>
    You operate within a live, instrumented Automagik Hive system with direct control via Model Context Protocol (MCP) tools.
    These tools enable autonomous operations on the agent instance while requiring responsible usage.
  </context>

  <available_tools>
    <tool name="postgres" status="Working">
      <purpose>Direct SQL queries on main system DB (port 5532)</purpose>
      <example>SELECT * FROM hive.component_versions</example>
    </tool>
    
    <tool name="automagik-hive" status="Auth Required">
      <purpose>API interactions (agents/teams/workflows)</purpose>
      <note>Check .env for HIVE_API_KEY</note>
    </tool>
    
    <tool name="automagik-forge" status="Working">
      <purpose>Project & task management</purpose>
      <usage>List projects, create/update tasks</usage>
    </tool>
    
    <tool name="search-repo-docs" status="Working">
      <purpose>External library docs</purpose>
      <usage>Agno (/context7/agno), other dependencies</usage>
    </tool>
    
    <tool name="ask-repo-agent" status="Requires Indexing">
      <purpose>GitHub repo Q&A</purpose>
      <usage>Agno (agno-agi/agno), external repos</usage>
    </tool>
    
    <tool name="wait" status="Working">
      <purpose>Workflow delays</purpose>
      <usage>wait_minutes(0.1) for async ops</usage>
    </tool>
    
    <tool name="send_whatsapp_message" status="Working">
      <purpose>External notifications</purpose>
      <usage>Use responsibly for alerts</usage>
    </tool>
  </available_tools>

  <database_schema>
    ```sql
    -- Main system database (postgresql://localhost:5532/automagik_hive)
    
    -- agno schema
    agno.knowledge_base         -- Vector embeddings for RAG system
      ├── id, name, content    -- Core fields
      ├── embedding (vector)   -- pgvector embeddings  
      └── meta_data, filters   -- JSONB for filtering
    
    -- hive schema  
    hive.component_versions     -- Agent/team/workflow versioning
      ├── component_type       -- 'agent', 'team', 'workflow'
      ├── name, version        -- Component identification
      └── modified_at         -- Version tracking
    
    -- Example queries:
    SELECT * FROM hive.component_versions WHERE component_type = 'agent';
    SELECT * FROM agno.knowledge_base WHERE meta_data->>'domain' = 'development';
    ```
  </database_schema>

  <usage_workflow>
    <step order="1">Query current state using postgres for system analysis</step>
    <step order="2">Document strategy in automagik-forge tasks before execution</step>
    <step order="3">Take actions only with explicit user approval</step>
    <step order="4">Ensure development server is running (use Bash tool with run_in_background=True)</step>
    <step order="5">Bump version in YAML files when configs are modified</step>
  </usage_workflow>

  <best_practices>
    <practice>Query current state first before modifying</practice>
    <practice>Get user approval for planned work and features</practice>
    <practice>Automatically report critical issues, bugs, and blockers found during analysis</practice>
    <practice>Use BEGIN; ... COMMIT/ROLLBACK; for DB changes</practice>
    <practice>Store important actions in automagik-forge tasks for audit trail</practice>
    <practice>Add wait between bulk operations to respect rate limits</practice>
    <practice>Have fallback strategies (API → DB → memory)</practice>
  </best_practices>

  <safety_rules>
    <rule tool="postgres">Readonly direct queries only</rule>
    <rule tool="automagik_forge">Track decisions and progress in task management</rule>
    <rule tool="send_whatsapp_message">Confirm recipient/content before sending</rule>
    <rule general="version_bumping">ANY config change via tools requires YAML version update</rule>
  </safety_rules>

  <troubleshooting>
    <auth_issues>
      ```bash
      cat .env | grep HIVE_API_KEY  # Verify API key exists
      # If missing, check with user or use postgres as fallback
      ```
    </auth_issues>
    
    <connection_issues>
      <solution>Use `make stop` then Bash("make dev", run_in_background=True) for graceful restart</solution>
      <note>Main API runs on http://localhost:8886</note>
    </connection_issues>
  </troubleshooting>
</mcp_tool_integration>

<additional_references>
  <master_genie_configuration>
    For all behavioral guidelines, orchestration patterns, and agent routing intelligence, 
    see AGENTS.md which contains the complete Master Genie configuration.
  </master_genie_configuration>
  
  <system_summary>
    This framework provides a production-ready foundation for building sophisticated 
    multi-agent AI systems with enterprise-grade deployment capabilities.
  </system_summary>
</additional_references>