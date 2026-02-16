"""
Metrics model for storing performance metrics during simulation.

Tracks metrics like latency, throughput, error rates, and device outputs.
"""

from sqlalchemy import Column, String, Float, JSON, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from models.base import BaseModel


class Metric(BaseModel):
    """Model for performance metrics."""

    __tablename__ = "metrics"

    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=False, index=True)
    metric_name = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    tags = Column(JSON, nullable=False)  # Additional metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    scenario = relationship("Scenario", back_populates="metrics")

    # Composite index for efficient queries
    __table_args__ = (
        Index("idx_scenario_metric_time", "scenario_id", "metric_name", "timestamp"),
    )

    def __repr__(self):
        """String representation."""
        return f"<Metric(name={self.metric_name}, value={self.value}, scenario_id={self.scenario_id})>"
