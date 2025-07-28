"""
Genie Quality Domain Coordinator Package

Quality-focused domain coordinator that orchestrates code formatting, type checking,
and comprehensive quality assurance through intelligent routing to specialized .claude/agents.
"""

from .coordinator import GenieQualityCoordinator

__all__ = ["GenieQualityCoordinator"]
