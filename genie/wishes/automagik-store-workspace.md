# 🏪 Automagik Store - Agent Collection Workspace

## 🎯 Vision
Create a **separate repository** (`automagik-store`) that serves as a curated collection of production-ready agents, teams, workflows, and tools that can be:
- Published independently from the main framework
- Used as templates for new users
- Imported into any automagik-hive workspace
- Continuously expanded with community contributions

## 📋 Project Structure

### Phase 1: Foundation Setup ✅
**Goal**: Create the basic repository structure and validate it works with `uvx automagik-hive`

**T1.0: Repository Initialization**
- Create `/home/namastex/workspace/automagik-store/` directory
- Initialize git repository
- Create `.gitignore` for Python projects
- Add `README.md` with project description

**T1.1: Core Structure Creation**
- Create `ai/` directory structure
- Add `ai/agents/` for agent collection
- Add `ai/teams/` for team templates  
- Add `ai/workflows/` for workflow examples
- Add `ai/tools/` for custom tools

**T1.2: Environment Configuration**
- Create `.env.example` with required variables
- Add `.mcp.json` for MCP server configuration
- Document required API keys and services

### Phase 2: Example Agent Collection 🤖
**Goal**: Build working examples of each component type

**T2.0: Research Agent Suite**
- `research_agent/` - Web research and data gathering
  - `agent.py` - Factory function with custom logic
  - `config.yaml` - Agent configuration
  - `__init__.py` - Module exports

**T2.1: Analysis Agent Suite**
- `analysis_agent/` - Data analysis and insights
  - `agent.py` - Custom analysis logic
  - `config.yaml` - Configuration with tools
  - `__init__.py` - Module exports

**T2.2: Report Agent Suite**
- `report_agent/` - Report generation and formatting
  - `agent.py` - Custom reporting logic
  - `config.yaml` - Output configuration
  - `__init__.py` - Module exports

### Phase 3: Team Templates 👥
**Goal**: Create teams that coordinate agents

**T3.0: Research Team**
- `research_team/` - Coordinates research agents
  - `team.py` - Member loading and routing
  - `config.yaml` - Team configuration (mode: route)
  - `__init__.py` - Module exports

**T3.1: Development Team**
- `dev_team/` - Software development coordination
  - `team.py` - Development workflow routing
  - `config.yaml` - Team member configuration
  - `__init__.py` - Module exports

### Phase 4: Workflow Examples 🔄
**Goal**: Build complete workflow patterns

**T4.0: Research Workflow**
- `research_workflow/` - End-to-end research process
  - `workflow.py` - Step orchestration
  - `config.yaml` - Workflow steps configuration
  - `__init__.py` - Module exports

**T4.1: CI/CD Workflow**
- `cicd_workflow/` - Deployment automation
  - `workflow.py` - Deployment steps
  - `config.yaml` - Pipeline configuration
  - `__init__.py` - Module exports

### Phase 5: Custom Tools 🔧
**Goal**: Provide useful tool implementations

**T5.0: Web Search Tool**
- `web_search_tool/` - Custom web search implementation
  - `tool.py` - Search logic implementation
  - `config.yaml` - API configuration
  - `__init__.py` - Module exports

**T5.1: Database Tool**
- `database_tool/` - Database operations
  - `tool.py` - Query execution logic
  - `config.yaml` - Connection configuration
  - `__init__.py` - Module exports

### Phase 6: Testing & Validation ✅
**Goal**: Ensure everything works together

**T6.0: Component Testing**
- Test each agent independently
- Validate team routing works
- Verify workflow execution
- Confirm tool functionality

**T6.1: Integration Testing**
- Run `uvx automagik-hive /path/to/automagik-store`
- Test agent discovery and loading
- Validate team member resolution
- Confirm workflow step execution

**T6.2: Documentation**
- Document each component's purpose
- Create usage examples
- Add troubleshooting guide
- Write contribution guidelines

### Phase 7: Automation Preparation 🚀
**Goal**: Learn from manual process for automation

**T7.0: Pattern Extraction**
- Document file structures that work
- Identify minimal requirements
- Note configuration patterns
- List common customizations

**T7.1: Template Generation**
- Create template strings for each file type
- Build configuration generators
- Design factory function patterns
- Prepare for `cli/workspace.py` update

**T7.2: Automation Implementation**
- Update `cli/workspace.py` with learned patterns
- Remove hardcoding, use discovered templates
- Add flexibility for customization
- Test automated generation

## 🎯 Success Criteria

### Immediate Goals
- [ ] Working automagik-store repository
- [ ] Functional agents that can be loaded
- [ ] Teams that properly route to members
- [ ] Workflows that execute steps
- [ ] Tools that provide real functionality

### Long-term Vision
- [ ] Published as separate package
- [ ] Community contribution model
- [ ] Regular updates with new agents
- [ ] Integration with main framework
- [ ] Marketplace for agent sharing

## 📝 Key Decisions

### No Hardcoding Policy
- Build real workspace first
- Test thoroughly with actual usage
- Extract patterns from working code
- Only then automate with confidence

### Separation of Concerns
- Main repo: Framework and core functionality
- Store repo: Curated agent collection
- User workspaces: Custom implementations

### Quality Standards
- Every agent must have working example
- All teams must demonstrate routing
- Workflows must show orchestration
- Tools must provide real value

## 🚦 Current Status
- **Phase**: 1 - Foundation Setup
- **Next Action**: Create automagik-store directory
- **Blocker**: None
- **Priority**: 0 (Highest)

## 📋 Implementation Notes

### Directory Layout
```
automagik-store/
├── README.md
├── .gitignore
├── .env.example
├── .mcp.json
└── ai/
    ├── agents/
    │   ├── research_agent/
    │   ├── analysis_agent/
    │   └── report_agent/
    ├── teams/
    │   ├── research_team/
    │   └── dev_team/
    ├── workflows/
    │   ├── research_workflow/
    │   └── cicd_workflow/
    └── tools/
        ├── web_search_tool/
        └── database_tool/
```

### Testing Command
```bash
# From automagik-hive directory
uvx automagik-hive ../automagik-store

# Or with full path
uvx automagik-hive /home/namastex/workspace/automagik-store
```

### Git Configuration
```bash
cd automagik-store
git init
git remote add origin [repository-url]
git add .
git commit -m "Initial automagik-store setup"
```

## 🔄 Updates Log
- **2025-08-12**: Initial wish document created
- **Priority**: Set to 0 - highest priority
- **Approach**: Manual first, automation later