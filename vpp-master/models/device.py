"""
Device Data Model

Represents a distributed energy resource (DER) in the VPP system.
"""

from sqlalchemy import Column, String, DateTime, JSON, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from utils.database import Base
from utils.validators import DeviceStatus


class Device(Base):
    """
    Device model representing a distributed energy resource
    
    Attributes:
        id: Unique device identifier (primary key)
        device_type: Type of device (solar, wind, battery, load, grid)
        location: Physical location of the device
        status: Current device status (online, offline, error)
        last_heartbeat: Timestamp of last heartbeat
        capabilities: JSON object containing device capabilities
        configuration: JSON object containing device configuration
        created_at: Timestamp when device was registered
        updated_at: Timestamp of last update
        dispatches: Relationship to dispatch commands
    """
    
    __tablename__ = "devices"
    
    # Primary key
    id = Column(String(255), primary_key=True, nullable=False)
    
    # Device information
    device_type = Column(String(50), nullable=False, index=True)  # solar, wind, battery, load, grid
    location = Column(String(255), nullable=False, index=True)
    
    # Status tracking
    status = Column(String(20), default="offline", nullable=False, index=True)  # online, offline, error
    last_heartbeat = Column(DateTime, nullable=True)
    
    # Device metadata
    capabilities = Column(JSON, nullable=False, default={})
    configuration = Column(JSON, nullable=False, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    dispatches = relationship("Dispatch", back_populates="device", cascade="all, delete-orphan")
    
    # Indexes for query optimization
    __table_args__ = (
        Index('idx_device_type', 'device_type'),
        Index('idx_device_location', 'location'),
        Index('idx_device_status', 'status'),
        Index('idx_device_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Device(id={self.id}, type={self.device_type}, status={self.status})>"
    
    def to_dict(self):
        """Convert device to dictionary"""
        return {
            "id": self.id,
            "device_type": self.device_type,
            "location": self.location,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "capabilities": self.capabilities,
            "configuration": self.configuration,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def is_online(self):
        """Check if device is online"""
        return self.status == "online"
    
    def is_offline(self):
        """Check if device is offline"""
        return self.status == "offline"
    
    def is_error(self):
        """Check if device is in error state"""
        return self.status == "error"
    
    def update_status(self, new_status: str):
        """Update device status"""
        if new_status in ["online", "offline", "error"]:
            self.status = new_status
            self.updated_at = datetime.utcnow()
        else:
            raise ValueError(f"Invalid status: {new_status}")
    
    def update_heartbeat(self):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if self.status == "offline":
            self.status = "online"
    
    def update_configuration(self, config: dict):
        """Update device configuration"""
        self.configuration.update(config)
        self.updated_at = datetime.utcnow()
