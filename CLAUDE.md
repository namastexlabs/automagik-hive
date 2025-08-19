# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<project_context>
<project_overview>
Automagik Hive is an enterprise multi-agent AI framework built on Agno (agno-agi/agno) that enables rapid development of sophisticated multi-agent systems through YAML configuration. It provides production-ready boilerplate for building intelligent agents, routing teams, and business workflows with enterprise-grade deployment capabilities.
</project_overview>

<file_organization_standards>
<core_principles>
<small_focused_files>Default to multiple small files (<350 lines) rather than monolithic ones</small_focused_files>
<single_responsibility>Each file should have one clear purpose</single_responsibility>
<separation_of_concerns>Separate utilities, constants, types, components, and business logic</separation_of_concerns>
<clear_structure>Follow existing project structure, create new directories when appropriate</clear_structure>
<proper_imports_exports>Design for reusability and maintainability</proper_imports_exports>
<composition_over_inheritance>Use inheritance only for true 'is-a' relationships</composition_over_inheritance>
</core_principles>

<genie_workspace_structure>
<organization_pattern>/genie/ is the autonomous thinking space with streamlined WISHES-CENTRIC architecture</organization_pattern>
<primary_directory>wishes/ = CENTRAL HUB for all active planning, agent coordination, and implementation workflows</primary_directory>
<anti_proliferation_rule>ONE wish = ONE document in /genie/wishes/, refine in place with DEATH TESTAMENT completion</anti_proliferation_rule>
<directory_structure>
<wishes>PRIMARY - all active planning & execution with /wish command integration</wishes>
<ideas>brainstorms and concepts</ideas>
<experiments>prototypes and tests</experiments>
<knowledge>wisdom and learnings</knowledge>
</directory_structure>
<eliminated_architecture>reports/ folder ELIMINATED - replaced by DEATH TESTAMENT structured final reports embedded in wishes/</eliminated_architecture>
<misplaced_content>Move any misplaced folders to proper /genie/ structure with wishes/ as primary focus</misplaced_content>
</genie_workspace_structure>

<code_quality_standards>
<kiss_principle>Simplify over-engineered components, eliminate redundant layers</kiss_principle>
<no_mocking_placeholders>Never mock, use placeholders, hardcode, or omit code</no_mocking_placeholders>
<complete_implementation>Always provide full, working code</complete_implementation>
</code_quality_standards>

<behavioral_enforcement>
<violations_trigger>Immediate cross-agent behavioral updates</violations_trigger>
<personal_violation_memory>Maintained to prevent repetition</personal_violation_memory>
<validation_requirement>All agents must validate against these rules before file operations</validation_requirement>

<time_estimation_prohibition>
<absolute_prohibition>
CRITICAL BEHAVIORAL VIOLATION PREVENTION: ALL agents MUST NEVER estimate human implementation time.
USER FEEDBACK VIOLATION: Master Genie and agents creating 6-week plans, Week 1 timelines, etc.
ARCHITECTURE RULE: "We are execution engines working in minutes/seconds, NOT project managers"
NO agent will estimate weeks, days, hours, or any human temporal predictions.
</absolute_prohibition>

<violation_patterns_to_prevent>
<week_estimates>FORBIDDEN: "Week 1", "6-week plan", "over 2 weeks" estimations</week_estimates>
<day_estimates>FORBIDDEN: "3 days", "within a week", "daily" timeline predictions</day_estimates>
<hour_estimates>FORBIDDEN: "8 hours", "full day", temporal work estimates</hour_estimates>
<timeline_creation>FORBIDDEN: Any timeline or schedule creation for human implementation</timeline_creation>
</violation_patterns_to_prevent>

<architectural_compliance>
<logical_sequencing_only>Use "Phase 1", "Phase 2", "Initial Implementation", "Core Development"</logical_sequencing_only>
<execution_engine_understanding>We execute in minutes/seconds through agent orchestration</execution_engine_understanding>
<orchestration_planning_mandate>All wish documents MUST include explicit subagent execution strategies</orchestration_planning_mandate>
<agent_specification_required>Define which agents handle each implementation phase</agent_specification_required>
<tsd_orchestration_enhancement>TSD documents MUST include mandatory "Orchestration Strategy" section specifying agent execution plans, parallel/sequential patterns, Task() coordination, dependency mapping, context provision requirements</tsd_orchestration_enhancement>
<software_development_compliance>Follow systematic agent coordination planning for best practice compliance</software_development_compliance>
</architectural_compliance>

<enforcement_actions>
<immediate_behavioral_learning>Any time estimation triggers automatic hive-self-learn deployment</immediate_behavioral_learning>
<zero_tolerance_pattern>Time estimation = CRITICAL VIOLATION requiring immediate behavioral update</zero_tolerance_pattern>
<cross_agent_propagation>Time estimation prohibition must propagate to ALL hive agents</cross_agent_propagation>
</enforcement_actions>
</time_estimation_prohibition>

<critical_uv_compliance_enforcement>
<absolute_prohibition>
CRITICAL VIOLATION PREVENTION: ALL testing agents MUST use `uv run` for Python commands.
USER FEEDBACK VIOLATION: "violation, the testing maker isnt uving uv run"
ARCHITECTURE RULE: "NEVER use python directly - Always use `uv run` for ALL Python commands"
NO testing agent will use direct `pytest`, `python`, or `coverage` commands.
</absolute_prohibition>

<violation_patterns_to_prevent>
<direct_pytest_usage>FORBIDDEN: Direct `pytest` command usage in testing agents</direct_pytest_usage>
<direct_python_usage>FORBIDDEN: Direct `python` command usage in testing agents</direct_python_usage>
<direct_coverage_usage>FORBIDDEN: Direct `coverage` command usage in testing agents</direct_coverage_usage>
<testing_command_bypass>FORBIDDEN: Any testing command that bypasses UV protocol</testing_command_bypass>
</violation_patterns_to_prevent>

<architectural_compliance>
<testing_agent_responsibility>Testing agents MUST use `uv run pytest` for ALL test execution</testing_agent_responsibility>
<coverage_agent_responsibility>Testing agents MUST use `uv run coverage` for ALL coverage reporting</coverage_agent_responsibility>
<python_execution_responsibility>Testing agents MUST use `uv run python` for ALL Python execution</python_execution_responsibility>
<uv_protocol_enforcement>Mandatory UV compliance across ALL testing operations</uv_protocol_enforcement>
</architectural_compliance>

<enforcement_actions>
<immediate_behavioral_learning>Update ALL testing agents with UV compliance requirements</immediate_behavioral_learning>
<zero_tolerance_pattern>Any direct command usage = CRITICAL VIOLATION requiring immediate behavioral update</zero_tolerance_pattern>
<cross_agent_propagation>UV compliance requirements must propagate to ALL new testing agents</cross_agent_propagation>
</enforcement_actions>
</critical_uv_compliance_enforcement>

<install_command_environment_management>
<core_principle>
INSTALL COMMAND DESIGN: The --install command manages .env files intelligently:
- If .env exists with credentials: use existing credentials
- If .env exists but missing/placeholder credentials: generate and update .env
- If .env doesn't exist: generate from .env.example as base with real credentials
</core_principle>

<installation_workflow>
<env_detection>System detects if .env exists with valid credentials</env_detection>
<credential_generation>Generate secure credentials when needed during installation</credential_generation>
<env_creation>Create .env from .env.example template during initial setup</env_creation>
<credential_injection>Update .env with generated credentials during installation process</credential_injection>
</installation_workflow>

<architectural_compliance>
<installation_scope>Environment file management is part of installation/setup process</installation_scope>
<runtime_separation>Runtime application code reads environment variables, installation code manages them</runtime_separation>
<deployment_automation>Installation commands handle environment setup for deployment automation</deployment_automation>
<configuration_lifecycle>Clear separation between setup-time and runtime configuration management</configuration_lifecycle>
</architectural_compliance>
</install_command_environment_management>

<configuration_architecture_principles>
<critical_separation>STRICT separation between application-level (.env) and infrastructure-level (docker-compose.yml) configuration</critical_separation>
<prohibited_env_variables>
<infrastructure_variables>NEVER include in .env/.env.example files: POSTGRES_UID, POSTGRES_GID, port mappings for Docker</infrastructure_variables>
<docker_compose_only>Infrastructure variables belong ONLY in docker-compose.yml with ${VAR:-default} pattern</docker_compose_only>
</prohibited_env_variables>
<violation_prevention>
<env_file_scope>Application runtime configuration ONLY - database URLs, API keys, app settings</env_file_scope>
<docker_compose_scope>Container orchestration configuration ONLY - user permissions, port mappings, volume mounts</docker_compose_scope>
<override_mechanism>Use shell environment or docker-compose.override.yml for infrastructure overrides</override_mechanism>
</violation_prevention>
</configuration_architecture_principles>
</behavioral_enforcement>
</file_organization_standards>
</project_context>

<architecture_navigation>
<codebase_exploration_command>
```bash
# Use this tree command to explore the entire codebase structure
tree -I '__pycache__|.git|*.pyc|.venv|data|logs|.pytest_cache|*.egg-info|node_modules|.github|genie|scripts|common|docs|alembic' -P '*.py|*.yaml|*.yml|*.toml|*.md|Makefile|Dockerfile|*.ini|*.sh|*.csv|*.json' --prune -L 4
```
</codebase_exploration_command>

<architecture_treasure_map>
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
</architecture_treasure_map>
</architecture_navigation>

<development_methodologies>
<tdd_development_coordination>
<red_green_refactor_cycle>hive-testing-maker → hive-dev-coder → repeat</red_green_refactor_cycle>

<tdd_commands>
```bash
# 1. RED: Spawn testing-maker for failing tests
Task(subagent_type="hive-testing-maker", prompt="Create failing test suite for [feature]")
# 2. GREEN: Spawn dev-coder to implement minimal code  
Task(subagent_type="hive-dev-coder", prompt="Implement [feature] to make tests pass")
# 3. REFACTOR: Coordinate quality improvements while keeping tests green
```
</tdd_commands>

<tdd_rules>Never spawn dev-coder without prior failing tests from testing-maker</tdd_rules>
</tdd_development_coordination>
</development_methodologies>

<environment_workflow>
<unified_agent_commands>
```bash
# Unified agent environment management via uv run automagik-hive
uv run automagik-hive --agent-install      # Setup agent services (ports 38886/35532) - unified config from .env.example
uv run automagik-hive --agent-serve        # Start agent services 
uv run automagik-hive --agent-stop         # Stop agent services  
uv run automagik-hive --agent-restart      # Restart agent services
uv run automagik-hive --agent-status       # Check agent service status
uv run automagik-hive --agent-logs         # View agent logs (default 20 lines)
uv run automagik-hive --agent-logs --tail 50  # View last 50 log lines

# Your isolated agent environment:
# - Agent API: http://localhost:38886 
# - Agent DB: postgresql://localhost:35532 
# - Agent config: .env (unified credential system)
# - Docker containers: hive-postgres-agent, hive-agent-dev-server
# - Zero prompts or confirmations for automation compatibility
```
</unified_agent_commands>

<uv_command_reference>
<package_management>
```bash
uv sync                          # Install/sync all dependencies from pyproject.toml
uv add <package>                 # Add new dependency (NEVER use pip install)
uv add --dev <package>           # Add development dependency
```
</package_management>

<code_quality_testing>
```bash
uv run ruff check --fix          # Lint and auto-fix code issues
uv run mypy .                    # Type checking for quality assurance
uv run pytest                    # Run all tests
uv run pytest tests/agents/      # Test agent functionality
uv run pytest tests/workflows/   # Test workflow orchestration  
uv run pytest tests/api/         # Test API endpoints
uv run pytest --cov=ai --cov=api --cov=lib  # With coverage report
```
</code_quality_testing>
<agent_development_cli>
```bash
# Complete agent development workflow via uv run automagik-hive
uv run automagik-hive --agent-install      # Initial setup and service installation
uv run automagik-hive --agent-serve        # Start agent services (if stopped)
uv run automagik-hive --agent-stop         # Stop agent services (preserve state)
uv run automagik-hive --agent-restart      # Restart agent services
uv run automagik-hive --agent-status       # Agent service health check
uv run automagik-hive --agent-logs         # Agent application logs (default 20 lines)
uv run automagik-hive --agent-logs --tail 50  # Last 50 log lines
uv run automagik-hive --agent-reset        # Complete reset (destructive)

# Agent Environment Status:
# ✅ Agent Postgres: Runs on port 35532 (isolated from main postgres on 5532)
# ✅ Agent Server: Runs on port 38886 (isolated from main server on 8886)
# ✅ Configuration: Uses unified .env configuration
# ✅ Data: Stores data in data/postgres-agent (isolated from main data)

# Typical Development Workflow:
# 1. uv run automagik-hive --agent-install    # Set up isolated agent environment
# 2. uv run automagik-hive --agent-serve      # Start both postgres and server
# 3. uv run automagik-hive --agent-status     # Verify both services running
# 4. [Develop and test agent functionality]
# 5. uv run automagik-hive --agent-logs       # Debug issues if needed
```
</agent_development_cli>

</uv_command_reference>
</environment_workflow>

<development_standards>
<core_development_principles>
<kiss_yagni_dry>Write simple, focused code that solves current needs without unnecessary complexity</kiss_yagni_dry>
<solid_principles>Apply where relevant, favor composition over inheritance</solid_principles>
<modern_frameworks>Use industry standard libraries over custom implementations</modern_frameworks>
<no_backward_compatibility>Always break compatibility for clean, modern implementations</no_backward_compatibility>
<no_legacy_code>Remove backward compatibility code immediately - clean implementations only</no_legacy_code>
<explicit_side_effects>Make side effects explicit and minimal</explicit_side_effects>
<honest_assessment>Be brutally honest about whether ideas are good or bad</honest_assessment>
</core_development_principles>

<code_quality_standards>
<testing_required>Every new agent must have corresponding unit and integration tests</testing_required>
<knowledge_base>Use CSV-based RAG system with hot reload for context-aware responses</knowledge_base>
<no_hardcoding>Never hardcode values - always use .env files and YAML configs</no_hardcoding>
</code_quality_standards>

<component_specific_guides>
For detailed implementation guidance, see component-specific CLAUDE.md files:
- ai/CLAUDE.md - Multi-agent system orchestration
- api/CLAUDE.md - FastAPI integration patterns  
- lib/config/CLAUDE.md - Configuration management
- lib/knowledge/CLAUDE.md - Knowledge base management
- tests/CLAUDE.md - Testing patterns
</component_specific_guides>
</development_standards>

<tool_integration>
<mcp_tools_live_system_control>
You operate within a live, instrumented Automagik Hive system with direct control via Model Context Protocol (MCP) tools. These tools enable autonomous operations on the agent instance while requiring responsible usage aligned with our development principles.

<tool_arsenal>
<tool name="postgres" status="Working">
<purpose>Direct SQL queries on agent DB (port 35532)</purpose>
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
</tool_arsenal>

<database_schema_discovery>
```sql
-- Agent instance database (postgresql://localhost:35532/hive_agent)
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

-- Usage patterns:
SELECT * FROM hive.component_versions WHERE component_type = 'agent';
SELECT * FROM agno.knowledge_base WHERE meta_data->>'domain' = 'development';
```
</database_schema_discovery>

<mcp_integration_guidelines>
<discovery_pattern>
<query_current_state>Use postgres for system state queries and analysis</query_current_state>
<plan_actions>Document strategy in tasks before execution</plan_actions>
<take_actions>Only with explicit user approval - automagik-forge for task management, automagik-hive for agent operations</take_actions>
</discovery_pattern>

<integration_with_development_workflow>
<before_mcp_tools>Ensure agent environment is running (see UV Command Reference)</before_mcp_tools>
<after_tool_usage>Bump version in YAML files per our rules when configs are modified</after_tool_usage>
</integration_with_development_workflow>
</mcp_integration_guidelines>

<troubleshooting>
<auth_errors>
```bash
cat .env | grep HIVE_API_KEY  # Verify API key exists
# If missing, check with user or use postgres as fallback
```
</auth_errors>

<connection_failures>
<restart_command>Use `uv run automagik-hive --agent-restart` for graceful service restart</restart_command>
<agent_api_port>Agent API on http://localhost:38886</agent_api_port>
</connection_failures>
</troubleshooting>

<safety_guidelines>
<postgres>Readonly direct queries</postgres>
<automagik_forge>Track decisions and progress in task management</automagik_forge>
<send_whatsapp_message>Confirm recipient/content before sending</send_whatsapp_message>
<version_bumping>ANY config change via tools requires YAML version update</version_bumping>
</safety_guidelines>

<best_practices>
<always_verify>Query current state first before modifying</always_verify>
<smart_action_approval>Get user approval for planned work and features, but automatically report critical issues, bugs, and blockers found during analysis</smart_action_approval>
<use_transactions>Use BEGIN; ... COMMIT/ROLLBACK; for DB changes</use_transactions>
<log_important_actions>Store in automagik-forge tasks for audit trail</log_important_actions>
<respect_rate_limits>Add wait between bulk operations</respect_rate_limits>
<fail_gracefully>Have fallback strategies (API → DB → memory)</fail_gracefully>
</best_practices>

<transformation_note>These tools transform you from passive code assistant to active system operator. Use them wisely to accelerate development while maintaining system integrity.</transformation_note>
</mcp_tools_live_system_control>
</tool_integration>

<final_validation>
<critical_reminders>
For all behavioral guidelines, orchestration patterns, and agent routing intelligence, see GENIE.md which contains the complete Master Genie configuration.
</critical_reminders>

<system_summary>
This framework provides a production-ready foundation for building sophisticated multi-agent AI systems with enterprise-grade deployment capabilities.
</system_summary>
</final_validation>

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.