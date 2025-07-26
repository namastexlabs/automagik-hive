"""
Version History Model

Tracks version changes and updates for components.
Provides audit trail for all version transitions.
"""

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class VersionHistory(Base):
    __tablename__ = "version_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    component_id = Column(String(255), nullable=False, index=True)
    from_version = Column(Integer)  # NULL for initial creation
    to_version = Column(Integer, nullable=False)
    action = Column(
        String(50), nullable=False
    )  # created, updated, activated, deactivated
    description = Column(Text)
    changed_by = Column(String(255), default="system")
    changed_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<VersionHistory({self.component_id}: {self.from_version}→{self.to_version}, {self.action})>"
