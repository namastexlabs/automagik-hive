"""
Parallel Execution Manager for Domain Coordinators
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

from agno.utils.log import logger


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class CoordinationTask:
    """Represents a coordination task that can be executed in parallel."""
    task_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    executor: Optional[Callable[..., Any]] = None
    dependencies: Set[str] = field(default_factory=set)
    timeout: float = 300.0
    retry_count: int = 3
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    
    # Internal state tracking
    status: TaskStatus = field(default=TaskStatus.PENDING, init=False)
    start_time: Optional[float] = field(default=None, init=False)
    end_time: Optional[float] = field(default=None, init=False)
    error: Optional[Exception] = field(default=None, init=False)
    result: Any = field(default=None, init=False)
    attempts: int = field(default=0, init=False)


@dataclass
class CoordinationResult:
    """Result of a coordination execution."""
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    tasks: Dict[str, CoordinationTask] = field(default_factory=dict)
    success: bool = False
    total_duration: float = 0.0
    failed_tasks: List[str] = field(default_factory=list)
    cancelled_tasks: List[str] = field(default_factory=list)
    execution_summary: str = ""
    
    def get_successful_tasks(self) -> List[CoordinationTask]:
        """Get all successfully completed tasks."""
        return [
            task for task in self.tasks.values() 
            if task.status == TaskStatus.COMPLETED
        ]
    
    def get_failed_tasks(self) -> List[CoordinationTask]:
        """Get all failed tasks."""
        return [
            task for task in self.tasks.values() 
            if task.status == TaskStatus.FAILED
        ]


class ParallelExecutionManager:
    """Manages parallel execution of coordination tasks."""
    
    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        default_timeout: float = 300.0,
        enable_retries: bool = True,
    ):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.default_timeout = default_timeout
        self.enable_retries = enable_retries
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def execute_tasks(
        self,
        tasks: List[CoordinationTask],
        fail_fast: bool = False,
        progress_callback: Optional[Callable[[str, TaskStatus], None]] = None,
    ) -> CoordinationResult:
        """Execute tasks with basic dependency management."""
        execution_id = str(uuid4())
        start_time = time.time()
        
        logger.info(f"Starting parallel execution {execution_id} with {len(tasks)} tasks")
        
        # Simple sequential execution for now
        task_map = {task.task_id: task for task in tasks}
        completed_tasks = []
        failed_tasks = []
        
        for task in tasks:
            try:
                if task.executor:
                    task.status = TaskStatus.RUNNING
                    task.start_time = time.time()
                    if progress_callback:
                        progress_callback(task.task_id, TaskStatus.RUNNING)
                    
                    task.result = await task.executor(**task.context)
                    task.status = TaskStatus.COMPLETED
                    task.end_time = time.time()
                    completed_tasks.append(task.task_id)
                    
                    if progress_callback:
                        progress_callback(task.task_id, TaskStatus.COMPLETED)
                        
            except Exception as e:
                task.error = e
                task.status = TaskStatus.FAILED
                task.end_time = time.time()
                failed_tasks.append(task.task_id)
                logger.error(f"Task {task.task_id} failed: {e}")
                
                if progress_callback:
                    progress_callback(task.task_id, TaskStatus.FAILED)
        
        total_duration = time.time() - start_time
        success = len(failed_tasks) == 0
        
        return CoordinationResult(
            execution_id=execution_id,
            tasks=task_map,
            success=success,
            total_duration=total_duration,
            failed_tasks=failed_tasks,
            execution_summary=f"{len(completed_tasks)}/{len(tasks)} tasks completed in {total_duration:.2f}s",
        )
ENDFILE < /dev/null
