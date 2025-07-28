"""
Base DomainCoordinator Framework

Abstract base class for domain coordinators that inherit from Agno Agent
and provide parallel orchestration capabilities with MCP tool integration.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from agno.utils.log import logger

from .parallel_execution import (
    CoordinationResult,
    CoordinationTask,
    ParallelExecutionManager,
    TaskStatus,
)


class DomainCoordinatorBase(Agent):
    """
    Abstract base class for domain coordinators.
    
    Inherits from Agno Agent to maintain compatibility with the existing framework
    while adding specialized coordination capabilities for complex workflows.
    """
    
    def __init__(self, **kwargs):
        """Initialize the domain coordinator."""
        super().__init__(**kwargs)
        
        # Initialize parallel execution manager
        self.execution_manager = ParallelExecutionManager(
            max_concurrent_tasks=kwargs.get('max_concurrent_tasks', 5),
            default_timeout=kwargs.get('default_timeout', 300.0),
            enable_retries=kwargs.get('enable_retries', True),
        )
        
        # Coordination state
        self.active_executions: Dict[str, CoordinationResult] = {}
        self.coordination_history: List[CoordinationResult] = []
        
        logger.info(f"Domain Coordinator {self.__class__.__name__} initialized")

    async def run(self, message: str, **kwargs) -> str:
        """Override Agno Agent run method to provide coordination-specific behavior."""
        try:
            # Parse the coordination request
            coordination_request = await self.parse_coordination_request(message, **kwargs)
            
            # Execute the coordination workflow
            result = await self.execute_coordination(coordination_request)
            
            # Store results for future reference
            self.coordination_history.append(result)
            
            # Return formatted response
            return await self.format_coordination_response(result)
            
        except Exception as e:
            error_msg = f"Coordination failed: {e}"
            logger.error(error_msg)
            return error_msg

    @abstractmethod
    async def parse_coordination_request(
        self, message: str, **kwargs
    ) -> Dict[str, Any]:
        """Parse incoming coordination request into structured format."""
        pass

    @abstractmethod
    async def execute_coordination(
        self, request: Dict[str, Any]
    ) -> CoordinationResult:
        """Execute the main coordination workflow."""
        pass

    async def format_coordination_response(
        self, result: CoordinationResult
    ) -> str:
        """Format coordination result into human-readable response."""
        if result.success:
            return (
                f"Coordination completed successfully\n"
                f"Summary: {result.execution_summary}\n"
                f"Tasks: {len(result.get_successful_tasks())} successful"
            )
        else:
            failed_tasks = result.get_failed_tasks()
            return (
                f"Coordination completed with errors\n"
                f"Summary: {result.execution_summary}\n"
                f"Failed tasks: {len(failed_tasks)}"
            )

    async def create_coordination_task(
        self,
        name: str,
        executor: callable,
        context: Dict[str, Any] = None,
        dependencies: List[str] = None,
        timeout: float = 300.0,
        priority: int = 0,
    ) -> CoordinationTask:
        """Create a coordination task for parallel execution."""
        return CoordinationTask(
            name=name,
            executor=executor,
            context=context or {},
            dependencies=set(dependencies or []),
            timeout=timeout,
            priority=priority,
        )

    async def execute_parallel_tasks(
        self,
        tasks: List[CoordinationTask],
        fail_fast: bool = False,
    ) -> CoordinationResult:
        """Execute multiple tasks in parallel with dependency management."""
        logger.info(f"Executing {len(tasks)} tasks in parallel")
        
        # Execute tasks using the parallel execution manager
        result = await self.execution_manager.execute_tasks(
            tasks=tasks,
            fail_fast=fail_fast,
            progress_callback=self._task_progress_callback,
        )
        
        # Store active execution
        self.active_executions[result.execution_id] = result
        
        logger.info(f"Parallel execution completed: {result.execution_summary}")
        return result

    def _task_progress_callback(self, task_id: str, status: TaskStatus) -> None:
        """Callback for task progress updates."""
        logger.debug(f"Task {task_id} status: {status.value}")

    async def spawn_subagent(
        self,
        agent_type: str,
        task_description: str,
        context: Dict[str, Any] = None,
    ) -> Any:
        """Spawn a subagent using MCP tools for Level 2 -> Level 3 communication."""
        try:
            logger.info(f"Spawning subagent {agent_type} for: {task_description}")
            
            # Placeholder for actual MCP tool integration
            return {
                "agent_type": agent_type,
                "task": task_description,
                "status": "spawned",
                "result": "Subagent execution placeholder"
            }
            
        except Exception as e:
            logger.error(f"Failed to spawn subagent {agent_type}: {e}")
            raise

    def get_execution_history(self) -> List[CoordinationResult]:
        """Get coordination execution history."""
        return self.coordination_history.copy()

    def get_active_executions(self) -> Dict[str, CoordinationResult]:
        """Get currently active executions."""
        return self.active_executions.copy()
ENDFILE < /dev/null
