"""
Power flow result model for storing power flow calculations.

Stores network state, power flows, violations, and stability assessments.
"""

from sqlalchemy import Column, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from models.base import BaseModel


class PowerFlowResult(BaseModel):
    """Model for power flow calculation results."""

    __tablename__ = "power_flow_results"

    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=False, index=True)
    network_state = Column(JSON, nullable=False)  # Network topology and device states
    power_flows = Column(JSON, nullable=False)  # Power flow on each line
    violations = Column(JSON, nullable=False)  # Voltage and congestion violations
    stability_assessment = Column(JSON, nullable=False)  # Stability metrics
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    scenario = relationship("Scenario", back_populates="power_flow_results")

    def __repr__(self):
        """String representation."""
        return f"<PowerFlowResult(scenario_id={self.scenario_id}, timestamp={self.timestamp})>"
