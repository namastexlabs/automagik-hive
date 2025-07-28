"""
Genie Quality Domain Coordinator

Intelligent quality-focused coordinator that manages code formatting, type checking,
and comprehensive quality assurance through intelligent routing to specialized .claude/agents.
"""

import asyncio
from typing import Any, Dict, List

from agno.utils.log import logger

from lib.coordination.domain_coordinator_base import DomainCoordinatorBase
from lib.coordination.parallel_execution import CoordinationResult, CoordinationTask


class GenieQualityCoordinator(DomainCoordinatorBase):
    """
    Quality domain coordinator that orchestrates code quality tasks through
    intelligent routing to specialized .claude/agents.
    
    Manages:
    - genie-quality-ruff: Ruff formatting and linting
    - genie-quality-mypy: MyPy type checking and annotations  
    - genie-quality-format: Comprehensive quality orchestration
    """
    
    def __init__(self, **kwargs):
        """Initialize the Genie Quality Coordinator."""
        super().__init__(**kwargs)
        
        # Quality-specific agents mapping
        self.quality_agents = {
            "ruff": "genie-quality-ruff",
            "mypy": "genie-quality-mypy", 
            "format": "genie-quality-format",
            "comprehensive": "genie-quality-format"  # Alias for comprehensive quality
        }
        
        # Quality task priority mapping
        self.task_priorities = {
            "format": 1,      # High priority - foundational formatting
            "lint": 1,        # High priority - code quality issues
            "type_check": 2,  # Medium priority - type safety
            "comprehensive": 3 # Lower priority - comprehensive orchestration
        }
        
        logger.info("Genie Quality Coordinator initialized with quality agents")

    async def parse_coordination_request(
        self, message: str, **kwargs
    ) -> Dict[str, Any]:
        """Parse quality-focused coordination request into structured format."""
        
        # Extract quality context from the message
        quality_request = {
            "original_message": message,
            "quality_type": "comprehensive",  # Default to comprehensive
            "target_files": kwargs.get("files", []),
            "fix_mode": kwargs.get("fix", True),
            "check_only": kwargs.get("check_only", False),
            "context": kwargs
        }
        
        # Intelligent quality type detection
        message_lower = message.lower()
        
        if any(term in message_lower for term in ["ruff", "format", "lint", "style"]):
            quality_request["quality_type"] = "ruff"
        elif any(term in message_lower for term in ["mypy", "type", "annotation", "typing"]):
            quality_request["quality_type"] = "mypy"
        elif any(term in message_lower for term in ["format", "fix", "quality", "comprehensive"]):
            quality_request["quality_type"] = "format"
        
        # Detect specific quality operations
        if "fix" in message_lower or "format" in message_lower:
            quality_request["operation"] = "fix"
        elif "check" in message_lower or "validate" in message_lower:
            quality_request["operation"] = "check"
        else:
            quality_request["operation"] = "fix"  # Default to fix mode
            
        logger.info(f"Parsed quality request: {quality_request['quality_type']} operation: {quality_request['operation']}")
        
        return quality_request

    async def execute_coordination(
        self, request: Dict[str, Any]
    ) -> CoordinationResult:
        """Execute quality coordination workflow with intelligent routing."""
        
        quality_type = request.get("quality_type", "comprehensive")
        operation = request.get("operation", "fix")
        
        logger.info(f"Executing quality coordination: {quality_type} - {operation}")
        
        # Route to appropriate coordination logic based on quality type
        if quality_type == "ruff":
            return await self._execute_ruff_coordination(request)
        elif quality_type == "mypy":
            return await self._execute_mypy_coordination(request)
        elif quality_type in ["format", "comprehensive"]:
            return await self._execute_comprehensive_coordination(request)
        else:
            # Fallback to comprehensive quality
            logger.warning(f"Unknown quality type '{quality_type}', falling back to comprehensive")
            return await self._execute_comprehensive_coordination(request)

    async def _execute_ruff_coordination(self, request: Dict[str, Any]) -> CoordinationResult:
        """Execute Ruff-specific quality coordination."""
        
        logger.info("Executing Ruff quality coordination")
        
        # Create Ruff-specific task
        ruff_task = await self.create_coordination_task(
            name="ruff_quality",
            executor=self._spawn_ruff_agent,
            context={
                "agent_type": self.quality_agents["ruff"],
                "request": request,
                "task_description": f"Execute Ruff formatting and linting: {request['original_message']}"
            },
            priority=self.task_priorities.get("format", 1),
            timeout=300.0
        )
        
        # Execute the task
        return await self.execute_parallel_tasks([ruff_task])

    async def _execute_mypy_coordination(self, request: Dict[str, Any]) -> CoordinationResult:
        """Execute MyPy-specific quality coordination."""
        
        logger.info("Executing MyPy quality coordination")
        
        # Create MyPy-specific task  
        mypy_task = await self.create_coordination_task(
            name="mypy_quality",
            executor=self._spawn_mypy_agent,
            context={
                "agent_type": self.quality_agents["mypy"],
                "request": request,
                "task_description": f"Execute MyPy type checking: {request['original_message']}"
            },
            priority=self.task_priorities.get("type_check", 2),
            timeout=300.0
        )
        
        # Execute the task
        return await self.execute_parallel_tasks([mypy_task])

    async def _execute_comprehensive_coordination(self, request: Dict[str, Any]) -> CoordinationResult:
        """Execute comprehensive quality coordination using the format orchestrator."""
        
        logger.info("Executing comprehensive quality coordination")
        
        # For comprehensive quality, we use the genie-quality-format agent
        # which orchestrates both Ruff and MyPy internally
        comprehensive_task = await self.create_coordination_task(
            name="comprehensive_quality",
            executor=self._spawn_format_agent,
            context={
                "agent_type": self.quality_agents["format"],
                "request": request,
                "task_description": f"Execute comprehensive quality process: {request['original_message']}"
            },
            priority=self.task_priorities.get("comprehensive", 3),
            timeout=600.0  # Longer timeout for comprehensive quality
        )
        
        # Execute the comprehensive task
        return await self.execute_parallel_tasks([comprehensive_task])

    async def _spawn_ruff_agent(self, **context) -> Dict[str, Any]:
        """Spawn the genie-quality-ruff agent for Ruff-specific tasks."""
        
        agent_type = context["agent_type"]
        request = context["request"]
        task_description = context["task_description"]
        
        try:
            logger.info(f"Spawning {agent_type} for Ruff quality tasks")
            
            # Use the subagent spawning capability from the base class
            result = await self.spawn_subagent(
                agent_type=agent_type,
                task_description=task_description,
                context={
                    "quality_type": "ruff",
                    "operation": request.get("operation", "fix"),
                    "target_files": request.get("target_files", []),
                    "fix_mode": request.get("fix_mode", True),
                    "original_request": request["original_message"]
                }
            )
            
            logger.info(f"Ruff agent {agent_type} execution completed")
            return result
            
        except Exception as e:
            logger.error(f"Failed to spawn Ruff agent {agent_type}: {e}")
            raise

    async def _spawn_mypy_agent(self, **context) -> Dict[str, Any]:
        """Spawn the genie-quality-mypy agent for MyPy-specific tasks."""
        
        agent_type = context["agent_type"]
        request = context["request"]
        task_description = context["task_description"]
        
        try:
            logger.info(f"Spawning {agent_type} for MyPy quality tasks")
            
            # Use the subagent spawning capability from the base class
            result = await self.spawn_subagent(
                agent_type=agent_type,
                task_description=task_description,
                context={
                    "quality_type": "mypy",
                    "operation": request.get("operation", "check"),
                    "target_files": request.get("target_files", []),
                    "check_only": request.get("check_only", False),
                    "original_request": request["original_message"]
                }
            )
            
            logger.info(f"MyPy agent {agent_type} execution completed")
            return result
            
        except Exception as e:
            logger.error(f"Failed to spawn MyPy agent {agent_type}: {e}")
            raise

    async def _spawn_format_agent(self, **context) -> Dict[str, Any]:
        """Spawn the genie-quality-format agent for comprehensive quality orchestration."""
        
        agent_type = context["agent_type"]
        request = context["request"]
        task_description = context["task_description"]
        
        try:
            logger.info(f"Spawning {agent_type} for comprehensive quality orchestration")
            
            # Use the subagent spawning capability from the base class
            result = await self.spawn_subagent(
                agent_type=agent_type,
                task_description=task_description,
                context={
                    "quality_type": "comprehensive",
                    "operation": request.get("operation", "fix"),
                    "target_files": request.get("target_files", []),
                    "fix_mode": request.get("fix_mode", True),
                    "check_only": request.get("check_only", False),
                    "original_request": request["original_message"]
                }
            )
            
            logger.info(f"Format agent {agent_type} execution completed")
            return result
            
        except Exception as e:
            logger.error(f"Failed to spawn format agent {agent_type}: {e}")
            raise

    def get_agent_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get capabilities of available quality agents."""
        
        return {
            "genie-quality-ruff": {
                "description": "Ruff formatting and linting specialist",
                "capabilities": ["code_formatting", "linting", "import_sorting", "style_fixing"],
                "priority": self.task_priorities.get("format", 1),
                "best_for": ["formatting", "style", "lint_fixes", "import_organization"]
            },
            "genie-quality-mypy": {
                "description": "MyPy type checking and annotation specialist", 
                "capabilities": ["type_checking", "annotation_generation", "type_safety", "static_analysis"],
                "priority": self.task_priorities.get("type_check", 2),
                "best_for": ["type_safety", "annotations", "static_analysis", "type_errors"]
            },
            "genie-quality-format": {
                "description": "Comprehensive quality orchestration coordinator",
                "capabilities": ["quality_orchestration", "ruff_coordination", "mypy_coordination", "comprehensive_quality"],
                "priority": self.task_priorities.get("comprehensive", 3),
                "best_for": ["comprehensive_quality", "full_formatting", "complete_quality_check", "quality_orchestration"]
            }
        }
