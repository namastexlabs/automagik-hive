"""
Component Versions Model

Tracks component versions and configurations for agents, teams, and workflows.
Replaces the AgnoVersionService hack with proper database model.
"""

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class ComponentVersion(Base):
    __tablename__ = "component_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    component_id = Column(String(255), nullable=False, index=True)
    component_type = Column(
        String(50), nullable=False, index=True
    )  # agent, team, workflow
    version = Column(Integer, nullable=False, default=1)
    config = Column(JSON, nullable=False)  # YAML config as JSON
    description = Column(Text)
    is_active = Column(Boolean, default=False, index=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by = Column(String(255), default="system")

    def __repr__(self):
        return f"<ComponentVersion({self.component_id} v{self.version}, active={self.is_active})>"
