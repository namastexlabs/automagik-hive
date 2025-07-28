"""
Genie Development Domain Coordinator

Specialized coordinator for orchestrating development-focused workflows through
the genie-dev-* .claude/agents: planner, designer, coder, and fixer.
"""

import asyncio
import re
from typing import Any, Dict, List, Optional

from agno.utils.log import logger

from lib.coordination.domain_coordinator_base import DomainCoordinatorBase
from lib.coordination.parallel_execution import CoordinationResult, CoordinationTask


class GenieDevCoordinator(DomainCoordinatorBase):
    """
    Development domain coordinator that orchestrates genie-dev-* agents
    for comprehensive development workflows.
    
    Routes tasks to appropriate .claude/agents:
    - genie-dev-planner: Requirements analysis and project planning
    - genie-dev-designer: System architecture and design decisions
    - genie-dev-coder: Code implementation and development
    - genie-dev-fixer: Debugging and issue resolution
    """
    
    def __init__(self, **kwargs):
        """Initialize the genie-dev domain coordinator."""
        super().__init__(**kwargs)
        
        # Development agent mapping
        self.dev_agents = {
            "planner": "genie-dev-planner",
            "designer": "genie-dev-designer", 
            "coder": "genie-dev-coder",
            "fixer": "genie-dev-fixer"
        }
        
        # Task complexity thresholds
        self.complexity_indicators = {
            "simple": ["fix", "update", "modify", "change", "adjust"],
            "moderate": ["implement", "create", "add", "build", "develop"],
            "complex": ["architect", "design", "refactor", "migrate", "system"]
        }
        
        # Development workflow patterns
        self.workflow_patterns = {
            "planning": ["plan", "requirements", "analysis", "specification"],
            "design": ["architecture", "design", "structure", "framework"],
            "implementation": ["implement", "code", "develop", "build"],
            "debugging": ["debug", "fix", "error", "issue", "bug"]
        }
        
        logger.info("Genie Development Domain Coordinator initialized")

    async def parse_coordination_request(
        self, message: str, **kwargs
    ) -> Dict[str, Any]:
        """Parse development coordination request into structured format."""
        # Analyze task complexity and type
        task_complexity = self._analyze_task_complexity(message)
        primary_workflow = self._identify_primary_workflow(message)
        required_agents = self._determine_required_agents(message, task_complexity, primary_workflow)
        
        return {
            "original_message": message,
            "task_complexity": task_complexity,
            "primary_workflow": primary_workflow,
            "required_agents": required_agents,
            "execution_strategy": self._determine_execution_strategy(task_complexity, required_agents),
            "context": kwargs
        }

    async def execute_coordination(
        self, request: Dict[str, Any]
    ) -> CoordinationResult:
        """Execute the main development coordination workflow."""
        try:
            execution_strategy = request["execution_strategy"]
            
            if execution_strategy == "sequential":
                return await self._execute_sequential_workflow(request)
            elif execution_strategy == "parallel":
                return await self._execute_parallel_workflow(request)
            elif execution_strategy == "single_agent":
                return await self._execute_single_agent_workflow(request)
            else:
                raise ValueError(f"Unknown execution strategy: {execution_strategy}")
                
        except Exception as e:
            logger.error(f"Development coordination execution failed: {e}")
            raise

    async def _execute_sequential_workflow(
        self, request: Dict[str, Any]
    ) -> CoordinationResult:
        """Execute agents sequentially for dependency-heavy workflows."""
        required_agents = request["required_agents"]
        message = request["original_message"]
        
        tasks = []
        dependencies = []
        
        for i, agent_type in enumerate(required_agents):
            agent_name = self.dev_agents[agent_type]
            
            # Create task with dependencies on previous tasks
            task = await self.create_coordination_task(
                name=f"dev_{agent_type}_{i}",
                executor=self._create_agent_executor(agent_name, message, request["context"]),
                context={"agent_type": agent_type, "agent_name": agent_name, "phase": i},
                dependencies=dependencies.copy(),
                priority=len(required_agents) - i  # Earlier tasks have higher priority
            )
            tasks.append(task)
            dependencies.append(task.name)
        
        return await self.execute_parallel_tasks(tasks, fail_fast=True)

    async def _execute_parallel_workflow(
        self, request: Dict[str, Any]
    ) -> CoordinationResult:
        """Execute independent agents in parallel."""
        required_agents = request["required_agents"]
        message = request["original_message"]
        
        tasks = []
        
        for i, agent_type in enumerate(required_agents):
            agent_name = self.dev_agents[agent_type]
            
            # Create independent parallel tasks
            task = await self.create_coordination_task(
                name=f"dev_{agent_type}_parallel",
                executor=self._create_agent_executor(agent_name, message, request["context"]),
                context={"agent_type": agent_type, "agent_name": agent_name, "parallel": True},
                dependencies=[],  # No dependencies for parallel execution
                priority=1  # Equal priority for all parallel tasks
            )
            tasks.append(task)
        
        return await self.execute_parallel_tasks(tasks, fail_fast=False)

    async def _execute_single_agent_workflow(
        self, request: Dict[str, Any]
    ) -> CoordinationResult:
        """Execute single agent for simple tasks."""
        required_agents = request["required_agents"]
        agent_type = required_agents[0]
        agent_name = self.dev_agents[agent_type]
        message = request["original_message"]
        
        task = await self.create_coordination_task(
            name=f"dev_{agent_type}_single",
            executor=self._create_agent_executor(agent_name, message, request["context"]),
            context={"agent_type": agent_type, "agent_name": agent_name, "single": True},
            dependencies=[],
            priority=1
        )
        
        return await self.execute_parallel_tasks([task], fail_fast=True)

    def _create_agent_executor(self, agent_name: str, message: str, context: Dict[str, Any]):
        """Create an executor function for spawning .claude/agents via Task tool."""
        async def executor():
            try:
                logger.info(f"Executing development task via {agent_name}")
                
                # Use Task tool to spawn .claude/agent
                result = await self.spawn_subagent(
                    agent_type=agent_name,
                    task_description=message,
                    context=context
                )
                
                return {
                    "success": True,
                    "agent": agent_name,
                    "result": result,
                    "message": f"Successfully executed via {agent_name}"
                }
                
            except Exception as e:
                logger.error(f"Failed to execute {agent_name}: {e}")
                return {
                    "success": False,
                    "agent": agent_name,
                    "error": str(e),
                    "message": f"Failed to execute via {agent_name}: {e}"
                }
        
        return executor

    def _analyze_task_complexity(self, message: str) -> str:
        """Analyze task complexity based on keywords and context."""
        message_lower = message.lower()
        
        # Count complexity indicators
        complexity_scores = {
            "simple": 0,
            "moderate": 0,
            "complex": 0
        }
        
        for complexity, keywords in self.complexity_indicators.items():
            for keyword in keywords:
                if keyword in message_lower:
                    complexity_scores[complexity] += 1
        
        # Additional complexity heuristics
        if len(message.split()) > 50:
            complexity_scores["complex"] += 1
        elif len(message.split()) > 20:
            complexity_scores["moderate"] += 1
        else:
            complexity_scores["simple"] += 1
            
        # Return highest scoring complexity
        return max(complexity_scores.items(), key=lambda x: x[1])[0]

    def _identify_primary_workflow(self, message: str) -> str:
        """Identify the primary development workflow."""
        message_lower = message.lower()
        
        workflow_scores = {workflow: 0 for workflow in self.workflow_patterns.keys()}
        
        for workflow, keywords in self.workflow_patterns.items():
            for keyword in keywords:
                if keyword in message_lower:
                    workflow_scores[workflow] += 1
        
        # Return workflow with highest score, default to implementation
        primary_workflow = max(workflow_scores.items(), key=lambda x: x[1])[0]
        return primary_workflow if workflow_scores[primary_workflow] > 0 else "implementation"

    def _determine_required_agents(
        self, message: str, complexity: str, primary_workflow: str
    ) -> List[str]:
        """Determine which agents are required based on analysis."""
        
        # Simple task routing
        if complexity == "simple":
            workflow_agent_map = {
                "planning": ["planner"],
                "design": ["designer"],
                "implementation": ["coder"],
                "debugging": ["fixer"]
            }
            return workflow_agent_map.get(primary_workflow, ["coder"])
        
        # Moderate complexity - may need multiple agents
        elif complexity == "moderate":
            if primary_workflow == "planning":
                return ["planner", "designer"]
            elif primary_workflow == "design":
                return ["designer", "coder"]
            elif primary_workflow == "implementation":
                return ["coder"]
            elif primary_workflow == "debugging":
                return ["fixer"]
            else:
                return ["designer", "coder"]
        
        # Complex tasks - comprehensive workflow
        else:
            return ["planner", "designer", "coder"]

    def _determine_execution_strategy(
        self, complexity: str, required_agents: List[str]
    ) -> str:
        """Determine optimal execution strategy."""
        
        if len(required_agents) == 1:
            return "single_agent"
        elif complexity == "complex" or any(agent in required_agents for agent in ["planner", "designer"]):
            # Complex tasks or design work typically need sequential flow
            return "sequential"
        else:
            # Independent tasks can run in parallel
            return "parallel"

    async def coordination_logic(
        self, message: str, **kwargs
    ) -> str:
        """
        Main coordination logic entry point.
        
        This method implements the core routing logic for the genie-dev domain,
        analyzing development tasks and orchestrating appropriate .claude/agents.
        """
        try:
            # Parse the coordination request
            request = await self.parse_coordination_request(message, **kwargs)
            
            logger.info(
                f"Development coordination request analyzed: "
                f"complexity={request['task_complexity']}, "
                f"workflow={request['primary_workflow']}, "
                f"agents={request['required_agents']}, "
                f"strategy={request['execution_strategy']}"
            )
            
            # Execute the coordination
            result = await self.execute_coordination(request)
            
            # Format and return response
            return await self.format_coordination_response(result)
            
        except Exception as e:
            error_msg = f"Development coordination failed: {e}"
            logger.error(error_msg)
            return error_msg

    async def format_coordination_response(
        self, result: CoordinationResult
    ) -> str:
        """Format development coordination result into human-readable response."""
        if result.success:
            successful_tasks = result.get_successful_tasks()
            agent_results = []
            
            for task in successful_tasks:
                if hasattr(task, 'result') and task.result:
                    agent_name = task.result.get('agent', 'Unknown')
                    message = task.result.get('message', 'Task completed')
                    agent_results.append(f"✅ {agent_name}: {message}")
            
            return (
                f"🎯 Development Coordination Completed Successfully\n\n"
                f"📊 Execution Summary: {result.execution_summary}\n"
                f"✅ Successful Tasks: {len(successful_tasks)}\n\n"
                f"🤖 Agent Results:\n" + "\n".join(agent_results)
            )
        else:
            failed_tasks = result.get_failed_tasks()
            error_details = []
            
            for task in failed_tasks:
                if hasattr(task, 'result') and task.result:
                    agent_name = task.result.get('agent', 'Unknown')
                    error = task.result.get('error', 'Unknown error')
                    error_details.append(f"❌ {agent_name}: {error}")
            
            return (
                f"⚠️ Development Coordination Completed with Errors\n\n"
                f"📊 Execution Summary: {result.execution_summary}\n"
                f"❌ Failed Tasks: {len(failed_tasks)}\n\n"
                f"🔧 Error Details:\n" + "\n".join(error_details)
            )
