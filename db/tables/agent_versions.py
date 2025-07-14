"""
Agent Versions Database Schema

This module defines the database schema for managing agent versions,
supporting configuration changes, A/B testing, and rollback capabilities.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, JSON, Index
from sqlalchemy.sql import func
from typing import Dict, Any, Optional
from datetime import datetime

from .base import Base


class AgentVersion(Base):
    """
    Agent versions table for managing different configurations and prompts.
    
    Supports the dynamic versioning architecture where agents can have
    multiple versions (v25, v26, v27, etc.) with different configurations.
    """
    
    __tablename__ = "agent_versions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(255), nullable=False, comment="Stable agent identifier (e.g., 'pagbank-specialist')")
    version = Column(Integer, nullable=False, comment="Version number (e.g., 27, 28, 29)")
    config = Column(JSON, nullable=False, comment="Full agent configuration including prompts, tools, model settings")
    created_at = Column(DateTime, default=func.now(), comment="When this version was created")
    created_by = Column(String(255), comment="User who created this version")
    is_active = Column(Boolean, default=False, comment="Whether this version is currently active")
    is_deprecated = Column(Boolean, default=False, comment="Whether this version is deprecated")
    description = Column(Text, comment="Description of changes in this version")
    
    # Ensure unique agent_id + version combination
    __table_args__ = (
        Index('idx_agent_versions_unique', 'agent_id', 'version', unique=True),
        Index('idx_agent_versions_lookup', 'agent_id', 'version'),
        Index('idx_agent_versions_active', 'agent_id', 'is_active'),
        Index('idx_agent_versions_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AgentVersion(agent_id='{self.agent_id}', version={self.version}, active={self.is_active})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "version": self.version,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "is_active": self.is_active,
            "is_deprecated": self.is_deprecated,
            "description": self.description
        }
    
    @classmethod
    def from_config_file(
        cls, 
        agent_id: str, 
        version: int, 
        config: Dict[str, Any], 
        created_by: str = "system",
        description: str = None
    ) -> "AgentVersion":
        """Create an AgentVersion from a configuration dictionary."""
        return cls(
            agent_id=agent_id,
            version=version,
            config=config,
            created_by=created_by,
            description=description or f"Version {version} configuration"
        )


class AgentVersionHistory(Base):
    """
    Agent version history table for tracking changes and rollbacks.
    
    Maintains an audit trail of all version changes for compliance
    and debugging purposes.
    """
    
    __tablename__ = "agent_version_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(255), nullable=False)
    version = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False, comment="Action: created, activated, deactivated, deprecated")
    previous_state = Column(JSON, comment="Previous state before change")
    new_state = Column(JSON, comment="New state after change")
    changed_by = Column(String(255), comment="User who made the change")
    changed_at = Column(DateTime, default=func.now(), comment="When the change was made")
    reason = Column(Text, comment="Reason for the change")
    
    __table_args__ = (
        Index('idx_agent_version_history_lookup', 'agent_id', 'version', 'changed_at'),
        Index('idx_agent_version_history_changed', 'changed_at'),
    )
    
    def __repr__(self):
        return f"<AgentVersionHistory(agent_id='{self.agent_id}', version={self.version}, action='{self.action}')>"


class AgentVersionMetrics(Base):
    """
    Agent version metrics table for A/B testing and performance tracking.
    
    Tracks usage statistics and performance metrics for each version
    to support data-driven version management decisions.
    """
    
    __tablename__ = "agent_version_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(255), nullable=False)
    version = Column(Integer, nullable=False)
    metric_date = Column(DateTime, default=func.now(), comment="Date for this metric snapshot")
    total_requests = Column(Integer, default=0, comment="Total requests handled by this version")
    successful_requests = Column(Integer, default=0, comment="Successfully handled requests")
    failed_requests = Column(Integer, default=0, comment="Failed requests")
    average_response_time = Column(Integer, comment="Average response time in milliseconds")
    escalation_rate = Column(Integer, comment="Percentage of requests that were escalated")
    user_satisfaction = Column(Integer, comment="User satisfaction score (1-10)")
    
    __table_args__ = (
        Index('idx_agent_version_metrics_lookup', 'agent_id', 'version', 'metric_date'),
        Index('idx_agent_version_metrics_date', 'metric_date'),
    )
    
    def __repr__(self):
        return f"<AgentVersionMetrics(agent_id='{self.agent_id}', version={self.version}, date={self.metric_date})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "version": self.version,
            "metric_date": self.metric_date.isoformat() if self.metric_date else None,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "average_response_time": self.average_response_time,
            "escalation_rate": self.escalation_rate,
            "user_satisfaction": self.user_satisfaction
        }