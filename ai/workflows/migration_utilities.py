"""
Migration utilities for transitioning Agno Workflows from 1.0 to 2.0 architecture.
This module provides tools for refactoring existing workflows to be compatible with
both current and future versions of the Agno framework.
"""

import json
import os
from typing import Dict, Any, Optional, List, Iterator, Union
from pathlib import Path
from datetime import datetime

from agno.workflow import Workflow, RunResponse, RunEvent
from agno.storage.postgres import PostgresStorage
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.utils.log import logger
from pydantic import BaseModel, Field, ConfigDict


class WorkflowMigrationInfo(BaseModel):
    """Information about a workflow migration status."""
    workflow_name: str = Field(description="Name of the workflow")
    original_version: str = Field(description="Original workflow version")
    migrated_version: str = Field(description="Migrated workflow version")
    migration_date: datetime = Field(description="Date of migration")
    migration_status: str = Field(description="Status of migration (completed, pending, failed)")
    migration_notes: Optional[str] = Field(description="Additional migration notes")


class WorkflowAnalyzer:
    """Analyzes existing workflows for migration readiness."""
    
    def __init__(self, workflows_dir: str = "ai/workflows"):
        self.workflows_dir = Path(workflows_dir)
        self.migration_log: List[WorkflowMigrationInfo] = []
    
    def analyze_workflow_structure(self, workflow_name: str) -> Dict[str, Any]:
        """Analyze the structure of a workflow for migration assessment."""
        workflow_path = self.workflows_dir / workflow_name
        
        analysis = {
            "workflow_name": workflow_name,
            "has_config_yaml": False,
            "has_models_dir": False,
            "has_workflow_py": False,
            "agents_count": 0,
            "models_count": 0,
            "migration_complexity": "unknown",
            "recommended_actions": []
        }
        
        # Check for configuration file
        config_path = workflow_path / "config.yaml"
        if config_path.exists():
            analysis["has_config_yaml"] = True
        else:
            analysis["recommended_actions"].append("Create config.yaml file")
        
        # Check for models directory
        models_path = workflow_path / "models"
        if models_path.exists():
            analysis["has_models_dir"] = True
            analysis["models_count"] = len(list(models_path.glob("*.py")))
        else:
            analysis["recommended_actions"].append("Create models directory with organized Pydantic models")
        
        # Check for workflow.py
        workflow_py_path = workflow_path / "workflow.py"
        if workflow_py_path.exists():
            analysis["has_workflow_py"] = True
            # Analyze workflow.py content
            with open(workflow_py_path, 'r') as f:
                content = f.read()
                # Count agents (rough estimation)
                analysis["agents_count"] = content.count("Agent(")
        else:
            analysis["recommended_actions"].append("Create workflow.py file")
        
        # Determine migration complexity
        if analysis["has_config_yaml"] and analysis["has_models_dir"] and analysis["has_workflow_py"]:
            analysis["migration_complexity"] = "low"
        elif analysis["has_workflow_py"]:
            analysis["migration_complexity"] = "medium"
        else:
            analysis["migration_complexity"] = "high"
        
        return analysis
    
    def get_migration_recommendations(self, workflow_name: str) -> List[str]:
        """Get specific migration recommendations for a workflow."""
        analysis = self.analyze_workflow_structure(workflow_name)
        recommendations = []
        
        if analysis["migration_complexity"] == "high":
            recommendations.extend([
                "Start with creating basic workflow structure",
                "Implement Pydantic models for data validation",
                "Add proper configuration management",
                "Create comprehensive unit tests"
            ])
        elif analysis["migration_complexity"] == "medium":
            recommendations.extend([
                "Extract models into separate files",
                "Add YAML configuration support",
                "Implement proper error handling",
                "Add session state management"
            ])
        else:  # low complexity
            recommendations.extend([
                "Optimize agent orchestration",
                "Add parallel execution where beneficial",
                "Implement streaming capabilities",
                "Add comprehensive logging"
            ])
        
        return recommendations


class WorkflowRefactorer:
    """Refactors workflows to follow modern Agno patterns."""
    
    def __init__(self, workflows_dir: str = "ai/workflows"):
        self.workflows_dir = Path(workflows_dir)
        self.config_loader = None
    
    def modernize_workflow_structure(self, workflow_name: str) -> bool:
        """
        Modernize a workflow to follow current best practices.
        This prepares workflows for eventual 2.0 migration.
        """
        workflow_path = self.workflows_dir / workflow_name
        
        try:
            # Create models directory if it doesn't exist
            models_path = workflow_path / "models"
            models_path.mkdir(exist_ok=True)
            
            # Create __init__.py in models directory
            init_file = models_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""Models for {} workflow."""\n'.format(workflow_name))
            
            # Create shared utilities if they don't exist
            shared_path = self.workflows_dir / "shared"
            shared_path.mkdir(exist_ok=True)
            
            # Create config loader if it doesn't exist
            self._ensure_config_loader_exists()
            
            logger.info(f"Modernized workflow structure for {workflow_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to modernize workflow {workflow_name}: {e}")
            return False
    
    def _ensure_config_loader_exists(self):
        """Ensure the shared config loader exists."""
        shared_path = self.workflows_dir / "shared"
        config_loader_path = shared_path / "config_loader.py"
        
        if not config_loader_path.exists():
            config_loader_content = '''"""
Centralized configuration loader for all workflows.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

class WorkflowConfigLoader:
    """Centralized configuration loader for all workflows."""
    
    def __init__(self, workflows_dir: str = "ai/workflows"):
        self.workflows_dir = Path(workflows_dir)
    
    def load_workflow_config(self, workflow_name: str) -> Dict[str, Any]:
        """Load configuration for a specific workflow."""
        config_path = self.workflows_dir / workflow_name / "config.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_model_config(self, workflow_name: str, model_key: str = "model") -> Dict[str, Any]:
        """Get model configuration for a workflow."""
        config = self.load_workflow_config(workflow_name)
        return config.get(model_key, {})
    
    def get_storage_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get storage configuration for a workflow."""
        config = self.load_workflow_config(workflow_name)
        return config.get("storage", {})
    
    def get_agents_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get agents configuration for a workflow."""
        config = self.load_workflow_config(workflow_name)
        return config.get("agents", {})
'''
            
            config_loader_path.write_text(config_loader_content)
            logger.info("Created shared config loader")
    
    def create_migration_ready_workflow(self, workflow_name: str, config: Dict[str, Any]) -> bool:
        """
        Create a workflow that's ready for future 2.0 migration.
        This follows current best practices while being step-migration ready.
        """
        workflow_path = self.workflows_dir / workflow_name
        workflow_path.mkdir(exist_ok=True)
        
        try:
            # Create config.yaml
            config_file = workflow_path / "config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            # Create models directory structure
            models_path = workflow_path / "models"
            models_path.mkdir(exist_ok=True)
            
            # Create base models
            base_models_content = '''"""
Base models for {} workflow.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class BaseWorkflowModel(BaseModel):
    """Base model for all workflow data structures."""
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class WorkflowResult(BaseWorkflowModel):
    """Base result model for workflow outputs."""
    
    success: bool = Field(description="Whether the workflow completed successfully")
    message: Optional[str] = Field(description="Result message")
    data: Optional[Dict[str, Any]] = Field(description="Result data")
    errors: Optional[List[str]] = Field(description="List of errors if any")
'''.format(workflow_name)
            
            base_models_file = models_path / "base.py"
            base_models_file.write_text(base_models_content)
            
            # Create workflow.py template
            workflow_content = '''"""
Modern {} workflow implementation.
"""

import os
from typing import Dict, Any, Optional, Iterator
from pathlib import Path

from agno.workflow import Workflow, RunResponse, RunEvent
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.utils.log import logger

from .models.base import BaseWorkflowModel, WorkflowResult
from ..shared.config_loader import WorkflowConfigLoader


class {}Workflow(Workflow):
    """
    Modern {} workflow implementation.
    
    This workflow follows current Agno best practices and is prepared
    for future migration to Workflows 2.0 step-based architecture.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_loader = WorkflowConfigLoader()
        self.workflow_name = "{}"
        self._setup_workflow()
    
    def _setup_workflow(self):
        """Initialize workflow configuration and components."""
        try:
            # Load configuration
            self.config = self.config_loader.load_workflow_config(self.workflow_name)
            
            # Setup storage
            storage_config = self.config.get("storage", {{}})
            if storage_config.get("type") == "postgres":
                self.storage = PostgresStorage(
                    table_name=storage_config.get("table_name", f"{self.workflow_name}_sessions"),
                    db_url=os.getenv("DATABASE_URL")
                )
            
            # Setup agents
            self._setup_agents()
            
        except Exception as e:
            logger.error(f"Failed to setup workflow {{self.workflow_name}}: {{e}}")
            raise
    
    def _setup_agents(self):
        """Initialize workflow agents."""
        agents_config = self.config.get("agents", {{}})
        
        # Create agents based on configuration
        for agent_name, agent_config in agents_config.items():
            model_config = agent_config.get("model", {{}})
            
            # Create model instance
            model = Claude(
                id=model_config.get("id", "claude-sonnet-4-20250514"),
                temperature=model_config.get("temperature", 0.7),
                max_tokens=model_config.get("max_tokens", 2000)
            )
            
            # Create agent
            agent = Agent(
                name=agent_config.get("name", agent_name),
                model=model,
                description=agent_config.get("description", ""),
                instructions=agent_config.get("instructions", []),
                tools=agent_config.get("tools", [])
            )
            
            # Set as attribute
            setattr(self, agent_name, agent)
    
    def run(self, **kwargs) -> Iterator[RunResponse]:
        """
        Execute the workflow.
        
        This method should be implemented by subclasses to define
        the specific workflow logic.
        """
        logger.info(f"Starting {{self.workflow_name}} workflow")
        
        try:
            # Workflow implementation goes here
            # This is where the step-based logic will be implemented
            # when migrating to Workflows 2.0
            
            yield RunResponse(
                run_id=self.run_id,
                content="Workflow template - implement specific logic",
                event=RunEvent.workflow_completed
            )
            
        except Exception as e:
            logger.error(f"Workflow {{self.workflow_name}} failed: {{e}}")
            yield RunResponse(
                run_id=self.run_id,
                content=f"Workflow failed: {{str(e)}}",
                event=RunEvent.workflow_completed
            )
'''.format(workflow_name, workflow_name.title(), workflow_name, workflow_name)
            
            workflow_file = workflow_path / "workflow.py"
            workflow_file.write_text(workflow_content)
            
            logger.info(f"Created migration-ready workflow: {workflow_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create workflow {workflow_name}: {e}")
            return False


class WorkflowMigrator:
    """Main migration orchestrator."""
    
    def __init__(self, workflows_dir: str = "ai/workflows"):
        self.workflows_dir = Path(workflows_dir)
        self.analyzer = WorkflowAnalyzer(workflows_dir)
        self.refactorer = WorkflowRefactorer(workflows_dir)
        self.migration_log: List[WorkflowMigrationInfo] = []
    
    def migrate_workflow(self, workflow_name: str) -> bool:
        """
        Migrate a workflow to modern standards.
        
        This performs the current migration to prepare for future 2.0 upgrade.
        """
        logger.info(f"Starting migration for workflow: {workflow_name}")
        
        try:
            # Analyze current structure
            analysis = self.analyzer.analyze_workflow_structure(workflow_name)
            logger.info(f"Workflow analysis: {analysis}")
            
            # Modernize structure
            if self.refactorer.modernize_workflow_structure(workflow_name):
                logger.info(f"Successfully modernized {workflow_name}")
                
                # Log migration
                migration_info = WorkflowMigrationInfo(
                    workflow_name=workflow_name,
                    original_version="1.0",
                    migrated_version="1.0-modern",
                    migration_date=datetime.now(),
                    migration_status="completed",
                    migration_notes=f"Modernized for 2.0 readiness. Complexity: {analysis['migration_complexity']}"
                )
                self.migration_log.append(migration_info)
                
                return True
            else:
                logger.error(f"Failed to modernize {workflow_name}")
                return False
                
        except Exception as e:
            logger.error(f"Migration failed for {workflow_name}: {e}")
            return False
    
    def get_migration_status(self) -> List[Dict[str, Any]]:
        """Get status of all migrations."""
        return [info.model_dump() for info in self.migration_log]
    
    def prepare_for_2_0_migration(self) -> Dict[str, Any]:
        """
        Prepare migration plan for when Workflows 2.0 becomes available.
        
        Returns a detailed migration plan and checklist.
        """
        return {
            "migration_plan": {
                "phase_1": {
                    "name": "Current Migration (1.0 → 1.0-modern)",
                    "status": "available",
                    "tasks": [
                        "Modernize workflow structure",
                        "Extract models into separate files",
                        "Add YAML configuration support",
                        "Implement proper error handling",
                        "Add session state management"
                    ]
                },
                "phase_2": {
                    "name": "Future Migration (1.0-modern → 2.0)",
                    "status": "pending_release",
                    "tasks": [
                        "Convert to step-based architecture",
                        "Implement parallel execution",
                        "Add conditional routing",
                        "Implement streaming capabilities",
                        "Add advanced error handling with retry strategies"
                    ]
                }
            },
            "readiness_checklist": [
                "All workflows have config.yaml files",
                "Models are properly organized",
                "Configuration loader is implemented",
                "Error handling is comprehensive",
                "Session state management is working",
                "Unit tests are comprehensive"
            ]
        }


def create_migration_utility():
    """Create a migration utility instance."""
    return WorkflowMigrator()


if __name__ == "__main__":
    # Example usage
    migrator = create_migration_utility()
    
    # Migrate existing workflows
    workflows_to_migrate = ["conversation_typification", "human_handoff"]
    
    for workflow_name in workflows_to_migrate:
        migrator.migrate_workflow(workflow_name)
    
    # Get migration status
    status = migrator.get_migration_status()
    print(f"Migration status: {status}")
    
    # Get 2.0 preparation plan
    plan = migrator.prepare_for_2_0_migration()
    print(f"2.0 Migration plan: {plan}")