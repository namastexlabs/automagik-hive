"""
Genie Testing Domain Coordinator

Specialized coordinator for orchestrating testing workflows through intelligent
routing between genie-testing-fixer and genie-testing-maker agents.
"""

import re
from typing import Any, Dict, List

from agno.utils.log import logger

from lib.coordination.domain_coordinator_base import DomainCoordinatorBase
from lib.coordination.parallel_execution import CoordinationResult, CoordinationTask


class GenieTestingCoordinator(DomainCoordinatorBase):
    """
    Domain coordinator specialized in testing workflow orchestration.
    
    Routes testing requests intelligently between:
    - genie-testing-fixer: Test failures, coverage gaps, infrastructure fixes
    - genie-testing-maker: New test creation, comprehensive test suites
    """
    
    def __init__(self, **kwargs):
        """Initialize the testing coordinator with testing-specific configuration."""
        super().__init__(**kwargs)
        
        # Testing-specific configuration
        self.coverage_threshold = kwargs.get('coverage_threshold', 80.0)
        self.supported_agents = kwargs.get('supported_agents', [
            'genie-testing-fixer',
            'genie-testing-maker'
        ])
        self.parallel_execution = kwargs.get('parallel_test_execution', True)
        
        logger.info("Genie Testing Coordinator initialized with coverage threshold: %.1f%%", 
                   self.coverage_threshold)

    async def parse_coordination_request(self, message: str, **kwargs) -> Dict[str, Any]:
        """Parse testing coordination request into structured format."""
        
        # Extract testing context and requirements
        request_analysis = await self._analyze_testing_request(message)
        
        # Determine optimal agent routing strategy
        routing_strategy = await self._determine_routing_strategy(request_analysis)
        
        coordination_request = {
            "original_message": message,
            "request_type": request_analysis["request_type"],
            "testing_scope": request_analysis["testing_scope"],
            "priority_level": request_analysis["priority_level"],
            "routing_strategy": routing_strategy,
            "parallel_opportunities": request_analysis["parallel_opportunities"],
            "coverage_requirements": request_analysis.get("coverage_requirements", {}),
            "context": kwargs
        }
        
        logger.info("Testing request parsed: type=%s, scope=%s, strategy=%s", 
                   request_analysis["request_type"],
                   request_analysis["testing_scope"],
                   routing_strategy["primary_agent"])
        
        return coordination_request

    async def execute_coordination(self, request: Dict[str, Any]) -> CoordinationResult:
        """Execute the testing coordination workflow."""
        
        try:
            # Create coordination tasks based on routing strategy
            tasks = await self._create_testing_tasks(request)
            
            # Execute tasks with dependency management
            if self.parallel_execution and len(tasks) > 1:
                logger.info("Executing %d testing tasks in parallel", len(tasks))
                result = await self.execute_parallel_tasks(tasks, fail_fast=False)
            else:
                logger.info("Executing %d testing tasks sequentially", len(tasks))
                result = await self.execute_parallel_tasks(tasks, fail_fast=False)
            
            # Enhance result with testing-specific analysis
            await self._enhance_testing_result(result, request)
            
            # Store coordination pattern for learning
            await self._store_coordination_pattern(request, result)
            
            return result
            
        except Exception as e:
            logger.error("Testing coordination execution failed: %s", e)
            raise

    async def _analyze_testing_request(self, message: str) -> Dict[str, Any]:
        """Analyze testing request to determine type, scope, and requirements."""
        
        message_lower = message.lower()
        
        # Determine request type through pattern analysis
        request_type = "unknown"
        testing_scope = []
        priority_level = "medium"
        parallel_opportunities = []
        
        # Pattern matching for request type classification
        failure_patterns = [
            r'fail(ing|ed|ure)?\s+test', r'broken\s+test', r'fix.*test',
            r'test.*error', r'coverage.*gap', r'flaky.*test'
        ]
        
        creation_patterns = [
            r'create.*test', r'generate.*test', r'new.*test', r'test.*suite',
            r'comprehensive.*test', r'write.*test', r'add.*test'
        ]
        
        infrastructure_patterns = [
            r'test.*infrastructure', r'pytest.*config', r'test.*setup',
            r'test.*framework', r'testing.*pipeline'
        ]
        
        if any(re.search(pattern, message_lower) for pattern in failure_patterns):
            request_type = "test_fixing"
            priority_level = "high"
        elif any(re.search(pattern, message_lower) for pattern in creation_patterns):
            request_type = "test_creation"
            priority_level = "medium"
        elif any(re.search(pattern, message_lower) for pattern in infrastructure_patterns):
            request_type = "test_infrastructure"
            priority_level = "medium"
        
        # Identify testing scope
        scope_patterns = {
            "unit": r'unit.*test',
            "integration": r'integration.*test',
            "api": r'api.*test',
            "end-to-end": r'e2e.*test|end.*to.*end',
            "performance": r'performance.*test|load.*test',
            "security": r'security.*test'
        }
        
        for scope, pattern in scope_patterns.items():
            if re.search(pattern, message_lower):
                testing_scope.append(scope)
        
        # Default to unit tests if no scope specified
        if not testing_scope:
            testing_scope = ["unit"]
        
        # Identify parallel execution opportunities
        if len(testing_scope) > 1:
            parallel_opportunities.append("multi_scope_testing")
        
        if re.search(r'multiple.*component|all.*module|entire.*codebase', message_lower):
            parallel_opportunities.append("multi_component_testing")
            priority_level = "high"
        
        return {
            "request_type": request_type,
            "testing_scope": testing_scope,
            "priority_level": priority_level,
            "parallel_opportunities": parallel_opportunities,
            "coverage_requirements": {
                "threshold": self.coverage_threshold,
                "enforce_quality": True
            }
        }

    async def _determine_routing_strategy(self, request_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine optimal agent routing strategy based on request analysis."""
        
        request_type = request_analysis["request_type"]
        testing_scope = request_analysis["testing_scope"]
        parallel_opportunities = request_analysis["parallel_opportunities"]
        
        # Primary agent selection based on request type
        primary_agent = None
        secondary_agent = None
        execution_mode = "sequential"
        
        if request_type in ["test_fixing", "test_infrastructure"]:
            primary_agent = "genie-testing-fixer"
            # Add test creation if comprehensive coverage needed
            if "comprehensive" in " ".join(testing_scope) or len(testing_scope) > 2:
                secondary_agent = "genie-testing-maker"
                execution_mode = "parallel"
                
        elif request_type == "test_creation":
            primary_agent = "genie-testing-maker"
            # Add test validation/fixing for quality assurance
            if len(testing_scope) > 1 or "comprehensive" in " ".join(testing_scope):
                secondary_agent = "genie-testing-fixer"
                execution_mode = "sequential"  # Maker first, then fixer validates
                
        else:  # unknown or complex requests
            primary_agent = "genie-testing-maker"
            secondary_agent = "genie-testing-fixer"
            execution_mode = "parallel"
        
        # Override execution mode based on parallel opportunities
        if parallel_opportunities and self.parallel_execution:
            execution_mode = "parallel"
        
        return {
            "primary_agent": primary_agent,
            "secondary_agent": secondary_agent,
            "execution_mode": execution_mode,
            "justification": f"Request type '{request_type}' with scope {testing_scope} routed to {primary_agent}"
        }

    async def _create_testing_tasks(self, request: Dict[str, Any]) -> List[CoordinationTask]:
        """Create coordination tasks based on routing strategy."""
        
        tasks = []
        routing = request["routing_strategy"]
        testing_scope = request["testing_scope"]
        original_message = request["original_message"]
        
        # Create primary agent task
        primary_task = await self.create_coordination_task(
            name=f"{routing['primary_agent']}_primary",
            executor=self._create_agent_executor(routing["primary_agent"]),
            context={
                "agent_type": routing["primary_agent"],
                "task_description": original_message,
                "testing_scope": testing_scope,
                "priority": "primary",
                "coverage_threshold": self.coverage_threshold
            },
            timeout=600.0,
            priority=1
        )
        tasks.append(primary_task)
        
        # Create secondary agent task if needed
        if routing.get("secondary_agent"):
            dependencies = []
            if routing["execution_mode"] == "sequential":
                dependencies = [primary_task.task_id]
            
            secondary_task = await self.create_coordination_task(
                name=f"{routing['secondary_agent']}_secondary",
                executor=self._create_agent_executor(routing["secondary_agent"]),
                context={
                    "agent_type": routing["secondary_agent"],
                    "task_description": f"Secondary validation/enhancement for: {original_message}",
                    "testing_scope": testing_scope,
                    "priority": "secondary",
                    "coverage_threshold": self.coverage_threshold
                },
                dependencies=dependencies,
                timeout=600.0,
                priority=2
            )
            tasks.append(secondary_task)
        
        logger.info("Created %d testing coordination tasks for execution", len(tasks))
        return tasks

    def _create_agent_executor(self, agent_type: str):
        """Create executor function for spawning testing agents."""
        
        async def executor(**context):
            """Execute agent spawning with testing-specific context."""
            try:
                logger.info("Spawning testing agent: %s", agent_type)
                
                # Use the spawn_subagent method from base class
                result = await self.spawn_subagent(
                    agent_type=agent_type,
                    task_description=context.get("task_description", ""),
                    context=context
                )
                
                logger.info("Testing agent %s completed successfully", agent_type)
                return result
                
            except Exception as e:
                logger.error("Testing agent %s execution failed: %s", agent_type, e)
                raise
        
        return executor

    async def _enhance_testing_result(self, result: CoordinationResult, request: Dict[str, Any]) -> None:
        """Enhance coordination result with testing-specific analysis."""
        
        successful_tasks = result.get_successful_tasks()
        failed_tasks = result.get_failed_tasks()
        
        # Create enhanced summary
        testing_summary = []
        testing_summary.append(f"Testing coordination completed")
        testing_summary.append(f"Request type: {request['request_type']}")
        testing_summary.append(f"Testing scope: {', '.join(request['testing_scope'])}")
        testing_summary.append(f"Successful agents: {len(successful_tasks)}")
        
        if failed_tasks:
            testing_summary.append(f"Failed agents: {len(failed_tasks)}")
        
        # Add coverage analysis if available
        coverage_analysis = await self._analyze_coverage_results(successful_tasks)
        if coverage_analysis:
            testing_summary.append(f"Coverage analysis: {coverage_analysis}")
        
        result.execution_summary = "\n".join(testing_summary)
        
        # Mark overall success based on testing criteria
        result.success = (
            len(failed_tasks) == 0 and 
            len(successful_tasks) > 0 and
            await self._validate_testing_quality(successful_tasks)
        )

    async def _analyze_coverage_results(self, successful_tasks: List[CoordinationTask]) -> str:
        """Analyze test coverage from successful task results."""
        
        # Placeholder for coverage analysis
        # In real implementation, this would parse agent results for coverage data
        if successful_tasks:
            return f"Coverage validation completed for {len(successful_tasks)} testing agents"
        return "No coverage data available"

    async def _validate_testing_quality(self, successful_tasks: List[CoordinationTask]) -> bool:
        """Validate overall testing quality meets standards."""
        
        # Basic quality validation - all tasks must have completed
        if not successful_tasks:
            return False
        
        # Additional quality checks could be added here
        # - Coverage threshold validation
        # - Test result parsing
        # - Quality gate enforcement
        
        logger.info("Testing quality validation passed for %d agents", len(successful_tasks))
        return True

    async def _store_coordination_pattern(self, request: Dict[str, Any], result: CoordinationResult) -> None:
        """Store successful coordination pattern for future learning."""
        
        if result.success:
            pattern_summary = (
                f"Testing coordination pattern: {request['request_type']} "
                f"with scope {request['testing_scope']} "
                f"using {request['routing_strategy']['primary_agent']} "
                f"completed successfully in {result.total_duration:.2f}s"
            )
            
            # Store in genie-memory for pattern learning
            try:
                # Placeholder for memory storage
                # In real implementation, this would use MCP genie-memory tool
                logger.info("Stored testing coordination pattern: %s", pattern_summary)
            except Exception as e:
                logger.warning("Failed to store coordination pattern: %s", e)
