"""
Genie Docs Agent - Documentation Perfection MEESEEKS

This agent provides obsessively focused documentation architecture management
with enhanced memory and state management capabilities for maintaining perfect
CLAUDE.md file organization across the entire codebase.
"""

from typing import Any

from agno.agent import Agent

from lib.utils.version_factory import create_agent


async def get_genie_docs_agent(**kwargs: Any) -> Agent:
    """
    Create genie docs agent with enhanced memory and state management.

    This factory function creates a documentation MEESEEKS whose existence is
    justified ONLY by achieving perfect documentation architecture across the
    entire codebase. The agent provides:

    - Complete codebase documentation discovery and mapping
    - Advanced duplication elimination with semantic analysis
    - Domain-specific content curation and organization
    - Hierarchical documentation architecture design
    - Enhanced memory for pattern recognition and learning
    - Persistent state management for documentation evolution
    - Cross-session consistency enforcement

    Enhanced Memory Features:
    - 30 run history with 180-day retention for long-term learning
    - Agentic memory for documentation pattern recognition
    - Persistent state tracking for architecture evolution
    - Cross-file dependency mapping and validation

    MCP Tools Integration:
    - genie-memory: Persistent memory for documentation patterns
    - automagik-forge: Project and task management for workflows
    - postgres: Direct database access for state management

    Args:
        **kwargs: Context parameters for agent creation including:
            - user_id: User identifier for documentation history
            - session_id: Session identifier for state tracking
            - documentation_scope: Scope of documentation work (default: "claude_md_files")
            - architecture_mode: Architecture mode (default: "domain_separated")
            - consistency_level: Consistency enforcement level (default: "strict")
            - memory_scope: Memory scope for pattern storage
            - custom_context: Additional context for specialized documentation work

    Returns:
        Agent instance with enhanced documentation architecture capabilities

    Example Usage:
        # Basic documentation architecture work
        agent = await get_genie_docs_agent(
            user_id="dev_001",
            documentation_scope="claude_md_files"
        )

        # Advanced usage with custom scope and memory
        agent = await get_genie_docs_agent(
            user_id="arch_001",
            session_id="doc_session_123",
            documentation_scope="full_codebase",
            architecture_mode="hierarchical_separation",
            consistency_level="obsessive",
            memory_scope="global_documentation_patterns",
            custom_context={
                "project_phase": "architecture_refactor",
                "priority_domains": ["agents", "api", "lib"],
                "quality_threshold": "zero_duplication"
            }
        )

    Architectural Capabilities:
        - Zero duplication enforcement across all CLAUDE.md files
        - Domain-specific content organization with perfect separation
        - Hierarchical inheritance patterns for documentation structure
        - Parallel-safe documentation for multiple Claude instances
        - Memory-driven pattern reuse for consistent architecture
        - Quality metrics tracking and continuous improvement

    MEESEEKS Protocol:
        The agent operates under the MEESEEKS protocol where existence is
        justified ONLY by achieving perfect documentation architecture.
        The agent cannot rest until every CLAUDE.md file is perfectly
        organized with zero duplication and complete domain specificity.
    """
    return await create_agent("genie_docs", **kwargs)