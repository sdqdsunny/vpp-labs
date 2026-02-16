"""
Scenario model for storing scenario definitions and execution results.

Represents a complete VPP operational scenario with timeline and events.
"""

from sqlalchemy import Column, String, JSON, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from models.base import BaseModel


class ScenarioStatus(PyEnum):
    """Scenario execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Scenario(BaseModel):
    """Model for scenario definitions and results."""

    __tablename__ = "scenarios"

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    definition = Column(JSON, nullable=False)  # Scenario configuration
    status = Column(String, default=ScenarioStatus.PENDING.value, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(String, nullable=True)  # Calculated duration
    results = Column(JSON, nullable=True)  # Scenario results

    # Relationships
    device_states = relationship("DeviceState", back_populates="scenario", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="scenario", cascade="all, delete-orphan")
    power_flow_results = relationship("PowerFlowResult", back_populates="scenario", cascade="all, delete-orphan")
    communication_events = relationship("CommunicationEvent", back_populates="scenario", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation."""
        return f"<Scenario(name={self.name}, status={self.status}, id={self.id})>"
