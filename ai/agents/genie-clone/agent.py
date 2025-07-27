"""
Genie Clone Agent - Master Genie's Parallel Self

This agent mirrors the .claude/agents/genie-clone.md personality and instructions exactly
but is enhanced with Agno memory/state management for persistent parallel execution context.
Specialized for clean context parallel execution while preserving Master Genie's strategic focus.
"""

from typing import Any

from agno.agent import Agent

from lib.utils.version_factory import create_agent


async def get_genie_clone_agent(**kwargs: Any) -> Agent:
    """
    Create genie clone agent with enhanced Agno memory and state management.

    This factory function creates Master Genie's parallel self that:
    
    - Executes complex tasks with Master Genie's full strategic brilliance
    - Operates in fresh, isolated context for maximum cognitive efficiency
    - Possesses all Master Genie capabilities (Zen discussions, MCP tools, agent spawning)
    - Preserves Master Genie's strategic context through parallel execution
    - Provides autonomous execution with structured results reporting
    - Uses enhanced memory for persistent parallel execution patterns

    Enhanced Memory Features:
    - 30 run history with 180-day retention for strategic pattern recognition
    - Agentic memory for persistent execution strategies and decision patterns
    - Memory references for cross-session strategic consistency
    - Session summaries for complex multi-component implementation operations
    - Enhanced context management for parallel execution coordination

    State Management:
    - Context-aware strategic decisions based on Master Genie patterns
    - Parallel execution tracking with strategic alignment validation
    - Persistent storage of successful implementation techniques
    - Enhanced coordination with Master Genie's strategic context
    - Clean context isolation while maintaining strategic continuity

    Parallel Execution Features:
    - Clean context isolation for maximum cognitive efficiency
    - Strategic alignment with Master Genie's vision and decisions
    - Autonomous execution without disrupting Master Genie's flow
    - Structured reporting back to Master Genie with complete results
    - Parallel scaling for complex multi-component tasks

    Args:
        **kwargs: Context parameters for agent configuration including:
            - user_id: User identifier for personalized execution preferences
            - master_context: Master Genie's strategic context for alignment
            - execution_scope: Scope of parallel execution (single-task, multi-component)
            - strategic_priorities: Master Genie's current strategic priorities
            - coordination_mode: Level of coordination with Master Genie
            - isolation_level: Context isolation requirements (clean, partial, shared)
            - reporting_format: Structured reporting format for Master Genie
            - memory_context: Additional context for persistent memory alignment
            - parallel_execution_id: Unique identifier for parallel execution tracking

    Returns:
        Agent instance with enhanced memory/state management for parallel execution

    Example Usage:
        # Basic parallel execution
        agent = await get_genie_clone_agent(
            user_id="dev_123",
            master_context="agent_development_focus",
            execution_scope="single_component"
        )

        # Enhanced multi-component parallel execution
        agent = await get_genie_clone_agent(
            user_id="dev_456",
            master_context={
                "strategic_priority": "agent_development",
                "quality_standards": "enterprise_grade",
                "architecture_patterns": "agno_framework"
            },
            execution_scope="multi_component",
            strategic_priorities=[
                "autonomous_execution", 
                "quality_enforcement", 
                "architecture_compliance"
            ],
            coordination_mode="strategic_alignment",
            isolation_level="clean_context",
            reporting_format="structured_completion_report",
            memory_context={
                "execution_domain": "agent_development",
                "parallel_pattern": "master_clone_coordination",
                "quality_requirements": "enterprise_standards"
            },
            parallel_execution_id="master_genie_parallel_001"
        )

    Execution Capabilities:
        # Strategic Execution
        - All Master Genie capabilities in clean context
        - Zen discussions with Gemini/Grok for complex analysis
        - Agent spawning for specialized task delegation
        - MCP tool mastery for system integration
        
        # Parallel Coordination
        - Clean context isolation for maximum focus
        - Strategic alignment with Master Genie's vision
        - Autonomous execution without context pollution
        - Structured reporting for seamless handoff
        
        # Implementation Excellence
        - Agno framework integration patterns
        - YAML-first architecture compliance
        - PostgreSQL + pgvector database design
        - Comprehensive testing and quality validation
        
        # Memory-Enhanced Execution
        - Persistent parallel execution patterns
        - Strategic decision memory bank
        - Cross-session implementation consistency
        - Enhanced context management

    Memory Integration:
        The agent leverages genie-memory MCP tool for:
        - Storing successful parallel execution patterns
        - Learning from previous strategic decisions
        - Maintaining alignment with Master Genie patterns
        - Building knowledge base of implementation solutions
        
        Enhanced Agno memory provides:
        - Persistent context across parallel executions
        - Pattern recognition for similar implementation challenges
        - State preservation during complex multi-component operations
        - Intelligent adaptation to Master Genie's strategic preferences

    Strategic Alignment:
        The clone maintains perfect alignment with Master Genie through:
        - Shared memory patterns and decision frameworks
        - Strategic priority inheritance and preservation
        - Consistent implementation and quality standards
        - Seamless handoff with structured completion reports
        
        Parallel Efficiency Benefits:
        - Master Genie preserves strategic context and high-level coordination
        - Clone handles focused execution in clean, isolated context
        - Maximum cognitive efficiency through specialized context management
        - Unlimited parallel scaling through multiple clone instances
    """
    return await create_agent("genie_clone", **kwargs)