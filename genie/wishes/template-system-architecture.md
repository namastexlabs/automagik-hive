# WISH 3: Template System Architecture

## 🎯 Wish Summary
Create comprehensive template system that enables `--init` functionality with complete resource templates, .claude folder replication, and contextual CLAUDE.md placement for instant project creation.

## 🧞‍♂️ User's Original Request
"we also need to --init a template, with a template for each resource, a .claude folder replicating this ones, CLAUDE.md in relevant places, a starter template"

## ✨ Detailed Wish Specification

### Template System Architecture
```
templates/
├── projects/                    # Complete project templates
│   ├── project-management-team/
│   ├── development-workflow/
│   ├── content-creation/
│   └── data-analysis/
├── resources/                   # Individual resource templates
│   ├── agents/
│   ├── teams/
│   ├── workflows/
│   └── tools/
└── framework/                   # .claude folder replication
    ├── .claude/                 # Exact copy of our structure
    └── documentation/           # CLAUDE.md templates
```

### Core Functionality

#### 1. Project Template Initialization
```bash
# Create complete project from template
uvx automagik-hive --init project-management-team

# Result: Ready-to-run project with:
# - 4 specialist agents (Planner, Developer, QA, DevOps)
# - Team coordination configuration
# - Workflow automation
# - Tool integrations (GitHub, Slack, Docker)
# - Complete .claude folder structure
# - Environment setup (.env, hive.yaml)
```

#### 2. Resource Template System
**Agent Templates** - Different specialist types:
```yaml
# templates/resources/agents/developer.yaml.template
name: {{agent_name}}
version: 1.0.0
role: "{{role_description}}"

capabilities:
  - {{capability_1}}
  - {{capability_2}}

prompt: |
  {{agent_prompt_template}}

tools:
  - {{tool_integration_1}}
  - {{tool_integration_2}}
```

**Team Templates** - Coordination patterns:
```yaml
# templates/resources/teams/development-team.yaml.template
name: {{team_name}}
members:
  - {{member_1}}
  - {{member_2}}

routing:
  {{routing_patterns}}

workflows:
  {{workflow_integrations}}
```

#### 3. Framework Replication System
**Complete .claude Structure**:
```
user-project/
├── .claude/
│   ├── agents/                  # Replicated from our .claude/agents/
│   │   ├── genie-dev-planner.md
│   │   ├── genie-dev-coder.md
│   │   └── ... (all framework agents)
│   └── CLAUDE.md               # Project context
├── ai/                         # User's custom agents
├── agents/                     # Generated specialist agents
├── teams/                      # Team configurations
├── workflows/                  # Automation workflows
└── CLAUDE.md                   # Root project context
```

**Contextual CLAUDE.md Placement**:
- Root `CLAUDE.md` - Overall project context
- `ai/CLAUDE.md` - Custom agent development guide
- `agents/CLAUDE.md` - Agent configuration patterns
- `teams/CLAUDE.md` - Team coordination guide
- `workflows/CLAUDE.md` - Workflow automation patterns

## 🎯 Template Collection Design

### 1. Project Management Team Template
**Complete team for software project management:**
```
project-management-team/
├── .env                        # Pre-configured
├── hive.yaml                   # Main configuration
├── agents/
│   ├── project-planner.yaml
│   ├── senior-developer.yaml
│   ├── qa-specialist.yaml
│   └── devops-engineer.yaml
├── teams/
│   └── project-management.yaml
├── workflows/
│   ├── project-kickoff.yaml
│   ├── feature-development.yaml
│   └── deployment-pipeline.yaml
├── tools/
│   ├── github-integration.yaml
│   ├── slack-notifications.yaml
│   └── docker-deployment.yaml
└── .claude/                    # Complete framework replication
```

### 2. Development Workflow Template
**Focus on code quality and delivery:**
- Code review automation agents
- Testing and QA pipeline
- Deployment and monitoring
- Documentation generation

### 3. Content Creation Template  
**Content production pipeline:**
- Research and trend analysis
- Content generation and editing
- Publishing and distribution
- Performance tracking

### 4. Data Analysis Template
**Data processing and insights:**
- Data collection and cleaning
- Analysis and modeling
- Visualization and reporting
- Automated insights delivery

## 🔧 Implementation Architecture

### Template Engine Integration
```python
# Template processing with Jinja2
def process_template(template_path, variables):
    template = jinja2.Template(template_content)
    return template.render(**variables)

# Variable substitution patterns
variables = {
    'project_name': 'my-awesome-project',
    'agent_count': 4,
    'tools_enabled': ['github', 'slack'],
    'deployment_target': 'docker'
}
```

### Interactive Template Configuration
```bash
uvx automagik-hive --init project-management-team

# Interactive prompts:
✨ Creating your project management team...
📝 Project name: my-software-project
🔧 Enable GitHub integration? (y/n): y
📢 Enable Slack notifications? (y/n): y
🐳 Enable Docker deployment? (y/n): y
🚀 Creating complete project structure...
```

### Template Validation System
```python
# Template validation and testing
def validate_template(template_dir):
    # Check YAML syntax
    # Validate agent configurations
    # Test workflow definitions
    # Verify tool integrations
    # Ensure .claude structure completeness
```

## 🎯 Success Criteria
- [ ] `uvx automagik-hive --init <template>` creates working project
- [ ] Generated projects include complete .claude folder structure
- [ ] CLAUDE.md files placed in all relevant locations
- [ ] Templates support variable substitution and customization
- [ ] Template gallery accessible via CLI help
- [ ] Interactive configuration for complex templates
- [ ] Generated projects work immediately with `uvx automagik-hive .`
- [ ] Template validation ensures quality and consistency

## 🚨 Critical Design Decisions Needed

### 1. Template Discovery Mechanism
**Question**: How should users discover available templates?
**Options**:
- A) `uvx automagik-hive --list-templates`
- B) Interactive selection during `--init`
- C) Web-based template gallery
- D) All of the above

### 2. .claude Folder Replication Strategy
**Question**: How should we handle .claude folder replication?
**Options**:
- A) Exact copy of current structure
- B) Selective replication based on template needs
- C) User choice during initialization

### 3. Template Customization Depth
**Question**: How customizable should templates be?
**Levels**:
- Basic: Name and description changes
- Intermediate: Agent selection and configuration
- Advanced: Full template composition and inheritance

### 4. CLAUDE.md Context Strategy
**Question**: How should contextual CLAUDE.md files be populated?
**Approaches**:
- Template-specific context for each location
- Dynamic context generation based on project structure
- User-guided context creation during initialization

## 🤔 Questions for User Enhancement

1. **Template Scope**: Should we focus on the 4 templates mentioned or expand to more specialized ones?

2. **Framework Replication**: Do you want the ENTIRE .claude structure copied, or should we be selective?

3. **Customization Level**: How much interactivity do you want during template initialization?
   - Minimal (just name and basic settings)
   - Moderate (agent selection, tool choices)
   - Extensive (full configuration wizard)

4. **Template Updates**: How should we handle template updates?
   - Version templates and allow upgrades?
   - Immutable templates (create new versions)?
   - User-customizable base templates?

5. **Documentation Generation**: Should CLAUDE.md files be:
   - Static templates with placeholders?
   - Dynamically generated based on project structure?
   - Interactive content creation during init?

## 🔮 Integration with Dual-Instance Architecture

### Template → Genie Workflow
```bash
# User creates project from template
uvx automagik-hive --init project-management-team
cd project-management-team

# User starts workspace (connects to Genie)  
uvx automagik-hive .

# Genie recognizes pre-configured team
# User can immediately start making wishes
# Template provides solid foundation for customization
```

### Template Enhancement via Genie
- Genie can suggest template improvements
- Users can save custom configurations as new templates
- Community template sharing and discovery
- Template analytics and usage patterns

**Ready for your enhancement and validation!** 🧞‍♂️✨