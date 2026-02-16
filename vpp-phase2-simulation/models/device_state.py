"""
Device state model for storing simulator device states.

Tracks the state of all simulated devices during scenario execution.
"""

from sqlalchemy import Column, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from models.base import BaseModel


class DeviceState(BaseModel):
    """Model for device simulator states."""

    __tablename__ = "device_states"

    device_id = Column(String, nullable=False, index=True)
    device_type = Column(String, nullable=False)  # solar, wind, battery, load
    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=False, index=True)
    state_data = Column(JSON, nullable=False)  # Device-specific state
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    scenario = relationship("Scenario", back_populates="device_states")

    def __repr__(self):
        """String representation."""
        return f"<DeviceState(device_id={self.device_id}, type={self.device_type}, scenario_id={self.scenario_id})>"
