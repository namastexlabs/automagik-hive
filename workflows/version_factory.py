"""
Workflow Version Factory - Dynamic Workflow Creation from Database Configurations

Unified factory for creating workflows with specific version configurations
loaded from the database, enabling versioned workflow instantiation.
"""

from typing import Optional, Dict, Any
from agno.workflow import Workflow
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.utils.log import logger
from sqlalchemy.orm import Session

from db.session import get_db, db_url
from db.services.component_version_service import ComponentVersionService


def create_versioned_workflow(
    workflow_id: str,
    version: int,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    # User context parameters
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    cpf: Optional[str] = None,
    **kwargs
) -> Workflow:
    """
    Create a workflow instance using version-specific configuration from database.
    
    Args:
        workflow_id: Workflow identifier (e.g., "human_handoff")
        version: Version number to load
        session_id: Session ID for conversation tracking
        debug_mode: Enable debug mode
        user_id: User ID for session tracking
        user_name: User name for context
        phone_number: Phone number for context
        cpf: CPF for context
        **kwargs: Additional parameters
        
    Returns:
        Configured Workflow instance with version-specific configuration
        
    Raises:
        ValueError: If version not found or configuration invalid
    """
    
    # Get database session
    db: Session = next(get_db())
    
    try:
        # Load version-specific configuration
        service = ComponentVersionService(db)
        version_record = service.get_version(workflow_id, version)
        
        if not version_record:
            raise ValueError(f"Workflow version {version} not found for {workflow_id}")
        
        if version_record.component_type != "workflow":
            raise ValueError(f"Component {workflow_id} version {version} is not a workflow")
        
        config = version_record.config
        
        # Import specific workflow class based on workflow_id
        if workflow_id == "human-handoff":
            from workflows.human_handoff.workflow import HumanHandoffWorkflow
            workflow_class = HumanHandoffWorkflow
        elif workflow_id == "conversation-typification":
            from workflows.conversation_typification.workflow import get_conversation_typification_workflow
            # Use factory function instead of direct instantiation
            return get_conversation_typification_workflow(debug_mode=debug_mode)
        else:
            raise ValueError(f"Unknown workflow type: {workflow_id}")
        
        # Create workflow with version-specific configuration
        workflow = workflow_class(
            workflow_id=config.get("workflow", {}).get("workflow_id", workflow_id),
            session_id=session_id,
            user_id=user_id,
            debug_mode=debug_mode,
            description=config.get("workflow", {}).get("description"),
            storage=PostgresStorage(
                table_name=config.get("storage", {}).get("table_name", f"{workflow_id}_workflows"),
                db_url=db_url,
                auto_upgrade_schema=config.get("storage", {}).get("auto_upgrade_schema", True),
            ),
            # Workflow-specific parameters from config
            **{k: v for k, v in config.items() if k not in ["workflow", "storage", "model"]}
        )
        
        logger.info(f"✅ Created workflow {workflow_id} version {version}")
        return workflow
        
    except Exception as e:
        logger.error(f"❌ Failed to create workflow {workflow_id} version {version}: {str(e)}")
        raise
    finally:
        db.close()


def get_workflow_default_config(workflow_id: str) -> Dict[str, Any]:
    """
    Get default configuration for a workflow type.
    
    Args:
        workflow_id: Workflow identifier
        
    Returns:
        Default configuration dictionary
    """
    
    # Default workflow configurations
    defaults = {
        "human-handoff": {
            "workflow": {
                "workflow_id": "human-handoff",
                "name": "Human Handoff Workflow",
                "description": "Workflow simplificado para escalação humana"
            },
            "storage": {
                "type": "postgres",
                "table_name": "human-handoff-workflows",
                "auto_upgrade_schema": True
            },
            "whatsapp_enabled": True,
            "whatsapp_instance": "SofIA"
        },
        "conversation-typification": {
            "workflow": {
                "workflow_id": "conversation-typification",
                "name": "Conversation Typification Workflow",
                "description": "5-level categorization workflow"
            },
            "storage": {
                "type": "postgres",
                "table_name": "conversation-typification-workflows",
                "auto_upgrade_schema": True
            },
            "max_levels": 5,
            "confidence_threshold": 0.85,
            "fallback_to_human": True
        }
    }
    
    return defaults.get(workflow_id, {})


def sync_workflow_version_from_yaml(workflow_id: str, yaml_config: Dict[str, Any]) -> int:
    """
    Sync workflow configuration from YAML to database.
    
    Args:
        workflow_id: Workflow identifier
        yaml_config: Configuration from YAML file
        
    Returns:
        Version number created
    """
    
    db: Session = next(get_db())
    
    try:
        service = ComponentVersionService(db)
        
        # Get current version or default to 1
        current_version = service.get_active_version(workflow_id)
        next_version = (current_version.version + 1) if current_version else 1
        
        # Create new version
        version_record = service.create_version(
            component_id=workflow_id,
            component_type="workflow",
            version=next_version,
            config=yaml_config,
            created_by="yaml_sync",
            description=f"Synced from YAML file",
            is_active=True,
            sync_source="yaml"
        )
        
        logger.info(f"✅ Synced workflow {workflow_id} to version {next_version}")
        return version_record.version
        
    except Exception as e:
        logger.error(f"❌ Failed to sync workflow {workflow_id}: {str(e)}")
        raise
    finally:
        db.close()


def get_human_handoff_workflow_versioned(
    version: Optional[int] = None,
    whatsapp_enabled: bool = True,
    whatsapp_instance: str = "SofIA",
    **kwargs
):
    """
    Factory function for versioned human handoff workflow.
    
    Args:
        version: Specific version to load (None for active)
        whatsapp_enabled: Enable WhatsApp notifications
        whatsapp_instance: WhatsApp instance name
        **kwargs: Additional parameters
        
    Returns:
        Configured HumanHandoffWorkflow instance
    """
    
    workflow_id = "human-handoff"
    
    if version is None:
        # Get active version
        db: Session = next(get_db())
        try:
            service = ComponentVersionService(db)
            active_version = service.get_active_version(workflow_id)
            version = active_version.version if active_version else 1
        finally:
            db.close()
    
    return create_versioned_workflow(
        workflow_id=workflow_id,
        version=version,
        whatsapp_enabled=whatsapp_enabled,
        whatsapp_instance=whatsapp_instance,
        **kwargs
    )