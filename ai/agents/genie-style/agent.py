"""
Genie Style Agent - Code Style Perfection Meeseeks

This agent mirrors the .claude/agents/genie-style.md personality and instructions exactly
but is enhanced with Agno memory/state management for persistent style/formatting context.
Specializes in incremental file-by-file processing with checkpoint commits for safety.
"""

from typing import Any

from agno.agent import Agent

from lib.utils.version_factory import create_agent


async def get_genie_style_agent(**kwargs: Any) -> Agent:
    """
    Create genie style agent with enhanced Agno memory and state management.

    This factory function creates a specialized code style perfectionist agent that:
    
    - Enforces perfect code formatting using Ruff (Black-compatible)
    - Achieves zero linting violations across entire codebase
    - Ensures bulletproof type safety with MyPy strict mode
    - Uses incremental file-by-file processing with checkpoint commits
    - Maintains persistent memory of style patterns and enforcement strategies
    - Provides enhanced state management for complex formatting contexts

    Enhanced Memory Features:
    - 30 run history with 180-day retention for pattern recognition
    - Agentic memory for persistent style enforcement strategies
    - Memory references for cross-session style consistency
    - Session summaries for complex multi-file formatting operations

    State Management:
    - Context-aware formatting decisions based on project patterns
    - Incremental progress tracking with checkpoint validation
    - Persistent storage of successful enforcement techniques
    - Enhanced error recovery with backup and restoration

    Processing Safety Features:
    - ONE FILE AT A TIME processing to prevent cascade failures
    - Checkpoint git commits after each successful file processing
    - Git status validation between files for safety
    - File backup and restoration on processing failures
    - Progress reporting with memory persistence

    Args:
        **kwargs: Context parameters for agent configuration including:
            - user_id: User identifier for personalized style preferences
            - project_context: Project-specific formatting requirements
            - style_preferences: Custom formatting and linting configurations
            - debug_mode: Enable detailed processing diagnostics
            - safety_mode: Enhanced validation and backup procedures
            - incremental_mode: Force one-file-at-a-time processing
            - checkpoint_pattern: Custom git commit message patterns
            - memory_context: Additional context for persistent memory

    Returns:
        Agent instance with enhanced memory/state management for code style perfection

    Example Usage:
        # Basic style enforcement
        agent = await get_genie_style_agent(
            user_id="dev_123",
            project_context="python_enterprise"
        )

        # Enhanced incremental processing
        agent = await get_genie_style_agent(
            user_id="dev_456",
            project_context="microservices_api",
            style_preferences={
                "line_length": 88,
                "quote_style": "double",
                "import_organization": "strict"
            },
            safety_mode=True,
            incremental_mode=True,
            checkpoint_pattern="style({filename}): enforce perfect formatting and type safety",
            memory_context={
                "codebase_type": "enterprise_python",
                "team_style_guide": "black_compatible",
                "quality_standards": "strict_mypy"
            }
        )

    Processing Capabilities:
        # Formatting Excellence
        - Ruff formatting with Black-compatible settings
        - Perfect indentation, spacing, and line length
        - Organized imports with dependency management
        
        # Linting Mastery  
        - Comprehensive rule enforcement (E, W, F, I, N, D, UP, etc.)
        - Code quality and complexity validation
        - Best practices and convention enforcement
        
        # Type Safety
        - MyPy strict mode compliance
        - Complete type annotation coverage
        - Generic usage and Optional handling
        
        # Incremental Safety
        - Single-file processing with checkpoints
        - Git validation between file processing
        - Backup and restoration on failures
        - Progress tracking with memory persistence

    Memory Integration:
        The agent leverages genie-memory MCP tool for:
        - Storing successful style enforcement patterns
        - Learning from previous formatting decisions
        - Maintaining consistency across sessions
        - Building knowledge base of style solutions
        
        Enhanced Agno memory provides:
        - Persistent context across multiple runs
        - Pattern recognition for similar codebases
        - State preservation during complex operations
        - Intelligent adaptation to project requirements
    """
    return await create_agent("genie_style", **kwargs)