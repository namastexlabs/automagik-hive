"""
Component Versions Database Schema

Unified table for managing versions of agents, teams, and workflows.
Supports bilateral sync between YAML configurations and database storage.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, JSON, Index
from sqlalchemy.sql import func
from typing import Dict, Any

from .base import Base


class ComponentVersion(Base):
    """
    Unified component versions table for agents, teams, and workflows.
    
    Supports the bilateral sync architecture where components can have
    multiple versions with different configurations, synced between YAML and DB.
    """
    
    __tablename__ = "component_versions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    component_id = Column(String(255), nullable=False, comment="Component identifier (e.g., 'pagbank-specialist', 'ana-team')")
    component_type = Column(String(20), nullable=False, comment="Component type: 'agent', 'team', 'workflow'")
    version = Column(Integer, nullable=False, comment="Version number (e.g., 27, 28, 29)")
    config = Column(JSON, nullable=False, comment="Full component configuration (YAML content)")
    created_at = Column(DateTime, default=func.now(), comment="When this version was created")
    created_by = Column(String(255), default="system", comment="User/system who created this version")
    is_active = Column(Boolean, default=False, comment="Whether this version is currently active")
    is_deprecated = Column(Boolean, default=False, comment="Whether this version is deprecated")
    description = Column(Text, comment="Description of changes in this version")
    
    # Ensure unique component_id + version combination
    __table_args__ = (
        Index('idx_component_versions_unique', 'component_id', 'version', unique=True),
        Index('idx_component_versions_lookup', 'component_id', 'component_type'),
        Index('idx_component_versions_active', 'component_id', 'is_active'),
        Index('idx_component_versions_type', 'component_type'),
        Index('idx_component_versions_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ComponentVersion(component_id='{self.component_id}', type='{self.component_type}', version={self.version}, active={self.is_active})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "component_id": self.component_id,
            "component_type": self.component_type,
            "version": self.version,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "is_active": self.is_active,
            "is_deprecated": self.is_deprecated,
            "description": self.description
        }
    
    @classmethod
    def from_yaml_config(
        cls, 
        component_id: str,
        component_type: str,
        version: int, 
        config: Dict[str, Any], 
        created_by: str = "system",
        description: str = None
    ) -> "ComponentVersion":
        """Create a ComponentVersion from a YAML configuration."""
        return cls(
            component_id=component_id,
            component_type=component_type,
            version=version,
            config=config,
            created_by=created_by,
            description=description or f"{component_type.title()} {component_id} version {version}"
        )


class ComponentVersionHistory(Base):
    """
    Component version history table for tracking changes and rollbacks.
    
    Maintains an audit trail of all version changes for compliance
    and debugging purposes.
    """
    
    __tablename__ = "component_version_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    component_id = Column(String(255), nullable=False)
    component_type = Column(String(20), nullable=False)
    version = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False, comment="Action: created, activated, deactivated, deprecated, yaml_sync, db_sync")
    previous_state = Column(JSON, comment="Previous state before change")
    new_state = Column(JSON, comment="New state after change")
    changed_by = Column(String(255), comment="User/system who made the change")
    changed_at = Column(DateTime, default=func.now(), comment="When the change was made")
    reason = Column(Text, comment="Reason for the change")
    sync_source = Column(String(20), comment="Source of sync: 'yaml', 'db', 'api'")
    
    __table_args__ = (
        Index('idx_component_history_lookup', 'component_id', 'component_type', 'changed_at'),
        Index('idx_component_history_changed', 'changed_at'),
        Index('idx_component_history_action', 'action'),
    )
    
    def __repr__(self):
        return f"<ComponentVersionHistory(component_id='{self.component_id}', type='{self.component_type}', version={self.version}, action='{self.action}')>"