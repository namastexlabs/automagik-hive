# --init Template Structure

## Overview
`uvx automagik-hive --init project-management-team` creates a complete, runnable project template with zero configuration needed.

## Template Directory Structure
```
project-management-team/
├── .env                    # Pre-configured environment variables
├── .env.example           # Template for customization
├── hive.yaml              # Main hive configuration
├── agents/                # Individual agent definitions
│   ├── project-planner.yaml
│   ├── senior-developer.yaml
│   ├── qa-specialist.yaml
│   └── devops-engineer.yaml
├── teams/                 # Team coordination configs
│   └── project-management.yaml
├── workflows/             # Automated workflow definitions
│   ├── project-kickoff.yaml
│   ├── feature-development.yaml
│   └── deployment-pipeline.yaml
├── tools/                 # Custom tool integrations
│   ├── github-integration.yaml
│   ├── slack-notifications.yaml
│   └── docker-deployment.yaml
├── README.md              # Project-specific documentation
└── examples/              # Sample tasks and demonstrations
    ├── build-todo-app.md
    ├── api-development.md
    └── deployment-guide.md
```

## Core Template Components

### 1. `.env` - Pre-configured Environment
```bash
# Automagik Hive Configuration
HIVE_PROJECT_NAME=project-management-team
HIVE_LOG_LEVEL=INFO
HIVE_PORT=8887

# AI Model Configuration (optional - uses defaults)
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here

# Tool Integrations (optional)
# GITHUB_TOKEN=your_token_here
# SLACK_WEBHOOK=your_webhook_here
# DOCKER_REGISTRY=your_registry_here

# Database (uses in-memory by default)
# DATABASE_URL=postgresql://localhost:5432/hive_project
```

### 2. `hive.yaml` - Main Configuration
```yaml
name: project-management-team
version: 1.0.0
description: "AI-powered project management team for software development"

# Team composition
teams:
  - project-management

# Default workflows
workflows:
  - project-kickoff
  - feature-development
  - deployment-pipeline

# Available tools
tools:
  - github-integration
  - slack-notifications
  - docker-deployment

# Genie configuration
genie:
  enabled: true
  personality: project-manager
  welcome_message: "Welcome! I'm Genie, ready to help manage your software project. What would you like to build today?"
```

### 3. Agent Templates (4 Core Agents)

#### `agents/project-planner.yaml`
```yaml
name: project-planner
version: 1.0.0
role: "Project Planning Specialist"

description: |
  Expert at breaking down complex projects into manageable tasks,
  creating roadmaps, and coordinating team efforts.

capabilities:
  - requirement_analysis
  - task_breakdown
  - timeline_planning
  - resource_allocation

prompt: |
  You are a senior project manager with 10+ years of experience.
  You excel at:
  - Breaking complex projects into clear, actionable tasks
  - Creating realistic timelines and milestones
  - Identifying dependencies and potential blockers
  - Coordinating between team members

tools:
  - github-integration
  - slack-notifications

memory:
  type: persistent
  scope: project
```

#### `agents/senior-developer.yaml`
```yaml
name: senior-developer
version: 1.0.0
role: "Senior Software Developer"

description: |
  Experienced developer specializing in full-stack development,
  architecture design, and best practices implementation.

capabilities:
  - code_development
  - architecture_design
  - code_review
  - technical_mentoring

prompt: |
  You are a senior software developer with expertise in:
  - Full-stack development (React, Python, Node.js, databases)
  - Clean architecture and design patterns
  - Testing strategies and implementation
  - Performance optimization and scalability

tools:
  - github-integration
  - docker-deployment

memory:
  type: persistent
  scope: project
```

#### `agents/qa-specialist.yaml`
```yaml
name: qa-specialist
version: 1.0.0
role: "Quality Assurance Specialist"

description: |
  Quality assurance expert focused on testing strategy,
  automation, and ensuring product reliability.

capabilities:
  - test_planning
  - automated_testing
  - quality_assurance
  - bug_tracking

prompt: |
  You are a QA specialist responsible for:
  - Creating comprehensive testing strategies
  - Implementing automated test suites
  - Identifying edge cases and potential issues
  - Ensuring code quality and reliability

tools:
  - github-integration
  - slack-notifications

memory:
  type: persistent
  scope: project
```

#### `agents/devops-engineer.yaml`
```yaml
name: devops-engineer
version: 1.0.0
role: "DevOps Engineer"

description: |
  DevOps expert handling deployment, infrastructure,
  monitoring, and CI/CD pipeline management.

capabilities:
  - deployment_automation
  - infrastructure_management
  - monitoring_setup
  - ci_cd_pipelines

prompt: |
  You are a DevOps engineer specializing in:
  - Docker containerization and orchestration
  - CI/CD pipeline setup and optimization
  - Infrastructure as code and automation
  - Monitoring, logging, and alerting systems

tools:
  - docker-deployment
  - github-integration
  - slack-notifications

memory:
  type: persistent
  scope: project
```

### 4. Team Configuration

#### `teams/project-management.yaml`
```yaml
name: project-management
version: 1.0.0
description: "Coordinated project management team"

members:
  - project-planner
  - senior-developer
  - qa-specialist
  - devops-engineer

# Intelligent routing rules
routing:
  planning: project-planner
  development: senior-developer
  testing: qa-specialist
  deployment: devops-engineer
  
  # Complex tasks use multiple agents
  feature_complete: [senior-developer, qa-specialist]
  project_launch: [project-planner, devops-engineer]
  full_pipeline: [project-planner, senior-developer, qa-specialist, devops-engineer]

# Team workflows
coordination:
  daily_standup: "0 9 * * 1-5"  # 9 AM weekdays
  sprint_planning: "0 10 * * 1"  # 10 AM Mondays
  deployment_review: "0 14 * * 5"  # 2 PM Fridays
```

### 5. Workflow Templates

#### `workflows/project-kickoff.yaml`
```yaml
name: project-kickoff
version: 1.0.0
description: "Initial project setup and planning workflow"

trigger:
  manual: true
  command: "kickoff"

steps:
  - name: requirements_gathering
    agent: project-planner
    task: "Analyze project requirements and create initial plan"
    
  - name: architecture_design
    agent: senior-developer
    task: "Design system architecture and tech stack"
    depends_on: [requirements_gathering]
    
  - name: testing_strategy
    agent: qa-specialist
    task: "Create testing strategy and quality gates"
    depends_on: [architecture_design]
    
  - name: deployment_plan
    agent: devops-engineer
    task: "Design deployment and infrastructure plan"
    depends_on: [architecture_design]

outputs:
  - project_specification
  - architecture_document
  - testing_plan
  - deployment_strategy
```

### 6. Tool Integrations

#### `tools/github-integration.yaml`
```yaml
name: github-integration
version: 1.0.0
description: "GitHub repository management and automation"

capabilities:
  - create_repositories
  - manage_branches
  - create_pull_requests
  - issue_tracking

configuration:
  auth_method: token
  default_branch: main
  auto_merge: false

endpoints:
  - name: create_repo
    method: POST
    url: "https://api.github.com/user/repos"
    
  - name: create_issue
    method: POST
    url: "https://api.github.com/repos/{owner}/{repo}/issues"
```

### 7. Project Documentation

#### `README.md` (Template-specific)
```markdown
# Project Management Team

AI-powered project management team created with Automagik Hive.

## Your Team
- 🎯 **Project Planner** - Requirements analysis and task coordination
- 💻 **Senior Developer** - Full-stack development and architecture
- 🧪 **QA Specialist** - Testing strategy and quality assurance
- 🚀 **DevOps Engineer** - Deployment and infrastructure management

## Quick Start
```bash
# Start your team
uvx automagik-hive .

# Make your first wish
# Visit: http://localhost:8887
# Or use: uvx automagik-hive . --chat
```

## Example Projects
- Build a todo application
- Create a REST API
- Set up a deployment pipeline
- Implement automated testing

## Team Commands
- `kickoff <project_name>` - Start a new project
- `develop <feature>` - Build a new feature
- `deploy <environment>` - Deploy to environment
```

## Template Principles

### ✅ **Zero Configuration**
- Everything works out of the box
- Pre-configured .env with sensible defaults
- All integrations optional but ready to enable

### ✅ **Immediate Value**
- Can run `uvx automagik-hive .` immediately after init
- Sample workflows demonstrate capabilities
- Clear examples of what each agent does

### ✅ **Production Ready**
- Proper versioning and metadata
- Scalable architecture patterns
- Security best practices included

### ✅ **Extensible**
- Easy to add new agents
- Simple to customize workflows
- Clear patterns for tool integration

This template structure ensures that `uvx automagik-hive --init project-management-team` creates a complete, functional project that users can immediately run and understand.