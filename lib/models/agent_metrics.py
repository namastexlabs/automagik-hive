"""
Agent Metrics Model

Stores metrics data for agent executions.
Replaces direct SQL CREATE TABLE statements with proper model.
"""

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from .base import Base


class AgentMetrics(Base):
    __tablename__ = "agent_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    agent_name = Column(String(255), nullable=False, index=True)
    execution_type = Column(String(50), nullable=False, index=True)
    metrics = Column(JSON, nullable=False)  # JSONB for performance
    version = Column(String(10), nullable=False, default="1.0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AgentMetrics({self.agent_name}, {self.execution_type} at {self.timestamp})>"
