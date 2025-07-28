"""
Coordination Framework for Automagik Hive

This module provides the base framework for domain coordinators that orchestrate
complex multi-agent workflows with parallel execution capabilities.
"""

from .domain_coordinator_base import DomainCoordinatorBase
from .parallel_execution import (
    CoordinationResult,
    CoordinationTask,
    ParallelExecutionManager,
    TaskStatus,
)

__all__ = [
    "DomainCoordinatorBase",
    "ParallelExecutionManager", 
    "CoordinationTask",
    "CoordinationResult",
    "TaskStatus",
]
EOF < /dev/null
