"""
Agent Version Service

This module provides database operations for managing agent versions,
including CRUD operations, version activation, and A/B testing support.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime
import json

from ..tables.agent_versions import AgentVersion, AgentVersionHistory, AgentVersionMetrics
from ..session import get_db


class AgentVersionService:
    """
    Service class for managing agent versions in the database.
    
    Provides methods for creating, retrieving, updating, and managing
    agent versions with full audit trail and metrics support.
    """
    
    def __init__(self, db: Session = None):
        """Initialize with optional database session."""
        self.db = db or next(get_db())
    
    def create_version(
        self,
        agent_id: str,
        version: int,
        config: Dict[str, Any],
        created_by: str = "system",
        description: str = None,
        is_active: bool = False
    ) -> AgentVersion:
        """
        Create a new agent version.
        
        Args:
            agent_id: Stable agent identifier (e.g., 'pagbank-specialist')
            version: Version number (e.g., 27, 28, 29)
            config: Full agent configuration dictionary
            created_by: User who created this version
            description: Description of changes
            is_active: Whether to make this version active immediately
            
        Returns:
            Created AgentVersion instance
            
        Raises:
            ValueError: If version already exists
        """
        # Check if version already exists
        existing = self.get_version(agent_id, version)
        if existing:
            raise ValueError(f"Version {version} already exists for agent {agent_id}")
        
        # Create new version
        new_version = AgentVersion(
            agent_id=agent_id,
            version=version,
            config=config,
            created_by=created_by,
            description=description or f"Version {version} configuration",
            is_active=is_active
        )
        
        self.db.add(new_version)
        self.db.commit()
        self.db.refresh(new_version)
        
        # Log the creation
        self._log_version_change(
            agent_id=agent_id,
            version=version,
            action="created",
            new_state={"is_active": is_active, "config": config},
            changed_by=created_by,
            reason=description
        )
        
        return new_version
    
    def get_version(self, agent_id: str, version: int) -> Optional[AgentVersion]:
        """
        Get a specific agent version.
        
        Args:
            agent_id: Agent identifier
            version: Version number
            
        Returns:
            AgentVersion instance or None if not found
        """
        return self.db.query(AgentVersion).filter(
            and_(
                AgentVersion.agent_id == agent_id,
                AgentVersion.version == version
            )
        ).first()
    
    def get_latest_version(self, agent_id: str) -> Optional[AgentVersion]:
        """
        Get the latest version for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Latest AgentVersion instance or None if no versions exist
        """
        return self.db.query(AgentVersion).filter(
            AgentVersion.agent_id == agent_id
        ).order_by(desc(AgentVersion.version)).first()
    
    def get_active_version(self, agent_id: str) -> Optional[AgentVersion]:
        """
        Get the currently active version for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Active AgentVersion instance or None if no active version
        """
        return self.db.query(AgentVersion).filter(
            and_(
                AgentVersion.agent_id == agent_id,
                AgentVersion.is_active == True
            )
        ).first()
    
    def list_versions(
        self, 
        agent_id: str, 
        include_deprecated: bool = False
    ) -> List[AgentVersion]:
        """
        List all versions for an agent.
        
        Args:
            agent_id: Agent identifier
            include_deprecated: Whether to include deprecated versions
            
        Returns:
            List of AgentVersion instances ordered by version desc
        """
        query = self.db.query(AgentVersion).filter(
            AgentVersion.agent_id == agent_id
        )
        
        if not include_deprecated:
            query = query.filter(AgentVersion.is_deprecated == False)
        
        return query.order_by(desc(AgentVersion.version)).all()
    
    def activate_version(
        self, 
        agent_id: str, 
        version: int, 
        changed_by: str = "system",
        reason: str = None
    ) -> AgentVersion:
        """
        Activate a specific version (deactivates all others).
        
        Args:
            agent_id: Agent identifier
            version: Version number to activate
            changed_by: User making the change
            reason: Reason for activation
            
        Returns:
            Activated AgentVersion instance
            
        Raises:
            ValueError: If version doesn't exist
        """
        # Get the version to activate
        version_to_activate = self.get_version(agent_id, version)
        if not version_to_activate:
            raise ValueError(f"Version {version} not found for agent {agent_id}")
        
        # Deactivate all other versions
        self.db.query(AgentVersion).filter(
            and_(
                AgentVersion.agent_id == agent_id,
                AgentVersion.version != version
            )
        ).update({"is_active": False})
        
        # Activate the specified version
        version_to_activate.is_active = True
        
        self.db.commit()
        self.db.refresh(version_to_activate)
        
        # Log the activation
        self._log_version_change(
            agent_id=agent_id,
            version=version,
            action="activated",
            new_state={"is_active": True},
            changed_by=changed_by,
            reason=reason or f"Activated version {version}"
        )
        
        return version_to_activate
    
    def deprecate_version(
        self, 
        agent_id: str, 
        version: int,
        changed_by: str = "system",
        reason: str = None
    ) -> AgentVersion:
        """
        Mark a version as deprecated.
        
        Args:
            agent_id: Agent identifier
            version: Version number to deprecate
            changed_by: User making the change
            reason: Reason for deprecation
            
        Returns:
            Deprecated AgentVersion instance
            
        Raises:
            ValueError: If version doesn't exist or is currently active
        """
        version_to_deprecate = self.get_version(agent_id, version)
        if not version_to_deprecate:
            raise ValueError(f"Version {version} not found for agent {agent_id}")
        
        if version_to_deprecate.is_active:
            raise ValueError(f"Cannot deprecate active version {version}. Activate another version first.")
        
        version_to_deprecate.is_deprecated = True
        
        self.db.commit()
        self.db.refresh(version_to_deprecate)
        
        # Log the deprecation
        self._log_version_change(
            agent_id=agent_id,
            version=version,
            action="deprecated",
            new_state={"is_deprecated": True},
            changed_by=changed_by,
            reason=reason or f"Deprecated version {version}"
        )
        
        return version_to_deprecate
    
    def get_config(self, agent_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific version or the active version.
        
        Args:
            agent_id: Agent identifier
            version: Specific version number, or None for active version
            
        Returns:
            Configuration dictionary or None if not found
        """
        if version is not None:
            agent_version = self.get_version(agent_id, version)
        else:
            agent_version = self.get_active_version(agent_id)
        
        return agent_version.config if agent_version else None
    
    def update_config(
        self,
        agent_id: str,
        version: int,
        config: Dict[str, Any],
        changed_by: str = "system",
        reason: str = None
    ) -> AgentVersion:
        """
        Update configuration for a specific version.
        
        Args:
            agent_id: Agent identifier
            version: Version number to update
            config: New configuration dictionary
            changed_by: User making the change
            reason: Reason for the update
            
        Returns:
            Updated AgentVersion instance
            
        Raises:
            ValueError: If version doesn't exist
        """
        version_to_update = self.get_version(agent_id, version)
        if not version_to_update:
            raise ValueError(f"Version {version} not found for agent {agent_id}")
        
        old_config = version_to_update.config
        version_to_update.config = config
        
        self.db.commit()
        self.db.refresh(version_to_update)
        
        # Log the configuration change
        self._log_version_change(
            agent_id=agent_id,
            version=version,
            action="config_updated",
            previous_state={"config": old_config},
            new_state={"config": config},
            changed_by=changed_by,
            reason=reason or f"Updated configuration for version {version}"
        )
        
        return version_to_update
    
    def get_version_history(self, agent_id: str, version: int = None) -> List[AgentVersionHistory]:
        """
        Get version history for an agent or specific version.
        
        Args:
            agent_id: Agent identifier
            version: Optional specific version number
            
        Returns:
            List of AgentVersionHistory instances
        """
        query = self.db.query(AgentVersionHistory).filter(
            AgentVersionHistory.agent_id == agent_id
        )
        
        if version is not None:
            query = query.filter(AgentVersionHistory.version == version)
        
        return query.order_by(desc(AgentVersionHistory.changed_at)).all()
    
    def record_metrics(
        self,
        agent_id: str,
        version: int,
        total_requests: int = 0,
        successful_requests: int = 0,
        failed_requests: int = 0,
        average_response_time: int = None,
        escalation_rate: int = None,
        user_satisfaction: int = None
    ) -> AgentVersionMetrics:
        """
        Record metrics for a specific agent version.
        
        Args:
            agent_id: Agent identifier
            version: Version number
            total_requests: Total requests handled
            successful_requests: Successfully handled requests
            failed_requests: Failed requests
            average_response_time: Average response time in milliseconds
            escalation_rate: Percentage of requests that were escalated
            user_satisfaction: User satisfaction score (1-10)
            
        Returns:
            Created AgentVersionMetrics instance
        """
        metrics = AgentVersionMetrics(
            agent_id=agent_id,
            version=version,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=average_response_time,
            escalation_rate=escalation_rate,
            user_satisfaction=user_satisfaction
        )
        
        self.db.add(metrics)
        self.db.commit()
        self.db.refresh(metrics)
        
        return metrics
    
    def get_metrics(
        self, 
        agent_id: str, 
        version: int = None,
        days: int = 30
    ) -> List[AgentVersionMetrics]:
        """
        Get metrics for an agent or specific version.
        
        Args:
            agent_id: Agent identifier
            version: Optional specific version number
            days: Number of days to look back
            
        Returns:
            List of AgentVersionMetrics instances
        """
        query = self.db.query(AgentVersionMetrics).filter(
            AgentVersionMetrics.agent_id == agent_id
        )
        
        if version is not None:
            query = query.filter(AgentVersionMetrics.version == version)
        
        # Filter by date range
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        query = query.filter(AgentVersionMetrics.metric_date >= start_date)
        
        return query.order_by(desc(AgentVersionMetrics.metric_date)).all()
    
    def _log_version_change(
        self,
        agent_id: str,
        version: int,
        action: str,
        previous_state: Dict[str, Any] = None,
        new_state: Dict[str, Any] = None,
        changed_by: str = "system",
        reason: str = None
    ) -> AgentVersionHistory:
        """
        Log a version change to the history table.
        
        Args:
            agent_id: Agent identifier
            version: Version number
            action: Action performed (created, activated, deprecated, etc.)
            previous_state: Previous state before change
            new_state: New state after change
            changed_by: User who made the change
            reason: Reason for the change
            
        Returns:
            Created AgentVersionHistory instance
        """
        history = AgentVersionHistory(
            agent_id=agent_id,
            version=version,
            action=action,
            previous_state=previous_state,
            new_state=new_state,
            changed_by=changed_by,
            reason=reason
        )
        
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        
        return history
    
    def get_all_agents(self) -> List[str]:
        """
        Get list of all agent IDs that have versions.
        
        Returns:
            List of unique agent IDs
        """
        result = self.db.query(AgentVersion.agent_id).distinct().all()
        return [row[0] for row in result]
    
    def clone_version(
        self,
        agent_id: str,
        source_version: int,
        target_version: int,
        created_by: str = "system",
        description: str = None
    ) -> AgentVersion:
        """
        Clone an existing version to create a new version.
        
        Args:
            agent_id: Agent identifier
            source_version: Version to clone from
            target_version: New version number
            created_by: User creating the clone
            description: Description for the new version
            
        Returns:
            Created AgentVersion instance
            
        Raises:
            ValueError: If source version doesn't exist or target version already exists
        """
        source = self.get_version(agent_id, source_version)
        if not source:
            raise ValueError(f"Source version {source_version} not found for agent {agent_id}")
        
        # Clone the configuration
        config_copy = json.loads(json.dumps(source.config))  # Deep copy
        
        return self.create_version(
            agent_id=agent_id,
            version=target_version,
            config=config_copy,
            created_by=created_by,
            description=description or f"Cloned from version {source_version}"
        )