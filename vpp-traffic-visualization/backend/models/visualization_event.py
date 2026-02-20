"""
Visualization Event Data Model

Represents a standardized event for visualization in the frontend.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class VisualizationEvent:
    """
    Represents a visualization event
    
    Attributes:
        from_component: Source component name
        to_component: Destination component name
        traffic_type: Type of traffic ('Control' or 'Telemetry')
        intensity: Traffic intensity (0.0-1.0)
        packet_size: Packet size in bytes
        timestamp: Event timestamp
    """
    
    from_component: str
    to_component: str
    traffic_type: Literal['Control', 'Telemetry']
    intensity: float
    packet_size: int
    timestamp: datetime
    
    def __post_init__(self):
        """Validate data after initialization"""
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError(f"Intensity must be between 0.0 and 1.0, got {self.intensity}")
        
        if self.traffic_type not in ('Control', 'Telemetry'):
            raise ValueError(f"Traffic type must be 'Control' or 'Telemetry', got {self.traffic_type}")
        
        if self.packet_size < 0:
            raise ValueError(f"Packet size must be non-negative, got {self.packet_size}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary format for JSON serialization"""
        return {
            'from': self.from_component,
            'to': self.to_component,
            'type': self.traffic_type,
            'intensity': self.intensity,
            'packet_size': self.packet_size,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VisualizationEvent':
        """Create from dictionary format"""
        return cls(
            from_component=data['from'],
            to_component=data['to'],
            traffic_type=data['type'],
            intensity=data['intensity'],
            packet_size=data['packet_size'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )
    
    def __repr__(self) -> str:
        return (f"VisualizationEvent({self.from_component} -> {self.to_component}, "
                f"type={self.traffic_type}, intensity={self.intensity:.2f})")
