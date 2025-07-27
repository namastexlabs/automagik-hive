"""
Genie Forge Agent - Workflow Automation Meeseeks

This agent mirrors the .claude/agents/genie-forge.md personality and instructions exactly
but is enhanced with Agno memory/state management for persistent automation context.
Specializes in creating comprehensive development workflow automation that eliminates
all manual processes and enforces quality gates automatically.
"""

from typing import Any

from agno.agent import Agent

from lib.utils.version_factory import create_agent


async def get_genie_forge_agent(**kwargs: Any) -> Agent:
    """
    Create genie forge agent with enhanced Agno memory and state management.

    This factory function creates a specialized workflow automation architect that:
    
    - Creates comprehensive pre-commit hook automation for quality enforcement
    - Builds bulletproof CI/CD pipelines with automated testing and deployment
    - Implements one-command task runners for all development operations
    - Centralizes tool configuration in pyproject.toml for consistency
    - Eliminates all manual processes through intelligent automation
    - Uses enhanced memory/state management for persistent automation context

    Enhanced Memory Features:
    - 30 run history with 180-day retention for automation pattern recognition
    - Agentic memory for persistent workflow construction strategies
    - Memory references for cross-session automation consistency
    - Session summaries for complex multi-component automation projects

    State Management:
    - Context-aware automation decisions based on project requirements
    - Persistent automation progress tracking across sessions
    - Storage of successful workflow patterns and implementation techniques
    - Enhanced error recovery with automation rollback capabilities

    Automation Construction Features:
    - Pre-commit hook orchestration with quality gate enforcement
    - CI/CD pipeline architecture with parallel execution optimization
    - Task runner integration with centralized configuration management
    - Configuration consolidation with tool standardization
    - Integration validation with compatibility testing

    Args:
        **kwargs: Context parameters for agent configuration including:
            - user_id: User identifier for personalized automation preferences
            - project_context: Project-specific automation requirements
            - automation_scope: Scope of automation (precommit, cicd, tasks, all)
            - quality_gates: Quality enforcement requirements and thresholds
            - deployment_automation: Deployment pipeline automation settings
            - tool_preferences: Preferred automation tools and configurations
            - performance_targets: Automation performance and speed requirements
            - memory_context: Additional context for persistent memory storage

    Returns:
        Agent instance with enhanced memory/state management for workflow automation

    Example Usage:
        # Basic automation construction
        agent = await get_genie_forge_agent(
            user_id="dev_123",
            project_context="python_microservice"
        )

        # Comprehensive automation with enhanced memory
        agent = await get_genie_forge_agent(
            user_id="dev_456",
            project_context="enterprise_application",
            automation_scope="comprehensive",
            quality_gates={
                "code_coverage": 85,
                "type_checking": "strict",
                "security_scanning": "required",
                "performance_benchmarks": True
            },
            deployment_automation={
                "staging_auto_deploy": True,
                "production_approval": "required",
                "rollback_strategy": "automatic"
            },
            tool_preferences={
                "ci_platform": "github_actions",
                "task_runner": "makefile_taskipy",
                "container_platform": "docker",
                "monitoring": "prometheus"
            },
            performance_targets={
                "precommit_speed": 30,  # seconds
                "ci_pipeline_speed": 300,  # seconds
                "deployment_speed": 600  # seconds
            },
            memory_context={
                "team_size": "medium",
                "automation_maturity": "intermediate",
                "compliance_requirements": ["SOC2", "ISO27001"],
                "deployment_environments": ["staging", "production"]
            }
        )

    Automation Capabilities:
        # Pre-commit Automation
        - Comprehensive hook configuration with quality enforcement
        - Fast execution with intelligent caching and parallel processing
        - Integration with formatting, linting, type checking, and security tools
        - Customizable quality gates and failure handling
        
        # CI/CD Pipeline Construction
        - Multi-platform pipeline architecture (GitHub Actions, GitLab CI)
        - Parallel execution optimization for speed and efficiency
        - Matrix testing across multiple Python versions and environments
        - Security fortress validation with vulnerability scanning
        - Automated deployment with quality gates and rollback capabilities
        
        # Task Runner Integration
        - One-command execution for all development operations
        - Centralized configuration management in pyproject.toml
        - Environment management and agent coordination commands
        - Workflow shortcuts and automation aliases
        
        # Configuration Management
        - Tool standardization and configuration consolidation
        - Single source of truth for all automation settings
        - Duplication elimination and consistency enforcement
        - Version control and change management for configurations

    Memory Integration:
        The agent leverages genie-memory MCP tool for:
        - Storing successful automation construction patterns
        - Learning from previous workflow implementation experiences
        - Maintaining consistency across automation projects
        - Building knowledge base of automation solutions and optimizations
        
        Enhanced Agno memory provides:
        - Persistent context across multiple automation sessions
        - Pattern recognition for similar project requirements
        - State preservation during complex automation construction
        - Intelligent adaptation to team processes and preferences

    Subagent Orchestration:
        The agent coordinates specialized subagent strategies:
        - PRECOMMIT_BUILDER: Hook orchestration and configuration
        - PIPELINE_ARCHITECT: CI/CD workflow construction and optimization
        - CONFIG_CENTRALIZER: Tool configuration consolidation
        - TASK_AUTOMATOR: Development task automation
        - INTEGRATION_VALIDATOR: Cross-tool compatibility validation

    Quality Gates & Success Criteria:
        Mandatory achievement metrics:
        - Pre-commit automation with <30s execution time
        - Complete CI/CD pipeline with parallel processing
        - One-command execution for all development operations
        - Centralized configuration in pyproject.toml
        - Zero manual intervention with intelligent error handling
        - Enhanced memory documentation of all patterns
        - State persistence for complex automation projects

    Advanced Techniques:
        # Pre-commit Hook Orchestration
        - Comprehensive .pre-commit-config.yaml configuration
        - Code formatting, linting, type checking automation
        - Security scanning and dependency validation
        - Test execution with coverage requirements
        
        # CI/CD Pipeline Architecture
        - GitHub Actions / GitLab CI workflows
        - Parallel quality checks and matrix testing
        - Security validation and performance benchmarks
        - Automated deployment with quality gates
        
        # Task Runner Integration
        - Makefile + taskipy automation
        - pyproject.toml centralized configuration
        - Environment management commands
        - Agent coordination shortcuts
    """
    return await create_agent("genie_forge", **kwargs)