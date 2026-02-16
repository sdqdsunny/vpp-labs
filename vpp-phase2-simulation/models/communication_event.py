"""
Communication event model for tracking protocol communications.

Records all communication events between VCC and devices with latency and packet loss info.
"""

from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from models.base import BaseModel


class CommunicationEvent(BaseModel):
    """Model for communication events."""

    __tablename__ = "communication_events"

    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=False, index=True)
    protocol = Column(String, nullable=False)  # IEC 104, MQTT, etc.
    source = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    message_type = Column(String, nullable=False)
    latency_ms = Column(Float, nullable=False)
    packet_loss = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    scenario = relationship("Scenario", back_populates="communication_events")

    def __repr__(self):
        """String representation."""
        return f"<CommunicationEvent(protocol={self.protocol}, source={self.source}, dest={self.destination})>"
